#Versao 2.0

import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração inicial da página
st.set_page_config(page_title="Análise Energética", page_icon="⚡", layout="wide", initial_sidebar_state="auto")

# Função para carregar dados
@st.cache_data
def load_data():
    return pd.read_excel("Dados.xlsx", sheet_name=None)

# Carregar dados do Excel
data = load_data()

# Função para exibir a página de métricas com um layout melhorado
def show_metrics_page():
    st.title('Métricas')

    # Obter período e calcular métricas
    start_period, end_period = setup_metrics(data)
    metrics = calculate_metrics(data, start_period, end_period)

    # Período de Referência
    st.markdown(f"### Período de Referência: {metrics['Periodo']}")
    st.markdown("<hr>", unsafe_allow_html=True)

    # Uso de containers ou expanders para agrupar métricas
    energy_metrics = st.container()
    cost_metrics = st.expander("Detalhes dos Custos", expanded=False)

    with energy_metrics:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Consumo Total (kWh)", f"{metrics['Consumo Total']:.2f}")
        with col2:
            st.metric("Geração Total (kWh)", f"{metrics['Geração Total']:.2f}")
        with col3:
            st.metric("Média Diária (kWh)", f"{metrics['Média Diária de Consumo']:.2f}")

    with cost_metrics:
        st.metric("Custo Total (R$)", f"R$ {metrics['Custo Total']:.2f}")
        st.metric("Energia Compensada (kWh)", f"{metrics['Energia Compensada Total']:.2f}")
        st.metric("Energia Transferida (kWh)", f"{metrics['Energia Transferida Total']:.2f}")

    st.markdown("<hr>", unsafe_allow_html=True)

def show_charts_page():
    st.title('Gráficos')
    tipo_dado, localidades_selecionadas, tipo_grafico = setup_charts_sidebar(data)
    titulo_grafico = f"{tipo_dado} nas propriedades {', '.join(localidades_selecionadas)}"
    plot_chart(data, titulo_grafico, tipo_dado, tipo_grafico, localidades_selecionadas)

def show_distribution_page():
    st.title('Distribuição de Energia')
    selected_month = setup_distribution_sidebar(data)
    display_monthly_energy_distribution(data, selected_month)
    with st.expander(f"Visualizar Sugestão de Distribuição Baseada no Consumo do mês {selected_month}"):
        display_suggested_energy_distribution(data, selected_month)

def calculate_metrics(data, start_period, end_period):
    total_consumo = 0
    total_geracao = 0
    total_custo = 0
    total_energia_compensada = 0
    total_energia_transferida = 0
    saldo_atual_geracao = 0
    consumo_pago_total = 0

    # Criar lista de meses/anos mantendo a ordem original
    all_dates = []
    for df in data.values():
        for date in df['Mês/Ano']:
            if date not in all_dates:
                all_dates.append(date)

    # Obtendo os índices das datas inicial e final na lista ordenada
    start_index = all_dates.index(start_period)
    end_index = all_dates.index(end_period)
 
    # Processando cada dataframe e somando os valores
    for df in data.values():
        filtered_df = df[df['Mês/Ano'].isin(all_dates[start_index:end_index + 1])]
        total_consumo += filtered_df['Consumo Total em kWh'].sum()
        total_custo += filtered_df['Valor a Pagar (R$)'].sum()
        total_energia_compensada += filtered_df['Energia Compensada em kWh'].sum()
        total_energia_transferida += filtered_df['Energia Transferida em kWh'].sum()
        saldo_atual_geracao += filtered_df['Saldo Atual de Geração em kWh'].iloc[-1]  # Assumindo que o saldo mais recente é relevante
        consumo_pago_total += filtered_df['Consumo Pago em kWh'].sum()

    # Tratamento específico para 'Sapecado 1'
    if 'Sapecado 1' in data:
        sapecado_df = data['Sapecado 1']
        filtered_sapecado = sapecado_df[sapecado_df['Mês/Ano'].isin(all_dates[start_index:end_index + 1])]
        total_geracao = filtered_sapecado['Energia Gerada em kWh'].sum()

    # Calculando a média diária de consumo
    dias_totais = sum(filtered_df['Dias Considerados'].sum() for df in data.values())
    media_diaria_consumo = total_consumo / dias_totais if dias_totais > 0 else 0

    periodo_formatado = f"{start_period} - {end_period}"
    return {
        "Periodo": periodo_formatado,
        "Consumo Total": total_consumo,
        "Geração Total": total_geracao,
        "Custo Total": total_custo,
        "Energia Compensada Total": total_energia_compensada,
        "Energia Transferida Total": total_energia_transferida,
        "Saldo Atual de Geração": saldo_atual_geracao,
        "Consumo Pago Total": consumo_pago_total,
        "Média Diária de Consumo": media_diaria_consumo
    }

