/* Utilidades compartidas entre paneles por rol */
const API = "/api";

const STATUS_LABELS = {
  scheduled: "Programada",
  completed: "Completada",
  cancelled: "Cancelada",
  no_show: "No asistió",
  pending: "Pendiente",
  paid: "Pagado",
  partial: "Parcial",
  exempt: "Exento",
  refund_pending: "Reembolso pendiente",
};

const WEEKDAYS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"];

let _loaderTimer = null;
let _loaderCount = 0;

function getBootUser() {
  const el = document.getElementById("boot-user");
  if (!el) return null;
  try {
    return JSON.parse(el.textContent);
  } catch {
    return null;
  }
}

function showLoading(message = "Cargando…") {
  const el = document.getElementById("app-loader");
  const text = document.getElementById("app-loader-text");
  if (text) text.textContent = message;
  _loaderCount += 1;
  clearTimeout(_loaderTimer);
  _loaderTimer = setTimeout(() => {
    if (!el) return;
    el.hidden = false;
  }, 160);
}

function hideLoading() {
  _loaderCount = Math.max(0, _loaderCount - 1);
  if (_loaderCount > 0) return;
  clearTimeout(_loaderTimer);
  const el = document.getElementById("app-loader");
  if (el) el.hidden = true;
}

async function api(path, options = {}) {
  const silent = options.silent;
  delete options.silent;
  if (!silent) showLoading();
  try {
    const res = await fetch(`${API}${path}`, {
      headers: { "Content-Type": "application/json", ...(options.headers || {}) },
      ...options,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(typeof err.detail === "string" ? err.detail : JSON.stringify(err.detail));
    }
    if (res.status === 204) return null;
    return res.json();
  } finally {
    if (!silent) hideLoading();
  }
}

function toast(msg, type = "success") {
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.textContent = msg;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 3500);
}

function fmtDate(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("es-MX", {
    weekday: "short",
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function fmtTime(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleTimeString("es-MX", { hour: "2-digit", minute: "2-digit" });
}

function fmtDateTime(iso) {
  return `${fmtDate(iso)} ${fmtTime(iso)}`;
}

function badge(status) {
  return `<span class="badge badge-${status}">${STATUS_LABELS[status] || status}</span>`;
}

function todayISO() {
  return new Date().toISOString().slice(0, 10);
}

function setPageChrome(panel) {
  if (!panel) return;
  const map = [
    ["page-title", panel.dataset.title],
    ["page-eyebrow", panel.dataset.eyebrow],
    ["page-lead", panel.dataset.lead],
  ];
  map.forEach(([id, val]) => {
    const el = document.getElementById(id);
    if (el && val) el.textContent = val;
  });
  if (panel.dataset.title) document.title = `${panel.dataset.title} · Proyecto H`;
}

function bindRoleNavigation(loaders) {
  function navigateTo(tab) {
    document.querySelectorAll("[data-tab]").forEach((el) => {
      el.classList.toggle("active", el.dataset.tab === tab);
    });
    document.querySelectorAll(".panel").forEach((p) => p.classList.toggle("active", p.id === `panel-${tab}`));
    setPageChrome(document.getElementById(`panel-${tab}`));
    document.getElementById("primary-nav")?.classList.remove("is-open");
    loaders[tab]?.();
  }

  document.getElementById("tabs")?.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-tab]");
    if (btn) navigateTo(btn.dataset.tab);
  });
  document.getElementById("sidebar-nav")?.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-tab]");
    if (btn) navigateTo(btn.dataset.tab);
  });
  document.getElementById("nav-toggle")?.addEventListener("click", () => {
    document.getElementById("primary-nav")?.classList.toggle("is-open");
  });

  const dateEl = document.getElementById("utility-date");
  if (dateEl) {
    dateEl.textContent = new Date().toLocaleDateString("es-MX", {
      weekday: "long",
      day: "numeric",
      month: "long",
      year: "numeric",
    });
  }

  return navigateTo;
}

function empty(msg) {
  return `<p class="empty">${msg}</p>`;
}
