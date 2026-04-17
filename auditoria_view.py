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
    
    # AJUSTE: Formato de data brasileiro no seletor
    data_sel = c2.date_input(
        "Data do Movimento:", 
        value=date.today(),
        format="DD/MM/YYYY"
    )
    
    loja_id = mapa_lojas[loja_nome]

    res = db.buscar_fechamento_multiplas_lojas(supabase, [loja_id], str(data_sel), str(data_sel))

    if res and res.data:
        d = res.data[0]
        # Mantendo proporção similar ao lançamento para consistência visual
        col_dados, col_auditoria = st.columns([2.2, 2])

        with col_dados:
            st.subheader("📋 Conferência de Valores")
            
            # --- GRUPO 1: ENTRADAS ---
            entradas = [
                {"Descrição": "CARTÃO", "Sistema": d['sis_cartao'], "Conferência": d['conf_cartao']},
                {"Descrição": "CREDIÁRIO", "Sistema": d['sis_crediario'], "Conferência": d['conf_crediario']},
                {"Descrição": "DINHEIRO", "Sistema": d['sis_dinheiro'], "Conferência": d['conf_dinheiro']},
                {"Descrição": "BOLETO", "Sistema": d.get('sis_boleto', 0), "Conferência": d.get('conf_boleto', 0)},
                {"Descrição": "IFOOD", "Sistema": d['sis_ifood'], "Conferência": d['conf_ifood']},
                {"Descrição": "PBM", "Sistema": d['sis_pbm'], "Conferência": d['conf_pbm']},
                {"Descrição": "PIX / TRANSF", "Sistema": d['sis_pix'], "Conferência": d['conf_pix']},
                {"Descrição": "VALE COMPRA", "Sistema": d['sis_vale_compra'], "Conferência": d['conf_vale_compra']},
                {"Descrição": "FAPP", "Sistema": d.get('sis_fapp', 0), "Conferência": d.get('conf_fapp', 0)},
                {"Descrição": "VLINK", "Sistema": d.get('sis_vlink', 0), "Conferência": d.get('conf_vlink', 0)},
            ]
            df_ent = pd.DataFrame(entradas)
            df_ent['Acerto'] = df_ent['Conferência'] - df_ent['Sistema']
            
            st.table(df_ent.style.format({"Sistema": "{:.2f}", "Conferência": "{:.2f}", "Acerto": "{:.2f}"}))
            
            t_sis_ent = df_ent['Sistema'].sum()
            t_conf_ent = df_ent['Conferência'].sum()
            t_ace_ent = df_ent['Acerto'].sum()

            st.markdown(f"""
                <div style='background-color:#1a1a1a; padding:12px; border-radius:8px; border:1px solid #444; border-left: 5px solid #555;'>
                    <small style='color:#bbb; font-weight:bold; text-transform: uppercase;'>Resumo das Vendas do Sistema:</small><br>
                    <span style='font-size:15px;'>Sistema: R$ {t_sis_ent:,.2f} | <span style='color:#00ff00;'>Conf.: R$ {t_conf_ent:,.2f}</span> | <span style='color:#ff4b4b;'>Diferença: R$ {t_ace_ent:,.2f}</span></span>
                </div>
            """, unsafe_allow_html=True)

            # --- GRUPO 2: SAÍDAS ---
            st.subheader("📤 Saídas (Justificativas)")
            saidas = [
                {"Descrição": "DESPESA", "Conferência": d['conf_despesa']},
                {"Descrição": "VALE FUNC.", "Conferência": d['conf_vale_func']},
                {"Descrição": "DEV. CARTÃO", "Conferência": d['conf_dev_cartao']},
                {"Descrição": "OUTROS", "Conferência": d['conf_outros']}
            ]
            df_sai = pd.DataFrame(saidas)
            st.table(df_sai.style.format({"Conferência": "{:.2f}"}))
            
            t_conf_sai = df_sai['Conferência'].sum()

            # Lógica de Divergência Final (Gaveta + Saídas) - Sistema
            divergencia_final = (t_conf_ent + t_conf_sai) - t_sis_ent
            
            if -0.01 <= divergencia_final <= 0.01:
                cor_div = "#00ff00"; label_div = "Caixa Ajustado (OK)"
            elif divergencia_final < 0:
                cor_div = "#ff4b4b"; label_div = "Divergência: FALTA"
            else:
                cor_div = "#33ccff"; label_div = "Divergência: SOBRA"

            st.markdown(f"""
                <div style='background-color:#1a1a1a; padding:10px; border-radius:5px; border:1px solid #333; margin-bottom:20px;'>
                    <b>TOTAL JUSTIFICADO:</b> <span style='color:#00ff00;'>R$ {t_conf_sai:,.2f}</span>
                </div>
            """, unsafe_allow_html=True)

            # --- CARD FINAL DE IMPACTO ---
            st.markdown(f"""
                <div style="background-color:#141414; padding:25px; border-radius:15px; border-left: 8px solid #00ff00; box-shadow: 2px 2px 10px rgba(0,0,0,0.5);">
                    <p style="margin:0; font-size:18px; color:#00ff00; font-weight:bold; letter-spacing: 1px;">CAIXA TOTAL DO DIA (VALOR CONFERIDO)</p>
                    <h1 style="margin:5px 0; color:white; font-size:52px; font-weight:900;">R$ {t_conf_ent:,.2f}</h1>
                    <hr style="border: 0; border-top: 1px solid #333; margin: 15px 0;">
                    <p style="margin:0; font-size:22px; color:{cor_div}; font-weight:bold; text-transform: uppercase;">
                        Status da Auditoria: {label_div} (R$ {divergencia_final:,.2f})
                    </p>
                </div>
                <br>
            """, unsafe_allow_html=True)

        with col_auditoria:
            st.subheader("🔍 Evidências")
            with st.container(border=True):
                st.markdown("**📝 Observações do Gerente:**")
                st.info(d['observacoes'] if d['observacoes'] else "Nenhuma observação.")
                
                st.markdown("**🖼️ Anexos:**")
                if d.get('urls_prints'):
                    cols_img = st.columns(2)
                    for idx, url in enumerate(d['urls_prints']):
                        with cols_img[idx % 2]:
                            st.image(url, use_container_width=True)
                else:
                    st.warning("Sem comprovantes.")

            st.write("---")
            st.subheader("✍️ Parecer do Financeiro")
            
            if d.get('auditado_por'):
                st.success(f"✅ Auditado por: **{d['auditado_por']}**")
            else:
                st.warning("⚠️ Aguardando Auditoria")

            with st.form("form_auditoria_vFinal"):
                # Novos Checkboxes de conferência específica
                c1, c2, c3 = st.columns(3)
                check_sis = c1.checkbox("Comp. Sistema", value=d.get('check_sistema', False))
                check_dep = c2.checkbox("Comp. Depósito", value=d.get('check_deposito', False))
                check_des = c3.checkbox("Comp. Despesas", value=d.get('check_despesas', False))
                
                novo_feedback = st.text_area("Réplica / Feedback para o Gerente:", value=d.get('replica_gestor', ''))
                confirmar = st.checkbox("Marcar como CONFERIDO / AUDITADO", value=(d.get('status_auditoria') == 'Auditado'))
                
                if st.form_submit_button("💾 SALVAR PARECER E ENVIAR", use_container_width=True):
                    dados_update = {
                        "check_sistema": check_sis,
                        "check_deposito": check_dep,
                        "check_despesas": check_des,
                        "replica_gestor": novo_feedback,
                        "status_auditoria": "Auditado" if confirmar else "Pendente",
                        "auditado_por": user['nome']
                    }
                    
                    sucesso = db.atualizar_auditoria(supabase, d['id'], dados_update)
                    if sucesso:
                        st.success("Auditoria salva com sucesso!")
                        st.rerun()
                    else:
                        st.error("Erro ao conectar com o banco de dados.")
    else:
        st.info("Nenhum lançamento encontrado para os filtros selecionados.")
