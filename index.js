require("dotenv").config();
const venom = require("venom-bot");
const axios = require("axios");

// Configuração do cliente HTTP com timeout
const httpClient = axios.create({
  timeout: 30000, // 30 segundos
  headers: {
    "Content-Type": "application/json",
  },
});

// Cria o cliente WhatsApp
venom
  .create({
    session: "chatbot-session",
    multidevice: true,
    browserArgs: ["--no-sandbox", "--disable-setuid-sandbox"],
    headless: true,
    useChrome: true,
    logQR: false, // Não mostrar QR no console
    statusFind: (statusSession, session) => {
      console.log("Status:", statusSession);
      console.log("Session name:", session);
    },
    onLoadingScreen: (percent, message) => {
      console.log("Loading screen:", percent, message);
    },
  })
  .then((client) => start(client))
  .catch((err) => {
    console.error("❌ Erro ao iniciar o bot:", err);
    process.exit(1);
  });

// Função para validar resposta da API
function validateApiResponse(data) {
  if (!data) {
    throw new Error("Resposta vazia da API");
  }

  if (typeof data !== "object") {
    throw new Error("Resposta da API não é um objeto válido");
  }

  if (!data.reply) {
    throw new Error("Campo 'reply' não encontrado na resposta");
  }

  return true;
}

// Função principal de integração
function start(client) {
  console.log("✅ Bot conectado com sucesso!");

  // Tratamento de desconexão
  client.onStateChange((state) => {
    console.log("Estado do cliente:", state);
    if (state === "CONFLICT" || state === "UNPAIRED") {
      console.log("❌ Cliente desconectado");
      process.exit(1);
    }
  });

  client.onMessage(async (message) => {
    // Filtrar mensagens inválidas
    if (
      !message.body ||
      message.isGroupMsg ||
      message.from === "status@broadcast"
    ) {
      return;
    }

    // Ignorar mensagens do próprio bot
    if (message.fromMe) {
      return;
    }

    const userNumber = message.from.replace("@c.us", "");
    const userMessage = message.body.trim();

    console.log(`📥 Mensagem recebida de ${userNumber}: ${userMessage}`);

    try {
      const payload = {
        user_number: userNumber,
        message: userMessage,
      };

      console.log("🔄 Enviando para API:", payload);

      const response = await httpClient.post(
        process.env.BACKEND_API_URL,
        payload
      );

      console.log("📥 Resposta da API:", response.data);

      // Validar resposta
      validateApiResponse(response.data);

      const reply = response.data.reply;

      if (reply && reply.trim()) {
        await client.sendText(message.from, reply);
        console.log("📤 Resposta enviada com sucesso");
      } else {
        console.warn("⚠️ Resposta vazia recebida do backend");
        await client.sendText(
          message.from,
          "Desculpe, não consegui processar sua mensagem. Pode tentar novamente?"
        );
      }
    } catch (error) {
      console.error("❌ Erro ao processar mensagem:", error);

      // Log detalhado do erro
      if (error.response) {
        console.error("📄 Dados do erro:", error.response.data);
        console.error("📊 Status:", error.response.status);
      }

      try {
        await client.sendText(
          message.from,
          "Desculpe, ocorreu um erro temporário. Tente novamente em alguns momentos."
        );
      } catch (sendError) {
        console.error("❌ Erro ao enviar mensagem de erro:", sendError);
      }
    }
  });

  // Manter o processo vivo
  process.on("SIGINT", async () => {
    console.log("🔄 Fechando o bot...");
    await client.close();
    process.exit(0);
  });
}

// Tratamento de erros não capturados
process.on("unhandledRejection", (reason, promise) => {
  console.error("❌ Unhandled Rejection at:", promise, "reason:", reason);
});

process.on("uncaughtException", (error) => {
  console.error("❌ Uncaught Exception:", error);
  process.exit(1);
});
