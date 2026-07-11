/* =========================================================================
   Spider Panel — app.js (Unified SPA Controller)
   Mobile-first, cookie session + CSRF, page routing, FAB, modal, toast.
   ========================================================================= */
(function () {
  "use strict";

  // ===== DOM Utilities =====
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
  const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, c => ({
    "&": "\u0026",
    "<": "\u003C",
    ">": "\u003E",
    '"': "\u201D",
    "'": "\u2019"
  }[c]));

  // ===== Toast =====
  function toast(msg, kind = "") {
    const w = $("#toast-wrap");
    if (!w) return;
    const t = document.createElement("div");
    t.className = "toast " + kind;
    t.textContent = msg;
    w.appendChild(t);
    setTimeout(() => { t.style.opacity = "0"; setTimeout(() => t.remove(), 300); }, 2600);
  }

  // ===== Modal =====
  function modal(html, onMount) {
    const back = $("#modal");
    const card = $("#modal-card");
    card.innerHTML = html;
    back.hidden = false;
    if (onMount) onMount(card);
    back.onclick = (e) => { if (e.target === back) closeModal(); };
    const x = $(".modal-close", card);
    if (x) x.onclick = closeModal;
    return card;
  }
  function closeModal() {
    const b = $("#modal");
    b.hidden = true;
    $("#modal-card").innerHTML = "";
  }
  window.closeModal = closeModal;

  // ===== Copy to Clipboard =====
  async function copy(text, label) {
    try {
      await navigator.clipboard.writeText(text);
      toast(label || "Copied", "ok");
    } catch (_) {
      const ta = document.createElement("textarea");
      ta.value = text; document.body.appendChild(ta); ta.select();
      try { document.execCommand("copy"); toast(label || "Copied", "ok"); }
      catch { toast("Copy failed", "err"); }
      ta.remove();
    }
  }
  window.copy = copy;

  // ===== API Helper (Cookie Session + CSRF) =====
  let CSRF = "";
  async function api(method, path, body, isForm) {
    const headers = {};
    if (body && !isForm) headers["Content-Type"] = "application/json";
    if (CSRF) headers["X-CSRF-Token"] = CSRF;
    headers["X-Requested-With"] = "SpiderSPA";
    const opt = { method, headers, credentials: "same-origin" };
    if (body) opt.body = isForm ? body : JSON.stringify(body);
    const r = await fetch(path, opt);
    if (r.status === 401) { location.href = "/login"; throw new Error("unauthorized"); }
    let data = null;
    try { data = await r.json(); } catch (_) {}
    if (!r.ok) throw new Error((data && data.detail) || ("HTTP " + r.status));
    return data;
  }

  // ===== Debounce =====
  function debounce(fn, ms) { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; }

  // ===== Ripple on Buttons =====
  document.addEventListener("pointerdown", (e) => {
    const b = e.target.closest(".btn");
    if (!b) return;
    const r = b.getBoundingClientRect();
    const d = Math.max(r.width, r.height) * 2;
    const s = document.createElement("span");
    s.className = "ripple";
    s.style.width = s.style.height = d + "px";
    s.style.left = e.clientX - r.left - d / 2 + "px";
    s.style.top = e.clientY - r.top - d / 2 + "px";
    b.appendChild(s);
    setTimeout(() => s.remove(), 600);
  });

  // ===== Sidebar & Scrim =====
  function openSidebar() { $("#sidebar")?.classList.add("open"); $("#scrim")?.classList.add("show"); }
  function closeSidebar() { $("#sidebar")?.classList.remove("open"); $("#scrim")?.classList.remove("show"); }

  function bindShell() {
    const mb = $("#menu-btn"); if (mb) mb.onclick = openSidebar;
    const sc = $("#scrim"); if (sc) sc.onclick = closeSidebar;
    const lo = $("#logout-btn"); if (lo) lo.onclick = logout;
    $$(".nav-item").forEach(a => a.addEventListener("click", () => {
      closeSidebar();
      if (a.dataset.go) location.href = a.dataset.go;
    }));
  }

  async function logout() {
    try { await api("POST", "/api/auth/logout"); } catch (_) {}
    location.href = "/login";
  }

  // ===== FAB (Telegram Contact) - Draggable, Auto-Collapse =====
  function initFab() {
    const fab = $("#tg-fab");
    if (!fab) return;

    let collapsed = false, timer = null;
    const collapse = () => { fab.classList.remove("expanded"); collapsed = true; };
    const expand = () => { fab.classList.add("expanded"); collapsed = false; clearTimeout(timer); timer = setTimeout(collapse, 3000); };
    timer = setTimeout(collapse, 3000);
    fab.addEventListener("click", (e) => { if (fab._dragging) return; expand(); });

    // Drag
    let sx = 0, sy = 0, ox = 0, oy = 0, dragging = false;
    const isTouch = matchMedia("(pointer: coarse)").matches;
    function down(e) {
      dragging = false; fab._dragging = false;
      const p = e.touches ? e.touches[0] : e;
      sx = p.clientX; sy = p.clientY;
      const r = fab.getBoundingClientRect();
      ox = r.left; oy = r.top;
      window.addEventListener(isTouch ? "touchmove" : "mousemove", move);
      window.addEventListener(isTouch ? "touchend" : "mouseup", up);
    }
    function move(e) {
      const p = e.touches ? e.touches[0] : e;
      const dx = p.clientX - sx, dy = p.clientY - sy;
      if (Math.abs(dx) > 4 || Math.abs(dy) > 4) { dragging = true; fab._dragging = true; }
      if (!dragging) return;
      e.preventDefault();
      let nl = ox + dx, nt = oy + dy;
      nl = Math.max(6 + (parseFloat(getComputedStyle(document.documentElement).getPropertyValue("--safe-left")) || 0), Math.min(window.innerWidth - fab.offsetWidth - 6, nl));
      nt = Math.max(6 + (parseFloat(getComputedStyle(document.documentElement).getPropertyValue("--safe-top")) || 0), Math.min(window.innerHeight - fab.offsetHeight - 6, nt));
      fab.style.left = nl + "px"; fab.style.top = nt + "px";
      fab.style.right = "auto"; fab.style.bottom = "auto";
    }
    function up() {
      window.removeEventListener(isTouch ? "touchmove" : "mousemove", move);
      window.removeEventListener(isTouch ? "touchend" : "mouseup", up);
      if (dragging) setTimeout(() => { fab._dragging = false; }, 50);
    }
    fab.addEventListener(isTouch ? "touchstart" : "mousedown", down);
  }

  // ===== URI Parser for Config Cards =====
  function parseUri(uri) {
    try {
      const q = uri.split("?")[1] || "";
      const m = new URLSearchParams(q);
      let proto = "VLESS";
      const t = m.get("type");
      if (t === "xhttp") proto = "XHTTP";
      else if (t === "ws") proto = "WebSocket";
      else if (t === "grpc") proto = "gRPC";
      else if (t === "tcp") proto = "TCP";
      const sec = m.get("security") || "none";
      return { proto, security: sec };
    } catch (_) { return { proto: "VLESS", security: "none" }; }
  }
  function protoIcon(p) {
    return { XHTTP: "protocol_xhttp", WebSocket: "protocol_ws", gRPC: "protocol_grpc", TCP: "protocol_tcp", VLESS: "sub", Reality: "lock" }[p] || "sub";
  }

  function fmtBytes(n) {
    n = Number(n) || 0; const u = ["B", "KB", "MB", "GB", "TB"]; let i = 0;
    while (n >= 1024 && i < u.length - 1) { n /= 1024; i++; }
    return n.toFixed(i ? 2 : 0) + " " + u[i];
  }

  // ===== QR Modal =====
  function showQr(uuid, index) {
    modal(`
      <button class="modal-close">${ICON("close")}</button>
      <h3>QR Code</h3>
      <div class="qr-box"><img src="/api/qr/${uuid}/raw?index=${index}" alt="QR" loading="lazy"></div>
      <p class="muted" style="text-align:center">Scan with your VPN client.</p>
    `);
  }
  window.showQr = showQr;

  // ===== Page: Login =====
  async function bootLogin() {
    initFab();
    $("#login-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const u = $("#username").value.trim(), pw = $("#password").value;
      const err = $("#login-error"); err.textContent = "";
      try {
        const r = await fetch("/api/auth/login", {
          method: "POST", headers: { "Content-Type": "application/json", "X-Requested-With": "SpiderSPA" },
          body: JSON.stringify({ username: u, password: pw }),
        });
        const d = await r.json();
        if (!r.ok) { err.textContent = d.detail || "Login failed"; return; }
        CSRF = d.csrf_token || "";
        location.href = "/dashboard";
      } catch (ex) { err.textContent = ex.message || "Login failed"; }
    });
    const tp = $(".toggle-pw");
    if (tp) tp.onclick = () => { const i = $("#password"); i.type = i.type === "password" ? "text" : "password"; };
  }

  // ===== Page: Dashboard =====
  async function bootDashboard() {
    bindShell(); initFab();
    try {
      const s = await api("GET", "/api/dashboard/stats");
      const cards = [
        { k: "Users", v: s.total_users, icon: "users" },
        { k: "Online", v: s.online_connections, icon: "online" },
        { k: "Expired", v: s.expired_users, icon: "clock" },
        { k: "Disabled", v: s.disabled_users, icon: "disable" },
        { k: "Inbounds", v: "\u2014", icon: "inbounds", href: "/inbounds" },
        { k: "Settings", v: "\u2014", icon: "settings", href: "/settings" },
        { k: "Subscription", v: "\u2014", icon: "subscription", href: "/subscription" },
        { k: "Domains", v: "\u2014", icon: "domains", href: "/domains" },
      ];
      $("#content").innerHTML = `
        <h3>Statistics</h3>
        <div class="grid stats-grid">
          ${cards.map(c => `
            <div class="card stat-card" ${c.href ? `data-go="${c.href}" style="cursor:pointer"` : ""}>
              <div class="icon-box">${ICON(c.icon)}</div>
              <div class="meta"><div class="k">${esc(c.k)}</div><div class="v">${esc(c.v)}</div></div>
            </div>
          `).join("")}
        </div>
        <div class="card" style="margin-top:var(--space-lg)">
          <div class="kv">
            <div class="key">Xray</div><div class="val ${s.xray_running ? "ok" : "error-text"}">${s.xray_running ? "running" : "stopped"}</div>
            ${s.extra && s.extra.version ? `<div class="key">Version</div><div class="val">${esc(s.extra.version)}</div>` : ""}
            <div class="key">CPU</div><div class="val">${s.cpu_percent == null ? "n/a" : s.cpu_percent + "%"}</div>
            <div class="key">Memory</div><div class="val">${s.memory_percent == null ? "n/a" : s.memory_percent + "%"}</div>
            <div class="key">Traffic</div><div class="val">${fmtBytes(s.total_traffic_bytes)}</div>
            ${s.extra && s.extra.last_error ? `<div class="key">Last error</div><div class="val error-text">${esc(s.extra.last_error)}</div>` : ""}
          </div>
        </div>
      `;
      $$("#content .stat-card[data-go]").forEach(el => el.onclick = () => location.href = el.dataset.go);
    } catch (ex) { $("#content").innerHTML = `<div class="empty">${esc(ex.message)}</div>`; }
  }

  // ===== Page: Users =====
  async function bootUsers() {
    bindShell(); initFab();
    const c = $("#content");
    c.innerHTML = `
      <div class="row" style="margin-bottom:var(--space-md)">
        <input id="u-search" class="field" placeholder="Search users..." style="flex:1;max-width:320px" />
        <button class="btn btn-primary" id="u-add">${ICON("plus")} Add</button>
      </div>
      <div id="u-list" class="tbl"><div class="empty">Loading\u2026</div></div>
    `;
    $("#u-add").onclick = showUserForm;
    let users = [];
    async function load() {
      try { users = await api("GET", "/api/users?search=" + encodeURIComponent($("#u-search").value)); }
      catch (ex) { users = []; toast(ex.message, "err"); }
      const list = $("#u-list");
      if (!users.length) { list.innerHTML = `<div class="empty">${ICON("users")}<div>No users yet.</div></div>`; return; }
      list.innerHTML = users.map(u => `
        <div class="tr">
          <div><strong>${esc(u.username)}</strong> <span class="badge ${u.enabled ? "on" : "off"}">${u.enabled ? "on" : "off"}</span></div>
          <div class="actions">
            <button class="btn btn-sm" data-act="sub" data-id="${u.id}">${ICON("sub")} Sub</button>
            <button class="btn btn-sm" data-act="edit" data-id="${u.id}">${ICON("edit")} Edit</button>
            <button class="btn btn-sm btn-danger" data-act="del" data-id="${u.id}">${ICON("trash")} Del</button>
          </div>
          <div class="grow">UUID: ${esc(u.uuid)} \u00b7 ${u.enabled_inbounds || "all inbounds"}</div>
        </div>
      `).join("");
      $$("#u-list [data-act]", list).forEach(b => b.onclick = () => {
        const id = +b.dataset.id; const u = users.find(x => x.id === id);
        if (b.dataset.act === "sub") openSubscription(u);
        else if (b.dataset.act === "edit") showUserForm(u);
        else if (b.dataset.act === "del") confirmDelete(u);
      });
    }
    $("#u-search").addEventListener("input", debounce(load, 350));
    await load();

    function showUserForm(u) {
      const ed = !!u;
      modal(`
        <button class="modal-close">${ICON("close")}</button>
        <h3>${ed ? "Edit user" : "New user"}</h3>
        <form id="uf">
          <div class="field"><label class="lbl">Username</label><input name="username" value="${ed ? esc(u.username) : ""}" required ${ed ? "disabled" : ""}></div>
          <div class="field"><label class="lbl">${ed ? "Extend expiry (days)" : "Expire days"}</label><input name="expire_days" type="number" value="${ed ? 30 : 30}" min="0"></div>
          <div class="field"><label class="lbl">Traffic limit (GB, 0=unlimited)</label><input name="traffic_limit_gb" type="number" value="${ed ? (u.traffic_limit_bytes / 1073741824).toFixed(1) : 0}" min="0" step="0.5"></div>
          <div class="field"><label class="lbl">IP limit (0=unlimited)</label><input name="ip_limit" type="number" value="${ed ? u.ip_limit : 0}" min="0"></div>
          <div class="modal-actions">
            <button type="button" class="btn btn-ghost" onclick="closeModal()">Cancel</button>
            <button class="btn btn-primary">${ed ? "Save" : "Create"}</button>
          </div>
        </form>
      `, (card) => {
        card.querySelector("#uf").onsubmit = async (e) => {
          e.preventDefault(); const f = Object.fromEntries(new FormData(e.target).entries());
          const body = { username: f.username, expire_days: +f.expire_days || 0, traffic_limit_gb: +f.traffic_limit_gb || 0, ip_limit: +f.ip_limit || 0 };
          try {
            if (ed) { await api("PUT", "/api/users/" + u.id, body); }
            else { await api("POST", "/api/users", body); }
            toast("Saved", "ok"); closeModal(); load();
          } catch (ex) { toast(ex.message, "err"); }
        };
      });
    }

    async function confirmDelete(u) {
      modal(`
        <h3>Delete user</h3>
        <p class="muted">Delete <strong>${esc(u.username)}</strong>? This cannot be undone.</p>
        <div class="modal-actions">
          <button class="btn btn-ghost" onclick="closeModal()">Cancel</button>
          <button class="btn btn-danger" id="del-go">Delete</button>
        </div>
      `, (card) => { card.querySelector("#del-go").onclick = async () => { try { await api("DELETE", "/api/users/" + u.id); toast("Deleted", "ok"); closeModal(); load(); } catch (ex) { toast(ex.message, "err"); } }; });
    }
  }

  // ===== Subscription Management (per user) =====
  async function openSubscription(u) {
    let info;
    try { info = await api("GET", "/sub/" + u.uuid + "?format=json"); } catch (ex) { toast(ex.message, "err"); return; }
    const uris = info.uris || [];
    const subLink = location.origin + "/sub/" + u.uuid;
    const cfgHtml = uris.map((uri, i) => {
      const p = parseUri(uri);
      return `
        <div class="cfg-row">
          <div class="cfg-head">
            <div class="icon-box">${ICON(protoIcon(p.proto))}</div>
            <div><strong>${esc(p.proto)}</strong> <span class="badge ${p.security === "reality" ? "on" : ""}">${esc(p.security)}</span></div>
            <button class="btn btn-sm btn-danger" style="margin-left:auto" data-del="${i}">${ICON("trash")} Delete</button>
          </div>
          <div class="sub-link">${esc(uri)}</div>
          <div class="cfg-actions">
            <button class="btn btn-sm" data-copy="${i}">${ICON("copy")} Copy Config</button>
            <button class="btn btn-sm" data-copysub>${ICON("copy")} Copy Subscription</button>
            <button class="btn btn-sm" data-qr="${i}">${ICON("qr")} QR</button>
            <button class="btn btn-sm" data-toggle="1">Disable</button>
          </div>
        </div>
      `;
    }).join("") || `<div class="empty">${ICON("sub")}<div>No configs.</div></div>`;

    modal(`
      <button class="modal-close">${ICON("close")}</button>
      <h3>Subscription \u00b7 ${esc(u.username)}</h3>
      <div class="kv">
        <div class="key">Status</div><div class="val">${u.enabled ? '<span class="ok">active</span>' : '<span class="error-text">disabled</span>'}</div>
        <div class="key">Expire</div><div class="val">${esc(info.expire_at || "\u2014")}</div>
        <div class="key">Traffic</div><div class="val">${fmtBytes(info.used_traffic_bytes)} / ${fmtBytes(info.traffic_limit_bytes)}</div>
        <div class="key">IP limit</div><div class="val">${u.ip_limit || "\u221e"}</div>
      </div>
      <div style="margin-top:var(--space-md)">
        <div class="sub-link">${esc(subLink)}</div>
        <div class="cfg-actions" style="margin:var(--space-sm) 0">
          <button class="btn btn-sm" id="cp-sub">${ICON("copy")} Copy Link</button>
          <button class="btn btn-sm" id="cp-qr">${ICON("qr")} QR</button>
          <button class="btn btn-sm" id="reset">${ICON("reset")} Reset Traffic</button>
          <button class="btn btn-sm" id="renew">${ICON("renew")} Renew 30d</button>
          <button class="btn btn-sm btn-danger" id="delu">${ICON("trash")} Delete</button>
        </div>
      </div>
      <h3 style="margin-top:var(--space-lg)">Configs</h3>
      <div id="cfgs">${cfgHtml}</div>
    `, (card) => {
      card.querySelector("#cp-sub").onclick = () => copy(subLink, "Link copied");
      card.querySelector("#cp-qr").onclick = () => showQr(u.uuid, 0);
      $$("#cfgs [data-copy]", card).forEach(b => b.onclick = () => copy(uris[+b.dataset.copy], "Config copied"));
      const cs = card.querySelector("#cfgs [data-copysub]"); if (cs) cs.onclick = () => copy(subLink, "Subscription copied");
      $$("#cfgs [data-qr]", card).forEach(b => b.onclick = () => showQr(u.uuid, +b.dataset.qr));
      $$("#cfgs [data-del]", card).forEach(b => b.onclick = () => toast("Use the user's enabled inbounds to change configs", "err"));
      $$("#cfgs [data-toggle]", card).forEach(b => b.onclick = async () => {
        const en = b.dataset.toggle === "1";
        try { await api("POST", "/api/users/" + u.id + (en ? "/disable" : "/enable")); toast(en ? "Disabled" : "Enabled", "ok"); closeModal(); if (window._usersReload) window._usersReload(); } catch (ex) { toast(ex.message, "err"); }
      });
      card.querySelector("#reset").onclick = async () => { try { await api("POST", "/api/users/" + u.id + "/reset-traffic"); toast("Traffic reset", "ok"); } catch (ex) { toast(ex.message, "err"); } };
      card.querySelector("#renew").onclick = async () => { try { await api("PUT", "/api/users/" + u.id, { expire_days: 30 }); toast("Renewed", "ok"); } catch (ex) { toast(ex.message, "err"); } };
      card.querySelector("#delu").onclick = async () => { try { await api("DELETE", "/api/users/" + u.id); toast("Deleted", "ok"); closeModal(); if (window._usersReload) window._usersReload(); } catch (ex) { toast(ex.message, "err"); } };
    });
  }

  // ===== Page: Subscription (User List + Manage) =====
  async function bootSubscription() {
    bindShell(); initFab();
    const c = $("#content");
    c.innerHTML = `<div class="empty">${ICON("sub")}<div>Select a user to manage their subscription.</div></div><div id="u-list" class="tbl" style="margin-top:var(--space-md)"></div>`;
    try {
      const users = await api("GET", "/api/users");
      window._usersReload = async () => { location.reload(); };
      $("#u-list").innerHTML = users.map(u => `
        <div class="tr">
          <div><strong>${esc(u.username)}</strong> <span class="badge ${u.enabled ? "on" : "off"}">${u.enabled ? "on" : "off"}</span></div>
          <div class="actions"><button class="btn btn-sm btn-primary" data-id="${u.id}">${ICON("sub")} Manage</button></div>
        </div>
      `).join("");
      $$("#u-list [data-id]", $("#u-list")).forEach(b => b.onclick = async () => {
        const u = users.find(x => x.id === +b.dataset.id);
        openSubscription(u);
      });
    } catch (ex) { c.innerHTML = `<div class="empty">${esc(ex.message)}</div>`; }
  }

  // ===== Page: Inbounds =====
  async function bootInbounds() {
    bindShell(); initFab();
    const c = $("#content");
    c.innerHTML = `<div class="empty">Loading inbounds\u2026</div>`;
    let ibs = [];
    async function load() {
      try { ibs = await api("GET", "/api/inbounds"); } catch (ex) { ibs = []; toast(ex.message, "err"); }
      c.innerHTML = `<div class="row" style="margin-bottom:var(--space-md)"><button class="btn btn-primary" id="add">${ICON("plus")} New Inbound</button></div>
        <div class="tbl">${ibs.length ? ibs.map(b => `
        <div class="tr">
          <div><strong>${esc(b.tag)}</strong> <span class="badge ${b.enabled ? "on" : "off"}">${b.enabled ? "on" : "off"}</span></div>
          <div class="actions">
            <button class="btn btn-sm" data-act="regen" data-id="${b.id}">${ICON("lock")} Keys</button>
            <button class="btn btn-sm btn-danger" data-act="del" data-id="${b.id}">${ICON("trash")} Del</button>
          </div>
          <div class="grow">${esc(b.network)} / ${esc(b.security)} \u00b7 :${b.port}${b.domain ? " \u00b7 " + esc(b.domain) : ""}</div>
        </div>`).join("") : `<div class="empty">No inbounds.</div>`}</div>`;
      $("#add").onclick = () => toast("Use the API or DB to add inbounds (default inbound is created on first run)", "err");
      $$("#content [data-act]").forEach(el => el.onclick = async () => {
        const id = el.dataset.id;
        try {
          if (el.dataset.act === "regen") { await api("POST", "/api/inbounds/" + id + "/regen-keys"); toast("Keys regenerated", "ok"); }
          else if (el.dataset.act === "del") { await api("DELETE", "/api/inbounds/" + id); toast("Deleted", "ok"); }
          load();
        } catch (ex) { toast(ex.message, "err"); }
      });
    }
    await load();
  }

  // ===== Page: Domains =====
  async function bootDomains() {
    bindShell(); initFab();
    const c = $("#content"); c.innerHTML = `<div class="empty">Loading domains\u2026</div>`;
    try {
      const ds = await api("GET", "/api/domains");
      c.innerHTML = `<div class="row" style="margin-bottom:var(--space-md)"><input id="d-new" class="field" placeholder="example.com" style="flex:1;max-width:320px"><button class="btn btn-primary" id="d-add">${ICON("plus")} Add</button></div>
        <div class="tbl">${ds.map(d => `
        <div class="tr">
          <div><strong>${esc(d.domain)}</strong> ${d.is_active ? '<span class="badge on">active</span>' : ''}</div>
          <div class="actions">
            ${d.is_active ? "" : `<button class="btn btn-sm" data-act="act" data-id="${d.id}">Activate</button>`}
            <button class="btn btn-sm btn-danger" data-act="del" data-id="${d.id}">Del</button>
          </div>
        </div>`).join("")}</div>`;
      const reload = () => bootDomains();
      $("#d-add").onclick = async () => { const v = $("#d-new").value.trim(); if (!v) return; try { await api("POST", "/api/domains", { domain: v }); reload(); } catch (ex) { toast(ex.message, "err"); } };
      $$("#content [data-act]").forEach(el => el.onclick = async () => {
        const id = el.dataset.id;
        try { if (el.dataset.act === "act") await api("POST", "/api/domains/" + id + "/activate"); else await api("DELETE", "/api/domains/" + id); reload(); }
        catch (ex) { toast(ex.message, "err"); }
      });
    } catch (ex) { c.innerHTML = `<div class="empty">${esc(ex.message)}</div>`; }
  }

  // ===== Page: System / Xray =====
  async function bootXray() {
    bindShell(); initFab();
    const c = $("#content");
    try {
      const h = await api("GET", "/api/system/xray/health");
      const last = await api("GET", "/api/xray/last-result");
      c.innerHTML = `<div class="card" style="margin-bottom:var(--space-md)"><div class="kv">
        <div class="key">Xray</div><div class="val ${h.running ? "ok" : "error-text"}">${h.running ? "running (pid " + (h.pid || "?") + ")" : "stopped"}</div>
        <div class="key">Version</div><div class="val">${esc(h.version || "?")}</div>
        <div class="key">Auto-restart</div><div class="val">${h.auto_restart ? "on" : "off"}</div>
        <div class="key">Last error</div><div class="val ${last.error ? "error-text" : ""}">${esc(last.error || "none")}</div>
      </div></div>
      <div class="row-actions">
        <button class="btn btn-primary" id="start">${ICON("play")} Start</button>
        <button class="btn" id="stop">${ICON("stop")} Stop</button>
        <button class="btn" id="restart">${ICON("refresh")} Restart</button>
        <button class="btn" id="validate">${ICON("check")} Validate</button>
      </div>
      <div id="sys-out" class="term" style="margin-top:var(--space-md)"></div>`;
      const out = $("#sys-out");
      const run = async (m, p) => { out.textContent = "\u2026"; try { const r = await api(m, p); out.textContent = JSON.stringify(r, null, 2); } catch (ex) { out.textContent = ex.message; } };
      $("#start").onclick = () => run("POST", "/api/system/xray/start");
      $("#stop").onclick = () => run("POST", "/api/system/xray/stop");
      $("#restart").onclick = () => run("POST", "/api/system/xray/restart");
      $("#validate").onclick = async () => { out.textContent = "validating\u2026"; try { const r = await api("POST", "/api/xray/validate"); out.textContent = (r.ok ? "OK\n" : "FAILED\n") + (r.message || ""); } catch (ex) { out.textContent = ex.message; } };
    } catch (ex) { c.innerHTML = `<div class="empty">${esc(ex.message)}</div>`; }
  }

  // ===== Page: Settings =====
  async function bootSettings() {
    bindShell(); initFab();
    const c = $("#content");
    c.innerHTML = `<div class="card" style="margin-bottom:var(--space-md)"><h3>Change credentials</h3>
      <form id="cred"><div class="field"><label class="lbl">Current password</label><input name="current" type="password" required></div>
      <div class="field"><label class="lbl">New username</label><input name="username"></div>
      <div class="field"><label class="lbl">New password</label><input name="password" type="password"></div>
      <div class="modal-actions"><button class="btn btn-primary">Save</button></div></form></div>
      <div class="card"><h3>Preferences</h3>
      <form id="pref"><label class="remember"><input type="checkbox" name="music" checked> Play music on open</label>
      <div class="modal-actions"><button class="btn btn-primary" id="savepref">Save</button></div></form></div>`;
    $("#cred").onsubmit = async (e) => { e.preventDefault(); const f = Object.fromEntries(new FormData(e.target).entries()); const body = { current_password: f.current }; if (f.username) body.username = f.username; if (f.password) body.password = f.password; try { await api("POST", "/api/auth/change-credentials", body); toast("Saved", "ok"); } catch (ex) { toast(ex.message, "err"); } };
    $("#savepref").onclick = async () => { const music = $("#pref [name=music]").checked ? "1" : ""; try { await api("POST", "/api/settings", { key: "music_on_open", value: music }); toast("Preferences saved", "ok"); } catch (ex) { toast(ex.message, "err"); } };
  }

  // ===== Page: News =====
  async function bootNews() {
    bindShell(); initFab();
    const c = $("#content");
    c.innerHTML = `<div class="empty">${ICON("news")}<div>Loading latest news\u2026</div></div>`;
    try {
      const r = await api("GET", "/api/news");
      if (!r.items || !r.items.length) { c.innerHTML = `<div class="empty">No news available.</div>`; return; }
      c.innerHTML = `<h3>Latest News</h3><div class="news-box">` + r.items.map(n => `
        <div style="margin-bottom:var(--space-lg)">
          <div class="news-title">${esc(n.title)}</div>
          <div class="news-meta">${esc(n.source || "")} \u00b7 ${n.published ? esc(n.published) : ""}</div>
          <div class="news-text">${esc(n.text)}</div>
        </div>`).join("") + `</div>`;
    } catch (ex) { c.innerHTML = `<div class="empty">${esc(ex.message)}</div>`; }
  }

  // ===== Page: Statistics =====
  async function bootStatistics() {
    bindShell(); initFab();
    return bootDashboard();
  }

  // ===== Page: About =====
  async function bootAbout() {
    bindShell(); initFab();
    $("#content").innerHTML = `
      <div class="card" style="text-align:center; padding:var(--space-2xl)">
        <div class="spider-logo" style="display:inline-flex">${ICON("spider")}</div>
        <h2 class="title-neon" style="margin-top:var(--space-sm)">Spider Panel</h2>
        <p class="muted">Red Neon Futuristic Cyber Xray Management Panel</p>
        <div class="kv" style="margin-top:var(--space-lg); text-align:left">
          <div class="key">Core</div><div class="val">Xray-core (VLESS Reality + XHTTP)</div>
          <div class="key">Backend</div><div class="val">FastAPI + SQLAlchemy + SQLite</div>
          <div class="key">Deploy</div><div class="val">Railway Proxy</div>
          <div class="key">UI</div><div class="val">Mobile-first, glassmorphism</div>
        </div>
        <a class="btn btn-ghost" style="margin-top:var(--space-lg)" href="https://t.me/amirsplder" target="_blank" rel="noopener">${ICON("telegram")} Contact</a>
      </div>`;
  }

  // ===== Page: Public Subscription Landing =====
  async function bootSub() {
    initFab();
    const params = new URLSearchParams(location.search);
    const uuid = params.get("uuid");
    const c = $("#content");
    if (!uuid) { c.innerHTML = `<div class="empty">${ICON("sub")}<div>Invalid subscription link.</div></div>`; return; }
    c.innerHTML = `<div class="empty">${ICON("sub")}<div>Loading\u2026</div></div>`;
    try {
      const info = await api("GET", "/sub/" + uuid + "?format=json");
      const uris = info.uris || [];
      const subLink = location.origin + "/sub/" + uuid;
      c.innerHTML = `
        <div class="card" style="text-align:center">
          <h2 class="title-neon">${esc(info.username)}</h2>
          <div class="sub-link">${esc(subLink)}</div>
          <div class="cfg-actions" style="justify-content:center">
            <button class="btn btn-sm" id="cp">${ICON("copy")} Copy Link</button>
            <button class="btn btn-sm" id="qr">${ICON("qr")} QR</button>
            <button class="btn btn-sm" id="ping">${ICON("online")} Ping</button>
          </div>
          <div id="ping-out" class="muted" style="margin-top:var(--space-sm)"></div>
        </div>
        <div class="card" style="margin-top:var(--space-md)"><div class="kv">
          <div class="key">Status</div><div class="val">${info.enabled ? '<span class="ok">active</span>' : '<span class="error-text">disabled</span>'}</div>
          <div class="key">Expire</div><div class="val">${esc(info.expire_at || "\u2014")}</div>
          <div class="key">Used</div><div class="val">${fmtBytes(info.used_traffic_bytes)}</div>
          <div class="key">Limit</div><div class="val">${fmtBytes(info.traffic_limit_bytes)}</div>
        </div></div>
        <div class="card" style="margin-top:var(--space-md)"><h3>Configs</h3>
          ${uris.map((u, i) => { const p = parseUri(u); return `
            <div class="cfg-row"><div class="cfg-head"><div class="icon-box">${ICON(protoIcon(p.proto))}</div><div><strong>${esc(p.proto)}</strong> <span class="badge ${p.security==="reality"?"on":""}">${esc(p.security)}</span></div></div>
            <div class="sub-link">${esc(u)}</div>
            <div class="cfg-actions"><button class="btn btn-sm" data-c="${i}">${ICON("copy")} Copy</button><button class="btn btn-sm" data-q="${i}">${ICON("qr")} QR</button></div></div>`; }).join("") || '<div class="empty">No configs.</div>'}
        </div>`;
      $("#cp").onclick = () => copy(subLink, "Link copied");
      $("#qr").onclick = () => showQr(uuid, 0);
      $$("#content [data-c]").forEach(b => b.onclick = () => copy(uris[+b.dataset.c], "Config copied"));
      $$("#content [data-q]").forEach(b => b.onclick = () => showQr(uuid, +b.dataset.q));
      $("#ping").onclick = async () => { const o = $("#ping-out"); o.textContent = "pinging\u2026"; try { const r = await api("GET", "/sub/" + uuid + "/ping"); o.innerHTML = r.ok ? '<span class="ok">reachable ' + r.ms + ' ms</span>' : '<span class="error-text">' + esc(r.error || "unreachable") + '</span>'; } catch (ex) { o.textContent = ex.message; } };
    } catch (ex) { c.innerHTML = `<div class="empty">${esc(ex.message)}</div>`; }
  }

  // ===== Page Dispatcher =====
  window.bootPage = function (page) {
    const el = $("#content");
    const applyEnter = () => { if (el) { el.classList.remove("page-enter"); void el.offsetWidth; el.classList.add("page-enter"); } };
    const map = {
      login: bootLogin, dashboard: bootDashboard, users: bootUsers,
      subscription: bootSubscription, inbounds: bootInbounds, domains: bootDomains,
      system: bootXray, settings: bootSettings, xray: bootXray, news: bootNews,
      about: bootAbout, statistics: bootStatistics, sub: bootSub,
    };
    const fn = map[page] || bootDashboard;
    fn().then(applyEnter).catch(ex => { if (el) el.innerHTML = `<div class="empty">${esc(ex.message)}</div>`; });
  };
})();