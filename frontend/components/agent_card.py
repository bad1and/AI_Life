import streamlit as st
import time
from .chat_history import render_chat_history


def agent_card(agent, api):
    with st.container():
        col1, col2 = st.columns([1, 3])

        with col1:
            # Эмодзи настроения
            if agent['mood'] > 0.7:
                st.markdown("# 😊")
            elif agent['mood'] < 0.3:
                st.markdown("# 😢")
            else:
                st.markdown("# 😐")

        with col2:
            st.markdown(f"**{agent['name']}**")
            st.caption(f"🎭 {agent['personality']}")
            st.caption(f"📍 {agent.get('location', 'общая зона')}")
            st.caption(f"😊 Настроение: {agent['mood']:.2f}")

        # Вкладки в карточке
        tab1, tab2 = st.tabs(["💬 Чат", "📜 История"])

        with tab1:
            # Используем session_state для хранения ответа
            reply_key = f"last_reply_{agent['id']}"

            # Поле ввода
            msg = st.text_input("Сообщение", key=f"msg_{agent['id']}")

            # Кнопка отправки
            if st.button("Отправить", key=f"btn_{agent['id']}"):
                if msg:  # Проверяем что сообщение не пустое
                    with st.spinner("🤔 Агент думает..."):
                        resp = api.send_message(agent['id'], msg)
                        if resp:
                            # Сохраняем ответ в session_state
                            st.session_state[reply_key] = {
                                'text': resp.get('reply', ''),
                                'time': time.time()
                            }
                            # НЕ ДЕЛАЕМ rerun() - просто обновляем состояние

            # Показываем ответ если он есть
            if reply_key in st.session_state:
                reply = st.session_state[reply_key]
                # Показываем ответ в красивом контейнере
                with st.container():
                    st.markdown("---")
                    st.markdown("**🤖 Ответ:**")
                    st.success(reply['text'])
                    # Кнопка чтобы скрыть ответ
                    if st.button("✖️ Скрыть", key=f"hide_{agent['id']}"):
                        del st.session_state[reply_key]
                        st.rerun()

        with tab2:
            render_chat_history(agent['id'], agent['name'], api)