"""Especialidades permitidas en el hospital (catálogo cerrado)."""

ESPECIALIDADES = (
    "Medicina General",
    "Pediatría",
    "Ginecología",
    "Dermatología",
)

ESPECIALIDADES_SET = set(ESPECIALIDADES)

# Ginecología: doctoras y pacientes mujeres
ESPECIALIDADES_SOLO_MUJERES = {"Ginecología"}


def validar_genero_especialidad(
    especialidad: str,
    *,
    sexo_doctor: str | None = None,
    sexo_paciente: str | None = None,
) -> str | None:
    if especialidad not in ESPECIALIDADES_SOLO_MUJERES:
        return None
    if sexo_doctor is not None and sexo_doctor != "F":
        return "Ginecología solo admite doctoras (sexo F)"
    if sexo_paciente is not None and sexo_paciente != "F":
        return "Ginecología solo admite pacientes mujeres (sexo F)"
    return None
