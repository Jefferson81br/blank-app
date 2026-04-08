import streamlit as st
import database_utils as db
import auth_utils as auth

def gerenciar_usuarios(supabase, user):
    st.title("👥 Gestão de Usuários")
    usuarios = db.buscar_todos_usuarios(supabase)
    lojas = db.buscar_lojas(supabase)
    mapa_lojas = {l['id']: l['nome'] for l in lojas.data} if lojas.data else {}
    
    if usuarios and usuarios.data:
        for u in usuarios.data:
            n_loja = mapa_lojas.get(u['unidade_id'], "Admin/Geral")
            with st.expander(f"{u['nome']} - {n_loja} (@{u['username']})"):
                c1, c2, c3 = st.columns([2,1,1])
                c1.write(f"E-mail: {u['email']} | Função: {u['funcao']}")
                if c2.popover("🔑 Resetar").button("Confirmar Reset", key=f"rs_{u['id']}"):
                    st.info("Reset disponível.")
                if c3.button("Excluir", key=f"ex_{u['id']}", use_container_width=True):
                    supabase.table("usuarios").delete().eq("id", u['id']).execute(); st.rerun()

def adicionar_usuario(supabase):
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
                db.cadastrar_usuario(supabase, {
                    "nome": nome_c, "sobrenome": sobrenome_c, "email": email_c,
                    "username": user_c, "senha_hash": auth.gerar_hash_senha(pass_c),
                    "funcao": func_c, "unidade_id": dict_lojas.get(loja_sel)
                })
                st.success("Cadastrado!")
            else: st.warning("Preencha tudo.")
