import streamlit as st
import database_utils as db

def renderizar_tela(supabase, user):
    # Cabeçalho da Tela
    st.title("🛠️ Ferramentas do Sistema")
    st.markdown("Área destinada a utilitários de suporte técnico, manutenção de banco de dados e ferramentas de produtividade.")

    # Verificação de segurança (Apenas para o seu perfil técnico)
    if user['funcao'] not in ['admin', 'proprietario']:
        st.error("Acesso restrito ao Administrador do Sistema.")
        st.stop()

    # Espaço reservado para as suas futuras ferramentas
    st.info("Esta tela está pronta para receber novos módulos e scripts de automação.")
    
    # Exemplo de organização por colunas para ferramentas futuras
    col1, col2 = st.columns(2)
    
    with col1:
        with st.container(border=True):
            st.subheader("🧹 Manutenção")
            st.write("Espaço para limpeza de cache ou logs antigos.")
            if st.button("Limpar Cache do App", use_container_width=True):
                st.cache_data.clear()
                st.success("Cache limpo com sucesso!")

    with col2:
        with st.container(border=True):
            st.subheader("📂 Exportação")
            st.write("Backup rápido de tabelas críticas em formato JSON/CSV.")
            st.button("Gerar Backup de Lojas", use_container_width=True, disabled=True)
