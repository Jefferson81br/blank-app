import bcrypt

def gerar_hash_senha(senha_plana):
    salt = bcrypt.gensalt()
    # Transforma a string em bytes, gera o hash e volta para string
    return bcrypt.hashpw(senha_plana.encode('utf-8'), salt).decode('utf-8')

def verificar_senha(senha_digitada, senha_hash_banco):
    try:
        # Tenta verificar se é um hash válido do bcrypt
        return bcrypt.checkpw(senha_digitada.encode('utf-8'), senha_hash_banco.encode('utf-8'))
    except Exception:
        # Se der erro (ex: a senha no banco não é um hash), retorna False
        return False
