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
      throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
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

function todayISO() {
  return new Date().toISOString().slice(0, 10);
}

const PAGE_LOADERS = {
  dashboard: () => loadDashboard(),
  doctors: () => loadDoctors(),
  patients: () => loadPatients(),
  schedules: () => loadSchedules(),
  appointments: () => loadAppointments(),
  payments: () => loadPayments(),
  users: () => loadUsers(),
  media: () => loadMedia(),
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
    const upcoming = appts.filter((a) => new Date(a.starts_at) >= new Date()).slice(0, 8);
    const container = document.getElementById("dashboard-appointments");
    if (!upcoming.length) {
      container.innerHTML = '<p class="empty">No hay citas programadas próximas</p>';
      return;
    }
    container.innerHTML = `<table><thead><tr><th>Fecha</th><th>Doctor</th><th>Paciente</th><th>Estado</th><th>Pago</th></tr></thead><tbody>
      ${upcoming.map((a) => `<tr>
        <td>${fmtDateTime(a.starts_at)}</td>
        <td>${a.doctor_name || a.doctor_id}</td>
        <td>${a.patient_name || a.patient_id}</td>
        <td>${badge(a.status)}</td>
        <td>${a.payment ? badge(a.payment.status) : "—"}</td>
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
      ? `<table><thead><tr><th>Nombre</th><th>Especialidad</th><th>Duración</th><th>Tarifa</th><th>Activo</th><th>Acciones</th></tr></thead><tbody>
        ${doctors.map((d) => `<tr>
          <td>${d.full_name}</td><td>${d.specialty}</td><td>${d.consultation_minutes} min</td>
          <td>$${d.default_fee.toFixed(2)}</td><td>${d.is_active ? "Sí" : "No"}</td>
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
  document.getElementById("doctor-active").checked = true;
  document.getElementById("doctor-form-title").textContent = "Nuevo doctor";
  document.getElementById("doctor-cancel-edit").style.display = "none";
}

document.getElementById("doctor-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const id = document.getElementById("doctor-id").value;
  const payload = {
    full_name: document.getElementById("doctor-name").value,
    specialty: document.getElementById("doctor-specialty").value,
    consultation_minutes: parseInt(document.getElementById("doctor-minutes").value),
    default_fee: parseFloat(document.getElementById("doctor-fee").value),
    is_active: document.getElementById("doctor-active").checked,
  };
  try {
    if (id) {
      await api(`/doctors/${id}`, { method: "PUT", body: JSON.stringify(payload) });
      toast("Doctor actualizado");
    } else {
      await api("/doctors", { method: "POST", body: JSON.stringify(payload) });
      toast("Doctor creado");
    }
    resetDoctorForm();
    loadDoctors();
  } catch (err) {
    toast(err.message, "error");
  }
});

document.getElementById("doctor-cancel-edit").addEventListener("click", resetDoctorForm);

window.editDoctor = async (id) => {
  const d = await api(`/doctors/${id}`);
  document.getElementById("doctor-id").value = d.id;
  document.getElementById("doctor-name").value = d.full_name;
  document.getElementById("doctor-specialty").value = d.specialty;
  document.getElementById("doctor-minutes").value = d.consultation_minutes;
  document.getElementById("doctor-fee").value = d.default_fee;
  document.getElementById("doctor-active").checked = d.is_active;
  document.getElementById("doctor-form-title").textContent = "Editar doctor";
  document.getElementById("doctor-cancel-edit").style.display = "inline-block";
};

window.deleteDoctor = async (id) => {
  if (!confirm("¿Eliminar este doctor?")) return;
  try {
    await api(`/doctors/${id}`, { method: "DELETE" });
    toast("Doctor eliminado");
    loadDoctors();
  } catch (e) {
    toast(e.message, "error");
  }
};

// Pacientes
async function loadPatients() {
  try {
    const patients = await api("/patients");
    document.getElementById("patients-table").innerHTML = patients.length
      ? `<table><thead><tr><th>Nombre</th><th>Documento</th><th>Teléfono</th><th>Email</th><th>Acciones</th></tr></thead><tbody>
        ${patients.map((p) => `<tr>
          <td>${p.full_name}</td><td>${p.document_id}</td><td>${p.phone || "—"}</td><td>${p.email || "—"}</td>
          <td class="actions">
            <button class="btn btn-sm btn-primary" onclick="editPatient(${p.id})">Editar</button>
            <button class="btn btn-sm btn-danger" onclick="deletePatient(${p.id})">Eliminar</button>
          </td>
        </tr>`).join("")}
      </tbody></table>`
      : '<p class="empty">No hay pacientes registrados</p>';
    populatePatientSelects(patients);
  } catch (e) {
    toast(e.message, "error");
  }
}

