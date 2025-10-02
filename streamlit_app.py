import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from io import StringIO

# Configuração
st.set_page_config(
    page_title="📦 Estoque Mobile - Silva Holding",
    page_icon="📦",
    layout="wide"
)

# URLs
SHEETS_URL = "https://docs.google.com/spreadsheets/d/1PpiMQingHf4llA03BiPIuPJPIZqul4grRU_emWDEK1o/export?format=csv"
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbxDAmK8RaizGAJMBbIr_urPVP-REsD6zVZAFQI6tQPydWtxllXY2ccNPpEpITFXZ9hp/exec"

# Função para carregar produtos
@st.cache_data(ttl=30)
def carregar_produtos():
    try:
        response = requests.get(SHEETS_URL, timeout=10)
        response.raise_for_status()
        
        csv_data = StringIO(response.text)
        df = pd.read_csv(csv_data)
        
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        return pd.DataFrame()

# Função para movimentar estoque
def movimentar_estoque(codigo, quantidade, tipo, colaborador):
    try:
        dados = {
            'codigo': codigo,
            'quantidade': int(quantidade),
            'tipo': tipo,
            'colaborador': colaborador
        }
        
        response = requests.post(
            WEBHOOK_URL,
            json=dados,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            resultado = response.json()
            return resultado
        else:
            return {'success': False, 'error': f'Erro HTTP: {response.status_code}'}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

# Interface com logo e centralização
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    try:
        st.image("logo_silva.jpeg", width=200)
    except:
        st.title("🦁 SILVA HOLDING")
    
    st.markdown("""
    <div style="text-align: center;">
        <h2>📦 Estoque Mobile</h2>
        <p style="font-style: italic; color: #666; font-size: 0.9em;">
        "Se parar para sentir o perfume das rosas, vem um caminhão e te atropela"
        </p>
    </div>
    """, unsafe_allow_html=True)

# Carregar dados
produtos_df = carregar_produtos()

if produtos_df.empty:
    st.error("❌ Não foi possível carregar os produtos")
    st.stop()

st.success(f"✅ {len(produtos_df)} produtos carregados")

# Controles centralizados
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    # Seleção de colaborador
    colaboradores = ['Pericles', 'Maria', 'Camila', 'Cris Vanti', 'Stella', 'Raquel']
    colaborador_selecionado = st.selectbox("👤 Colaborador:", colaboradores)

    # Filtro por categoria
    if 'categoria' in produtos_df.columns:
        categorias = ['Todas'] + sorted(produtos_df['categoria'].unique().tolist())
        categoria_selecionada = st.selectbox("📂 Categoria:", categorias)
        
        if categoria_selecionada == 'Todas':
            produtos_filtrados = produtos_df
        else:
            produtos_filtrados = produtos_df[produtos_df['categoria'] == categoria_selecionada]
        
        st.info(f"📦 {len(produtos_filtrados)} produtos na categoria '{categoria_selecionada}'")
    else:
        produtos_filtrados = produtos_df

    # Busca
    busca = st.text_input("🔍 Buscar produto:", placeholder="Digite código ou nome...")

if busca and len(busca) >= 2:
    # Filtrar produtos (dentro da categoria selecionada)
    produtos_encontrados = produtos_filtrados[
        produtos_filtrados['codigo'].str.contains(busca, case=False, na=False) |
        produtos_filtrados['nome'].str.contains(busca, case=False, na=False)
    ]
    
    if not produtos_encontrados.empty:
        st.write(f"**{len(produtos_encontrados)} produto(s) encontrado(s):**")
        
        for i, (idx, produto) in enumerate(produtos_encontrados.iterrows()):
            # Layout compacto - só código e estoque
            st.markdown(f"**{produto['codigo']}** | {int(produto['estoque_atual'])} unidades")
            
            # Controles compactos em uma linha
            col1, col2, col3, col4 = st.columns([1, 2, 1, 2])
            
            with col1:
                qtd_entrada = st.number_input("", min_value=1, value=1, key=f"ent_{i}")
            with col2:
                if st.button("➕ Entrada", key=f"btn_ent_{i}"):
                    resultado = movimentar_estoque(produto['codigo'], qtd_entrada, 'entrada', colaborador_selecionado)
                    if resultado['success']:
                        st.success(f"✅ {resultado['message']}")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(f"❌ {resultado['error']}")
            
            with col3:
                max_saida = max(1, int(produto['estoque_atual']))
                qtd_saida = st.number_input("", min_value=1, max_value=max_saida, value=1, key=f"sai_{i}")
            with col4:
                if st.button("➖ Saída", key=f"btn_sai_{i}"):
                    resultado = movimentar_estoque(produto['codigo'], qtd_saida, 'saida', colaborador_selecionado)
                    if resultado['success']:
                        st.success(f"✅ {resultado['message']}")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(f"❌ {resultado['error']}")
            
            st.markdown("---")
    else:
        st.warning("❌ Nenhum produto encontrado")
elif not busca:
    st.info("💡 Digite pelo menos 2 caracteres para buscar")

# Produtos com estoque baixo (acesso rápido)
st.subheader("⚠️ Estoque Baixo")
produtos_baixos = produtos_filtrados[produtos_filtrados['estoque_atual'] <= produtos_filtrados['estoque_min']]

if not produtos_baixos.empty:
    st.warning(f"🚨 {len(produtos_baixos)} produto(s) com estoque baixo!")
    
    if st.button("👁️ Ver Produtos com Estoque Baixo"):
        for i, (idx, produto) in enumerate(produtos_baixos.head(3).iterrows()):
            st.markdown(f"""
            <div style="background: #fff3cd; padding: 0.8rem; border-radius: 6px; margin: 0.3rem 0; border-left: 4px solid #ffc107;">
                <strong>{produto['codigo']}</strong><br>
                <small>📦 Atual: {int(produto['estoque_atual'])} | Mínimo: {int(produto['estoque_min'])}</small>
            </div>
            """, unsafe_allow_html=True)
else:
    st.success("✅ Nenhum produto com estoque baixo!")

# Resumo
st.subheader("📊 Resumo")
total_produtos = len(produtos_df)
estoque_total = produtos_df['estoque_atual'].sum()

col1, col2 = st.columns(2)
col1.metric("Total Produtos", total_produtos)
col2.metric("Estoque Total", f"{estoque_total:.0f}")

# Atualizar
if st.button("🔄 Atualizar"):
    st.cache_data.clear()
    st.rerun()
