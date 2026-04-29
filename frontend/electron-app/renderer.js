// =======================
// ELEMENTS
// =======================
const { ipcRenderer } = require("electron");
const socket = io("http://127.0.0.1:5000");
const logs = document.getElementById("logs");
const aiText = document.getElementById("ai-text");
const input = document.getElementById("command-input");
const liveFeed = document.getElementById("live-feed");
const weatherIcon = document.getElementById("weather-icon");
const weatherCity = document.getElementById("weather-city");
const weatherTemp = document.getElementById("weather-temp");
const weatherDesc = document.getElementById("weather-desc");
// =======================
// LOG SYSTEM
// =======================
function addLog(msg) {
  const p = document.createElement("p");
  p.textContent = "> " + msg;
  logs.appendChild(p);
  logs.scrollTop = logs.scrollHeight;
}

// =======================
// LIVE FEED
// =======================
function addFeed(msg) {
  const p = document.createElement("p");
  p.textContent = "> " + msg;
  liveFeed.appendChild(p);
  liveFeed.scrollTop = liveFeed.scrollHeight;
}

async function getUserLocation() {
  return new Promise((resolve) => {

    // ✅ Try GPS first
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          resolve({
            lat: pos.coords.latitude,
            lon: pos.coords.longitude,
            source: "gps"
          });
        },
        async () => {
          // ❌ GPS failed → fallback to backend
          try {
            const res = await fetch("http://127.0.0.1:5000/command", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ command: "my location" })
            });

            const data = await res.json();

            if (data.response && data.response.lat) {
              resolve({ ...data.response, source: "backend" });
            } else {
              resolve(null);
            }

          } catch {
            resolve(null);
          }
        }
      );
    } else {
      resolve(null);
    }
  });
}

// =======================
// RANDOM SYSTEM LOGS
// =======================
setInterval(() => {
  const msgs = [
    "Scanning environment...",
    "Connecting to network...",
    "Loading modules...",
    "Running diagnostics...",
    "Accessing global database...",
    "Monitoring traffic..."
  ];
  addLog(msgs[Math.floor(Math.random() * msgs.length)]);
}, 1500);

// =======================
// TYPING EFFECT
// =======================
function typeResponse(text) {
  aiText.textContent = "";
  let i = 0;

  function typing() {
    if (i < text.length) {
      aiText.textContent += text.charAt(i);
      i++;
      setTimeout(typing, 15); // typing speed
    }
  }

  typing();
}

async function askJarvis(command) {
  try {
    const res = await fetch("http://127.0.0.1:5000/command", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ command }),
    });

    const data = await res.json();
    return data;

  } catch (err) {
    console.error(err);
    return "⚠️ Backend not reachable";
  }
}

// =======================
// COMMAND HANDLER
// =======================
if (input) {
  input.addEventListener("keydown", async (e) => {
    if (e.key === "Enter") {
      const command = input.value.trim();
      if (!command) return;

      input.value = "";

      addLog("User: " + command);

      // Live feed simulation
      addFeed("Analyzing command...");
      setTimeout(() => addFeed("Understanding intent..."), 300);
      setTimeout(() => addFeed("Generating response..."), 600);

      aiText.textContent = "Thinking...";

      try {
        // ensure location is set before AI call
        const location = await getUserLocation();

        if (location) {
          await fetch("http://127.0.0.1:5000/update-context", {
            method: "POST",
            headers: {
              "Content-Type": "application/json"
            },
            body: JSON.stringify({
              location: {
                city: document.getElementById("weather-city")?.textContent || "Unknown",
                lat: location.lat,
                lon: location.lon
              }
            })
          });
        }

        const response = await askJarvis(command);
        console.log("Backend response:", response);

        // 🔥 HANDLE ACTIONS FROM BACKEND
        if (response.action === "open_camera") {
          startCamera();
        }

        if (response.action === "capture_photo") {
          startCamera();
          setTimeout(capturePhoto, 500);
        }

        if (response.action === "record_video") {
          startCamera();
          setTimeout(startRecording, 500);
        }

        if (response.action === "stop_recording") {
          stopRecording();
        }

        if (response.action === "close_camera") {
          stopCamera();
        }

        typeResponse(response);

      } catch (err) {
        console.error(err);
        aiText.textContent = "Error connecting to JARVIS.";
      }
       }
  });
}

// =======================
// SYSTEM STATS
// =======================
setInterval(() => {
  const cpu = Math.floor(Math.random() * 100);
  const ram = Math.floor(Math.random() * 100);

  const cpuEl = document.getElementById("cpu");
  const ramEl = document.getElementById("ram");

  if (cpuEl) cpuEl.textContent = cpu + "%";
  if (ramEl) ramEl.textContent = ram + "%";
}, 1500);

