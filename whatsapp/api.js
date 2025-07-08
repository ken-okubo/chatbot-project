const express = require("express");
const router = express.Router();
const client = require("./client");

// Enviar mensagem via WhatsApp
router.post("/send-message", async (req, res) => {
  const { number, message } = req.body;

  if (!number || !message) {
    return res
      .status(400)
      .json({ error: "Número e mensagem são obrigatórios." });
  }

  try {
    const finalNumber = number.includes("@c.us") ? number : `${number}@c.us`;

    await client.sendMessage(finalNumber, message);
    return res.status(200).json({ status: "Mensagem enviada com sucesso!" });
  } catch (error) {
    console.error("Erro ao enviar mensagem:", error);
    return res
      .status(500)
      .json({ error: "Erro ao enviar mensagem via WhatsApp." });
  }
});

module.exports = router;
