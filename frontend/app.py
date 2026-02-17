import streamlit as st
import time

from api import get_api
from components.agent_card import agent_card
from components.graph import render_graph
from components.chat_room import render_chat_room  # <-- Импортируем

st.cache_data.clear()

st.set_page_config(page_title="КИБЕР РЫВОК", layout="wide")
st.title("🧠 КИБЕР РЫВОК - Виртуальный мир AI-агентов")

api = get_api()

# Боковая панель (оставляем как есть)
with st.sidebar:
    st.header("Управление")

    # Создание агента
    name = st.text_input("Имя", "Алиса")
    personality = st.selectbox("Характер",
                               ["дружелюбный", "задумчивый", "энергичный", "спокойный", "саркастичный", "любопытный"])

    if st.button("✨ Создать агента"):
        api.create_agent(name, personality)
        st.rerun()

    st.divider()

    # Событие
    event = st.text_area("Глобальное событие", "Найден клад!")
    if st.button("🌍 Добавить событие"):
        api.add_event(event)
        st.rerun()


# Основной экран - теперь 4 вкладки
tab1, tab2, tab3, tab4 = st.tabs(["👥 Агенты", "🔗 Граф", "📜 События", "💬 Общий чат"])

with tab1:
    agents = api.get_agents()
    if not agents:
        st.info("Создайте первого агента в боковой панели")
    else:
        cols = st.columns(3)
        for i, agent in enumerate(agents):
            with cols[i % 3]:
                agent_card(agent, api)

with tab2:
    graph_data = api.get_graph()
    render_graph(graph_data)

with tab3:
    events = api.get_events(limit=100)
    for e in events[:50]:
        col1, col2 = st.columns([1, 10])
        with col1:
            if e['type'] == 'chat':
                st.markdown("💬")
            elif e['type'] == 'global':
                st.markdown("🌍")
            else:
                st.markdown("📌")
        with col2:
            st.write(e['content'])
            st.caption(e['timestamp'][:19] if e['timestamp'] else "")
        st.divider()

with tab4:
    # Новая вкладка с общим чатом
    render_chat_room(api)


