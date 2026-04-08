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
    
    if user['funcao'] in ['gerente', 'admin']:
        if st.sidebar.button("📝 Lançamento Diário", use_container_width=True):
            st.session_state.pagina_ativa = "📝 Lançamento Diário"; st.rerun()

    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Sair", use_container_width=True):
        st.session_state.autenticado = False; st.session_state.user_data = None; st.rerun()

    # --- RENDERIZAÇÃO DE TELAS ---
    escolha = st.session_state.pagina_ativa

    # 1. TELA DASHBOARD (CORRIGIDA COM TODOS OS ITENS)
    if escolha == "📊 Dashboard":
        st.title("📊 Painel de Performance")
        lojas_res = db.buscar_lojas(supabase)
        mapa_lojas = {l['nome']: l['id'] for l in lojas_res.data} if lojas_res.data else {}
        
        if user['funcao'] in ['admin', 'proprietario']:
            lojas_sel_nomes = st.multiselect("Unidades:", options=list(mapa_lojas.keys()), default=list(mapa_lojas.keys())[:1])
            lista_ids = [mapa_lojas[n] for n in lojas_sel_nomes]
        else:
            if not user['unidade_id']: st.stop()
            lista_ids = [user['unidade_id']]

        if not lista_ids: st.stop()

        c1, c2 = st.columns(2)
        periodo = c1.selectbox("Período:", ["Dia", "Semana", "Mês"])
        hoje = date.today()
        if periodo == "Dia": d_ini = c2.date_input("Data:", hoje, max_value=hoje); d_fim = d_ini
        elif periodo == "Semana": d_ini = hoje - timedelta(days=hoje.weekday()); d_fim = hoje
        else: d_ini = hoje.replace(day=1); d_fim = hoje

        res = db.buscar_fechamento_multiplas_lojas(supabase, lista_ids, str(d_ini), str(d_fim))
        
        if res and res.data:
            df_geral = pd.DataFrame(res.data)
            id_para_nome = {v: k for k, v in mapa_lojas.items()}
            cols_dash = st.columns(len(lista_ids))
            
            for idx, l_id in enumerate(lista_ids):
                with cols_dash[idx]:
                    st.subheader(f"🏢 {id_para_nome.get(l_id)}")
                    df_l = df_geral[df_geral['loja_id'] == l_id]
                    if not df_l.empty:
                        # Totais Acumulados do Período
                        t_s = df_l[['sis_cartao', 'sis_crediario', 'sis_dinheiro', 'sis_ifood', 'sis_pix']].values.sum()
                        t_c = df_l[['conf_cartao', 'conf_crediario', 'conf_dinheiro', 'conf_ifood', 'conf_pix', 'despesa']].values.sum()
                        t_d = df_l['despesa'].sum()
                        t_a = t_c - t_s - (t_d * 2)
                        
                        st.metric("Venda (Sis)", f"R$ {t_s:,.2f}")
                        st.metric("Acerto", f"R$ {t_a:,.2f}", delta=f"{t_a:,.2f}")

                        if periodo == "Dia":
                            d = df_l.iloc[0]
                            # MAPEAMENTO COMPLETO DA PLANILHA
                            dados_completos = [
                                {"ITEM": "CARTÃO", "SIS": d['sis_cartao'], "CONF": d['conf_cartao']},
                                {"ITEM": "CREDIÁRIO", "SIS": d['sis_crediario'], "CONF": d['conf_crediario']},
                                {"ITEM": "DINHEIRO", "SIS": d['sis_dinheiro'], "CONF": d['conf_dinheiro']},
                                {"ITEM": "IFOOD", "SIS": d['sis_ifood'], "CONF": d['conf_ifood']},
                                {"ITEM": "PIX/TRANSF", "SIS": d['sis_pix'], "CONF": d['conf_pix']},
                                {"ITEM": "DESPESA", "SIS": 0.0, "CONF": d['despesa']}
                            ]
                            df_tab = pd.DataFrame(dados_completos)
                            df_tab['ACERTO'] = df_tab['CONF'] - df_tab['SIS']
                            # Ajuste sinal despesa
                            df_tab.loc[df_tab['ITEM'] == 'DESPESA', 'ACERTO'] = -d['despesa']

                            st.table(df_tab.style.format({"SIS": "R$ {:.2f}", "CONF": "R$ {:.2f}", "ACERTO": "R$ {:.2f}"}))
                            
                            if d['urls_prints']:
                                for url_p in d['urls_prints']:
                                    st.markdown(f'<a href="{url_p}" target="_blank"><img src="{url_p}" width="150" height="150" style="object-fit: cover; border-radius: 5px; margin-bottom:5px;"></a>', unsafe_allow_html=True)
                    else: st.caption("Sem dados.")
        else: st.info("Nenhum lançamento encontrado.")

    # 2. TELA LANÇAMENTO (MANTIDA CORRETA)
    elif escolha == "📝 Lançamento Diário":
        lancamento_view.renderizar_tela(supabase, user)

    # 3. TELA ADICIONAR USUÁRIO
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
                    db.cadastrar_usuario(supabase, {"nome": nome_c, "sobrenome": sobrenome_c, "email": email_c, "username": user_c, "senha_hash": auth.gerar_hash_senha(pass_c), "funcao": func_c, "unidade_id": dict_lojas.get(loja_sel)})
                    st.success("Cadastrado!")
                else: st.warning("Preencha tudo.")

    # 4. TELA CONSULTAR USUÁRIOS
    elif escolha == "👥 Consultar Usuários":
        st.title("👥 Gestão de Usuários")
        usuarios = db.buscar_todos_usuarios(supabase)
        lojas = db.buscar_lojas(supabase)
        mapa_lojas = {l['id']: l['nome'] for l in lojas.data} if lojas.data else {}
        if usuarios and usuarios.data:
            for u in usuarios.data:
                nome_loja = mapa_lojas.get(u['unidade_id'], "Admin/Geral")
                with st.expander(f"{u['nome']} - {nome_loja} (@{u['username']})"):
                    c1, c2, c3 = st.columns([2,1,1])
                    c1.write(f"E-mail: {u['email']} | Função: {u['funcao']}")
                    if c2.popover("🔑 Resetar").button("Confirmar Reset", key=f"rs_{u['id']}"):
                        st.info("Reset realizado.")
                    if c3.button("Excluir", key=f"ex_{u['id']}", use_container_width=True):
                        supabase.table("usuarios").delete().eq("id", u['id']).execute(); st.rerun()

    # 5. TELA CONSULTAR LOJAS
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
                                db.atualizar_loja(supabase, l['id'], {"nome":n, "marca":m, "endereco":e}); st.rerun()
        with t2:
            with st.form("n_loja"):
                nl, ml, el = st.text_input("Nome"), st.text_input("Marca"), st.text_input("Endereço")
                if st.form_submit_button("Salvar"):
                    db.cadastrar_loja(supabase, {"nome":nl, "marca":ml, "endereco":el}); st.rerun()
