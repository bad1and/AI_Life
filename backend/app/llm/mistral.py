from mistralai import Mistral
from ..config import config
from ..logger import get_logger
import time

logger = get_logger(__name__)


class MistralClient:
    def __init__(self):
        self.api_key = config.MISTRAL_API_KEY
        self.model = config.MISTRAL_MODEL

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

    def generate(self, prompt: str, system: str = None) -> str:
        if not self.client:
            logger.warning("⚠️ Mistral клиент не доступен, используется заглушка")
            return "(Mistral не настроен)"

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            start_time = time.time()
            logger.debug(f"📤 Запрос к Mistral: {prompt[:50]}...")

            response = self.client.chat.complete(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=150
            )

            duration = time.time() - start_time
            answer = response.choices[0].message.content

            logger.debug(f"📥 Ответ от Mistral ({duration:.2f}с): {answer[:50]}...")

            # Логируем успешные запросы в отдельный файл
            with open(config.LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(f"\n🤖 MISTRAL REQUEST [{time.strftime('%Y-%m-%d %H:%M:%S')}]\n")
                f.write(f"   Prompt: {prompt}\n")
                f.write(f"   Response: {answer}\n")
                f.write("-" * 50 + "\n")

            return answer

        except Exception as e:
            logger.error(f"❌ Ошибка Mistral API: {e}")
            return f"(Ошибка: {str(e)})"

    def agent_response(self, agent_name: str, personality: str, message: str) -> str:
        logger.info(f"💬 Генерация ответа для {agent_name}")
        system = f"Ты {agent_name}. Твой характер: {personality}. Отвечай кратко, 1-2 предложения."
        return self.generate(message, system)


llm = MistralClient()