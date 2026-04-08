import streamlit as st
from supabase import create_client, Client
import database_utils as db  # Importa suas funções de banco
import auth_utils as auth    # Importa sua lógica de senha
from datetime import date

# --- CONFIGURAÇÃO DE PÁGINA ---
st.set_page_config(page_title="Farma Gestor 1.0", layout="wide", initial_sidebar_state="expanded")

# --- CSS PERSONALIZADO (FIX: Botões +/- e Cores dos Inputs) ---
st.markdown("""
    <style>
        /* Fundo principal e Sidebar */
        .stApp { background-color: #000000; }
        [data-testid="stSidebar"] { background-color: #0d0d0d; border-right: 1px solid #333333; }
        
        /* Forçar campos de input a ficarem escuros */
        input[type=number], input[type=text], input[type=password], .stTextArea textarea {
            background-color: #1a1a1a !important;
            color: #ffffff !important;
            border: 1px solid #333333 !important;
        }

        /* REMOVER BOTÕES + e - de todos os navegadores */
        input::-webkit-outer-spin-button,
        input::-webkit-inner-spin-button {
            -webkit-appearance: none !important;
            margin: 0 !important;
        }
        input[type=number] {
            -moz-appearance: textfield !important;
        }
        
        /* Esconder botões de step do Streamlit */
        button[step="up"], button[step="down"], .stNumberInput button {
            display: none !important;
        }

        /* Estilo para expanders, forms e botões */
        .st-expander, .stForm { border: 1px solid #333333 !important; background-color: #0d0d0d !important; }
        .stButton>button { border: 1px solid #333333; background-color: #1a1a1a; color: white; }
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
    user = st.session_state.user_data
    if not user: st.rerun()

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
        st.session_state.pagina_ativa = "📊 Dashboard"; st.rerun()

    if user['funcao'] == 'admin':
        if st.sidebar.button("👥 Consultar Usuários", use_container_width=True):
            st.session_state.pagina_ativa = "👥 Consultar Usuários"; st.rerun()
        if st.sidebar.button("➕ Adicionar Usuário", use_container_width=True):
            st.session_state.pagina_ativa = "➕ Adicionar Usuário"; st.rerun()
        if st.sidebar.button("🏢 Consultar Lojas", use_container_width=True):
            st.session_state.pagina_ativa = "🏢 Consultar Lojas"; st.rerun()
    
    if user['funcao'] == 'gerente' or user['funcao'] == 'admin':
        if st.sidebar.button("📝 Lançamento Diário", use_container_width=True):
            st.session_state.pagina_ativa = "📝 Lançamento Diário"; st.rerun()

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
                    db.cadastrar_usuario(supabase, {
                        "nome": nome_c, "sobrenome": sobrenome_c, "email": email_c,
                        "username": user_c, "senha_hash": auth.gerar_hash_senha(pass_c),
                        "funcao": func_c, "unidade_id": id_loja
                    })
                    st.success("Cadastrado!")
                else:
                    st.warning("Preencha os campos obrigatórios.")

    elif escolha == "📝 Lançamento Diário":
        st.title("📝 Fechamento de Caixa Diário")
        
        loja_id = user['unidade_id']
        if not loja_id and user['funcao'] != 'admin':
            st.error("Usuário sem loja vinculada.")
            st.stop()

        # Configuração de Data com trava para não permitir futuro
        data_sel = st.date_input("Data do Movimento", value=date.today(), max_value=date.today(), key="data_mov")
        st.write("---")
        
        h1, h2, h3, h4 = st.columns([2, 2, 2, 1.5])
        h1.write("**DESCRIÇÃO**"); h2.write("**VALOR SISTEMA**"); h3.write("**CONFERÊNCIA**"); h4.write("**ACERTO**")

        def gerar_linha_viva(label, chave):
            col_desc, col_sis, col_conf, col_acer = st.columns([2, 2, 2, 1.5])
            col_desc.markdown(f"<div style='padding-top:10px'><b>{label}</b></div>", unsafe_allow_html=True)
            val_sis = col_sis.number_input("R$", key=f"s_{chave}", format="%.2f", step=0.01, label_visibility="collapsed")
            val_conf = col_conf.number_input("R$", key=f"c_{chave}", format="%.2f", step=0.01, label_visibility="collapsed")
            acerto = val_conf - val_sis
            cor = "white" if acerto == 0 else ("#ff4b4b" if acerto < 0 else "#00ff00")
            col_acer.markdown(f"<div style='padding-top:10px; color:{cor}; font-weight:bold;'>R$ {acerto:.2f}</div>", unsafe_allow_html=True)
            return val_sis, val_conf

        s_car, c_car = gerar_linha_viva("CARTÃO", "car")
        s_cre, c_cre = gerar_linha_viva("CREDIÁRIO", "cre")
        s_din, c_din = gerar_linha_viva("DINHEIRO", "din")
        s_ifo, c_ifo = gerar_linha_viva("IFOOD", "ifo")
        s_pix, c_pix = gerar_linha_viva("PIX/TRANSF", "pix")
        
        st.write("---")
        _, _, col_l_desp, col_v_desp = st.columns([2, 2, 2, 1.5])
        col_l_desp.write("**DESPESA (-)**")
        v_desp = col_v_desp.number_input("R$", key="desp_v", format="%.2f", step=0.01, label_visibility="collapsed")

        # Cálculos Totais
        tot_sis = s_car + s_cre + s_din + s_ifo + s_pix
        tot_conf = c_car + c_cre + c_din + c_ifo + c_pix + v_desp
        tot_acer = tot_conf - tot_sis - (v_desp * 2) # Ajuste lógico do cálculo de acerto

        st.markdown("---")
        t1, t2, t3, t4 = st.columns([2, 2, 2, 1.5])
        t1.subheader("TOTAL")
        t2.subheader(f"R$ {tot_sis:.2f}")
        t3.subheader(f"R$ {tot_conf:.2f}")
        cor_t = "white" if tot_acer == 0 else ("#ff4b4b" if tot_acer < 0 else "#00ff00")
        t4.markdown(f"<h3 style='color:{cor_t};'>R$ {tot_acer:.2f}</h3>", unsafe_allow_html=True)

        with st.form("form_finalizacao", clear_on_submit=True):
            arquivos = st.file_uploader("Anexar Prints (Máx 5)", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'])
            obs = st.text_area("Observações")
            if st.form_submit_button("✅ SALVAR FECHAMENTO NO BANCO", use_container_width=True):
                with st.spinner("Enviando..."):
                    urls = []
                    for i, f in enumerate(arquivos):
                        path = f"loja_{loja_id}/{data_sel}/p_{i}.{f.name.split('.')[-1]}"
                        url_f = db.fazer_upload_print(supabase, f, path)
                        if url_f: urls.append(url_f)
                    
                    db.salvar_fechamento(supabase, {
                        "loja_id": loja_id, "usuario_id": user['id'], "data_fechamento": str(data_sel),
                        "sis_cartao": s_car, "conf_cartao": c_car, "sis_crediario": s_cre, "conf_crediario": c_cre,
                        "sis_dinheiro": s_din, "conf_dinheiro": c_din, "sis_ifood": s_ifo, "conf_ifood": c_ifo,
                        "sis_pix": s_pix, "conf_pix": c_pix, "despesa": v_desp, "observacoes": obs, "urls_prints": urls
                    })
                    st.success("Salvo com sucesso!")
                    st.balloons()

    # (Mantenha aqui as outras telas: Consultar Usuários, Consultar Lojas, etc...)
