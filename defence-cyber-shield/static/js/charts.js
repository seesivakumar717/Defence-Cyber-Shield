/* Defence Cyber Shield — analytics charts (Chart.js) */
(function () {
  "use strict";
  if (typeof Chart === "undefined") return;

  Chart.defaults.color = "#85a0b3";
  Chart.defaults.font.family = "'Chakra Petch', sans-serif";
  Chart.defaults.borderColor = "rgba(255,255,255,0.06)";

  const el = document.getElementById("chart-data");
  if (!el) return;
  const data = JSON.parse(el.textContent);

  /* Risk distribution — doughnut */
  const riskCtx = document.getElementById("riskDistributionChart");
  if (riskCtx) {
    new Chart(riskCtx, {
      type: "doughnut",
      data: {
        labels: ["Low", "Medium", "High"],
        datasets: [{
          data: [data.risk_counts.Low, data.risk_counts.Medium, data.risk_counts.High],
          backgroundColor: ["#22e08c", "#ffb020", "#ff3b45"],
          borderColor: "#0c1a26",
          borderWidth: 3,
        }],
      },
      options: {
        plugins: { legend: { position: "bottom" } },
        cutout: "68%",
      },
    });
  }

  /* Incident status — bar */
  const statusCtx = document.getElementById("incidentStatusChart");
  if (statusCtx) {
    new Chart(statusCtx, {
      type: "bar",
      data: {
        labels: ["Pending", "Open", "Resolved"],
        datasets: [{
          label: "Incidents",
          data: [data.incident_counts.Pending, data.incident_counts.Open, data.incident_counts.Resolved],
          backgroundColor: ["#ffb020", "#00e0ff", "#22e08c"],
          borderRadius: 6,
          maxBarThickness: 46,
        }],
      },
      options: {
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false } },
          y: { beginAtZero: true, ticks: { precision: 0 }, grid: { color: "rgba(255,255,255,0.06)" } },
        },
      },
    });
  }

  /* Monthly trend — line */
  const trendCtx = document.getElementById("monthlyTrendChart");
  if (trendCtx) {
    const gradient = trendCtx.getContext("2d").createLinearGradient(0, 0, 0, 260);
    gradient.addColorStop(0, "rgba(0, 224, 255, 0.35)");
    gradient.addColorStop(1, "rgba(0, 224, 255, 0)");

    new Chart(trendCtx, {
      type: "line",
      data: {
        labels: data.monthly_trend.map((m) => m.month),
        datasets: [{
          label: "Scans",
          data: data.monthly_trend.map((m) => m.count),
          borderColor: "#00e0ff",
          backgroundColor: gradient,
          fill: true,
          tension: 0.35,
          pointBackgroundColor: "#00e0ff",
          pointRadius: 4,
        }],
      },
      options: {
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false } },
          y: { beginAtZero: true, ticks: { precision: 0 }, grid: { color: "rgba(255,255,255,0.06)" } },
        },
      },
    });
  }

  /* Top threat types — horizontal bar (derived from indicator categories) */
  const threatCtx = document.getElementById("topThreatsChart");
  if (threatCtx && data.top_threats) {
    new Chart(threatCtx, {
      type: "bar",
      data: {
        labels: data.top_threats.map((t) => t.label),
        datasets: [{
          data: data.top_threats.map((t) => t.count),
          backgroundColor: "#8fae3f",
          borderRadius: 6,
          maxBarThickness: 26,
        }],
      },
      options: {
        indexAxis: "y",
        plugins: { legend: { display: false } },
        scales: {
          x: { beginAtZero: true, ticks: { precision: 0 }, grid: { color: "rgba(255,255,255,0.06)" } },
          y: { grid: { display: false } },
        },
      },
    });
  }
})();
