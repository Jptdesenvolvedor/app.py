import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date

# Arquivo de dados
FILE = 'dados_financas.csv'

# Categorias
CATEGORIAS = [
    'Academia', 'Aluguel', 'Água', 'Cartão de Crédito', 'Condomínio', 'Cuidado Pessoal',
    'Dívidas', 'Diversão', 'Empregada Doméstica', 'Estudos', 'Extras', 'Gás',
    'Internet', 'Investimentos', 'IPTU', 'IPVA', 'Luz', 'Mercado', 'Parcela do Carro',
    'Recebimentos', 'Restaurantes', 'Saldo Bancário', 'Seguro do Carro', 'Telefone',
    'TV a Cabo', 'Viagens'
]

# Carrega ou cria base
def carregar_dados():
    try:
        df = pd.read_csv(FILE)
        if df.empty:
            return pd.DataFrame(columns=['Data', 'Tipo', 'Categoria', 'Valor', 'Observação'])
        
        df = df.dropna(subset=['Data'])
        
        if df.empty:
            return pd.DataFrame(columns=['Data', 'Tipo', 'Categoria', 'Valor', 'Observação'])
        
        try:
            df['Data'] = pd.to_datetime(df['Data'], format='mixed', dayfirst=True, errors='coerce')
        except:
            try:
                df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
            except:
                df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        
        df = df.dropna(subset=['Data'])
        
        return df
    except FileNotFoundError:
        return pd.DataFrame(columns=['Data', 'Tipo', 'Categoria', 'Valor', 'Observação'])
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        return pd.DataFrame(columns=['Data', 'Tipo', 'Categoria', 'Valor', 'Observação'])

def salvar_dados(df):
    df_copy = df.copy()
    df_copy['Data'] = pd.to_datetime(df_copy['Data']).dt.strftime('%Y-%m-%d')
    df_copy.to_csv(FILE, index=False)

st.title("📊 Controle Financeiro Pessoal")

aba = st.sidebar.radio("Menu", ["Adicionar Lançamento", "Relatório"])

df = carregar_dados()

if aba == "Adicionar Lançamento":
    if 'form_tipo' not in st.session_state:
        st.session_state['form_tipo'] = 'Receita'
    if 'form_categoria' not in st.session_state:
        st.session_state['form_categoria'] = CATEGORIAS[0]
    if 'form_obs' not in st.session_state:
        st.session_state['form_obs'] = ''

    def atualiza_obs():
        st.session_state['form_obs'] = ''

    tipo = st.radio("Tipo", ["Receita", "Despesa"], key='form_tipo', on_change=atualiza_obs)
    categoria = st.selectbox("Categoria", sorted(CATEGORIAS), key='form_categoria', on_change=atualiza_obs)

    with st.form("form_lancamento"):
        valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01, format="%.2f", help="Digite como 1000.00 (sem ponto de milhar)")
        data = st.date_input("Data", value=date.today())
        obs = st.text_input("Observação", value=st.session_state['form_obs'], key='form_obs_input')
        enviar = st.form_submit_button("Salvar")

        if enviar:
            if valor > 0:
                data_convertida = pd.to_datetime(data)
                novo = pd.DataFrame([[data_convertida, tipo, categoria, valor, obs]], columns=df.columns)
                df = pd.concat([df, novo], ignore_index=True)
                salvar_dados(df)
                st.success("Lançamento salvo com sucesso!")
                st.rerun()
            else:
                st.error("Por favor, insira um valor maior que zero.")

