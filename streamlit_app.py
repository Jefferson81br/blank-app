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
    
    # Barra Lateral
    st.sidebar.title(f"Olá, {user['nome']}")
    st.sidebar.info(f"Nível: {user['funcao'].upper()}")

    # Na Sidebar, para todos os usuários
    with st.sidebar.expander("⚙️ Minha Conta"):
        with st.form("form_troca_senha_propria"):
            st.write("Alterar Senha")
            senha_atual = st.text_input("Senha Atual", type="password")
            nova_senha = st.text_input("Nova Senha", type="password")
            confirmar = st.form_submit_button("Atualizar Senha")
            
            if confirmar:
                # 1. Verificar se a senha atual está correta
                if auth.verificar_senha(senha_atual, user['senha_hash']):
                    if nova_senha:
                        # 2. Gerar novo hash e salvar
                        novo_hash = auth.gerar_hash_senha(nova_senha)
                        db.atualizar_senha_usuario(supabase, user['id'], novo_hash)
                        st.success("Senha alterada! Relogue para aplicar.")
                    else:
                        st.error("Digite uma nova senha.")
                else:
                    st.error("Senha atual incorreta.")
    
    # Definindo as opções de menu com base no cargo
    if user['funcao'] == 'admin':
        menu_opcoes = ["📊 Dashboard", "👥 Consultar Usuários", "➕ Adicionar Usuário"]
    elif user['funcao'] == 'proprietario':
        menu_opcoes = ["📊 Dashboard"]
    elif user['funcao'] == 'gerente':
        menu_opcoes = ["📝 Lançamento Diário"]
    else:
        menu_opcoes = ["📊 Dashboard"]

    escolha = st.sidebar.radio("Navegação", menu_opcoes)
    
    if st.sidebar.button("Sair"):
        st.session_state.autenticado = False
        st.session_state.user_data = None
        st.rerun()

    # --- LÓGICA DE TELAS ---

    # 1. TELA DE DASHBOARD (Admin e Proprietário)
    if escolha == "📊 Dashboard":
        st.title("📊 Dashboard Executivo")
        st.write("Bem-vindo ao centro de controle das 8 farmácias.")
        # Futuramente incluiremos os gráficos aqui

    # 2. TELA DE ADICIONAR USUÁRIO (A que acabamos de criar)
    elif escolha == "➕ Adicionar Usuário":
        st.title("➕ Cadastrar Novo Usuário")
        # Coloque aqui o código do formulário de cadastro que testamos
        # (Lembre-se de usar auth.gerar_hash_senha)

    # 3. TELA DE CONSULTAR USUÁRIOS (Excluir e Mudar Senha)
    elif escolha == "👥 Consultar Usuários":
        st.title("👥 Gestão de Usuários")
        
        usuarios_res = db.buscar_todos_usuarios(supabase) # Vamos criar essa função
        
        if usuarios_res and usuarios_res.data:
            for u in usuarios_res.data:
                with st.expander(f"{u['nome']} {u['sobrenome'] or ''} (@{u['username']})"):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        st.write(f"**E-mail:** {u['email']}")
                        st.write(f"**Função:** {u['funcao']}")
                        st.write(f"**Loja:** {u['unidade_id'] or 'N/A'}")
                    
                    with col2:
                        if st.button("Nova Senha", key=f"pass_{u['id']}"):
                            # Lógica para resetar senha (veremos a seguir)
                            # Dentro do menu "Consultar Usuários", no expander de cada usuário 'u'
    with col2:
        # Usamos uma chave única para o formulário de cada usuário
        com_reset = st.popover("🔑 Resetar Senha")
        with com_reset:
            nova_senha_admin = st.text_input("Nova senha para o usuário", type="password", key=f"new_pass_{u['id']}")
            if st.button("Confirmar Reset", key=f"btn_res_{u['id']}"):
                if nova_senha_admin:
                    novo_hash_admin = auth.gerar_hash_senha(nova_senha_admin)
                    db.atualizar_senha_usuario(supabase, u['id'], novo_hash_admin)
                    st.success(f"Senha de {u['username']} atualizada!")
                else:
                    st.error("Campo vazio.")
                            
                    with col3:
                        if st.button("Excluir", key=f"del_{u['id']}"):
                            # Chamada para deletar no banco
                            try:
                                supabase.table("usuarios").delete().eq("id", u['id']).execute()
                                st.success("Usuário removido!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro: {e}")
