import streamlit as st
import pandas as pd
from datetime import date
import database_utils as db

def renderizar_tela(supabase, user):
    st.title("⚖️ Auditoria de Fechamentos")

    # --- FILTROS DE BUSCA ---
    lojas_res = db.buscar_lojas(supabase)
    mapa_lojas = {l['nome']: l['id'] for l in lojas_res.data} if lojas_res.data else {}
    
    c1, c2, c3 = st.columns([2, 1, 1])
    loja_nome = c1.selectbox("Selecione a Unidade:", options=list(mapa_lojas.keys()))
    data_sel = c2.date_input("Data do Movimento:", value=date.today())
    loja_id = mapa_lojas[loja_nome]

    # Busca o registro específico
    res = db.buscar_fechamento_multiplas_lojas(supabase, [loja_id], str(data_sel), str(data_sel))

    if res and res.data:
        d = res.data[0]
        
        # Colunas: [Dados à Esquerda] [Interação à Direita]
        col_dados, col_auditoria = st.columns([2.5, 2])

        with col_dados:
            st.subheader("📋 Conferência de Valores")
            
            # --- GRUPO 1: ENTRADAS ---
            entradas = [
                {"Descrição": "CARTÃO", "Sistema": d['sis_cartao'], "Conferência": d['conf_cartao']},
                {"Descrição": "CREDIÁRIO", "Sistema": d['sis_crediario'], "Conferência": d['conf_crediario']},
                {"Descrição": "DINHEIRO", "Sistema": d['sis_dinheiro'], "Conferência": d['conf_dinheiro']},
                {"Descrição": "BOLETO", "Sistema": d['sis_boleto'], "Conferência": d['conf_boleto']},
                {"Descrição": "IFOOD", "Sistema": d['sis_ifood'], "Conferência": d['conf_ifood']},
                {"Descrição": "PBM", "Sistema": d['sis_pbm'], "Conferência": d['conf_pbm']},
                {"Descrição": "PIX / TRANSF", "Sistema": d['sis_pix'], "Conferência": d['conf_pix']},
                {"Descrição": "VALE COMPRA", "Sistema": d['sis_vale_compra'], "Conferência": d['conf_vale_compra']},
                {"Descrição": "FAPP", "Sistema": d['sis_fapp'], "Conferência": d['conf_fapp']},
                {"Descrição": "VLINK", "Sistema": d['sis_vlink'], "Conferência": d['conf_vlink']},
            ]
            df_ent = pd.DataFrame(entradas)
            df_ent['Acerto'] = df_ent['Conferência'] - df_ent['Sistema']
            
            st.table(df_ent.style.format({"Sistema": "{:.2f}", "Conferência": "{:.2f}", "Acerto": "{:.2f}"}))
            
            t_conf_ent = df_ent['Conferência'].sum()
            t_ace_ent = df_ent['Acerto'].sum()

            # --- GRUPO 2: SAÍDAS ---
            saidas = [
                {"Descrição": "DESPESA", "Valor": d['conf_despesa']},
                {"Descrição": "VALE FUNC.", "Valor": d['conf_vale_func']},
                {"Descrição": "DEV. CARTÃO", "Valor": d['conf_dev_cartao']},
                {"Descrição": "OUTROS", "Valor": d['conf_outros']}
            ]
            df_sai = pd.DataFrame(saidas)
            st.table(df_sai.style.format({"Valor": "{:.2f}"}))
            
            t_conf_sai = df_sai['Valor'].sum()
            saldo = t_conf_ent - t_conf_sai

            # Totais em destaque
            st.markdown(f"""
                <div style='background-color:#1a1a1a; padding:15px; border-radius:10px; border:1px solid #333;'>
                    <span style='color:#aaa;'>SALDO FINAL AUDITADO:</span><br>
                    <h2 style='color:#00ff00; margin:0;'>R$ {saldo:,.2f}</h2>
                    <span style='color:#ff4b4b;'>Diferença total de acerto: R$ {t_ace_ent:,.2f}</span>
                </div>
            """, unsafe_allow_html=True)

        with col_auditoria:
            # 1. Observações e Comprovantes (Visão do Auditor)
            st.subheader("🔍 Evidências")
            with st.container(border=True):
                st.markdown("**📝 Observações do Gerente:**")
                st.info(d['observacoes'] if d['observacoes'] else "Nenhuma observação enviada.")
                
                st.markdown("**🖼️ Anexos:**")
                if d.get('urls_prints'):
                    cols_img = st.columns(3)
                    for idx, url in enumerate(d['urls_prints']):
                        with cols_img[idx % 3]:
                            st.image(url, use_container_width=True)
                else:
                    st.warning("Sem comprovantes.")

            st.write("---")
            
            # 2. Formulário de Auditoria
            st.subheader("✍️ Parecer do Financeiro")
            
            # Status atual
            status_atual = d.get('status_auditoria', 'Pendente')
            st.caption(f"Status Atual: **{status_atual}**")
            if d.get('auditado_por'):
                st.caption(f"Última revisão por: {d['auditado_por']}")

            with st.form("form_auditoria"):
                novo_feedback = st.text_area("Réplica / Feedback para o Gerente:", value=d.get('replica_gestor', ''))
                confirmar = st.checkbox("Marcar como CONFERIDO / AUDITADO", value=(status_atual == 'Auditado'))
                
                if st.form_submit_button("💾 SALVAR AUDITORIA", use_container_width=True):
                    dados_update = {
                        "replica_gestor": novo_feedback,
                        "status_auditoria": "Auditado" if confirmar else "Pendente",
                        "auditado_por": user['nome'] # Registra quem está logado fazendo a auditoria
                    }
                    
                    # Chamada para atualizar no banco
                    sucesso = db.atualizar_auditoria(supabase, d['id'], dados_update)
                    if sucesso:
                        st.success("Auditoria salva com sucesso!")
                        st.rerun()
                    else:
                        st.error("Erro ao atualizar banco de dados.")

    else:
        st.info("Nenhum fechamento encontrado para esta unidade na data selecionada.")
