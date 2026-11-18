const loaders = {
  dashboard: loadDashboard,
  appointments: loadAppointments,
  payments: loadPayments,
  staff: loadStaff,
  reports: loadReports,
};

bindRoleNavigation(loaders);

async function loadDashboard() {
  try {
    const stats = await api("/appointments/stats/dashboard");
    document.getElementById("stat-doctors").textContent = stats.doctors_active;
    document.getElementById("stat-patients").textContent = stats.patients_total;
    document.getElementById("stat-today").textContent = stats.appointments_today;
    document.getElementById("stat-pending").textContent = stats.payments_pending;
    const appts = await api("/appointments?status=scheduled");
    const upcoming = sortByInicioAsc(appts.filter(esCitaProxima)).slice(0, 8);
    document.getElementById("director-recent").innerHTML = upcoming.length
      ? `<table><thead><tr><th>Fecha</th><th>Doctor</th><th>Paciente</th><th>Estado</th><th>Pago</th></tr></thead><tbody>
        ${upcoming.map((a) => `<tr><td>${fmtDateTime(a.inicio)}</td><td>${a.nombre_doctor || "—"}</td><td>${a.nombre_paciente || "—"}</td><td>${badge(a.estado)}</td><td>${a.pago ? badge(a.pago.estado) : "—"}</td></tr>`).join("")}
      </tbody></table>`
      : empty("Sin citas próximas sin cobrar");
  } catch (e) {
    toast(e.message, "error");
  }
}

async function loadAppointments() {
  try {
    const appts = await api("/appointments");
    document.getElementById("director-appointments").innerHTML = appts.length
      ? `<table><thead><tr><th>Fecha</th><th>Doctor</th><th>Paciente</th><th>Estado</th><th>Pago</th></tr></thead><tbody>
        ${appts.map((a) => `<tr><td>${fmtDateTime(a.inicio)}</td><td>${a.nombre_doctor || "—"}</td><td>${a.nombre_paciente || "—"}</td><td>${badge(a.estado)}</td><td>${a.pago ? badge(a.pago.status) : "—"}</td></tr>`).join("")}
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
        ${payments.map((p) => `<tr><td>#${p.cita_id}</td><td>$${Number(p.monto).toFixed(2)}</td><td>${badge(p.estado)}</td><td>${p.method || "—"}</td></tr>`).join("")}
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
        ${doctors.map((d) => `<tr><td>${d.nombre_completo}</td><td>${d.especialidad}</td><td>$${Number(d.tarifa).toFixed(2)}</td><td>${d.activo ? "Activo" : "Inactivo"}</td></tr>`).join("")}
      </tbody></table>`
      : empty("Sin doctores");
    document.getElementById("director-patients").innerHTML = patients.length
      ? `<table><thead><tr><th>Nombre</th><th>Documento</th><th>Teléfono</th><th>Email</th></tr></thead><tbody>
        ${patients.map((p) => `<tr><td>${p.nombre_completo}</td><td>${p.documento}</td><td>${p.telefono || "—"}</td><td>${p.correo || "—"}</td></tr>`).join("")}
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
    const paid = payments.filter((p) => p.estado === "paid").reduce((s, p) => s + Number(p.monto), 0);
    const pending = payments.filter((p) => p.estado === "pending").reduce((s, p) => s + Number(p.monto), 0);
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
