import streamlit as st
import time
from .chat_history import render_chat_history


def agent_card(agent, api):
    with st.container():
        col1, col2 = st.columns([1, 3])

        with col1:
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
        tab1, tab2, tab3 = st.tabs(["💬 Чат", "📜 История", "⚙️ Управление"])

        with tab1:
            msg = st.text_input("Сообщение", key=f"msg_{agent['id']}")
            if st.button("Отправить", key=f"btn_{agent['id']}"):
                if msg:
                    with st.spinner("🤔 Агент думает..."):
                        resp = api.send_message(agent['id'], msg)
                        if resp:
                            st.success(f"Ответ: {resp.get('reply', '')}")

        with tab2:
            render_chat_history(agent['id'], agent['name'], api)

        with tab3:
            st.markdown("**Опасная зона**")
            if st.button(f"🗑️ Удалить {agent['name']}", key=f"delete_{agent['id']}"):
                api.delete_agent(agent['id'])
                st.success(f"{agent['name']} удален! Нажмите кнопку ниже для обновления.")

            if st.button("🔄 Обновить список агентов", key=f"refresh_{agent['id']}"):
                st.rerun()