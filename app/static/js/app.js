const API = "/api";

const STATUS_LABELS = {
  scheduled: "Programada",
  completed: "Realizada",
  cancelled: "Cancelada",
  no_show: "Paciente tarde",
  doctor_absent: "Doctor ausente",
  pending: "Pendiente",
  paid: "Pagado",
  partial: "Parcial",
  exempt: "Exento",
  refund_pending: "Reembolso pendiente",
};

const WEEKDAYS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"];

const ESPECIALIDADES = [
  "Medicina General",
  "Pediatría",
  "Ginecología",
  "Dermatología",
];

let _doctorsCache = [];

let _loaderTimer = null;
let _loaderCount = 0;

function showLoading(message = "Cargando…") {
  const el = document.getElementById("app-loader");
  const text = document.getElementById("app-loader-text");
  if (text) text.textContent = message;
  _loaderCount += 1;
  clearTimeout(_loaderTimer);
  _loaderTimer = setTimeout(() => {
    if (!el) return;
    el.hidden = false;
    el.setAttribute("aria-hidden", "false");
  }, 180);
}

function hideLoading() {
  _loaderCount = Math.max(0, _loaderCount - 1);
  if (_loaderCount > 0) return;
  clearTimeout(_loaderTimer);
  const el = document.getElementById("app-loader");
  if (!el) return;
  el.hidden = true;
  el.setAttribute("aria-hidden", "true");
}

