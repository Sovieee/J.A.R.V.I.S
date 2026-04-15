const { app, BrowserWindow, ipcMain } = require("electron");
const axios = require("axios");
require("dotenv").config();
const GROQ_API_KEY = process.env.GROQ_API_KEY;
// =======================
// 🤖 AI HANDLER (GLOBAL)
// =======================
ipcMain.handle("ask-ai", async (event, prompt) => {
  try {
    const res = await axios.post(
      "https://api.groq.com/openai/v1/chat/completions",
        {
          model: "llama-3.3-70b-versatile",
          messages: [
            {
              role: "user",
              content: prompt.trim()
            }
          ],
          temperature: 0.7,
          max_tokens: 1024
        },
      {
        headers: {
          Authorization: `Bearer ${GROQ_API_KEY}`,
          "Content-Type": "application/json",
        },
      }
    );

    return res.data.choices[0].message.content;

  } catch (err) {
  console.log("REAL ERROR:", err.response?.data);
  return "Error connecting to AI.";
  }
});


// =======================
// 🪟 WINDOW
// =======================
function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  });

  win.loadFile("index.html");
}

app.whenReady().then(createWindow);