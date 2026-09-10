/**
 * RPS-BR Mission Control & Telemetry Client
 * Conecta via WebSocket ao FastAPI e atualiza o mapa Leaflet, os gráficos Chart.js e a telemetria.
 */

let map = null;
let satMarkers = {};
let satTrails = {};
let stationMarker = null;
let stationCircle = null;
let dopChart = null;
let ws = null;
let isPaused = false;
let stationsPopulated = false;

// Ícones SVG Customizados para o Mapa
const geoIcon = L.divIcon({
  className: 'sat-marker-geo',
  html: `<div style="background:#06b6d4;width:14px;height:14px;border-radius:2px;transform:rotate(45deg);border:2px solid #ffffff;box-shadow:0 0 10px #06b6d4;"></div>`,
  iconSize: [14, 14],
  iconAnchor: [7, 7]
});

const igsoIcon = L.divIcon({
  className: 'sat-marker-igso',
  html: `<div style="background:#f59e0b;width:14px;height:14px;border-radius:50%;border:2px solid #ffffff;box-shadow:0 0 10px #f59e0b;"></div>`,
  iconSize: [14, 14],
  iconAnchor: [7, 7]
});

const stationIcon = L.divIcon({
  className: 'station-marker',
  html: `<div style="background:#10b981;width:12px;height:12px;border-radius:50%;border:2px solid #ffffff;box-shadow:0 0 12px #10b981;"></div>`,
  iconSize: [12, 12],
  iconAnchor: [6, 6]
});

// Inicialização da Página
document.addEventListener('DOMContentLoaded', () => {
  initMap();
  initChart();
  connectWebSocket();
});

// 1. Inicialização do Mapa Leaflet 2D
function initMap() {
  // Centro aproximado do Brasil
  map = L.map('map-container', {
    zoomControl: true,
    attributionControl: false
  }).setView([-14.235, -51.925], 4);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 9,
    minZoom: 2
  }).addTo(map);
}

// 2. Inicialização do Gráfico Chart.js (DOP)
function initChart() {
  const ctx = document.getElementById('dop-chart').getContext('2d');
  dopChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: [],
      datasets: [
        {
          label: 'GDOP (Geométrico)',
          borderColor: '#f59e0b',
          borderDash: [4, 4],
          data: [],
          borderWidth: 1.5,
          tension: 0.3,
          pointRadius: 0
        },
        {
          label: 'PDOP (Posição 3D)',
          borderColor: '#10b981',
          backgroundColor: 'rgba(16, 185, 129, 0.08)',
          fill: true,
          data: [],
          borderWidth: 2,
          tension: 0.3,
          pointRadius: 0
        },
        {
          label: 'HDOP (Horizontal)',
          borderColor: '#06b6d4',
          data: [],
          borderWidth: 1.5,
          tension: 0.3,
          pointRadius: 0
        },
        {
          label: 'VDOP (Vertical)',
          borderColor: '#818cf8',
          data: [],
          borderWidth: 1.5,
          tension: 0.3,
          pointRadius: 0
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      plugins: {
        legend: {
          labels: { color: '#94a3b8', font: { family: 'Inter', size: 10 } }
        }
      },
      scales: {
        x: {
          ticks: { color: '#64748b', font: { family: 'JetBrains Mono', size: 9 }, maxTicksLimit: 8 },
          grid: { color: 'rgba(51, 65, 85, 0.3)' }
        },
        y: {
          beginAtZero: true,
          suggestedMin: 0,
          suggestedMax: 12,
          ticks: { color: '#64748b', font: { family: 'JetBrains Mono', size: 9 } },
          grid: { color: 'rgba(51, 65, 85, 0.3)' }
        }
      }
    }
  });
}

