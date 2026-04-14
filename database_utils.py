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

def atualizar_senha_usuario(supabase, user_id, novo_hash):
    """Atualiza o hash da senha de um usuário específico."""
    try:
        return supabase.table("usuarios").update({"senha_hash": novo_hash}).eq("id", user_id).execute()
    except Exception as e:
        st.error(f"Erro ao atualizar senha no banco: {e}")
        return None

def buscar_lojas(supabase):
    return supabase.table("lojas").select("*").order("nome").execute()



def cadastrar_loja(supabase, dados):
    return supabase.table("lojas").insert(dados).execute()

def atualizar_loja(supabase, loja_id, dados):
    return supabase.table("lojas").update(dados).eq("id", loja_id).execute()

def fazer_upload_print(supabase, arquivo, caminho_destino):
    """Envia uma imagem para o Storage e retorna a URL pública."""
    try:
        # Lê os bytes do arquivo enviado pelo Streamlit
        conteudo = arquivo.getvalue()
        # Faz o upload
        supabase.storage.from_("comprovantes").upload(caminho_destino, conteudo)
        # Retorna a URL pública do arquivo
        return supabase.storage.from_("comprovantes").get_public_url(caminho_destino)
    except Exception as e:
        st.error(f"Erro no upload da imagem: {e}")
        return None

def salvar_fechamento(supabase, dados):
    """Salva os dados de fechamento na tabela e trata erros de duplicidade."""
    try:
        res = supabase.table("fechamentos").insert(dados).execute()
        return True, res
    except Exception as e:
        # Verifica se o erro é de chave duplicada (código 23505 no PostgreSQL)
        erro_str = str(e)
        if "23505" in erro_str:
            return False, "Este dia já possui um lançamento para esta loja."
        else:
            return False, f"Erro inesperado: {erro_str}"
def buscar_fechamento_multiplas_lojas(supabase, lista_loja_ids, data_inicio, data_fim):
    """Busca lançamentos de várias lojas ao mesmo tempo."""
    try:
        return supabase.table("fechamentos")\
            .select("*")\
            .in_("loja_id", lista_loja_ids)\
            .gte("data_fechamento", data_inicio)\
            .lte("data_fechamento", data_fim)\
            .order("data_fechamento")\
            .execute()
    except Exception as e:
        st.error(f"Erro ao buscar dados: {e}")
        return None

def buscar_fechamento_por_data(supabase, loja_id, data_inicio, data_fim):
    """Busca lançamentos em um intervalo de datas para uma loja específica."""
    try:
        return supabase.table("fechamentos")\
            .select("*")\
            .eq("loja_id", loja_id)\
            .gte("data_fechamento", data_inicio)\
            .lte("data_fechamento", data_fim)\
            .order("data_fechamento")\
            .execute()
    except Exception as e:
        st.error(f"Erro ao buscar dados: {e}")
        return None

def atualizar_auditoria(supabase, registro_id, dados):
    """
    Atualiza os campos de auditoria em um registro de fechamento existente.
    """
    try:
        res = supabase.table("fechamentos").update(dados).eq("id", registro_id).execute()
        # Se res.data existe, a atualização foi bem sucedida
        return len(res.data) > 0
    except Exception as e:
        print(f"Erro ao atualizar auditoria: {e}")
        return False
