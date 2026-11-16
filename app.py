
import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# =====================================
# CONFIGURAÇÃO
# =====================================

st.set_page_config(
    page_title="Gestão Rural",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================
# BANCO DE DADOS
# =====================================

@st.cache_resource
def conectar_banco():
    banco = sqlite3.connect(
        "gestao_rural.db",
        check_same_thread=False
    )
    banco.execute("PRAGMA foreign_keys = ON")
    return banco

conn = conectar_banco()

def executar(sql, parametros=()):
    conn.execute(sql, parametros)
    conn.commit()

def consultar(sql):
    return pd.read_sql_query(sql, conn)

# Criar tabelas
executar("""
CREATE TABLE IF NOT EXISTS horta (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cultura TEXT,
    canteiro TEXT,
    quantidade INTEGER,
    plantio TEXT,
    colheita TEXT,
    status TEXT
)
""")

executar("""
CREATE TABLE IF NOT EXISTS suinos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    identificacao TEXT,
    raca TEXT,
    sexo TEXT,
    peso REAL,
    nascimento TEXT,
    status TEXT
)
""")

executar("""
CREATE TABLE IF NOT EXISTS despesas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    categoria TEXT,
    descricao TEXT,
    valor REAL,
    data TEXT
)
""")

executar("""
CREATE TABLE IF NOT EXISTS receitas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    descricao TEXT,
    valor REAL,
    data TEXT
)
""")

# =====================================
# MENU LATERAL
# =====================================

st.sidebar.title("🌾 GESTÃO RURAL")
st.sidebar.caption("Controle da propriedade")

if "pagina" not in st.session_state:
    st.session_state.pagina = "Dashboard"

paginas = {
    "Dashboard": "🏠 Dashboard",
    "Horta": "🌱 Horta",
    "Suínos": "🐖 Suínos",
    "Financeiro": "💰 Financeiro"
}

for nome, rotulo in paginas.items():
    if st.sidebar.button(
        rotulo,
        key=f"menu_{nome}",
        use_container_width=True,
        type="primary" if st.session_state.pagina == nome else "secondary"
    ):
        st.session_state.pagina = nome
        st.rerun()

st.sidebar.divider()
st.sidebar.caption("Sistema de Gestão Rural")

menu = st.session_state.pagina

# =====================================
# DASHBOARD
# =====================================

if menu == "Dashboard":

    st.title("🌱 Painel de Gestão Rural")
    st.write("Bem-vindo ao controle da sua propriedade!")

    horta = consultar("SELECT * FROM horta")
    suinos = consultar("SELECT * FROM suinos")
    despesas = consultar("SELECT * FROM despesas")
    receitas = consultar("SELECT * FROM receitas")

    total_receitas = receitas["valor"].sum()
    total_despesas = despesas["valor"].sum()
    saldo = total_receitas - total_despesas

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("🌱 Plantações", len(horta))
    col2.metric("🐖 Suínos", len(suinos))
    col3.metric("💰 Receitas", f"R$ {total_receitas:,.2f}")
    col4.metric("📊 Saldo", f"R$ {saldo:,.2f}")

    st.divider()

    esquerda, direita = st.columns(2)

    with esquerda:
        st.subheader("🌱 Situação da Horta")

        if not horta.empty:
            st.dataframe(
                horta,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Nenhuma plantação cadastrada.")

    with direita:
        st.subheader("🐖 Situação dos Suínos")

        if not suinos.empty:
            st.dataframe(
                suinos,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Nenhum suíno cadastrado.")

    st.divider()
    st.subheader("💵 Resumo Financeiro")

    financeiro = pd.DataFrame({
        "Tipo": ["Receitas", "Despesas"],
        "Valor": [total_receitas, total_despesas]
    })

    st.bar_chart(financeiro.set_index("Tipo"))

# =====================================
# HORTA
# =====================================

elif menu == "Horta":

    st.title("🌱 Gestão da Horta")
    st.write("Cadastre e acompanhe suas plantações.")

    with st.form("form_horta", clear_on_submit=True):

        cultura = st.text_input("Nome da cultura")
        canteiro = st.text_input("Identificação do canteiro")

        quantidade = st.number_input(
            "Quantidade plantada",
            min_value=1,
            step=1
        )

        plantio = st.date_input("Data do plantio", value=date.today())

        colheita = st.date_input(
            "Previsão de colheita",
            value=date.today()
        )

        status = st.selectbox(
            "Situação",
            [
                "Plantado",
                "Em crescimento",
                "Pronto para colher",
                "Colhido"
            ]
        )

        salvar = st.form_submit_button(
            "Cadastrar plantação",
            use_container_width=True
        )

        if salvar:
            if cultura.strip():
                executar("""
                    INSERT INTO horta
                    (cultura, canteiro, quantidade, plantio, colheita, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    cultura.strip(),
                    canteiro,
                    quantidade,
                    str(plantio),
                    str(colheita),
                    status
                ))

                st.success("Plantação cadastrada!")
                st.rerun()
            else:
                st.error("Informe o nome da cultura.")

    st.divider()
    st.subheader("📋 Plantações cadastradas")

    dados = consultar("SELECT * FROM horta")

    if not dados.empty:

        st.dataframe(
            dados,
            use_container_width=True,
            hide_index=True
        )

        ids = dados["id"].tolist()

        excluir_id = st.selectbox(
            "Selecione a plantação para excluir",
            ids,
            format_func=lambda x: f"ID {x} - {dados.loc[dados.id == x, 'cultura'].iloc[0]}"
        )

        if st.button("🗑️ Excluir plantação"):
            executar(
                "DELETE FROM horta WHERE id = ?",
                (excluir_id,)
            )
            st.success("Plantação excluída!")
            st.rerun()

    else:
        st.info("Ainda não existem plantações cadastradas.")

# =====================================
# SUÍNOS
# =====================================

elif menu == "Suínos":

    st.title("🐖 Gestão de Suínos")
    st.write("Controle individual dos animais.")

    with st.form("form_suinos", clear_on_submit=True):

        identificacao = st.text_input("Identificação / Brinco")

        raca = st.selectbox(
            "Raça",
            [
                "Landrace",
                "Large White",
                "Duroc",
                "Pietrain",
                "Mestiço",
                "Outra"
            ]
        )

        sexo = st.selectbox(
            "Sexo",
            ["Macho", "Fêmea"]
        )

        peso = st.number_input(
            "Peso atual (kg)",
            min_value=0.0,
            step=0.5
        )

        nascimento = st.date_input(
            "Data de nascimento",
            value=date.today()
        )

        status = st.selectbox(
            "Situação",
            [
                "Ativo",
                "Matriz",
                "Reprodutor",
                "Engorda",
                "Vendido"
            ]
        )

        salvar = st.form_submit_button(
            "Cadastrar suíno",
            use_container_width=True
        )

        if salvar:
            if identificacao.strip():
                executar("""
                    INSERT INTO suinos
                    (identificacao, raca, sexo, peso, nascimento, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    identificacao.strip(),
                    raca,
                    sexo,
                    peso,
                    str(nascimento),
                    status
                ))

                st.success("Suíno cadastrado!")
                st.rerun()
            else:
                st.error("Informe a identificação do animal.")

    st.divider()
    st.subheader("📋 Animais cadastrados")

    dados = consultar("SELECT * FROM suinos")

    if not dados.empty:

        st.dataframe(
            dados,
            use_container_width=True,
            hide_index=True
        )

        ids = dados["id"].tolist()

        excluir_id = st.selectbox(
            "Selecione o animal para excluir",
            ids,
            format_func=lambda x: f"ID {x} - {dados.loc[dados.id == x, 'identificacao'].iloc[0]}",
            key="excluir_suino"
        )

        if st.button("🗑️ Excluir suíno"):
            executar(
                "DELETE FROM suinos WHERE id = ?",
                (excluir_id,)
            )
            st.success("Animal excluído!")
            st.rerun()

    else:
        st.info("Nenhum suíno cadastrado.")

# =====================================
# FINANCEIRO
# =====================================

elif menu == "Financeiro":

    st.title("💰 Controle Financeiro")

    aba1, aba2, aba3 = st.tabs([
        "📉 Despesas",
        "📈 Receitas",
        "📊 Resumo"
    ])

    with aba1:

        st.subheader("Cadastrar despesa")

        with st.form("form_despesa", clear_on_submit=True):

            categoria = st.selectbox(
                "Categoria",
                [
                    "Ração",
                    "Sementes",
                    "Adubo",
                    "Medicamentos",
                    "Mão de obra",
                    "Equipamentos",
                    "Outros"
                ]
            )

            descricao = st.text_input("Descrição da despesa")

            valor = st.number_input(
                "Valor (R$)",
                min_value=0.0,
                step=1.0
            )

            data_despesa = st.date_input(
                "Data da despesa",
                value=date.today()
            )

            salvar = st.form_submit_button("Salvar despesa")

            if salvar:
                executar("""
                    INSERT INTO despesas
                    (categoria, descricao, valor, data)
                    VALUES (?, ?, ?, ?)
                """, (
                    categoria,
                    descricao,
                    valor,
                    str(data_despesa)
                ))

                st.success("Despesa registrada!")
                st.rerun()

        dados = consultar("SELECT * FROM despesas")
        st.dataframe(dados, use_container_width=True, hide_index=True)

    with aba2:

        st.subheader("Cadastrar receita")

        with st.form("form_receita", clear_on_submit=True):

            descricao = st.text_input("Descrição da receita")

            valor = st.number_input(
                "Valor recebido (R$)",
                min_value=0.0,
                step=1.0
            )

            data_receita = st.date_input(
                "Data da receita",
                value=date.today()
            )

            salvar = st.form_submit_button("Salvar receita")

            if salvar:
                executar("""
                    INSERT INTO receitas
                    (descricao, valor, data)
                    VALUES (?, ?, ?)
                """, (
                    descricao,
                    valor,
                    str(data_receita)
                ))

                st.success("Receita registrada!")
                st.rerun()

        dados = consultar("SELECT * FROM receitas")
        st.dataframe(dados, use_container_width=True, hide_index=True)

    with aba3:

        st.subheader("Resumo financeiro")

        despesas = consultar("SELECT * FROM despesas")
        receitas = consultar("SELECT * FROM receitas")

        total_despesas = despesas["valor"].sum()
        total_receitas = receitas["valor"].sum()

        col1, col2, col3 = st.columns(3)

        col1.metric("Receitas", f"R$ {total_receitas:,.2f}")
        col2.metric("Despesas", f"R$ {total_despesas:,.2f}")
        col3.metric(
            "Saldo",
            f"R$ {total_receitas - total_despesas:,.2f}"
        )

        resumo = pd.DataFrame({
            "Tipo": ["Receitas", "Despesas"],
            "Valor": [total_receitas, total_despesas]
        })

        st.bar_chart(resumo.set_index("Tipo"))