async function api(path, options = {}) {
  const silent = options.silent;
  delete options.silent;
  if (!silent) showLoading();
  try {
    const res = await fetch(`${API}${path}`, {
      headers: { "Content-Type": "application/json", ...options.headers },
      ...options,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      const detail = err.detail || "Error en la solicitud";
      if (res.status >= 500) {
        window.location.href = `/error?code=${res.status}&title=${encodeURIComponent("Error del servidor")}&message=${encodeURIComponent(String(detail))}`;
      }
      const error = new Error(
        typeof detail === "string" ? detail : detail.mensaje || JSON.stringify(detail)
      );
      error.status = res.status;
      error.detail = detail;
      throw error;
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
  const d = new Date(iso);
  return d.toLocaleDateString("es-MX", { weekday: "short", day: "2-digit", month: "short", year: "numeric" });
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

function esCitaPagada(a) {
  return !!(a && a.pago && a.pago.estado === "paid");
}

function esCitaProxima(a) {
  if (!a || a.estado !== "scheduled") return false;
  if (esCitaPagada(a)) return false;
  return new Date(a.inicio) >= new Date();
}

function esCitaHistorial(a) {
  return !esCitaProxima(a);
}

function sortByInicioAsc(list) {
  return [...list].sort((a, b) => new Date(a.inicio) - new Date(b.inicio));
}

function sortByInicioDesc(list) {
  return [...list].sort((a, b) => new Date(b.inicio) - new Date(a.inicio));
}

function todayISO() {
  // Fecha de calendario en Ciudad de México (YYYY-MM-DD)
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "America/Mexico_City",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date());
}

function maxAgendaISO() {
  const parts = todayISO().split("-").map(Number);
  const d = new Date(Date.UTC(parts[0], parts[1] - 1, parts[2]));
  d.setUTCDate(d.getUTCDate() + 365);
  return d.toISOString().slice(0, 10);
}

function bindAgendaDateInput(el) {
  if (!el) return;
  el.min = todayISO();
  el.max = maxAgendaISO();
  if (el.value && el.value < el.min) el.value = el.min;
  if (el.value && el.value > el.max) el.value = el.max;
}

const PAGE_LOADERS = {
  dashboard: () => loadDashboard(),
  doctors: () => loadDoctors(),
  patients: () => loadPatients(),
  schedules: () => loadSchedules(),
  appointments: () => loadAppointments(),
  payments: () => loadPayments(),
  users: () => loadUsers(),
};

function setPageChrome(panel) {
  const title = panel?.dataset.title || "Proyecto H";
  const eyebrow = panel?.dataset.eyebrow || "Operaciones clínicas";
  const lead = panel?.dataset.lead || "";
  const titleEl = document.getElementById("page-title");
  const eyebrowEl = document.getElementById("page-eyebrow");
  const leadEl = document.getElementById("page-lead");
  if (titleEl) titleEl.textContent = title;
  if (eyebrowEl) eyebrowEl.textContent = eyebrow;
  if (leadEl) leadEl.textContent = lead;
  document.title = `${title} · Proyecto H`;
}

function navigateTo(tab) {
  if (!tab) return;
  document.querySelectorAll("[data-tab]").forEach((el) => {
    el.classList.toggle("active", el.dataset.tab === tab);
  });
  document.querySelectorAll(".panel").forEach((p) => p.classList.toggle("active", p.id === `panel-${tab}`));
  const panel = document.getElementById(`panel-${tab}`);
  setPageChrome(panel);
  const nav = document.getElementById("primary-nav");
  const toggle = document.getElementById("nav-toggle");
  if (nav) nav.classList.remove("is-open");
  if (toggle) toggle.setAttribute("aria-expanded", "false");
  PAGE_LOADERS[tab]?.();
}

document.getElementById("tabs")?.addEventListener("click", (e) => {
  const btn = e.target.closest("[data-tab]");
  if (!btn) return;
  navigateTo(btn.dataset.tab);
});

document.getElementById("sidebar-nav")?.addEventListener("click", (e) => {
  const btn = e.target.closest("[data-tab]");
  if (!btn) return;
  navigateTo(btn.dataset.tab);
});

document.querySelector(".brand")?.addEventListener("click", (e) => {
  e.preventDefault();
  navigateTo("dashboard");
});

document.getElementById("nav-toggle")?.addEventListener("click", () => {
  const nav = document.getElementById("primary-nav");
  const toggle = document.getElementById("nav-toggle");
  const open = nav?.classList.toggle("is-open");
  toggle?.setAttribute("aria-expanded", open ? "true" : "false");
});

(() => {
  const dateEl = document.getElementById("utility-date");
  if (dateEl) {
    dateEl.textContent = new Date().toLocaleDateString("es-MX", {
      weekday: "long",
      day: "numeric",
      month: "long",
      year: "numeric",
    });
  }
  const yearEl = document.getElementById("footer-year");
  if (yearEl) yearEl.textContent = String(new Date().getFullYear());
})();

// Dashboard
async function loadDashboard() {
  try {
    const stats = await api("/appointments/stats/dashboard");
    document.getElementById("stat-doctors").textContent = stats.doctors_active;
    document.getElementById("stat-patients").textContent = stats.patients_total;
    document.getElementById("stat-today").textContent = stats.appointments_today;
    document.getElementById("stat-pending").textContent = stats.payments_pending;

    const appts = await api("/appointments?status=scheduled");
    const upcoming = sortByInicioAsc(appts.filter(esCitaProxima)).slice(0, 8);
    const container = document.getElementById("dashboard-appointments");
    if (!upcoming.length) {
      container.innerHTML = '<p class="empty">No hay citas próximas (sin cobrar)</p>';
      return;
    }
    container.innerHTML = `<table><thead><tr><th>Fecha</th><th>Doctor</th><th>Paciente</th><th>Estado</th><th>Pago</th></tr></thead><tbody>
      ${upcoming.map((a) => `<tr>
        <td>${fmtDateTime(a.inicio)}</td>
        <td>${a.nombre_doctor || a.doctor_id}</td>
        <td>${a.nombre_paciente || a.paciente_id}</td>
        <td>${badge(a.estado)}</td>
        <td>${a.pago ? badge(a.pago.estado) : "—"}</td>
      </tr>`).join("")}
    </tbody></table>`;
  } catch (e) {
    toast(e.message, "error");
  }
}

// Doctores
async function loadDoctors() {
  try {
    const doctors = await api("/doctors");
    document.getElementById("doctors-table").innerHTML = doctors.length
      ? `<table><thead><tr><th>Nombre</th><th>Especialidad</th><th>Sexo</th><th>Duración</th><th>Tarifa</th><th>Activo</th><th>Acciones</th></tr></thead><tbody>
        ${doctors.map((d) => `<tr>
          <td>${d.nombre_completo}</td><td>${d.especialidad}</td><td>${d.sexo === "F" ? "Mujer" : d.sexo === "M" ? "Hombre" : "—"}</td><td>${d.minutos_consulta} min</td>
          <td>$${d.tarifa.toFixed(2)}</td><td>${d.activo ? "Sí" : "No"}</td>
          <td class="actions">
            <button class="btn btn-sm btn-primary" onclick="editDoctor(${d.id})">Editar</button>
            <button class="btn btn-sm btn-danger" onclick="deleteDoctor(${d.id})">Eliminar</button>
          </td>
        </tr>`).join("")}
      </tbody></table>`
      : '<p class="empty">No hay doctores registrados</p>';
    populateDoctorSelects(doctors);
  } catch (e) {
    toast(e.message, "error");
  }
}

function resetDoctorForm() {
  document.getElementById("doctor-form").reset();
  document.getElementById("doctor-id").value = "";
  document.getElementById("doctor-minutes").value = 30;
  document.getElementById("doctor-fee").value = 500;
  document.getElementById("doctor-sexo").value = "F";
  document.getElementById("doctor-active").checked = true;
  const gen = document.getElementById("doctor-gen-schedule");
  if (gen) gen.checked = true;
  const wrap = document.getElementById("doctor-gen-schedule-wrap");
  if (wrap) wrap.style.display = "";
  document.getElementById("doctor-form-title").textContent = "Nuevo doctor";
  document.getElementById("doctor-cancel-edit").style.display = "none";
}

document.getElementById("doctor-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const id = document.getElementById("doctor-id").value;
  const payload = {
    nombre_completo: document.getElementById("doctor-name").value,
    especialidad: document.getElementById("doctor-especialidad").value,
    sexo: document.getElementById("doctor-sexo").value,
    minutos_consulta: parseInt(document.getElementById("doctor-minutes").value),
    tarifa: parseFloat(document.getElementById("doctor-fee").value),
    activo: document.getElementById("doctor-active").checked,
  };
  if (payload.especialidad === "Ginecología" && payload.sexo !== "F") {
    toast("Ginecología solo admite doctoras", "error");
    return;
  }
  const genSchedule = document.getElementById("doctor-gen-schedule")?.checked;
  try {
    if (id) {
      await api(`/doctors/${id}`, { method: "PUT", body: JSON.stringify(payload) });
      toast("Doctor actualizado");
    } else {
      const creado = await api("/doctors", { method: "POST", body: JSON.stringify(payload) });
      if (genSchedule && creado?.id) {
        try {
          const bloques = await api(`/doctors/${creado.id}/schedules/generate`, {
            method: "POST",
            body: JSON.stringify({ reemplazar: false }),
          });
          toast(`Doctor creado con ${bloques.length} bloque(s) de horario`);
        } catch (genErr) {
          toast(`Doctor creado, pero no se generaron horarios: ${genErr.message}`, "error");
        }
      } else {
        toast("Doctor creado");
      }
    }
    resetDoctorForm();
    loadDoctors();
    if (typeof loadSchedules === "function") loadSchedules();
  } catch (err) {
    toast(err.message, "error");
  }
});

document.getElementById("doctor-cancel-edit").addEventListener("click", resetDoctorForm);

window.editDoctor = async (id) => {
  const d = await api(`/doctors/${id}`);
  document.getElementById("doctor-id").value = d.id;
  document.getElementById("doctor-name").value = d.nombre_completo;
  document.getElementById("doctor-especialidad").value = d.especialidad;
  document.getElementById("doctor-sexo").value = d.sexo || "F";
  document.getElementById("doctor-minutes").value = d.minutos_consulta;
  document.getElementById("doctor-fee").value = d.tarifa;
  document.getElementById("doctor-active").checked = d.activo;
  const wrap = document.getElementById("doctor-gen-schedule-wrap");
  if (wrap) wrap.style.display = "none";
  document.getElementById("doctor-form-title").textContent = "Editar doctor";
  document.getElementById("doctor-cancel-edit").style.display = "inline-block";
};

let _pendingDeleteDoctorId = null;

function openReassignDoctorDialog(doctorId, detalle) {
  const dlg = document.getElementById("reassign-doctor-dialog");
  const checks = document.getElementById("reassign-doctor-checks");
  const list = document.getElementById("reassign-doctor-citas");
  const msg = document.getElementById("reassign-doctor-msg");
  if (!dlg || !checks) {
    toast("No se pudo abrir el diálogo de reasignación", "error");
    return;
  }
  _pendingDeleteDoctorId = doctorId;
  const citas = detalle.citas || [];
  const doctores = detalle.doctores || [];
  const esp = detalle.especialidad || "la misma especialidad";
  msg.textContent =
    detalle.mensaje ||
    `Este doctor tiene ${citas.length || "varias"} cita(s). Se repartirán entre doctores de ${esp}.`;
  list.innerHTML = citas.length
    ? `<ul>${citas
        .slice(0, 8)
        .map(
          (c) =>
            `<li>#${c.id} · ${c.inicio} · ${STATUS_LABELS[c.estado] || c.estado}</li>`
        )
        .join("")}${citas.length > 8 ? `<li>… y ${citas.length - 8} más</li>` : ""}</ul>`
    : "";
  checks.innerHTML = doctores.length
    ? doctores
        .map(
          (d) => `<label class="reassign-check">
            <input type="checkbox" name="reassign-doc" value="${d.id}" checked>
            <span>${d.nombre_completo}</span>
          </label>`
        )
        .join("")
    : "<p class=\"empty\">No hay otros doctores activos de esa especialidad</p>";
  dlg.showModal();
}

window.deleteDoctor = async (id) => {
  if (!confirm("¿Eliminar este doctor?")) return;
  try {
    await api(`/doctors/${id}`, { method: "DELETE" });
    toast("Doctor eliminado");
    loadDoctors();
    if (typeof loadAppointments === "function") loadAppointments();
  } catch (e) {
    const detalle = e.detail || null;
    const doctores = detalle && detalle.doctores;
    if (e.status === 409 && doctores && doctores.length) {
      openReassignDoctorDialog(id, detalle);
      return;
    }
    if (e.status === 409 && doctores && !doctores.length) {
      toast("No hay otro doctor de la misma especialidad para repartir las citas", "error");
      return;
    }
    toast(e.message, "error");
  }
};

const reassignForm = document.getElementById("reassign-doctor-form");
if (reassignForm) {
  reassignForm.addEventListener("submit", async (ev) => {
    const submitter = ev.submitter;
    if (!submitter || submitter.value !== "save") {
      _pendingDeleteDoctorId = null;
      return;
    }
    ev.preventDefault();
    const ids = [
      ...document.querySelectorAll('#reassign-doctor-checks input[name="reassign-doc"]:checked'),
    ].map((el) => Number(el.value));
    if (!_pendingDeleteDoctorId || !ids.length) {
      toast("Marca al menos un doctor receptor", "error");
      return;
    }
    const params = new URLSearchParams({
      redistribuir: "true",
      doctor_ids: ids.join(","),
    });
    try {
      await api(`/doctors/${_pendingDeleteDoctorId}?${params}`, { method: "DELETE" });
      document.getElementById("reassign-doctor-dialog").close();
      _pendingDeleteDoctorId = null;
      toast(
        ids.length > 1
          ? `Doctor eliminado; citas repartidas entre ${ids.length} colegas`
          : "Doctor eliminado y citas reasignadas"
      );
      loadDoctors();
      if (typeof loadAppointments === "function") loadAppointments();
    } catch (err) {
      toast(err.message, "error");
    }
  });
}

// Pacientes
let _patientsCache = [];

function _normText(s) {
  return String(s || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();
}

function filteredSortedPatients() {
  const q = _normText(document.getElementById("patient-search")?.value || "");
  const sort = document.getElementById("patient-sort")?.value || "az";
  let list = [..._patientsCache];

  if (q) {
    list = list.filter((p) => {
      const blob = _normText(
        `${p.nombre_completo} ${p.documento} ${p.telefono || ""} ${p.correo || ""}`
      );
      return blob.includes(q);
    });
  }

  list.sort((a, b) => {
    if (sort === "doc") {
      return _normText(a.documento).localeCompare(_normText(b.documento), "es");
    }
    const cmp = _normText(a.nombre_completo).localeCompare(
      _normText(b.nombre_completo),
      "es"
    );
    return sort === "za" ? -cmp : cmp;
  });
  return list;
}

function renderPatientsTable() {
  const patients = filteredSortedPatients();
  const hint = document.getElementById("patients-result-hint");
  const q = (document.getElementById("patient-search")?.value || "").trim();
  if (hint) {
    if (!_patientsCache.length) {
      hint.hidden = true;
    } else {
      hint.hidden = false;
      hint.textContent = q
        ? `${patients.length} de ${_patientsCache.length} pacientes`
        : `${patients.length} pacientes · orden ${
            document.getElementById("patient-sort")?.selectedOptions?.[0]?.text || "A → Z"
          }`;
    }
  }

  document.getElementById("patients-table").innerHTML = patients.length
    ? `<table><thead><tr><th>Nombre</th><th>Documento</th><th>Sexo</th><th>Teléfono</th><th>Email</th><th>Acciones</th></tr></thead><tbody>
        ${patients
          .map(
            (p) => `<tr>
          <td>${p.nombre_completo}</td><td>${p.documento}</td><td>${
              p.sexo === "F" ? "Mujer" : p.sexo === "M" ? "Hombre" : "—"
            }</td><td>${p.telefono || "—"}</td><td>${p.correo || "—"}</td>
          <td class="actions">
            <button class="btn btn-sm btn-primary" onclick="editPatient(${p.id})">Editar</button>
            <button class="btn btn-sm btn-danger" onclick="deletePatient(${p.id})">Eliminar</button>
          </td>
        </tr>`
          )
          .join("")}
      </tbody></table>`
    : `<p class="empty">${
        q ? "Ningún paciente coincide con la búsqueda" : "No hay pacientes registrados"
      }</p>`;
}

async function loadPatients() {
  try {
    const patients = await api("/patients");
    _patientsCache = patients;
    renderPatientsTable();
    fillAppointmentPatients();
  } catch (e) {
    toast(e.message, "error");
  }
}

document.getElementById("patient-search")?.addEventListener("input", () => {
  renderPatientsTable();
  fillAppointmentPatients();
});
document.getElementById("patient-sort")?.addEventListener("change", () => {
  renderPatientsTable();
  fillAppointmentPatients();
});
document.getElementById("patient-refresh-btn")?.addEventListener("click", async () => {
  await loadPatients();
  toast("Listado redesplegado");
});

function resetPatientForm() {
  document.getElementById("patient-form").reset();
  document.getElementById("patient-id").value = "";
  document.getElementById("patient-sexo").value = "F";
  document.getElementById("patient-form-title").textContent = "Nuevo paciente";
  document.getElementById("patient-cancel-edit").style.display = "none";
}

document.getElementById("patient-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const id = document.getElementById("patient-id").value;
  const payload = {
    nombre_completo: document.getElementById("patient-name").value,
    documento: document.getElementById("patient-document").value,
    sexo: document.getElementById("patient-sexo").value,
    telefono: document.getElementById("patient-phone").value || null,
    correo: document.getElementById("patient-email").value || null,
  };
  try {
    if (id) {
      await api(`/patients/${id}`, { method: "PUT", body: JSON.stringify(payload) });
      toast("Paciente actualizado");
    } else {
      await api("/patients", { method: "POST", body: JSON.stringify(payload) });
      toast("Paciente creado");
    }
    resetPatientForm();
    loadPatients();
  } catch (err) {
    toast(err.message, "error");
  }
});

document.getElementById("patient-cancel-edit").addEventListener("click", resetPatientForm);

window.editPatient = async (id) => {
  const p = await api(`/patients/${id}`);
  document.getElementById("patient-id").value = p.id;
  document.getElementById("patient-name").value = p.nombre_completo;
  document.getElementById("patient-document").value = p.documento;
  document.getElementById("patient-sexo").value = p.sexo || "F";
  document.getElementById("patient-phone").value = p.telefono || "";
  document.getElementById("patient-email").value = p.correo || "";
  document.getElementById("patient-form-title").textContent = "Editar paciente";
  document.getElementById("patient-cancel-edit").style.display = "inline-block";
};

window.deletePatient = async (id) => {
  if (!confirm("¿Eliminar este paciente? También se borrarán sus citas y pagos.")) return;
  try {
    await api(`/patients/${id}`, { method: "DELETE" });
    toast("Paciente eliminado");
    loadPatients();
    if (typeof loadAppointments === "function") loadAppointments();
  } catch (e) {
    toast(e.message, "error");
  }
};

// Selects helpers
function populateDoctorSelects(doctors) {
  _doctorsCache = doctors || [];
  const opts = (list, all) => {
    const base = all ? '<option value="">Todos</option>' : "";
    return (
      base +
      list
        .map((d) => `<option value="${d.id}">${d.nombre_completo} (${d.especialidad})</option>`)
        .join("")
    );
  };
  fillSlotsDoctorSelect();
  ["appt-filter-doctor", "pay-filter-doctor"].forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.innerHTML = opts(doctors, true);
  });
  fillAppointmentDoctors();
}

function fillSlotsDoctorSelect() {
  const specialty = document.getElementById("slots-specialty")?.value || "";
  const el = document.getElementById("slots-doctor");
  if (!el) return;
  let list = _doctorsCache.filter((d) => d.activo && (!specialty || d.especialidad === specialty));
  list = list.sort((a, b) =>
    _normText(a.nombre_completo).localeCompare(_normText(b.nombre_completo), "es")
  );
  el.innerHTML = list.length
    ? list
        .map(
          (d) =>
            `<option value="${d.id}">${d.nombre_completo} — ${d.especialidad}</option>`
        )
        .join("")
    : '<option value="">Sin doctores</option>';
}

function updateScheduleDoctorMeta() {
  const doctorId = document.getElementById("schedule-doctor")?.value;
  const doc = _doctorsCache.find((d) => String(d.id) === String(doctorId));
  const set = (id, val) => {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
  };
  if (!doc) {
    set("sched-meta-name", "—");
    set("sched-meta-specialty", "—");
    set("sched-meta-sex", "—");
    set("sched-meta-minutes", "—");
    const title = document.getElementById("schedule-editor-title");
    if (title) title.textContent = "Agenda del doctor";
    return;
  }
  set("sched-meta-name", doc.nombre_completo);
  set("sched-meta-specialty", doc.especialidad);
  set("sched-meta-sex", doc.sexo === "F" ? "Mujer" : doc.sexo === "M" ? "Hombre" : "—");
  set("sched-meta-minutes", `${doc.minutos_consulta} min`);
  const title = document.getElementById("schedule-editor-title");
  if (title) title.textContent = `Agenda · ${doc.nombre_completo}`;
}

function fillAppointmentDoctors() {
  const specialtyEl = document.getElementById("appt-specialty");
  const doctorEl = document.getElementById("appt-doctor");
  if (!doctorEl) return;
  const specialty = specialtyEl ? specialtyEl.value : "";
  let list = _doctorsCache.filter(
    (d) => d.activo && (!specialty || d.especialidad === specialty)
  );
  if (specialty === "Ginecología") {
    list = list.filter((d) => d.sexo === "F");
  }
  if (!specialty) {
    doctorEl.innerHTML = '<option value="">Seleccione especialidad</option>';
    return;
  }
  doctorEl.innerHTML = list.length
    ? list
        .map((d) => `<option value="${d.id}">${d.nombre_completo}</option>`)
        .join("")
    : '<option value="">Sin doctores en esa especialidad</option>';
}

document.getElementById("appt-specialty")?.addEventListener("change", () => {
  fillAppointmentDoctors();
  fillAppointmentPatients();
  if (typeof loadAppointmentSlots === "function") loadAppointmentSlots();
});

document.getElementById("doctor-especialidad")?.addEventListener("change", (e) => {
  if (e.target.value === "Ginecología") {
    document.getElementById("doctor-sexo").value = "F";
  }
});

function populatePatientSelects(patients) {
  _patientsCache = patients || [];
  fillAppointmentPatients();
}

function fillAppointmentPatients() {
  const el = document.getElementById("appt-patient");
  if (!el) return;
  const specialty = document.getElementById("appt-specialty")?.value || "";
  let list = _patientsCache.slice();
  if (specialty === "Ginecología") {
    list = list.filter((p) => p.sexo === "F");
  }
  list.sort((a, b) =>
    _normText(a.nombre_completo).localeCompare(_normText(b.nombre_completo), "es")
  );
  el.innerHTML = list.length
    ? list
        .map((p) => `<option value="${p.id}">${p.nombre_completo} (${p.documento})</option>`)
        .join("")
    : '<option value="">Sin pacientes elegibles</option>';
}

// Horarios
let _scheduleBlocksCache = {};
let _selectedScheduleDoctorId = null;

function selectedScheduleDays() {
  return Array.from(document.querySelectorAll('input[name="schedule-day"]:checked')).map((el) =>
    Number(el.value)
  );
}

function syncScheduleDoctorHidden() {
  const doctorId = document.getElementById("schedule-doctor")?.value;
  const hidden = document.getElementById("schedule-filter-doctor");
  if (hidden && doctorId) hidden.value = doctorId;
  updateScheduleDoctorMeta();
}

function summarizeBlocks(blocks) {
  if (!blocks || !blocks.length) return "Sin horarios";
  const byDay = {};
  blocks.forEach((b) => {
    const d = b.dia_semana;
    if (!byDay[d]) byDay[d] = [];
    byDay[d].push(
      `${String(b.hora_inicio).slice(0, 5)}–${String(b.hora_fin).slice(0, 5)}`
    );
  });
  return Object.keys(byDay)
    .sort((a, b) => Number(a) - Number(b))
    .map((d) => `${WEEKDAYS[d].slice(0, 3)} ${byDay[d].join(", ")}`)
    .join(" · ");
}

function filteredScheduleDoctors() {
  const q = _normText(document.getElementById("schedule-search")?.value || "");
  const esp = document.getElementById("schedule-specialty-filter")?.value || "";
  let list = _doctorsCache.filter((d) => d.activo);
  if (esp) list = list.filter((d) => d.especialidad === esp);
  if (q) {
    list = list.filter((d) => {
      const blob = _normText(`${d.nombre_completo} ${d.especialidad} ${d.correo || ""}`);
      return blob.includes(q);
    });
  }
  return list.sort((a, b) => {
    const espCmp = _normText(a.especialidad).localeCompare(_normText(b.especialidad), "es");
    if (espCmp !== 0) return espCmp;
    return _normText(a.nombre_completo).localeCompare(_normText(b.nombre_completo), "es");
  });
}

async function ensureScheduleBlocks(doctorIds) {
  const missing = doctorIds.filter((id) => !_scheduleBlocksCache[id]);
  await Promise.all(
    missing.map(async (id) => {
      try {
        _scheduleBlocksCache[id] = await api(`/doctors/${id}/schedules`, { silent: true });
      } catch {
        _scheduleBlocksCache[id] = [];
      }
    })
  );
}

async function renderScheduleDirectory() {
  const box = document.getElementById("schedule-doctor-directory");
  const hint = document.getElementById("schedule-dir-hint");
  if (!box) return;
  const list = filteredScheduleDoctors();
  if (hint) {
    hint.textContent = list.length
      ? `${list.length} doctor(es) · clic en Ver agenda`
      : "Ningún doctor coincide con la búsqueda";
  }
  if (!list.length) {
    box.innerHTML = '<p class="empty">Sin doctores para mostrar</p>';
    return;
  }
  await ensureScheduleBlocks(list.map((d) => d.id));
  box.innerHTML = `<table class="schedule-dir-table"><thead><tr>
      <th>Nombre</th><th>Especialidad</th><th>Horario semanal</th><th></th>
    </tr></thead><tbody>
    ${list
      .map((d) => {
        const blocks = _scheduleBlocksCache[d.id] || [];
        const selected = String(_selectedScheduleDoctorId) === String(d.id);
        return `<tr class="${selected ? "is-selected" : ""}">
          <td><strong>${d.nombre_completo}</strong></td>
          <td><span class="role-pill">${d.especialidad}</span></td>
          <td class="schedule-dir-summary">${summarizeBlocks(blocks)}</td>
          <td class="actions">
            <button type="button" class="btn btn-sm btn-primary" onclick="selectScheduleDoctor(${d.id})">
              ${selected ? "Editando" : "Ver agenda"}
            </button>
          </td>
        </tr>`;
      })
      .join("")}
  </tbody></table>`;
}

window.selectScheduleDoctor = async (doctorId) => {
  _selectedScheduleDoctorId = doctorId;
  const sel = document.getElementById("schedule-doctor");
  if (sel) sel.value = String(doctorId);
  syncScheduleDoctorHidden();
  const editor = document.getElementById("schedule-editor");
  if (editor) editor.hidden = false;
  await renderSchedules(doctorId);
  await renderScheduleDirectory();
  editor?.scrollIntoView({ behavior: "smooth", block: "start" });
};

async function loadSchedules() {
  const doctors = await api("/doctors");
  _scheduleBlocksCache = {};
  populateDoctorSelects(doctors);
  await renderScheduleDirectory();
  if (_selectedScheduleDoctorId) {
    const still = _doctorsCache.some((d) => d.id === _selectedScheduleDoctorId && d.activo);
    if (still) {
      await selectScheduleDoctor(_selectedScheduleDoctorId);
    } else {
      _selectedScheduleDoctorId = null;
      const editor = document.getElementById("schedule-editor");
      if (editor) editor.hidden = true;
    }
  }
}

async function renderSchedules(doctorId) {
  const board = document.getElementById("schedules-table");
  if (!board) return;
  try {
    const blocks = await api(`/doctors/${doctorId}/schedules`);
    _scheduleBlocksCache[doctorId] = blocks;
    const byDay = Object.fromEntries(WEEKDAYS.map((_, i) => [i, []]));
    blocks.forEach((b) => {
      byDay[b.dia_semana]?.push(b);
    });
    board.innerHTML = WEEKDAYS.map((nombre, dia) => {
      const items = (byDay[dia] || []).sort((a, b) =>
        String(a.hora_inicio).localeCompare(String(b.hora_inicio))
      );
      const body = items.length
        ? items
            .map(
              (b) => `<div class="schedule-slot">
                <span>${String(b.hora_inicio).slice(0, 5)} – ${String(b.hora_fin).slice(0, 5)}</span>
                <button type="button" class="btn btn-sm btn-danger" onclick="deleteSchedule(${b.id})">Quitar</button>
              </div>`
            )
            .join("")
        : '<p class="schedule-day-empty">Sin turno</p>';
      return `<article class="schedule-day-card">
        <div class="schedule-day-card__head">${nombre}</div>
        <div class="schedule-day-card__body">${body}</div>
      </article>`;
    }).join("");
  } catch (e) {
    toast(e.message, "error");
  }
}

document.getElementById("schedule-search")?.addEventListener("input", () => {
  renderScheduleDirectory();
});
document.getElementById("schedule-specialty-filter")?.addEventListener("change", () => {
  renderScheduleDirectory();
});
document.getElementById("schedule-refresh-btn")?.addEventListener("click", async () => {
  await loadSchedules();
  toast("Horarios redesplegados");
});
document.getElementById("slots-specialty")?.addEventListener("change", fillSlotsDoctorSelect);

document.querySelectorAll(".preset-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".preset-btn").forEach((b) => b.classList.remove("is-active"));
    btn.classList.add("is-active");
    document.getElementById("schedule-start").value = btn.dataset.start;
    document.getElementById("schedule-end").value = btn.dataset.end;
  });
});

document.getElementById("schedule-form")?.addEventListener("submit", async (e) => {
  e.preventDefault();
  const doctorId = parseInt(document.getElementById("schedule-doctor").value, 10);
  const dias = selectedScheduleDays();
  const start = document.getElementById("schedule-start").value;
  const end = document.getElementById("schedule-end").value;
  if (!doctorId) return toast("Selecciona un doctor", "error");
  if (!dias.length) return toast("Marca al menos un día", "error");
  if (!start || !end || start >= end) {
    return toast("La hora de inicio debe ser antes que la de fin", "error");
  }

  let ok = 0;
  let fallos = 0;
  for (const dia of dias) {
    try {
      await api("/schedules", {
        method: "POST",
        body: JSON.stringify({
          doctor_id: doctorId,
          dia_semana: dia,
          hora_inicio: `${start}:00`,
          hora_fin: `${end}:00`,
        }),
        silent: true,
      });
      ok += 1;
    } catch (_) {
      fallos += 1;
    }
  }
  if (ok) toast(`Se agregaron ${ok} turno(s)`);
  if (fallos) toast(`${fallos} día(s) no se pudieron agregar (quizá ya existían)`, "error");
  delete _scheduleBlocksCache[doctorId];
  syncScheduleDoctorHidden();
  await renderSchedules(doctorId);
  await renderScheduleDirectory();
});

const scheduleGenerateBtn = document.getElementById("schedule-generate-btn");
if (scheduleGenerateBtn) {
  scheduleGenerateBtn.addEventListener("click", async () => {
    const doctorId = parseInt(document.getElementById("schedule-doctor").value, 10);
    if (!doctorId) {
      toast("Selecciona un doctor", "error");
      return;
    }
    let reemplazar = false;
    try {
      const actuales = await api(`/doctors/${doctorId}/schedules`, { silent: true });
      if (actuales.length) {
        if (
          !confirm(
            `Este doctor ya tiene ${actuales.length} turno(s). ¿Reemplazarlos por una semana generada al azar?`
          )
        ) {
          return;
        }
        reemplazar = true;
      }
    } catch (_) {
      /* continuar */
    }
    try {
      const bloques = await api(`/doctors/${doctorId}/schedules/generate`, {
        method: "POST",
        body: JSON.stringify({ reemplazar }),
      });
      toast(`Semana lista: ${bloques.length} turno(s)`);
      delete _scheduleBlocksCache[doctorId];
      syncScheduleDoctorHidden();
      await renderSchedules(doctorId);
      await renderScheduleDirectory();
    } catch (err) {
      toast(err.message, "error");
    }
  });
}

window.deleteSchedule = async (id) => {
  if (!confirm("¿Eliminar este bloque horario?")) return;
  try {
    await api(`/schedules/${id}`, { method: "DELETE" });
    toast("Horario eliminado");
    if (_selectedScheduleDoctorId) delete _scheduleBlocksCache[_selectedScheduleDoctorId];
    await loadSchedules();
  } catch (e) {
    toast(e.message, "error");
  }
};

document.getElementById("slots-date").value = todayISO();
document.getElementById("slots-search").addEventListener("click", async () => {
  const doctorId = document.getElementById("slots-doctor").value;
  const day = document.getElementById("slots-date").value;
  if (!doctorId || !day) return toast("Seleccione doctor y fecha", "error");
  try {
    const slots = await api(`/doctors/${doctorId}/slots?day=${day}`);
    document.getElementById("slots-list").innerHTML = slots.length
      ? `<table><thead><tr><th>Inicio</th><th>Fin</th></tr></thead><tbody>
        ${slots.map((s) => `<tr><td>${fmtTime(s.inicio)}</td><td>${fmtTime(s.fin)}</td></tr>`).join("")}
      </tbody></table>`
      : '<p class="empty">No hay slots disponibles</p>';
  } catch (e) {
    toast(e.message, "error");
  }
});

// Citas
async function loadAppointmentSlots() {
  const doctorId = document.getElementById("appt-doctor").value;
  const day = document.getElementById("appt-date").value;
  const slotSelect = document.getElementById("appt-slot");
  if (!doctorId || !day) {
    slotSelect.innerHTML = '<option value="">Seleccione doctor y fecha</option>';
    return;
  }
  try {
    const slots = await api(`/doctors/${doctorId}/slots?day=${day}`);
    slotSelect.innerHTML = slots.length
      ? slots.map((s) => `<option value="${s.inicio}">${fmtTime(s.inicio)} - ${fmtTime(s.fin)}</option>`).join("")
      : '<option value="">Sin slots disponibles</option>';
  } catch (e) {
    toast(e.message, "error");
  }
}

document.getElementById("appt-doctor").addEventListener("change", loadAppointmentSlots);
document.getElementById("appt-date").addEventListener("change", loadAppointmentSlots);
bindAgendaDateInput(document.getElementById("appt-date"));
document.getElementById("appt-date").value = todayISO();
bindAgendaDateInput(document.getElementById("slots-date"));
bindAgendaDateInput(document.getElementById("reschedule-date"));

document.getElementById("appointment-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const payload = {
    doctor_id: parseInt(document.getElementById("appt-doctor").value),
    paciente_id: parseInt(document.getElementById("appt-patient").value),
    inicio: document.getElementById("appt-slot").value,
    notas: document.getElementById("appt-notes").value || null,
  };
  try {
    await api("/appointments", { method: "POST", body: JSON.stringify(payload) });
    toast("Cita agendada");
    e.target.reset();
    document.getElementById("appt-date").value = todayISO();
    loadAppointments();
  } catch (err) {
    toast(err.message, "error");
  }
});

function adminApptActions(a) {
  if (esCitaPagada(a)) return "<small>En historial (pagada)</small>";
  if (a.estado === "scheduled") {
    return `
      <button class="btn btn-sm btn-primary" onclick="markOutcome(${a.id}, 'completed')">Realizada</button>
      <button class="btn btn-sm btn-ghost" onclick="markOutcome(${a.id}, 'patient_late')">Paciente tarde</button>
      <button class="btn btn-sm btn-ghost" onclick="markOutcome(${a.id}, 'doctor_absent')">Doctor ausente</button>
      <button class="btn btn-sm btn-primary" onclick="rescheduleAppt(${a.id})">Reprogramar</button>
      <button class="btn btn-sm btn-danger" onclick="cancelAppt(${a.id})">Cancelar</button>`;
  }
  if (a.estado === "no_show" || a.estado === "doctor_absent") {
    return `<button class="btn btn-sm btn-primary" onclick="rescheduleAppt(${a.id})">Reagendar</button>`;
  }
  if (a.estado === "cancelled") return `<small>${a.motivo_cancelacion || ""}</small>`;
  return "<small>Cerrada</small>";
}

function renderAdminApptTable(list, emptyMsg) {
  if (!list.length) return `<p class="empty">${emptyMsg}</p>`;
  return `<table><thead><tr><th>Fecha</th><th>Doctor</th><th>Paciente</th><th>Estado</th><th>Pago</th><th>Acciones</th></tr></thead><tbody>
    ${list
      .map(
        (a) => `<tr>
      <td>${fmtDateTime(a.inicio)}</td>
      <td>${a.nombre_doctor || a.doctor_id}</td>
      <td>${a.nombre_paciente || a.paciente_id}</td>
      <td>${badge(a.estado)}</td>
      <td>${a.pago ? badge(a.pago.estado) + ` $${a.pago.monto.toFixed(2)}` : "—"}</td>
      <td class="actions">${adminApptActions(a)}</td>
    </tr>`
      )
      .join("")}
  </tbody></table>`;
}

async function loadAppointments() {
  const doctors = await api("/doctors");
  const patients = await api("/patients");
  populateDoctorSelects(doctors);
  populatePatientSelects(patients);

  const params = new URLSearchParams();
  const doctorId = document.getElementById("appt-filter-doctor").value;
  const status = document.getElementById("appt-filter-status").value;
  if (doctorId) params.set("doctor_id", doctorId);
  if (status) params.set("status", status);

  try {
    const appts = await api(`/appointments?${params}`);
    const upcoming = sortByInicioAsc(appts.filter(esCitaProxima));
    const history = sortByInicioDesc(appts.filter(esCitaHistorial));
    const upEl = document.getElementById("appointments-upcoming");
    const histEl = document.getElementById("appointments-history");
    if (upEl) upEl.innerHTML = renderAdminApptTable(upcoming, "No hay citas próximas sin cobrar");
    if (histEl) histEl.innerHTML = renderAdminApptTable(history, "Sin historial aún");
  } catch (e) {
    toast(e.message, "error");
  }
}

document.getElementById("appt-filter-btn").addEventListener("click", loadAppointments);

let _pendingCancelId = null;
let _pendingReschedule = null;

window.markOutcome = async (id, resultado) => {
  const labels = {
    completed: "¿Marcar la cita como realizada?",
    patient_late: "¿Registrar que el paciente llegó tarde / no asistió?",
    doctor_absent: "¿Registrar que el doctor no llegó?",
  };
  if (!confirm(labels[resultado] || "¿Confirmar?")) return;
  try {
    await api(`/appointments/${id}/outcome`, {
      method: "POST",
      body: JSON.stringify({ resultado }),
    });
    toast("Resultado de la cita guardado");
    loadAppointments();
  } catch (e) {
    toast(e.message, "error");
  }
};

window.cancelAppt = async (id) => {
  const dlg = document.getElementById("cancel-appt-dialog");
  if (!dlg) return;
  try {
    const appt = await api(`/appointments/${id}`, { silent: true });
    _pendingCancelId = id;
    document.getElementById("cancel-appt-summary").textContent =
      `${appt.nombre_paciente || "Paciente"} con ${appt.nombre_doctor || "doctor"} · ${fmtDateTime(appt.inicio)}`;
    document.getElementById("cancel-appt-reason").value = "";
    dlg.showModal();
  } catch (e) {
    toast(e.message, "error");
  }
};

const cancelApptForm = document.getElementById("cancel-appt-form");
if (cancelApptForm) {
  cancelApptForm.addEventListener("submit", async (ev) => {
    const submitter = ev.submitter;
    if (!submitter || submitter.value !== "save") {
      _pendingCancelId = null;
      return;
    }
    ev.preventDefault();
    const reason = document.getElementById("cancel-appt-reason").value.trim();
    if (!_pendingCancelId || !reason) {
      toast("Escribe el motivo de cancelación", "error");
      return;
    }
    try {
      await api(`/appointments/${_pendingCancelId}/cancel`, {
        method: "POST",
        body: JSON.stringify({ motivo: reason }),
      });
      document.getElementById("cancel-appt-dialog").close();
      _pendingCancelId = null;
      toast("Cita cancelada");
      loadAppointments();
    } catch (e) {
      toast(e.message, "error");
    }
  });
}

function _rescheduleDoctorId() {
  const sel = document.getElementById("reschedule-doctor");
  if (sel && sel.value) return Number(sel.value);
  return _pendingReschedule ? _pendingReschedule.doctor_id : null;
}

async function loadRescheduleSlots() {
  const day = document.getElementById("reschedule-date").value;
  const slotSelect = document.getElementById("reschedule-slot");
  const hint = document.getElementById("reschedule-slots-hint");
  const doctorId = _rescheduleDoctorId();
  if (!_pendingReschedule || !day || !doctorId) {
    slotSelect.innerHTML = '<option value="">Seleccione doctor y fecha</option>';
    return;
  }
  const hoy = todayISO();
  if (day < hoy) {
    slotSelect.innerHTML = '<option value="">No se puede reagendar en el pasado</option>';
    if (hint) hint.textContent = "La fecha está en el pasado (calendario México).";
    return;
  }
  try {
    const slots = await api(
      `/doctors/${doctorId}/slots?day=${day}&excluir_cita_id=${_pendingReschedule.id}`,
      { silent: true }
    );
    const doc = (_doctorsCache || []).find((d) => d.id === doctorId);
    const nombre = doc ? doc.nombre_completo : `doctor #${doctorId}`;
    if (hint) {
      hint.textContent =
        day === hoy
          ? `Hoy · ${nombre}: solo horas futuras (Ciudad de México). ${slots.length} horario(s).`
          : `${nombre}: ${slots.length} horario(s) libre(s) ese día.`;
    }
    slotSelect.innerHTML = slots.length
      ? slots
          .map(
            (s) =>
              `<option value="${s.inicio}">${fmtTime(s.inicio)} - ${fmtTime(s.fin)}</option>`
          )
          .join("")
      : '<option value="">Sin horarios libres ese día</option>';
  } catch (e) {
    slotSelect.innerHTML = '<option value="">Error al cargar horarios</option>';
    toast(e.message, "error");
  }
}

