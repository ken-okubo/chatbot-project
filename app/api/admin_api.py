from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db import models
from app.db.crud import get_conversation_by_id, get_messages_by_conversation_id, close_inactive_conversations
import pandas as pd
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import html
from typing import Optional
from uuid import UUID

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/admin/messages")
def list_messages(
    conversation_id: UUID,
    db: Session = Depends(get_db)
):
    messages = db.query(models.Message).filter(
        models.Message.conversation_id == conversation_id
    ).order_by(models.Message.timestamp.asc()).all()

    # Buscar a conversa dessa conversa_id
    conversation = db.query(models.Conversation).filter(
        models.Conversation.id == conversation_id
    ).first()

    # Pega o business_type/status da conversa
    conversation_business_type = conversation.business_type if conversation else 'unknown'

    result = []
    for msg in messages:
        result.append({
            "id": str(msg.id),
            "conversation_id": str(msg.conversation_id),
            "user_number": msg.user_number,
            "content": msg.content,
            "from_user": msg.from_user,
            "business_type": msg.business_type,
            "conversation_business_type": conversation_business_type,
            "timestamp": msg.timestamp.isoformat() if msg.timestamp else None
        })
    return result


@router.get("/admin/conversations")
def list_conversations(
    user_number: Optional[str] = None,
    status: Optional[str] = None,
    needs_human: Optional[bool] = None,
    sentiment: Optional[str] = None,
    db: Session = Depends(get_db)
):
    close_inactive_conversations(db)
    query = db.query(models.Conversation)

    if user_number:
        query = query.filter(models.Conversation.user_number == user_number)
    if status:
        query = query.filter(models.Conversation.status == status)
    if needs_human is not None:
        query = query.filter(models.Conversation.needs_human == needs_human)
    if sentiment:
        query = query.filter(models.Conversation.sentiment == sentiment)

    conversations = query.order_by(models.Conversation.start_time.desc()).all()

    result = []
    for conv in conversations:
        result.append({
            "id": str(conv.id),
            "user_number": conv.user_number,
            "start_time": conv.start_time.isoformat() if conv.start_time else None,
            "end_time": conv.end_time.isoformat() if conv.end_time else None,
            "business_type": conv.business_type,
            "status": conv.status,
            "needs_human": conv.needs_human,
            "sentiment": conv.sentiment,
            "sentiment_score": conv.sentiment_score,
            "last_sentiment_update": conv.last_sentiment_update.isoformat() if conv.last_sentiment_update else None
        })

    return result


def format_timestamp_br(timestamp):
    """Formata timestamp para padrão brasileiro"""
    if timestamp:
        try:
            if hasattr(timestamp, 'strftime'):
                return timestamp.strftime("%d/%m/%Y %H:%M:%S")
            else:
                dt = datetime.fromisoformat(
                    str(timestamp).replace('Z', '+00:00'))
                return dt.strftime("%d/%m/%Y %H:%M:%S")
        except:
            return str(timestamp)
    return "Não informado"


def translate_business_type(business_type):
    """Traduz business_type para português"""
    mapping = {
        "delivery": "Delivery",
        "mecanica": "Mecânica",
        "farmacia": "Farmácia",
        "unknown": "Indefinido"
    }
    return mapping.get(str(business_type).lower(), business_type)


def translate_status(status):
    """Traduz status para português"""
    mapping = {
        "open": "Aberta",
        "closed": "Fechada"
    }
    return mapping.get(str(status).lower(), status)


@router.get("/admin/conversations/{conversation_id}/download/csv")
async def download_conversation_csv(
    conversation_id: str,
    db: Session = Depends(get_db)
):
    """Download da conversa em formato CSV"""
    try:
        # Buscar conversa
        conversation = get_conversation_by_id(db, conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=404, detail="Conversa não encontrada")

        # Buscar mensagens
        messages = get_messages_by_conversation_id(db, conversation_id)

        # Preparar dados para CSV
        csv_data = []

        # Adicionar informações da conversa
        csv_data.append({
            'Tipo': 'INFORMAÇÕES DA CONVERSA',
            'Remetente': '',
            'Conteúdo': '',
            'Data/Hora': '',
            'ID': ''
        })

        csv_data.append({
            'Tipo': 'Número do Cliente',
            'Remetente': conversation.user_number,
            'Conteúdo': '',
            'Data/Hora': '',
            'ID': ''
        })

        csv_data.append({
            'Tipo': 'Tipo de Negócio',
            'Remetente': translate_business_type(conversation.business_type),
            'Conteúdo': '',
            'Data/Hora': '',
            'ID': ''
        })

        csv_data.append({
            'Tipo': 'Status',
            'Remetente': translate_status(conversation.status),
            'Conteúdo': '',
            'Data/Hora': '',
            'ID': ''
        })

        csv_data.append({
            'Tipo': 'Precisa Humano',
            'Remetente': 'Sim' if conversation.needs_human else 'Não',
            'Conteúdo': '',
            'Data/Hora': '',
            'ID': ''
        })

        csv_data.append({
            'Tipo': 'Início da Conversa',
            'Remetente': format_timestamp_br(conversation.start_time),
            'Conteúdo': '',
            'Data/Hora': '',
            'ID': ''
        })

        if conversation.end_time:
            csv_data.append({
                'Tipo': 'Fim da Conversa',
                'Remetente': format_timestamp_br(conversation.end_time),
                'Conteúdo': '',
                'Data/Hora': '',
                'ID': ''
            })

        # Linha separadora
        csv_data.append({
            'Tipo': '',
            'Remetente': '',
            'Conteúdo': '',
            'Data/Hora': '',
            'ID': ''
        })

        csv_data.append({
            'Tipo': 'MENSAGENS DA CONVERSA',
            'Remetente': '',
            'Conteúdo': '',
            'Data/Hora': '',
            'ID': ''
        })

        # Adicionar mensagens
        for msg in sorted(messages, key=lambda x: x.timestamp):
            csv_data.append({
                'Tipo': 'Mensagem',
                'Remetente': 'Cliente' if msg.from_user else 'Bot',
                'Conteúdo': msg.content,
                'Data/Hora': format_timestamp_br(msg.timestamp),
                'ID': str(msg.id)
            })

        # Criar DataFrame
        df = pd.DataFrame(csv_data)

        # Gerar CSV
        output = io.StringIO()
        df.to_csv(output, index=False, encoding='utf-8-sig')
        output.seek(0)

        # Nome do arquivo
        filename = f"conversa_{conversation.user_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        # Retornar como download
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode('utf-8-sig')),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao gerar CSV: {str(e)}")


