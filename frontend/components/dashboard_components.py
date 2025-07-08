"""
Componentes adicionais para o Dashboard Profissional
Inclui widgets customizados e funcionalidades avançadas
"""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta


def create_kpi_card(title, value, icon, color="#667eea", delta=None, delta_color="normal"):
    """Cria um card KPI profissional"""
    delta_html = ""
    if delta is not None:
        delta_color_map = {
            "normal": "#28a745",
            "inverse": "#dc3545",
            "off": "#6c757d"
        }
        color_code = delta_color_map.get(delta_color, "#28a745")
        arrow = "↗" if delta > 0 else "↘" if delta < 0 else "→"
        delta_html = f'<div style="color: {color_code}; font-size: 0.9rem; margin-top: 0.5rem;">{arrow} {delta:+.1f}%</div>'

    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {color} 0%, {color}dd 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
        transition: transform 0.2s ease;
    " onmouseover="this.style.transform='translateY(-3px)'" onmouseout="this.style.transform='translateY(0)'">
        <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">{icon}</div>
        <div style="font-size: 2.2rem; font-weight: 700; margin-bottom: 0.3rem;">{value}</div>
        <div style="font-size: 0.9rem; opacity: 0.9; text-transform: uppercase; letter-spacing: 1px;">{title}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


def create_progress_ring(percentage, title, color="#667eea"):
    """Cria um anel de progresso circular"""
    fig = go.Figure(data=[go.Pie(
        values=[percentage, 100-percentage],
        hole=0.7,
        marker_colors=[color, '#f8f9fa'],
        textinfo='none',
        hoverinfo='none',
        showlegend=False
    )])

    fig.update_layout(
        annotations=[dict(text=f'{percentage}%', x=0.5,
                          y=0.5, font_size=20, showarrow=False)],
        height=200,
        margin=dict(t=0, b=0, l=0, r=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    st.plotly_chart(fig, use_container_width=True)
    st.markdown(f"<div style='text-align: center; margin-top: -1rem; font-weight: 500;'>{title}</div>",
                unsafe_allow_html=True)


def create_timeline_chart(data, title="Timeline"):
    """Cria um gráfico de timeline interativo"""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=data['date'],
        y=data['value'],
        mode='lines+markers',
        line=dict(color='#667eea', width=3),
        marker=dict(size=8, color='#667eea'),
        fill='tonexty',
        fillcolor='rgba(102, 126, 234, 0.1)'
    ))

    fig.update_layout(
        title=title,
        xaxis_title="Data",
        yaxis_title="Valor",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_family="Inter",
        title_font_size=16,
        showlegend=False,
        height=300
    )

    fig.update_xaxis(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.1)')
    fig.update_yaxis(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.1)')

    return fig


