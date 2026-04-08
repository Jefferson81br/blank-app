import streamlit as st
from supabase import create_client, Client
import database_utils as db  # Importa suas funções de banco
import auth_utils as auth    # Importa sua lógica de senha
from datetime import date, timedelta
import pandas as pd

# --- CONFIGURAÇÃO DE PÁGINA ---
st.set_page_config(page_title="Farma Gestor 1.0", layout="wide", initial_sidebar_state="expanded")

# --- CSS PERSONALIZADO ---
st.markdown("""
    <style>
        .stApp { background-color: #000000; }
        [data-testid="stSidebar"] { background-color: #0d0d0d; border-right: 1px solid #333333; }
        
        /* Forçar campos de input a ficarem escuros */
        input[type=number], input[type=text], input[type=password], .stTextArea textarea {
            background-color: #1a1a1a !important;
            color: #ffffff !important;
            border: 1px solid #333333 !important;
        }

        /* REMOVER BOTÕES + e - de todos os navegadores */
        input::-webkit-outer-spin-button, input::-webkit-inner-spin-button {
            -webkit-appearance: none !important;
            margin: 0 !important;
        }
        input[type=number] { -moz-appearance: textfield !important; }
        button[step="up"], button[step="down"], .stNumberInput button { display: none !important; }

        /* Estilo para expanders, forms e botões */
        .st-expander, .stForm { border: 1px solid #333333 !important; background-color: #0d0d0d !important; }
        .stButton>button { border: 1px solid #333333; background-color: #1a1a1a; color: white; }
        
        /* Ajuste para st.table no tema escuro */
        .stTable { background-color: #0d0d0d; color: white; }
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

# --- FLUXO DE ACESSO ---
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
                    user_db = res.data[0]
                    if auth.verificar_senha(pass_input, user_db['senha_hash']) or pass_input == user_db['senha_hash']:
                        st.session_state.autenticado = True
                        st.session_state.user_data = user_db
                        st.rerun()
                    else:
                        st.error("Senha incorreta.")
                else:
                    st.error("Usuário não encontrado.")
else:
    user = st.session_state.user_data
    
    # --- SIDEBAR NAVEGAÇÃO ---
    st.sidebar.title(f"Olá, {user['nome']}")
    st.sidebar.info(f"Nível: {user['funcao'].upper()}")

    if st.sidebar.button("📊 Dashboard", use_container_width=True):
        st.session_state.pagina_ativa = "📊 Dashboard"; st.rerun()

    if user['funcao'] == 'admin':
        if st.sidebar.button("👥 Consultar Usuários", use_container_width=True):
            st.session_state.pagina_ativa = "👥 Consultar Usuários"; st.rerun()
        if st.sidebar.button("➕ Adicionar Usuário", use_container_width=True):
            st.session_state.pagina_ativa = "➕ Adicionar Usuário"; st.rerun()
        if st.sidebar.button("🏢 Consultar Lojas", use_container_width=True):
            st.session_state.pagina_ativa = "🏢 Consultar Lojas"; st.rerun()
    
    if user['funcao'] in ['gerente', 'admin']:
        if st.sidebar.button("📝 Lançamento Diário", use_container_width=True):
            st.session_state.pagina_ativa = "📝 Lançamento Diário"; st.rerun()

    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Sair", use_container_width=True):
        st.session_state.autenticado = False; st.rerun()

    # --- RENDERIZAÇÃO DE TELAS ---
    escolha = st.session_state.pagina_ativa

    if escolha == "📊 Dashboard":
        st.title("📊 Painel de Performance")
        loja_id = user['unidade_id']
        
        if not loja_id and user['funcao'] != 'admin':
            st.warning("Usuário sem loja vinculada.")
        else:
            c1, c2 = st.columns(2)
            periodo = c1.selectbox("Período:", ["Dia", "Semana", "Mês"])
            hoje = date.today()

            if periodo == "Dia":
                d_ini = c2.date_input("Data:", hoje, max_value=hoje)
                d_fim = d_ini
            elif periodo == "Semana":
                d_ini = hoje - timedelta(days=hoje.weekday())
                d_fim = hoje
            else:
                d_ini = hoje.replace(day=1)
                d_fim = hoje

            res = db.buscar_fechamento_por_data(supabase, loja_id, str(d_ini), str(d_fim))
            
            if res and res.data:
                df_raw = pd.DataFrame(res.data)
                
                # VISUALIZAÇÃO POR DIA (ESTILO PLANILHA)
                if periodo == "Dia":
                    d = res.data[0]
                    st.markdown(f"### LOJA: {user.get('nome_loja', 'Unidade Selecionada')}")
                    
                    dados_tabela = [
                        {"DESCRIÇÃO": "CARTÃO", "VALOR SISTEMA": d['sis_cartao'], "VALOR DE CONFERENCIA": d['conf_cartao']},
                        {"DESCRIÇÃO": "CREDIÁRIO", "VALOR SISTEMA": d['sis_crediario'], "VALOR DE CONFERENCIA": d['conf_crediario']},
                        {"DESCRIÇÃO": "DINHEIRO", "VALOR SISTEMA": d['sis_dinheiro'], "VALOR DE CONFERENCIA": d['conf_dinheiro']},
                        {"DESCRIÇÃO": "IFOOD", "VALOR SISTEMA": d['sis_ifood'], "VALOR DE CONFERENCIA": d['conf_ifood']},
                        {"DESCRIÇÃO": "PIX TRANSF", "VALOR SISTEMA": d['sis_pix'], "VALOR DE CONFERENCIA": d['conf_pix']},
                        {"DESCRIÇÃO": "DESPESA", "VALOR SISTEMA": 0.0, "VALOR DE CONFERENCIA": d['despesa']}
                    ]
                    
                    df_tab = pd.DataFrame(dados_tabela)
                    df_tab['ACERTO'] = df_tab['VALOR DE CONFERENCIA'] - df_tab['VALOR SISTEMA']
                    df_tab.loc[df_tab['DESCRIÇÃO'] == 'DESPESA', 'ACERTO'] = -d['despesa']

                    st.table(df_tab.style.format({
                        "VALOR SISTEMA": "R$ {:.2f}", 
                        "VALOR DE CONFERENCIA": "R$ {:.2f}", 
                        "ACERTO": "R$ {:.2f}"
                    }))

                    # TOTAIS
                    t_sis = df_tab['VALOR SISTEMA'].sum()
                    t_conf = df_tab['VALOR DE CONFERENCIA'].sum()
                    t_ace = t_conf - t_sis - (d['despesa'] * 2)
                    
                    c_t1, c_t2, c_t3 = st.columns([2, 2, 1.5])
                    c_t1.subheader("TOTAL")
                    c_t2.subheader(f"R$ {t_sis:,.2f} | R$ {t_conf:,.2f}")
                    cor_f = "#ff4b4b" if t_ace < 0 else "#00ff00"
                    c_t3.markdown(f"<h3 style='color:{cor_f};'>R$ {t_ace:,.2f}</h3>", unsafe_allow_html=True)

                    if d['urls_prints']:
                        st.write("---")
                        st.write("**📸 Comprovantes (150x150):**")
                        cols_p = st.columns(len(d['urls_prints']))
                        for i, url_p in enumerate(d['urls_prints']):
                            cols_p[i].markdown(f"""
                                <a href="{url_p}" target="_blank">
                                    <img src="{url_p}" width="150" height="150" style="object-fit: cover; border-radius: 5px; border: 1px solid #333;">
                                </a>
                            """, unsafe_allow_html=True)
                
                else:
                    # VISUALIZAÇÃO ACUMULADA (MÉTRICAS)
                    tot_sis = df_raw[['sis_cartao', 'sis_crediario', 'sis_dinheiro', 'sis_ifood', 'sis_pix']].values.sum()
                    tot_conf = df_raw[['conf_cartao', 'conf_crediario', 'conf_dinheiro', 'conf_ifood', 'conf_pix', 'despesa']].values.sum()
                    tot_desp = df_raw['despesa'].sum()
                    tot_acer = tot_conf - tot_sis - (tot_desp * 2)

                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Sistema", f"R$ {tot_sis:,.2f}")
                    m2.metric("Conferido", f"R$ {tot_conf:,.2f}")
                    m3.metric("Despesas", f"R$ {tot_desp:,.2f}")
                    m4.metric("Acerto", f"R$ {tot_acer:,.2f}", delta=f"{tot_acer:,.2f}")
            else:
                st.info("Nenhum dado encontrado para este período.")

    elif escolha == "📝 Lançamento Diário":
        st.title("📝 Fechamento de Caixa Diário")
        loja_id = user['unidade_id']
        data_sel = st.date_input("Data do Movimento", value=date.today(), max_value=date.today())
        st.write("---")
        
        h1, h2, h3, h4 = st.columns([2, 2, 2, 1.5])
        h1.write("**DESCRIÇÃO**"); h2.write("**VALOR SISTEMA**"); h3.write("**CONFERÊNCIA**"); h4.write("**ACERTO**")

        def linha(label, key):
            c_desc, c_sis, c_conf, c_ace = st.columns([2, 2, 2, 1.5])
            c_desc.markdown(f"<div style='padding-top:10px'><b>{label}</b></div>", unsafe_allow_html=True)
            v_s = c_sis.number_input("R$", key=f"s_{key}", format="%.2f", step=0.01, label_visibility="collapsed")
            v_c = c_conf.number_input("R$", key=f"c_{key}", format="%.2f", step=0.01, label_visibility="collapsed")
            ace = v_c - v_s
            cor = "white" if ace == 0 else ("#ff4b4b" if ace < 0 else "#00ff00")
            c_ace.markdown(f"<div style='padding-top:10px; color:{cor}; font-weight:bold;'>R$ {ace:.2f}</div>", unsafe_allow_html=True)
            return v_s, v_c

        s_car, c_car = linha("CARTÃO", "car")
        s_cre, c_cre = linha("CREDIÁRIO", "cre")
        s_din, c_din = linha("DINHEIRO", "din")
        s_ifo, c_ifo = linha("IFOOD", "ifo")
        s_pix, c_pix = linha("PIX/TRANSF", "pix")
        
        st.write("---")
        _, _, cl_l, cl_v = st.columns([2, 2, 2, 1.5])
        cl_l.write("**DESPESA (-)**")
        v_desp = cl_v.number_input("R$", key="dv", format="%.2f", step=0.01, label_visibility="collapsed")

        t_sis = s_car + s_cre + s_din + s_ifo + s_pix
        t_conf = c_car + c_cre + c_din + c_ifo + c_pix + v_desp
        t_ace = t_conf - t_sis - (v_desp * 2)

        st.markdown("---")
        r1, r2, r3, r4 = st.columns([2, 2, 2, 1.5])
        r1.subheader("TOTAL"); r2.subheader(f"R$ {t_sis:.2f}"); r3.subheader(f"R$ {t_conf:.2f}")
        c_t = "white" if t_ace == 0 else ("#ff4b4b" if t_ace < 0 else "#00ff00")
        r4.markdown(f"<h3 style='color:{c_t};'>R$ {t_ace:.2f}</h3>", unsafe_allow_html=True)

        with st.form("f_final", clear_on_submit=True):
            imgs = st.file_uploader("Prints", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'])
            obs = st.text_area("Obs")
            if st.form_submit_button("✅ SALVAR NO BANCO", use_container_width=True):
                with st.spinner("Salvando..."):
                    urls = []
                    for i, f in enumerate(imgs):
                        url_f = db.fazer_upload_print(supabase, f, f"loja_{loja_id}/{data_sel}/p_{i}.jpg")
                        if url_f: urls.append(url_f)
                    db.salvar_fechamento(supabase, {
                        "loja_id": loja_id, "usuario_id": user['id'], "data_fechamento": str(data_sel),
                        "sis_cartao": s_car, "conf_cartao": c_car, "sis_crediario": s_cre, "conf_crediario": c_cre,
                        "sis_dinheiro": s_din, "conf_dinheiro": c_din, "sis_ifood": s_ifo, "conf_ifood": c_ifo,
                        "sis_pix": s_pix, "conf_pix": c_pix, "despesa": v_desp, "observacoes": obs, "urls_prints": urls
                    })
                    st.success("Sucesso!"); st.balloons()
