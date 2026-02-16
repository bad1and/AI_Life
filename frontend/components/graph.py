import streamlit as st
import plotly.graph_objects as go


def render_graph(graph_data):
    if not graph_data['nodes']:
        st.info("Нет агентов для отображения")
        return

    fig = go.Figure()

    # Узлы
    fig.add_trace(go.Scatter(
        x=[i for i in range(len(graph_data['nodes']))],
        y=[1] * len(graph_data['nodes']),
        mode='markers+text',
        text=[n['name'] for n in graph_data['nodes']],
        marker=dict(
            size=30,
            color=[n.get('mood', 0.5) for n in graph_data['nodes']],
            colorscale='RdYlGn',
            showscale=True
        )
    ))

    fig.update_layout(
        title="Агенты",
        showlegend=False,
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)