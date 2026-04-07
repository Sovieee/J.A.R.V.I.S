const { app, BrowserWindow } = require("electron");

function createWindow() {
  const win = new BrowserWindow({
    width: 900,
    height: 600,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false   // 🔥 IMPORTANT
    }
  });

  win.loadFile("index.html");

  // 🔥 Open DevTools for debugging
  win.webContents.openDevTools();
}

app.whenReady().then(createWindow);