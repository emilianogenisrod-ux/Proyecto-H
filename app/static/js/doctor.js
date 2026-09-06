const USER = getBootUser() || {};
const DOCTOR_ID = USER.doctor_id;

const loaders = {
  dashboard: loadDashboard,
  schedule: loadSchedule,
  appointments: loadAppointments,
  patients: loadPatients,
};

bindRoleNavigation(loaders);

async function loadDashboard() {
  if (!DOCTOR_ID) {
    document.getElementById("doctor-upcoming").innerHTML = empty("Cuenta de doctor no vinculada al expediente clínico.");
    return;
  }
  try {
    const note = document.getElementById("doctor-profile-note");
    if (note) note.textContent = `${USER.name}${USER.specialty ? " · " + USER.specialty : ""}`;

    const [appts, blocks] = await Promise.all([
      api(`/appointments?doctor_id=${DOCTOR_ID}`),
      api(`/doctors/${DOCTOR_ID}/schedules`),
    ]);
    const today = todayISO();
    const todayCount = appts.filter((a) => a.starts_at.slice(0, 10) === today && a.status === "scheduled").length;
    document.getElementById("doc-stat-today").textContent = todayCount;
    document.getElementById("doc-stat-week").textContent = appts.filter((a) => a.status === "scheduled").length;
    document.getElementById("doc-stat-blocks").textContent = blocks.length;

    const upcoming = appts
      .filter((a) => a.status === "scheduled" && new Date(a.starts_at) >= new Date())
      .slice(0, 10);
    document.getElementById("doctor-upcoming").innerHTML = upcoming.length
      ? `<table><thead><tr><th>Fecha</th><th>Paciente</th><th>Notas</th><th>Estado</th></tr></thead><tbody>
        ${upcoming.map((a) => `<tr><td>${fmtDateTime(a.starts_at)}</td><td>${a.patient_name || "—"}</td><td>${a.notes || "—"}</td><td>${badge(a.status)}</td></tr>`).join("")}
      </tbody></table>`
      : empty("No tiene citas próximas");
  } catch (e) {
    toast(e.message, "error");
  }
}

async function loadSchedule() {
  if (!DOCTOR_ID) return;
  try {
    const blocks = await api(`/doctors/${DOCTOR_ID}/schedules`);
    document.getElementById("doctor-schedule").innerHTML = blocks.length
      ? `<table><thead><tr><th>Día</th><th>Inicio</th><th>Fin</th></tr></thead><tbody>
        ${blocks.map((b) => `<tr><td>${WEEKDAYS[b.weekday]}</td><td>${b.start_time}</td><td>${b.end_time}</td></tr>`).join("")}
      </tbody></table>`
      : empty("Sin bloques de horario");
  } catch (e) {
    toast(e.message, "error");
  }
}

async function loadAppointments() {
  if (!DOCTOR_ID) return;
  try {
    const appts = await api(`/appointments?doctor_id=${DOCTOR_ID}`);
    document.getElementById("doctor-appointments").innerHTML = appts.length
      ? `<table><thead><tr><th>Fecha</th><th>Paciente</th><th>Estado</th><th>Pago</th></tr></thead><tbody>
        ${appts.map((a) => `<tr><td>${fmtDateTime(a.starts_at)}</td><td>${a.patient_name || "—"}</td><td>${badge(a.status)}</td><td>${a.payment ? badge(a.payment.status) : "—"}</td></tr>`).join("")}
      </tbody></table>`
      : empty("Sin citas");
  } catch (e) {
    toast(e.message, "error");
  }
}

async function loadPatients() {
  try {
    const patients = await api("/patients");
    document.getElementById("doctor-patients").innerHTML = patients.length
      ? `<table><thead><tr><th>Nombre</th><th>Documento</th><th>Teléfono</th><th>Email</th></tr></thead><tbody>
        ${patients.map((p) => `<tr><td>${p.full_name}</td><td>${p.document_id}</td><td>${p.phone || "—"}</td><td>${p.email || "—"}</td></tr>`).join("")}
      </tbody></table>`
      : empty("Sin pacientes");
  } catch (e) {
    toast(e.message, "error");
  }
}

loadDashboard();
