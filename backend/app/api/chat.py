import asyncio
import random
import uuid
from datetime import datetime
from typing import Dict, List

from fastapi import APIRouter, HTTPException

from ..agents.personalities import get_chat_response_prompt
from ..db.database import db
from ..llm.mistral import llm
from ..logger import get_logger
from ..memory.store import memory_store

logger = get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

# In-memory chat storage. Keeps the app simple and avoids changing DB schema.
chat_messages: List[Dict] = []
MAX_CHAT_HISTORY = 200

background_task_running = False
background_task = None


def _trim_chat_history() -> None:
    """Keep only the last MAX_CHAT_HISTORY messages."""
    if len(chat_messages) > MAX_CHAT_HISTORY:
        chat_messages[:] = chat_messages[-MAX_CHAT_HISTORY:]


def _append_message(message: Dict) -> Dict:
    """Append a message to chat and trim old history."""
    chat_messages.append(message)
    _trim_chat_history()
    return message


def _build_recent_context(limit: int = 8, exclude_last: bool = False) -> str:
    """Build readable context for prompts from recent chat messages."""
    if not chat_messages:
        return ""

    messages = chat_messages[:-1] if exclude_last else chat_messages
    recent = messages[-limit:]
    if not recent:
        return ""

    lines = ["Недавние сообщения в общем чате:"]
    for msg in recent:
        name = msg.get("agent_name", "Кто-то")
        text = msg.get("message", "")
        lines.append(f"{name}: {text}")
    return "\n".join(lines)


@router.get("/messages")
async def get_chat_messages(limit: int = 50):
    """Получить последние сообщения из общего чата."""
    limit = max(1, min(limit, MAX_CHAT_HISTORY))
    return {
        "messages": chat_messages[-limit:],
        "total": len(chat_messages),
    }


