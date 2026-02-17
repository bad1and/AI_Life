import streamlit as st
import time
from datetime import datetime
import random


def render_chat_room(api):
    """Общая комната чата с автоматическим обновлением"""

    st.markdown("## 💬 Общий чат агентов")
    st.caption("Агенты общаются сами по себе. Вы можете вмешаться в любой момент!")

    # Панель управления сверху
    col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])

    with col1:
        st.markdown("**Управление:**")

    with col2:
        if st.button("▶️ Запустить", use_container_width=True):
            api.start_background_chat()
            st.success("Агенты начали общаться!")
            time.sleep(0.5)
            st.rerun()

    with col3:
        if st.button("⏸️ Стоп", use_container_width=True):
            api.stop_background_chat()
            st.info("Общение приостановлено")
            time.sleep(0.5)
            st.rerun()

    with col4:
        if st.button("🧹 Очистить", use_container_width=True):
            api.clear_chat()
            st.rerun()

    with col5:
        # Переключатель автообновления
        auto_refresh = st.checkbox("Автообновление", value=True)

    # Контейнер для чата с фиксированной высотой
    chat_container = st.container(height=500)  # Высота 500px

    # Получаем сообщения
    try:
        response = api.get_chat_messages(limit=100)
        messages = response.get('messages', [])
    except:
        messages = []
        st.error("Не удалось загрузить сообщения чата")

    # Отображаем сообщения в контейнере
    with chat_container:
        if not messages:
            st.info("Чат пуст. Напишите что-нибудь или запустите общение агентов!")
        else:
            for msg in messages:
                # Определяем тип сообщения
                if msg['type'] == 'user_message':
                    with st.chat_message("user"):
                        st.markdown(f"**{msg['agent_name']}**")
                        st.markdown(msg['message'])
                        if msg.get('timestamp'):
                            st.caption(f"🕐 {msg['timestamp'][11:19]}")
                else:
                    # Агент
                    with st.chat_message("assistant"):
                        # Иконка агента (разная для разных имен)
                        icon = get_agent_icon(msg['agent_name'])
                        st.markdown(f"**{icon} {msg['agent_name']}**")
                        st.markdown(msg['message'])

                        # Показываем время и индикатор ответа
                        cols = st.columns([1, 5])
                        with cols[0]:
                            if msg.get('timestamp'):
                                st.caption(f"🕐 {msg['timestamp'][11:19]}")
                        with cols[1]:
                            if 'in_reply_to' in msg:
                                st.caption("↪️ ответ")

    # Поле ввода внизу (всегда видимо)
    st.markdown("---")

    input_col, send_col = st.columns([5, 1])

    with input_col:
        # Используем уникальный ключ для поля ввода
        if "chat_input" not in st.session_state:
            st.session_state.chat_input = ""

        user_message = st.text_input(
            "Ваше сообщение",
            key="chat_input_widget",
            value=st.session_state.chat_input,
            label_visibility="collapsed",
            placeholder="Напишите сообщение в чат..."
        )

    with send_col:
        if st.button("📤 Отправить", use_container_width=True):
            if user_message:
                with st.spinner("..."):
                    api.user_send_to_chat(user_message, "Пользователь")
                # Очищаем поле ввода
                st.session_state.chat_input = ""
                st.rerun()




def get_agent_icon(name: str) -> str:
    """Разные иконки для разных агентов"""
    icons = {
        'Алиса': '👩‍💻',
        'Боб': '👨‍💻',
        'Чарли': '🧑‍🎨',
        'Диана': '👩‍🎨',
        'Федя': '🧑‍🔧',
        'Степа': '👨‍🔧'
    }
    return icons.get(name, '🤖')