@router.get("/admin/conversations/{conversation_id}/download/pdf")
async def download_conversation_pdf(
    conversation_id: str,
    db: Session = Depends(get_db)
):
    """Download da conversa em formato PDF"""
    try:
        # Buscar conversa
        conversation = get_conversation_by_id(db, conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=404, detail="Conversa não encontrada")

        # Buscar mensagens
        messages = get_messages_by_conversation_id(db, conversation_id)

        # Criar PDF em memória
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*inch)

        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            textColor=colors.HexColor('#2c3e50')
        )

        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.HexColor('#34495e')
        )

        message_user_style = ParagraphStyle(
            'MessageUser',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=8,
            leftIndent=20,
            backgroundColor=colors.HexColor('#e3f2fd'),
            borderPadding=8
        )

        message_bot_style = ParagraphStyle(
            'MessageBot',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=8,
            rightIndent=20,
            backgroundColor=colors.HexColor('#f5f5f5'),
            borderPadding=8
        )

        # Conteúdo do PDF
        story = []

        # Título
        story.append(
            Paragraph("💬 Relatório de Conversa WhatsApp", title_style))
        story.append(Spacer(1, 20))

        # Informações da conversa
        story.append(Paragraph("📋 Informações da Conversa", heading_style))

        info_data = [
            ['Campo', 'Valor'],
            ['📱 Número do Cliente', conversation.user_number],
            ['🏢 Tipo de Negócio', translate_business_type(
                conversation.business_type)],
            ['📊 Status', translate_status(conversation.status)],
            ['🆘 Precisa Humano', 'Sim' if conversation.needs_human else 'Não'],
            ['🕐 Início', format_timestamp_br(conversation.start_time)],
            ['🏁 Fim', format_timestamp_br(
                conversation.end_time) if conversation.end_time else 'Em andamento'],
            ['🆔 ID da Conversa', str(conversation.id)]
        ]

        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1),
             [colors.white, colors.HexColor('#f8f9fa')])
        ]))

        story.append(info_table)
        story.append(Spacer(1, 30))

        # Mensagens
        story.append(Paragraph("💬 Histórico de Mensagens", heading_style))
        story.append(Spacer(1, 10))

        for i, msg in enumerate(sorted(messages, key=lambda x: x.timestamp), 1):
            sender = "👤 Cliente" if msg.from_user else "🤖 Bot"
            timestamp = format_timestamp_br(msg.timestamp)
            content = html.escape(msg.content)

            # Estilo baseado no remetente
            style = message_user_style if msg.from_user else message_bot_style

            message_text = f"<b>{sender}</b> - {timestamp}<br/>{content}"
            story.append(Paragraph(message_text, style))

        # Rodapé
        story.append(Spacer(1, 30))
        story.append(Paragraph(
            f"Relatório gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}",
            ParagraphStyle(
                'Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey)
        ))

        # Gerar PDF
        doc.build(story)
        buffer.seek(0)

        # Nome do arquivo
        filename = f"conversa_{conversation.user_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        # Retornar como download
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao gerar PDF: {str(e)}")


@router.post("/admin/conversations/{conversation_id}/update-sentiment")
async def update_conversation_sentiment_endpoint(
    conversation_id: str,
    db: Session = Depends(get_db)
):
    """
    Força atualização do sentiment de uma conversa
    """
    try:
        from app.db.crud import update_conversation_sentiment
        conversation = update_conversation_sentiment(db, conversation_id)

        if not conversation:
            raise HTTPException(
                status_code=404, detail="Conversa não encontrada")

        return {
            "conversation_id": str(conversation.id),
            "sentiment": conversation.sentiment,
            "sentiment_score": conversation.sentiment_score,
            "last_update": conversation.last_sentiment_update
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao atualizar sentiment: {str(e)}")
