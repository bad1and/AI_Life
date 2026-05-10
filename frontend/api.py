import requests
import streamlit as st


class API:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url

    def get_agents(self):
        """Получить всех агентов."""
        try:
            r = requests.get(f"{self.base_url}/agents", timeout=10)
            return r.json() if r.ok else []
        except Exception as e:
            st.error(f"Ошибка получения агентов: {e}")
            return []

    def create_agent(self, name, personality):
        try:
            r = requests.post(
                f"{self.base_url}/agents",
                params={"name": name, "personality": personality},
                timeout=30,
            )
            return r.json() if r.ok else None
        except Exception as e:
            st.error(f"Ошибка создания агента: {e}")
            return None

    def send_message(self, agent_id, message):
        try:
            r = requests.post(
                f"{self.base_url}/agents/{agent_id}/message",
                params={"message": message},
                timeout=60,
            )
            return r.json() if r.ok else None
        except Exception as e:
            st.error(f"Ошибка отправки сообщения агенту: {e}")
            return None

    def add_event(self, text):
        try:
            r = requests.post(
                f"{self.base_url}/events",
                params={"event_text": text},
                timeout=30,
            )
            return r.json() if r.ok else None
        except Exception as e:
            st.error(f"Ошибка добавления события: {e}")
            return None

    def get_events(self, limit=50):
        try:
            r = requests.get(f"{self.base_url}/events", params={"limit": limit}, timeout=10)
            return r.json() if r.ok else []
        except Exception as e:
            st.error(f"Ошибка получения событий: {e}")
            return []

    def get_graph(self):
        try:
            r = requests.get(f"{self.base_url}/graph", timeout=10)
            return r.json() if r.ok else {"nodes": [], "edges": []}
        except Exception as e:
            st.error(f"Ошибка получения графа: {e}")
            return {"nodes": [], "edges": []}

    def get_chat_messages(self, limit=50):
        """Получить сообщения из общего чата."""
        try:
            r = requests.get(
                f"{self.base_url}/chat/messages",
                params={"limit": limit},
                timeout=10,
            )
            return r.json() if r.ok else {"messages": [], "total": 0}
        except Exception as e:
            st.error(f"Ошибка получения сообщений чата: {e}")
            return {"messages": [], "total": 0}

    def get_chat_status(self):
        """Получить статус фонового общения."""
        try:
            r = requests.get(f"{self.base_url}/chat/status", timeout=10)
            return r.json() if r.ok else {
                "background_running": False,
                "messages_count": 0,
                "agents_active": 0,
            }
        except Exception as e:
            st.error(f"Ошибка получения статуса чата: {e}")
            return {
                "background_running": False,
                "messages_count": 0,
                "agents_active": 0,
            }

    def send_to_chat(self, agent_id, message):
        """Агент отправляет сообщение в чат."""
        try:
            r = requests.post(
                f"{self.base_url}/chat/send",
                params={"agent_id": agent_id, "message": message},
                timeout=30,
            )
            if r.ok:
                return r.json()
            st.error(f"Ошибка: {r.text}")
            return None
        except Exception as e:
            st.error(f"Ошибка отправки: {e}")
            return None

    def user_send_to_chat(self, message, user_name="Пользователь"):
        """Пользователь отправляет сообщение в чат."""
        try:
            r = requests.post(
                f"{self.base_url}/chat/user",
                params={"message": message, "user_name": user_name},
                timeout=30,
            )
            if r.ok:
                return r.json()
            st.error(f"Ошибка: {r.text}")
            return None
        except Exception as e:
            st.error(f"Ошибка отправки: {e}")
            return None

    def clear_chat(self):
        """Очистить историю чата."""
        try:
            r = requests.post(f"{self.base_url}/chat/clear", timeout=10)
            return r.ok
        except Exception as e:
            st.error(f"Ошибка очистки чата: {e}")
            return False

    def start_background_chat(self):
        """Запустить фоновое общение агентов."""
        try:
            r = requests.post(f"{self.base_url}/chat/start-background", timeout=10)
            return r.ok
        except Exception as e:
            st.error(f"Ошибка запуска фонового чата: {e}")
            return False

    def stop_background_chat(self):
        """Остановить фоновое общение агентов."""
        try:
            r = requests.post(f"{self.base_url}/chat/stop-background", timeout=10)
            return r.ok
        except Exception as e:
            st.error(f"Ошибка остановки фонового чата: {e}")
            return False

    def delete_agent(self, agent_id: str):
        """Удалить агента."""
        try:
            r = requests.delete(f"{self.base_url}/agents/{agent_id}", timeout=10)
            if r.ok:
                return True
            st.error(f"Ошибка удаления: {r.text}")
            return False
        except Exception as e:
            st.error(f"Ошибка удаления: {e}")
            return False


def get_api():
    return API()
