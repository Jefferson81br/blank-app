import streamlit as st
import database_utils as db
import time

def renderizar_tela(supabase, user):
    st.title("🛠️ Ferramentas do Sistema")
    
    # Trava de segurança (Substitua pelo seu ID real)
    if user['id'] != 'b0439cb9-caa3-40dd-9f78-40ca3c9d80d8':
        st.error("Acesso restrito ao desenvolvedor principal.")
        st.stop()

    # --- PRIMEIRA LINHA ---
    row1_col1, row1_col2 = st.columns(2)

    with row1_col1:
        with st.container(border=True):
            st.subheader("🧹 Manutenção")
            st.write("Limpeza de cache e otimização do Streamlit.")
            if st.button("Limpar Cache do App", use_container_width=True, key="btn_cache"):
                st.cache_data.clear()
                st.success("Cache limpo!")

    with row1_col2:
        with st.container(border=True):
            st.subheader("📂 Exportação")
            st.write("Backup de tabelas críticas (Lojas/Usuários).")
            if st.button("Gerar Backup em CSV", use_container_width=True, key="btn_backup"):
                # Aqui você chamaria uma função do database_utils
                st.toast("Função em desenvolvimento...")

    # --- SEGUNDA LINHA ---
    row2_col1, row2_col2 = st.columns(2)

    with row2_col1:
        with st.container(border=True):
            st.subheader("🔍 Logs de Auditoria")
            st.write("Verificar quem inativou registros recentemente.")
            if st.button("Visualizar Logs", use_container_width=True, key="btn_logs"):
                st.toast("Buscando logs...")

    with row2_col2:
        with st.container(border=True):
            st.subheader("🧪 Testes / Debug")
            st.write("Verificar conexão e status do Supabase.")
            if st.button("Testar Conexão", use_container_width=True, key="btn_test"):
                with st.spinner("Pingando banco..."):
                    time.sleep(1)
                    st.success("Conexão OK!")

    st.divider()
    st.caption("Modo Desenvolvedor Ativo")