def create_heatmap_calendar(data, title="Atividade"):
    """Cria um heatmap de calendário"""
    # Simular dados de heatmap
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
    values = [abs(hash(str(d)) % 10) for d in dates]

    fig = go.Figure(data=go.Heatmap(
        z=[values[i:i+7] for i in range(0, len(values), 7)],
        colorscale='Blues',
        showscale=False
    ))

    fig.update_layout(
        title=title,
        height=200,
        margin=dict(t=30, b=0, l=0, r=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_family="Inter"
    )

    return fig


def create_status_distribution(data):
    """Cria gráfico de distribuição de status"""
    colors = ['#28a745', '#ffc107', '#dc3545', '#6c757d']

    fig = go.Figure(data=[go.Pie(
        labels=list(data.keys()),
        values=list(data.values()),
        hole=0.4,
        marker_colors=colors[:len(data)],
        textinfo='label+percent',
        textposition='outside'
    )])

    fig.update_layout(
        title="Distribuição de Status",
        height=300,
        margin=dict(t=50, b=0, l=0, r=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_family="Inter",
        showlegend=False
    )

    return fig


def create_conversation_flow():
    """Cria um fluxograma de conversas"""
    fig = go.Figure()

    # Nodes
    node_x = [0, 1, 2, 1, 2]
    node_y = [0, 0, 0, -1, -1]
    node_text = ['Início', 'Bot', 'Resolvido', 'Humano', 'Finalizado']
    node_colors = ['#667eea', '#28a745', '#17a2b8', '#ffc107', '#6c757d']

    for i, (x, y, text, color) in enumerate(zip(node_x, node_y, node_text, node_colors)):
        fig.add_trace(go.Scatter(
            x=[x], y=[y],
            mode='markers+text',
            marker=dict(size=50, color=color),
            text=text,
            textposition='middle center',
            textfont=dict(color='white', size=10),
            showlegend=False,
            hoverinfo='none'
        ))

    # Edges
    edges = [(0, 1), (1, 2), (1, 3), (3, 4)]
    for start, end in edges:
        fig.add_trace(go.Scatter(
            x=[node_x[start], node_x[end]],
            y=[node_y[start], node_y[end]],
            mode='lines',
            line=dict(color='#dee2e6', width=2),
            showlegend=False,
            hoverinfo='none'
        ))

    fig.update_layout(
        title="Fluxo de Conversas",
        height=250,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_family="Inter",
        margin=dict(t=50, b=0, l=0, r=0)
    )

    return fig


def create_real_time_metrics():
    """Cria seção de métricas em tempo real"""
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        margin-bottom: 2rem;
    ">
        <h3 style="margin: 0 0 1rem 0; text-align: center;">📊 Métricas em Tempo Real</h3>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
            <div style="text-align: center;">
                <div style="font-size: 2rem; font-weight: bold;">🟢 Online</div>
                <div style="opacity: 0.9;">Status do Bot</div>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 2rem; font-weight: bold;">3</div>
                <div style="opacity: 0.9;">Conversas Ativas</div>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 2rem; font-weight: bold;">1.2s</div>
                <div style="opacity: 0.9;">Tempo Resposta</div>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 2rem; font-weight: bold;">98%</div>
                <div style="opacity: 0.9;">Uptime</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def create_advanced_filters():
    """Cria filtros avançados"""
    with st.expander("🔍 Filtros Avançados", expanded=False):
        col1, col2, col3 = st.columns(3)

        with col1:
            st.selectbox("Sentimento", [
                         "Todos", "Positivo", "Neutro", "Negativo"])
            st.selectbox("Origem", ["Todas", "WhatsApp", "Telegram", "Web"])

        with col2:
            st.slider("Duração (min)", 0, 60, (0, 30))
            st.selectbox("Resolvido por", ["Todos", "Bot", "Humano", "Misto"])

        with col3:
            st.multiselect("Tags", ["Urgente", "VIP", "Reclamação", "Elogio"])
            st.selectbox(
                "Idioma", ["Todos", "Português", "Inglês", "Espanhol"])


def create_export_section():
    """Cria seção de exportação"""
    st.markdown("### 📥 Exportar Dados")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📊 Relatório Excel", type="secondary"):
            st.success("Relatório Excel gerado!")

    with col2:
        if st.button("📄 Relatório PDF", type="secondary"):
            st.success("Relatório PDF gerado!")

    with col3:
        if st.button("📋 Dados CSV", type="secondary"):
            st.success("Dados CSV exportados!")


def create_notification_center():
    """Cria centro de notificações"""
    notifications = [
        {"type": "info", "message": "5 novas conversas hoje", "time": "2 min atrás"},
        {"type": "warning", "message": "Tempo de resposta acima da média",
            "time": "15 min atrás"},
        {"type": "success", "message": "Meta de satisfação atingida", "time": "1h atrás"},
    ]

    st.markdown("### 🔔 Notificações")

    for notif in notifications:
        icon_map = {"info": "ℹ️", "warning": "⚠️", "success": "✅"}
        color_map = {"info": "#17a2b8",
                     "warning": "#ffc107", "success": "#28a745"}

        st.markdown(f"""
        <div style="
            background: white;
            border-left: 4px solid {color_map[notif['type']]};
            padding: 1rem;
            margin-bottom: 0.5rem;
            border-radius: 0 8px 8px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        ">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span>{icon_map[notif['type']]} {notif['message']}</span>
                <small style="color: #6c757d;">{notif['time']}</small>
            </div>
        </div>
        """, unsafe_allow_html=True)


def create_quick_actions():
    """Cria seção de ações rápidas"""
    st.markdown("### ⚡ Ações Rápidas")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔄 Reiniciar Bot", type="primary"):
            st.success("Bot reiniciado!")
        if st.button("📢 Enviar Broadcast"):
            st.info("Abrindo editor de broadcast...")

    with col2:
        if st.button("🛠️ Modo Manutenção"):
            st.warning("Modo manutenção ativado!")
        if st.button("📊 Gerar Relatório"):
            st.success("Relatório sendo gerado...")

# Função para aplicar tema escuro


def apply_dark_theme():
    """Aplica tema escuro ao dashboard"""
    st.markdown("""
    <style>
        .stApp {
            background-color: #1e1e1e;
            color: #ffffff;
        }
        
        .main-header {
            background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%);
        }
        
        .metric-card {
            background: #2d3748;
            border: 1px solid #4a5568;
            color: #ffffff;
        }
        
        .conversation-card {
            background: #2d3748;
            border: 1px solid #4a5568;
            color: #ffffff;
        }
        
        .message-bot {
            background: #4a5568;
            color: #ffffff;
        }
    </style>
    """, unsafe_allow_html=True)
