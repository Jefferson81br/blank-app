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
                    # Caso a senha no banco ainda seja texto puro (como o seu admin atual)
                    if pass_input == user['senha_hash']:
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
        st.subheader("🆕 Cadastro de Novo Usuário")
        
        with st.form("form_cadastro_usuario", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                nome = st.text_input("Nome")
                email = st.text_input("E-mail")
                novo_usuario = st.text_input("Login (Username)")
            with col2:
                sobrenome = st.text_input("Sobrenome")
                # Dropdown para as 8 lojas
                loja = st.selectbox("Unidade/Loja", [1, 2, 3, 4, 5, 6, 7, 8, "Nenhuma (Admin/Proprietário)"])
                nova_senha = st.text_input("Senha Inicial", type="password")
            
            funcao = st.selectbox("Nível de Acesso", ["gerente", "proprietario", "financeiro", "admin"])
            
            botao_cadastrar = st.form_submit_button("Finalizar Cadastro")
            
            if botao_cadastrar:
                if nome and novo_usuario and nova_senha and email:
                    # 1. Gerar o Hash da senha antes de enviar para o banco
                    senha_protegida = auth.gerar_hash_senha(nova_senha)
                    
                    # 2. Preparar os dados
                    dados_usuario = {
                        "nome": f"{nome} {sobrenome}",
                        "email": email,
                        "username": novo_usuario,
                        "senha_hash": senha_protegida, # Senha já criptografada
                        "funcao": funcao,
                        "unidade_id": loja if isinstance(loja, int) else None
                    }
                    
                    # 3. Enviar para o Supabase (usando nossa função do database_utils)
                    try:
                        db.cadastrar_usuario(supabase, dados_usuario)
                        st.success(f"Usuário {novo_usuario} cadastrado com segurança!")
                    except Exception as e:
                        st.error(f"Erro ao cadastrar no banco: {e}")
                else:
                    st.warning("Por favor, preencha todos os campos obrigatórios.")
        
    elif user['funcao'] == 'gerente':
        st.header(f"🏪 Lançamento Diário - Unidade {user['unidade_id']}")
        # Aqui você chamaria: gerente_view.render(supabase, user['unidade_id'])
        
    elif user['funcao'] == 'proprietario':
        st.header("📊 Dashboard Executivo")
        # Visão de BI para o dono das 8 lojas
