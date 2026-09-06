const loaders = {
  dashboard: loadDashboard,
  appointments: loadAppointments,
  payments: loadPayments,
  staff: loadStaff,
  reports: loadReports,
  media: loadMedia,
};

bindRoleNavigation(loaders);

let _mediaRefresh = null;
async function loadMedia() {
  if (!_mediaRefresh) _mediaRefresh = bindMediaPanel();
  await _mediaRefresh();
}

async function loadDashboard() {
  try {
    const stats = await api("/appointments/stats/dashboard");
    document.getElementById("stat-doctors").textContent = stats.doctors_active;
    document.getElementById("stat-patients").textContent = stats.patients_total;
    document.getElementById("stat-today").textContent = stats.appointments_today;
    document.getElementById("stat-pending").textContent = stats.payments_pending;
    const appts = await api("/appointments?status=scheduled");
    const upcoming = appts.slice(0, 8);
    document.getElementById("director-recent").innerHTML = upcoming.length
      ? `<table><thead><tr><th>Fecha</th><th>Doctor</th><th>Paciente</th><th>Estado</th></tr></thead><tbody>
        ${upcoming.map((a) => `<tr><td>${fmtDateTime(a.starts_at)}</td><td>${a.doctor_name || "—"}</td><td>${a.patient_name || "—"}</td><td>${badge(a.status)}</td></tr>`).join("")}
      </tbody></table>`
      : empty("Sin actividad programada");
  } catch (e) {
    toast(e.message, "error");
  }
}

async function loadAppointments() {
  try {
    const appts = await api("/appointments");
    document.getElementById("director-appointments").innerHTML = appts.length
      ? `<table><thead><tr><th>Fecha</th><th>Doctor</th><th>Paciente</th><th>Estado</th><th>Pago</th></tr></thead><tbody>
        ${appts.map((a) => `<tr><td>${fmtDateTime(a.starts_at)}</td><td>${a.doctor_name || "—"}</td><td>${a.patient_name || "—"}</td><td>${badge(a.status)}</td><td>${a.payment ? badge(a.payment.status) : "—"}</td></tr>`).join("")}
      </tbody></table>`
      : empty("No hay citas");
  } catch (e) {
    toast(e.message, "error");
  }
}

async function loadPayments() {
  try {
    const payments = await api("/payments");
    document.getElementById("director-payments").innerHTML = payments.length
      ? `<table><thead><tr><th>Cita</th><th>Monto</th><th>Estado</th><th>Método</th></tr></thead><tbody>
        ${payments.map((p) => `<tr><td>#${p.appointment_id}</td><td>$${Number(p.amount).toFixed(2)}</td><td>${badge(p.status)}</td><td>${p.method || "—"}</td></tr>`).join("")}
      </tbody></table>`
      : empty("No hay pagos");
  } catch (e) {
    toast(e.message, "error");
  }
}

async function loadStaff() {
  try {
    const [doctors, patients] = await Promise.all([api("/doctors"), api("/patients")]);
    document.getElementById("director-doctors").innerHTML = doctors.length
      ? `<table><thead><tr><th>Nombre</th><th>Especialidad</th><th>Tarifa</th><th>Estado</th></tr></thead><tbody>
        ${doctors.map((d) => `<tr><td>${d.full_name}</td><td>${d.specialty}</td><td>$${Number(d.default_fee).toFixed(2)}</td><td>${d.is_active ? "Activo" : "Inactivo"}</td></tr>`).join("")}
      </tbody></table>`
      : empty("Sin doctores");
    document.getElementById("director-patients").innerHTML = patients.length
      ? `<table><thead><tr><th>Nombre</th><th>Documento</th><th>Teléfono</th><th>Email</th></tr></thead><tbody>
        ${patients.map((p) => `<tr><td>${p.full_name}</td><td>${p.document_id}</td><td>${p.phone || "—"}</td><td>${p.email || "—"}</td></tr>`).join("")}
      </tbody></table>`
      : empty("Sin pacientes");
  } catch (e) {
    toast(e.message, "error");
  }
}

async function loadReports() {
  try {
    const stats = await api("/appointments/stats/dashboard");
    const payments = await api("/payments");
    const paid = payments.filter((p) => p.status === "paid").reduce((s, p) => s + Number(p.amount), 0);
    const pending = payments.filter((p) => p.status === "pending").reduce((s, p) => s + Number(p.amount), 0);
    document.getElementById("director-reports").innerHTML = `
      <div class="stats-grid" style="grid-template-columns: repeat(2,minmax(0,1fr)); margin-bottom:0;">
        <article class="stat-card"><div class="stat-card__value">${stats.appointments_today}</div><div class="stat-card__label">Citas del día</div></article>
        <article class="stat-card"><div class="stat-card__value">${stats.doctors_active}</div><div class="stat-card__label">Capacidad médica activa</div></article>
        <article class="stat-card"><div class="stat-card__value">$${paid.toFixed(0)}</div><div class="stat-card__label">Cobrado (histórico)</div></article>
        <article class="stat-card accent"><div class="stat-card__value">$${pending.toFixed(0)}</div><div class="stat-card__label">Cartera pendiente</div></article>
      </div>`;
  } catch (e) {
    toast(e.message, "error");
  }
}

loadDashboard();
