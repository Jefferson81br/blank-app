import streamlit as st

def renderizar_tela(supabase, user):
    # Cabeçalho com Estilo Atualizado para v1.3
    st.markdown(f"""
        <div style="background-color: #1e1e1e; padding: 20px; border-radius: 15px; border-left: 8px solid #00ff00; margin-bottom: 25px;">
            <h1 style="margin:0; color: white;">🏠 Farma Gestor 1.3</h1>
            <p style="font-size: 18px; color: #aaa;">Bem-vindo(a), <b>{user['nome']}</b>! Este é o seu painel central de controle.</p>
        </div>
    """, unsafe_allow_html=True)

    # --- NOVO: CHANGE LOG DA VERSÃO 1.3 (CORRIGIDO) ---
    with st.expander("🚀 NOVIDADES DA VERSÃO 1.3", expanded=True):
        # Usando Markdown puro para as listas para evitar erros de renderização de HTML
        st.markdown("#### ⚖️ Tela de Auditoria: Monitoramento Duplo")
        st.write("Agora, os botões de data contam com um sistema de **Indicadores Duplos** para facilitar a identificação de pendências:")
        
        # Caixa de Legenda usando uma única string HTML para evitar quebra de código
        legenda_html = """
        <div style="background-color: #262626; padding: 15px; border-radius: 10px; border: 1px solid #333; margin: 10px 0; color: white;">
            <p style="margin-bottom: 8px;"><b>📍 1º Marcador (Status Global):</b></p>
            <ul style="margin-top:0;">
                <li>🟡 <b>Pendente:</b> Lançamento ainda não auditado.</li>
                <li>✅ <b>Auditado:</b> Conferência financeira finalizada.</li>
            </ul>
            <p style="margin-bottom: 8px;"><b>📍 2º Marcador (Integridade Documental):</b></p>
            <ul style="margin-top:0;">
                <li>✅ <b>Completo:</b> Todos os 3 comprovantes (Sistema, Depósito e Despesas) conferidos.</li>
                <li>🟡 <b>Pendência:</b> Falta o check em pelo menos um dos comprovantes obrigatórios.</li>
            </ul>
            <p style="margin-top: 10px; font-size: 14px; color: #aaa;">
                <i>Exemplo: <b>✅🟡</b> significa que o dia foi auditado, mas ainda possui pendência de documentação.</i>
            </p>
        </div>
        """
        st.markdown(legenda_html, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### ➕ Autonomia do Auditor")
        st.write("O Auditor agora pode **incluir anexos extras** (esquecidos pelo gerente) diretamente na tela de auditoria, sem precisar inativar o lançamento.")
        
        st.markdown("---")
        st.markdown("#### 📋 Filtros Avançados em Relatórios")
        st.write("Além de loja e período, agora é possível extrair relatórios filtrando por **Status da Auditoria** ou **Integridade dos Comprovantes**.")

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
        """)

    # --- ABA DE ADMINISTRADORES / GESTORES ---
    if user['funcao'] in ['admin', 'proprietario', 'financeiro']:
        with st.expander("⚖️ INSTRUÇÕES PARA ADMINISTRADORES E GESTORES", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("""
                **Gestão Estrutural:**
                * **👥 Usuários:** Criar, excluir e resetar senhas da equipe.
                * **🏢 Lojas:** Gerenciar o cadastro das unidades da rede.
                * **📋 Relatórios:** Extração de dados consolidados com novos filtros.
                """)
            with col2:
                st.markdown("""
                **Controle Financeiro:**
                * **🔍 Auditoria:** Conferência diária dos lançamentos.
                * **🛠️ Correções:** Adicionar documentos ou inativar registros.
                """)

    st.divider()
    
    # Rodapé
    c1, c2 = st.columns([4, 1])
    with c1:
        st.caption("Versão do Sistema: 1.3.0 | Suporte Técnico: Jefferson Admin")
    with c2:
        st.info("🚪 **Sair:** Menu lateral.")

    st.warning("**Lembrete de Segurança:** Nunca compartilhe sua senha. Todos os logs são registrados.")