// =======================
// REAL MAP (LEAFLET)
// =======================
window.addEventListener("DOMContentLoaded", () => {
  if (typeof L === "undefined") {
    console.error("Leaflet not loaded ❌");
    return;
  }

  const mapEl = document.getElementById("map");
  if (!mapEl) return;

  const map = L.map("map", {
    zoomControl: false,
    attributionControl: false
  }).setView([20, 0], 2);

  L.tileLayer(
    "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
    { subdomains: "abcd", maxZoom: 19 }
  ).addTo(map);

  // 🌍 USE REAL LOCATION (same as weather)
  if (!navigator.geolocation) {
    console.warn("Geolocation not supported");
    return;
  }

  getUserLocation().then((location) => {
    if (!location) {
      addLog("⚠️ Unable to detect location");
      return;
    }

    const { lat, lon, source } = location;

    map.setView([lat, lon], 12);

    const useMarker = L.circleMarker([lat, lon], {
      radius: 8,
      color: "#00f7ff",
      fillColor: "#00f7ff",
      fillOpacity: 0.9
    }).addTo(map);

    useMarker.bindPopup(`📍 You are here (${source})`).openPopup();

    addLog(`📍 Location via ${source}`);

    fetch("http://127.0.0.1:5000/update-context", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        location: {
          city: document.getElementById("weather-city")?.textContent || "Unknown",
          lat: location.lat,
          lon: location.lon
        }
      })
    })
    .then(res => res.json())
    .then(data => console.log("✅ Context updated:", data))
    .catch(err => console.error("❌ Context error:", err));
    },
    (err) => {
      console.warn("Location error:", err.message);
      addLog("⚠️ Location access denied");
    }
  );

  // Animated pings
  function addPing() {
    const lat = (Math.random() * 140) - 70;
    const lng = (Math.random() * 360) - 180;

    const circle = L.circle([lat, lng], {
      color: "#00f7ff",
      fillColor: "#00f7ff",
      fillOpacity: 0.5,
      radius: 200000
    }).addTo(map);

    setTimeout(() => {
      map.removeLayer(circle);
    }, 2000);
  }

  setInterval(addPing, 1500);
});

// =======================
// GRAPH (CHART.JS)
// =======================
const ctx = document.getElementById("chart");

if (ctx) {
  const data = {
    labels: [],
    datasets: [
      {
        label: "CPU Usage",
        data: [],
        borderColor: "#00f7ff",
        tension: 0.3,
      },
      {
        label: "RAM Usage",
        data: [],
        borderColor: "#00ff9f",
        tension: 0.3,
      }
    ]
  };

  const chart = new Chart(ctx, {
    type: "line",
    data: data,
    options: {
      responsive: true,
      animation: false,
      plugins: {
        legend: {
          labels: { color: "#00f7ff" }
        }
      },
      scales: {
        x: {
          ticks: { color: "#00f7ff" },
          grid: { color: "rgba(0,255,255,0.1)" }
        },
        y: {
          ticks: { color: "#00f7ff" },
          grid: { color: "rgba(0,255,255,0.1)" },
          min: 0,
          max: 100
        }
      }
    }
  });

  setInterval(() => {
    const time = new Date().toLocaleTimeString();

    const cpu = Math.floor(Math.random() * 100);
    const ram = Math.floor(Math.random() * 100);

    data.labels.push(time);
    data.datasets[0].data.push(cpu);
    data.datasets[1].data.push(ram);

    if (data.labels.length > 10) {
      data.labels.shift();
      data.datasets.forEach(ds => ds.data.shift());
    }

    chart.update();
  }, 1500);
}
socket.emit("start_listening");
// =======================
// USER VOICE INPUT
// =======================
socket.on("jarvis_user", (data) => {
  addLog("User (voice): " + data.command);
});
// =======================
// STREAMED RESPONSE (chunk by chunk)
// =======================
socket.on("jarvis_chunk", (data) => {
  aiText.textContent += data.chunk;
});
// =======================
// RESPONSE COMPLETE
// =======================
socket.on("jarvis_done", () => {
  addFeed("Response complete.");
});

// =======================
// WEATHER FUNCTION
// =======================

// 🔹 ICON FUNCTION (clean & global)
function getWeatherIcon(main) {
  switch (main.toLowerCase()) {
    case "clear": return "☀️";
    case "clouds": return "☁️";
    case "rain": return "🌧️";
    case "drizzle": return "🌦️";
    case "thunderstorm": return "⛈️";
    case "snow": return "❄️";
    case "mist":
    case "fog":
    case "haze": return "🌫️";
    default: return "🌍";
  }
}

