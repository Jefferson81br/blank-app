import bcrypt

def gerar_hash_senha(senha_plana):
    """Transforma senha comum em Hash seguro."""
    # O 'salt' adiciona uma camada aleatória de segurança
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(senha_plana.encode('utf-8'), salt).decode('utf-8')

def verificar_senha(senha_digitada, senha_hash_banco):
    """Compara a senha digitada com o Hash salvo no banco."""
    return bcrypt.checkpw(senha_digitada.encode('utf-8'), senha_hash_banco.encode('utf-8'))
