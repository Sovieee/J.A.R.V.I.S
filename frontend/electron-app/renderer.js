// =======================
// ELEMENTS
// =======================
const socket = io("http://127.0.0.1:5000");
const logs = document.getElementById("logs");
const aiText = document.getElementById("ai-text");
const input = document.getElementById("command-input");
const liveFeed = document.getElementById("live-feed");

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
    return data.response || "No response";

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
        const response = await askJarvis(command);
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
// MAP (LEAFLET)
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