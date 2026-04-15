// =======================
// LOG SYSTEM
// =======================
let isTypingActive = true;
const { ipcRenderer } = require("electron");
const logs = document.getElementById("logs");
const aiText = document.getElementById("ai-text");

const logMessages = [
  "Initializing core systems...",
  "Loading neural modules...",
  "Establishing secure connection...",
  "Scanning environment...",
  "Accessing global database...",
  "Monitoring network traffic...",
  "Running diagnostics..."
];

function addLog(message) {
  const p = document.createElement("p");
  p.textContent = "> " + message;
  logs.appendChild(p);
  logs.scrollTop = logs.scrollHeight;
}

setInterval(() => {
  const msg = logMessages[Math.floor(Math.random() * logMessages.length)];
  addLog(msg);
}, 1200);


// =======================
// AI TYPING EFFECT
// =======================
const sentences = [
  "System online.",
  "All modules functioning.",
  "Awaiting your command..."
];

let index = 0;

function typeText(text, i = 0) {
  if (!isTypingActive) return; // 🔥 STOP if disabled

  if (i < text.length) {
    aiText.textContent = text.slice(0, i + 1);
    setTimeout(() => typeText(text, i + 1), 40);
  } else {
    setTimeout(() => {
      index = (index + 1) % sentences.length;
      typeText(sentences[index]);
    }, 2000);
  }
}

typeText(sentences[0]);


// =======================
// SYSTEM STATS
// =======================
setInterval(() => {
  document.getElementById("cpu").textContent =
    Math.floor(Math.random() * 100) + "%";

  document.getElementById("ram").textContent =
    Math.floor(Math.random() * 100) + "%";
}, 1500);


// =======================
// 🌍 LEAFLET MAP (FIXED)
// =======================
window.addEventListener("DOMContentLoaded", () => {

  if (typeof L === "undefined") {
    console.error("Leaflet not loaded ❌");
    return;
  }

  const mapElement = document.getElementById("map");

  if (!mapElement) {
    console.error("Map container not found ❌");
    return;
  }

  const map = L.map('map', {
    zoomControl: false,
    attributionControl: false
  }).setView([20, 0], 2);

  L.tileLayer(
    'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
    {
      subdomains: 'abcd',
      maxZoom: 19
    }
  ).addTo(map);

  // 🔥 Animated activity pings
  function addPing() {
    const lat = (Math.random() * 140) - 70;
    const lng = (Math.random() * 360) - 180;

    const circle = L.circle([lat, lng], {
      color: '#00f7ff',
      fillColor: '#00f7ff',
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
// 📊 LIVE GRAPH SYSTEM
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
          labels: {
            color: "#00f7ff"
          }
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

  // Update graph in real-time
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

// =======================
// 🤖 COMMAND SYSTEM
// =======================
const input = document.getElementById("command-input");

if (input) {
  input.addEventListener("keydown", async (e) => {
  if (e.key === "Enter") {

    isTypingActive = false; // 🔥 STOP animation

    const command = input.value;
    input.value = "";

    addLog("User: " + command);
    addFeed("Analyzing command...");
    setTimeout(() => addFeed("Understanding intent..."), 300);
    setTimeout(() => addFeed("Generating response..."), 600);

    aiText.textContent = "Thinking...";

    const response = await ipcRenderer.invoke("ask-ai", command);

    typeResponse(response);
  }
});
}
function typeResponse(text) {
  let i = 0;
  aiText.textContent = "";

  function type() {
    if (i < text.length) {
      aiText.textContent += text.charAt(i);
      aiText.scrollTop = aiText.scrollHeight; // auto-scroll
      i++;
      setTimeout(type, 10); // speed (lower = faster)
    }
  }

  type();
}
const liveFeed = document.getElementById("live-feed");

function addFeed(msg) {
  const p = document.createElement("p");
  p.textContent = "> " + msg;
  liveFeed.appendChild(p);
  liveFeed.scrollTop = liveFeed.scrollHeight;
}