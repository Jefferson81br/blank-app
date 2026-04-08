import streamlit as st
from supabase import create_client, Client
import database_utils as db  # Importa suas funções de banco
import auth_utils as auth    # Importa sua lógica de senha

# --- CONFIGURAÇÃO DE PÁGINA ---
st.set_page_config(page_title="Farma Gestor 1.0", layout="wide", initial_sidebar_state="expanded")

# --- CSS PERSONALIZADO ---
st.markdown("""
    <style>
        .stApp { background-color: #000000; }
        [data-testid="stSidebar"] { background-color: #0d0d0d; border-right: 1px solid #333333; }
        .stButton>button { border: 1px solid #333333; background-color: #1a1a1a; color: white; }
        .st-expander, .stForm { border: 1px solid #333333 !important; background-color: #0d0d0d !important; }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO SUPABASE ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# --- ESTADO DA SESSÃO ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.user_data = None
if 'pagina_ativa' not in st.session_state:
    st.session_state.pagina_ativa = "📊 Dashboard"

# --- FLUXO DE TELAS ---

if not st.session_state.autenticado:
    # TELA DE LOGIN CENTRALIZADA
    v_esq, centro, v_dir = st.columns([1, 1, 1])
    with centro:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.title("💊 Farma Gestor 1.0")
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
    # SISTEMA LOGADO
    user = st.session_state.user_data
    if not user: st.rerun() # Segurança caso a sessão expire

    # --- SIDEBAR NAVEGAÇÃO ---
    st.sidebar.title(f"Olá, {user['nome']}")
    st.sidebar.info(f"Nível: {user['funcao'].upper()}")

    with st.sidebar.expander("⚙️ Minha Conta"):
        with st.form("form_troca_senha_propria"):
            s_atual = st.text_input("Senha Atual", type="password")
            s_nova = st.text_input("Nova Senha", type="password")
            if st.form_submit_button("Atualizar Senha", use_container_width=True):
                if auth.verificar_senha(s_atual, user['senha_hash']) or s_atual == user['senha_hash']:
                    db.atualizar_senha_usuario(supabase, user['id'], auth.gerar_hash_senha(s_nova))
                    st.success("Senha alterada!")
                else:
                    st.error("Senha atual incorreta.")

    st.sidebar.markdown("---")
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
        st.rerun()

    # --- RENDERIZAÇÃO ---
    escolha = st.session_state.pagina_ativa

    if escolha == "📊 Dashboard":
        st.title("📊 Dashboard Executivo")
        st.info("Painel de indicadores em desenvolvimento.")

    elif escolha == "➕ Adicionar Usuário":
        st.title("➕ Cadastrar Novo Usuário")
        # Busca lojas ANTES do formulário
        res_lojas = db.buscar_lojas(supabase)
        dict_lojas = {l['nome']: l['id'] for l in res_lojas.data} if res_lojas.data else {}
        
        with st.form("form_cadastro_usuario", clear_on_submit=True):
            c1, c2 = st.columns(2)
            nome_c = c1.text_input("Nome")
            sobrenome_c = c2.text_input("Sobrenome")
            email_c = c1.text_input("E-mail")
            loja_sel = c2.selectbox("Unidade", ["Nenhuma"] + list(dict_lojas.keys()))
            user_c = c1.text_input("Login")
            pass_c = c2.text_input("Senha Inicial", type="password")
            func_c = st.selectbox("Nível", ["gerente", "proprietario", "financeiro", "admin"])
            
            if st.form_submit_button("Finalizar Cadastro", use_container_width=True):
                if nome_c and user_c and pass_c:
                    id_loja = dict_lojas.get(loja_sel)
                    dados = {
                        "nome": nome_c, "sobrenome": sobrenome_c, "email": email_c,
                        "username": user_c, "senha_hash": auth.gerar_hash_senha(pass_c),
                        "funcao": func_c, "unidade_id": id_loja
                    }
                    db.cadastrar_usuario(supabase, dados)
                    st.success("Cadastrado!")
                else:
                    st.warning("Preencha os campos obrigatórios.")

    elif escolha == "👥 Consultar Usuários":
        st.title("👥 Gestão de Usuários")
        usuarios = db.buscar_todos_usuarios(supabase)
        lojas = db.buscar_lojas(supabase)
        # Mapa para mostrar Nome da Loja em vez de ID
        mapa_lojas = {l['id']: l['nome'] for l in lojas.data} if lojas.data else {}

        if usuarios and usuarios.data:
            for u in usuarios.data:
                nome_loja = mapa_lojas.get(u['unidade_id'], "Admin/Geral")
                with st.expander(f"{u['nome']} - {nome_loja} (@{u['username']})"):
                    col1, col2, col3 = st.columns([2,1,1])
                    col1.write(f"E-mail: {u['email']} | Função: {u['funcao']}")
                    if col2.popover("🔑 Resetar").button("Confirmar Reset", key=f"rs_{u['id']}"):
                        # Aqui você pode adicionar um campo de texto no popover se quiser definir a senha
                        st.info("Use o Reset no formulário padrão.")
                    if col3.button("Excluir", key=f"ex_{u['id']}", use_container_width=True):
                        supabase.table("usuarios").delete().eq("id", u['id']).execute()
                        st.rerun()

    elif escolha == "🏢 Consultar Lojas":
        st.title("🏢 Gestão de Unidades")
        t1, t2 = st.tabs(["Lista", "➕ Nova"])
        with t1:
            lojas_lista = db.buscar_lojas(supabase)
            if lojas_lista.data:
                for l in lojas_lista.data:
                    with st.expander(f"{l['nome']} ({l['marca']})"):
                        with st.form(f"f_{l['id']}"):
                            n = st.text_input("Nome", value=l['nome'])
                            m = st.text_input("Marca", value=l['marca'])
                            e = st.text_input("Endereço", value=l['endereco'])
                            if st.form_submit_button("Atualizar"):
                                db.atualizar_loja(supabase, l['id'], {"nome":n, "marca":m, "endereco":e})
                                st.rerun()
        with t2:
            with st.form("n_loja"):
                nl, ml, el = st.text_input("Nome"), st.text_input("Marca"), st.text_input("Endereço")
                if st.form_submit_button("Salvar"):
                    db.cadastrar_loja(supabase, {"nome":nl, "marca":ml, "endereco":el})
                    st.rerun()
    elif escolha == "📝 Lançamento Diário":
    st.title("📝 Fechamento de Caixa Diário")
    
    loja_id = user['unidade_id']
    if not loja_id:
        st.error("Usuário sem loja vinculada.")
        st.stop()

    # --- CAMPOS FORA DO FORMULÁRIO PARA CÁLCULO EM TEMPO REAL ---
    # Usamos colunas para organizar o cabeçalho
    st.date_input("Data do Movimento", key="data_mov")
    st.write("---")
    
    h1, h2, h3, h4 = st.columns([2, 2, 2, 1.5])
    h1.write("**DESCRIÇÃO**")
    h2.write("**VALOR SISTEMA**")
    h3.write("**CONFERÊNCIA**")
    h4.write("**ACERTO**")

    # Função interna para gerar as linhas com cálculos vivos
    def gerar_linha_viva(label, chave):
        col_desc, col_sis, col_conf, col_acer = st.columns([2, 2, 2, 1.5])
        col_desc.markdown(f"<div style='padding-top:10px'><b>{label}</b></div>", unsafe_allow_html=True)
        
        # step=None remove os botões de + e - em alguns navegadores e impede o incremento
        val_sis = col_sis.number_input("R$", key=f"s_{chave}", format="%.2f", step=0.01, label_visibility="collapsed")
        val_conf = col_conf.number_input("R$", key=f"c_{chave}", format="%.2f", step=0.01, label_visibility="collapsed")
        
        acerto = val_conf - val_sis
        cor = "white" if acerto == 0 else ("#ff4b4b" if acerto < 0 else "#00ff00")
        
        col_acer.markdown(f"""
            <div style='padding-top:10px; color:{cor}; font-weight:bold;'>
                R$ {acerto:.2f}
            </div>
        """, unsafe_allow_html=True)
        return val_sis, val_conf, acerto

    # Gerando as linhas e capturando os valores vivos
    s_cartao, c_cartao, a_cartao = gerar_linha_viva("CARTÃO", "cartao")
    s_cred, c_cred, a_cred = gerar_linha_viva("CREDIÁRIO", "cred")
    s_din, c_din, a_din = gerar_linha_viva("DINHEIRO", "din")
    s_ifood, c_ifood, a_ifood = gerar_linha_viva("IFOOD", "ifood")
    s_pix, c_pix, a_pix = gerar_linha_viva("PIX/TRANSF", "pix")
    
    st.write("---")
    # Linha de Despesa
    _, _, col_l_desp, col_v_desp = st.columns([2, 2, 2, 1.5])
    col_l_desp.write("**DESPESA (-)**")
    v_despesa = col_v_desp.number_input("R$", key="despesa_v", format="%.2f", step=0.01, label_visibility="collapsed")

    # CÁLCULO DO TOTAL FINAL (Igual à sua planilha)
    total_sistema = s_cartao + s_cred + s_din + s_ifood + s_pix
    total_conf = c_cartao + c_cred + c_din + c_ifood + c_pix + v_despesa # Somando despesa como valor de saída conferido
    total_acerto = a_cartao + a_cred + a_din + a_ifood + a_pix - v_despesa

    # EXIBIÇÃO DO TOTAL ESTILO PLANILHA
    st.markdown("---")
    t1, t2, t3, t4 = st.columns([2, 2, 2, 1.5])
    t1.subheader("TOTAL")
    t2.subheader(f"R$ {total_sistema:.2f}")
    t3.subheader(f"R$ {total_conf:.2f}")
    
    cor_total = "white" if total_acerto == 0 else ("#ff4b4b" if total_acerto < 0 else "#00ff00")
    t4.markdown(f"<h3 style='color:{cor_total};'>R$ {total_acerto:.2f}</h3>", unsafe_allow_html=True)

    # --- ÁREA DE ENVIO (FORMULÁRIO APENAS PARA O BOTÃO E UPLOAD) ---
    with st.form("form_finalizacao", clear_on_submit=True):
        arquivos = st.file_uploader("Anexar Prints (Máx 5)", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'])
        obs = st.text_area("Observações")
        
        if st.form_submit_button("✅ SALVAR FECHAMENTO NO BANCO", use_container_width=True):
            # Lógica de salvar (db.salvar_fechamento...) usando as variáveis acima
            pass
