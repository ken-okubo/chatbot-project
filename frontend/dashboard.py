"""
Dashboard CORRIGIDO - Business Type e ID Completo
Correção dos bugs identificados
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import html
from datetime import datetime, timedelta
from collections import defaultdict
import pytz

BRAZIL_TZ = pytz.timezone('America/Sao_Paulo')
UTC = pytz.UTC


def convert_utc_to_brazil(utc_timestamp):
    """
    Converte timestamp UTC para horário do Brasil
    Aceita string ISO, datetime ou None
    """
    if not utc_timestamp:
        return None

    try:
        # Se é string, converter para datetime
        if isinstance(utc_timestamp, str):
            if 'T' in utc_timestamp:
                # Formato ISO com timezone
                dt = datetime.fromisoformat(
                    utc_timestamp.replace('Z', '+00:00'))
            else:
                # Formato simples, assumir UTC
                dt = datetime.strptime(utc_timestamp, '%Y-%m-%d %H:%M:%S')
                dt = UTC.localize(dt)
        else:
            # Se já é datetime
            dt = utc_timestamp
            if dt.tzinfo is None:
                dt = UTC.localize(dt)

        # Converter para Brasil
        return dt.astimezone(BRAZIL_TZ)
    except Exception as e:
        print(f"Erro ao converter timestamp {utc_timestamp}: {e}")
        return None


def format_timestamp_brazil(timestamp):
    """Formata timestamp para exibição brasileira"""
    brazil_time = convert_utc_to_brazil(timestamp)
    if brazil_time:
        return brazil_time.strftime("%d/%m/%Y %H:%M")
    return "Não Informado"


def format_time_brazil(timestamp):
    """Formata apenas o horário (para gráficos)"""
    brazil_time = convert_utc_to_brazil(timestamp)
    if brazil_time:
        return brazil_time.strftime("%H:%M")
    return None


def get_hour_brazil(timestamp):
    """Retorna a hora no timezone Brasil (0-23)"""
    brazil_time = convert_utc_to_brazil(timestamp)
    if brazil_time:
        return brazil_time.hour
    return None


def get_date_brazil(timestamp):
    """Retorna a data no timezone Brasil"""
    brazil_time = convert_utc_to_brazil(timestamp)
    if brazil_time:
        return brazil_time.date()
    return None


def get_sentiment_badge(sentiment, score=None):
    """Retorna badge HTML para sentiment"""
    if not sentiment:
        return '<span class="sentiment-badge sentiment-unknown">❓ Indefinido</span>'

    mapping = {
        "POSITIVO": ("😊 Positivo", "sentiment-positive"),
        "NEUTRO": ("😐 Neutro", "sentiment-neutral"),
        "NEGATIVO": ("😠 Negativo", "sentiment-negative")
    }

    text, css_class = mapping.get(
        sentiment, ("❓ Indefinido", "sentiment-unknown"))

    # Adicionar score se disponível
    if score is not None:
        text += f" ({score:.2f})"

    return f'<span class="sentiment-badge {css_class}">{text}</span>'


# Configuração da página
st.set_page_config(
    page_title="Chatbot Dashboard",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS profissional com BADGE para business_type
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    /* Header principal */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }

    .main-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }

    .main-header p {
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
        opacity: 0.9;
    }

    /* Cards de métricas */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        border: 1px solid #f0f0f0;
        text-align: center;
        transition: transform 0.2s ease;
    }

    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(0,0,0,0.12);
    }

    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #2c3e50;
        margin: 0;
    }

    .metric-label {
        font-size: 0.9rem;
        color: #7f8c8d;
        margin: 0.5rem 0 0 0;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .metric-icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
    }

    /* Status badges */
    .status-badge {
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-right: 0.5rem;
        display: inline-block;
    }

    .status-open {
        background: #d4edda;
        color: #155724;
    }

    .status-closed {
        background: #f8d7da;
        color: #721c24;
    }

    .needs-human-yes {
        background: #fff3cd;
        color: #856404;
    }

    .needs-human-no {
        background: #d1ecf1;
        color: #0c5460;
    }

    /* Business type badges - CORRIGIDOS */
    .business-delivery {
        background: #fff3cd;
        color: #856404;
    }

    .business-mecanica {
        background: #d1ecf1;
        color: #0c5460;
    }

    .business-farmacia {
        background: #d4edda;
        color: #155724;
    }

    .business-unknown {
        background: #f8d7da;
        color: #721c24;
    }

    /* Container integrado para conversa */
    .conversation-container {
        background: white;
        border: 1px solid #e9ecef;
        border-radius: 12px;
        margin-bottom: 0.5rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        transition: all 0.2s ease;
        overflow: hidden;
    }

    .conversation-container:hover {
        border-color: #667eea;
        box-shadow: 0 4px 20px rgba(102, 126, 234, 0.1);
    }

    .conversation-header {
        padding: 1.5rem;
        border-bottom: 1px solid #f8f9fa;
    }

    .conversation-title {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
    }

    .phone-number {
        font-size: 1.1rem;
        font-weight: 600;
        color: #2c3e50;
    }

    .conversation-meta {
        display: flex;
        gap: 1rem;
        font-size: 0.9rem;
        color: #6c757d;
        flex-wrap: wrap;
    }

    /* Expander customizado integrado */
    .stExpander {
        border: none !important;
        box-shadow: none !important;
        background: transparent !important;
        margin-top: 0 !important;
        margin-bottom: 0.5rem !important;
    }

    .stExpander > div:first-child {
        border: none !important;
        background: #f8f9fa !important;
        border-top: 1px solid #e9ecef !important;
        margin: 0 !important;
        padding: 0.75rem 1rem !important;
    }

    .stExpander > div:first-child:hover {
        background: #e9ecef !important;
    }

    .stExpander > div:last-child {
        border: none !important;
        background: white !important;
        padding: 1rem !important;
        margin: 0 !important;
    }

    /* Bubbles de mensagem */
    .message-bubble {
        max-width: 80%;
        padding: 1rem;
        border-radius: 18px;
        margin: 0.5rem 0;
        position: relative;
        word-wrap: break-word;
    }

    .message-user {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin-left: auto;
        border-bottom-right-radius: 4px;
    }

    .message-bot {
        background: #f8f9fa;
        color: #2c3e50;
        border: 1px solid #e9ecef;
        border-bottom-left-radius: 4px;
    }

    .message-timestamp {
        font-size: 0.75rem;
        opacity: 0.7;
        margin-top: 0.5rem;
    }

    /* 🌡️ SENTIMENT BADGES */
    .sentiment-badge {
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 500;
        margin-left: 8px;
    }

    .sentiment-positive {
        background: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
    }

    .sentiment-neutral {
        background: #fff3cd;
        color: #856404;
        border: 1px solid #ffeaa7;
    }

    .sentiment-negative {
        background: #f8d7da;
        color: #721c24;
        border: 1px solid #f5c6cb;
    }

    .sentiment-unknown {
        background: #e2e3e5;
        color: #6c757d;
        border: 1px solid #d6d8db;
    }

    /* Responsivo */
    @media (max-width: 768px) {
        .main-header h1 {
            font-size: 2rem;
        }

        .metric-card {
            padding: 1rem;
        }

        .metric-value {
            font-size: 2rem;
        }

        .conversation-meta {
            flex-direction: column;
            gap: 0.5rem;
        }

        .conversation-title {
            flex-direction: column;
            align-items: flex-start;
            gap: 0.5rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# Configurações da API
API_BASE_URL = "http://localhost:8000"

# Dicionário de tradução para termos em inglês
TRANSLATIONS = {
    # Status
    "open": "Aberta",
    "closed": "Fechada",
    "pending": "Pendente",
    "active": "Ativa",
    "inactive": "Inativa",

    # Business Types
    "delivery": "Delivery",
    "mecanica": "Mecânica",
    "farmacia": "Farmácia",
    "unknown": "Indefinido",
    "undefined": "Indefinido",

    # Needs Human
    "true": "Atendimento Humano",
    "false": "Resolvido pelo Bot",

    # Valores None/Null
    "none": "Não Informado",
    "null": "Não Informado",
    "": "Não Informado",

    # Outros termos comuns
    "yes": "Sim",
    "no": "Não",
    "error": "Erro",
    "success": "Sucesso",
    "failed": "Falhou",
    "completed": "Concluído"
}


def translate_term(term):
    """Traduz termos em inglês para português"""
    if not term:
        return "Não Informado"

    term_lower = str(term).lower().strip()
    return TRANSLATIONS.get(term_lower, str(term).title())

# Cache para performance


@st.cache_data(ttl=60)
def fetch_conversations(params=None):
    """Busca conversas da API"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/admin/conversations", params=params or {})
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Erro ao carregar conversas: {e}")
        return []


