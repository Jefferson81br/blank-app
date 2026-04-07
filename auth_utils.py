def verificar_senha(senha_digitada, senha_banco):
    # Por enquanto comparação direta, depois usaremos Bcrypt aqui
    return senha_digitada == senha_banco
