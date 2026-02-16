import streamlit as st
import time
from datetime import datetime


def render_chat_room(api):
    """Общая комната чата для агентов и пользователя"""

    st.markdown("## 💬 Общий чат")
    st.caption("Агенты общаются друг с другом и с вами")

    # Получаем сообщения чата
    try:
        response = api.get_chat_messages(limit=50)
        messages = response.get('messages', [])
    except:
        messages = []
        st.error("Не удалось загрузить сообщения чата")

    # Контейнер для сообщений
    chat_container = st.container()

    # Отображаем сообщения
    with chat_container:
        if not messages:
            st.info("Чат пуст. Напишите что-нибудь!")
        else:
            for msg in reversed(messages):  # Показываем от старых к новым
                # Определяем стиль сообщения
                if msg['type'] == 'user_message':
                    # Сообщение от пользователя
                    with st.chat_message("user"):
                        st.markdown(f"**{msg['agent_name']}**")
                        st.markdown(msg['message'])
                        st.caption(f"🕐 {msg['timestamp'][11:19] if msg['timestamp'] else ''}")

                elif msg['type'] == 'agent_message':
                    # Сообщение от агента
                    with st.chat_message("assistant"):
                        # Определяем эмодзи по настроению агента
                        # (можно добавить запрос настроения)
                        st.markdown(f"**🤖 {msg['agent_name']}**")
                        st.markdown(msg['message'])

                        # Показываем информацию об ответе
                        if 'in_reply_to' in msg:
                            st.caption(f"↪️ В ответ на сообщение")

                        st.caption(f"🕐 {msg['timestamp'][11:19] if msg['timestamp'] else ''}")

                else:
                    # Другие типы сообщений
                    with st.chat_message("assistant"):
                        st.markdown(f"**{msg.get('agent_name', 'Система')}**")
                        st.markdown(msg['message'])
                        st.caption(f"🕐 {msg['timestamp'][11:19] if msg['timestamp'] else ''}")

    # Панель управления чатом
    with st.container():
        st.markdown("---")

        col1, col2, col3 = st.columns([3, 1, 1])

        with col1:
            # Поле ввода сообщения
            user_message = st.text_input("Ваше сообщение в общий чат", key="chat_input")

        with col2:
            # Кнопка отправки
            if st.button("📤 Отправить", use_container_width=True):
                if user_message:
                    with st.spinner("Отправка..."):
                        api.user_send_to_chat(user_message, "Пользователь")
                    st.rerun()

        with col3:
            # Кнопка обновления
            if st.button("🔄 Обновить", use_container_width=True):
                st.rerun()

    # Инструменты для агентов (опционально)
    with st.expander("🤖 Управление агентами в чате"):
        agents = api.get_agents()

        if agents:
            st.markdown("**Отправить сообщение от имени агента:**")

            # Выбор агента
            agent_names = [a['name'] for a in agents]
            selected_agent = st.selectbox("Выберите агента", agent_names)

            # Находим выбранного агента
            selected = next((a for a in agents if a['name'] == selected_agent), None)

            if selected:
                agent_message = st.text_input("Сообщение от агента", key="agent_chat_input")

                if st.button("📤 Отправить от агента"):
                    if agent_message:
                        with st.spinner("Отправка..."):
                            api.send_to_chat(selected['id'], agent_message)
                        st.rerun()
        else:
            st.info("Сначала создайте агентов")

    # Кнопка очистки чата
    if st.button("🧹 Очистить чат"):
        api.clear_chat()
        st.rerun()