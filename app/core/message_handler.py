from app.core import openai_client, business_context
import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.db import crud, models


def detect_business_type(db, conversation_id, messages):
    formatted_messages = []
    for m in messages:
        role = 'user' if m.from_user else 'assistant'
        formatted_messages.append({"role": role, "content": m.content})

    formatted_messages = formatted_messages[-10:]

    system_prompt = (
        "Você é um classificador de tipo de negócio com apenas quatro opções possíveis: "
        "'delivery', 'mechanic', 'pharmacy' ou 'unknown'. "
        "Analise as mensagens abaixo. Se o cliente falar de algo relacionado a comida, pedidos ou delivery, responda 'delivery'. "
        "Se for sobre veículos, serviços automotivos ou manutenção de carros, responda 'mechanic'. "
        "Se for sobre medicamentos, saúde, farmácia ou remédios, responda 'pharmacy'. "
        "Se não for possível identificar, responda apenas 'unknown'. "
        "IMPORTANTE: Responda APENAS com uma das quatro palavras: delivery, mechanic, pharmacy ou unknown. "
        "NÃO adicione texto extra, explicações ou frases."
    )

    openai_messages = [
        {"role": "system", "content": system_prompt}] + formatted_messages

    try:
        business_type = openai_client.get_openai_response(openai_messages)
        business_type = business_type.lower().strip()

        # Limpar resposta removendo possíveis caracteres extra
        business_type = business_type.replace('"', '').replace(
            "'", "").replace(".", "").replace(",", "")

        # Verificar se a resposta é válida
        valid_types = ['delivery', 'mechanic', 'pharmacy', 'unknown']

        # Se a resposta não for exatamente uma das opções válidas, forçar 'unknown'
        if business_type not in valid_types:
            print(
                f"⚠️ Tipo de negócio inválido detectado: '{business_type}'. Usando 'unknown'.")
            business_type = 'unknown'

        print(f"✅ Tipo de negócio detectado: '{business_type}'")

        # Só atualizar se for um tipo válido e diferente do atual
        if business_type in ['delivery', 'mechanic', 'pharmacy']:
            conversation = db.query(models.Conversation).filter(
                models.Conversation.id == conversation_id
            ).first()
            if conversation and conversation.business_type != business_type:
                conversation.business_type = business_type
                db.commit()
                print(f"✅ Business type atualizado para: {business_type}")

        return business_type

    except Exception as e:
        print(f"❌ Erro na detecção do tipo de negócio: {e}")
        return 'unknown'
    return business_type


def check_if_needs_human(ai_response: str):
    keywords = [
        "não sei",
        "não consigo ajudar",
        "precisa falar com um atendente",
        "não entendi",
        "não posso te ajudar"
    ]
    ai_response_lower = ai_response.lower()
    return any(keyword in ai_response_lower for keyword in keywords)


def extract_json_from_response(text):
    """
    Extrai JSON da resposta da OpenAI de forma mais robusta
    """
    try:
        # Remove espaços em branco e quebras de linha
        text = text.strip()

        # Primeiro, tenta parsear como JSON direto
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Procura por um JSON válido na resposta
        start_idx = text.find('{')
        end_idx = text.rfind('}')

        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_str = text[start_idx:end_idx + 1]
            return json.loads(json_str)

        # Se a resposta não contém JSON mas tem conteúdo, criar um JSON válido
        if text and len(text.strip()) > 0:
            return {
                "reply": text.strip(),
                "sentiment": "NEUTRO",
                "score": 0.0
            }

        return None

    except json.JSONDecodeError as e:
        print(f"❌ Erro ao decodificar JSON: {e}")
        print(f"❌ Texto recebido: {repr(text)}")

        # Como último recurso, se tiver texto, usar como reply
        if text and len(text.strip()) > 0:
            return {
                "reply": text.strip(),
                "sentiment": "NEUTRO",
                "score": 0.0
            }

        return None