@st.cache_data(ttl=60)
def fetch_messages(conversation_id):
    """Busca mensagens de uma conversa"""
    try:
        response = requests.get(f"{API_BASE_URL}/admin/messages",
                                params={"conversation_id": conversation_id})
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Erro ao carregar mensagens: {e}")
        return []


@st.cache_data(ttl=60)
def fetch_all_messages(params=None):
    """Busca todas as mensagens para análise temporal - CORRIGIDO"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/admin/messages/all", params=params or {})
        response.raise_for_status()
        return response.json()
    except Exception as e:
        # Se não existir endpoint específico, buscar de todas as conversas
        conversations = fetch_conversations(params)
        all_messages = []
        for conv in conversations:
            messages = fetch_messages(conv.get('id'))
            # CORREÇÃO: Adicionar business_type da conversa às mensagens
            for msg in messages:
                msg['conversation_business_type'] = conv.get(
                    'business_type', 'unknown')
            all_messages.extend(messages)
        return all_messages


def format_timestamp(ts):
    """Formata timestamp para exibição brasileira"""
    if ts:
        try:
            if 'T' in str(ts):
                dt = datetime.fromisoformat(str(ts).replace('Z', '+00:00'))
            else:
                dt = datetime.strptime(str(ts), '%Y-%m-%d %H:%M:%S')
            return dt.strftime("%d/%m/%Y %H:%M")
        except:
            return str(ts)
    return "Não Informado"


def get_status_badge(status):
    """Retorna badge HTML para status"""
    status_translated = translate_term(status)

    if status == "open":
        return f'<span class="status-badge status-open">{status_translated}</span>'
    elif status == "closed":
        return f'<span class="status-badge status-closed">{status_translated}</span>'
    else:
        return f'<span class="status-badge status-open">{status_translated}</span>'


def get_needs_human_badge(needs_human):
    """Retorna badge para needs_human com texto melhorado"""
    if needs_human:
        return '<span class="status-badge needs-human-yes">🆘 Atendimento Humano</span>'
    else:
        return '<span class="status-badge needs-human-no">✅ Resolvido pelo Bot</span>'


def get_business_type_badge(business_type):
    """Retorna badge HTML para business_type - CORRIGIDO"""
    mapping = {
        "delivery": ("🍕 Delivery", "business-delivery"),
        "mecanica": ("🔧 Mecânica", "business-mecanica"),
        "farmacia": ("💊 Farmácia", "business-farmacia"),
        "unknown": ("❓ Indefinido", "business-unknown"),
        "undefined": ("❓ Indefinido", "business-unknown"),
        "none": ("❓ Não Informado", "business-unknown"),
        "null": ("❓ Não Informado", "business-unknown"),
        "": ("❓ Não Informado", "business-unknown")
    }

    if not business_type:
        text, css_class = ("❓ Não Informado", "business-unknown")
    else:
        business_lower = str(business_type).lower().strip()
        text, css_class = mapping.get(
            business_lower, (f"📋 {translate_term(business_type)}", "business-unknown"))

    return f'<span class="status-badge {css_class}">{text}</span>'


def calculate_conversation_duration(start_time, end_time):
    """Calcula duração da conversa - CORRIGIDO PARA BRASIL"""
    if not start_time:
        return "Não Informado"

    try:
        # Converter para horário do Brasil
        start_brazil = convert_utc_to_brazil(start_time)
        if not start_brazil:
            return "Não Informado"

        if end_time:
            end_brazil = convert_utc_to_brazil(end_time)
            if not end_brazil:
                return "Não Informado"
            duration = end_brazil - start_brazil
        else:
            # Conversa ainda aberta - usar horário atual do Brasil
            now_brazil = datetime.now(BRAZIL_TZ)
            duration = now_brazil - start_brazil

        total_minutes = int(duration.total_seconds() / 60)
        if total_minutes < 60:
            return f"{total_minutes}min"
        else:
            hours = total_minutes // 60
            minutes = total_minutes % 60
            return f"{hours}h {minutes}min" + ("" if end_time else " (em andamento)")

    except Exception as e:
        return "Não Informado"


def render_conversation_integrated(conv, messages):
    """Renderiza conversa com UX integrada e botões organizados à esquerda"""

    # Calcular estatísticas da conversa
    total_messages = len(messages)
    user_messages = len([m for m in messages if m.get('from_user', True)])
    bot_messages = total_messages - user_messages
    duration = calculate_conversation_duration(
        conv.get('start_time'), conv.get('end_time'))

    # ID completo da conversa
    conversation_id = str(conv.get('id', 'N/A'))
    sentiment_badge = get_sentiment_badge(
        conv.get('sentiment'), conv.get('sentiment_score'))

    # Container integrado
    st.markdown(f"""
    <div class="conversation-container">
        <div class="conversation-header">
            <div class="conversation-title">
                <div class="phone-number">📱 {conv.get('user_number', 'Não Informado')}</div>
                <div>
                    {get_status_badge(conv.get('status', 'unknown'))}
                    {get_business_type_badge(
                        conv.get('business_type', 'unknown'))}
                    {get_needs_human_badge(conv.get('needs_human', False))}
                    {sentiment_badge}
                </div>
            </div>
            <div class="conversation-meta">
                <span>🕐 Início: {format_timestamp(conv.get('start_time'))}</span>
                <span>🏁 Fim: {format_timestamp(conv.get('end_time')) if conv.get('end_time') else 'Em andamento'}</span>
                <span>⏱️ Duração: {duration}</span>
                <span>💬 {total_messages} mensagens ({user_messages} cliente, {bot_messages} bot)</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Expander integrado com botões organizados
    with st.expander(f"💬 Ver Mensagens (ID da Conversa: {conversation_id})", expanded=False):

        # CSS para botões organizados à esquerda
        st.markdown("""
        <style>
        .download-section {
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            border-left: 4px solid #667eea;
        }
        .download-buttons {
            display: flex;
            gap: 1rem;
            align-items: center;
            flex-wrap: wrap;
        }
        .download-info {
            color: #6c757d;
            font-size: 0.9rem;
            margin-top: 0.5rem;
        }
        </style>
        """, unsafe_allow_html=True)

        # Seção de downloads organizada
        st.markdown("""
        <div class="download-section">
            <h4 style="margin: 0 0 0.5rem 0; color: #2c3e50;">📥 Downloads da Conversa</h4>
            <div class="download-info">
                💡 Use CSV para análise em Excel e PDF para relatórios formais
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Botões organizados à esquerda
        col1, col2, col3 = st.columns([1, 1, 3])

        with col1:
            if st.button("📊 Baixar CSV", key=f"csv_{conversation_id}", help="Download em formato CSV para Excel"):
                try:
                    # URL CORRIGIDA com /admin
                    csv_url = f"{API_BASE_URL}/admin/conversations/{conversation_id}/download/csv"

                    with st.spinner("Gerando CSV..."):
                        response = requests.get(csv_url)
                        response.raise_for_status()

                        # Nome do arquivo
                        user_number = conv.get(
                            'user_number', 'unknown').replace('+', '')
                        filename = f"conversa_{user_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

                        # Download direto
                        st.download_button(
                            label="⬇️ Clique para baixar CSV",
                            data=response.content,
                            file_name=filename,
                            mime="text/csv",
                            key=f"download_csv_{conversation_id}"
                        )
                        st.success("✅ CSV gerado com sucesso!")

                except Exception as e:
                    st.error(f"❌ Erro ao gerar CSV: {str(e)}")

        with col2:
            if st.button("📄 Baixar PDF", key=f"pdf_{conversation_id}", help="Download em formato PDF para relatórios"):
                try:
                    # URL CORRIGIDA com /admin
                    pdf_url = f"{API_BASE_URL}/admin/conversations/{conversation_id}/download/pdf"

                    with st.spinner("Gerando PDF..."):
                        response = requests.get(pdf_url)
                        response.raise_for_status()

                        # Nome do arquivo
                        user_number = conv.get(
                            'user_number', 'unknown').replace('+', '')
                        filename = f"conversa_{user_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

                        # Download direto
                        st.download_button(
                            label="⬇️ Clique para baixar PDF",
                            data=response.content,
                            file_name=filename,
                            mime="application/pdf",
                            key=f"download_pdf_{conversation_id}"
                        )
                        st.success("✅ PDF gerado com sucesso!")

                except Exception as e:
                    st.error(f"❌ Erro ao gerar PDF: {str(e)}")

        with col3:
            # Informações adicionais
            st.markdown(f"""
            <div style="
                background: white;
                padding: 0.75rem;
                border-radius: 6px;
                border: 1px solid #dee2e6;
                font-size: 0.85rem;
                color: #6c757d;
            ">
                <strong>📋 Informações:</strong><br>
                • ID: {conversation_id}<br>
                • Mensagens: {total_messages} ({user_messages} cliente, {bot_messages} bot)<br>
                • Duração: {duration}
            </div>
            """, unsafe_allow_html=True)

        # Separador
        st.markdown("---")

        # Mensagens (resto da função continua igual)
        if messages:
            render_messages(messages)
        else:
            st.info("Nenhuma mensagem encontrada para esta conversa")


def render_messages(messages):
    """Renderiza mensagens da conversa em formato de chat"""
    if not messages:
        st.info("Nenhuma mensagem encontrada")
        return

    # Ordenar mensagens por timestamp
    sorted_messages = sorted(messages, key=lambda x: x.get('timestamp', ''))

    for msg in sorted_messages:
        is_user = msg.get('from_user', True)
        content = html.escape(
            str(msg.get('content', 'Sem conteúdo'))).replace('\n', '<br>')
        timestamp_brazil = format_timestamp_brazil(msg.get('timestamp'))
        message_id = str(msg.get('id', 'N/A'))

        bubble_class = "message-user" if is_user else "message-bot"
        icon = "👤" if is_user else "🤖"
        sender = "Cliente" if is_user else "Bot"

        st.markdown(f"""
        <div class="message-bubble {bubble_class}">
            <strong>{icon} {sender}</strong><br>
            {content}
            <div class="message-timestamp">{timestamp_brazil} • ID da Mensagem: {message_id}</div>
        </div>
        """, unsafe_allow_html=True)


def render_hourly_messages_chart(conversations, date_range):
    """Renderiza gráfico de mensagens recebidas por hora, separado por business_type - CORRIGIDO"""

    # Buscar todas as mensagens do período
    params = {}
    if len(date_range) == 2:
        params["start_date"] = date_range[0].isoformat()
        params["end_date"] = date_range[1].isoformat()

    all_messages = fetch_all_messages(params)

    if not all_messages:
        st.info("Nenhuma mensagem encontrada para o período selecionado")
        return

    # Organizar dados por hora e business_type - CORRIGIDO
    hourly_data = defaultdict(lambda: defaultdict(int))

    for msg in all_messages:
        try:
            # Extrair hora da mensagem
            timestamp = msg.get('timestamp')
            if timestamp:
                hour_brazil = get_hour_brazil(timestamp)
                if hour_brazil is not None:
                    business_type = msg.get(
                        'conversation_business_type') or 'unknown'
                    business_type_display = translate_term(business_type)
                    hourly_data[business_type_display][hour_brazil] += 1
        except Exception as e:
            # Debug: mostrar erro se necessário
            continue

    if not hourly_data:
        st.info("Não foi possível processar os dados de mensagens por hora")
        return

    # Criar DataFrame para o gráfico
    chart_data = []
    hours = list(range(24))  # 0-23

    for business_type, hour_counts in hourly_data.items():
        for hour in hours:
            chart_data.append({
                'Hora': hour,
                'Mensagens': hour_counts.get(hour, 0),
                'Tipo de Negócio': business_type
            })

    df = pd.DataFrame(chart_data)

    # Debug: mostrar dados se necessário
    if st.checkbox("🔍 Debug: Mostrar dados do gráfico"):
        st.write("Dados processados:")
        st.write(df.groupby('Tipo de Negócio')['Mensagens'].sum())

    # Criar gráfico de linha
    fig = px.line(
        df,
        x='Hora',
        y='Mensagens',
        color='Tipo de Negócio',
        title='📈 Mensagens Recebidas por Hora do Dia',
        markers=True,
        color_discrete_sequence=['#667eea', '#764ba2',
                                 '#28a745', '#ffc107', '#dc3545']
    )

    # Customizar o gráfico
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_family="Inter",
        height=400,
        xaxis_title="Hora do Dia",
        yaxis_title="Número de Mensagens Recebidas",
        legend_title="Tipo de Negócio",
        hovermode='x unified'
    )

    # Configurar eixo X para mostrar todas as horas
    fig.update_xaxes(
        tickmode='linear',
        tick0=0,
        dtick=2,  # Mostrar a cada 2 horas
        range=[0, 23]
    )

    # Configurar hover
    fig.update_traces(
        hovertemplate='<b>%{fullData.name}</b><br>' +
                      'Hora (Brasil): %{x}:00<br>' +
                      'Mensagens: %{y}<br>' +
                      '<extra></extra>'
    )

    st.plotly_chart(fig, use_container_width=True)
    st.markdown("""
    <div class="timezone-info">
        <strong>ℹ️ Informação sobre Horários:</strong><br>
        Todos os horários exibidos estão no <strong>fuso horário do Brasil (UTC-3)</strong>.<br>
        Os dados são convertidos automaticamente do UTC para facilitar a análise.
    </div>
    """, unsafe_allow_html=True)

    # Mostrar insights
    total_messages = df['Mensagens'].sum()
    if total_messages > 0:
        peak_hour = df.groupby('Hora')['Mensagens'].sum().idxmax()
        peak_count = df.groupby('Hora')['Mensagens'].sum().max()

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("📊 Total de Mensagens", f"{total_messages:,}")

        with col2:
            st.metric("⏰ Horário de Pico", f"{peak_hour}:00h")

        with col3:
            st.metric("📈 Mensagens no Pico", f"{peak_count}")


def render_simple_analytics(conversations):
    """Renderiza analytics simples baseados nos dados reais"""

    if not conversations:
        st.warning("Nenhuma conversa encontrada para análise")
        return

    # Calcular métricas básicas
    total_conversations = len(conversations)
    open_conversations = len(
        [c for c in conversations if c.get('status') == 'open'])
    closed_conversations = len(
        [c for c in conversations if c.get('status') == 'closed'])
    needs_human = len(
        [c for c in conversations if c.get('needs_human', False)])

    # Distribuição por business_type
    business_types = {}
    for conv in conversations:
        bt = conv.get('business_type', 'unknown')
        business_types[bt] = business_types.get(bt, 0) + 1

    # KPIs principais
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">💬</div>
            <div class="metric-value">{total_conversations}</div>
            <div class="metric-label">Total Conversas</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">🟢</div>
            <div class="metric-value">{open_conversations}</div>
            <div class="metric-label">Conversas Abertas</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">✅</div>
            <div class="metric-value">{closed_conversations}</div>
            <div class="metric-label">Conversas Fechadas</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">🆘</div>
            <div class="metric-value">{needs_human}</div>
            <div class="metric-label">Precisam Humano</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Gráficos simples se houver dados suficientes
    if len(business_types) > 1:
        col1, col2 = st.columns(2)

        with col1:
            # Gráfico de distribuição por tipo de negócio
            fig = px.pie(
                values=list(business_types.values()),
                names=[translate_term(bt) for bt in business_types.keys()],
                title="Distribuição por Tipo de Negócio",
                color_discrete_sequence=['#667eea',
                                         '#764ba2', '#28a745', '#ffc107']
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_family="Inter",
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Gráfico de status
            status_data = {'Abertas': open_conversations,
                           'Fechadas': closed_conversations}
            if any(status_data.values()):
                fig = px.bar(
                    x=list(status_data.keys()),
                    y=list(status_data.values()),
                    title="Status das Conversas",
                    color=list(status_data.keys()),
                    color_discrete_map={
                        'Abertas': '#28a745', 'Fechadas': '#6c757d'}
                )
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_family="Inter",
                    showlegend=False,
                    height=300
                )
                st.plotly_chart(fig, use_container_width=True)


def main():
    """Função principal do dashboard"""

    # Header principal
    st.markdown("""
    <div class="main-header">
        <h1>💬 Dashboard do Chatbot WhatsApp</h1>
        <p>Monitore e gerencie suas conversas em tempo real (Horário do Brasil 🇧🇷)</p>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar com filtros baseados nos campos reais
    with st.sidebar:
        st.markdown("### 🔍 Filtros")

        # Filtro por número do usuário
        user_number = st.text_input(
            "📱 Número do Cliente", placeholder="Ex: 5511999999999")

        # Filtro por status (baseado no modelo)
        status_options = ["Todos", "open", "closed"]
        status_labels = ["Todos", "Abertas", "Fechadas"]
        status_selected = st.selectbox("📊 Status", status_labels)
        status = status_options[status_labels.index(
            status_selected)] if status_selected != "Todos" else None

        # Filtro por tipo de negócio (baseado no modelo)
        business_options = ["Todos", "delivery",
                            "mecanica", "farmacia", "unknown"]
        business_labels = ["Todos", "Delivery",
                           "Mecânica", "Farmácia", "Indefinido"]
        business_selected = st.selectbox("🏢 Tipo de Negócio", business_labels)
        business_type = business_options[business_labels.index(
            business_selected)] if business_selected != "Todos" else None

        # Filtro por needs_human (baseado no modelo)
        needs_human = st.checkbox(
            "🆘 Apenas conversas que precisam de atendimento humano")

        st.markdown("### 🌡️ Temperatura")
        sentiment_options = ["Todos", "POSITIVO", "NEUTRO", "NEGATIVO"]
        sentiment_selected = st.selectbox("😊 Sentiment", sentiment_options)
        sentiment = sentiment_selected if sentiment_selected != "Todos" else None

        # Filtro por período (baseado nos campos start_time/end_time)
        st.markdown("📅 **Período (Horário do Brasil)**")
        date_range = st.date_input(
            "Selecione o período",
            value=[datetime.now().date() - timedelta(days=7),
                   datetime.now().date()],
            max_value=datetime.now().date(),
            help="Os horários serão interpretados no fuso horário do Brasil (UTC-3)"
        )

        # Botão de atualizar
        if st.button("🔄 Atualizar", type="primary"):
            st.cache_data.clear()

        brazil_now = datetime.now(BRAZIL_TZ)
        st.markdown(f"""
        <div style="background: #f0f8ff; padding: 0.5rem; border-radius: 5px; margin-top: 1rem; font-size: 0.8rem;">
            🕐 <strong>Horário Atual (Brasil):</strong><br>
            {brazil_now.strftime('%d/%m/%Y %H:%M:%S')} (UTC-3)
        </div>
        """, unsafe_allow_html=True)

    # Construir parâmetros de filtro baseados nos campos reais
    params = {}
    if user_number:
        params["user_number"] = user_number
    if status:
        params["status"] = status
    if business_type:
        params["business_type"] = business_type
    if needs_human:
        params["needs_human"] = "true"
    if sentiment:
        params["sentiment"] = sentiment

    # Adicionar filtros de data se implementados na API
    if len(date_range) == 2:
        # Converter datas do Brasil para UTC para enviar para a API
        start_date_brazil = datetime.combine(
            date_range[0], datetime.min.time())
        end_date_brazil = datetime.combine(date_range[1], datetime.max.time())

        # Localizar no timezone Brasil e converter para UTC
        start_date_brazil = BRAZIL_TZ.localize(start_date_brazil)
        end_date_brazil = BRAZIL_TZ.localize(end_date_brazil)

        start_date_utc = start_date_brazil.astimezone(UTC)
        end_date_utc = end_date_brazil.astimezone(UTC)

        params["start_date"] = start_date_utc.isoformat()
        params["end_date"] = end_date_utc.isoformat()

    # Carregar conversas
    with st.spinner("Carregando conversas..."):
        conversations = fetch_conversations(params)

    if not conversations:
        st.info("Nenhuma conversa encontrada com os filtros aplicados")
        return

    # Analytics simples
    st.subheader("📊 Resumo Geral")
    render_simple_analytics(conversations)

    st.markdown("---")

    # Gráfico de mensagens por hora
    st.subheader("📈 Análise Temporal")
    render_hourly_messages_chart(conversations, date_range)

    st.markdown("---")

    render_daily_messages_chart(conversations, date_range)

    st.markdown("---")

    # Lista de conversas
    st.subheader(f"💬 Conversas ({len(conversations)})")

    def get_conversation_sort_time(conv):
        """Retorna timestamp para ordenação"""
        start_time = conv.get('start_time')
        if start_time:
            brazil_time = convert_utc_to_brazil(start_time)
            return brazil_time if brazil_time else datetime.min.replace(tzinfo=BRAZIL_TZ)
        return datetime.min.replace(tzinfo=BRAZIL_TZ)

    conversations_sorted = sorted(
        conversations, key=get_conversation_sort_time, reverse=True)

    # Renderizar cada conversa com UX integrada
    for conv in conversations_sorted:
        messages = fetch_messages(conv.get('id'))
        render_conversation_integrated(conv, messages)


def render_daily_messages_chart(conversations, date_range):
    """Renderiza gráfico de mensagens por dia - NOVO"""

    params = {}
    if len(date_range) == 2:
        start_date_brazil = datetime.combine(
            date_range[0], datetime.min.time())
        end_date_brazil = datetime.combine(date_range[1], datetime.max.time())
        start_date_brazil = BRAZIL_TZ.localize(start_date_brazil)
        end_date_brazil = BRAZIL_TZ.localize(end_date_brazil)
        start_date_utc = start_date_brazil.astimezone(UTC)
        end_date_utc = end_date_brazil.astimezone(UTC)
        params["start_date"] = start_date_utc.isoformat()
        params["end_date"] = end_date_utc.isoformat()

    all_messages = fetch_all_messages(params)

    if not all_messages:
        return

    # ✅ Organizar dados por dia no timezone Brasil
    daily_data = defaultdict(lambda: defaultdict(int))

    for msg in all_messages:
        try:
            timestamp = msg.get('timestamp')
            if timestamp:
                date_brazil = get_date_brazil(timestamp)
                if date_brazil:
                    business_type = msg.get(
                        'conversation_business_type') or 'unknown'
                    business_type_display = translate_term(business_type)
                    daily_data[business_type_display][date_brazil] += 1
        except Exception:
            continue

    if not daily_data:
        return

    # Criar DataFrame
    chart_data = []
    all_dates = set()
    for business_type, date_counts in daily_data.items():
        all_dates.update(date_counts.keys())

    all_dates = sorted(list(all_dates))

    for business_type, date_counts in daily_data.items():
        for date in all_dates:
            chart_data.append({
                'Data': date,
                'Mensagens': date_counts.get(date, 0),
                'Tipo de Negócio': business_type
            })

    df = pd.DataFrame(chart_data)

    if len(df) > 0:
        # Criar gráfico de barras empilhadas
        fig = px.bar(
            df,
            x='Data',
            y='Mensagens',
            color='Tipo de Negócio',
            title='📅 Mensagens Recebidas por Dia (Horário do Brasil)',
            color_discrete_sequence=[
                '#667eea', '#764ba2', '#28a745', '#ffc107', '#dc3545']
        )

        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_family="Inter",
            height=400,
            xaxis_title="Data (Horário do Brasil)",
            yaxis_title="Número de Mensagens",
            legend_title="Tipo de Negócio",
            hovermode='x unified'
        )

        # Configurar eixo X para datas
        fig.update_xaxes(
            tickformat='%d/%m',
            tickangle=45
        )

        # Hover personalizado
        fig.update_traces(
            hovertemplate='<b>%{fullData.name}</b><br>' +
            'Data: %{x}<br>' +
            'Mensagens: %{y}<br>' +
                          '<extra></extra>'
        )

        st.plotly_chart(fig, use_container_width=True)

        # Insights diários
        total_messages_daily = df['Mensagens'].sum()
        if total_messages_daily > 0:
            peak_day = df.groupby('Data')['Mensagens'].sum().idxmax()
            peak_count_daily = df.groupby('Data')['Mensagens'].sum().max()
            avg_daily = total_messages_daily / \
                len(all_dates) if all_dates else 0

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("📊 Média Diária", f"{avg_daily:.1f}")

            with col2:
                st.metric("📅 Dia de Pico", peak_day.strftime('%d/%m')
                          if hasattr(peak_day, 'strftime') else str(peak_day))

            with col3:
                st.metric("📈 Mensagens no Dia de Pico", f"{peak_count_daily}")


