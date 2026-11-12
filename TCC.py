import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt


# ==========================================================
# CÁLCULO DAS TARIFAS
# ==========================================================

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
    tarifas["tarifa_disponibilidade"] = (
        tarifas_2024["tarifa_disponibilidade"] * fator
    )

    # Tarifa GD II
    tarifa_gd = tarifas_2024["tarifa_gd"]

    for ano_reajuste in range(2025, ano + 1):
        tarifa_gd *= (1 - reajustes[ano_reajuste])

    tarifas["tarifa_gd"] = tarifa_gd

    return tarifas


# ==========================================================
# CÁLCULO GD II
# ==========================================================

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
    energia_scee = (
        energia_compensavel_kwh * tarifa_scee
    )

    # Créditos disponíveis
    creditos_disponiveis = (
        saldo_credito_kwh + injetado_kwh
    )

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
        creditos_disponiveis
        - energia_compensada_kwh
    )

    # Diferença correspondente ao Fio B
    diferenca_fio_b = max(
        0,
        energia_compensada_kwh
        * (tarifa_scee - tarifa_gd)
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
        creditos_restantes
        - compensacao_adicional_kwh
    )

    # Déficit de energia não compensada
    deficit = max(
        0,
        energia_compensavel_kwh
        - energia_compensada_kwh
    )

    # Saldo final
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
        "compensacao_adicional_kwh": (
            compensacao_adicional_kwh
        ),
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


# ==========================================================
# CÁLCULO GD I
# ==========================================================

def calcular_gd1(
    consumo_kwh,
    injetado_kwh,
    ano,
    custo_disponibilidade_kwh,
    saldo_credito_kwh
):

    tarifas = calcular_tarifas(ano)

    tarifa_disponibilidade = (
        tarifas["tarifa_disponibilidade"]
    )

    # Custo de disponibilidade
    energia_eletrica = (
        custo_disponibilidade_kwh
        * tarifa_disponibilidade
    )

    # Verifica a diferença entre energia injetada
    # e consumo do ciclo
    saldo_antes = (
        saldo_credito_kwh
        + injetado_kwh
        - consumo_kwh
    )

    # Se houver excedente, ele é acumulado.
    # Se o consumo superar os créditos disponíveis,
    # o saldo fica zerado.
    credito = max(0, saldo_antes)

    # Quantidade de energia que não pôde ser
    # compensada com os créditos disponíveis
    deficit = max(0, -saldo_antes)

    # Na GD I, conforme o critério adotado no simulador,
    # a fatura considera somente o custo de disponibilidade.
    valor_fatura = energia_eletrica

    return {
        "energia_eletrica": energia_eletrica,
        "energia_scee": 0,
        "energia_compensada": 0,
        "energia_compensada_kwh": 0,
        "fio_b_kwh": 0,
        "fio_b": 0,
        "compensacao_adicional_kwh": 0,
        "compensacao_adicional": 0,
        "fio_b_nao_compensado": 0,
        "credito": credito,
        "valor_fatura": valor_fatura,
        "deficit": deficit,
        "tarifa_scee": tarifas["tarifa_scee"],
        "tarifa_gd": tarifas["tarifa_gd"],
        "tarifa_fio_b": tarifas["tarifa_fio_b"],
        "tarifa_disponibilidade": (
            tarifa_disponibilidade
        )
    }


# ==========================================================
# INTERFACE
# ==========================================================

st.title(
    "Simulador de Compensação de Energia "
    "na Geração Distribuída"
)

st.caption(
    "Baseado na Lei 14.300/2022 e Resoluções da ANEEL"
)


# ==========================================================
# INFORMAÇÕES
# ==========================================================

