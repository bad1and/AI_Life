import requests
import streamlit as st


class API:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url

    def get_agents(self):
        """Получить всех агентов (без кэширования)"""
        try:
            r = requests.get(f"{self.base_url}/agents")
            return r.json() if r.ok else []
        except Exception as e:
            st.error(f"Ошибка получения агентов: {e}")
            return []

    def create_agent(self, name, personality):
        try:
            r = requests.post(f"{self.base_url}/agents", params={"name": name, "personality": personality})
            return r.json() if r.ok else None
        except:
            return None

    def send_message(self, agent_id, message):
        try:
            r = requests.post(f"{self.base_url}/agents/{agent_id}/message", params={"message": message})
            return r.json() if r.ok else None
        except:
            return None

    def add_event(self, text):
        try:
            r = requests.post(f"{self.base_url}/events", params={"event_text": text})
            return r.json() if r.ok else None
        except:
            return None

    def get_events(self, limit=50):
        try:
            r = requests.get(f"{self.base_url}/events", params={"limit": limit})
            return r.json() if r.ok else []
        except:
            return []

    def get_graph(self):
        try:
            r = requests.get(f"{self.base_url}/graph")
            return r.json() if r.ok else {"nodes": [], "edges": []}
        except:
            return {"nodes": [], "edges": []}

    def get_chat_messages(self, limit=50):
        """Получить сообщения из общего чата"""
        try:
            r = requests.get(f"{self.base_url}/chat/messages", params={"limit": limit})
            return r.json() if r.ok else {"messages": []}
        except Exception as e:
            st.error(f"Ошибка получения сообщений чата: {e}")
            return {"messages": []}

    def send_to_chat(self, agent_id, message):
        """Агент отправляет сообщение в чат"""
        try:
            r = requests.post(
                f"{self.base_url}/chat/send",
                params={"agent_id": agent_id, "message": message}
            )
            if r.ok:
                return r.json()
            else:
                st.error(f"Ошибка: {r.text}")
                return None
        except Exception as e:
            st.error(f"Ошибка отправки: {e}")
            return None

    def user_send_to_chat(self, message, user_name="Пользователь"):
        """Пользователь отправляет сообщение в чат"""
        try:
            r = requests.post(
                f"{self.base_url}/chat/user",
                params={"message": message, "user_name": user_name}
            )
            if r.ok:
                return r.json()
            else:
                st.error(f"Ошибка: {r.text}")
                return None
        except Exception as e:
            st.error(f"Ошибка отправки: {e}")
            return None

    def clear_chat(self):
        """Очистить историю чата"""
        try:
            r = requests.post(f"{self.base_url}/chat/clear")
            return r.ok
        except:
            return False

    def start_background_chat(self):
        """Запустить фоновое общение агентов"""
        try:
            r = requests.post(f"{self.base_url}/chat/start-background")
            return r.ok
        except:
            return False

    def stop_background_chat(self):
        """Остановить фоновое общение агентов"""
        try:
            r = requests.post(f"{self.base_url}/chat/stop-background")
            return r.ok
        except:
            return False

    def delete_agent(self, agent_id: str):
        """Удалить агента"""
        try:
            r = requests.delete(f"{self.base_url}/agents/{agent_id}")
            if r.ok:
                st.success(f"Агент удален")
                return True  # Возвращаем True при успехе
            else:
                st.error(f"Ошибка удаления: {r.text}")
                return False
        except Exception as e:
            st.error(f"Ошибка: {e}")
            return False


def get_api():
    return API()

