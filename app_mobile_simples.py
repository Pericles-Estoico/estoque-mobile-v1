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

# CSS Simples
st.markdown("""
<style>
.main .block-container { padding: 1rem; }
.produto-card { 
    background: #f8f9fa; 
    padding: 1rem; 
    border-radius: 8px; 
    margin: 0.5rem 0;
    border-left: 4px solid #007bff;
}
.alert-success { 
    background: #d4edda; 
    color: #155724; 
    padding: 1rem; 
    border-radius: 8px; 
    margin: 1rem 0;
}
.alert-error { 
    background: #f8d7da; 
    color: #721c24; 
    padding: 1rem; 
    border-radius: 8px; 
    margin: 1rem 0;
}
</style>
""", unsafe_allow_html=True)

# URLs
SHEETS_URL = "https://docs.google.com/spreadsheets/d/1PpiMQingHf4llA03BiPIuPJPIZqul4grRU_emWDEK1o/export?format=csv"
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbzCxotWn-SXG52CXU7tNnd7KtBhx1uYwHr-ka2qWjswTcfj3QvHuA1VvDo-BL_fpg8U/exec"

# Funções
@st.cache_data(ttl=30)
def carregar_produtos():
    try:
        response = requests.get(SHEETS_URL, timeout=10)
        df = pd.read_csv(StringIO(response.text))
        
        # Validar colunas obrigatórias
        required_cols = ['codigo', 'nome', 'categoria', 'estoque_atual', 'estoque_min']
        for col in required_cols:
            if col not in df.columns:
                st.error(f"Coluna '{col}' não encontrada na planilha")
                return pd.DataFrame()
        
        # Limpar dados
        df = df.dropna(subset=['codigo', 'nome'])
        df['estoque_atual'] = pd.to_numeric(df['estoque_atual'], errors='coerce').fillna(0)
        df['estoque_min'] = pd.to_numeric(df['estoque_min'], errors='coerce').fillna(0)
        
        # Verificar se existe coluna estoque_max (opcional)
        if 'estoque_max' in df.columns:
            df['estoque_max'] = pd.to_numeric(df['estoque_max'], errors='coerce').fillna(0)
            df['falta_max'] = (df['estoque_max'] - df['estoque_atual']).clip(lower=0)
        else:
            df['estoque_max'] = 0
            df['falta_max'] = 0
        
        # Calcular falta para mínimo
        df['falta_min'] = (df['estoque_min'] - df['estoque_atual']).clip(lower=0)
        
        return df
        
    except Exception as e:
        st.error(f"Erro ao carregar planilha: {str(e)}")
        return pd.DataFrame()

def buscar_produtos(termo, df):
    if not termo or df.empty:
        return []
    
    termo = termo.lower().strip()
    resultados = []
    
    for _, produto in df.iterrows():
        codigo = str(produto['codigo']).lower()
        nome = str(produto['nome']).lower()
        
        if termo in codigo or termo in nome:
            resultados.append({
                'codigo': produto['codigo'],
                'nome': produto['nome'],
                'categoria': produto['categoria'],
                'estoque_atual': int(produto['estoque_atual']),
                'estoque_min': int(produto['estoque_min'])
            })
    
    return resultados[:5]

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
            return {
                'success': True,
                'message': f'{tipo.title()} realizada com sucesso!',
                'novo_estoque': result.get('novoEstoque', 0)
            }
        else:
            return {
                'success': False,
                'error': result.get('error', 'Erro desconhecido')
            }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

# Interface
st.title("📦 Controle de Estoque Mobile")

# Carregar dados
produtos_df = carregar_produtos()

if produtos_df.empty:
    st.error("Não foi possível carregar os produtos")
    st.stop()

st.success(f"✅ {len(produtos_df)} produtos carregados")

# Filtro por categoria
categorias = ['Todas'] + sorted(produtos_df['categoria'].unique().tolist())
categoria_selecionada = st.selectbox("📂 Selecionar categoria:", categorias)

# Filtrar produtos por categoria
if categoria_selecionada == 'Todas':
    produtos_filtrados = produtos_df
else:
    produtos_filtrados = produtos_df[produtos_df['categoria'] == categoria_selecionada]

