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
        
        input[type=number], input[type=text], input[type=password], .stTextArea textarea {
            background-color: #1a1a1a !important;
            color: #ffffff !important;
            border: 1px solid #333333 !important;
        }

        input::-webkit-outer-spin-button, input::-webkit-inner-spin-button {
            -webkit-appearance: none !important;
            margin: 0 !important;
        }
        input[type=number] { -moz-appearance: textfield !important; }
        button[step="up"], button[step="down"], .stNumberInput button { display: none !important; }

        .st-expander, .stForm { border: 1px solid #333333 !important; background-color: #0d0d0d !important; }
        .stButton>button { border: 1px solid #333333; background-color: #1a1a1a; color: white; }
        
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
    if not user: st.rerun()

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
        
        # 1. BUSCA DE LOJAS PARA FILTRO
        lojas_res = db.buscar_lojas(supabase)
        mapa_lojas = {l['nome']: l['id'] for l in lojas_res.data} if lojas_res.data else {}
        
        if user['funcao'] in ['admin', 'proprietario']:
            lojas_sel_nomes = st.multiselect(
                "Unidades para visualizar:", 
                options=list(mapa_lojas.keys()),
                default=list(mapa_lojas.keys())[:1]
            )
            lista_ids = [mapa_lojas[n] for n in lojas_sel_nomes]
        else:
            if not user['unidade_id']:
                st.warning("Gerente sem unidade vinculada.")
                st.stop()
            lista_ids = [user['unidade_id']]

        if not lista_ids:
            st.info("Selecione uma loja.")
            st.stop()

        # 2. FILTROS DE DATA
        c1, c2 = st.columns(2)
        periodo = c1.selectbox("Período:", ["Dia", "Semana", "Mês"])
        hoje = date.today()
        if periodo == "Dia":
            d_ini = c2.date_input("Data:", hoje, max_value=hoje); d_fim = d_ini
        elif periodo == "Semana":
            d_ini = hoje - timedelta(days=hoje.weekday()); d_fim = hoje
        else:
            d_ini = hoje.replace(day=1); d_fim = hoje

        # 3. BUSCA E EXIBIÇÃO
        res = db.buscar_fechamento_multiplas_lojas(supabase, lista_ids, str(d_ini), str(d_fim))
        
        if res and res.data:
            df_geral = pd.DataFrame(res.data)
            id_para_nome = {v: k for k, v in mapa_lojas.items()}
            
            # Layout dinâmico em colunas
            cols_dash = st.columns(len(lista_ids))
            
            for idx, l_id in enumerate(lista_ids):
                with cols_dash[idx]:
                    st.subheader(f"🏢 {id_para_nome.get(l_id)}")
                    df_l = df_geral[df_geral['loja_id'] == l_id]
                    
                    if not df_l.empty:
                        t_s = df_l[['sis_cartao', 'sis_crediario', 'sis_dinheiro', 'sis_ifood', 'sis_pix']].values.sum()
                        t_c = df_l[['conf_cartao', 'conf_crediario', 'conf_dinheiro', 'conf_ifood', 'conf_pix', 'despesa']].values.sum()
                        t_d = df_l['despesa'].sum()
                        t_a = t_c - t_s - (t_d * 2)

                        st.metric("Venda (Sis)", f"R$ {t_s:,.2f}")
                        st.metric("Acerto", f"R$ {t_a:,.2f}", delta=f"{t_a:,.2f}")

                        if periodo == "Dia":
                            d = df_l.iloc[0]
                            tab_d = pd.DataFrame({
                                "Item": ["Cartão", "Dinheiro", "Despesa"],
                                "Conferido": [d['conf_cartao'], d['conf_dinheiro'], d['despesa']]
                            })
                            st.table(tab_d.style.format({"Conferido": "R$ {:.2f}"}))
                            if d['urls_prints']:
                                for url_p in d['urls_prints']:
                                    st.markdown(f'<a href="{url_p}" target="_blank"><img src="{url_p}" width="100%" style="max-width:150px; border-radius:5px; margin-bottom:5px;"></a>', unsafe_allow_html=True)
                    else:
                        st.caption("Sem dados.")
        else:
            st.info("Nenhum lançamento encontrado.")

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
                with st.spinner("Validando e salvando..."):
                    d_ins = {
                        "loja_id": loja_id, "usuario_id": user['id'], "data_fechamento": str(data_sel),
                        "sis_cartao": s_car, "conf_cartao": c_car, "sis_crediario": s_cre, "conf_crediario": c_cre,
                        "sis_dinheiro": s_din, "conf_dinheiro": c_din, "sis_ifood": s_ifo, "conf_ifood": c_ifo,
                        "sis_pix": s_pix, "conf_pix": c_pix, "despesa": v_desp, "observacoes": obs, "urls_prints": []
                    }
                    ok, res_m = db.salvar_fechamento(supabase, d_ins)
                    if ok:
                        urls = []
                        for i, f in enumerate(imgs):
                            u_f = db.fazer_upload_print(supabase, f, f"loja_{loja_id}/{data_sel}/p_{i}.jpg")
                            if u_f: urls.append(u_f)
                        if urls:
                            supabase.table("fechamentos").update({"urls_prints": urls}).eq("id", res_m.data[0]['id']).execute()
                        st.success("✅ Salvo com sucesso!"); st.balloons()
                    else:
                        st.error(f"❌ Erro: {res_m}")

    # (Lógica para Adicionar Usuário, Consultar Usuários e Lojas mantida...)
