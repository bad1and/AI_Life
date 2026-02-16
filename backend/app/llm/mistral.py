from mistralai import Mistral
from ..config import config
from ..logger import get_logger
import time
from typing import List, Dict

logger = get_logger(__name__)


class MistralClient:
    def __init__(self):
        self.api_key = config.MISTRAL_API_KEY
        self.model = config.MISTRAL_MODEL

        # Хранилище истории разговоров для каждого агента
        # {agent_id: [{"role": "user/assistant", "content": "текст"}, ...]}
        self.conversation_history = {}

        # Максимальная длина истории (чтобы не переполнить контекст)
        self.max_history = 10

        if self.api_key:
            try:
                self.client = Mistral(api_key=self.api_key)
                logger.info("✅ Mistral AI клиент инициализирован")
                logger.info(f"🤖 Модель: {self.model}")
            except Exception as e:
                logger.error(f"❌ Ошибка инициализации Mistral: {e}")
                self.client = None
        else:
            logger.warning("⚠️ API ключ Mistral не найден")
            self.client = None

    def add_to_history(self, agent_id: str, role: str, content: str):
        """Добавить сообщение в историю агента"""
        if agent_id not in self.conversation_history:
            self.conversation_history[agent_id] = []

        self.conversation_history[agent_id].append({
            "role": role,
            "content": content,
            "timestamp": time.time()
        })

        # Ограничиваем длину истории
        if len(self.conversation_history[agent_id]) > self.max_history:
            self.conversation_history[agent_id] = self.conversation_history[agent_id][-self.max_history:]

        logger.debug(f"📝 История {agent_id}: {len(self.conversation_history[agent_id])} сообщений")

    def get_history_context(self, agent_id: str) -> str:
        """Получить контекст из истории для промпта"""
        if agent_id not in self.conversation_history or not self.conversation_history[agent_id]:
            return ""

        history = self.conversation_history[agent_id][:-1]  # Всё кроме последнего
        if not history:
            return ""

        context = "\n\nПредыдущий разговор:\n"
        for msg in history[-5:]:  # Берём последние 5 сообщений
            role = "Ты" if msg["role"] == "assistant" else "Собеседник"
            context += f"{role}: {msg['content']}\n"

        return context

    def generate(self, agent_id: str, prompt: str, system: str = None) -> str:
        """Генерация с учетом истории"""
        if not self.client:
            logger.warning("⚠️ Mistral клиент не доступен, используется заглушка")
            return "(Mistral не настроен)"

        # Добавляем сообщение пользователя в историю
        self.add_to_history(agent_id, "user", prompt)

        # Получаем контекст из истории
        history_context = self.get_history_context(agent_id)

        # Формируем полный промпт с историей
        full_prompt = prompt
        if history_context:
            full_prompt = f"{history_context}\n\nТекущий вопрос: {prompt}"

        messages = []
        if system:
            messages.append({"role": "system", "content": system})

        # Добавляем историю как отдельные сообщения (более правильно)
        if agent_id in self.conversation_history:
            # Берём предпоследние сообщения (всё кроме последнего)
            for msg in self.conversation_history[agent_id][:-1]:
                messages.append({
                    "role": "assistant" if msg["role"] == "assistant" else "user",
                    "content": msg["content"]
                })

        # Добавляем текущий запрос
        messages.append({"role": "user", "content": prompt})

        try:
            start_time = time.time()
            logger.debug(f"📤 Запрос к Mistral для {agent_id}: {prompt[:50]}...")
            logger.debug(f"📚 История сообщений: {len(messages) - 1} предыдущих")

            response = self.client.chat.complete(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=150
            )

            duration = time.time() - start_time
            answer = response.choices[0].message.content

            # Добавляем ответ в историю
            self.add_to_history(agent_id, "assistant", answer)

            logger.debug(f"📥 Ответ от Mistral ({duration:.2f}с): {answer[:50]}...")

            # Логируем успешные запросы
            with open(config.LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(f"\n🤖 MISTRAL REQUEST [{time.strftime('%Y-%m-%d %H:%M:%S')}]\n")
                f.write(f"   Agent: {agent_id}\n")
                f.write(f"   History: {len(messages) - 1} messages\n")
                f.write(f"   Response: {answer}\n")
                f.write("-" * 50 + "\n")

            return answer

        except Exception as e:
            logger.error(f"❌ Ошибка Mistral API: {e}")
            return f"(Ошибка: {str(e)})"

    def agent_response(self, agent_id: str, agent_name: str, personality: str, message: str) -> str:
        """Ответ агента с учетом истории"""
        logger.info(f"💬 Генерация ответа для {agent_name} (id: {agent_id})")
        system = f"Ты {agent_name}. Твой характер: {personality}. Отвечай кратко, 1-2 предложения. Помни предыдущий разговор."
        return self.generate(agent_id, message, system)

    def clear_history(self, agent_id: str):
        """Очистить историю агента"""
        if agent_id in self.conversation_history:
            del self.conversation_history[agent_id]
            logger.info(f"🧹 История очищена для агента {agent_id}")


llm = MistralClient()