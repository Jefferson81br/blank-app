import streamlit as st
import database_utils as db
import pandas as pd

def renderizar_tela(supabase, user):
    st.title("📉 Quebras de CX")
    
    st.markdown(f"""
        ### Monitoramento de Divergências
        Esta tela está em desenvolvimento. 
        Em breve, aqui você poderá consultar:
        * Ranking de quebras por unidade.
        * Histórico de faltas e sobras justificadas.
        * Gráficos de evolução de divergências.
        
        ---
        **Usuário atual:** {user['nome']}  
        **Unidade:** {user.get('unidade_id', 'Geral')}
    """)
