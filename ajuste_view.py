import streamlit as st
import database_utils as db
from datetime import date

def renderizar_tela(supabase, user):
    st.title("⚙️ Ajustes de Sistema")
    st.markdown("Utilize esta tela para realizar ajustes manuais de saldos ou correções administrativas.")

    if user['funcao'] not in ['admin', 'proprietario']:
        st.error("Acesso restrito a Administradores.")
        st.stop()

    with st.container(border=True):
        st.subheader("Novo Ajuste Manual")
        
        col1, col2 = st.columns(2)
        
        # Busca lojas para o ajuste
        lojas_res = db.buscar_lojas(supabase)
        mapa_lojas = {l['nome']: l['id'] for l in lojas_res.data} if lojas_res.data else {}
        
        loja_sel = col1.selectbox("Selecione a Unidade:", options=list(mapa_lojas.keys()))
        data_ajuste = col2.date_input("Data do Ajuste:", value=date.today())
        
        tipo_ajuste = st.selectbox("Tipo de Ajuste:", ["Sobra Manual", "Falta Manual", "Ajuste de Cartão", "Outros"])
        valor = st.number_input("Valor do Ajuste (R$):", min_value=0.0, format="%.2f")
        obs = st.text_area("Justificativa do Ajuste:", placeholder="Descreva detalhadamente o motivo deste ajuste...")

        if st.button("Confirmar Ajuste", type="primary"):
            if valor > 0 and obs:
                # Aqui você chamará uma função no database_utils para salvar
                # Exemplo: db.salvar_ajuste(supabase, {...})
                st.success("Ajuste registrado com sucesso!")
            else:
                st.warning("Preencha o valor e a justificativa.")
