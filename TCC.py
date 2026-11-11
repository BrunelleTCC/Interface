
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt


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

    fator = 1

    for ano_reajuste in range(2025, ano + 1):
        fator *= (1 + reajustes[ano_reajuste])

    tarifas = {}

    tarifas["tarifa_scee"] = tarifas_2024["tarifa_scee"] * fator
    tarifas["tarifa_fio_b"] = tarifas_2024["tarifa_fio_b"] * fator
    tarifas["tarifa_disponibilidade"] = tarifas_2024["tarifa_disponibilidade"] * fator

    # Tarifa GD II
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

    # Parcela do consumo que pode ser compensada
    energia_compensavel_kwh = max(
        0,
        consumo_kwh - custo_disponibilidade_kwh
    )

    # Custo de disponibilidade
    energia_eletrica = (
        custo_disponibilidade_kwh * tarifa_disponibilidade
    )

    # Valor da energia antes da compensação
    energia_scee = energia_compensavel_kwh * tarifa_scee

    # Créditos disponíveis, considerando saldo positivo ou negativo
    creditos_disponiveis = saldo_credito_kwh + injetado_kwh

    # Compensação principal GD II
    energia_compensada_kwh = min(
        energia_compensavel_kwh,
        max(0, creditos_disponiveis)
    )

    energia_compensada = (
        energia_compensada_kwh * tarifa_gd
    )

    # Créditos restantes após compensação principal
    creditos_restantes = (
        creditos_disponiveis - energia_compensada_kwh
    )

    # Diferença correspondente ao Fio B
    diferenca_fio_b = max(
        0,
        energia_compensada_kwh * (tarifa_scee - tarifa_gd)
    )

    # Quantidade inteira de kWh para compensação adicional
    fio_b_kwh = max(
        0,
        int(diferenca_fio_b / tarifa_fio_b)
    )

    # Compensação adicional limitada aos créditos positivos restantes
    compensacao_adicional_kwh = min(
        fio_b_kwh,
        max(0, creditos_restantes)
    )

    compensacao_adicional = (
        compensacao_adicional_kwh * tarifa_fio_b
    )

    # Fio B devido
    fio_b_devido = diferenca_fio_b

    # Fio B não compensado
    fio_b_nao_compensado = max(
        0,
        fio_b_devido - compensacao_adicional
    )

    # Saldo após as compensações
    saldo_resultante = (
        creditos_restantes - compensacao_adicional_kwh
    )

    # Déficit de energia não compensada
    deficit = max(
        0,
        energia_compensavel_kwh - energia_compensada_kwh
    )

    # Saldo final: permite valores negativos
    credito = saldo_resultante

    # Valor final estimado da fatura
    valor_fatura = (
        energia_eletrica
        + energia_scee
        - energia_compensada
        - compensacao_adicional
    )

    return {
        "energia_eletrica": energia_eletrica,
        "energia_scee": energia_scee,
        "energia_compensada": energia_compensada,
        "energia_compensada_kwh": energia_compensada_kwh,
        "fio_b_kwh": fio_b_kwh,
        "fio_b": fio_b_devido,
        "compensacao_adicional_kwh": compensacao_adicional_kwh,
        "compensacao_adicional": compensacao_adicional,
        "fio_b_nao_compensado": fio_b_nao_compensado,
        "credito": credito,
        "valor_fatura": valor_fatura,
        "deficit": deficit,
        "tarifa_scee": tarifa_scee,
        "tarifa_gd": tarifa_gd,
        "tarifa_fio_b": tarifa_fio_b,
        "tarifa_disponibilidade": tarifa_disponibilidade
    }



# INTERFACE

st.title(
    "Simulador de Compensação de Energia "
    "na Geração Distribuída"
)

st.caption(
    "Baseado na Lei 14.300/2022 e Resoluções da ANEEL"
)