window.rescheduleAppt = async (id) => {
  const dlg = document.getElementById("reschedule-dialog");
  if (!dlg) return;
  try {
    const appt = await api(`/appointments/${id}`);
    _pendingReschedule = appt;
    const wrap = document.getElementById("reschedule-doctor-wrap");
    const doctorSel = document.getElementById("reschedule-doctor");
    const especialidad = appt.especialidad_doctor;
    if (wrap) wrap.hidden = false;

    const doctors = _doctorsCache.length
      ? _doctorsCache
      : await api("/doctors", { silent: true });
    let list = doctors.filter(
      (d) => d.activo && (!especialidad || d.especialidad === especialidad)
    );
    if (especialidad === "Ginecología") list = list.filter((d) => d.sexo === "F");
    if (appt.estado === "doctor_absent") {
      list = list.filter((d) => d.id !== appt.doctor_id);
      document.getElementById("reschedule-summary").textContent =
        `${appt.nombre_paciente || "Paciente"} · doctor ausente. Elige otro de ${especialidad || "la misma especialidad"} y un horario libre.`;
    } else {
      document.getElementById("reschedule-summary").textContent =
        `${appt.nombre_paciente || "Paciente"} · actual: ${fmtDateTime(appt.inicio)}. Elige doctor (misma especialidad), fecha y horario.`;
    }
    list.sort((a, b) =>
      _normText(a.nombre_completo).localeCompare(_normText(b.nombre_completo), "es")
    );
    doctorSel.innerHTML = list.length
      ? list
          .map(
            (d) =>
              `<option value="${d.id}" ${d.id === appt.doctor_id ? "selected" : ""}>${d.nombre_completo} — ${d.especialidad}</option>`
          )
          .join("")
      : '<option value="">Sin doctores disponibles</option>';
    if (appt.estado === "doctor_absent" && list.length) {
      doctorSel.value = String(list[0].id);
    } else if (list.some((d) => d.id === appt.doctor_id)) {
      doctorSel.value = String(appt.doctor_id);
    }

    const dayInput = document.getElementById("reschedule-date");
    dayInput.value = todayISO();
    bindAgendaDateInput(dayInput);
    await loadRescheduleSlots();
    dlg.showModal();
  } catch (e) {
    toast(e.message, "error");
  }
};

