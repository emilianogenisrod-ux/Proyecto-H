const USER = getBootUser() || {};
const PATIENT_ID = USER.patient_id;

const loaders = {
  dashboard: loadDashboard,
  book: loadBook,
  appointments: loadAppointments,
  payments: loadPayments,
  profile: loadProfile,
};

bindRoleNavigation(loaders);

async function loadDashboard() {
  if (!PATIENT_ID) {
    document.getElementById("patient-upcoming").innerHTML = empty("Cuenta de paciente no vinculada.");
    return;
  }
  try {
    const appts = await api(`/appointments?paciente_id=${PATIENT_ID}`);
    const scheduled = appts.filter((a) => a.estado === "scheduled");
    const pendingPay = scheduled.filter((a) => a.pago && a.pago.estado === "pending").length;
    document.getElementById("pat-stat-appts").textContent = scheduled.length;
    document.getElementById("pat-stat-pending").textContent = pendingPay;
    const upcoming = scheduled.filter((a) => new Date(a.inicio) >= new Date()).slice(0, 8);
    document.getElementById("patient-upcoming").innerHTML = upcoming.length
      ? `<table><thead><tr><th>Fecha</th><th>Doctor</th><th>Estado</th><th>Pago</th></tr></thead><tbody>
        ${upcoming.map((a) => `<tr><td>${fmtDateTime(a.inicio)}</td><td>${a.nombre_doctor || "—"}</td><td>${badge(a.estado)}</td><td>${a.pago ? badge(a.pago.status) : "—"}</td></tr>`).join("")}
      </tbody></table>`
      : empty("No tiene citas próximas. Use Agendar para reservar.");
  } catch (e) {
    toast(e.message, "error");
  }
}

let _patDoctors = [];

function fillPatientDoctors() {
  const specialty = document.getElementById("pat-specialty")?.value || "";
  const sel = document.getElementById("pat-doctor");
  if (!sel) return;
  const list = _patDoctors.filter(
    (d) => d.activo && (!specialty || d.especialidad === specialty)
  );
  if (!specialty) {
    sel.innerHTML = '<option value="">Seleccione especialidad</option>';
    return;
  }
  sel.innerHTML = list.length
    ? list.map((d) => `<option value="${d.id}">${d.nombre_completo}</option>`).join("")
    : '<option value="">Sin doctores en esa especialidad</option>';
}

async function loadBook() {
  try {
    const doctors = await api("/doctors");
    _patDoctors = doctors.filter((d) => d.activo);
    fillPatientDoctors();
    const date = document.getElementById("pat-date");
    if (!date.value) date.value = todayISO();
    await refreshSlots();
  } catch (e) {
    toast(e.message, "error");
  }
}

async function refreshSlots() {
  const doctorId = document.getElementById("pat-doctor").value;
  const day = document.getElementById("pat-date").value;
  const slotSel = document.getElementById("pat-slot");
  if (!doctorId || !day) {
    slotSel.innerHTML = '<option value="">Seleccione doctor y fecha</option>';
    return;
  }
  try {
    const slots = await api(`/doctors/${doctorId}/slots?day=${day}`, { silent: true });
    slotSel.innerHTML = slots.length
      ? slots.map((s) => `<option value="${s.inicio}">${fmtTime(s.inicio)} – ${fmtTime(s.fin)}</option>`).join("")
      : '<option value="">Sin horarios disponibles</option>';
  } catch (e) {
    slotSel.innerHTML = '<option value="">Error al cargar slots</option>';
  }
}

document.getElementById("pat-specialty")?.addEventListener("change", async () => {
  fillPatientDoctors();
  await refreshSlots();
});
document.getElementById("pat-doctor")?.addEventListener("change", refreshSlots);
document.getElementById("pat-date")?.addEventListener("change", refreshSlots);

document.getElementById("patient-book-form")?.addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!PATIENT_ID) return toast("Paciente no vinculado", "error");
  const inicio = document.getElementById("pat-slot").value;
  if (!inicio) return toast("Seleccione un horario", "error");
  try {
    await api("/appointments", {
      method: "POST",
      body: JSON.stringify({
        doctor_id: Number(document.getElementById("pat-doctor").value),
        paciente_id: PATIENT_ID,
        inicio,
        notas: document.getElementById("pat-notes").value || null,
      }),
    });
    toast("Cita agendada correctamente");
    e.target.reset();
    loadDashboard();
  } catch (err) {
    toast(err.message, "error");
  }
});

async function loadAppointments() {
  if (!PATIENT_ID) return;
  try {
    const appts = await api(`/appointments?paciente_id=${PATIENT_ID}`);
    document.getElementById("patient-appointments").innerHTML = appts.length
      ? `<table><thead><tr><th>Fecha</th><th>Doctor</th><th>Estado</th><th>Notas</th></tr></thead><tbody>
        ${appts.map((a) => `<tr><td>${fmtDateTime(a.inicio)}</td><td>${a.nombre_doctor || "—"}</td><td>${badge(a.estado)}</td><td>${a.notes || "—"}</td></tr>`).join("")}
      </tbody></table>`
      : empty("Aún no tiene citas");
  } catch (e) {
    toast(e.message, "error");
  }
}

async function loadPayments() {
  if (!PATIENT_ID) return;
  try {
    const appts = await api(`/appointments?paciente_id=${PATIENT_ID}`);
    const rows = appts.filter((a) => a.pago).map((a) => ({ ...a.pago, when: a.inicio, doctor: a.nombre_doctor }));
    document.getElementById("patient-payments").innerHTML = rows.length
      ? `<table><thead><tr><th>Cita</th><th>Doctor</th><th>Monto</th><th>Estado</th></tr></thead><tbody>
        ${rows.map((p) => `<tr><td>${fmtDateTime(p.when)}</td><td>${p.doctor || "—"}</td><td>$${Number(p.monto).toFixed(2)}</td><td>${badge(p.estado)}</td></tr>`).join("")}
      </tbody></table>`
      : empty("Sin pagos registrados");
  } catch (e) {
    toast(e.message, "error");
  }
}

async function loadProfile() {
  if (!PATIENT_ID) {
    document.getElementById("patient-profile").innerHTML = empty("Sin expediente vinculado");
    return;
  }
  try {
    const p = await api(`/patients/${PATIENT_ID}`);
    document.getElementById("patient-profile").innerHTML = `
      <dl class="profile-grid">
        <div><dt>Nombre</dt><dd>${p.nombre_completo}</dd></div>
        <div><dt>Documento</dt><dd>${p.documento}</dd></div>
        <div><dt>Teléfono</dt><dd>${p.telefono || "—"}</dd></div>
        <div><dt>Email</dt><dd>${p.correo || "—"}</dd></div>
        <div><dt>Rol</dt><dd>${USER.role_label || "Paciente"}</dd></div>
      </dl>`;
  } catch (e) {
    toast(e.message, "error");
  }
}

loadDashboard();
