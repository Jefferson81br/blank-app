import streamlit as st
import database_utils as db
import auth_utils as auth

def gerenciar_usuarios(supabase, user):
    st.title("👥 Gestão de Usuários 2")
    
    usuarios = db.buscar_todos_usuarios(supabase)
    lojas = db.buscar_lojas(supabase)
    mapa_lojas = {l['id']: l['nome'] for l in lojas.data} if lojas.data else {}
    dict_lojas_invertido = {l['nome']: l['id'] for l in lojas.data} if lojas.data else {}

    if not usuarios or not usuarios.data:
        st.info("Nenhum usuário cadastrado.")
        return

    # --- FILTRO RÁPIDO ---
    col_b1, col_b2 = st.columns([2, 1])
    termo_busca = col_b1.text_input("🔍 Buscar por nome ou login:", placeholder="Digite para filtrar...").lower()
    loja_filtro = col_b2.selectbox("Filtrar por Unidade:", ["Todas"] + list(dict_lojas_invertido.keys()))

    usuarios_filtrados = [
        u for u in usuarios.data
        if (termo_busca in u.get('nome', '').lower() or termo_busca in u.get('username', '').lower())
        and (loja_filtro == "Todas" or mapa_lojas.get(u.get('unidade_id')) == loja_filtro)
    ]

    st.caption(f"Mostrando {len(usuarios_filtrados)} de {len(usuarios.data)} usuários.")

    for u in usuarios_filtrados:
        n_loja = mapa_lojas.get(u.get('unidade_id'), "Admin/Geral")
        with st.expander(f"{u['nome']} - {n_loja} (@{u['username']})"):
            c_info, c_acoes = st.columns([1.8, 1.2])

            with c_info:
                st.markdown(f"""
                    **Nome:** {u.get('nome', '')} {u.get('sobrenome', '') or ''}  
                    **Login:** `{u.get('username')}`  
                    **E-mail:** {u.get('email') or 'Não informado'}  
                    **Nível de Acesso:** `{u.get('funcao', 'gerente')}`  
                    **Unidade Vinculada:** {n_loja}
                """)

            with c_acoes:
                # --- 1. REDEFINIR SENHA ---
                with st.popover("🔑 Alterar Senha", use_container_width=True):
                    st.markdown(f"**Nova senha para @{u['username']}**")
                    nova_senha = st.text_input("Digite a nova senha:", type="password", key=f"nova_senha_{u['id']}")
                    confirma_senha = st.text_input("Confirme a nova senha:", type="password", key=f"conf_senha_{u['id']}")
                    
                    if st.button("Salvar Nova Senha", key=f"btn_salvar_senha_{u['id']}", use_container_width=True):
                        if not nova_senha:
                            st.warning("Informe uma senha válida.")
                        elif nova_senha != confirma_senha:
                            st.error("As senhas não conferem.")
                        elif len(nova_senha) < 4:
                            st.warning("A senha deve conter ao menos 4 caracteres.")
                        else:
                            hash_novo = auth.gerar_hash_senha(nova_senha)
                            res = supabase.table("usuarios").update({"senha_hash": hash_novo}).eq("id", u['id']).execute()
                            if res.data:
                                st.success("Senha alterada com sucesso!")
                                st.rerun()
                            else:
                                st.error("Erro ao atualizar a senha no banco.")

                # --- 2. EDITAR DADOS / UNIDADE ---
                with st.popover("✏️ Editar Perfil", use_container_width=True):
                    st.markdown(f"**Editar @{u['username']}**")
                    with st.form(f"form_edita_{u['id']}"):
                        e_nome = st.text_input("Nome", value=u.get('nome', ''))
                        e_sobrenome = st.text_input("Sobrenome", value=u.get('sobrenome', '') or '')
                        e_email = st.text_input("E-mail", value=u.get('email', '') or '')

                        lista_opcoes_loja = ["Nenhuma (Admin/Geral)"] + list(dict_lojas_invertido.keys())
                        loja_atual = n_loja if n_loja in dict_lojas_invertido else "Nenhuma (Admin/Geral)"
                        idx_loja = lista_opcoes_loja.index(loja_atual) if loja_atual in lista_opcoes_loja else 0
                        e_loja = st.selectbox("Unidade", options=lista_opcoes_loja, index=idx_loja)

                        niveis = ["gerente", "proprietario", "financeiro", "admin"]
                        idx_func = niveis.index(u.get('funcao', 'gerente')) if u.get('funcao') in niveis else 0
                        e_func = st.selectbox("Nível", options=niveis, index=idx_func)

                        if st.form_submit_button("Atualizar Cadastro", use_container_width=True):
                            id_loja_final = dict_lojas_invertido.get(e_loja) if e_loja != "Nenhuma (Admin/Geral)" else None
                            payload = {
                                "nome": e_nome,
                                "sobrenome": e_sobrenome,
                                "email": e_email,
                                "unidade_id": id_loja_final,
                                "funcao": e_func
                            }
                            supabase.table("usuarios").update(payload).eq("id", u['id']).execute()
                            st.success("Dados atualizados!")
                            st.rerun()

                # --- 3. EXCLUIR USUÁRIO (COM CONFIRMAÇÃO) ---
                if u['id'] != user.get('id'):
                    with st.popover("🗑️ Excluir", use_container_width=True):
                        st.write(f"Tem certeza que deseja excluir **@{u['username']}**?")
                        if st.button("Sim, excluir usuário", key=f"ex_{u['id']}", type="primary", use_container_width=True):
                            supabase.table("usuarios").delete().eq("id", u['id']).execute()
                            st.rerun()
                else:
                    st.caption("*(Sua própria conta)*")

def adicionar_usuario(supabase):
    st.title("➕ Cadastrar Novo Usuário")
    res_lojas = db.buscar_lojas(supabase)
    dict_lojas = {l['nome']: l['id'] for l in res_lojas.data} if res_lojas.data else {}
    
    with st.form("form_cadastro_usuario", clear_on_submit=True):
        c1, c2 = st.columns(2)
        nome_c = c1.text_input("Nome")
        sobrenome_c = c2.text_input("Sobrenome")
        email_c = c1.text_input("E-mail")
        loja_sel = c2.selectbox("Unidade", ["Nenhuma (Admin/Geral)"] + list(dict_lojas.keys()))
        user_c = c1.text_input("Login")
        pass_c = c2.text_input("Senha Inicial", type="password")
        func_c = st.selectbox("Nível", ["gerente", "proprietario", "financeiro", "admin"])
        
        if st.form_submit_button("Finalizar Cadastro", use_container_width=True):
            if nome_c and user_c and pass_c:
                unidade_id = dict_lojas.get(loja_sel) if loja_sel != "Nenhuma (Admin/Geral)" else None
                db.cadastrar_usuario(supabase, {
                    "nome": nome_c, 
                    "sobrenome": sobrenome_c, 
                    "email": email_c,
                    "username": user_c.strip().lower(), 
                    "senha_hash": auth.gerar_hash_senha(pass_c),
                    "funcao": func_c, 
                    "unidade_id": unidade_id
                })
                st.success("Usuário cadastrado com sucesso!")
            else:
                st.warning("Preencha Nome, Login e Senha Inicial obrigatoriamente.")