def process_message(db: Session, user_number: str, content: str, conversation_id):
    messages = db.query(models.Message).filter(
        models.Message.conversation_id == conversation_id
    ).order_by(models.Message.timestamp).all()

    # Buscar a conversa
    conversation = db.query(models.Conversation).filter(
        models.Conversation.id == conversation_id
    ).first()

    # Sempre reexecuta a detecção a cada nova mensagem
    detected_type = detect_business_type(db, conversation_id, messages + [models.Message(
        user_number=user_number,
        content=content,
        from_user=True
    )])

    # Verificação extra de segurança para business_type
    valid_business_types = ['delivery', 'mechanic', 'pharmacy', 'unknown']
    if detected_type not in valid_business_types:
        print(
            f"⚠️ Tipo de negócio inválido detectado: '{detected_type}'. Forçando 'unknown'.")
        detected_type = 'unknown'

    # Só atualizar se for diferente e válido
    if detected_type != 'unknown' and conversation.business_type != detected_type:
        conversation.business_type = detected_type
        try:
            db.commit()
            print(f"✅ Business type salvo: {detected_type}")
        except Exception as e:
            print(f"❌ Erro ao salvar business_type: {e}")
            db.rollback()

    # Construir o system prompt baseado no business_type
    system_prompt = "Você é um chatbot de atendimento ao cliente. "

    if conversation and conversation.business_type in business_context.business_profiles:
        profile = business_context.business_profiles[conversation.business_type]

        system_prompt += f"Negócio: {conversation.business_type}. "
        system_prompt += f"Horário de funcionamento: {profile.get('working_hours', '')}. "

        if 'products' in profile:
            product_list = []
            for p in profile['products']:
                status = 'Disponível' if p.get('available') else 'Indisponível'
                price_info = f" - {p.get('price', 'Preço sob consulta')}" if p.get(
                    'available') else ""
                prescription_info = " (RECEITA OBRIGATÓRIA)" if p.get(
                    'requires_prescription') else ""
                note_info = f" ({p.get('note', '')})" if p.get('note') else ""

                product_list.append(
                    f"{p['name']}{price_info} ({status}){prescription_info}{note_info}")

            system_prompt += f"Produtos: {'; '.join(product_list)}. "

        if 'services' in profile:
            service_list = []
            for s in profile['services']:
                # Para serviços que são strings simples (compatibilidade com formato antigo)
                if isinstance(s, str):
                    service_list.append(s)
                # Para serviços que são dicionários com preço
                elif isinstance(s, dict):
                    status = 'Disponível' if s.get(
                        'available') else 'Indisponível'
                    price_info = f" - {s.get('price', 'Preço sob consulta')}" if s.get(
                        'available') else ""
                    duration_info = f" (Duração: {s.get('duration', '')})" if s.get(
                        'duration') else ""
                    note_info = f" ({s.get('note', '')})" if s.get(
                        'note') else ""

                    service_list.append(
                        f"{s['name']}{price_info} ({status}){duration_info}{note_info}")

            system_prompt += f"Serviços: {'; '.join(service_list)}. "

        # Incluir políticas importantes
        if 'policies' in profile:
            for key, value in profile['policies'].items():
                if key == 'payment_methods':
                    system_prompt += f"Formas de pagamento: {', '.join(value)}. "
                elif key == 'delivery_fee':
                    system_prompt += f"Taxa de entrega: {value}. "
                elif key == 'minimum_order':
                    system_prompt += f"Pedido mínimo: {value}. "
                elif key == 'delivery_time':
                    system_prompt += f"Tempo de entrega: {value}. "
                elif key == 'diagnostic_fee':
                    system_prompt += f"Taxa de diagnóstico: {value}. "
                elif key == 'warranty':
                    system_prompt += f"Garantia: {value}. "
                elif key == 'appointment_required' and value:
                    system_prompt += "Agendamento obrigatório para todos os serviços. "

    # Regras gerais para IA responder de forma completa
    tone_guidelines = ""

    if conversation.business_type == 'delivery':
        tone_guidelines = (
            "Responda de forma leve, simpática e descontraída. "
            "Use emojis quando fizer sentido (ex: 🍕😉). "
            "Seja rápido nas respostas. Mantenha o clima de um atendimento de pizzaria ou restaurante informal."
            "O cliente pode escolher até 2 sabores por pizza, sendo que o tamanho da pizza é sempre grande e o preço será do valor do sabor mais caro."
            "SEMPRE informe o preço quando o cliente perguntar sobre produtos específicos. "
            "Se o cliente perguntar por um sabor que não existe, informe que não temos esse sabor. "
            "Informe sempre o horário de funcionamento quando relevante."
            "Caso o cliente faça o pedido fora do horário de funcionamento, explique que estamos fechados e informe o próximo horário de abertura. "
            "Se o cliente perguntar sobre formas de pagamento, informe: Pix, Dinheiro ou Cartão. "
            "Mencione a taxa de entrega e pedido mínimo quando necessário. "
        )

    elif conversation.business_type == 'mechanic':
        tone_guidelines = (
            "Seja profissional, direto e prestativo. "
            "Use linguagem técnica acessível. Foque em agendamentos, revisões, diagnósticos e informações claras. "
            "Evite exageros ou brincadeiras. Mantenha um tom objetivo, mas cordial."
            "SEMPRE informe preços dos serviços quando solicitado. "
            "Explique que alguns serviços incluem apenas a mão de obra, sendo peças por conta do cliente. "
            "Informe que é necessário agendar um horário para serviços de mecânica e que o preço final será informado após a avaliação."
            "Se o cliente perguntar sobre preços, explique que é necessário trazer o veículo para uma avaliação antes de confirmar valores. "
            "Se o cliente perguntar por serviços que não realizamos (ex: conserto residencial), informe de forma educada que só atendemos veículos automotores."
        )

    elif conversation.business_type == 'pharmacy':
        tone_guidelines = (
            "Seja educado, empático e confiável. "
            "Oriente o cliente com clareza sobre medicamentos controlados e exigência de receita. "
            "Use emojis de forma moderada (ex: 💊🙂). "
            "SEMPRE informe preços quando solicitado. "
            "Se o cliente perguntar por um produto que tem diferentes versões ou que exija prescrição, pergunte por mais detalhes como dosagem e tipo antes de confirmar. "
            "Se não encontrar o produto ou serviço, informe claramente. "
            "Se o cliente mencionar apenas o nome genérico de um medicamento (ex: 'Dipirona'), sempre pergunte pela dosagem e forma (comprimido, gotas, etc) antes de confirmar. "
            "Se o medicamento for controlado ou exigir receita, informe claramente que só é possível vender mediante apresentação da receita física ou digital, conforme a legislação. "
            "Se o cliente perguntar por um produto que não temos, informe de forma clara e educada."
            "Informe sobre entrega em domicílio quando apropriado. "
        )

    system_prompt += (
        " Sempre responda de forma educada, objetiva e sem inventar informações. "
        "No final da resposta, envie **apenas** um objeto JSON válido, sem nenhuma explicação ou texto fora do JSON. "
        "O formato exato deve ser:\n"
        "{\n"
        "  \"reply\": \"Mensagem que deve ser enviada ao cliente\",\n"
        "  \"sentiment\": \"POSITIVO\" | \"NEUTRO\" | \"NEGATIVO\",\n"
        "  \"score\": número decimal entre -1.0 e 1.0\n"
        "}\n\n"
        "➡️ Interprete o **sentimento do cliente**, com base nas palavras, tom, pontuação e contexto:\n"
        "- Use **NEGATIVO** e score negativo se o cliente expressar frustração, impaciência, ironia, cobrança ou reclamação.\n"
        "- Use **POSITIVO** e score positivo se o cliente demonstrar entusiasmo, elogio ou gratidão.\n"
        "- Use **NEUTRO** se o cliente apenas fizer uma pergunta ou comentário objetivo, sem emoção clara.\n"
        "Quanto mais intenso o sentimento, mais próximo de -1.0 ou 1.0 deve ser o score. Por padrão, use 0.0 para casos neutros."
        "Analise o tom emocional do cliente com atenção. Use a pontuação, palavras e contexto para identificar emoções.\n"
        "- Se houver empolgação, alegria ou aprovação: use POSITIVO e score entre 0.6 e 1.0\n"
        "- Se houver reclamação, ironia ou frustração: use NEGATIVO e score entre -0.6 e -1.0\n"
        "- Se for neutro ou dúvida direta: use NEUTRO e score entre -0.1 e 0.1\n"
        "Evite usar score 0.0 em casos com emoção clara."
        "\n\n*** FORMATO DE RESPOSTA OBRIGATÓRIO ***\n"
        "VOCÊ DEVE SEMPRE, EM TODAS AS RESPOSTAS, retornar APENAS um JSON válido.\n"
        "NÃO adicione texto antes ou depois do JSON.\n"
        "NÃO explique sua resposta.\n"
        "NÃO adicione comentários.\n"
        "RETORNE APENAS O JSON:\n\n"
        "{\n"
        "  \"reply\": \"Sua mensagem completa para o cliente aqui\",\n"
        "  \"sentiment\": \"POSITIVO\" | \"NEUTRO\" | \"NEGATIVO\",\n"
        "  \"score\": número entre -1.0 e 1.0\n"
        "}\n\n"
        "INSTRUÇÕES PARA SENTIMENTO:\n"
        "- NEGATIVO (score -1.0 a -0.1): cliente frustrado, irritado, reclamando\n"
        "- POSITIVO (score 0.1 a 1.0): cliente animado, satisfeito, elogiando\n"
        "- NEUTRO (score 0.0): pergunta normal, sem emoção aparente\n\n"
        "LEMBRE-SE: Responda SOMENTE com o JSON, nada mais!"
    )

    system_prompt += tone_guidelines

    # Montar histórico da conversa
    openai_messages = [{"role": "system", "content": system_prompt}]
    for m in messages:
        role = 'user' if m.from_user else 'assistant'
        openai_messages.append({"role": role, "content": m.content})

    # Adicionar a nova mensagem
    openai_messages.append({"role": "user", "content": content})

    # Chamar a OpenAI
    response_raw = openai_client.get_openai_response(openai_messages)
    print("📤 Resposta da OpenAI:", response_raw)
    print("DEBUG (repr):", repr(response_raw))

    # Tentar extrair JSON da resposta
    response_data = extract_json_from_response(response_raw)

    # Se não conseguiu extrair JSON válido, fazer nova tentativa com prompt mais direto
    if response_data is None or not response_data.get("reply"):
        print("⚠️ Primeira resposta não estava em formato JSON. Tentando novamente...")

        # Fazer nova tentativa com prompt mais direto
        retry_prompt = {
            "role": "user",
            "content": "Por favor, responda APENAS com um JSON válido no formato: {\"reply\": \"sua resposta aqui\", \"sentiment\": \"NEUTRO\", \"score\": 0.0}"
        }

        retry_messages = openai_messages + [retry_prompt]
        response_raw = openai_client.get_openai_response(retry_messages)
        print("📤 Segunda tentativa - Resposta da OpenAI:", response_raw)

        response_data = extract_json_from_response(response_raw)

    if response_data is None:
        # Se não conseguir extrair JSON, usar valores padrão
        print("❌ Não foi possível extrair JSON da resposta. Usando fallback.")
        response_data = {
            "reply": "Desculpe, não consegui processar sua mensagem. Pode repetir?",
            "sentiment": "NEUTRO",
            "score": 0.0
        }

    # Extrair dados da resposta
    ai_response = response_data.get(
        "reply", "Desculpe, não consegui entender.")
    sentiment = response_data.get("sentiment", "NEUTRO").upper()
    score = float(response_data.get("score", 0.0))

    # Fallback se OpenAI retornar vazio na primeira mensagem
    if (not ai_response or ai_response.strip() == '') and len(messages) == 0:
        ai_response = (
            "Olá! Como posso ajudar você hoje? "
            "Somos especializados em delivery, mecânica ou farmácia. Em que posso te auxiliar? 😊"
        )

    # Atualizar conversa com sentimento
    conversation.sentiment = sentiment
    conversation.sentiment_score = score
    conversation.last_sentiment_update = datetime.now(timezone.utc)

    if sentiment == "NEGATIVO" and score < -0.5:
        conversation.needs_human = True

    if check_if_needs_human(ai_response):
        conversation.needs_human = True

    db.commit()

    # Salvar a resposta do bot
    crud.create_message(
        db=db,
        user_number=user_number,
        content=ai_response,
        from_user=False,
        business_type=conversation.business_type
    )

    return {
        "reply": ai_response,
        "sentiment": sentiment,
        "score": score
    }