if aba == "Relatório":
    st.subheader("Resumo Mensal")
    if df.empty or df['Data'].isnull().all():
        st.info("Nenhum dado disponível ainda.")
    else:
        df['Data'] = pd.to_datetime(df['Data'])
        meses_disponiveis = df['Data'].dropna().dt.to_period("M").astype(str).unique()
        
        if len(meses_disponiveis) == 0:
            st.info("Nenhum dado disponível ainda.")
        else:
            mes = st.selectbox("Escolha o mês", sorted(meses_disponiveis, reverse=True))
            df_mes = df[df['Data'].dt.to_period("M").astype(str) == mes].copy()
            
            total_receitas = df_mes[df_mes['Tipo'] == 'Receita']['Valor'].sum()
            total_despesas = df_mes[df_mes['Tipo'] == 'Despesa']['Valor'].sum()
            saldo = total_receitas - total_despesas

            col1, col2, col3 = st.columns(3)
            col1.metric("Receitas", f"R$ {total_receitas:.2f}")
            col2.metric("Despesas", f"R$ {total_despesas:.2f}")
            col3.metric("Saldo", f"R$ {saldo:.2f}", delta=f"{saldo:.2f}")

            st.subheader("Despesas por categoria")
            despesas_cat = df_mes[df_mes['Tipo'] == 'Despesa'].groupby("Categoria")['Valor'].sum()
            if not despesas_cat.empty:
                fig, ax = plt.subplots(figsize=(8, 6))
                despesas_cat.plot.pie(autopct='%1.1f%%', ax=ax, startangle=90)
                ax.set_ylabel("")
                st.pyplot(fig)
            else:
                st.info("Nenhuma despesa neste mês.")

            st.subheader("Lançamentos")
            df_display = df_mes.sort_values(by="Data", ascending=False).reset_index(drop=True)
            df_display['Data_Original'] = df_display['Data']
            df_display['Data'] = df_display['Data'].dt.strftime('%d/%m/%Y')
            st.dataframe(df_display[['Data', 'Tipo', 'Categoria', 'Valor', 'Observação']], use_container_width=True)

            if len(df_display) > 0:
                with st.expander("Editar / Excluir Lançamento"):
                    index_to_edit = st.number_input("Índice do lançamento (linha da tabela acima)", min_value=0, max_value=len(df_display)-1, step=1)
                    selected_row = df_display.iloc[index_to_edit]

                    with st.form("form_edit"):
                        tipo_edit = st.radio("Tipo", ["Receita", "Despesa"], index=["Receita", "Despesa"].index(selected_row['Tipo']))
                        categoria_edit = st.selectbox("Categoria", sorted(CATEGORIAS), index=sorted(CATEGORIAS).index(selected_row['Categoria']))
                        valor_edit = st.number_input("Valor (R$)", min_value=0.0, step=0.01, format="%.2f", value=float(selected_row['Valor']))
                        data_edit = st.date_input("Data", value=pd.to_datetime(selected_row['Data_Original']))
                        obs_edit = st.text_input("Observação", value=str(selected_row['Observação']) if pd.notna(selected_row['Observação']) else "")

                        col1, col2 = st.columns(2)
                        editar = col1.form_submit_button("Salvar Alterações")
                        excluir = col2.form_submit_button("Excluir Lançamento", type="primary")

                        if editar:
                            mask = (df['Data'] == selected_row['Data_Original']) & (df['Tipo'] == selected_row['Tipo']) & (df['Categoria'] == selected_row['Categoria']) & (df['Valor'] == selected_row['Valor'])
                            idx_original = df[mask].index[0]
                            
                            df.loc[idx_original] = [data_edit, tipo_edit, categoria_edit, valor_edit, obs_edit]
                            salvar_dados(df)
                            st.success("Alterações salvas!")
                            st.rerun()

                        if excluir:
                            mask = (df['Data'] == selected_row['Data_Original']) & (df['Tipo'] == selected_row['Tipo']) & (df['Categoria'] == selected_row['Categoria']) & (df['Valor'] == selected_row['Valor'])
                            idx_original = df[mask].index[0]
                            
                            df = df.drop(idx_original).reset_index(drop=True)
                            salvar_dados(df)
                            st.warning("Lançamento excluído.")
                            st.rerun()
