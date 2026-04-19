import streamlit as st

def renderizar_tela(supabase, user):
    # Cabeçalho com Estilo
    st.markdown(f"""
        <div style="background-color: #1e1e1e; padding: 20px; border-radius: 15px; border-left: 8px solid #00ff00; margin-bottom: 25px;">
            <h1 style="margin:0; color: white;">🏠 Farma Gestor 1.2</h1>
            <p style="font-size: 18px; color: #aaa;">Bem-vindo(a), <b>{user['nome']}</b>! Este é o seu painel central de controle.</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("### ℹ️ Guia de Utilização do Sistema")
    st.write("Selecione o seu perfil abaixo para entender as funcionalidades disponíveis:")

    # --- ABA DE GERENTES ---
    with st.expander("👨‍💼 INSTRUÇÕES PARA GERENTES", expanded=(user['funcao'] == 'gerente')):
        st.markdown("""
        * **👤 Minha Conta:** Alteração de sua senha pessoal de acesso.
        * **📊 Dashboard:** Consulta rápida aos lançamentos da sua loja através da seleção da data.
        * **📉 Quebras de Caixa:** Acompanhe o histórico de diferenças (faltas/sobras) diárias e o acumulado do mês.
        * **📝 Lançamento Diário (Principal):**
            * **Atenção Máxima:** Uma vez salvo, o lançamento **não pode ser editado** por você.
            * **Comprovantes:** É obrigatório anexar os prints do sistema Alpha7, comprovantes de cartões e despesas.
            * **Observações:** Utilize este campo para justificar qualquer diferença ou detalhar despesas.
            * **Feedbacks:** Fique atento a esta tela para ler mensagens do Gestor/Financeiro solicitando correções.
            * **Bloqueio:** O sistema não permite dois lançamentos para a mesma data.
            * **Erros:** Caso erre, entre em contato com o Gestor para que ele inative o registro e você possa refazer.
        """)

    # --- ABA DE ADMINISTRADORES / GESTORES ---
    if user['funcao'] in ['admin', 'proprietario', 'financeiro']:
        with st.expander("⚖️ INSTRUÇÕES PARA ADMINISTRADORES E GESTORES", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                **Gestão Estrutural:**
                * **👥 Usuários:** Criar, excluir e resetar senhas da equipe.
                * **🏢 Lojas:** Gerenciar o cadastro das unidades da rede.
                * **📋 Relatórios:** Extração de dados consolidados em CSV para contabilidade.
                * **📉 Quebras:** Visão macro de todas as lojas simultaneamente.
                """)
            
            with col2:
                st.markdown("""
                **Controle Financeiro:**
                * **🔍 Auditoria:** Conferência diária dos lançamentos. Aqui você valida os dados, checa as fotos e envia feedbacks.
                * **🛠️ Correções:** Em Auditoria, você pode **desativar** um lançamento incorreto para que o gerente possa lançar novamente.
                * **📝 Lançamento:** Você também pode lançar, mas lembre-se de selecionar a unidade correta antes.
                """)

    st.divider()

    # Rodapé com Destaque para o Botão de Saída
    c1, c2 = st.columns([4, 1])
    with c1:
        st.caption("Versão do Sistema: 1.2.0 | Suporte Técnico: Jefferson Admin")
    with c2:
        st.info("🚪 **Sair:** Utilize o botão ao final do menu lateral para deslogar com segurança.")

    # Alerta de Segurança Crítico para todos
    st.warning("""
        **Lembrete de Segurança:** Nunca compartilhe sua senha. Todos os lançamentos e auditorias ficam registrados com o nome do usuário responsável.
    """)
