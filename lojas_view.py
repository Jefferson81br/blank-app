import streamlit as st
import database_utils as db

def gerenciar_lojas(supabase):
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