// 3. Conexão WebSocket com Reconexão Automática
function connectWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/ws/telemetry`;

  ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    document.getElementById('ws-status').innerText = 'STREAMING ATIVO';
    document.getElementById('ws-indicator').className = 'w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse';
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      updateDashboard(data);
    } catch (e) {
      console.error("Erro ao processar telemetria:", e);
    }
  };

  ws.onclose = () => {
    document.getElementById('ws-status').innerText = 'RECONECTANDO...';
    document.getElementById('ws-indicator').className = 'w-2.5 h-2.5 rounded-full bg-amber-500 animate-ping';
    setTimeout(connectWebSocket, 2000);
  };

  ws.onerror = () => {
    ws.close();
  };
}

// 4. Atualização Central de Todo o Dashboard
function updateDashboard(data) {
  const sim = data.simulation;
  const dop = data.dop;
  const sats = data.satellites;
  const atm = data.atmospheric;

  // Atualiza Relógio e Estado de Execução
  document.getElementById('sim-time').innerText = sim.time_str;
  document.getElementById('sim-multiplier').innerText = `${sim.multiplier}x`;
  isPaused = sim.is_paused;
  
  const pauseBtn = document.getElementById('btn-pause');
  if (isPaused) {
    pauseBtn.innerHTML = '▶️ Retomar';
    pauseBtn.className = "px-3 py-2 rounded-xl bg-emerald-700 hover:bg-emerald-600 text-xs font-semibold text-white border border-emerald-500 shadow-lg shadow-emerald-700/30 transition";
  } else {
    pauseBtn.innerHTML = '⏸️ Pausar';
    pauseBtn.className = "px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-white border border-slate-700 transition";
  }

  const modeBadge = document.getElementById('sim-mode-badge');
  if (modeBadge) {
    if (sim.mode === 'MASTER_GAZEBO') {
      modeBadge.innerText = isPaused ? '⏸️ GAZEBO (PAUSADO)' : '🛰️ MASTER: GAZEBO';
      modeBadge.className = isPaused
        ? 'text-[9px] font-mono px-2 py-0.5 rounded-full bg-rose-950 text-rose-300 border border-rose-800 font-bold'
        : 'text-[9px] font-mono px-2 py-0.5 rounded-full bg-cyan-950 text-cyan-300 border border-cyan-800 font-bold';
    } else {
      modeBadge.innerText = isPaused ? '⏸️ AUTÔNOMO (PAUSADO)' : '⚡ STANDALONE';
      modeBadge.className = isPaused
        ? 'text-[9px] font-mono px-2 py-0.5 rounded-full bg-rose-950 text-rose-300 border border-rose-800'
        : 'text-[9px] font-mono px-2 py-0.5 rounded-full bg-amber-950 text-amber-300 border border-amber-800';
    }
  }

  // Atualiza Estações no Dropdown se ainda não populadas
  if (!stationsPopulated && data.stations) {
    const sel = document.getElementById('station-selector');
    sel.innerHTML = '';
    data.stations.forEach(st => {
      const opt = document.createElement('option');
      opt.value = st;
      opt.innerText = st;
      if (st === sim.station_name) opt.selected = true;
      sel.appendChild(opt);
    });
    stationsPopulated = true;
  }

  document.getElementById('active-station-label').innerText = sim.station_name;

  // Atualiza Estação no Mapa
  if (sim.station_lat && sim.station_lon) {
    const staPos = [sim.station_lat, sim.station_lon];
    if (!stationMarker) {
      stationMarker = L.marker(staPos, { icon: stationIcon }).addTo(map)
        .bindPopup(`<b>Estação Base:</b> ${sim.station_name}<br>Lat: ${sim.station_lat.toFixed(2)}°, Lon: ${sim.station_lon.toFixed(2)}°`);
      stationCircle = L.circle(staPos, {
        color: '#10b981',
        fillColor: '#10b981',
        fillOpacity: 0.05,
        radius: 3500000 // Raio de cobertura aproximado
      }).addTo(map);
    } else {
      stationMarker.setLatLng(staPos);
      stationCircle.setLatLng(staPos);
    }
  }

  // Atualiza Métricas DOP
  document.getElementById('val-pdop').innerText = dop.pdop;
  document.getElementById('val-hdop').innerText = dop.hdop;
  document.getElementById('val-vdop').innerText = dop.vdop;
  document.getElementById('val-gdop').innerText = dop.gdop;
  document.getElementById('visible-sats-count').innerText = dop.visible_count;

  // Badge de Status do PDOP
  const badge = document.getElementById('dop-status-badge');
  badge.innerText = dop.status;
  if (dop.pdop <= 2.5) {
    badge.className = "px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-950 text-emerald-300 border border-emerald-800";
  } else if (dop.pdop <= 5.0) {
    badge.className = "px-2.5 py-0.5 rounded-full text-xs font-semibold bg-cyan-950 text-cyan-300 border border-cyan-800";
  } else {
    badge.className = "px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-950 text-rose-300 border border-rose-800";
  }

  // Atualiza Histórico do Gráfico (GDOP, PDOP, HDOP, VDOP)
  if (data.history && data.history.length > 0) {
    dopChart.data.labels = data.history.map(h => h.time_str);
    dopChart.data.datasets[0].data = data.history.map(h => (h.gdop !== undefined ? h.gdop : 0));
    dopChart.data.datasets[1].data = data.history.map(h => h.pdop);
    dopChart.data.datasets[2].data = data.history.map(h => h.hdop);
    dopChart.data.datasets[3].data = data.history.map(h => h.vdop);
    dopChart.update();
  }

  // Atualiza Marcadores e Trilhas dos Satélites no Mapa
  sats.forEach(sat => {
    const latLng = [sat.lat, sat.lon];
    const icon = sat.type === 'GEO' ? geoIcon : igsoIcon;

    if (!satMarkers[sat.id]) {
      satMarkers[sat.id] = L.marker(latLng, { icon: icon }).addTo(map)
        .bindPopup(`<b>${sat.name}</b> (${sat.type})<br>Lat: ${sat.lat.toFixed(2)}°<br>Lon: ${sat.lon.toFixed(2)}°<br>Alt: ${sat.alt_km} km`);
      satTrails[sat.id] = [];
    } else {
      satMarkers[sat.id].setLatLng(latLng);
      satMarkers[sat.id].setPopupContent(`<b>${sat.name}</b> (${sat.type})<br>Lat: ${sat.lat.toFixed(2)}°<br>Lon: ${sat.lon.toFixed(2)}°<br>Alt: ${sat.alt_km} km<br>Elevação: ${sat.elevation_deg}°`);
    }

    // Registra rastro para desenhar o analema dos IGSO
    if (sat.type === 'IGSO') {
      satTrails[sat.id].push(latLng);
      if (satTrails[sat.id].length > 100) satTrails[sat.id].shift();
    }
  });

  // Atualiza Tabela dos 7 Satélites
  const tbody = document.getElementById('satellite-table-body');
  tbody.innerHTML = '';
  sats.forEach(sat => {
    const tr = document.createElement('tr');
    tr.className = sat.in_view ? "hover:bg-slate-800/40 text-slate-200" : "opacity-40 hover:bg-slate-800/40 text-slate-500";
    
    const statusBadge = sat.in_view 
      ? `<span class="px-2 py-0.5 rounded text-[10px] bg-emerald-950 text-emerald-400 border border-emerald-800/60 font-semibold">ATIVO (LOS)</span>`
      : `<span class="px-2 py-0.5 rounded text-[10px] bg-slate-900 text-slate-500 border border-slate-800">SOB MÁSCARA</span>`;

    const typeColor = sat.type === 'GEO' ? 'text-cyan-400' : 'text-amber-400';

    tr.innerHTML = `
      <td class="py-2 px-3 font-bold text-slate-400">${String(sat.id).padStart(2, '0')}</td>
      <td class="py-2 px-3 font-semibold text-white">${sat.name}</td>
      <td class="py-2 px-3 ${typeColor} font-bold">${sat.type}</td>
      <td class="py-2 px-3">${sat.lat.toFixed(2)}°</td>
      <td class="py-2 px-3">${sat.lon.toFixed(2)}°</td>
      <td class="py-2 px-3">${sat.alt_km.toLocaleString()}</td>
      <td class="py-2 px-3">${sat.azimuth_deg.toFixed(1)}°</td>
      <td class="py-2 px-3 font-bold ${sat.in_view ? 'text-emerald-300' : 'text-slate-500'}">${sat.elevation_deg.toFixed(1)}°</td>
      <td class="py-2 px-3">${statusBadge}</td>
    `;
    tbody.appendChild(tr);
  });

  // Atualiza Cards de Retardo Troposférico (Saastamoinen)
  const tropoContainer = document.getElementById('tropo-cards');
  tropoContainer.innerHTML = '';
  sats.filter(s => s.in_view).forEach(sat => {
    const card = document.createElement('div');
    card.className = "bg-slate-950/70 p-2.5 rounded-xl border border-slate-800/70 text-xs";
    card.innerHTML = `
      <div class="flex items-center justify-between font-mono mb-1">
        <span class="font-bold text-slate-200">${sat.name}</span>
        <span class="text-cyan-400 text-[10px]">${sat.elevation_deg.toFixed(1)}° El</span>
      </div>
      <div class="flex items-baseline justify-between font-mono">
        <span class="text-[10px] text-slate-500">Atraso Δρ:</span>
        <span class="font-bold text-emerald-400">${sat.tropo_m.toFixed(3)} m</span>
      </div>
      <div class="flex items-baseline justify-between font-mono">
        <span class="text-[10px] text-slate-500">Tempo τ:</span>
        <span class="text-slate-300 text-[11px]">${sat.tropo_ns.toFixed(1)} ns</span>
      </div>
    `;
    tropoContainer.appendChild(card);
  });
}

// 5. Funções de Controle Interativo
function togglePause() {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ pause: !isPaused }));
  }
}

function setSpeed(mult) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ multiplier: mult }));
  }
}

function setMask(deg) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ mask: deg }));
  }
}

function changeStation(stationName) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ station: stationName }));
  }
}

// 6. Alternância de Visualização Geoespacial (2D Leaflet vs 3D Cesium)
function setGeoView(mode) {
  const mapContainer = document.getElementById('map-container');
  const cesiumFrame = document.getElementById('cesium-frame');
  const btn2d = document.getElementById('btn-view-2d');
  const btn3d = document.getElementById('btn-view-3d');

  if (mode === '3d') {
    mapContainer.classList.add('hidden');
    cesiumFrame.classList.remove('hidden');
    btn3d.className = 'px-3 py-1 text-xs font-semibold rounded-lg bg-slate-800 text-amber-300 transition';
    btn2d.className = 'px-3 py-1 text-xs font-semibold rounded-lg text-slate-400 hover:text-white transition';
  } else {
    cesiumFrame.classList.add('hidden');
    mapContainer.classList.remove('hidden');
    btn2d.className = 'px-3 py-1 text-xs font-semibold rounded-lg bg-slate-800 text-cyan-300 transition';
    btn3d.className = 'px-3 py-1 text-xs font-semibold rounded-lg text-slate-400 hover:text-white transition';
    if (map) {
      map.invalidateSize();
    }
  }
}

