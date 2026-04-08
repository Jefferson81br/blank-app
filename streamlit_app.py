import streamlit as st
from supabase import create_client, Client
import database_utils as db  # Importa suas funções de banco
import auth_utils as auth    # Importa sua lógica de senha

# 1. Configuração da Conexão
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# 2. Inicialização do Estado da Sessão
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.user_data = None

if 'pagina_ativa' not in st.session_state:
    st.session_state.pagina_ativa = "📊 Dashboard"

# --- FLUXO DE TELAS ---

if not st.session_state.autenticado:
    # TELA DE LOGIN
    st.title("💊 Farma Gestor 1.0")
    
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
                    # Fallback para senhas em texto puro (Admin inicial)
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
    
    # --- BARRA LATERAL (SIDEBAR) ---
    st.sidebar.title(f"Olá, {user['nome']}")
    st.sidebar.info(f"Nível: {user['funcao'].upper()}")

    # Expander de Minha Conta
    with st.sidebar.expander("⚙️ Minha Conta"):
        with st.form("form_troca_senha_propria"):
            st.write("Alterar Minha Senha")
            senha_atual = st.text_input("Senha Atual", type="password")
            nova_senha = st.text_input("Nova Senha", type="password")
            confirmar = st.form_submit_button("Atualizar Senha", use_container_width=True)
            
            if confirmar:
                if auth.verificar_senha(senha_atual, user['senha_hash']) or senha_atual == user['senha_hash']:
                    if nova_senha:
                        novo_hash = auth.gerar_hash_senha(nova_senha)
                        db.atualizar_senha_usuario(supabase, user['id'], novo_hash)
                        st.success("Senha alterada!")
                    else:
                        st.error("Digite a nova senha.")
                else:
                    st.error("Senha atual incorreta.")

    st.sidebar.markdown("---")
    st.sidebar.write("Navegação")

    # Botões de Navegação (Homogêneos)
    if st.sidebar.button("📊 Dashboard", use_container_width=True):
        st.session_state.pagina_ativa = "📊 Dashboard"
        st.rerun()

    if user['funcao'] == 'admin':
        if st.sidebar.button("👥 Consultar Usuários", use_container_width=True):
            st.session_state.pagina_ativa = "👥 Consultar Usuários"
            st.rerun()
        if st.sidebar.button("➕ Adicionar Usuário", use_container_width=True):
            st.session_state.pagina_ativa = "➕ Adicionar Usuário"
            st.rerun()
    
    if user['funcao'] == 'gerente':
        if st.sidebar.button("📝 Lançamento Diário", use_container_width=True):
            st.session_state.pagina_ativa = "📝 Lançamento Diário"
            st.rerun()

    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Sair", use_container_width=True):
        st.session_state.autenticado = False
        st.session_state.user_data = None
        st.session_state.pagina_ativa = "📊 Dashboard"
        st.rerun()

    # --- LÓGICA DE RENDERIZAÇÃO DAS TELAS ---
    escolha = st.session_state.pagina_ativa

    if escolha == "📊 Dashboard":
        st.title("📊 Dashboard Executivo")
        st.write(f"Bem-vindo ao centro de controle, {user['nome']}.")
        st.info("Os indicadores de vendas serão exibidos aqui.")

    elif escolha == "➕ Adicionar Usuário":
        st.title("➕ Cadastrar Novo Usuário")
        with st.form("form_cadastro_usuario", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                nome = st.text_input("Nome")
                email = st.text_input("E-mail")
                novo_usuario = st.text_input("Login")
            with col2:
                sobrenome = st.text_input("Sobrenome")
                loja = st.selectbox("Unidade", [1, 2, 3, 4, 5, 6, 7, 8, "N/A"])
                nova_senha_cad = st.text_input("Senha Inicial", type="password")
            
            funcao_cad = st.selectbox("Nível", ["gerente", "proprietario", "financeiro", "admin"])
            if st.form_submit_button("Finalizar Cadastro", use_container_width=True):
                if nome and novo_usuario and nova_senha_cad:
                    hash_cad = auth.gerar_hash_senha(nova_senha_cad)
                    dados = {
                        "nome": nome, "sobrenome": sobrenome, "email": email,
                        "username": novo_usuario, "senha_hash": hash_cad,
                        "funcao": funcao_cad, "unidade_id": loja if isinstance(loja, int) else None
                    }
                    db.cadastrar_usuario(supabase, dados)
                    st.success("Usuário criado!")
                else:
                    st.warning("Preencha os campos obrigatórios.")

    elif escolha == "👥 Consultar Usuários":
        st.title("👥 Gestão de Usuários")
        usuarios_res = db.buscar_todos_usuarios(supabase)
        if usuarios_res and usuarios_res.data:
            for u in usuarios_res.data:
                with st.expander(f"{u['nome']} {u['sobrenome'] or ''} (@{u['username']})"):
                    c1, c2, c3 = st.columns([2, 1, 1])
                    with c1:
                        st.write(f"Função: {u['funcao']} | Loja: {u['unidade_id'] or 'Admin'}")
                    with c2:
                        pop = st.popover("🔑 Resetar")
                        with pop:
                            nova_p = st.text_input("Nova senha", type="password", key=f"p_{u['id']}")
                            if st.button("Confirmar", key=f"b_{u['id']}"):
                                db.atualizar_senha_usuario(supabase, u['id'], auth.gerar_hash_senha(nova_p))
                                st.success("Resetado!")
                    with c3:
                        if st.button("Excluir", key=f"d_{u['id']}", use_container_width=True):
                            supabase.table("usuarios").delete().eq("id", u['id']).execute()
                            st.rerun()
