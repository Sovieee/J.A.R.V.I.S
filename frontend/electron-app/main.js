require("dotenv").config({
  path: require("path").join(__dirname, "../../.env")
});

const { app, BrowserWindow, ipcMain } = require("electron");

// ✅ IPC to send weather key
ipcMain.handle("get-weather-key", () => {
  return process.env.OPENWEATHER_API_KEY;
});

function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
    },
  });

  // ✅ allow geolocation
  win.webContents.session.setPermissionRequestHandler((wc, permission, callback) => {
    if (permission === "geolocation") callback(true);
    else callback(false);
  });

  win.loadFile("index.html");
}

app.whenReady().then(createWindow);