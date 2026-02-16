import streamlit as st


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

        with st.expander("💬 Написать"):
            msg = st.text_input("Сообщение", key=f"msg_{agent['id']}")
            if st.button("Отправить", key=f"btn_{agent['id']}"):
                resp = api.send_message(agent['id'], msg)
                if resp:
                    st.success(f"Ответ: {resp.get('reply', '')}")