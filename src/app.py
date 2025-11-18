import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Dashboard de Franquias",
                   page_icon="🚀",
                   layout="wide")

# --- FUNÇÕES DE CONEXÃO E CONSULTA (COM CACHE) ---

@st.cache_data(ttl=600)
def carregar_franquias():
    """Carrega a lista de 'id' e 'nome' de todas as franquias."""
    try:
        conn = st.connection("neon", type="sql")
        df = conn.query('SELECT id, nome FROM franquias ORDER BY nome;', ttl=600)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar franquias: {e}")
        return pd.DataFrame(columns=['id', 'nome'])

@st.cache_data(ttl=600)
def carregar_dados_franquia(franquia_id):
    """Carrega organizações, indivíduos e veículos da franquia selecionada."""
    try:
        conn = st.connection("neon", type="sql")
        
        query_orgs = f'SELECT * FROM organizacoes WHERE id_franquia = {franquia_id};'
        query_inds = f'SELECT * FROM individuos WHERE id_franquia = {franquia_id};'
        
        query_veis = f"""
            SELECT 
                v.*, 
                i.nome as comandante_nome
            FROM veiculos v
            LEFT JOIN comandantes c ON v.id_comandante = c.id
            LEFT JOIN individuos i ON c.id_individuo = i.id
            WHERE v.id_franquia = {franquia_id};
        """
        
        dados = {
            "orgs": conn.query(query_orgs, ttl=600),
            "inds": conn.query(query_inds, ttl=600),
            "veis": conn.query(query_veis, ttl=600)
        }
        return dados
    except Exception as e:
        st.error(f"Erro ao carregar dados da franquia: {e}")
        return {
            "orgs": pd.DataFrame(),
            "inds": pd.DataFrame(),
            "veis": pd.DataFrame()
        }

# --- NOVA FUNÇÃO ---
@st.cache_data(ttl=600)
def carregar_todos_os_dados():
    """Carrega TODOS os dados e adiciona o nome da franquia."""
    try:
        conn = st.connection("neon", type="sql")
        
        query_orgs = """
            SELECT o.*, f.nome as nome_franquia 
            FROM organizacoes o
            LEFT JOIN franquias f ON o.id_franquia = f.id;
        """
        query_inds = """
            SELECT i.*, f.nome as nome_franquia
            FROM individuos i
            LEFT JOIN franquias f ON i.id_franquia = f.id;
        """
        query_veis = """
            SELECT 
                v.*, 
                i.nome as comandante_nome,
                f.nome as nome_franquia
            FROM veiculos v
            LEFT JOIN comandantes c ON v.id_comandante = c.id
            LEFT JOIN individuos i ON c.id_individuo = i.id
            LEFT JOIN franquias f ON v.id_franquia = f.id;
        """
        
        dados = {
            "orgs": conn.query(query_orgs, ttl=600),
            "inds": conn.query(query_inds, ttl=600),
            "veis": conn.query(query_veis, ttl=600)
        }
        return dados
    except Exception as e:
        st.error(f"Erro ao carregar todos os dados: {e}")
        return {
            "orgs": pd.DataFrame(),
            "inds": pd.DataFrame(),
            "veis": pd.DataFrame()
        }
# --- FIM DA NOVA FUNÇÃO ---


# --- APLICAÇÃO PRINCIPAL ---
st.title("🚀 Dashboard Interativo de Franquias")
st.markdown("---")

# --- BARRA LATERAL (SIDEBAR) ---
st.sidebar.header("Filtro Principal")
df_franquias = carregar_franquias()

if df_franquias.empty:
    st.sidebar.error("Nenhuma franquia encontrada no banco de dados.")
