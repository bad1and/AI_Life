import time
import streamlit as st
import requests


def render_chat_history(agent_id: str, agent_name: str, api):
    """Отображение истории чата с агентом"""

    # Получаем историю
    try:
        response = requests.get(f"{api.base_url}/agents/{agent_id}/history")
        if response.ok:
            data = response.json()
            history = data.get('history', [])

            if history:
                st.markdown("### 📜 История разговора")

                # Показываем последние 10 сообщений
                for msg in history[-10:]:
                    if msg['role'] == 'user':
                        st.markdown(f"👤 **Вы:** {msg['content']}")
                    else:
                        st.markdown(f"🤖 **{agent_name}:** {msg['content']}")
                    st.caption(f"🕐 {time.strftime('%H:%M:%S', time.localtime(msg['timestamp']))}")
                    st.divider()

                # Кнопка очистки истории
                if st.button(f"🧹 Очистить историю {agent_name}", key=f"clear_{agent_id}"):
                    requests.post(f"{api.base_url}/agents/{agent_id}/history/clear")
                    st.rerun()
            else:
                st.info("📭 История пуста")
    except:
        st.warning("Не удалось загрузить историю")