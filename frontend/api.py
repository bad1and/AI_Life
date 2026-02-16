import requests
import streamlit as st


class API:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url

    def get_agents(self):
        try:
            r = requests.get(f"{self.base_url}/agents")
            return r.json() if r.ok else []
        except:
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


@st.cache_resource
def get_api():
    return API()