else:
    franquia_map = pd.Series(df_franquias.id.values, index=df_franquias.nome).to_dict()
    
    # --- MUDANÇA AQUI: Adiciona "Todas as Franquias" à lista ---
    opcoes_franquia = ["Todas as Franquias"] + list(franquia_map.keys())
    
    nome_selecionado = st.sidebar.selectbox(
        "Selecione uma Franquia:",
        options=opcoes_franquia,
        index=0 # Define "Todas as Franquias" como padrão
    )

    # --- MUDANÇA AQUI: Lógica IF/ELSE para carregar dados ---
    if nome_selecionado == "Todas as Franquias":
        dados = carregar_todos_os_dados()
        st.header(f"Visão Geral: {nome_selecionado}")
    else:
        # Lógica antiga para franquia específica
        id_selecionado = franquia_map[nome_selecionado]
        dados = carregar_dados_franquia(id_selecionado)
        st.header(f"Visão Geral: {nome_selecionado}")
    # --- FIM DAS MUDANÇAS NA LÓGICA DE CARREGAMENTO ---

    # Carrega os dataframes (brutos) com base na seleção
    df_orgs_bruto = dados["orgs"]
    df_inds_bruto = dados["inds"]
    df_veis_bruto = dados["veis"]

    # --- FILTROS DETALHADOS (Funcionam com ambos os carregamentos) ---
    st.sidebar.header("Filtros Detalhados")

    if not df_orgs_bruto.empty:
        opcoes_tipo_org = df_orgs_bruto['tipo_organizacao'].unique()
        tipo_org_filtro = st.sidebar.multiselect(
            "Filtrar por Tipo de Organização:",
            options=opcoes_tipo_org,
            default=opcoes_tipo_org
        )
    else:
        tipo_org_filtro = []

    if not df_inds_bruto.empty:
        opcoes_especie = df_inds_bruto['especie'].unique()
        especie_filtro = st.sidebar.multiselect(
            "Filtrar por Espécie:",
            options=opcoes_especie,
            default=opcoes_especie
        )
    else:
        especie_filtro = []

    if not df_veis_bruto.empty:
        opcoes_fabricante = df_veis_bruto['fabricante'].unique()
        fabricante_filtro = st.sidebar.multiselect(
            "Filtrar por Fabricante:",
            options=opcoes_fabricante,
            default=opcoes_fabricante
        )
    else:
        fabricante_filtro = []

    # --- APLICA OS FILTROS NOS DATAFRAMES ---
    df_orgs_filtrado = df_orgs_bruto.query("tipo_organizacao == @tipo_org_filtro")
    df_inds_filtrado = df_inds_bruto.query("especie == @especie_filtro")
    df_veis_filtrado = df_veis_bruto.query("fabricante == @fabricante_filtro")


    # --- PÁGINA PRINCIPAL ---
    st.markdown(f"**Resultados filtrados:**")

    # --- MÉTRICAS PRINCIPAIS (KPIs) ---
    col1, col2, col3 = st.columns(3)
    col1.metric(label="Organizações Encontradas", value=df_orgs_filtrado.shape[0])
    col2.metric(label="Indivíduos Encontrados", value=df_inds_filtrado.shape[0])
    col3.metric(label="Veículos Encontrados", value=df_veis_filtrado.shape[0])

    st.markdown("---")

    # --- ABAS COM DADOS DETALHADOS ---
    tab1, tab2, tab3 = st.tabs(["Organizações", "Indivíduos", "Veículos"])

    with tab1:
        st.subheader("Organizações")
        if not df_orgs_filtrado.empty:
            tipo_orgs = df_orgs_filtrado['tipo_organizacao'].value_counts().reset_index()
            fig_orgs = px.pie(tipo_orgs, 
                              names='tipo_organizacao', 
                              values='count', 
                              title="Tipos de Organização (Filtrado)")
            st.plotly_chart(fig_orgs, use_container_width=True)
            st.dataframe(df_orgs_filtrado) 
        else:
            st.info("Nenhuma organização encontrada com os filtros atuais.")

    with tab2:
        st.subheader("Indivíduos")
        if not df_inds_filtrado.empty:
            contagem_especie = df_inds_filtrado['especie'].value_counts().reset_index()
            fig_inds = px.bar(contagem_especie, 
                              x='especie', 
                              y='count', 
                              title="Contagem por Espécie (Filtrado)")
            st.plotly_chart(fig_inds, use_container_width=True)
            st.dataframe(df_inds_filtrado)
        else:
            st.info("Nenhum indivíduo encontrado com os filtros atuais.")

    with tab3:
        st.subheader("Veículos")
        if not df_veis_filtrado.empty:
            contagem_fab = df_veis_filtrado['fabricante'].value_counts().reset_index()
            fig_veis = px.bar(contagem_fab, 
                              x='fabricante', 
                              y='count', 
                              title="Veículos por Fabricante (Filtrado)")
            st.plotly_chart(fig_veis, use_container_width=True)
            st.dataframe(df_veis_filtrado)
        else:
            st.info("Nenhum veículo encontrado com os filtros atuais.")