function resetPatientForm() {
  document.getElementById("patient-form").reset();
  document.getElementById("patient-id").value = "";
  document.getElementById("patient-form-title").textContent = "Nuevo paciente";
  document.getElementById("patient-cancel-edit").style.display = "none";
}

document.getElementById("patient-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const id = document.getElementById("patient-id").value;
  const payload = {
    full_name: document.getElementById("patient-name").value,
    document_id: document.getElementById("patient-document").value,
    phone: document.getElementById("patient-phone").value || null,
    email: document.getElementById("patient-email").value || null,
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
  document.getElementById("patient-name").value = p.full_name;
  document.getElementById("patient-document").value = p.document_id;
  document.getElementById("patient-phone").value = p.phone || "";
  document.getElementById("patient-email").value = p.email || "";
  document.getElementById("patient-form-title").textContent = "Editar paciente";
  document.getElementById("patient-cancel-edit").style.display = "inline-block";
};

window.deletePatient = async (id) => {
  if (!confirm("¿Eliminar este paciente?")) return;
  try {
    await api(`/patients/${id}`, { method: "DELETE" });
    toast("Paciente eliminado");
    loadPatients();
  } catch (e) {
    toast(e.message, "error");
  }
};

// Selects helpers
function populateDoctorSelects(doctors) {
  const active = doctors.filter((d) => d.is_active);
  const opts = (list, all) => {
    const base = all ? '<option value="">Todos</option>' : "";
    return base + list.map((d) => `<option value="${d.id}">${d.full_name} (${d.specialty})</option>`).join("");
  };
  ["schedule-doctor", "schedule-filter-doctor", "slots-doctor", "appt-doctor"].forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.innerHTML = opts(doctors, false);
  });
  ["appt-filter-doctor", "pay-filter-doctor"].forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.innerHTML = opts(doctors, true);
  });
  if (document.getElementById("schedule-filter-doctor") && doctors.length) {
    document.getElementById("schedule-filter-doctor").innerHTML = opts(doctors, false);
  }
}

function populatePatientSelects(patients) {
  const el = document.getElementById("appt-patient");
  if (el) {
    el.innerHTML = patients.map((p) => `<option value="${p.id}">${p.full_name} (${p.document_id})</option>`).join("");
  }
}

// Horarios
async function loadSchedules() {
  const doctors = await api("/doctors");
  populateDoctorSelects(doctors);
  const doctorId = document.getElementById("schedule-filter-doctor").value || doctors[0]?.id;
  if (doctorId) {
    document.getElementById("schedule-filter-doctor").value = doctorId;
    await renderSchedules(doctorId);
  }
}

async function renderSchedules(doctorId) {
  try {
    const blocks = await api(`/doctors/${doctorId}/schedules`);
    document.getElementById("schedules-table").innerHTML = blocks.length
      ? `<table><thead><tr><th>Día</th><th>Inicio</th><th>Fin</th><th>Acciones</th></tr></thead><tbody>
        ${blocks.map((b) => `<tr>
          <td>${WEEKDAYS[b.weekday]}</td>
          <td>${b.start_time.slice(0, 5)}</td>
          <td>${b.end_time.slice(0, 5)}</td>
          <td><button class="btn btn-sm btn-danger" onclick="deleteSchedule(${b.id})">Eliminar</button></td>
        </tr>`).join("")}
      </tbody></table>`
      : '<p class="empty">Sin horarios para este doctor</p>';
  } catch (e) {
    toast(e.message, "error");
  }
}

document.getElementById("schedule-filter-doctor").addEventListener("change", (e) => {
  renderSchedules(e.target.value);
});

document.getElementById("schedule-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const payload = {
    doctor_id: parseInt(document.getElementById("schedule-doctor").value),
    weekday: parseInt(document.getElementById("schedule-weekday").value),
    start_time: document.getElementById("schedule-start").value + ":00",
    end_time: document.getElementById("schedule-end").value + ":00",
  };
  try {
    await api("/schedules", { method: "POST", body: JSON.stringify(payload) });
    toast("Horario agregado");
    e.target.reset();
    renderSchedules(payload.doctor_id);
  } catch (err) {
    toast(err.message, "error");
  }
});

window.deleteSchedule = async (id) => {
  if (!confirm("¿Eliminar este bloque horario?")) return;
  try {
    await api(`/schedules/${id}`, { method: "DELETE" });
    toast("Horario eliminado");
    loadSchedules();
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
        ${slots.map((s) => `<tr><td>${fmtTime(s.starts_at)}</td><td>${fmtTime(s.ends_at)}</td></tr>`).join("")}
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
      ? slots.map((s) => `<option value="${s.starts_at}">${fmtTime(s.starts_at)} - ${fmtTime(s.ends_at)}</option>`).join("")
      : '<option value="">Sin slots disponibles</option>';
  } catch (e) {
    toast(e.message, "error");
  }
}

