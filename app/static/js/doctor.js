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
    if (note) note.textContent = `${USER.name}${USER.especialidad ? " · " + USER.especialidad : ""}`;

    const [appts, blocks] = await Promise.all([
      api(`/appointments?doctor_id=${DOCTOR_ID}`),
      api(`/doctors/${DOCTOR_ID}/schedules`),
    ]);
    const today = todayISO();
    const proximas = appts.filter(esCitaProxima);
    const todayCount = proximas.filter((a) => a.inicio.slice(0, 10) === today).length;
    document.getElementById("doc-stat-today").textContent = todayCount;
    document.getElementById("doc-stat-week").textContent = proximas.length;
    document.getElementById("doc-stat-blocks").textContent = blocks.length;

    const upcoming = sortByInicioAsc(proximas).slice(0, 10);
    document.getElementById("doctor-upcoming").innerHTML = upcoming.length
      ? `<table><thead><tr><th>Fecha</th><th>Paciente</th><th>Notas</th><th>Pago</th><th>Estado</th></tr></thead><tbody>
        ${upcoming
          .map(
            (a) =>
              `<tr><td>${fmtDateTime(a.inicio)}</td><td>${a.nombre_paciente || "—"}</td><td>${a.notas || a.notes || "—"}</td><td>${a.pago ? badge(a.pago.estado) : "—"}</td><td>${badge(a.estado)}</td></tr>`
          )
          .join("")}
      </tbody></table>`
      : empty("No tiene citas próximas sin cobrar");
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

window.docMarkOutcome = async (id, resultado) => {
  const msgs = {
    completed: "¿Marcar consulta como realizada?",
    patient_late: "¿Registrar que el paciente llegó tarde?",
    doctor_absent: "¿Registrar que usted no pudo atender?",
  };
  if (!confirm(msgs[resultado] || "¿Confirmar?")) return;
  try {
    await api(`/appointments/${id}/outcome`, {
      method: "POST",
      body: JSON.stringify({ resultado }),
    });
    toast("Estado actualizado");
    loadAppointments();
    loadDashboard();
  } catch (e) {
    toast(e.message, "error");
  }
};

function docApptActions(a) {
  if (esCitaPagada(a)) return "<small>Pagada</small>";
  if (a.estado === "scheduled") {
    return `<button class="btn btn-sm btn-primary" onclick="docMarkOutcome(${a.id}, 'completed')">Realizada</button>
      <button class="btn btn-sm btn-ghost" onclick="docMarkOutcome(${a.id}, 'patient_late')">Paciente tarde</button>
      <button class="btn btn-sm btn-ghost" onclick="docMarkOutcome(${a.id}, 'doctor_absent')">No pude atender</button>`;
  }
  return "—";
}

function renderDoctorApptTable(list, emptyMsg) {
  if (!list.length) return empty(emptyMsg);
  return `<table><thead><tr><th>Fecha</th><th>Paciente</th><th>Estado</th><th>Pago</th><th>Acciones</th></tr></thead><tbody>
    ${list
      .map(
        (a) => `<tr>
      <td>${fmtDateTime(a.inicio)}</td>
      <td>${a.nombre_paciente || "—"}</td>
      <td>${badge(a.estado)}</td>
      <td>${a.pago ? badge(a.pago.estado) : "—"}</td>
      <td class="actions">${docApptActions(a)}</td>
    </tr>`
      )
      .join("")}
  </tbody></table>`;
}

async function loadAppointments() {
  if (!DOCTOR_ID) return;
  try {
    const appts = await api(`/appointments?doctor_id=${DOCTOR_ID}`);
    const upcoming = sortByInicioAsc(appts.filter(esCitaProxima));
    const history = sortByInicioDesc(appts.filter(esCitaHistorial));
    const up = document.getElementById("doctor-appointments-upcoming");
    const hist = document.getElementById("doctor-appointments-history");
    if (up) up.innerHTML = renderDoctorApptTable(upcoming, "No hay citas próximas sin cobrar");
    if (hist) hist.innerHTML = renderDoctorApptTable(history, "Sin historial aún");
  } catch (e) {
    toast(e.message, "error");
  }
}

async function loadPatients() {
  try {
    const patients = await api("/patients");
    document.getElementById("doctor-patients").innerHTML = patients.length
      ? `<table><thead><tr><th>Nombre</th><th>Documento</th><th>Teléfono</th><th>Email</th></tr></thead><tbody>
        ${patients.map((p) => `<tr><td>${p.nombre_completo}</td><td>${p.documento}</td><td>${p.telefono || "—"}</td><td>${p.correo || "—"}</td></tr>`).join("")}
      </tbody></table>`
      : empty("Sin pacientes");
  } catch (e) {
    toast(e.message, "error");
  }
}

loadDashboard();
