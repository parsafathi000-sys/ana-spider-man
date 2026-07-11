/* Spider Panel — Animated Background (Canvas API, no external libs)
   Dark-red neon spider-web + drifting particles + glow + parallax + pointer/touch.
   Lightweight: caps DPR, pauses when tab hidden, throttled to ~60fps. */
(function () {
  const canvas = document.getElementById("bg-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  let W = 0, H = 0, DPR = 1;
  const reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // Configuration
  const CONFIG = {
    nodes: 26,
    nodeSpeed: 0.18,
    nodeSize: { min: 1.2, max: 3.0 },
    connectionDistance: 150,
    connectionOpacity: 0.22,
    particleDensity: 42000, // px^2 per particle
    particleSpeed: 0.25,
    particleSize: { min: 0.6, max: 2.0 },
    particleAlpha: { min: 0.2, max: 0.55 },
    parallaxStrength: 0.0004,
    nodeParallaxStrength: 0.0003,
    mouseInfluenceRadius: 300,
    glowEnabled: true,
  };

  const nodes = [];
  const particles = [];
  const mouse = { x: 0, y: 0, tx: 0, ty: 0, active: false };
  let raf = null, last = 0;

  function resize() {
    DPR = Math.min(window.devicePixelRatio || 1, 2);
    W = canvas.clientWidth = window.innerWidth;
    H = canvas.clientHeight = window.innerHeight;
    canvas.width = Math.floor(W * DPR);
    canvas.height = Math.floor(H * DPR);
    ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
    seed();
  }

  function seed() {
    nodes.length = 0; particles.length = 0;

    // Spider web nodes
    for (let i = 0; i < CONFIG.nodes; i++) {
      nodes.push({
        x: Math.random() * W,
        y: Math.random() * H,
        vx: (Math.random() - 0.5) * CONFIG.nodeSpeed,
        vy: (Math.random() - 0.5) * CONFIG.nodeSpeed,
        r: CONFIG.nodeSize.min + Math.random() * (CONFIG.nodeSize.max - CONFIG.nodeSize.min),
        phase: Math.random() * Math.PI * 2,
      });
    }

    // Drifting particles
    const pn = Math.round((W * H) / CONFIG.particleDensity);
    for (let i = 0; i < pn; i++) {
      particles.push({
        x: Math.random() * W,
        y: Math.random() * H,
        vx: (Math.random() - 0.5) * CONFIG.particleSpeed,
        vy: (Math.random() - 0.5) * CONFIG.particleSpeed,
        r: CONFIG.particleSize.min + Math.random() * (CONFIG.particleSize.max - CONFIG.particleSize.min),
        a: CONFIG.particleAlpha.min + Math.random() * (CONFIG.particleAlpha.max - CONFIG.particleAlpha.min),
      });
    }
  }

  function step(t) {
    raf = requestAnimationFrame(step);
    if (t - last < 16) return; // ~60fps cap
    last = t;

    ctx.clearRect(0, 0, W, H);

    // Smooth mouse following
    mouse.x += (mouse.tx - mouse.x) * 0.06;
    mouse.y += (mouse.ty - mouse.y) * 0.06;

    // Parallax offset
    const px = mouse.active ? (mouse.x - W / 2) * CONFIG.parallaxStrength : 0;
    const py = mouse.active ? (mouse.y - H / 2) * CONFIG.parallaxStrength : 0;
    const npX = mouse.active ? (mouse.x - W / 2) * CONFIG.nodeParallaxStrength : 0;
    const npY = mouse.active ? (mouse.y - H / 2) * CONFIG.nodeParallaxStrength : 0;

    // Particles
    for (const p of particles) {
      p.x += p.vx + px;
      p.y += p.vy + py;
      // Wrap around
      if (p.x < -10) p.x = W + 10;
      if (p.x > W + 10) p.x = -10;
      if (p.y < -10) p.y = H + 10;
      if (p.y > H + 10) p.y = -10;

      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(255,90,120,${p.a})`;
      ctx.fill();
    }

    // Spider web nodes & connections
    for (let i = 0; i < nodes.length; i++) {
      const n = nodes[i];
      n.x += n.vx + npX;
      n.y += n.vy + npY;

      // Bounce off edges
      if (n.x < 0 || n.x > W) n.vx *= -1;
      if (n.y < 0 || n.y > H) n.vy *= -1;
      n.x = Math.max(0, Math.min(W, n.x));
      n.y = Math.max(0, Math.min(H, n.y));

      // Connections to nearby nodes
      for (let j = i + 1; j < nodes.length; j++) {
        const m = nodes[j];
        const dx = n.x - m.x;
        const dy = n.y - m.y;
        const d = Math.hypot(dx, dy);
        if (d < CONFIG.connectionDistance) {
          ctx.beginPath();
          ctx.moveTo(n.x, n.y);
          ctx.lineTo(m.x, m.y);
          const a = (1 - d / CONFIG.connectionDistance) * CONFIG.connectionOpacity;
          ctx.strokeStyle = `rgba(255,45,85,${a})`;
          ctx.lineWidth = 1;
          ctx.stroke();
        }
      }

      // Node glow
      if (CONFIG.glowEnabled) {
        const grad = ctx.createRadialGradient(n.x, n.y, 0, n.x, n.y, n.r * 4);
        grad.addColorStop(0, `rgba(255,138,163,0.35)`);
        grad.addColorStop(1, `rgba(255,45,85,0)`);
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.r * 4, 0, Math.PI * 2);
        ctx.fillStyle = grad;
        ctx.fill();
      }

      // Node core
      ctx.beginPath();
      ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
      ctx.fillStyle = "rgba(255,138,163,0.55)";
      ctx.fill();
    }
  }

  function start() {
    if (!raf && !reduce) raf = requestAnimationFrame(step);
  }
  function stop() {
    if (raf) { cancelAnimationFrame(raf); raf = null; }
  }

  function onMove(x, y) {
    mouse.tx = x; mouse.ty = y; mouse.active = true;
  }

  window.addEventListener("mousemove", (e) => onMove(e.clientX, e.clientY), { passive: true });
  window.addEventListener("touchmove", (e) => { const t = e.touches[0]; if (t) onMove(t.clientX, t.clientY); }, { passive: true });
  window.addEventListener("mouseleave", () => { mouse.active = false; });
  window.addEventListener("resize", resize);
  document.addEventListener("visibilitychange", () => { document.hidden ? stop() : start(); });

  resize();
  start();
})();