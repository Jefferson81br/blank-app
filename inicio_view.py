import streamlit as st

def renderizar_tela(supabase, user):
    # Cabeçalho com Estilo Atualizado para v1.4
    st.markdown(f"""
        <div style="background-color: #1e1e1e; padding: 20px; border-radius: 15px; border-left: 8px solid #00ff00; margin-bottom: 25px;">
            <h1 style="margin:0; color: white;">🏠 Farma Gestor 1.4</h1>
            <p style="font-size: 18px; color: #aaa;">Bem-vindo(a), <b>{user['nome']}</b>! Este é o seu painel central de controle.</p>
        </div>
    """, unsafe_allow_html=True)

    # --- NOVIDADES DA VERSÃO 1.4 ---
    with st.expander("🚀 NOVIDADES DA VERSÃO 1.4", expanded=True):
        st.markdown("#### 📋 Relatórios Expandidos e Exportação em PDF")
        st.write("O módulo de relatórios foi totalmente refinado para dar maior poder de análise e conformidade:")
        
        # Caixa informativa sobre a exportação
        exportacao_html = """
        <div style="background-color: #262626; padding: 15px; border-radius: 10px; border: 1px solid #333; margin: 10px 0; color: white;">
            <ul style="margin:0; padding-left: 20px;">
                <li><b>Visualização Completa:</b> Exibição de todas as colunas de conferência do caixa (Cartão, Crediário, Dinheiro, Boleto, Ifood, PBM, Pix, VC, FAPP, Vlink, Total, Despesas, Quebra e Auditoria).</li>
                <li><b>Exportação em PDF Executivo:</b> Geração nativa de arquivos PDF em modo paisagem, contendo rodapé assinado com data, hora e o nome do usuário que emitiu o relatório.</li>
                <li><b>Segurança por Filial:</b> Filtros de busca bloqueados automaticamente para gerentes, permitindo apenas a consulta da sua própria unidade.</li>
            </ul>
        </div>
        """
        st.markdown(exportacao_html, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### 🗑️ Gestão de Comprovantes na Auditoria")
        st.write("Agora o Auditor tem a possibilidade de **excluir anexos incorretos ou duplicados** enviados por engano pelos gerentes. A operação conta com confirmação dupla de segurança e remove o arquivo permanentemente do servidor.")

        st.markdown("---")
        st.markdown("#### ⚙️ Ajustes Financeiros Robustos contra Nulos")
        st.write("O módulo de Ajustes Administrativos foi blindado contra campos sem preenchimento (`NULL`) e recebeu o mapeamento completo das saídas, incluindo a coluna de **Outros** no recálculo automático de saldo de quebras.")

        st.markdown("---")
        st.markdown("#### 🛡️ Segurança de Login & Correção de Bugs")
        st.write("A aplicação foi protegida contra o cenário de Gerentes cadastrados sem loja vinculada (que causava o travamento da tela preta). O sistema agora detecta a inconsistência no login, bloqueia a tela com um aviso amigável e orienta o usuário a procurar o suporte administrativo.")

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
                * **📋 Relatórios:** Extração de dados consolidados com novos filtros e exportação em PDF.
                """)
            with col2:
                st.markdown("""
                **Controle Financeiro:**
                * **🔍 Auditoria:** Conferência diária de lançamentos com permissão de exclusão de mídias.
                * **🛠️ Correções:** Ajustar valores pontuais e recalcular saldos retroativamente.
                """)

    st.divider()
    
    # Rodapé
    c1, c2 = st.columns([4, 1])
    with c1:
        st.caption("Versão do Sistema: 1.4.0 | Suporte Técnico: Jefferson Admin")
    with c2:
        st.info("🚪 **Sair:** Menu lateral.")

    st.warning("**Lembrete de Segurança:** O banco de dados opera sob políticas estritas de Row-Level Security (RLS). Mantenha suas credenciais em sigilo.")
