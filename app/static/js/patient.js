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
    const appts = await api(`/appointments?patient_id=${PATIENT_ID}`);
    const scheduled = appts.filter((a) => a.status === "scheduled");
    const pendingPay = scheduled.filter((a) => a.payment && a.payment.status === "pending").length;
    document.getElementById("pat-stat-appts").textContent = scheduled.length;
    document.getElementById("pat-stat-pending").textContent = pendingPay;
    const upcoming = scheduled.filter((a) => new Date(a.starts_at) >= new Date()).slice(0, 8);
    document.getElementById("patient-upcoming").innerHTML = upcoming.length
      ? `<table><thead><tr><th>Fecha</th><th>Doctor</th><th>Estado</th><th>Pago</th></tr></thead><tbody>
        ${upcoming.map((a) => `<tr><td>${fmtDateTime(a.starts_at)}</td><td>${a.doctor_name || "—"}</td><td>${badge(a.status)}</td><td>${a.payment ? badge(a.payment.status) : "—"}</td></tr>`).join("")}
      </tbody></table>`
      : empty("No tiene citas próximas. Use Agendar para reservar.");
  } catch (e) {
    toast(e.message, "error");
  }
}

async function loadBook() {
  try {
    const doctors = await api("/doctors");
    const active = doctors.filter((d) => d.is_active);
    const sel = document.getElementById("pat-doctor");
    sel.innerHTML = active.map((d) => `<option value="${d.id}">${d.full_name} — ${d.specialty}</option>`).join("");
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
      ? slots.map((s) => `<option value="${s.starts_at}">${fmtTime(s.starts_at)} – ${fmtTime(s.ends_at)}</option>`).join("")
      : '<option value="">Sin horarios disponibles</option>';
  } catch (e) {
    slotSel.innerHTML = '<option value="">Error al cargar slots</option>';
  }
}

document.getElementById("pat-doctor")?.addEventListener("change", refreshSlots);
document.getElementById("pat-date")?.addEventListener("change", refreshSlots);

document.getElementById("patient-book-form")?.addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!PATIENT_ID) return toast("Paciente no vinculado", "error");
  const starts_at = document.getElementById("pat-slot").value;
  if (!starts_at) return toast("Seleccione un horario", "error");
  try {
    await api("/appointments", {
      method: "POST",
      body: JSON.stringify({
        doctor_id: Number(document.getElementById("pat-doctor").value),
        patient_id: PATIENT_ID,
        starts_at,
        notes: document.getElementById("pat-notes").value || null,
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
    const appts = await api(`/appointments?patient_id=${PATIENT_ID}`);
    document.getElementById("patient-appointments").innerHTML = appts.length
      ? `<table><thead><tr><th>Fecha</th><th>Doctor</th><th>Estado</th><th>Notas</th></tr></thead><tbody>
        ${appts.map((a) => `<tr><td>${fmtDateTime(a.starts_at)}</td><td>${a.doctor_name || "—"}</td><td>${badge(a.status)}</td><td>${a.notes || "—"}</td></tr>`).join("")}
      </tbody></table>`
      : empty("Aún no tiene citas");
  } catch (e) {
    toast(e.message, "error");
  }
}

async function loadPayments() {
  if (!PATIENT_ID) return;
  try {
    const appts = await api(`/appointments?patient_id=${PATIENT_ID}`);
    const rows = appts.filter((a) => a.payment).map((a) => ({ ...a.payment, when: a.starts_at, doctor: a.doctor_name }));
    document.getElementById("patient-payments").innerHTML = rows.length
      ? `<table><thead><tr><th>Cita</th><th>Doctor</th><th>Monto</th><th>Estado</th></tr></thead><tbody>
        ${rows.map((p) => `<tr><td>${fmtDateTime(p.when)}</td><td>${p.doctor || "—"}</td><td>$${Number(p.amount).toFixed(2)}</td><td>${badge(p.status)}</td></tr>`).join("")}
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
        <div><dt>Nombre</dt><dd>${p.full_name}</dd></div>
        <div><dt>Documento</dt><dd>${p.document_id}</dd></div>
        <div><dt>Teléfono</dt><dd>${p.phone || "—"}</dd></div>
        <div><dt>Email</dt><dd>${p.email || "—"}</dd></div>
        <div><dt>Rol</dt><dd>${USER.role_label || "Paciente"}</dd></div>
      </dl>`;
  } catch (e) {
    toast(e.message, "error");
  }
}

loadDashboard();
