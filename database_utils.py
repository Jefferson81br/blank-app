import streamlit as st

def buscar_usuario(supabase, username):
    """Busca um usuário pelo username no banco."""
    try:
        return supabase.table("usuarios").select("*").eq("username", username).execute()
    except Exception as e:
        st.error(f"Erro ao consultar banco: {e}")
        return None

def cadastrar_usuario(supabase, dados):
    """Insere um novo usuário na tabela."""
    return supabase.table("usuarios").insert(dados).execute()

def buscar_todos_usuarios(supabase):
    """Retorna a lista de todos os usuários cadastrados."""
    try:
        return supabase.table("usuarios").select("*").order("nome").execute()
    except Exception as e:
        st.error(f"Erro ao buscar usuários: {e}")
        return None