# Botão de informações
with st.popover("ℹ️ Sobre o simulador"):
    st.markdown("""
    O simulador foi desenvolvido para auxiliar na compreensão e na análise
    do faturamento de unidades consumidoras participantes do Sistema de
    Compensação de Energia Elétrica (SCEE), com geração distribuída
    fotovoltaica enquadrada na modalidade GD II.

    A ferramenta pode ser utilizada para diferentes finalidades:

    - **Projeção de créditos de energia:** permite que consumidores que já
      possuem painéis fotovoltaicos estimem a evolução de seus créditos
      e os valores das faturas ao longo dos próximos seis meses.

    - **Análise para instalação de sistemas fotovoltaicos:** possibilita
      simular diferentes valores de consumo e energia injetada, auxiliando
      na compreensão dos possíveis impactos da geração própria sobre
      o faturamento da unidade consumidora.

    - **Finalidade didática:** pode ser utilizada em cursos e atividades
      acadêmicas relacionadas à geração distribuída, permitindo visualizar
      o funcionamento do sistema de compensação e os efeitos da cobrança
      da componente Fio B na modalidade GD II.

    ### Como funciona a compensação de energia?

    O cálculo considera duas etapas distintas:

    **1. Energia compensada GD II**

    Corresponde à energia utilizada para compensar o consumo da unidade
    consumidora, limitada à quantidade de créditos disponíveis. A
    compensação considera a tarifa GD II, conforme os parâmetros adotados
    no simulador.

    **2. Compensação adicional**

    Após a compensação do consumo, caso ainda existam créditos disponíveis,
    uma parcela deles pode ser utilizada adicionalmente para abater o valor
    correspondente à componente Fio B. Essa utilização é apresentada
    separadamente dos créditos utilizados na compensação principal.

    **E quando os créditos são insuficientes?**

    Quando a quantidade de créditos disponíveis não é suficiente para
    compensar toda a energia considerada no cálculo, o simulador limita
    a compensação à quantidade existente. A energia que não puder ser
    compensada permanece como parcela a pagar na fatura e é apresentada
    como déficit de compensação.

    Da mesma forma, se não houver créditos excedentes para realizar a
    compensação adicional, o valor correspondente ao Fio B que não puder
    ser abatido permanece na fatura.

    O déficit de energia não é convertido em saldo negativo de créditos
    para o mês seguinte.

    ### Observações sobre os resultados

    Os valores apresentados são estimativas baseadas nas tarifas e nos
    parâmetros adotados no modelo. O simulador tem finalidade de apoio
    à análise e ao aprendizado, não substituindo o cálculo oficial da
    distribuidora. Outros componentes da fatura, como tributos, bandeiras
    tarifárias e contribuição de iluminação pública, não estão contemplados
    nesta versão.
    """)




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

