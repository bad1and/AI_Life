from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import uuid
import random
import time

from .config import config
from .db.database import db
from .agents.models import Agent
from .llm.mistral import llm
from .memory.store import memory_store
from .logger import get_logger, log_request, log_response, log_error, main_logger

# Создаем логгер для этого модуля
logger = get_logger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# Мидлварь для логирования всех запросов
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    # Логируем запрос
    log_request(
        endpoint=request.url.path,
        method=request.method,
        params=dict(request.query_params)
    )

    try:
        response = await call_next(request)
        duration = time.time() - start_time

        # Логируем ответ
        log_response(
            endpoint=request.url.path,
            status=response.status_code,
            duration=duration
        )

        return response
    except Exception as e:
        log_error(e, f"Запрос: {request.url.path}")
        raise


@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Сервер запускается...")
    logger.info(f"📁 База данных: {config.DATABASE_PATH}")
    logger.info(f"🤖 Mistral AI: {'✅ Доступен' if config.MISTRAL_API_KEY else '❌ Не настроен'}")
    logger.info(f"📝 Логи пишутся в: {config.LOG_FILE}")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("👋 Сервер останавливается...")


@app.get("/")
def root():
    logger.debug("Корневой эндпоинт вызван")
    return {
        "status": "ok",
        "mistral": bool(config.MISTRAL_API_KEY),
        "time": datetime.now().isoformat()
    }


@app.post("/agents")
def create_agent(name: str, personality: str = "дружелюбный"):
    logger.info(f"✨ Создание нового агента: {name} (характер: {personality})")

    agent = Agent(name=name, personality=personality)

    db.execute(
        "INSERT INTO agents (id, name, personality, mood, location, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (agent.id, agent.name, agent.personality, agent.mood, agent.location, agent.created_at.isoformat())
    )

    logger.info(f"✅ Агент создан: {agent.id}")

    # Логируем в файл отдельно
    with open(config.LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"\n✨ СОЗДАН АГЕНТ: {agent.name} ({agent.id})\n")

    return agent.to_dict()


@app.get("/agents")
def get_agents():
    logger.debug("Запрос списка всех агентов")
    rows = db.fetch_all("SELECT * FROM agents ORDER BY created_at DESC")
    logger.info(f"📊 Получено агентов: {len(rows)}")
    return [dict(row) for row in rows]


@app.get("/agents/{agent_id}")
def get_agent(agent_id: str):
    logger.debug(f"Запрос агента: {agent_id}")
    row = db.fetch_one("SELECT * FROM agents WHERE id = ?", (agent_id,))
    if not row:
        logger.warning(f"❌ Агент не найден: {agent_id}")
        return {"error": "Not found"}
    return dict(row)


@app.post("/agents/{agent_id}/message")
def send_message(agent_id: str, message: str):
    logger.info(f"💬 Сообщение агенту {agent_id}: {message}")

    agent = db.fetch_one("SELECT * FROM agents WHERE id = ?", (agent_id,))
    if not agent:
        logger.error(f"❌ Агент {agent_id} не найден")
        return {"error": "Agent not found"}

    logger.info(f"🤖 Агент {agent['name']} обрабатывает сообщение...")

    # Генерируем ответ с передачей agent_id для истории
    reply = llm.agent_response(
        agent_id=agent_id,  # Теперь передаём ID
        agent_name=agent['name'],
        personality=agent['personality'],
        message=message
    )
    logger.info(f"📝 Ответ от Mistral: {reply}")

    # Сохраняем в векторную память (долговременную)
    memory_store.add(
        agent_id,
        f"Разговор: Пользователь: {message} -> Я ответил: {reply}",
        "нейтрально"
    )

    # Меняем настроение
    new_mood = min(1.0, max(0.0, agent['mood'] + random.uniform(-0.1, 0.2)))
    db.execute("UPDATE agents SET mood = ? WHERE id = ?", (new_mood, agent_id))
    logger.info(f"😊 Настроение изменено: {agent['mood']:.2f} -> {new_mood:.2f}")

    # Событие в ленту
    db.execute(
        "INSERT INTO events (id, content, agent_id, type, timestamp) VALUES (?, ?, ?, ?, ?)",
        (str(uuid.uuid4()), f"{agent['name']}: {reply}", agent_id, "message", datetime.now())
    )

    return {
        "reply": reply,
        "mood": new_mood,
        "emotion": "😊" if new_mood > 0.7 else "😐" if new_mood > 0.3 else "😢"
    }


@app.get("/agents/{agent_id}/history")
def get_agent_history(agent_id: str):
    """Получить историю разговора с агентом"""
    if agent_id not in llm.conversation_history:
        return {"history": []}

    history = llm.conversation_history[agent_id]
    return {
        "agent_id": agent_id,
        "history": history,
        "count": len(history)
    }


@app.post("/agents/{agent_id}/history/clear")
def clear_agent_history(agent_id: str):
    """Очистить историю агента"""
    llm.clear_history(agent_id)
    return {"ok": True, "message": f"История агента {agent_id} очищена"}


@app.post("/events")
def add_event(event_text: str):
    logger.info(f"🌍 Глобальное событие: {event_text}")

    agents = db.fetch_all("SELECT id FROM agents")
    logger.info(f"👥 Затронуто агентов: {len(agents)}")

    for agent in agents:
        memory_store.add(agent['id'], f"Событие: {event_text}", "нейтрально")
        db.execute(
            "UPDATE agents SET mood = mood + ? WHERE id = ?",
            (random.uniform(-0.1, 0.2), agent['id'])
        )

    event_id = str(uuid.uuid4())
    db.execute(
        "INSERT INTO events (id, content, type, timestamp) VALUES (?, ?, ?, ?)",
        (event_id, event_text, "global", datetime.now())
    )

    logger.info(f"✅ Событие добавлено: {event_id}")

    return {"ok": True, "affected": len(agents)}


@app.get("/events")
def get_events(limit: int = 50):
    logger.debug(f"Запрос событий (лимит: {limit})")
    rows = db.fetch_all("SELECT * FROM events ORDER BY timestamp DESC LIMIT ?", (limit,))
    return [dict(row) for row in rows]


@app.get("/graph")
def get_graph():
    logger.debug("Запрос данных для графа")
    agents = db.fetch_all("SELECT id, name, mood FROM agents")
    logger.info(f"📊 Граф: {len(agents)} узлов")
    return {
        "nodes": [dict(a) for a in agents],
        "edges": []
    }