const rescheduleDate = document.getElementById("reschedule-date");
if (rescheduleDate) {
  rescheduleDate.addEventListener("change", loadRescheduleSlots);
}
document.getElementById("reschedule-doctor")?.addEventListener("change", loadRescheduleSlots);

const rescheduleForm = document.getElementById("reschedule-form");
if (rescheduleForm) {
  rescheduleForm.addEventListener("submit", async (ev) => {
    const submitter = ev.submitter;
    if (!submitter || submitter.value !== "save") {
      _pendingReschedule = null;
      return;
    }
    ev.preventDefault();
    const inicio = document.getElementById("reschedule-slot").value;
    if (!_pendingReschedule || !inicio) {
      toast("Elige un horario disponible", "error");
      return;
    }
    const day = document.getElementById("reschedule-date").value;
    if (day < todayISO()) {
      toast("No se puede reagendar en una fecha pasada", "error");
      return;
    }
    const doctorId = _rescheduleDoctorId();
    if (!doctorId) {
      toast("Elige un doctor", "error");
      return;
    }
    const body = { inicio, doctor_id: doctorId };
    try {
      await api(`/appointments/${_pendingReschedule.id}/reschedule`, {
        method: "POST",
        body: JSON.stringify(body),
      });
      document.getElementById("reschedule-dialog").close();
      _pendingReschedule = null;
      toast("Cita reprogramada");
      loadAppointments();
    } catch (e) {
      toast(e.message, "error");
    }
  });
}