st.subheader("Preencha os dados dos últimos 6 meses")

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
            min_value=2024,
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

    deficit_final = 0

    historico_creditos = []

    for i in range(6):
        consumo = float(df_editado.loc[i, "Consumo (kWh)"])
        injetado = float(df_editado.loc[i, "Injetado (kWh)"])
        ano_mes = int(df_editado.loc[i, "Ano"])

        resultado = calcular_gd2(
            consumo_kwh=consumo,
            injetado_kwh=injetado,
            ano=ano_mes,
            custo_disponibilidade_kwh=custo_disponibilidade_kwh,
            saldo_credito_kwh=saldo_credito_kwh
        )

        saldo_credito_kwh = resultado["credito"]
        deficit_final = resultado["deficit"]

        # Histórico do saldo de créditos
        historico_creditos.append({
            "Ciclo": f"Ciclo {i + 1}",
            "Saldo de créditos (kWh)": saldo_credito_kwh,
            "Valor da fatura (R$)": resultado["valor_fatura"]
        })

        detalhamento_lista.append({
            "Mês": meses[i],
            "Ano": ano_mes,
            #"Tarifa SCEE": resultado["tarifa_scee"],
            #"Tarifa GD": resultado["tarifa_gd"],
            #"Tarifa Fio B": resultado["tarifa_fio_b"],
            #"Tarifa disponibilidade": resultado["tarifa_disponibilidade"],
            "Energia elétrica (R$)": resultado["energia_eletrica"],
            "Energia SCEE (R$)": resultado["energia_scee"],
            "Energia compensada GD II (R$)": resultado["energia_compensada"],
            #"Energia compensada GD II (kWh)": resultado["energia_compensada_kwh"],
            "Fio B calculado (kWh)": resultado["fio_b_kwh"],
            #"Compensação adicional (kWh)": resultado["compensacao_adicional_kwh"],
            "Compensação adicional (R$)": resultado["compensacao_adicional"],
            #"Fio B não compensado (R$)": resultado["fio_b_nao_compensado"],
            "Créditos disponíveis (kWh)": resultado["credito"],
            #"Déficit (kWh)": resultado["deficit"],
            "Valor final (R$)": resultado["valor_fatura"],
            #"Saldo de créditos (kWh)": resultado["credito"],
        })

    df_resultado = pd.DataFrame(detalhamento_lista)

    st.subheader("Resultado mensal")

    colunas_monetarias = [
        "Tarifa SCEE",
        "Tarifa GD",
        "Tarifa Fio B",
        "Tarifa disponibilidade",
        "Energia elétrica (R$)",
        "Energia SCEE (R$)",
        "Energia compensada GD II (R$)",
        "Compensação adicional (R$)",
        "Fio B não compensado (R$)",
        "Valor final (R$)",
        "Créditos disponíveis (kWh)"
    ]

    formatacao = {
        coluna: "{:.2f}" for coluna in colunas_monetarias
    }

    st.dataframe(
        df_resultado.style.format(formatacao),
        hide_index=True
    )

    # ==========================================
    # INTERPRETAÇÃO AUTOMÁTICA DOS RESULTADOS
    # ==========================================

    st.subheader("Interpretação dos resultados")

    # Valores das faturas dos ciclos simulados
    valores_faturas = [
        item["Valor final (R$)"]
        for item in detalhamento_lista
    ]

    # Indicadores da simulação
    quantidade_ciclos = len(valores_faturas)

    if quantidade_ciclos > 0:

        media_fatura = sum(valores_faturas) / quantidade_ciclos
        maior_fatura = max(valores_faturas)
        menor_fatura = min(valores_faturas)

        # Texto inicial
        st.markdown(
            f"A simulação foi realizada considerando "
            f"{quantidade_ciclos} ciclos de faturamento."
        )

        # Interpretação do saldo final
        if saldo_credito_kwh > 0:

            st.markdown(
                f"A simulação terminou com um saldo positivo de "
                f"**{saldo_credito_kwh:.2f} kWh em créditos de energia**, "
                "indicando que ainda existem créditos disponíveis "
                "para utilização em ciclos posteriores."
            )

        elif saldo_credito_kwh < 0:

            st.markdown(
                f"A simulação terminou com um saldo negativo de "
                f"**{abs(saldo_credito_kwh):.2f} kWh**, "
                "representando um déficit acumulado de energia "
                "conforme o critério adotado no simulador."
            )

        else:

            st.markdown(
                "A simulação terminou sem saldo de créditos ou "
                "déficit acumulado de energia."
            )

        # Interpretação das faturas
        st.markdown(
            f"Durante o período analisado, o valor médio das faturas "
            f"foi de **R$ {media_fatura:.2f}**, com valores entre "
            f"**R$ {menor_fatura:.2f}** e "
            f"**R$ {maior_fatura:.2f}**."
        )

        # Existência de valores a pagar
        ciclos_com_cobranca = sum(
            valor > 0 for valor in valores_faturas
        )

        if ciclos_com_cobranca == quantidade_ciclos:

            st.markdown(
                "Em todos os ciclos simulados permaneceu um valor "
                "a pagar, mesmo com a utilização dos créditos de energia."
            )

        elif ciclos_com_cobranca > 0:

            st.markdown(
                f"Em **{ciclos_com_cobranca} dos {quantidade_ciclos} ciclos** "
                "houve valor positivo de fatura. Nos demais ciclos, "
                "o resultado calculado foi igual ou inferior a zero."
            )

        else:

            st.markdown(
                "Não foram identificados valores positivos de fatura "
                "nos ciclos simulados."
            )

    # ==========================================
    # GRÁFICO DE COMPOSIÇÃO LÍQUIDA DA FATURA
    # ==========================================

    st.subheader("Composição da fatura por ciclo")

    df_composicao = pd.DataFrame(detalhamento_lista)

    ciclos = [
        f"{mes} - {ano}"
        for mes, ano in zip(df_composicao["Mês"], df_composicao["Ano"])
    ]

    # Valores brutos cobrados
    energia_eletrica = df_composicao["Energia elétrica (R$)"].abs()
    energia_scee = df_composicao["Energia SCEE (R$)"].abs()

    # Total das compensações
    compensacoes = (
            df_composicao["Energia compensada GD II (R$)"].abs()
            + df_composicao["Compensação adicional (R$)"].abs()
    )

    # Desconta as compensações primeiro da Energia SCEE
    energia_scee_liquida = (energia_scee - compensacoes).clip(lower=0)

    # Caso as compensações ultrapassem a Energia SCEE,
    # o restante é descontado da Energia elétrica
    compensacao_restante = (compensacoes - energia_scee).clip(lower=0)

    energia_eletrica_liquida = (
            energia_eletrica - compensacao_restante
    ).clip(lower=0)

    # Gráfico de colunas empilhadas
    fig, ax = plt.subplots(figsize=(11, 6))

    ax.bar(
        ciclos,
        energia_eletrica_liquida,
        label="Energia elétrica",
        color="#2196F3"
    )

    ax.bar(
        ciclos,
        energia_scee_liquida,
        bottom=energia_eletrica_liquida,
        label="Energia SCEE",
        color="#FF9800"
    )

    # Identificação do valor final da fatura
    valores_finais = df_composicao["Valor final (R$)"]

    for i, valor in enumerate(valores_finais):
        ax.annotate(
            f"R$ {valor:.2f}",
            (i, max(valor, 0)),
            xytext=(0, 5),
            textcoords="offset points",
            ha="center",
            fontsize=9,
            fontweight="bold"
        )

    # Formatação
    ax.set_title("Composição líquida da fatura por ciclo")
    ax.set_xlabel("Ciclo")
    ax.set_ylabel("Valor (R$)")

    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.3)

    ax.set_ylim(bottom=0)
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()

    st.pyplot(fig)
    plt.close(fig)

    # GRÁFICO DE EVOLUÇÃO DOS CRÉDITOS E DA FATURA

    st.subheader("Evolução dos créditos e do valor da fatura")

    df_creditos = pd.DataFrame(historico_creditos)

    # Criação do gráfico
    fig, ax1 = plt.subplots(figsize=(10, 5))

    ciclos = df_creditos["Ciclo"]

    # Linha dos créditos
    linha_creditos = ax1.plot(
        ciclos,
        df_creditos["Saldo de créditos (kWh)"],
        marker="o",
        markersize=7,
        linewidth=2,
        color="blue",
        label="Saldo de créditos (kWh)"
    )

    ax1.set_xlabel("Ciclo")
    ax1.set_ylabel("Saldo de créditos (kWh)", color="blue")
    ax1.tick_params(axis="y", labelcolor="blue")

    # Ajuste automático do eixo dos créditos
    max_creditos = df_creditos["Saldo de créditos (kWh)"].max()

    min_creditos = df_creditos["Saldo de créditos (kWh)"].min()
    max_creditos = df_creditos["Saldo de créditos (kWh)"].max()

    margem = max(
        (max_creditos - min_creditos) * 0.15,
        5
    )

    ax1.set_ylim(
        min(0, min_creditos - margem),
        max(0, max_creditos + margem)
    )

    # Linha de referência do saldo zero
    ax1.axhline(
        y=0,
        color="gray",
        linestyle="--",
        linewidth=1
    )

    # Valores dos créditos sobre as bolinhas
    for i, valor in enumerate(df_creditos["Saldo de créditos (kWh)"]):
        ax1.annotate(
            f"{valor:.0f} kWh",
            (i, valor),
            textcoords="offset points",
            xytext=(0, 8),
            ha="center",
            fontsize=9,
            color="blue"
        )

    # Criação do segundo eixo para o valor da fatura
    ax2 = ax1.twinx()

    linha_fatura = ax2.plot(
        ciclos,
        df_creditos["Valor da fatura (R$)"],
        marker="o",
        markersize=7,
        linewidth=2,
        color="red",
        label="Valor da fatura (R$)"
    )

    ax2.set_ylabel("Valor da fatura (R$)", color="red")
    ax2.tick_params(axis="y", labelcolor="red")

    # Ajuste automático do eixo da fatura
    max_fatura = df_creditos["Valor da fatura (R$)"].max()

    if max_fatura > 0:
        ax2.set_ylim(0, max_fatura * 1.15)
    else:
        ax2.set_ylim(0, 10)

    # Valores da fatura sobre as bolinhas
    for i, valor in enumerate(df_creditos["Valor da fatura (R$)"]):
        ax2.annotate(
            f"R$ {valor:.2f}",
            (i, valor),
            textcoords="offset points",
            xytext=(0, 8),
            ha="center",
            fontsize=9,
            color="red"
        )

    # Junta as legendas dos dois eixos
    linhas = linha_creditos + linha_fatura

    etiquetas = [
        "Saldo de créditos (kWh)",
        "Valor da fatura (R$)"
    ]

    ax1.legend(
        linhas,
        etiquetas,
        loc="upper center",
        bbox_to_anchor=(0.5, 1.12),
        ncol=2
    )

    # Grade horizontal
    ax1.grid(
        axis="y",
        linestyle="--",
        alpha=0.4
    )

    # Ajuste do gráfico
    fig.tight_layout()

    st.pyplot(fig)
