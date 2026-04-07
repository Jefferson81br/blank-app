import streamlit as st
from supabase import create_client, Client

# Conexão
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.title("Sistema de Gestão - 8 Unidades")

# Inicializa o estado de login se não existir
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.user_data = None

# --- TELA DE LOGIN ---
if not st.session_state.autenticado:
    with st.container():
        st.subheader("Login")
        usuario_input = st.text_input("Usuário")
        senha_input = st.text_input("Senha", type="password")
        
        if st.button("Entrar"):
            # Consulta o banco de dados pelo username
            res = supabase.table("usuarios").select("*").eq("username", usuario_input).execute()
            
            if res.data:
                user = res.data[0]
                # Verifica a senha (Atenção: aqui estamos comparando texto puro. 
                # No próximo passo usaremos criptografia/hash para segurança real)
                if senha_input == user['senha_hash']:
                    st.session_state.autenticado = True
                    st.session_state.user_data = user
                    st.rerun()
                else:
                    st.error("Senha incorreta.")
            else:
                st.error("Usuário não encontrado.")

# --- SISTEMA APÓS LOGIN ---
else:
    user = st.session_state.user_data
    st.sidebar.success(f"Conectado como: {user['nome']}")
    st.sidebar.write(f"Nível: {user['funcao'].capitalize()}")
    
    if st.sidebar.button("Sair"):
        st.session_state.autenticado = False
        st.session_state.user_data = None
        st.rerun()

    # O que aparece para cada um
    if user['funcao'] == 'admin':
        st.header("Painel Administrativo")
        # Aqui você colocará o formulário para CADASTRAR outros usuários
    
    elif user['funcao'] == 'gerente':
        st.header(f"Lançamento - Unidade {user['unidade_id']}")