def display_metrics(total_consumo, total_geracao, periodo_formatado):
    col1, col2, col3 = st.columns(3)
    col1.metric("Período de Referência", periodo_formatado)
    col2.metric("Consumo Total de Energia (kWh)", "{:,.2f} kWh".format(total_consumo).replace(",", "X").replace(".", ",").replace("X", "."))
    col3.metric("Total de Energia Gerada (kWh)", "{:,.2f} kWh".format(total_geracao).replace(",", "X").replace(".", ",").replace("X", "."))

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

# Função de configuração da barra lateral para gráficos
def setup_charts_sidebar(data):
    with st.sidebar:
        st.title('Filtros para os Gráficos')
        tipo_dado = st.selectbox('Selecione o que você gostaria de saber:', ['Consumo Total em kWh', 'Energia Compensada em kWh', 'Energia Transferida em kWh', 'Energia Gerada em kWh', 'Saldo Atual de Geração em kWh', 'Consumo Pago em kWh'])
        opcoes_localidades = list(data.keys())
        localidades_selecionadas = st.multiselect("Selecione as propriedades que deseja obter as informações:", options=opcoes_localidades, default=opcoes_localidades[0])
        tipo_grafico = st.radio('Selecione o tipo de gráfico:', ('Linha', 'Barra'))
        return tipo_dado, localidades_selecionadas, tipo_grafico

# Função de configuração da barra lateral para distribuição de energia
def setup_distribution_sidebar(data):
    with st.sidebar:
        st.title('Filtro para a Distribuição da Energia Gerada')
        meses_disponiveis = data['Sapecado 1']['Mês/Ano'].unique()
        selected_month = st.selectbox('Escolha o mês de referência:', meses_disponiveis)
        return selected_month

# Função de configuração da barra lateral para métricas
def setup_metrics(data):
    with st.sidebar:
        st.title('Filtros para as Métricas')
        # Criar lista de meses/anos mantendo a ordem original
        all_dates = []
        for df in data.values():
            for date in df['Mês/Ano']:
                if date not in all_dates:
                    all_dates.append(date)

        # Seletores para escolher o período de referência com rótulos
        start_period = st.selectbox('Data Inicial', all_dates, index=0)
        # Atualiza as opções para a data final com base na seleção inicial
        end_period_options = all_dates[all_dates.index(start_period):]
        end_period = st.selectbox('Data Final', end_period_options, index=0)

        return start_period, end_period

# Atualização da função para calcular a energia transferida
def calculate_energy_transferred(data, loc, selected_month_index):
    loc_data = data[loc]
    if selected_month_index == 0:
        transferred = loc_data.iloc[0]['Energia Transferida em kWh'] if 'Energia Transferida em kWh' in loc_data.columns else 0
        return transferred

    current_month_data = loc_data.iloc[selected_month_index]
    transferred = current_month_data['Energia Transferida em kWh'] if 'Energia Transferida em kWh' in current_month_data else 0
    return max(0, transferred)


def display_monthly_energy_distribution(data, selected_month):
    st.write(f"## Distribuição de Energia Transferida para o Mês: {selected_month}")

    selected_month_index = data[next(iter(data))]['Mês/Ano'].tolist().index(selected_month)
    transferred_data = [{'Localidade': loc, 'Energia Transferida': calculate_energy_transferred(data, loc, selected_month_index)} for loc in data.keys()]

    if transferred_data:
        df_transferred = pd.DataFrame(transferred_data)
        fig = px.pie(df_transferred, values='Energia Transferida', names='Localidade', title=f"Distribuição de Energia Transferida do mês {selected_month}")
        st.plotly_chart(fig)
    else:
        st.write("Não há dados de energia transferida para exibir.")

def display_suggested_energy_distribution(data, selected_month):

    consumption_data = []
    for loc in data.keys():
        loc_data = data[loc][data[loc]['Mês/Ano'] == selected_month]
        if not loc_data.empty and 'Consumo Total em kWh' in loc_data.columns:
            consumption = loc_data['Consumo Total em kWh'].sum()
            consumption_data.append({'Localidade': loc, 'Consumo': consumption})

    if consumption_data:
        df_consumption = pd.DataFrame(consumption_data)
        fig = px.pie(df_consumption, values='Consumo', names='Localidade', title=f"Sugestão de Distribuição Baseada no Consumo Total do Mês {selected_month}")
        st.plotly_chart(fig)
    else:
        st.write("Não há dados de consumo para exibir.")

# Seletor de páginas na barra lateral
with st.sidebar:
    st.title('***O que você gostaria de analisar?***:thinking_face:')
    page = st.radio("---", ("Métricas :information_source:", "Gráficos :bar_chart:", "Distribuição de Energia :battery:"))

# Exibindo a página selecionada
if page == "Métricas :information_source:":
    show_metrics_page()
elif page == "Gráficos :bar_chart:":
    show_charts_page()
elif page == "Distribuição de Energia :battery:":
    show_distribution_page()