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

  // ✅ SINGLE permission handler (FIXED)
  win.webContents.session.setPermissionRequestHandler((wc, permission, callback) => {
    console.log("Permission requested:", permission); // 🔍 debug log

    if (
      permission === "media" ||       // camera + mic
      permission === "camera" ||
      permission === "microphone" ||
      permission === "geolocation"
    ) {
      callback(true);
    } else {
      callback(false);
    }
  });

  win.loadFile("index.html");
}

// App ready
app.whenReady().then(createWindow);

// Quit on all windows closed (Windows/Linux)
app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});

// macOS behavior
app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});