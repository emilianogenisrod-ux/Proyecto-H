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
    const upcoming = sortByInicioAsc(appts.filter(esCitaProxima));
    const pendingPay = upcoming.filter((a) => a.pago && a.pago.estado === "pending").length;
    document.getElementById("pat-stat-appts").textContent = upcoming.length;
    document.getElementById("pat-stat-pending").textContent = pendingPay;
    document.getElementById("patient-upcoming").innerHTML = upcoming.length
      ? `<table><thead><tr><th>Fecha</th><th>Doctor</th><th>Estado</th><th>Pago</th></tr></thead><tbody>
        ${upcoming
          .slice(0, 8)
          .map(
            (a) =>
              `<tr><td>${fmtDateTime(a.inicio)}</td><td>${a.nombre_doctor || "—"}</td><td>${badge(a.estado)}</td><td>${a.pago ? badge(a.pago.estado) : "—"}</td></tr>`
          )
          .join("")}
      </tbody></table>`
      : empty("No tiene citas próximas sin cobrar. Use Agendar para reservar.");
  } catch (e) {
    toast(e.message, "error");
  }
}

let _patDoctors = [];
let _pendingPatReschedule = null;

function fillPatientDoctors() {
  const specialty = document.getElementById("pat-specialty")?.value || "";
  const sel = document.getElementById("pat-doctor");
  if (!sel) return;
  let list = _patDoctors.filter(
    (d) => d.activo && (!specialty || d.especialidad === specialty)
  );
  if (specialty === "Ginecología") {
    list = list.filter((d) => d.sexo === "F");
  }
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
    bindAgendaDateInput(date);
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

function appointmentActions(a) {
  if (esCitaPagada(a)) return "<small>Pagada</small>";
  if (a.estado === "scheduled") {
    return `
      <button class="btn btn-sm btn-primary" type="button" onclick="patMarkOutcome(${a.id}, 'completed')">Sí se hizo</button>
      <button class="btn btn-sm btn-ghost" type="button" onclick="patMarkOutcome(${a.id}, 'patient_late')">Llegué tarde</button>
      <button class="btn btn-sm btn-ghost" type="button" onclick="patMarkOutcome(${a.id}, 'doctor_absent')">Doctor no llegó</button>
    `;
  }
  if (a.estado === "no_show") {
    return `<button class="btn btn-sm btn-primary" type="button" onclick="patOpenReschedule(${a.id})">Reagendar cita</button>`;
  }
  if (a.estado === "doctor_absent") {
    return `<button class="btn btn-sm btn-primary" type="button" onclick="patOpenReschedule(${a.id})">Reagendar con otro doctor</button>`;
  }
  return "—";
}

function renderPatientApptTable(list, emptyMsg) {
  if (!list.length) return empty(emptyMsg);
  return `<table><thead><tr><th>Fecha</th><th>Doctor</th><th>Estado</th><th>Pago</th><th>Notas</th><th>Acciones</th></tr></thead><tbody>
    ${list
      .map(
        (a) => `<tr>
      <td>${fmtDateTime(a.inicio)}</td>
      <td>${a.nombre_doctor || "—"}</td>
      <td>${badge(a.estado)}</td>
      <td>${a.pago ? badge(a.pago.estado) : "—"}</td>
      <td>${a.notas || "—"}</td>
      <td class="actions">${appointmentActions(a)}</td>
    </tr>`
      )
      .join("")}
  </tbody></table>`;
}

async function loadAppointments() {
  if (!PATIENT_ID) return;
  try {
    if (!_patDoctors.length) {
      const doctors = await api("/doctors", { silent: true });
      _patDoctors = doctors.filter((d) => d.activo);
    }
    const appts = await api(`/appointments?paciente_id=${PATIENT_ID}`);
    const upcoming = sortByInicioAsc(appts.filter(esCitaProxima));
    const history = sortByInicioDesc(appts.filter(esCitaHistorial));
    const up = document.getElementById("patient-appointments-upcoming");
    const hist = document.getElementById("patient-appointments-history");
    if (up) up.innerHTML = renderPatientApptTable(upcoming, "No tiene citas próximas sin cobrar");
    if (hist) hist.innerHTML = renderPatientApptTable(history, "Sin historial aún");
  } catch (e) {
    toast(e.message, "error");
  }
}

window.patMarkOutcome = async (id, resultado) => {
  const msgs = {
    completed: "¿Confirmas que la consulta sí se realizó?",
    patient_late: "¿Confirmas que llegaste tarde y quieres poder reagendar?",
    doctor_absent: "¿Confirmas que el doctor no llegó?",
  };
  if (!confirm(msgs[resultado] || "¿Confirmar?")) return;
  try {
    await api(`/appointments/${id}/outcome`, {
      method: "POST",
      body: JSON.stringify({ resultado }),
    });
    toast("Estado de la cita actualizado");
    loadAppointments();
    loadDashboard();
  } catch (e) {
    toast(e.message, "error");
  }
};

async function loadPatRescheduleSlots() {
  const doctorId = document.getElementById("pat-reschedule-doctor").value;
  const day = document.getElementById("pat-reschedule-date").value;
  const slotSel = document.getElementById("pat-reschedule-slot");
  if (!doctorId || !day || !_pendingPatReschedule) {
    slotSel.innerHTML = '<option value="">Seleccione doctor y fecha</option>';
    return;
  }
  try {
    const slots = await api(
      `/doctors/${doctorId}/slots?day=${day}&excluir_cita_id=${_pendingPatReschedule.id}`,
      { silent: true }
    );
    slotSel.innerHTML = slots.length
      ? slots
          .map((s) => `<option value="${s.inicio}">${fmtTime(s.inicio)} – ${fmtTime(s.fin)}</option>`)
          .join("")
      : '<option value="">Sin horarios libres</option>';
  } catch (e) {
    slotSel.innerHTML = '<option value="">Error al cargar</option>';
  }
}

window.patOpenReschedule = async (id) => {
  const dlg = document.getElementById("pat-reschedule-dialog");
  if (!dlg) return;
  try {
    const appt = await api(`/appointments/${id}`);
    _pendingPatReschedule = appt;
    const especialidad = appt.especialidad_doctor;
    const doctorSel = document.getElementById("pat-reschedule-doctor");
    const wrap = document.getElementById("pat-reschedule-doctor-wrap");
    const dateInput = document.getElementById("pat-reschedule-date");

    if (appt.estado === "doctor_absent") {
      document.getElementById("pat-reschedule-summary").textContent =
        `Doctor ausente: ${appt.nombre_doctor}. Elige otro de ${especialidad || "la misma especialidad"}.`;
      wrap.style.display = "";
      let list = _patDoctors.filter(
        (d) => d.activo && d.id !== appt.doctor_id && (!especialidad || d.especialidad === especialidad)
      );
      if (especialidad === "Ginecología") list = list.filter((d) => d.sexo === "F");
      doctorSel.innerHTML = list.length
        ? list.map((d) => `<option value="${d.id}">${d.nombre_completo}</option>`).join("")
        : '<option value="">No hay otro doctor disponible</option>';
      doctorSel.required = true;
    } else {
      document.getElementById("pat-reschedule-summary").textContent =
        `Llegaste tarde a la cita con ${appt.nombre_doctor}. Elige un nuevo horario.`;
      wrap.style.display = "none";
      doctorSel.innerHTML = `<option value="${appt.doctor_id}">${appt.nombre_doctor}</option>`;
      doctorSel.required = false;
    }

    bindAgendaDateInput(dateInput);
    dateInput.value = todayISO();
    await loadPatRescheduleSlots();
    dlg.showModal();
  } catch (e) {
    toast(e.message, "error");
  }
};

document.getElementById("pat-reschedule-doctor")?.addEventListener("change", loadPatRescheduleSlots);
document.getElementById("pat-reschedule-date")?.addEventListener("change", loadPatRescheduleSlots);

document.getElementById("pat-reschedule-form")?.addEventListener("submit", async (ev) => {
  const submitter = ev.submitter;
  if (!submitter || submitter.value !== "save") {
    _pendingPatReschedule = null;
    return;
  }
  ev.preventDefault();
  if (!_pendingPatReschedule) return;
  const inicio = document.getElementById("pat-reschedule-slot").value;
  const doctorId = Number(document.getElementById("pat-reschedule-doctor").value);
  if (!inicio || !doctorId) return toast("Elige doctor y horario", "error");
  const body = { inicio };
  if (_pendingPatReschedule.estado === "doctor_absent") {
    body.doctor_id = doctorId;
  }
  try {
    await api(`/appointments/${_pendingPatReschedule.id}/reschedule`, {
      method: "POST",
      body: JSON.stringify(body),
    });
    document.getElementById("pat-reschedule-dialog").close();
    _pendingPatReschedule = null;
    toast("Cita reagendada");
    loadAppointments();
    loadDashboard();
  } catch (e) {
    toast(e.message, "error");
  }
});

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
        <div><dt>Sexo</dt><dd>${p.sexo === "F" ? "Mujer" : p.sexo === "M" ? "Hombre" : "—"}</dd></div>
        <div><dt>Teléfono</dt><dd>${p.telefono || "—"}</dd></div>
        <div><dt>Email</dt><dd>${p.correo || "—"}</dd></div>
        <div><dt>Rol</dt><dd>${USER.role_label || "Paciente"}</dd></div>
      </dl>`;
  } catch (e) {
    toast(e.message, "error");
  }
}

loadDashboard();