with st.popover("ℹ️ Sobre o simulador"):

    st.markdown("""
    O simulador foi desenvolvido para auxiliar na compreensão
    e na análise do faturamento de unidades consumidoras
    participantes do Sistema de Compensação de Energia Elétrica
    (SCEE), permitindo a simulação de diferentes condições
    de geração distribuída.

    A ferramenta permite selecionar entre as modalidades
    **GD I** e **GD II**.

    ### GD I

    Na modalidade GD I, o simulador considera o acúmulo dos
    excedentes de energia ao longo dos ciclos simulados.

    Quando a energia injetada é superior ao consumo, o excedente
    é incorporado ao saldo de créditos.

    Quando o consumo é superior à energia injetada, os créditos
    acumulados anteriormente são utilizados para compensar
    essa diferença.

    Para fins do modelo desenvolvido, o valor da fatura na
    GD I considera somente o custo de disponibilidade.

    ### GD II

    Na modalidade GD II, o cálculo considera a compensação
    da energia conforme os parâmetros tarifários adotados
    no modelo, incluindo a componente Fio B.

    O cálculo considera duas etapas distintas:

    **1. Energia compensada GD II**

    Corresponde à energia utilizada para compensar o consumo
    da unidade consumidora, limitada à quantidade de créditos
    disponíveis.

    **2. Compensação adicional**

    Após a compensação do consumo, caso ainda existam créditos
    disponíveis, uma parcela deles pode ser utilizada
    adicionalmente para abater o valor correspondente
    à componente Fio B.

    ### E quando os créditos são insuficientes?

    Quando a quantidade de créditos disponíveis não é suficiente
    para compensar toda a energia considerada no cálculo,
    o simulador limita a compensação à quantidade existente.

    A energia que não puder ser compensada permanece como
    déficit de compensação no ciclo.

    ### Observações sobre os resultados

    Os valores apresentados são estimativas baseadas nas tarifas
    e nos parâmetros adotados no modelo.

    O simulador tem finalidade de apoio à análise e ao aprendizado,
    não substituindo o cálculo oficial da distribuidora.

    Outros componentes da fatura, como tributos, bandeiras
    tarifárias e contribuição de iluminação pública, não estão
    contemplados nesta versão.
    """)


# ==========================================================
# ESCOLHA DA MODALIDADE
# ==========================================================

modalidade = st.selectbox(
    "Modalidade de geração distribuída",
    [
        "GD I",
        "GD II"
    ]
)


# ==========================================================
# TIPO DE INSTALAÇÃO
# ==========================================================

tipo_instalacao = st.selectbox(
    "Tipo de instalação",
    [
        "Monofásica",
        "Bifásica",
        "Trifásica"
    ]
)


# ==========================================================
# ENTRADA DOS DADOS
# ==========================================================

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


# ==========================================================
# SALDO INICIAL
# ==========================================================

saldo_inicial = st.number_input(
    "Saldo de crédito inicial (kWh)",
    min_value=0.0,
    value=0.0,
    step=1.0
)


# ==========================================================
# BOTÃO CALCULAR
# ==========================================================

