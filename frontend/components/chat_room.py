import streamlit as st
import time
from datetime import datetime


def render_chat_room(api):
    """Общая комната чата для агентов и пользователя"""

    st.markdown("## 💬 Общий чат агентов")
    st.caption("Агенты общаются сами по себе. Вы можете вмешаться в любой момент!")

    # Панель управления
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

    with col1:
        st.markdown("**Управление чатом:**")

    with col2:
        if st.button("▶️ Запустить общение", use_container_width=True):
            api.start_background_chat()
            st.success("Агенты начали общаться!")
            time.sleep(0.5)
            st.rerun()

    with col3:
        if st.button("⏸️ Остановить", use_container_width=True):
            api.stop_background_chat()
            st.info("Общение приостановлено")
            time.sleep(0.5)
            st.rerun()

    with col4:
        if st.button("🔄 Обновить", use_container_width=True):
            st.rerun()

    st.divider()

    # Получаем сообщения чата
    try:
        response = api.get_chat_messages(limit=100)
        messages = response.get('messages', [])
    except:
        messages = []
        st.error("Не удалось загрузить сообщения чата")

    # Отображаем сообщения в хронологическом порядке
    for msg in messages:
        # Определяем иконку и цвет
        if msg['type'] == 'user_message':
            icon = "👤"
            name_color = "blue"
        else:
            # Разные иконки для разных агентов
            icons = {
                msg.get('agent_name', ''): random_icon(msg.get('agent_name', ''))
            }
            icon = "🤖"
            name_color = "green"

        # Создаем колонки для сообщения
        col_time, col_name, col_msg = st.columns([1, 1, 5])

        with col_time:
            # Время сообщения
            if msg.get('timestamp'):
                time_str = msg['timestamp'][11:19]  # HH:MM:SS
                st.caption(time_str)
            else:
                st.caption("--:--:--")

        with col_name:
            # Имя отправителя с иконкой
            st.markdown(f"**{icon} {msg['agent_name']}**")

        with col_msg:
            # Текст сообщения
            st.markdown(msg['message'])

            # Если это ответ на другое сообщение, показываем подсказку
            if 'in_reply_to' in msg:
                st.caption("↪️ ответ на предыдущее")

        st.divider()

    # Поле для ввода нового сообщения
    st.markdown("---")
    st.markdown("### ✍️ Написать в чат")

    col_input, col_send = st.columns([4, 1])

    with col_input:
        user_message = st.text_input("Ваше сообщение", key="chat_input", label_visibility="collapsed")

    with col_send:
        if st.button("📤 Отправить", use_container_width=True):
            if user_message:
                with st.spinner("Отправка..."):
                    api.user_send_to_chat(user_message, "Пользователь")
                st.success("Сообщение отправлено!")
                time.sleep(0.5)
                st.rerun()

    # Статистика
    with st.expander("📊 Статистика чата"):
        agents = api.get_agents()
        st.markdown(f"**Агентов в чате:** {len(agents)}")
        st.markdown(f"**Всего сообщений:** {len(messages)}")

        if messages:
            # Подсчет сообщений по участникам
            stats = {}
            for msg in messages:
                name = msg['agent_name']
                stats[name] = stats.get(name, 0) + 1

            st.markdown("**Активность:**")
            for name, count in stats.items():
                st.markdown(f"- {name}: {count} сообщ.")


def random_icon(name):
    """Генерирует случайную иконку для агента на основе имени"""
    icons = ["🤖", "👾", "🎮", "🧠", "👽", "🤓", "🦊", "🐼", "🦁", "🐧"]
    # Берем индекс на основе имени для постоянства
    idx = sum(ord(c) for c in name) % len(icons)
    return icons[idx]