// Pagos
async function loadPayments() {
  const doctors = await api("/doctors");
  populateDoctorSelects(doctors);

  const params = new URLSearchParams();
  const status = document.getElementById("pay-filter-status").value;
  const doctorId = document.getElementById("pay-filter-doctor").value;
  if (status) params.set("status", status);
  if (doctorId) params.set("doctor_id", doctorId);

  try {
    const payments = await api(`/payments?${params}`);
    const appts = await api("/appointments");
    const apptMap = Object.fromEntries(appts.map((a) => [a.id, a]));

    document.getElementById("payments-table").innerHTML = payments.length
      ? `<table><thead><tr><th>Cita</th><th>Monto</th><th>Estado</th><th>Método</th><th>Acciones</th></tr></thead><tbody>
        ${payments.map((p) => {
          const a = apptMap[p.cita_id];
          const actions =
            p.estado === "paid"
              ? "<small>Cobrado · en historial de citas</small>"
              : `<button class="btn btn-sm btn-primary" onclick="updatePayment(${p.id}, 'paid')">Marcar pagado</button>
                 <button class="btn btn-sm" onclick="updatePayment(${p.id}, 'exempt')">Exento</button>`;
          return `<tr>
            <td>${a ? `${a.nombre_paciente} — ${fmtDateTime(a.inicio)}` : `#${p.cita_id}`}</td>
            <td>$${p.monto.toFixed(2)}</td>
            <td>${badge(p.estado)}</td>
            <td>${p.metodo || "—"}</td>
            <td class="actions">${actions}</td>
          </tr>`;
        }).join("")}
      </tbody></table>`
      : '<p class="empty">No hay pagos</p>';
  } catch (e) {
    toast(e.message, "error");
  }
}