if st.button("Calcular"):

    # Define o custo de disponibilidade
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


    # ======================================================
    # CÁLCULO DOS 6 CICLOS
    # ======================================================

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


        # --------------------------------------------------
        # GD I
        # --------------------------------------------------

        if modalidade == "GD I":

            resultado = calcular_gd1(
                consumo_kwh=consumo,
                injetado_kwh=injetado,
                ano=ano_mes,
                custo_disponibilidade_kwh=(
                    custo_disponibilidade_kwh
                ),
                saldo_credito_kwh=saldo_credito_kwh
            )


        # --------------------------------------------------
        # GD II
        # --------------------------------------------------

        else:

            resultado = calcular_gd2(
                consumo_kwh=consumo,
                injetado_kwh=injetado,
                ano=ano_mes,
                custo_disponibilidade_kwh=(
                    custo_disponibilidade_kwh
                ),
                saldo_credito_kwh=saldo_credito_kwh
            )


        # Atualiza o saldo
        saldo_credito_kwh = resultado["credito"]

        deficit_final = resultado["deficit"]


        # ==================================================
        # HISTÓRICO DOS CRÉDITOS
        # ==================================================

        historico_creditos.append({

            "Ciclo": f"Ciclo {i + 1}",

            "Saldo de créditos (kWh)": (
                saldo_credito_kwh
            ),

            "Valor da fatura (R$)": (
                resultado["valor_fatura"]
            )
        })


        # ==================================================
        # DETALHAMENTO
        # ==================================================

        detalhamento_lista.append({

            "Mês": meses[i],

            "Ano": ano_mes,

            "Energia elétrica (R$)": (
                resultado["energia_eletrica"]
            ),

            "Energia SCEE (R$)": (
                resultado["energia_scee"]
            ),

            "Energia compensada GD II (R$)": (
                resultado["energia_compensada"]
            ),

            "Fio B calculado (kWh)": (
                resultado["fio_b_kwh"]
            ),

            "Compensação adicional (R$)": (
                resultado["compensacao_adicional"]
            ),

            "Créditos disponíveis (kWh)": (
                resultado["credito"]
            ),

            "Valor final (R$)": (
                resultado["valor_fatura"]
            )
        })


    # ======================================================
    # DATAFRAME DE RESULTADOS
    # ======================================================

    df_resultado = pd.DataFrame(
        detalhamento_lista
    )


    st.subheader("Resultado mensal")


    # Formatação apenas das colunas existentes
    colunas_monetarias = [

        "Energia elétrica (R$)",

        "Energia SCEE (R$)",

        "Energia compensada GD II (R$)",

        "Compensação adicional (R$)",

        "Valor final (R$)"
    ]


    formatacao = {
        coluna: "{:.2f}"
        for coluna in colunas_monetarias
    }


    formatacao["Créditos disponíveis (kWh)"] = (
        "{:.2f}"
    )

    formatacao["Fio B calculado (kWh)"] = (
        "{:.0f}"
    )


    st.dataframe(
        df_resultado.style.format(formatacao),
        hide_index=True
    )


    # ======================================================
    # INTERPRETAÇÃO AUTOMÁTICA
    # ======================================================

    st.subheader(
        "Interpretação dos resultados"
    )


    valores_faturas = [

        item["Valor final (R$)"]

        for item in detalhamento_lista
    ]


    quantidade_ciclos = len(
        valores_faturas
    )


    if quantidade_ciclos > 0:

        media_fatura = (
            sum(valores_faturas)
            / quantidade_ciclos
        )

        maior_fatura = max(
            valores_faturas
        )

        menor_fatura = min(
            valores_faturas
        )


        st.markdown(

            f"A simulação foi realizada considerando "
            f"**{quantidade_ciclos} ciclos de faturamento**, "
            f"na modalidade **{modalidade}**."
        )


        # --------------------------------------------------
        # SALDO FINAL
        # --------------------------------------------------

        if saldo_credito_kwh > 0:

            st.markdown(

                f"A simulação terminou com um saldo positivo "
                f"de **{saldo_credito_kwh:.2f} kWh em créditos "
                f"de energia**, indicando que ainda existem "
                f"créditos disponíveis para utilização em "
                f"ciclos posteriores."
            )

        else:

            st.markdown(

                "A simulação terminou sem saldo de créditos "
                "disponível para os ciclos posteriores."
            )


        # --------------------------------------------------
        # VALORES DAS FATURAS
        # --------------------------------------------------

        st.markdown(
            f"Durante o período analisado, o valor médio "
            f"das faturas foi de **R\\$ {media_fatura:.2f}**, "
            f"com valores entre **R\\$ {menor_fatura:.2f}** "
            f"e **R\\$ {maior_fatura:.2f}**."
        )


        # --------------------------------------------------
        # COBRANÇA
        # --------------------------------------------------

        ciclos_com_cobranca = sum(

            valor > 0

            for valor in valores_faturas
        )


        if ciclos_com_cobranca == quantidade_ciclos:

            if modalidade == "GD II":

                st.markdown(

                    "Em todos os ciclos simulados permaneceu "
                    "um valor a pagar, mesmo com a utilização "
                    "dos créditos de energia."
                )

            else:

                st.markdown(

                    "Em todos os ciclos simulados permaneceu "
                    "o custo de disponibilidade como valor "
                    "a pagar na fatura."
                )


        elif ciclos_com_cobranca > 0:

            st.markdown(

                f"Em **{ciclos_com_cobranca} dos "
                f"{quantidade_ciclos} ciclos** houve valor "
                "positivo de fatura."
            )

        else:

            st.markdown(

                "Não foram identificados valores positivos "
                "de fatura nos ciclos simulados."
            )


    # ======================================================
    # GRÁFICO DE COMPOSIÇÃO DA FATURA
    # ======================================================

    st.subheader(
        "Composição da fatura por ciclo"
    )


    df_composicao = pd.DataFrame(
        detalhamento_lista
    )


    ciclos = [

        f"{mes} - {ano}"

        for mes, ano in zip(
            df_composicao["Mês"],
            df_composicao["Ano"]
        )
    ]


    # ======================================================
    # GD I
    # ======================================================

    if modalidade == "GD I":

        energia_eletrica = (
            df_composicao[
                "Energia elétrica (R$)"
            ].abs()
        )


        fig, ax = plt.subplots(
            figsize=(11, 6)
        )


        ax.bar(

            ciclos,

            energia_eletrica,

            label="Energia elétrica",

            color="#2196F3"
        )


        valores_finais = (
            df_composicao[
                "Valor final (R$)"
            ]
        )


        for i, valor in enumerate(
            valores_finais
        ):

            ax.annotate(

                f"R$ {valor:.2f}",

                (i, valor),

                xytext=(0, 5),

                textcoords="offset points",

                ha="center",

                fontsize=9,

                fontweight="bold"
            )


        ax.set_title(
            "Composição da fatura por ciclo - GD I"
        )

        ax.set_xlabel("Ciclo")

        ax.set_ylabel("Valor (R$)")

        ax.legend()

        ax.grid(
            axis="y",
            linestyle="--",
            alpha=0.3
        )

        ax.set_ylim(
            bottom=0
        )

        plt.xticks(
            rotation=30,
            ha="right"
        )

        plt.tight_layout()

        st.pyplot(fig)

        plt.close(fig)


    # ======================================================
    # GD II
    # ======================================================

    else:

        energia_eletrica = (
            df_composicao[
                "Energia elétrica (R$)"
            ].abs()
        )

        energia_scee = (
            df_composicao[
                "Energia SCEE (R$)"
            ].abs()
        )


        compensacoes = (

            df_composicao[
                "Energia compensada GD II (R$)"
            ].abs()

            +

            df_composicao[
                "Compensação adicional (R$)"
            ].abs()
        )


        # Desconta as compensações primeiro
        # da Energia SCEE

        energia_scee_liquida = (
            energia_scee
            - compensacoes
        ).clip(lower=0)


        # Caso as compensações ultrapassem
        # a Energia SCEE

        compensacao_restante = (

            compensacoes
            - energia_scee
        ).clip(lower=0)


        energia_eletrica_liquida = (

            energia_eletrica
            - compensacao_restante
        ).clip(lower=0)


        fig, ax = plt.subplots(
            figsize=(11, 6)
        )


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


        valores_finais = (
            df_composicao[
                "Valor final (R$)"
            ]
        )


        for i, valor in enumerate(
            valores_finais
        ):

            ax.annotate(

                f"R$ {valor:.2f}",

                (i, max(valor, 0)),

                xytext=(0, 5),

                textcoords="offset points",

                ha="center",

                fontsize=9,

                fontweight="bold"
            )


        ax.set_title(
            "Composição líquida da fatura por ciclo - GD II"
        )

        ax.set_xlabel("Ciclo")

        ax.set_ylabel("Valor (R$)")

        ax.legend()

        ax.grid(
            axis="y",
            linestyle="--",
            alpha=0.3
        )

        ax.set_ylim(
            bottom=0
        )

        plt.xticks(
            rotation=30,
            ha="right"
        )

        plt.tight_layout()

        st.pyplot(fig)

        plt.close(fig)


    # ======================================================
    # GRÁFICO DE EVOLUÇÃO DOS CRÉDITOS E DA FATURA
    # ======================================================

    st.subheader(
        "Evolução dos créditos e do valor da fatura"
    )


    df_creditos = pd.DataFrame(
        historico_creditos
    )


    fig, ax1 = plt.subplots(
        figsize=(10, 5)
    )


    ciclos = df_creditos[
        "Ciclo"
    ]


    # ======================================================
    # LINHA DOS CRÉDITOS
    # ======================================================

    linha_creditos = ax1.plot(

        ciclos,

        df_creditos[
            "Saldo de créditos (kWh)"
        ],

        marker="o",

        markersize=7,

        linewidth=2,

        color="blue",

        label="Saldo de créditos (kWh)"
    )


    ax1.set_xlabel(
        "Ciclo"
    )

    ax1.set_ylabel(
        "Saldo de créditos (kWh)",
        color="blue"
    )

    ax1.tick_params(
        axis="y",
        labelcolor="blue"
    )


    # Ajuste automático do eixo
    max_creditos = (
        df_creditos[
            "Saldo de créditos (kWh)"
        ].max()
    )

    min_creditos = (
        df_creditos[
            "Saldo de créditos (kWh)"
        ].min()
    )


    margem = max(

        (
            max_creditos
            - min_creditos
        ) * 0.15,

        5
    )


    ax1.set_ylim(

        min(
            0,
            min_creditos - margem
        ),

        max(
            0,
            max_creditos + margem
        )
    )


    # Linha do saldo zero
    ax1.axhline(

        y=0,

        color="gray",

        linestyle="--",

        linewidth=1
    )


    # Valores dos créditos
    for i, valor in enumerate(

        df_creditos[
            "Saldo de créditos (kWh)"
        ]
    ):

        ax1.annotate(

            f"{valor:.0f} kWh",

            (i, valor),

            textcoords="offset points",

            xytext=(0, 8),

            ha="center",

            fontsize=9,

            color="blue"
        )


    # ======================================================
    # EIXO DA FATURA
    # ======================================================

    ax2 = ax1.twinx()


    linha_fatura = ax2.plot(

        ciclos,

        df_creditos[
            "Valor da fatura (R$)"
        ],

        marker="o",

        markersize=7,

        linewidth=2,

        color="red",

        label="Valor da fatura (R$)"
    )


    ax2.set_ylabel(

        "Valor da fatura (R$)",

        color="red"
    )


    ax2.tick_params(

        axis="y",

        labelcolor="red"
    )


    # Ajuste automático do eixo da fatura
    max_fatura = (

        df_creditos[
            "Valor da fatura (R$)"
        ].max()
    )


    if max_fatura > 0:

        ax2.set_ylim(
            0,
            max_fatura * 1.15
        )

    else:

        ax2.set_ylim(
            0,
            10
        )


    # Valores das faturas
    for i, valor in enumerate(

        df_creditos[
            "Valor da fatura (R$)"
        ]
    ):

        ax2.annotate(

            f"R$ {valor:.2f}",

            (i, valor),

            textcoords="offset points",

            xytext=(0, 8),

            ha="center",

            fontsize=9,

            color="red"
        )


    # ======================================================
    # LEGENDAS
    # ======================================================

    linhas = (
        linha_creditos
        + linha_fatura
    )


    etiquetas = [

        "Saldo de créditos (kWh)",

        "Valor da fatura (R$)"
    ]


    ax1.legend(

        linhas,

        etiquetas,

        loc="upper center",

        bbox_to_anchor=(
            0.5,
            1.12
        ),

        ncol=2
    )


    ax1.grid(

        axis="y",

        linestyle="--",

        alpha=0.4
    )


    fig.tight_layout()

    st.pyplot(fig)

    plt.close(fig)
