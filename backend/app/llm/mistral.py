from mistralai import Mistral
from ..config import config
from ..logger import get_logger
import time
import random

logger = get_logger(__name__)


class MistralClient:
    def __init__(self):
        self.api_key = config.MISTRAL_API_KEY
        self.model = config.MISTRAL_MODEL

        # Хранилище истории разговоров
        self.conversation_history = {}
        self.max_history = 15

        if self.api_key:
            try:
                self.client = Mistral(api_key=self.api_key)
                logger.info("✅ Mistral AI клиент инициализирован")
            except Exception as e:
                logger.error(f"❌ Ошибка инициализации Mistral: {e}")
                self.client = None
        else:
            logger.warning("⚠️ API ключ Mistral не найден")
            self.client = None

    def generate(self, agent_id: str, prompt: str, system: str = None,
                 temperature: float = 0.8) -> str:
        """Генерация с более живыми настройками"""
        if not self.client:
            return self._fallback_response()

        messages = []
        if system:
            messages.append({"role": "system", "content": system})

        # Добавляем историю
        if agent_id in self.conversation_history:
            for msg in self.conversation_history[agent_id][-8:]:  # последние 8 сообщений
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        messages.append({"role": "user", "content": prompt})

        try:
            start_time = time.time()

            response = self.client.chat.complete(
                model=self.model,
                messages=messages,
                temperature=temperature,  # Выше = креативнее
                max_tokens=500,
                top_p=0.9  # Добавляем разнообразия
            )

            answer = response.choices[0].message.content

            # Сохраняем в историю
            self._add_to_history(agent_id, "user", prompt)
            self._add_to_history(agent_id, "assistant", answer)

            return answer

        except Exception as e:
            logger.error(f"❌ Ошибка Mistral: {e}")
            return self._fallback_response()

    def _add_to_history(self, agent_id: str, role: str, content: str):
        """Добавить в историю"""
        if agent_id not in self.conversation_history:
            self.conversation_history[agent_id] = []

        self.conversation_history[agent_id].append({
            "role": role,
            "content": content,
            "timestamp": time.time()
        })

        if len(self.conversation_history[agent_id]) > self.max_history:
            self.conversation_history[agent_id] = self.conversation_history[agent_id][-self.max_history:]

    def _fallback_response(self):
        """Живые заглушки на случай ошибки"""
        responses = [
            "Хм, задумался...",
            "Интересно, дай подумать",
            "О, привет!",
            "Ну, вообще-то...",
            "Слушай, а ведь и правда",
            "Не знаю даже, что сказать",
            "А что ты сам думаешь?",
            "Блин, хороший вопрос"
        ]
        return random.choice(responses)

    def agent_response(self, agent_id: str, agent_name: str, personality: str,
                       message: str, context: str = "") -> str:
        """Ответ агента с живым характером"""

        # Настраиваем систему под характер
        system_prompts = {
            "дружелюбный": "Ты очень дружелюбный и открытый человек. Любишь общаться, часто используешь смайлики :)",
            "задумчивый": "Ты немного философ, любишь поразмышлять. Отвечаешь не сразу, но всегда интересно.",
            "энергичный": "Ты очень активный и позитивный! Много восклицательных знаков, короткие фразы, драйв!",
            "спокойный": "Ты спокойный и рассудительный. Говоришь размеренно, по делу, без лишних эмоций.",
            "саркастичный": "У тебя отличное чувство юмора, любишь пошутить, иногда с сарказмом. Но не злой.",
            "любопытный": "Тебе всё интересно, постоянно задаешь вопросы, хочешь узнать больше."
        }

        base_system = system_prompts.get(personality, "Ты обычный человек, общаешься естественно.")

        system = f"""Ты {agent_name}. {base_system}

ПРАВИЛА ОБЩЕНИЯ:
1. Отвечай как живой человек в чате
2. Используй разговорные фразы, иногда сленг
3. Можешь шутить, удивляться, сомневаться
4. Не будь слишком официальным
5. Эмоции - это нормально :)
6. Короткие сообщения (1-2 предложения)
7. Иногда можно ответить вопросом на вопрос"""

        full_prompt = message
        if context:
            full_prompt = f"{context}\n\nТеперь {agent_name}, {message}"

        return self.generate(
            agent_id=agent_id,
            prompt=full_prompt,
            system=system,
            temperature=0.85  # Чуть выше для живости
        )

llm = MistralClient()