// 🔹 MAIN WEATHER LOADER
async function loadWeather(lat, lon) {
  try {
    const apiKey = await ipcRenderer.invoke("get-weather-key");

    const res = await fetch(
      `https://api.openweathermap.org/data/2.5/weather?lat=${lat}&lon=${lon}&units=metric&appid=${apiKey}`
    );

    const data = await res.json();

    if (data.cod !== 200) {
      throw new Error(data.message);
    }

    // =========================
    // UI UPDATE (SAFE)
    // =========================
    if (weatherCity) weatherCity.textContent = data.name;
    if (weatherTemp) weatherTemp.textContent = Math.round(data.main.temp) + "°C";
    if (weatherDesc) weatherDesc.textContent = data.weather[0].description;

    // =========================
    // ICON UPDATE (FIXED)
    // =========================
    if (weatherIcon) {
      const main = data.weather[0].main;
      weatherIcon.textContent = getWeatherIcon(main);
    }

    // =========================
    // INTELLIGENCE LAYER
    // =========================
    const temp = Math.round(data.main.temp);
    const condition = data.weather[0].main.toLowerCase();

    if (temp > 30) addLog("🌡️ It's quite hot outside.");
    if (condition.includes("rain")) addLog("🌧️ Carry an umbrella.");
    if (condition.includes("cloud")) addLog("☁️ Cloudy weather detected.");

  } catch (err) {
    console.error("Weather error:", err);

    if (weatherCity) weatherCity.textContent = "Weather unavailable";
    if (weatherTemp) weatherTemp.textContent = "--°C";
    if (weatherDesc) weatherDesc.textContent = "--";
    if (weatherIcon) weatherIcon.textContent = "⚠️";
  }
}

// =======================
// USER LOCATION FOR WEATHER
// =======================

async function initWeather() {
  const location = await getUserLocation();

  if (!location) {
    if (weatherCity) weatherCity.textContent = "Location unavailable";
    return;
  }

  loadWeather(location.lat, location.lon);
}

// 🔁 Refresh every 5 minutes
setInterval(async () => {
  const location = await getUserLocation();

  if (!location) return;

  loadWeather(location.lat, location.lon);

}, 300000);

// Camera Options

let stream = null;
let mediaRecorder = null;
let recordedChunks = [];

async function startCamera() {
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });

    const video = document.getElementById("camera");
    video.srcObject = stream;

    document.getElementById("camera-container").classList.remove("hidden");

    addLog("📷 Camera started");

  } catch (err) {
    console.error(err);
    addLog("❌ Camera access denied");
  }
}

// Capture Photos

function capturePhoto() {
  const video = document.getElementById("camera");

  const canvas = document.createElement("canvas");
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;

  const ctx = canvas.getContext("2d");
  ctx.drawImage(video, 0, 0);

  const image = canvas.toDataURL("image/png");

  // Download image
  const a = document.createElement("a");
  a.href = image;
  a.download = "jarvis_photo.png";
  a.click();

  addLog("📸 Photo captured");
}

// Record Video

function startRecording() {
  if (!stream) return;

  recordedChunks = [];

  mediaRecorder = new MediaRecorder(stream);

  mediaRecorder.ondataavailable = (e) => {
    if (e.data.size > 0) recordedChunks.push(e.data);
  };

  mediaRecorder.onstop = () => {
    const blob = new Blob(recordedChunks, { type: "video/webm" });

    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "jarvis_video.webm";
    a.click();

    addLog("🎥 Video saved");
  };

  mediaRecorder.start();
  addLog("🎥 Recording started");
}

// Stop Recording
function stopRecording() {
  if (mediaRecorder) {
    mediaRecorder.stop();
    addLog("⏹ Recording stopped");
  }
}

// Close Camera
function stopCamera() {
  if (stream) {
    stream.getTracks().forEach(track => track.stop());
    stream = null;
  }

  const video = document.getElementById("camera");
  if (video) {
    video.srcObject = null;
  }

  const container = document.getElementById("camera-container");
  if (container) {
    container.classList.add("hidden");
  }

  addLog("📴 Camera stopped");
}

// 🚀 Init on load
window.addEventListener("DOMContentLoaded", initWeather);
document.getElementById("capture-btn")?.addEventListener("click", capturePhoto);
document.getElementById("record-btn")?.addEventListener("click", startRecording);
document.getElementById("stop-btn")?.addEventListener("click", stopRecording);