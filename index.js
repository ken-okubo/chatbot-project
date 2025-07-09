require("dotenv").config();
const venom = require("venom-bot");
const axios = require("axios");
const fs = require("fs");

// Função para limpar sessões antigas
function clearOldSessions() {
  const sessionsToDelete = [
    "./tokens",
    "./.wwebjs_auth",
    "./.wwebjs_cache",
    "./chatbot-session",
    "./session",
    "./sessions",
    "./.venom",
    "./new-tokens",
  ];

  sessionsToDelete.forEach((dir) => {
    try {
      if (fs.existsSync(dir)) {
        fs.rmSync(dir, { recursive: true, force: true });
        console.log(`🗑️ Removido: ${dir}`);
      }
    } catch (error) {
      console.log(`⚠️ Não foi possível remover ${dir}:`, error.message);
    }
  });
}

// Limpar sessões antigas
console.log("🧹 Limpando sessões antigas...");
clearOldSessions();

// Configuração do cliente HTTP
const httpClient = axios.create({
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Nome único para sessão
const uniqueSessionName = `qr-session-${Date.now()}`;
console.log(`🆕 Criando nova sessão: ${uniqueSessionName}`);

// Configuração mínima para funcionar
venom
  .create({
    session: uniqueSessionName,
    headless: true, // Deixe headless mesmo para forçar terminal
    logQR: true,
    qrTimeout: 0,
    authTimeout: 0,
    catchQR: (base64Qrimg, asciiQR, attempts, urlCode) => {
      console.log("\n" + "🔥".repeat(20) + " QR CODE " + "🔥".repeat(20));
      console.log(`📱 Escaneie com seu WhatsApp - Tentativa: ${attempts}`);
      console.log("🔥".repeat(50));
      console.log(asciiQR);
      console.log("🔥".repeat(50));
      if (urlCode) {
        console.log(`🔗 URL alternativa: ${urlCode}`);
      }
      console.log("⏰ Aguardando scan...\n");
    },
    statusFind: (statusSession, session) => {
      console.log(`🔄 Status: ${statusSession}`);
      console.log(`📱 Session: ${session}`);
    },
    onLoadingScreen: (percent, message) => {
      console.log(`⏳ ${percent}% - ${message}`);
    },
  })
  .then((client) => {
    console.log("✅ CONECTADO COM SUCESSO!");
    start(client);
  })
  .catch((err) => {
    console.error("❌ Erro:", err);
    process.exit(1);
  });

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

function start(client) {
  console.log("✅ Bot conectado com sucesso!");

  client.onStateChange((state) => {
    console.log("Estado do cliente:", state);
    if (state === "CONFLICT" || state === "UNPAIRED") {
      console.log("❌ Cliente desconectado");
      process.exit(1);
    }
  });

  client.onMessage(async (message) => {
    if (
      !message.body ||
      message.isGroupMsg ||
      message.from === "status@broadcast"
    ) {
      return;
    }

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

  process.on("SIGINT", async () => {
    console.log("🔄 Fechando o bot...");
    await client.close();
    process.exit(0);
  });
}

process.on("unhandledRejection", (reason, promise) => {
  console.error("❌ Unhandled Rejection at:", promise, "reason:", reason);
});

process.on("uncaughtException", (error) => {
  console.error("❌ Uncaught Exception:", error);
  process.exit(1);
});
