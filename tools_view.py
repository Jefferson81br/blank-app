import streamlit as st
import database_utils as db
from datetime import datetime

def renderizar_tela(supabase, user):
    st.title("🛠️ Ferramentas do Sistema")
    
    # Trava de segurança para o seu ID de desenvolvedor
    if user['id'] != 'b0439cb9-caa3-40dd-9f78-40ca3c9d80d8':
        st.error("Acesso restrito.")
        st.stop()

    row1_col1, row1_col2 = st.columns(2)

    # QUADRADO 1: BANCO DE DADOS
    with row1_col1:
        with st.container(border=True):
            st.subheader("🗄️ Banco de Dados")
            st.write("Gere um arquivo .sql completo (Lojas, Usuários e Fechamentos) para recuperação de desastres.")
            
            # O backup SQL é gerado apenas quando o botão de download é solicitado
            if st.button("📥 Preparar Backup SQL", use_container_width=True):
                with st.spinner("Extraindo dados do Supabase..."):
                    try:
                        conteudo_sql = db.gerar_sql_dump(supabase)
                        
                        st.download_button(
                            label="💾 Baixar Arquivo .sql",
                            data=conteudo_sql,
                            file_name=f"farma_gestor_backup_{datetime.now().strftime('%Y%m%d_%H%M')}.sql",
                            mime="text/plain",
                            use_container_width=True
                        )
                        st.success("Cópia de segurança pronta para download.")
                    except Exception as e:
                        st.error(f"Falha ao gerar dump: {e}")

    # Outros blocos vazios para futuras ferramentas
    with row1_col2:
        with st.container(border=True):
            st.subheader("📂 Exportação")
            st.write("Espaço reservado.")

    st.divider()
    st.caption(f"Logado como desenvolvedor: {user['nome']}")