document.getElementById("appt-doctor").addEventListener("change", loadAppointmentSlots);
document.getElementById("appt-date").addEventListener("change", loadAppointmentSlots);
document.getElementById("appt-date").value = todayISO();

document.getElementById("appointment-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const payload = {
    doctor_id: parseInt(document.getElementById("appt-doctor").value),
    patient_id: parseInt(document.getElementById("appt-patient").value),
    starts_at: document.getElementById("appt-slot").value,
    notes: document.getElementById("appt-notes").value || null,
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
    document.getElementById("appointments-table").innerHTML = appts.length
      ? `<table><thead><tr><th>Fecha</th><th>Doctor</th><th>Paciente</th><th>Estado</th><th>Pago</th><th>Acciones</th></tr></thead><tbody>
        ${appts.map((a) => `<tr>
          <td>${fmtDateTime(a.starts_at)}</td>
          <td>${a.doctor_name || a.doctor_id}</td>
          <td>${a.patient_name || a.patient_id}</td>
          <td>${badge(a.status)}</td>
          <td>${a.payment ? badge(a.payment.status) + ` $${a.payment.amount.toFixed(2)}` : "—"}</td>
          <td class="actions">
            ${a.status !== "cancelled" ? `
              <button class="btn btn-sm btn-primary" onclick="rescheduleAppt(${a.id})">Reprogramar</button>
              <button class="btn btn-sm btn-danger" onclick="cancelAppt(${a.id})">Cancelar</button>
            ` : `<small>${a.cancellation_reason || ""}</small>`}
          </td>
        </tr>`).join("")}
      </tbody></table>`
      : '<p class="empty">No hay citas</p>';
  } catch (e) {
    toast(e.message, "error");
  }
}

document.getElementById("appt-filter-btn").addEventListener("click", loadAppointments);

window.cancelAppt = async (id) => {
  const reason = prompt("Motivo de cancelación:");
  if (!reason) return;
  try {
    await api(`/appointments/${id}/cancel`, { method: "POST", body: JSON.stringify({ reason }) });
    toast("Cita cancelada");
    loadAppointments();
  } catch (e) {
    toast(e.message, "error");
  }
};

window.rescheduleAppt = async (id) => {
  const appt = await api(`/appointments/${id}`);
  const day = prompt("Nueva fecha (YYYY-MM-DD):", appt.starts_at.slice(0, 10));
  if (!day) return;
  const slots = await api(`/doctors/${appt.doctor_id}/slots?day=${day}`);
  if (!slots.length) return toast("No hay slots disponibles ese día", "error");
  const options = slots.map((s, i) => `${i + 1}. ${fmtTime(s.starts_at)}`).join("\n");
  const choice = prompt(`Slots disponibles:\n${options}\n\nNúmero de slot:`);
  if (!choice) return;
  const slot = slots[parseInt(choice) - 1];
  if (!slot) return toast("Selección inválida", "error");
  try {
    await api(`/appointments/${id}/reschedule`, { method: "POST", body: JSON.stringify({ starts_at: slot.starts_at }) });
    toast("Cita reprogramada");
    loadAppointments();
  } catch (e) {
    toast(e.message, "error");
  }
};

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
          const a = apptMap[p.appointment_id];
          return `<tr>
            <td>${a ? `${a.patient_name} — ${fmtDateTime(a.starts_at)}` : `#${p.appointment_id}`}</td>
            <td>$${p.amount.toFixed(2)}</td>
            <td>${badge(p.status)}</td>
            <td>${p.method || "—"}</td>
            <td class="actions">
              <button class="btn btn-sm btn-primary" onclick="updatePayment(${p.id}, 'paid')">Marcar pagado</button>
              <button class="btn btn-sm" onclick="updatePayment(${p.id}, 'exempt')">Exento</button>
            </td>
          </tr>`;
        }).join("")}
      </tbody></table>`
      : '<p class="empty">No hay pagos</p>';
  } catch (e) {
    toast(e.message, "error");
  }
}

document.getElementById("pay-filter-btn").addEventListener("click", loadPayments);

window.updatePayment = async (id, status) => {
  try {
    await api(`/payments/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ status, method: status === "paid" ? "cash" : undefined }),
    });
    toast("Pago actualizado");
    loadPayments();
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

let _mediaRefresh = null;
async function loadMedia() {
  if (!_mediaRefresh) _mediaRefresh = bindMediaPanel();
  await _mediaRefresh();
}

// Init
setPageChrome(document.getElementById("panel-dashboard"));
loadDashboard();
