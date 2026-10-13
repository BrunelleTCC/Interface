import streamlit as st
import pandas as pd

def calcular_tarifas(ano):

    tarifas_2024 = {
        "tarifa_scee": 0.58982364,
        "tarifa_gd": 0.515534,
        "tarifa_fio_b": 0.85880364,
        "tarifa_disponibilidade": 1.08060412
    }

    reajustes = {
        2025: 0.0736,
        2026: 0.0650,
        2027: 0.0650,
        2028: 0.0650
    }

    if ano == 2023:
        fator = 1 / 1.1327

    elif ano == 2024:
        fator = 1

    else:
        fator = 1
        for ano_reajuste in range(2025, ano + 1):
            fator *= (1 + reajustes[ano_reajuste])

    tarifas = {}

    # Demais tarifas continuam aumentando com os reajustes
    tarifas["tarifa_scee"] = tarifas_2024["tarifa_scee"] * fator
    tarifas["tarifa_fio_b"] = tarifas_2024["tarifa_fio_b"] * fator
    tarifas["tarifa_disponibilidade"] = tarifas_2024["tarifa_disponibilidade"] * fator

    # TARIFA GD II
    if ano == 2023:
        tarifa_gd = 1 - (tarifas_2024["tarifa_gd"] / 1.1327)


    elif ano == 2024:
        tarifa_gd = tarifas_2024["tarifa_gd"]

    else:
        tarifa_gd = tarifas_2024["tarifa_gd"]

        for ano_reajuste in range(2025, ano + 1):
            tarifa_gd *= (1 - reajustes[ano_reajuste])

    tarifas["tarifa_gd"] = tarifa_gd

    return tarifas
def calcular_gd2(
    consumo_kwh,
    injetado_kwh,
    ano,
    custo_disponibilidade_kwh,
    saldo_credito_kwh
):

    tarifas = calcular_tarifas(ano)

    tarifa_scee = tarifas["tarifa_scee"]
    tarifa_gd = tarifas["tarifa_gd"]
    tarifa_fio_b = tarifas["tarifa_fio_b"]
    tarifa_disponibilidade = tarifas["tarifa_disponibilidade"]


    energia_eletrica = custo_disponibilidade_kwh * tarifa_disponibilidade
    energia_scee = (consumo_kwh - custo_disponibilidade_kwh) * tarifa_scee
    energia_compensada = (consumo_kwh - custo_disponibilidade_kwh) * tarifa_gd
    fio_b_kwh = int((energia_scee - energia_compensada)/ tarifa_fio_b)
    fio_b = fio_b_kwh * tarifa_fio_b
    credito = (saldo_credito_kwh + (injetado_kwh - (consumo_kwh - custo_disponibilidade_kwh) - fio_b_kwh))
    valor_fatura = (energia_eletrica + energia_scee - energia_compensada - fio_b)

    return {
        "energia_eletrica": energia_eletrica,
        "energia_scee": energia_scee,
        "energia_compensada": energia_compensada,
        "fio_b_kwh": fio_b_kwh,
        "fio_b": fio_b,
        "credito": credito,
        "valor_fatura": valor_fatura,

        "tarifa_scee": tarifa_scee,
        "tarifa_gd": tarifa_gd,
        "tarifa_fio_b": tarifa_fio_b,
        "tarifa_disponibilidade": tarifa_disponibilidade
    }


st.title(
    "Simulador de Compensação de Energia "
    "na Geração Distribuída"
)

st.caption(
    "Baseado na Lei 14.300/2022 e Resoluções da ANEEL"
)

tipo_instalacao = st.selectbox(
    "Tipo de instalação",
    [
        "Monofásica",
        "Bifásica",
        "Trifásica"
    ]
)


meses = [
    "Mês 1",
    "Mês 2",
    "Mês 3",
    "Mês 4",
    "Mês 5",
    "Mês 6"
]

st.subheader(
    "Preencha os dados dos últimos 6 meses"
)

df = pd.DataFrame({
    "Período": meses,
    "Ano": [2024] * 6,
    "Consumo (kWh)": [288] * 6,
    "Injetado (kWh)": [304] * 6
})


df_editado = st.data_editor(
    df,
    num_rows="fixed",
    width="stretch",
    hide_index=True,

    column_config={

        "Ano": st.column_config.NumberColumn(
            format="%d",
            min_value=2023,
            max_value=2028,
            step=1
        ),

        "Consumo (kWh)": st.column_config.NumberColumn(
            format="%.2f"
        ),

        "Injetado (kWh)": st.column_config.NumberColumn(
            format="%.2f"
        )
    }
)

saldo_inicial = st.number_input(
    "Saldo de crédito inicial (kWh)",
    min_value=0.0,
    value=0.0,
    step=1.0
)

if st.button("Calcular"):

    if tipo_instalacao == "Monofásica":
        custo_disponibilidade_kwh = 30

    elif tipo_instalacao == "Bifásica":
        custo_disponibilidade_kwh = 50

    else:
        custo_disponibilidade_kwh = 100

    saldo_credito_kwh = saldo_inicial

    detalhamento_lista = []

    producao_insuficiente = False

    for i in range(6):
        consumo = float(
            df_editado.loc[i, "Consumo (kWh)"]
        )
        injetado = float(
            df_editado.loc[i, "Injetado (kWh)"]
        )
        ano_mes = int(
            df_editado.loc[i, "Ano"]
        )
        resultado = calcular_gd2(
            consumo_kwh=consumo,
            injetado_kwh=injetado,
            ano=ano_mes,
            custo_disponibilidade_kwh=custo_disponibilidade_kwh,
            saldo_credito_kwh=saldo_credito_kwh
        )

        saldo_credito_kwh = resultado["credito"]

        detalhamento_lista.append({
            "Mês": meses[i],
            "Ano": ano_mes,
            "Tarifa SCEE":
                resultado["tarifa_scee"],
            "Tarifa GD":
                resultado["tarifa_gd"],
            "Tarifa Fio B":
                resultado["tarifa_fio_b"],
            "Tarifa disponibilidade":
                resultado["tarifa_disponibilidade"],
            "Energia elétrica (R$)":
                resultado["energia_eletrica"],
            "Energia SCEE (R$)":
                resultado["energia_scee"],
            "Energia compensada (R$)":
                resultado["energia_compensada"],
            "Fio B (R$)":
                resultado["fio_b"],
            "Crédito usado Fio B (kWh)":
                resultado["fio_b_kwh"],
            "Crédito (kWh)":
                resultado["credito"],
            "Valor final (R$)":
                resultado["valor_fatura"]
        })

    df_resultado = pd.DataFrame(
        detalhamento_lista
    )


    st.subheader("Resultado mensal")

    st.dataframe(
        df_resultado,
        hide_index=True
    )