document.getElementById("pay-filter-btn").addEventListener("click", loadPayments);

window.updatePayment = async (id, estado) => {
  try {
    await api(`/payments/${id}`, {
      method: "PATCH",
      body: JSON.stringify({
        estado,
        metodo: estado === "paid" ? "cash" : undefined,
      }),
    });
    toast(estado === "paid" ? "Pago registrado · cita movida al historial" : "Pago actualizado");
    loadPayments();
    if (typeof loadAppointments === "function") loadAppointments();
    if (typeof loadDashboard === "function") loadDashboard();
  } catch (e) {
    toast(e.message, "error");
  }
};

async function loadUsers() {
  const accounts = [
    { email: "emiliano@farma", role: "Administrador", name: "Emiliano Farma", access: "Control total" },
    { email: "sara@farma", role: "Administrador", name: "Sara Farma", access: "Control total" },
    { email: "director@farma", role: "Director", name: "Laura Mendoza", access: "Supervisión y reportes" },
    { email: "doctor@farma", role: "Doctor", name: "Dr. Andrés Vega", access: "Agenda clínica propia" },
    { email: "paciente@farma", role: "Paciente", name: "Sofía Ramírez", access: "Citas y pagos propios" },
  ];
  const el = document.getElementById("users-table");
  if (!el) return;
  el.innerHTML = `<table><thead><tr><th>Nombre</th><th>Correo</th><th>Rol</th><th>Permisos</th></tr></thead><tbody>
    ${accounts.map((a) => `<tr><td>${a.name}</td><td>${a.email}</td><td><span class="role-pill">${a.role}</span></td><td>${a.access}</td></tr>`).join("")}
  </tbody></table>`;
}

// Init
setPageChrome(document.getElementById("panel-dashboard"));
loadDashboard();

