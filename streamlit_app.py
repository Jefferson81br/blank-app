import streamlit as st
from supabase import create_client, Client
import database_utils as db  # Importa suas funções de banco
import auth_utils as auth    # Importa sua lógica de senha

# 1. Configuração da Conexão (Puxando dos Secrets do Streamlit Cloud)
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# 2. Inicialização do Estado da Sessão
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.user_data = None

# --- FLUXO DE TELAS ---

if not st.session_state.autenticado:
    # TELA DE LOGIN
    st.title("💊 Gestão de Farmácias - Grupo")
    
    with st.container():
        user_input = st.text_input("Usuário")
        pass_input = st.text_input("Senha", type="password")
        
        if st.button("Entrar", use_container_width=True):
            res = db.buscar_usuario(supabase, user_input)
            
            if res and res.data:
                user = res.data[0]
                # Verifica a senha usando o módulo de segurança
                if auth.verificar_senha(pass_input, user['senha_hash']):
                    st.session_state.autenticado = True
                    st.session_state.user_data = user
                    st.rerun()
                else:
                    st.error("Senha incorreta.")
            else:
                st.error("Usuário não encontrado.")

else:
    # SISTEMA APÓS LOGIN
    user = st.session_state.user_data
    
    # Barra Lateral Comum
    st.sidebar.title(f"Olá, {user['nome']}")
    st.sidebar.info(f"Nível: {user['funcao'].upper()}")
    
    if st.sidebar.button("Sair"):
        st.session_state.autenticado = False
        st.session_state.user_data = None
        st.rerun()

    # Roteamento por Nível de Acesso
    if user['funcao'] == 'admin':
        st.header("🛡️ Painel do Administrador")
        # Aqui você pode chamar uma função de outro arquivo: admin_view.render(supabase)
        st.write("Bem-vindo ao controle central. Aqui você gerencia usuários e lojas.")
        
    elif user['funcao'] == 'gerente':
        st.header(f"🏪 Lançamento Diário - Unidade {user['unidade_id']}")
        # Aqui você chamaria: gerente_view.render(supabase, user['unidade_id'])
        
    elif user['funcao'] == 'proprietario':
        st.header("📊 Dashboard Executivo")
        # Visão de BI para o dono das 8 lojas
