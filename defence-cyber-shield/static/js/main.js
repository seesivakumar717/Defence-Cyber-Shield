/* Defence Cyber Shield — core interactions */
(function () {
  "use strict";

  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ----------------------------------------------------------------
     Boot loader
     ---------------------------------------------------------------- */
  window.addEventListener("load", function () {
    const loader = document.getElementById("boot-loader");
    if (!loader) return;
    setTimeout(() => loader.classList.add("hidden"), reduceMotion ? 0 : 550);
  });

  /* ----------------------------------------------------------------
     Sidebar toggle (mobile)
     ---------------------------------------------------------------- */
  const sidebarToggle = document.getElementById("sidebar-toggle");
  const sidebar = document.getElementById("app-sidebar");
  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener("click", () => sidebar.classList.toggle("open"));
    document.addEventListener("click", (e) => {
      if (window.innerWidth > 900) return;
      if (!sidebar.contains(e.target) && !sidebarToggle.contains(e.target)) {
        sidebar.classList.remove("open");
      }
    });
  }

  /* ----------------------------------------------------------------
     Particle background canvas
     ---------------------------------------------------------------- */
  const canvas = document.getElementById("particle-canvas");
  if (canvas && !reduceMotion) {
    const ctx = canvas.getContext("2d");
    let particles = [];
    let w, h;

    function resize() {
      w = canvas.width = window.innerWidth;
      h = canvas.height = window.innerHeight;
    }
    window.addEventListener("resize", resize);
    resize();

    const COUNT = Math.min(70, Math.floor((w * h) / 22000));
    for (let i = 0; i < COUNT; i++) {
      particles.push({
        x: Math.random() * w,
        y: Math.random() * h,
        vx: (Math.random() - 0.5) * 0.25,
        vy: (Math.random() - 0.5) * 0.25,
        r: Math.random() * 1.6 + 0.4,
      });
    }

    function step() {
      ctx.clearRect(0, 0, w, h);
      ctx.fillStyle = "rgba(0, 224, 255, 0.55)";
      ctx.strokeStyle = "rgba(0, 224, 255, 0.12)";

      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0 || p.x > w) p.vx *= -1;
        if (p.y < 0 || p.y > h) p.vy *= -1;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fill();

        for (let j = i + 1; j < particles.length; j++) {
          const q = particles[j];
          const dx = p.x - q.x, dy = p.y - q.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 120) {
            ctx.globalAlpha = 1 - dist / 120;
            ctx.beginPath();
            ctx.moveTo(p.x, p.y);
            ctx.lineTo(q.x, q.y);
            ctx.stroke();
            ctx.globalAlpha = 1;
          }
        }
      }
      requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  /* ----------------------------------------------------------------
     Typing animation (hero)
     ---------------------------------------------------------------- */
  const typedEl = document.getElementById("typed-line");
  if (typedEl) {
    const lines = JSON.parse(typedEl.dataset.lines || "[]");
    let lineIdx = 0, charIdx = 0, deleting = false;

    function tick() {
      const current = lines[lineIdx];
      if (!deleting) {
        charIdx++;
        typedEl.textContent = current.slice(0, charIdx);
        if (charIdx === current.length) {
          deleting = true;
          setTimeout(tick, 1600);
          return;
        }
      } else {
        charIdx--;
        typedEl.textContent = current.slice(0, charIdx);
        if (charIdx === 0) {
          deleting = false;
          lineIdx = (lineIdx + 1) % lines.length;
        }
      }
      setTimeout(tick, deleting ? 28 : 55);
    }
    if (lines.length) tick();
  }

  /* ----------------------------------------------------------------
     Upload dropzone + preview
     ---------------------------------------------------------------- */
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("screenshot-input");
  const previewFrame = document.getElementById("preview-frame");
  const previewImg = document.getElementById("preview-img");
  const analyzeBtn = document.getElementById("analyze-btn");
  const uploadForm = document.getElementById("upload-form");

  if (dropzone && fileInput) {
    dropzone.addEventListener("click", () => fileInput.click());

    ["dragenter", "dragover"].forEach((evt) =>
      dropzone.addEventListener(evt, (e) => {
        e.preventDefault();
        dropzone.classList.add("dragover");
      })
    );
    ["dragleave", "drop"].forEach((evt) =>
      dropzone.addEventListener(evt, (e) => {
        e.preventDefault();
        dropzone.classList.remove("dragover");
      })
    );
    dropzone.addEventListener("drop", (e) => {
      const files = e.dataTransfer.files;
      if (files && files.length) {
        fileInput.files = files;
        showPreview(files[0]);
      }
    });
    fileInput.addEventListener("change", () => {
      if (fileInput.files && fileInput.files[0]) showPreview(fileInput.files[0]);
    });

    function showPreview(file) {
      if (!file.type.startsWith("image/")) return;
      const reader = new FileReader();
      reader.onload = (e) => {
        previewImg.src = e.target.result;
        previewFrame.classList.remove("d-none");
        dropzone.classList.add("d-none");
        if (analyzeBtn) analyzeBtn.disabled = false;
      };
      reader.readAsDataURL(file);
    }

    const removeBtn = document.getElementById("remove-preview");
    if (removeBtn) {
      removeBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        fileInput.value = "";
        previewFrame.classList.add("d-none");
        dropzone.classList.remove("d-none");
        if (analyzeBtn) analyzeBtn.disabled = true;
      });
    }
  }

  if (uploadForm) {
    uploadForm.addEventListener("submit", () => {
      if (analyzeBtn) {
        analyzeBtn.disabled = true;
        analyzeBtn.innerHTML =
          '<span class="spinner-border spinner-border-sm me-2"></span>Analyzing threat signature…';
      }
    });
  }

  /* ----------------------------------------------------------------
     Risk gauge animation
     ---------------------------------------------------------------- */
  const gauge = document.querySelector(".gauge-fill");
  if (gauge) {
    const score = parseFloat(gauge.dataset.score || "0");
    const radius = parseFloat(gauge.getAttribute("r"));
    const circumference = 2 * Math.PI * radius;
    gauge.style.strokeDasharray = `${circumference}`;
    gauge.style.strokeDashoffset = `${circumference}`;

    let color = "#22e08c";
    if (score > 60) color = "#ff3b45";
    else if (score > 30) color = "#ffb020";
    gauge.style.stroke = color;

    requestAnimationFrame(() => {
      const offset = circumference - (score / 100) * circumference;
      gauge.style.strokeDashoffset = `${offset}`;
    });

    const scoreLabel = document.getElementById("gauge-score-label");
    if (scoreLabel) {
      let current = 0;
      const target = Math.round(score);
      const duration = 1200;
      const start = performance.now();
      function animateNumber(now) {
        const progress = Math.min((now - start) / duration, 1);
        current = Math.round(progress * target);
        scoreLabel.textContent = current;
        if (progress < 1) requestAnimationFrame(animateNumber);
      }
      requestAnimationFrame(animateNumber);
    }
  }

  /* ----------------------------------------------------------------
     Incident detail modal (admin incidents page)
     ---------------------------------------------------------------- */
  const incidentModalEl = document.getElementById("incidentModal");
  if (incidentModalEl && window.bootstrap) {
    const modal = new bootstrap.Modal(incidentModalEl);
    document.querySelectorAll("[data-incident-id]").forEach((trigger) => {
      trigger.addEventListener("click", async () => {
        const id = trigger.dataset.incidentId;
        const body = document.getElementById("incidentModalBody");
        body.innerHTML = '<div class="text-center py-5"><span class="spinner-border text-info"></span></div>';
        modal.show();
        try {
          const res = await fetch(`/admin/incidents/${id}`);
          const data = await res.json();
          body.innerHTML = renderIncidentDetail(data);
        } catch (err) {
          body.innerHTML = '<p class="text-red">Failed to load incident detail.</p>';
        }
      });
    });
  }

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str || "";
    return div.innerHTML;
  }

  function renderIncidentDetail(d) {
    const indicators = (d.indicators || [])
      .map((i) => `<li class="mono small text-dim">${escapeHtml(i)}</li>`)
      .join("");
    return `
      <div class="row g-4">
        <div class="col-md-5">
          <div class="preview-frame mb-3">
            <img src="${d.uploaded_image}" alt="Reported screenshot" style="max-height:280px;object-fit:contain;">
          </div>
          <p class="mono small text-dim mb-1">SOLDIER</p>
          <p class="mb-1">${escapeHtml(d.soldier_name)} <span class="text-dim">(${escapeHtml(d.soldier_army_id)})</span></p>
          <p class="mono small text-dim">${escapeHtml(d.soldier_email)}</p>
        </div>
        <div class="col-md-7">
          <div class="d-flex align-items-center gap-2 mb-3">
            <span class="risk-badge ${d.risk_level.toLowerCase()}">${d.risk_level} · ${d.risk_score}</span>
            <span class="status-badge ${d.status.toLowerCase()}">${d.status}</span>
          </div>
          <p class="mono small text-dim mb-1">RECOMMENDATION</p>
          <p class="mb-3">${escapeHtml(d.recommendation)}</p>
          <p class="mono small text-dim mb-1">TRIGGERED INDICATORS</p>
          <ul class="mb-3 ps-3">${indicators || '<li class="text-dim small">None recorded</li>'}</ul>
          <p class="mono small text-dim mb-1">OCR EXTRACTED TEXT</p>
          <div class="glass p-3 mono small" style="max-height:160px;overflow-y:auto;white-space:pre-wrap;">${escapeHtml(d.ocr_text) || "(no text extracted)"}</div>
        </div>
      </div>`;
  }
})();
