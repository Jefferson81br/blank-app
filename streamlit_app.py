import streamlit as st
from supabase import create_client, Client
import database_utils as db  # Importa suas funções de banco
import auth_utils as auth    # Importa sua lógica de senha


# Configuração de página para forçar o layout e favicon
st.set_page_config(page_title="Gestão de Farmácias", layout="wide", initial_sidebar_state="expanded")

# CSS para forçar o fundo preto e remover bordas brancas
st.markdown("""
    <style>
        /* Fundo principal */
        .stApp {
            background-color: #000000;
        }
        
        /* Fundo da Sidebar */
        [data-testid="stSidebar"] {
            background-color: #0d0d0d;
            border-right: 1px solid #333333;
        }
        
        /* Ajuste de botões para o tema escuro */
        .stButton>button {
            border: 1px solid #333333;
            background-color: #1a1a1a;
            color: white;
        }
        
        /* Estilo para os expanders e formulários */
        .st-expander, .stForm {
            border: 1px solid #333333 !important;
            background-color: #0d0d0d !important;
        }
    </style>
    """, unsafe_allow_html=True)

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
    # Criamos 3 colunas: as das pontas vazias e a do meio com o conteúdo
    # O ratio [1, 2, 1] faz a coluna do meio ter 50% da largura da tela
    vazia_esq, centro, vazia_dir = st.columns([1, 1, 1])

    with centro:
        st.markdown("<br><br>", unsafe_allow_html=True) # Espaçamento no topo
        st.title("💊 Farma Gestor 1.0")
        
        # Usamos um container ou um form para agrupar visualmente
        with st.container(border=True):
            user_input = st.text_input("Usuário")
            pass_input = st.text_input("Senha", type="password")
            
            if st.button("Entrar", use_container_width=True):
                res = db.buscar_usuario(supabase, user_input)
                
                if res and res.data:
                    user = res.data[0]
                    if auth.verificar_senha(pass_input, user['senha_hash']) or pass_input == user['senha_hash']:
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
        if st.sidebar.button("🏢 Consultar Lojas", use_container_width=True):
            st.session_state.pagina_ativa = "🏢 Consultar Lojas"
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
                
                # 1. Busca as lojas reais cadastradas no banco
                res_lojas = db.buscar_lojas(supabase)
                # Cria um dicionário { "Nome da Loja": ID_da_Loja }
                dict_lojas = {l['nome']: l['id'] for l in res_lojas.data} if res_lojas.data else {}

            
            with col2:
                sobrenome = st.text_input("Sobrenome")
                # 2. Mostra o nome da loja, mas salva o ID
                loja_selecionada = st.selectbox("Unidade", ["Nenhuma (Admin/Prop.)"] + list(dict_lojas.keys()))
                nova_senha_cad = st.text_input("Senha Inicial", type="password")
                # ... (dentro da lógica do botão de cadastrar)
                id_da_loja_final = dict_lojas.get(loja_selecionada) # Pega o ID ou None se for "Nenhuma"
            funcao_cad = st.selectbox("Nível", ["gerente", "proprietario", "financeiro", "admin"])
            if st.form_submit_button("Finalizar Cadastro", use_container_width=True):
            if nome and novo_usuario and nova_senha_cad:
                hash_cad = auth.gerar_hash_senha(nova_senha_cad)
                
                # MAPEAMENTO CORRIGIDO:
                dados = {
                    "nome": nome, 
                    "sobrenome": sobrenome, 
                    "email": email,
                    "username": novo_usuario, 
                    "senha_hash": hash_cad,
                    "funcao": funcao_cad, 
                    "unidade_id": id_da_loja_final  # Usando a variável nova que criamos
                }
                
                db.cadastrar_usuario(supabase, dados)
                st.success(f"Usuário {novo_usuario} criado com sucesso!")
                st.rerun()
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
    
    elif escolha == "🏢 Consultar Lojas":
         st.title("🏢 Gestão de Unidades")
    
         tab1, tab2 = st.tabs(["Lista de Lojas", "➕ Nova Loja"])

         with tab1:
             lojas_res = db.buscar_lojas(supabase)
             if lojas_res and lojas_res.data:
                 for loja in lojas_res.data:
                     with st.expander(f"{loja['nome']} - {loja['marca'] or 'Sem Marca'}"):
                         with st.form(f"edit_loja_{loja['id']}"):
                             col1, col2 = st.columns(2)
                             novo_nome_l = col1.text_input("Nome da Loja", value=loja['nome'])
                             nova_marca_l = col2.text_input("Marca", value=loja['marca'])
                             novo_end_l = st.text_input("Endereço", value=loja['endereco'])
                        
                             # Buscar lista de usuários para selecionar o gerente
                             users_res = db.buscar_todos_usuarios(supabase)
                             lista_gerentes = {u['nome']: u['id'] for u in users_res.data} if users_res.data else {}
                        
                             # Tenta encontrar o nome do gerente atual para o selectbox
                             nome_gerente_atual = next((nome for nome, id_u in lista_gerentes.items() if id_u == loja['gerente_id']), None)
                        
                             novo_gerente = st.selectbox("Gerente Responsável", 
                                                   options=list(lista_gerentes.keys()),
                                                   index=list(lista_gerentes.keys()).index(nome_gerente_atual) if nome_gerente_atual else 0)

                             if st.form_submit_button("Salvar Alterações", use_container_width=True):
                                 dados_update = {
                                     "nome": novo_nome_l,
                                     "marca": nova_marca_l,
                                     "endereco": novo_end_l,
                                     "gerente_id": lista_gerentes[novo_gerente]
                                 }
                                 db.atualizar_loja(supabase, loja['id'], dados_update)
                                 st.success("Loja atualizada!")
                                 st.rerun()

         with tab2:
             st.subheader("Cadastrar Nova Unidade")
             with st.form("nova_loja_form"):
                 n_nome = st.text_input("Nome da Farmácia")
                 n_marca = st.text_input("Marca/Rede")
                 n_end = st.text_input("Endereço Completo")
            
                 if st.form_submit_button("Cadastrar Loja", use_container_width=True):
                     if n_nome:
                         db.cadastrar_loja(supabase, {"nome": n_nome, "marca": n_marca, "endereco": n_end})
                         st.success("Loja cadastrada com sucesso!")
                         st.rerun()
                     else:
                         st.error("O nome da loja é obrigatório.")  
