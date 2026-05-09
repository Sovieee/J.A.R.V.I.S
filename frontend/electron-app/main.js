const path = require("path");
const fs = require("fs");
const { app, BrowserWindow, ipcMain } = require("electron");
const { spawn } = require("child_process");

const isDev = !app.isPackaged;

// ─────────────────────────────────────────────
// FIX 1: Load .env manually and inject into
//         process.env BEFORE anything else.
//         dotenv alone does NOT pass these vars
//         into the spawned api.exe process.
// ─────────────────────────────────────────────
const envPath = isDev
  ? path.join(__dirname, "../../.env")
  : path.join(process.resourcesPath, ".env");

const injectedEnv = {};

if (fs.existsSync(envPath)) {
  const lines = fs.readFileSync(envPath, "utf-8").split(/\r?\n/);
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const eqIndex = trimmed.indexOf("=");
    if (eqIndex === -1) continue;
    const key = trimmed.slice(0, eqIndex).trim();
    const val = trimmed.slice(eqIndex + 1).trim();
    injectedEnv[key] = val;
    process.env[key] = val; // also set for ipcMain handlers
  }
}

let pythonProcess = null;

// ─────────────────────────────────────────────
// FIX 2: Log all backend output to a real file.
//         In a packaged app there is no console.
//         Without this you are completely blind
//         to why api.exe is crashing.
//         Log location: %AppData%\J.A.R.V.I.S\backend.log
// ─────────────────────────────────────────────
function getLogStream() {
  const logDir = app.getPath("userData");
  const logPath = path.join(logDir, "backend.log");
  return fs.createWriteStream(logPath, { flags: "a" });
}

function startPythonBackend() {
  const command = app.isPackaged
    ? path.join(process.resourcesPath, "api.exe")
    : "python";

  const args = app.isPackaged
    ? []
    : [path.join(__dirname, "../../api.py")];

  const cwd = app.isPackaged
    ? process.resourcesPath
    : path.join(__dirname, "../../");

  // ─────────────────────────────────────────
  // FIX 3: Pass injectedEnv explicitly into
  //         the spawned process. Without this,
  //         api.exe never receives your API keys
  //         (GROQ, Spotify, OpenWeather etc.)
  //         and crashes immediately on startup.
  // ─────────────────────────────────────────
  pythonProcess = spawn(command, args, {
    cwd,
    env: { ...process.env, ...injectedEnv },
    windowsHide: true,
  });

  const logStream = getLogStream();
  const timestamp = new Date().toISOString();
  logStream.write(`\n\n========== JARVIS START @ ${timestamp} ==========\n`);
  logStream.write(`Command: ${command}\n`);
  logStream.write(`CWD: ${cwd}\n`);
  logStream.write(`isPackaged: ${app.isPackaged}\n\n`);

  pythonProcess.stdout.on("data", (data) => {
    logStream.write(`[OUT] ${data}`);
  });

  pythonProcess.stderr.on("data", (data) => {
    logStream.write(`[ERR] ${data}`);
  });

  pythonProcess.on("close", (code) => {
    logStream.write(`[EXIT] Process exited with code ${code}\n`);
  });

  pythonProcess.on("error", (err) => {
    logStream.write(`[SPAWN ERROR] ${err.message}\n`);
  });
}

ipcMain.handle("get-weather-key", () => {
  return process.env.OPENWEATHER_API_KEY;
});

// ─────────────────────────────────────────────
// FIX 4: Pass success/failure status back from
//         waitForFlask so the renderer can show
//         a meaningful error if backend never
//         starts — instead of a blank "not
//         reachable" with no explanation.
// ─────────────────────────────────────────────
function waitForFlask(port, retries, callback) {
  const net = require("net");
  const client = new net.Socket();
  client.setTimeout(500);

  client.connect(port, "127.0.0.1", () => {
    client.destroy();
    callback(true); // ← success
  });

  client.on("error", () => {
    client.destroy();
    if (retries > 0) {
      setTimeout(() => waitForFlask(port, retries - 1, callback), 500);
    } else {
      callback(false); // ← failed after all retries
    }
  });

  client.on("timeout", () => {
    client.destroy();
    if (retries > 0) {
      setTimeout(() => waitForFlask(port, retries - 1, callback), 500);
    } else {
      callback(false);
    }
  });
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
    },
  });

  win.webContents.session.setPermissionRequestHandler((wc, permission, callback) => {
    if (["media", "camera", "microphone", "geolocation"].includes(permission)) {
      callback(true);
    } else {
      callback(false);
    }
  });

  // ─────────────────────────────────────────
  // FIX 5: Increased retries to 120 (60 sec).
  //         PyInstaller exes can take 20–30s to
  //         unpack on first run. 60 retries (30s)
  //         was not enough on slower machines.
  // ─────────────────────────────────────────
  waitForFlask(5000, 120, (success) => {
    win.loadFile(path.join(__dirname, "index.html"));

    if (!success) {
      // Inject a proper error message into the UI
      // telling the user where to find the log file
      win.webContents.once("did-finish-load", () => {
        const logPath = path.join(app.getPath("userData"), "backend.log")
          .replace(/\\/g, "\\\\");

        win.webContents.executeJavaScript(`
          const el = document.getElementById('ai-text');
          if (el) {
            el.innerHTML =
              '⚠️ Backend failed to start.<br><br>' +
              'Check the log file for the exact error:<br>' +
              '<span style="color:#ff4444;font-size:11px">${logPath}</span>';
          }
        `);
      });
    }
  });
}

app.whenReady().then(() => {
  startPythonBackend();
  createWindow();
});

app.on("window-all-closed", () => {
  if (pythonProcess) pythonProcess.kill();
  if (process.platform !== "darwin") app.quit();
});

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});