def render_timezone_comparison_table(sample_timestamps):
    """Renderiza tabela de comparação de timezones - FUNÇÃO ADICIONAL"""

    if not sample_timestamps:
        return

    st.subheader("🕐 Comparação de Fusos Horários")

    comparison_data = []

    for i, timestamp in enumerate(sample_timestamps[:5]):  # Máximo 5 exemplos
        try:
            # UTC original
            if isinstance(timestamp, str):
                if 'T' in timestamp:
                    utc_dt = datetime.fromisoformat(
                        timestamp.replace('Z', '+00:00'))
                else:
                    utc_dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                    utc_dt = UTC.localize(utc_dt)
            else:
                utc_dt = timestamp
                if utc_dt.tzinfo is None:
                    utc_dt = UTC.localize(utc_dt)

            # Brasil
            brazil_dt = convert_utc_to_brazil(timestamp)

            comparison_data.append({
                'Exemplo': f'#{i+1}',
                'UTC (Banco de Dados)': utc_dt.strftime('%d/%m/%Y %H:%M:%S UTC'),
                'Brasil (Exibição)': brazil_dt.strftime('%d/%m/%Y %H:%M:%S -03') if brazil_dt else 'Erro',
                'Diferença': '3 horas atrás' if brazil_dt else 'N/A'
            })
        except Exception as e:
            comparison_data.append({
                'Exemplo': f'#{i+1}',
                'UTC (Banco de Dados)': str(timestamp),
                'Brasil (Exibição)': f'Erro: {e}',
                'Diferença': 'N/A'
            })

    if comparison_data:
        df_comparison = pd.DataFrame(comparison_data)
        st.dataframe(df_comparison, use_container_width=True)

        st.markdown("""
        <div class="timezone-info">
            <strong>💡 Como funciona:</strong><br>
            • <strong>UTC:</strong> Horário padrão salvo no banco de dados<br>
            • <strong>Brasil:</strong> UTC convertido para América/São_Paulo (UTC-3)<br>
            • <strong>Vantagem:</strong> Dados consistentes independente do fuso horário do servidor
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