st.info(f"📦 {len(produtos_filtrados)} produtos na categoria '{categoria_selecionada}'")

# Busca
busca = st.text_input("🔍 Buscar produto:", placeholder="Digite código ou nome...")

if busca and len(busca) >= 2:
    resultados = buscar_produtos(busca, produtos_filtrados)
    
    if resultados:
        st.write(f"**{len(resultados)} produto(s) encontrado(s):**")
        
        for i, produto in enumerate(resultados):
            # Card do produto
            st.markdown(f"""
            <div class="produto-card">
                <strong>{produto['codigo']} - {produto['nome']}</strong><br>
                <small>{produto['categoria']}</small><br>
                <strong>Estoque atual: {produto['estoque_atual']} un</strong><br>
                <small>Estoque mínimo: {produto['estoque_min']} un</small>
            </div>
            """, unsafe_allow_html=True)
            
            # Controles
            col1, col2 = st.columns(2)
            
            with col1:
                qtd_entrada = st.number_input(
                    "Qtd Entrada:",
                    min_value=1,
                    value=1,
                    key=f"entrada_{i}"
                )
                
                if st.button(f"➕ Entrada", key=f"btn_entrada_{i}"):
                    resultado = movimentar_estoque(produto['codigo'], qtd_entrada, 'entrada')
                    
                    if resultado['success']:
                        st.markdown(f'<div class="alert-success">✅ {resultado["message"]}<br>Novo estoque: {resultado["novo_estoque"]}</div>', unsafe_allow_html=True)
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.markdown(f'<div class="alert-error">❌ {resultado["error"]}</div>', unsafe_allow_html=True)
            
            with col2:
                qtd_saida = st.number_input(
                    "Qtd Saída:",
                    min_value=1,
                    max_value=max(1, produto['estoque_atual']),
                    value=1,
                    key=f"saida_{i}"
                )
                
                if st.button(f"➖ Saída", key=f"btn_saida_{i}"):
                    if qtd_saida > produto['estoque_atual']:
                        st.markdown('<div class="alert-error">❌ Quantidade maior que estoque!</div>', unsafe_allow_html=True)
                    else:
                        resultado = movimentar_estoque(produto['codigo'], qtd_saida, 'saida')
                        
                        if resultado['success']:
                            st.markdown(f'<div class="alert-success">✅ {resultado["message"]}<br>Novo estoque: {resultado["novo_estoque"]}</div>', unsafe_allow_html=True)
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.markdown(f'<div class="alert-error">❌ {resultado["error"]}</div>', unsafe_allow_html=True)
            
            st.markdown("---")
    
    else:
        st.info("Nenhum produto encontrado")

elif busca and len(busca) < 2:
    st.info("Digite pelo menos 2 caracteres")

# Resumo
st.subheader("📊 Resumo")
total_produtos = len(produtos_df)
estoque_total = produtos_df['estoque_atual'].sum()
produtos_baixos = len(produtos_df[produtos_df['estoque_atual'] <= produtos_df['estoque_min']])

col1, col2, col3 = st.columns(3)
col1.metric("Produtos", total_produtos)
col2.metric("Estoque Total", f"{estoque_total:,.0f}")
col3.metric("Estoque Baixo", produtos_baixos)

# Relatórios Simples
st.subheader("📊 Relatórios Rápidos")

col1, col2 = st.columns(2)

with col1:
    if st.button("📋 Ver Estoque Baixo"):
        baixo = produtos_df[produtos_df['estoque_atual'] <= produtos_df['estoque_min']]
        if not baixo.empty:
            st.write("**Produtos com Estoque Baixo:**")
            for _, produto in baixo.iterrows():
                falta = max(0, produto['estoque_min'] - produto['estoque_atual'])
                st.write(f"• **{produto['codigo']}** - {produto['nome']}")
                st.write(f"  Atual: {produto['estoque_atual']} | Mín: {produto['estoque_min']} | Falta: {falta}")
        else:
            st.success("✅ Nenhum produto com estoque baixo!")

with col2:
    if st.button("🔄 Atualizar Dados"):
        st.cache_data.clear()
        st.rerun()

st.markdown("---")
st.caption(f"📦 Sistema Mobile • {datetime.now().strftime('%d/%m/%Y %H:%M')}")
