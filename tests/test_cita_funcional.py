from app.funcional.cita import aplicar_a_varias, calcular_fin_cita


def test_p01_fin_normal():
    assert calcular_fin_cita(540, 30)["fin"] == 570
    assert calcular_fin_cita(540, 30)["aceptada"] is True


def test_p02_duracion_negativa():
    resultado = calcular_fin_cita(540, -15)
    assert resultado["aceptada"] is False
    assert resultado["fin"] is None


def test_p03_duracion_cero():
    assert calcular_fin_cita(540, 0)["aceptada"] is False


def test_p04_duracion_minima():
    resultado = calcular_fin_cita(540, 5)
    assert resultado["aceptada"] is True
    assert resultado["fin"] == 545


def test_p05_duracion_maxima():
    resultado = calcular_fin_cita(600, 240)
    assert resultado["aceptada"] is True
    assert resultado["fin"] == 840


def test_p06_duracion_demasiado_larga():
    assert calcular_fin_cita(600, 241)["aceptada"] is False


def test_p07_duracion_vacia():
    assert calcular_fin_cita(540, None)["aceptada"] is False


def test_p08_inicio_medianoche():
    resultado = calcular_fin_cita(0, 30)
    assert resultado["aceptada"] is True
    assert resultado["fin"] == 30


def test_p09_cita_que_se_sale_del_dia():
    assert calcular_fin_cita(1420, 30)["aceptada"] is False


def test_p10_no_cambia_los_datos_originales():
    originales = [{"inicio": 540, "duracion": 30}, {"inicio": 540, "duracion": -15}]
    copia = [dict(item) for item in originales]
    aplicar_a_varias(originales)
    assert originales == copia


def test_p11_varias_citas_a_la_vez():
    citas = [{"inicio": 540, "duracion": 30}, {"inicio": 600, "duracion": 20}]
    resultados = aplicar_a_varias(citas)
    assert [item["fin"] for item in resultados] == [570, 620]


def test_p12_inicio_invalido():
    assert calcular_fin_cita(-10, 30)["aceptada"] is False