@router.post("/user")
async def user_send_to_chat(message: str, user_name: str = "Пользователь"):
    """Пользователь отправляет сообщение в общий чат."""
    message = (message or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message is empty")

    logger.info(f"👤 Пользователь {user_name} пишет: {message}")

    chat_message = _append_message({
        "id": str(uuid.uuid4()),
        "agent_id": "user",
        "agent_name": user_name,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "type": "user_message",
    })

    asyncio.create_task(process_new_message(chat_message))
    return {"ok": True, "message": chat_message}


@router.post("/send")
async def send_to_chat(agent_id: str, message: str):
    """Агент отправляет сообщение в чат."""
    message = (message or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message is empty")

    sender = db.fetch_one("SELECT * FROM agents WHERE id = ?", (agent_id,))
    if not sender:
        raise HTTPException(status_code=404, detail="Agent not found")

    chat_message = _append_message({
        "id": str(uuid.uuid4()),
        "agent_id": agent_id,
        "agent_name": sender["name"],
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "type": "agent_message",
    })

    memory_store.add(agent_id, f"Я написал в общий чат: {message}", "нейтрально")

    asyncio.create_task(process_new_message(chat_message))
    return {"ok": True, "message": chat_message}


@router.post("/clear")
async def clear_chat():
    """Очистить историю чата."""
    chat_messages.clear()
    logger.info("🧹 История чата очищена")
    return {"ok": True}


@router.post("/start-background")
async def start_background_chat():
    """Запустить фоновое общение агентов."""
    global background_task_running, background_task

    if background_task_running and background_task and not background_task.done():
        return {"ok": True, "message": "Already running"}

    background_task_running = True
    background_task = asyncio.create_task(background_agent_conversation())
    logger.info("🎮 Запущено фоновое общение агентов")
    return {"ok": True, "message": "Background chat started"}


@router.post("/stop-background")
async def stop_background_chat():
    """Остановить фоновое общение агентов."""
    global background_task_running, background_task

    background_task_running = False

    if background_task and not background_task.done():
        background_task.cancel()
        try:
            await background_task
        except asyncio.CancelledError:
            pass

    background_task = None
    logger.info("⏸️ Фоновое общение остановлено")
    return {"ok": True, "message": "Background chat stopped"}


@router.get("/status")
async def get_chat_status():
    """Получить статус общего чата."""
    agents = db.fetch_all("SELECT id FROM agents") or []
    task_alive = bool(background_task and not background_task.done())
    return {
        "background_running": bool(background_task_running and task_alive),
        "messages_count": len(chat_messages),
        "agents_active": len(agents),
    }


async def background_agent_conversation():
    """Фоновый процесс: агенты сами иногда инициируют разговор."""
    global background_task_running

    logger.info("🔄 Запуск фонового общения агентов")

    try:
        while background_task_running:
            try:
                await asyncio.sleep(random.uniform(10, 30))

                agents = db.fetch_all("SELECT * FROM agents") or []
                if len(agents) < 1:
                    continue

                speaker = random.choice(agents)
                context = _build_recent_context(limit=8)

                prompt = f"""Ты {speaker['name']} ({speaker['personality']}).
Ты участвуешь в общем чате с другими ИИ-агентами и пользователем.

{context}

Напиши новое сообщение в чат с учетом недавнего разговора.
Коротко: 1-2 предложения. Не повторяй одно и то же.

Твое сообщение:"""

                reply = llm.generate(
                    agent_id=speaker["id"],
                    prompt=prompt,
                    system=f"Ты {speaker['name']} и ты участвуешь в общем чате. Пиши живо, коротко и по характеру.",
                    temperature=0.9,
                )

                if reply and not reply.startswith("(Ошибка"):
                    chat_message = _append_message({
                        "id": str(uuid.uuid4()),
                        "agent_id": speaker["id"],
                        "agent_name": speaker["name"],
                        "message": reply.strip(),
                        "timestamp": datetime.now().isoformat(),
                        "type": "agent_message",
                        "initiative": "self",
                    })

                    logger.info(f"💬 {speaker['name']} (сам): {reply[:50]}...")
                    memory_store.add(speaker["id"], f"Я сам написал в чат: {reply}", "нейтрально")
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


async def process_new_message(trigger_message: Dict):
    """Обработка нового сообщения: другие агенты могут ответить один раз."""
    agents = db.fetch_all("SELECT * FROM agents") or []
    other_agents = [a for a in agents if a["id"] != trigger_message.get("agent_id")]

    if not other_agents:
        return

    context = _build_recent_context(limit=8, exclude_last=True)

    # Перемешиваем, чтобы не всегда отвечали в одном порядке.
    random.shuffle(other_agents)

    # Ограничение, чтобы после одного сообщения не отвечала сразу вся толпа.
    max_replies = 2 if len(other_agents) > 2 else 1
    replies_count = 0

    for agent in other_agents:
        if replies_count >= max_replies:
            break

        base_probability = 0.35
        text = trigger_message.get("message", "")

        if "?" in text:
            base_probability += 0.25

        if agent["personality"] in ["дружелюбный", "энергичный", "любопытный"]:
            base_probability += 0.15
        elif agent["personality"] in ["задумчивый", "спокойный"]:
            base_probability -= 0.1

        if random.random() >= base_probability:
            continue

        await asyncio.sleep(random.uniform(1.0, 3.0))

        base_prompt = get_chat_response_prompt(
            name=agent["name"],
            personality_type=agent["personality"],
            message=text,
            sender=trigger_message.get("agent_name", "Кто-то"),
        )

        prompt = f"""{context}

Последнее сообщение:
{trigger_message.get('agent_name', 'Кто-то')}: {text}

{base_prompt}

Важно: ответь именно на последнее сообщение, но учитывай контекст. Не повторяй чужие фразы."""

        reply = llm.generate(
            agent_id=agent["id"],
            prompt=prompt,
            system=f"Ты {agent['name']}, ИИ-агент в общем чате с другими ИИ и пользователем. Отвечай коротко и по характеру.",
            temperature=0.9,
        )

        if not reply or reply.startswith("(Ошибка"):
            continue

        reply_message = _append_message({
            "id": str(uuid.uuid4()),
            "agent_id": agent["id"],
            "agent_name": agent["name"],
            "message": reply.strip(),
            "timestamp": datetime.now().isoformat(),
            "type": "agent_message",
            "in_reply_to": trigger_message["id"],
        })

        replies_count += 1
        logger.info(f"💬 {agent['name']} ответил: {reply[:50]}...")

        memory_store.add(
            agent["id"],
            f"Я ответил {trigger_message.get('agent_name', 'кому-то')} в общем чате: {reply}",
            "нейтрально",
        )
