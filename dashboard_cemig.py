import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Análise Energética",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="auto",
)

# Função para carregar dados
@st.cache_data
def load_data():
    return pd.read_excel("Dados.xlsx", sheet_name=None)

# Carregar dados do Excel
data = load_data()

# Título do Dashboard
st.title('Análise Energética')

def calculate_metrics(data):
    total_consumo = sum(df['Consumo Total em kWh'].sum() for df in data.values())
    total_geracao = data['Sapecado 1']['Energia Gerada em kWh'].sum()
    periodo_inicial = data[next(iter(data))]['Mês/Ano'].iloc[0]
    periodo_final = data[next(iter(data))]['Mês/Ano'].iloc[-1]
    periodo_formatado = f"{periodo_inicial} - {periodo_final}"
    return total_consumo, total_geracao, periodo_formatado

def display_metrics(total_consumo, total_geracao, periodo_formatado):
    col1, col2, col3 = st.columns(3)
    col1.metric("Período de Referência", periodo_formatado)
    col2.metric("Consumo Total de Energia (kWh)", "{:,.2f} kWh".format(total_consumo).replace(",", "X").replace(".", ",").replace("X", "."))
    col3.metric("Total de Energia Gerada (kWh)", "{:,.2f} kWh".format(total_geracao).replace(",", "X").replace(".", ",").replace("X", "."))

# Cálculo e exibição de métricas
total_consumo, total_geracao, periodo_formatado = calculate_metrics(data)
display_metrics(total_consumo, total_geracao, periodo_formatado)

# Função para gerar os gráficos
def plot_chart(df, title, y_label, chart_type, localidades_selecionadas):
    # Verifica se 'Energia Gerada em kWh' foi selecionada sem 'Sapecado 1'
    if y_label == 'Energia Gerada em kWh' and 'Sapecado 1' not in localidades_selecionadas:
        st.error("A 'Energia Gerada em kWh' está disponível apenas para 'Sapecado 1'. Selecione 'Sapecado 1' para visualizar esse tipo de dado.")
        return

    # Filtrar os dados
    df_filtered = pd.DataFrame()
    for localidade in localidades_selecionadas:
        if localidade in df:
            df_loc = df[localidade].copy()
            df_loc['Localidade'] = localidade
            df_filtered = pd.concat([df_filtered, df_loc])
    
    if not df_filtered.empty:
        if chart_type == 'Linha':
            fig = px.line(df_filtered, x='Mês/Ano', y=y_label, color='Localidade', title=title)
        elif chart_type == 'Barra':
            fig = px.bar(df_filtered, x='Mês/Ano', y=y_label, color='Localidade', barmode='group', title=title)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("Não foram selecionadas propriedades para exibir.")

def setup_sidebar(data):
    with st.sidebar:
        st.title('Filtros para os Gráficos')
        tipo_dado = st.selectbox('Selecione o que você gostaria de saber:', ['Consumo Total em kWh', 'Energia Injetada em kWh', 'Energia Gerada em kWh', 
            'Saldo Atual de Geração', 'Consumo Pago em kWh'])
        opcoes_localidades = list(data.keys())
        localidades_selecionadas = st.multiselect("Selecione as propriedades que deseja obter as informações:",
                                                  options=opcoes_localidades,
                                                  default=opcoes_localidades[0])
        tipo_grafico = st.radio('Selecione o tipo de gráfico:', ('Linha', 'Barra'))
        st.write("---")
        st.title('Filtro para a Distribuição da Energia Gerada')
        meses_disponiveis = data['Sapecado 1']['Mês/Ano'].unique()
        selected_month = st.selectbox('Escolha o mês de referência:', meses_disponiveis)
    return tipo_dado, localidades_selecionadas, tipo_grafico, selected_month

# Setup sidebar e captura de valores de filtro
tipo_dado, localidades_selecionadas, tipo_grafico, selected_month = setup_sidebar(data)

# Função para calcular e exibir a porcentagem de energia injetada por mês
def display_monthly_energy_distribution(data, selected_month):
    # Encontrar o mês correspondente nos dados
    month_data = data['Sapecado 1'][data['Sapecado 1']['Mês/Ano'] == selected_month]
    if month_data.empty:
        st.error(f"Não há dados disponíveis para o mês: {selected_month}")
        return
    
    total_generated = month_data['Energia Gerada em kWh'].sum()
    st.write(f"## Distribuição de Energia para o Mês: {selected_month}")

    injected_data = []
    for loc in data.keys():
        loc_data = data[loc][data[loc]['Mês/Ano'] == selected_month]
        if not loc_data.empty and 'Energia Injetada em kWh' in loc_data.columns:
            injected = loc_data['Energia Injetada em kWh'].sum()
            injected_data.append({'Localidade': loc, 'Energia Injetada': injected})

    if injected_data:
        df_injected = pd.DataFrame(injected_data)
        fig = px.pie(df_injected, values='Energia Injetada', names='Localidade', title="Distribuição de Energia Injetada")
        st.plotly_chart(fig)
    else:
        st.write("Não há dados de energia injetada para exibir.")

def display_suggested_energy_distribution(data, selected_month):

    total_consumption = sum(df[df['Mês/Ano'] == selected_month]['Consumo Total em kWh'].sum() for df in data.values())

    consumption_data = []
    for loc in data.keys():
        loc_data = data[loc][data[loc]['Mês/Ano'] == selected_month]
        if not loc_data.empty and 'Consumo Total em kWh' in loc_data.columns:
            consumption = loc_data['Consumo Total em kWh'].sum()
            consumption_data.append({'Localidade': loc, 'Consumo': consumption})

    if consumption_data:
        df_consumption = pd.DataFrame(consumption_data)
        fig = px.pie(df_consumption, values='Consumo', names='Localidade', title="Sugestão de Distribuição Baseada no Consumo Total do Mês")
        st.plotly_chart(fig)
    else:
        st.write("Não há dados de consumo para exibir.")

# Tabs para diferentes visualizações
tab1, tab2 = st.tabs(["Gráficos", "Distribuição da Energia Gerada"])

with tab1:
    titulo_grafico = f"{tipo_dado} nas propriedades {', '.join(localidades_selecionadas)}"
    plot_chart(data, titulo_grafico, tipo_dado, tipo_grafico, localidades_selecionadas)    

# Aba de visualização da distribuição da energia gerada
with tab2:
    display_monthly_energy_distribution(data, selected_month)
    with st.expander("Visualizar Sugestão de Distribuição Baseada no Consumo"):
        display_suggested_energy_distribution(data, selected_month)

