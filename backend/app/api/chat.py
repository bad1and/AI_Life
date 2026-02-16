from fastapi import APIRouter, HTTPException
from datetime import datetime
import uuid
import random
import asyncio
from typing import List, Optional
from ..agents.personalities import get_personality_prompt
from ..db.database import db
from ..llm.mistral import llm
from ..memory.store import memory_store
from ..logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

# Хранилище сообщений
chat_messages = []
MAX_CHAT_HISTORY = 200  # Увеличим историю

# Флаг для фоновой активности агентов
background_task_running = False


@router.get("/messages")
async def get_chat_messages(limit: int = 50):
    """Получить последние сообщения из общего чата"""
    return {
        "messages": chat_messages[-limit:],
        "total": len(chat_messages)
    }


@router.post("/user")
async def user_send_to_chat(message: str, user_name: str = "Пользователь"):
    """Пользователь отправляет сообщение в общий чат"""
    logger.info(f"👤 Пользователь {user_name} пишет: {message}")

    chat_message = {
        "id": str(uuid.uuid4()),
        "agent_id": "user",
        "agent_name": user_name,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "type": "user_message"
    }

    chat_messages.append(chat_message)

    if len(chat_messages) > MAX_CHAT_HISTORY:
        chat_messages[:] = chat_messages[-MAX_CHAT_HISTORY:]

    # Запускаем ответы агентов
    asyncio.create_task(process_new_message(chat_message))

    return {"ok": True, "message": chat_message}


@router.post("/send")
async def send_to_chat(agent_id: str, message: str):
    """Агент отправляет сообщение в чат"""
    sender = db.fetch_one("SELECT * FROM agents WHERE id = ?", (agent_id,))
    if not sender:
        raise HTTPException(status_code=404, detail="Agent not found")

    chat_message = {
        "id": str(uuid.uuid4()),
        "agent_id": agent_id,
        "agent_name": sender['name'],
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "type": "agent_message"
    }

    chat_messages.append(chat_message)

    if len(chat_messages) > MAX_CHAT_HISTORY:
        chat_messages[:] = chat_messages[-MAX_CHAT_HISTORY:]

    # Сохраняем в память агента
    memory_store.add(
        agent_id,
        f"Я написал в чат: {message}",
        "нейтрально"
    )

    # Запускаем ответы других агентов
    asyncio.create_task(process_new_message(chat_message))

    return {"ok": True, "message": chat_message}


@router.post("/clear")
async def clear_chat():
    """Очистить историю чата"""
    chat_messages.clear()
    logger.info("🧹 История чата очищена")
    return {"ok": True}


@router.post("/start-background")
async def start_background_chat():
    """Запустить фоновое общение агентов"""
    global background_task_running
    if not background_task_running:
        background_task_running = True
        asyncio.create_task(background_agent_conversation())
        logger.info("🎮 Запущено фоновое общение агентов")
        return {"ok": True, "message": "Background chat started"}
    return {"ok": True, "message": "Already running"}


@router.post("/stop-background")
async def stop_background_chat():
    """Остановить фоновое общение агентов"""
    global background_task_running
    background_task_running = False
    logger.info("⏸️ Фоновое общение остановлено")
    return {"ok": True, "message": "Background chat stopped"}


async def background_agent_conversation():
    """Фоновый процесс - агенты сами инициируют разговоры"""
    global background_task_running

    logger.info("🔄 Запуск фонового общения агентов")

    while background_task_running:
        try:
            # Ждем случайное время (от 10 до 30 секунд)
            wait_time = random.uniform(10, 30)
            await asyncio.sleep(wait_time)

            # Получаем всех агентов
            agents = db.fetch_all("SELECT * FROM agents")
            if len(agents) < 2:
                continue

            # Выбираем случайного агента для инициации разговора
            speaker = random.choice(agents)

            # Определяем тему разговора на основе последних сообщений
            context = ""
            if chat_messages:
                recent = chat_messages[-5:]
                context = "Недавние сообщения в чате:\n"
                for msg in recent:
                    context += f"{msg['agent_name']}: {msg['message']}\n"

            # Генерируем сообщение от агента
            # Новый живой промпт
            prompt = f"""Контекст чата:
            {context}

            Ты сейчас {speaker['name']} и находишься в общем чате с другими.

            Что можно написать:
            - Поделиться мыслями о погоде/времени
            - Спросить как дела у других
            - Рассказать что-то смешное
            - Пожаловаться на что-то
            - Предложить тему для разговора
            - Или просто написать что-то спонтанное

            Пиши как человек в мессенджере - коротко, живо, с эмоциями!"""


            reply = llm.generate(
                agent_id=speaker['id'],
                prompt=prompt,
                system=f"Ты {speaker['name']} и ты участвуешь в общем чате. Пиши как человек."
            )

            if reply and not reply.startswith("(Ошибка"):
                # Отправляем сообщение в чат
                chat_message = {
                    "id": str(uuid.uuid4()),
                    "agent_id": speaker['id'],
                    "agent_name": speaker['name'],
                    "message": reply,
                    "timestamp": datetime.now().isoformat(),
                    "type": "agent_message",
                    "initiative": "self"  # пометка, что агент сам инициировал
                }

                chat_messages.append(chat_message)
                logger.info(f"💬 {speaker['name']} (сам): {reply[:50]}...")

                # Запускаем ответы на это сообщение
                asyncio.create_task(process_new_message(chat_message))

        except Exception as e:
            logger.error(f"Ошибка в фоновом общении: {e}")
            await asyncio.sleep(5)

    logger.info("⏸️ Фоновое общение завершено")


async def process_new_message(trigger_message):
    """Обработка нового сообщения"""
    agents = db.fetch_all("SELECT * FROM agents")

    other_agents = [a for a in agents if a['id'] != trigger_message.get('agent_id')]

    if not other_agents:
        return

    # Контекст из последних сообщений
    context = ""
    if len(chat_messages) > 3:
        context = "Недавние сообщения:\n"
        for msg in chat_messages[-4:-1]:
            context += f"{msg['agent_name']}: {msg['message']}\n"

    for agent in other_agents:
        # Агент решает, отвечать ли
        should_respond = random.random() < 0.5  # 50% шанс

        # Если вопрос - выше шанс
        if "?" in trigger_message['message']:
            should_respond = random.random() < 0.8

        if should_respond:
            await asyncio.sleep(random.uniform(1, 4))  # Пауза как у людей

            # Получаем персонализированный промпт
            personality_prompt = get_personality_prompt(
                agent['name'],
                agent['personality']
            )

            prompt = f"""{context}
Новое сообщение от {trigger_message['agent_name']}: "{trigger_message['message']}"

Ты сейчас читаешь это сообщение. Что ты ответишь?
Пиши естественно, как в реальном чате.
"""

            reply = llm.generate(
                agent_id=agent['id'],
                prompt=prompt,
                system=personality_prompt,
                temperature=0.9
            )

            if reply and not reply.startswith("(Ошибка"):
                # Отправляем ответ
                reply_message = {
                    "id": str(uuid.uuid4()),
                    "agent_id": agent['id'],
                    "agent_name": agent['name'],
                    "message": reply,
                    "timestamp": datetime.now().isoformat(),
                    "type": "agent_message"
                }

                chat_messages.append(reply_message)
                logger.info(f"💬 {agent['name']}: {reply[:50]}...")


# Запускаем фоновое общение при старте
@router.on_event("startup")
async def startup_event():
    """Запускаем фоновое общение при старте сервера"""
    asyncio.create_task(start_background_chat())