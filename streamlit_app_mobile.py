import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import json
from io import StringIO

# Configuração Mobile-First
st.set_page_config(
    page_title="📦 Estoque Mobile",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS Mobile Otimizado
st.markdown("""
<style>
    .main .block-container {
        padding: 0.5rem;
        max-width: 100%;
    }
    
    .mobile-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem 1rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 1rem;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    
    .mobile-header h1 {
        font-size: 1.6rem;
        margin: 0;
        font-weight: 700;
    }
    
    .mobile-header p {
        font-size: 0.9rem;
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
    }
    
    .produto-card {
        background: white;
        padding: 1rem;
        border-radius: 12px;
        margin: 0.75rem 0;
        border-left: 4px solid #007bff;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        transition: transform 0.2s ease;
    }
    
    .produto-card:active {
        transform: scale(0.98);
    }
    
    .produto-nome {
        font-weight: 600;
        font-size: 1rem;
        color: #333;
        margin: 0 0 0.5rem 0;
    }
    
    .produto-info {
        font-size: 0.85rem;
        color: #666;
        margin: 0;
    }
    
    .estoque-info {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 0.5rem;
    }
    
    .estoque-atual {
        font-size: 1.2rem;
        font-weight: 700;
        color: #28a745;
    }
    
    .estoque-baixo {
        color: #dc3545;
    }
    
    .btn-container {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0.5rem;
        margin-top: 1rem;
    }
    
    .stButton > button {
        width: 100%;
        padding: 0.75rem;
        font-size: 0.9rem;
        font-weight: 600;
        border-radius: 8px;
        border: none;
        transition: all 0.2s ease;
    }
    
    .entrada-btn {
        background: linear-gradient(135deg, #28a745, #20c997) !important;
        color: white !important;
    }
    
    .saida-btn {
        background: linear-gradient(135deg, #dc3545, #c82333) !important;
        color: white !important;
    }
    
    .stButton > button:active {
        transform: translateY(2px);
    }
    
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 0.5rem;
        margin-bottom: 1rem;
    }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        border-left: 4px solid;
    }
    
    .metric-number {
        font-size: 1.5rem;
        font-weight: 700;
        margin: 0;
    }
    
    .metric-label {
        font-size: 0.7rem;
        color: #666;
        margin: 0.25rem 0 0 0;
        text-transform: uppercase;
    }
    
    .metric-total { border-color: #17a2b8; }
    .metric-ok { border-color: #28a745; }
    .metric-baixo { border-color: #dc3545; }
    
    .search-container {
        background: white;
        padding: 1rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    .alert-success {
        background: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    
    .alert-error {
        background: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #dc3545;
        margin: 1rem 0;
    }
    
    .footer-mobile {
        text-align: center;
        padding: 1.5rem;
        color: #666;
        font-size: 0.8rem;
        margin-top: 2rem;
        border-top: 1px solid #eee;
    }
    
    /* Responsividade */
    @media (max-width: 480px) {
        .btn-container {
            grid-template-columns: 1fr;
        }
        
        .metric-grid {
            grid-template-columns: repeat(2, 1fr);
        }
    }
</style>
""", unsafe_allow_html=True)

# URLs e Configurações
SHEETS_URL = "https://docs.google.com/spreadsheets/d/1PpiMQingHf4llA03BiPIuPJPIZqul4grRU_emWDEK1o/export?format=csv"
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbwguXwfLsByVz0peA5VSq2sM-74kxvvlPFym6zb8R2Mc94CYwAnb1lGstRmv7lmHkc5/exec"

# Funções
@st.cache_data(ttl=30)
def carregar_produtos():
    """Carrega produtos da planilha Google Sheets"""
    try:
        response = requests.get(SHEETS_URL, timeout=10)
        response.raise_for_status()
        
        df = pd.read_csv(StringIO(response.text))
        
        # Validar colunas obrigatórias
        required_cols = ['codigo', 'nome', 'categoria', 'estoque_atual', 'estoque_min']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            st.error(f"❌ Colunas faltando na planilha: {missing_cols}")
            return pd.DataFrame()
        
        # Limpar e converter dados
        df = df.dropna(subset=['codigo', 'nome'])
        df['estoque_atual'] = pd.to_numeric(df['estoque_atual'], errors='coerce').fillna(0)
        df['estoque_min'] = pd.to_numeric(df['estoque_min'], errors='coerce').fillna(0)
        
        return df
        
    except Exception as e:
        st.error(f"❌ Erro ao carregar planilha: {str(e)}")
        return pd.DataFrame()

def buscar_produtos(termo, df):
    """Busca produtos por código ou nome"""
    if not termo or df.empty:
        return []
    
    termo = termo.lower().strip()
    resultados = []
    
    for _, produto in df.iterrows():
        codigo = str(produto['codigo']).lower()
        nome = str(produto['nome']).lower()
        
        # Busca por código ou nome
        if termo in codigo or termo in nome:
            resultados.append({
                'codigo': produto['codigo'],
                'nome': produto['nome'],
                'categoria': produto['categoria'],
                'estoque_atual': int(produto['estoque_atual']),
                'estoque_min': int(produto['estoque_min'])
            })
    
    # Ordenar por relevância (código primeiro, depois nome)
    resultados.sort(key=lambda x: (
        0 if termo in str(x['codigo']).lower() else 1,
        str(x['codigo']).lower()
    ))
    
    return resultados[:8]  # Máximo 8 resultados

def movimentar_estoque(codigo, quantidade, tipo):
    """Envia movimentação para Google Apps Script"""
    try:
        data = {
            'codigo': str(codigo),
            'quantidade': int(quantidade),
            'tipo': tipo
        }
        
        response = requests.post(WEBHOOK_URL, json=data, timeout=15)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get('success'):
            return {
                'success': True,
                'message': f'✅ {tipo.title()} realizada com sucesso!',
                'details': f'Produto: {result.get("produto", "")}\nEstoque anterior: {result.get("estoqueAnterior", "")}\nNovo estoque: {result.get("novoEstoque", "")}'
            }
        else:
            return {
                'success': False,
                'error': result.get('error', 'Erro desconhecido no servidor')
            }
        
    except requests.exceptions.Timeout:
        return {'success': False, 'error': 'Timeout - Tente novamente'}
    except requests.exceptions.RequestException as e:
        return {'success': False, 'error': f'Erro de conexão: {str(e)}'}
    except Exception as e:
        return {'success': False, 'error': f'Erro inesperado: {str(e)}'}

# Interface Principal
st.markdown("""
<div class="mobile-header">
    <h1>📦 Controle de Estoque</h1>
    <p>Entrada e Saída Mobile</p>
</div>
""", unsafe_allow_html=True)

# Carregar dados
with st.spinner("📊 Carregando produtos..."):
    produtos_df = carregar_produtos()

if produtos_df.empty:
    st.error("❌ Não foi possível carregar os produtos. Verifique a conexão.")
    st.stop()

# Status da conexão
st.success(f"✅ {len(produtos_df)} produtos carregados • {datetime.now().strftime('%H:%M:%S')}")

# Métricas rápidas
total_produtos = len(produtos_df)
estoque_total = produtos_df['estoque_atual'].sum()
produtos_baixos = len(produtos_df[produtos_df['estoque_atual'] <= produtos_df['estoque_min']])

st.markdown(f"""
<div class="metric-grid">
    <div class="metric-card metric-total">
        <div class="metric-number">{total_produtos}</div>
        <div class="metric-label">Produtos</div>
    </div>
    <div class="metric-card metric-ok">
        <div class="metric-number">{estoque_total:,.0f}</div>
        <div class="metric-label">Unidades</div>
    </div>
    <div class="metric-card metric-baixo">
        <div class="metric-number">{produtos_baixos}</div>
        <div class="metric-label">Baixo</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Navegação por abas
tab1, tab2 = st.tabs(["🔍 Movimentar", "📊 Resumo"])

with tab1:
    # Campo de busca
    st.markdown('<div class="search-container">', unsafe_allow_html=True)
    
    busca = st.text_input(
        "🔍 Buscar produto:",
        placeholder="Digite código (ex: P001) ou nome do produto...",
        key="busca_produto",
        help="Digite pelo menos 2 caracteres para buscar"
    )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Resultados da busca
    if busca and len(busca) >= 2:
        resultados = buscar_produtos(busca, produtos_df)
        
        if resultados:
            st.markdown(f"### 📦 {len(resultados)} produto(s) encontrado(s):")
            
            for i, produto in enumerate(resultados):
                # Determinar cor do estoque
                estoque_class = "estoque-atual"
                if produto['estoque_atual'] <= produto['estoque_min']:
                    estoque_class = "estoque-baixo"
                
                st.markdown(f"""
                <div class="produto-card">
                    <div class="produto-nome">{produto['codigo']} - {produto['nome']}</div>
                    <div class="produto-info">{produto['categoria']}</div>
                    <div class="estoque-info">
                        <span>Estoque atual:</span>
                        <span class="{estoque_class}">{produto['estoque_atual']} un</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Controles de movimentação
                col1, col2 = st.columns(2)
                
                with col1:
                    # Entrada
                    qtd_entrada = st.number_input(
                        "Qtd Entrada:",
                        min_value=1,
                        max_value=9999,
                        value=1,
                        key=f"entrada_{produto['codigo']}_{i}",
                        help="Quantidade para dar entrada"
                    )
                    
                    if st.button(
                        f"➕ Entrada ({qtd_entrada})",
                        key=f"btn_entrada_{produto['codigo']}_{i}",
                        use_container_width=True,
                        type="primary"
                    ):
                        with st.spinner("Processando entrada..."):
                            resultado = movimentar_estoque(
                                produto['codigo'],
                                qtd_entrada,
                                'entrada'
                            )
                        
                        if resultado['success']:
                            st.markdown(f'<div class="alert-success">{resultado["message"]}<br><small>{resultado["details"]}</small></div>', unsafe_allow_html=True)
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.markdown(f'<div class="alert-error">❌ Erro: {resultado["error"]}</div>', unsafe_allow_html=True)
                
                with col2:
                    # Saída
                    qtd_saida = st.number_input(
                        "Qtd Saída:",
                        min_value=1,
                        max_value=produto['estoque_atual'] if produto['estoque_atual'] > 0 else 1,
                        value=1,
                        key=f"saida_{produto['codigo']}_{i}",
                        help="Quantidade para dar saída"
                    )
                    
                    if st.button(
                        f"➖ Saída ({qtd_saida})",
                        key=f"btn_saida_{produto['codigo']}_{i}",
                        use_container_width=True,
                        type="secondary"
                    ):
                        if qtd_saida > produto['estoque_atual']:
                            st.markdown('<div class="alert-error">❌ Quantidade maior que estoque disponível!</div>', unsafe_allow_html=True)
                        else:
                            with st.spinner("Processando saída..."):
                                resultado = movimentar_estoque(
                                    produto['codigo'],
                                    qtd_saida,
                                    'saida'
                                )
                            
                            if resultado['success']:
                                st.markdown(f'<div class="alert-success">{resultado["message"]}<br><small>{resultado["details"]}</small></div>', unsafe_allow_html=True)
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.markdown(f'<div class="alert-error">❌ Erro: {resultado["error"]}</div>', unsafe_allow_html=True)
                
                st.markdown("---")
        
        elif len(busca) >= 2:
            st.info("🔍 Nenhum produto encontrado com esse termo")
    
    elif busca and len(busca) < 2:
        st.info("💡 Digite pelo menos 2 caracteres para buscar")

with tab2:
    st.subheader("📊 Resumo do Estoque")
    
    # Produtos com estoque baixo
    produtos_criticos = produtos_df[produtos_df['estoque_atual'] <= produtos_df['estoque_min']]
    
    if len(produtos_criticos) > 0:
        st.markdown("### ⚠️ Produtos com Estoque Baixo:")
        
        for _, produto in produtos_criticos.iterrows():
            faltante = max(0, produto['estoque_min'] - produto['estoque_atual'])
            
            st.markdown(f"""
            <div style='background: #fff3cd; padding: 1rem; border-radius: 8px; margin: 0.5rem 0; border-left: 4px solid #ffc107;'>
                <strong>{produto['codigo']} - {produto['nome']}</strong><br>
                <small>Estoque: {produto['estoque_atual']} | Mínimo: {produto['estoque_min']} | Faltam: {faltante}</small>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("✅ Todos os produtos com estoque adequado!")
    
    # Resumo por categoria
    if not produtos_df.empty:
        st.markdown("### 📋 Resumo por Categoria:")
        
        categoria_resumo = produtos_df.groupby('categoria').agg({
            'codigo': 'count',
            'estoque_atual': 'sum'
        }).reset_index()
        categoria_resumo.columns = ['Categoria', 'Produtos', 'Estoque Total']
        
        st.dataframe(categoria_resumo, use_container_width=True, hide_index=True)

# Botão de atualização
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    if st.button("🔄 Atualizar Dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

with col2:
    if st.button("📊 Ver Dashboard Completo", use_container_width=True):
        st.info("💡 Acesse o dashboard desktop para relatórios completos e gráficos detalhados")

# Footer
st.markdown("""
<div class="footer-mobile">
    <strong>📦 Sistema de Estoque Mobile v1.0</strong><br>
    Entrada e Saída Simplificada<br>
    <small>Sincronizado com Google Sheets • {}</small>
</div>
""".format(datetime.now().strftime("%d/%m/%Y %H:%M")), unsafe_allow_html=True)
