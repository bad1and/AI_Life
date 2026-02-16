from fastapi import APIRouter, HTTPException
from datetime import datetime
import uuid
import random
from typing import List, Optional
import asyncio

from ..db.database import db
from ..llm.mistral import llm
from ..memory.store import memory_store
from ..logger import get_logger

logger = get_logger(__name__)

# ЭТО САМОЕ ГЛАВНОЕ - создаем роутер с префиксом
router = APIRouter(prefix="/chat", tags=["chat"])

# Хранилище сообщений
chat_messages = []
MAX_CHAT_HISTORY = 100


@router.get("/messages")
async def get_chat_messages(limit: int = 50):
    """Получить последние сообщения из общего чата"""
    logger.info(f"📨 Запрос сообщений чата, лимит: {limit}")
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

    # Запускаем ответы агентов в фоне
    asyncio.create_task(process_chat_responses(chat_message))

    return {"ok": True, "message": chat_message}


@router.post("/send")
async def send_to_chat(agent_id: str, message: str):
    """Агент отправляет сообщение в чат"""
    logger.info(f"🤖 Агент {agent_id} пишет: {message}")

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

    asyncio.create_task(process_chat_responses(chat_message))

    return {"ok": True, "message": chat_message}


@router.post("/clear")
async def clear_chat():
    """Очистить историю чата"""
    chat_messages.clear()
    logger.info("🧹 История чата очищена")
    return {"ok": True}


async def process_chat_responses(trigger_message):
    """Обработка ответов агентов на сообщение"""
    logger.info(f"🔄 Обработка ответов на сообщение: {trigger_message['message'][:30]}...")

    agents = db.fetch_all("SELECT * FROM agents")

    other_agents = [a for a in agents if a['id'] != trigger_message.get('agent_id')]

    if not other_agents:
        return

    # Каждый агент с 30% шансом отвечает
    responding = []
    for agent in other_agents:
        if random.random() < 0.3:
            responding.append(agent)

    if not responding and other_agents:
        responding = [random.choice(other_agents)]

    for agent in responding:
        await asyncio.sleep(random.uniform(0.5, 2.0))

        context = f"В чате {trigger_message['agent_name']} написал: '{trigger_message['message']}'"

        # Получаем последние сообщения для контекста
        recent = ""
        if len(chat_messages) > 3:
            for msg in chat_messages[-4:-1]:
                recent += f"{msg['agent_name']}: {msg['message']}\n"

        prompt = f"{context}\n\nНедавние сообщения:\n{recent}\nЧто ты ответишь?"

        reply = llm.generate(
            agent_id=agent['id'],
            prompt=prompt,
            system=f"Ты {agent['name']}. Твой характер: {agent['personality']}. Ты в общем чате."
        )

        if reply and not reply.startswith("(Ошибка"):
            reply_msg = {
                "id": str(uuid.uuid4()),
                "agent_id": agent['id'],
                "agent_name": agent['name'],
                "message": reply,
                "timestamp": datetime.now().isoformat(),
                "type": "agent_message"
            }

            chat_messages.append(reply_msg)
            logger.info(f"✅ {agent['name']} ответил: {reply[:30]}...")