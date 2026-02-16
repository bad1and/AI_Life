import streamlit as st
import time

from api import get_api
from components.agent_card import agent_card
from components.graph import render_graph

st.set_page_config(page_title="КИБЕР РЫВОК", layout="wide")
st.title("🧠 КИБЕР РЫВОК")

api = get_api()

# Боковая панель
with st.sidebar:
    st.header("Управление")

    # Создание агента
    name = st.text_input("Имя", "Алиса")
    personality = st.selectbox("Характер",
                               ["дружелюбный", "задумчивый", "энергичный", "спокойный"])

    if st.button("✨ Создать агента"):
        api.create_agent(name, personality)
        st.rerun()

    st.divider()

    # Событие
    event = st.text_area("Событие", "Найден клад!")
    if st.button("🌍 Добавить событие"):
        api.add_event(event)
        st.rerun()

    st.divider()

    if st.button("🔄 Обновить"):
        st.rerun()

# Основной экран
tab1, tab2, tab3 = st.tabs(["Агенты", "Граф", "События"])

with tab1:
    agents = api.get_agents()
    if not agents:
        st.info("Создайте первого агента")
    else:
        cols = st.columns(3)
        for i, agent in enumerate(agents):
            with cols[i % 3]:
                agent_card(agent, api)

with tab2:
    graph_data = api.get_graph()
    render_graph(graph_data)

with tab3:
    events = api.get_events()
    for e in events[:20]:
        st.write(f"• {e['content']}")
        st.caption(e['timestamp'][:19] if e['timestamp'] else "")
        st.divider()

# Автообновление
time.sleep(2)
st.rerun()