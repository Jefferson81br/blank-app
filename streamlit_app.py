import streamlit as st
from supabase import create_client, Client
import database_utils as db  # Importa suas funções de banco
import auth_utils as auth    # Importa sua lógica de senha

# IMPORTAÇÃO DOS MÓDULOS DE TELAS
import dashboard_view
import lancamento_view
import usuarios_view
import lojas_view
import auditoria_view  # Novo módulo de auditoria

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
    
    # Botões comuns
    if st.sidebar.button("📊 Dashboard", use_container_width=True):
        st.session_state.pagina_ativa = "📊 Dashboard"; st.rerun()

    # Menu Administrativo
    if user['funcao'] == 'admin':
        if st.sidebar.button("👥 Consultar Usuários", use_container_width=True):
            st.session_state.pagina_ativa = "👥 Consultar Usuários"; st.rerun()
        if st.sidebar.button("➕ Adicionar Usuário", use_container_width=True):
            st.session_state.pagina_ativa = "➕ Adicionar Usuário"; st.rerun()
        if st.sidebar.button("🏢 Consultar Lojas", use_container_width=True):
            st.session_state.pagina_ativa = "🏢 Consultar Lojas"; st.rerun()

    # Menu de Auditoria (Apenas Admin e Proprietário)
    if user['funcao'] in ['admin', 'proprietario']:
        if st.sidebar.button("⚖️ Auditoria / Correção", use_container_width=True):
            st.session_state.pagina_ativa = "⚖️ Auditoria / Correção"; st.rerun()
        if st.sidebar.button("📋 Relatórios", use_container_width=True):
            st.session_state.tela_atual = "relatorios"; st.rerun()
    
    # Menu de Lançamento (Gerente e Admin)
    if user['funcao'] in ['gerente', 'admin']:
        if st.sidebar.button("📝 Lançamento Diário", use_container_width=True):
            st.session_state.pagina_ativa = "📝 Lançamento Diário"; st.rerun()

    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Sair", use_container_width=True):
        st.session_state.autenticado = False; st.session_state.user_data = None; st.rerun()

    # --- RENDERIZAÇÃO DE TELAS (O MAESTRO) ---
    escolha = st.session_state.pagina_ativa

    if escolha == "📊 Dashboard":
        dashboard_view.renderizar_tela(supabase, user)

    elif escolha == "📝 Lançamento Diário":
        lancamento_view.renderizar_tela(supabase, user)

    elif escolha == "⚖️ Auditoria / Correção":
        auditoria_view.renderizar_tela(supabase, user)

    elif escolha == "👥 Consultar Usuários":
        usuarios_view.gerenciar_usuarios(supabase, user)

    elif escolha == "➕ Adicionar Usuário":
        usuarios_view.adicionar_usuario(supabase)

    elif escolha == "🏢 Consultar Lojas":
        lojas_view.gerenciar_lojas(supabase)
