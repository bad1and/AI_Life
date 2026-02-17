import asyncio
import random
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException

from ..db.database import db
from ..llm.mistral import llm
from ..logger import get_logger
from ..memory.store import memory_store
from ..agents.personalities import get_chat_response_prompt
logger = get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

# Хранилище сообщений
chat_messages = []
MAX_CHAT_HISTORY = 200

# Флаг для фоновой активности агентов - глобальная переменная
background_task_running = False
background_task = None


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
    global background_task_running, background_task

    if not background_task_running:
        background_task_running = True
        # Создаем и сохраняем задачу
        background_task = asyncio.create_task(background_agent_conversation())
        logger.info("🎮 Запущено фоновое общение агентов")
        return {"ok": True, "message": "Background chat started"}

    return {"ok": True, "message": "Already running"}


@router.post("/stop-background")
async def stop_background_chat():
    """Остановить фоновое общение агентов"""
    global background_task_running, background_task

    background_task_running = False

    # Отменяем задачу если она существует
    if background_task and not background_task.done():
        background_task.cancel()
        try:
            await background_task
        except asyncio.CancelledError:
            pass

    logger.info("⏸️ Фоновое общение остановлено")
    return {"ok": True, "message": "Background chat stopped"}


@router.get("/status")
async def get_chat_status():
    """Получить статус чата"""
    global background_task_running
    return {
        "background_running": background_task_running,
        "messages_count": len(chat_messages),
        "agents_active": len(db.fetch_all("SELECT id FROM agents") or [])
    }


async def background_agent_conversation():
    """Фоновый процесс - агенты сами инициируют разговоры"""
    global background_task_running

    logger.info("🔄 Запуск фонового общения агентов")

    try:
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
                prompt = f"""Ты {speaker['name']} ({speaker['personality']}). 
                Напиши что-нибудь в чат. Коротко (1-2 предложения).
                Можно про нашу ИИ-жизнь или просто поболтать.

                Твое сообщение:"""

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
                        "initiative": "self"
                    }

                    chat_messages.append(chat_message)
                    logger.info(f"💬 {speaker['name']} (сам): {reply[:50]}...")

                    # Запускаем ответы на это сообщение
                    asyncio.create_task(process_new_message(chat_message))

            except asyncio.CancelledError:
                logger.info("⏸️ Фоновая задача отменена")
                break
            except Exception as e:
                logger.error(f"Ошибка в фоновом общении: {e}")
                await asyncio.sleep(5)
    finally:
        background_task_running = False
        logger.info("⏸️ Фоновое общение завершено")


async def process_new_message(trigger_message):
    """Обработка нового сообщения - все агенты могут ответить"""

    agents = db.fetch_all("SELECT * FROM agents")

    other_agents = [a for a in agents if a['id'] != trigger_message.get('agent_id')]

    if not other_agents:
        return



    # Контекст из последних сообщений
    context = ""
    if len(chat_messages) > 3:
        context = "Недавние сообщения в чате:\n"
        for msg in chat_messages[-4:-1]:
            context += f"{msg['agent_name']}: {msg['message']}\n"

    for agent in other_agents:
        base_probability = 0.4

        if "?" in trigger_message['message']:
            base_probability += 0.3

        if agent['personality'] in ["дружелюбный", "энергичный", "любопытный"]:
            base_probability += 0.2
        elif agent['personality'] in ["задумчивый", "спокойный"]:
            base_probability -= 0.1

        if random.random() < base_probability:
            await asyncio.sleep(random.uniform(1.0, 3.0))

            # Используем новый промпт с осознанием себя
            from ..agents.personalities import get_chat_context_prompt

            prompt = get_chat_response_prompt(
                name=agent['name'],
                personality_type=agent['personality'],
                message=trigger_message['message'],
                sender=trigger_message['agent_name']
            )

            reply = llm.generate(
                agent_id=agent['id'],
                prompt=prompt,
                system=f"Ты {agent['name']}, AI-модель в чате с другими AI.",
                temperature=0.9
            )

            if reply and not reply.startswith("(Ошибка"):
                reply_message = {
                    "id": str(uuid.uuid4()),
                    "agent_id": agent['id'],
                    "agent_name": agent['name'],
                    "message": reply,
                    "timestamp": datetime.now().isoformat(),
                    "type": "agent_message",
                    "in_reply_to": trigger_message['id']
                }

                chat_messages.append(reply_message)
                logger.info(f"💬 {agent['name']} ответил: {reply[:50]}...")

                memory_store.add(
                    agent['id'],
                    f"Я ответил {trigger_message['agent_name']} в чате: {reply}",
                    "нейтрально"
                )
        if random.random() < base_probability:
            await asyncio.sleep(random.uniform(1.0, 3.0))

            # Новый короткий промпт
            prompt = get_chat_response_prompt(
                name=agent['name'],
                personality_type=agent['personality'],
                message=trigger_message['message'],
                sender=trigger_message['agent_name']
            )

            reply = llm.generate(
                agent_id=agent['id'],
                prompt=prompt,
                system=f"Ты {agent['name']}. Отвечай коротко.",
                temperature=0.9  # Убрали max_tokens
            )