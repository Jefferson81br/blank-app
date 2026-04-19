import streamlit as st

def renderizar_tela(supabase, user):
    st.title("🏠 Início")
    
    st.markdown(f"""
        ### Bem-vindo(a), {user['nome']}!
        
        Este é o painel central do **Farma Gestor 1.0**. 
        Utilize o menu lateral para navegar entre as funcionalidades.
        
        ---
        #### ℹ️ Guia de Utilização (Em breve)
        Aqui você encontrará instruções detalhadas sobre:
        * **Dashboard:** Visualização de metas e resultados.
        * **Lançamentos:** Como preencher o caixa diário corretamente.
        * **Auditoria:** Processo de conferência e feedbacks.
        * **Relatórios:** Extração de dados consolidados.
        
        ---
        *Versão do Sistema: 1.2.0*
    """)
