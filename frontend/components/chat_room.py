from datetime import datetime

import streamlit as st

try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    st_autorefresh = None


AUTO_REFRESH_INTERVAL_MS = 3000


def render_chat_room(api):
    """Общая комната чата с рабочим автообновлением."""

    st.markdown("## 💬 Общий чат агентов")
    st.caption("Агенты общаются сами по себе. Вы можете вмешаться в любой момент!")

    status = api.get_chat_status()
    running = bool(status.get("background_running", False))
    agents_count = status.get("agents_active", 0)
    messages_count = status.get("messages_count", 0)

    col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])

    with col1:
        state_icon = "🟢" if running else "⚪"
        state_text = "запущен" if running else "остановлен"
        st.markdown(f"**{state_icon} Чат {state_text}**")
        st.caption(f"Агентов: {agents_count} · Сообщений: {messages_count}")

    with col2:
        if st.button("▶️ Запустить", disabled=running, use_container_width=True):
            if api.start_background_chat():
                st.rerun()

    with col3:
        if st.button("⏸️ Стоп", disabled=not running, use_container_width=True):
            if api.stop_background_chat():
                st.rerun()

    with col4:
        if st.button("🧹 Очистить", use_container_width=True):
            if api.clear_chat():
                st.rerun()

    with col5:
        auto_refresh = st.checkbox("Автообновление", value=True)

    if auto_refresh:
        if st_autorefresh is not None:
            st_autorefresh(interval=AUTO_REFRESH_INTERVAL_MS, key="chat_autorefresh")
        else:
            st.warning(
                "Автообновление требует пакет streamlit-autorefresh. "
                "Установите зависимости из обновленного requirements.txt."
            )

    try:
        response = api.get_chat_messages(limit=100)
        messages = response.get("messages", [])
    except Exception:
        messages = []
        st.error("Не удалось загрузить сообщения чата")

    chat_container = st.container(height=500)

    with chat_container:
        if not messages:
            st.info("Чат пуст. Напишите что-нибудь или запустите общение агентов!")
        else:
            for msg in messages:
                render_chat_message(msg)

    st.markdown("---")

    user_message = st.chat_input("Напишите сообщение в чат...")
    if user_message:
        text = user_message.strip()
        if text:
            api.user_send_to_chat(text, "Пользователь")
            st.rerun()


def render_chat_message(msg):
    """Отрисовать одно сообщение."""
    msg_type = msg.get("type", "agent_message")
    name = msg.get("agent_name", "Неизвестно")
    text = msg.get("message", "")
    timestamp = format_time(msg.get("timestamp"))

    if msg_type == "user_message":
        with st.chat_message("user"):
            st.markdown(f"**{name}**")
            st.markdown(text)
            if timestamp:
                st.caption(f"🕐 {timestamp}")
        return

    with st.chat_message("assistant"):
        icon = get_agent_icon(name)
        st.markdown(f"**{icon} {name}**")
        st.markdown(text)

        captions = []
        if timestamp:
            captions.append(f"🕐 {timestamp}")
        if msg.get("in_reply_to"):
            captions.append("↪️ ответ")
        if msg.get("initiative") == "self":
            captions.append("сам написал")

        if captions:
            st.caption(" · ".join(captions))


def format_time(timestamp: str) -> str:
    """Вернуть HH:MM:SS из ISO timestamp."""
    if not timestamp:
        return ""

    try:
        return datetime.fromisoformat(timestamp).strftime("%H:%M:%S")
    except ValueError:
        return timestamp[11:19] if len(timestamp) >= 19 else timestamp


def get_agent_icon(name: str) -> str:
    """Разные иконки для разных агентов."""
    icons = {
        "Алиса": "👩‍💻",
        "Боб": "👨‍💻",
        "Чарли": "🧑‍🎨",
        "Диана": "👩‍🎨",
        "Федя": "🧑‍🔧",
        "Степа": "👨‍🔧",
    }
    return icons.get(name, "🤖")
