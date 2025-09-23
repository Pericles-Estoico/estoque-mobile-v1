import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from io import StringIO

# Configuração
st.set_page_config(
    page_title="📦 Estoque Mobile",
    page_icon="📦",
    layout="wide"
)

# URLs
SHEETS_URL = "https://docs.google.com/spreadsheets/d/1PpiMQingHf4llA03BiPIuPJPIZqul4grRU_emWDEK1o/export?format=csv"
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbzCxotWn-SXG52CXU7tNnd7KtBhx1uYwHr-ka2qWjswTcfj3QvHuA1VvDo-BL_fpg8U/exec"

# Função para carregar produtos
@st.cache_data(ttl=30)
def carregar_produtos():
    try:
        response = requests.get(SHEETS_URL, timeout=10)
        df = pd.read_csv(StringIO(response.text))
        
        # Verificar colunas mínimas
        if 'codigo' not in df.columns or 'nome' not in df.columns:
            st.error("Colunas básicas não encontradas")
            return pd.DataFrame()
        
        # Limpar dados
        df = df.dropna(subset=['codigo', 'nome'])
        
        # Garantir colunas numéricas
        if 'estoque_atual' in df.columns:
            df['estoque_atual'] = pd.to_numeric(df['estoque_atual'], errors='coerce').fillna(0)
        else:
            df['estoque_atual'] = 0
            
        if 'estoque_min' in df.columns:
            df['estoque_min'] = pd.to_numeric(df['estoque_min'], errors='coerce').fillna(0)
        else:
            df['estoque_min'] = 0
            
        if 'categoria' not in df.columns:
            df['categoria'] = 'Geral'
        
        return df
        
    except Exception as e:
        st.error(f"Erro: {str(e)}")
        return pd.DataFrame()

# Função para movimentar estoque
def movimentar_estoque(codigo, quantidade, tipo):
    try:
        data = {
            'codigo': str(codigo),
            'quantidade': int(quantidade),
            'tipo': tipo
        }
        
        response = requests.post(WEBHOOK_URL, json=data, timeout=15)
        result = response.json()
        
        if result.get('success'):
            return {'success': True, 'message': f'{tipo.title()} realizada!'}
        else:
            return {'success': False, 'error': result.get('error', 'Erro')}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

# Interface
st.title("📦 Estoque Mobile")

# Carregar dados
produtos_df = carregar_produtos()

if produtos_df.empty:
    st.error("❌ Erro ao carregar produtos")
    st.stop()

st.success(f"✅ {len(produtos_df)} produtos carregados")

# Busca simples
busca = st.text_input("🔍 Buscar produto:", placeholder="Digite código ou nome...")

if busca and len(busca) >= 2:
    # Filtrar produtos
    mask = (produtos_df['codigo'].astype(str).str.contains(busca, case=False, na=False) | 
            produtos_df['nome'].astype(str).str.contains(busca, case=False, na=False))
    produtos_encontrados = produtos_df[mask].head(5)
    
    if not produtos_encontrados.empty:
        st.write(f"**{len(produtos_encontrados)} produto(s) encontrado(s):**")
        
        for i, (idx, produto) in enumerate(produtos_encontrados.iterrows()):
            # Card do produto
            st.markdown(f"""
            **{produto['codigo']} - {produto['nome']}**  
            Categoria: {produto.get('categoria', 'N/A')}  
            Estoque: {int(produto['estoque_atual'])} unidades
            """)
            
            # Controles
            col1, col2 = st.columns(2)
            
            with col1:
                qtd_entrada = st.number_input("Entrada:", min_value=1, value=1, key=f"ent_{i}")
                if st.button("➕ Entrada", key=f"btn_ent_{i}"):
                    resultado = movimentar_estoque(produto['codigo'], qtd_entrada, 'entrada')
                    if resultado['success']:
                        st.success(f"✅ {resultado['message']}")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(f"❌ {resultado['error']}")
            
            with col2:
                max_saida = max(1, int(produto['estoque_atual']))
                qtd_saida = st.number_input("Saída:", min_value=1, max_value=max_saida, value=1, key=f"sai_{i}")
                if st.button("➖ Saída", key=f"btn_sai_{i}"):
                    resultado = movimentar_estoque(produto['codigo'], qtd_saida, 'saida')
                    if resultado['success']:
                        st.success(f"✅ {resultado['message']}")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(f"❌ {resultado['error']}")
            
            st.markdown("---")
    else:
        st.info("Nenhum produto encontrado")

# Resumo
st.subheader("📊 Resumo")
total_produtos = len(produtos_df)
estoque_total = produtos_df['estoque_atual'].sum()

col1, col2 = st.columns(2)
col1.metric("Total Produtos", total_produtos)
col2.metric("Estoque Total", f"{estoque_total:,.0f}")

# Atualizar
if st.button("🔄 Atualizar"):
    st.cache_data.clear()
    st.rerun()

st.caption(f"📦 Mobile • {datetime.now().strftime('%d/%m/%Y %H:%M')}")
