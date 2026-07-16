import streamlit as st
import pandas as pd
from datetime import date, timedelta
import database_utils as db
import time

def renderizar_tela(supabase, user):
    st.title("⚖️ Auditoria de Fechamentos")

    # --- 1. SELEÇÃO DA UNIDADE (FILTRO PRINCIPAL) ---
    lojas_res = db.buscar_lojas(supabase)
    mapa_lojas = {l['nome']: l['id'] for l in lojas_res.data} if lojas_res.data else {}
    
    c1, c2, c3 = st.columns([2, 1, 1])
    loja_nome = c1.selectbox("Selecione a Unidade:", options=list(mapa_lojas.keys()))
    loja_id = mapa_lojas[loja_nome]

    # --- 2. BUSCA DATAS COM LANÇAMENTOS (INDICADORES DUPLOS) ---
    data_limite_busca = date.today() - timedelta(days=15)
    
    try:
        # Selecionamos os campos de checks para a lógica do segundo marcador
        res_datas = supabase.table("fechamentos")\
            .select("data_fechamento, status_auditoria, check_sistema, check_deposito, check_despesas")\
            .eq("loja_id", loja_id)\
            .gte("data_fechamento", str(data_limite_busca))\
            .eq("ativo", True)\
            .execute()

        if res_datas.data:
            # Ordenamos os registros por data (mais recente primeiro)
            registros = sorted(res_datas.data, key=lambda x: x['data_fechamento'], reverse=True)

            st.write(f"📅 **Lançamentos detectados em {loja_nome}:**")
            qtd_datas = len(registros)
            # Criamos as colunas (limitando a 10 por linha para não espremer)
            cols_datas = st.columns(qtd_datas if qtd_datas < 10 else 10)
            
            for i, reg in enumerate(registros[:10]):
                with cols_datas[i]:
                    dt_str = reg['data_fechamento']
                    dt_obj = date.fromisoformat(dt_str)
                    label = dt_obj.strftime("%d/%m")
                    
                    # Lógica 1: Status Geral da Auditoria
                    emoji_auditoria = "✅" if reg['status_auditoria'] == "Auditado" else "🟡"
                    
                    # Lógica 2: Combinação lógica E (AND) dos Comprovantes
                    # Só fica verde se os TRÊS estiverem marcados como True
                    comp_ok = reg.get('check_sistema', False) and \
                              reg.get('check_deposito', False) and \
                              reg.get('check_despesas', False)
                    emoji_comprovantes = "✅" if comp_ok else "🟡"
                    
                    # Texto do Botão com 2 Indicadores
                    if st.button(f"{emoji_auditoria}{emoji_comprovantes}\n{label}", key=f"btn_dt_{dt_str}"):
                        st.session_state.auditoria_date_manual = dt_obj
                        st.rerun()
        else:
            st.caption(f"ℹ️ Nenhuma pendência recente encontrada para {loja_nome}.")
    except Exception as e:
        st.error(f"Erro ao carregar cronograma: {e}")

    st.write("---")

    # --- 3. SELEÇÃO DE DATA ---
    data_padrao = st.session_state.get('auditoria_date_manual', date.today())
    
    data_sel = c2.date_input(
        "Data do Movimento:", 
        value=data_padrao,
        format="DD/MM/YYYY"
    )
    
    # Busca o fechamento específico
    res = db.buscar_fechamento_multiplas_lojas(supabase, [loja_id], str(data_sel), str(data_sel))

    if res and res.data:
        d = res.data[0]
        col_dados, col_auditoria = st.columns([2.2, 2])
        
        with col_dados:
            st.subheader("📋 Conferência de Valores")
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

            divergencia_final = (t_conf_ent + t_conf_sai) - t_sis_ent
            cor_div = "#00ff00" if -0.01 <= divergencia_final <= 0.01 else ("#ff4b4b" if divergencia_final < 0 else "#33ccff")
            label_div = "Caixa Ajustado (OK)" if -0.01 <= divergencia_final <= 0.01 else ("FALTA" if divergencia_final < 0 else "SOBRA")

            st.markdown(f"""
                <div style='background-color:#1a1a1a; padding:10px; border-radius:5px; border:1px solid #333; margin-bottom:20px;'>
                    <b>TOTAL JUSTIFICADO:</b> <span style='color:#00ff00;'>R$ {t_conf_sai:,.2f}</span>
                </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
                <div style="background-color:#141414; padding:25px; border-radius:15px; border-left: 8px solid #00ff00; box-shadow: 2px 2px 10px rgba(0,0,0,0.5);">
                    <p style="margin:0; font-size:18px; color:#00ff00; font-weight:bold; letter-spacing: 1px;">CAIXA TOTAL DO DIA (VALOR CONFERIDO)</p>
                    <h1 style="margin:5px 0; color:white; font-size:52px; font-weight:900;">R$ {t_conf_ent:,.2f}</h1>
                    <hr style="border: 0; border-top: 1px solid #333; margin: 15px 0;">
                    <p style="margin:0; font-size:22px; color:{cor_div}; font-weight:bold; text-transform: uppercase;">
                        Status da Auditoria: {label_div} (R$ {divergencia_final:,.2f})
                    </p>
                </div>
            """, unsafe_allow_html=True)

        with col_auditoria:
            st.subheader("🔍 Evidências")
            with st.container(border=True):
                st.markdown("**📝 Observações do Gerente:**")
                st.info(d['observacoes'] if d['observacoes'] else "Nenhuma observação.")
                
                st.markdown("**🖼️ Anexos Atuais:**")
                urls_atuais = d.get('urls_prints', [])
                if urls_atuais:
                    for idx, url in enumerate(urls_atuais):
                        # Linha com imagem/botão e coluna de remoção
                        col_anexo, col_excluir = st.columns([5, 1])
                        
                        with col_anexo:
                            # Thumbnail ou link direto para expandir
                            st.image(url, use_container_width=True)
                            
                        with col_excluir:
                            st.write("<br>" * 2, unsafe_allow_html=True) # Alinha o botão verticalmente com o topo da imagem
                            
                            # Botão de exclusão com confirmação em tempo de execução
                            if st.button("🗑️", key=f"btn_excluir_{idx}", help="Excluir este comprovante permanentemente"):
                                # Grava no session_state para solicitar confirmação
                                st.session_state.confirmar_exclusao_idx = idx
                        
                        # Bloco de confirmação de segurança logo abaixo da imagem em foco
                        if st.session_state.get('confirmar_exclusao_idx') == idx:
                            st.warning("⚠️ **A exclusão deste comprovante é irreversível!**")
                            col_conf_sim, col_conf_nao = st.columns(2)
                            
                            if col_conf_sim.button("Sim, Excluir", key=f"conf_sim_{idx}", type="primary", use_container_width=True):
                                with st.spinner("Excluindo arquivo do servidor..."):
                                    try:
                                        # 1. Extrai o caminho relativo do arquivo no bucket
                                        if "comprovantes/" in url:
                                            caminho_relativo = url.split("comprovantes/")[-1]
                                            # Remove o arquivo do Storage
                                            supabase.storage.from_("comprovantes").remove([caminho_relativo])
                                        
                                        # 2. Atualiza a lista filtrando fora o arquivo deletado
                                        nova_lista = [u for u in urls_atuais if u != url]
                                        
                                        # 3. Atualiza o registro no banco
                                        supabase.table("fechamentos")\
                                            .update({"urls_prints": nova_lista})\
                                            .eq("id", d['id'])\
                                            .execute()
                                            
                                        st.success("Anexo removido com sucesso!")
                                        del st.session_state.confirmar_exclusao_idx
                                        time.sleep(1)
                                        st.rerun()
                                    except Exception as err:
                                        st.error(f"Erro ao remover: {err}")
                                        
                            if col_conf_nao.button("Cancelar", key=f"conf_nao_{idx}", use_container_width=True):
                                del st.session_state.confirmar_exclusao_idx
                                st.rerun()
                        st.write("---")
                else: 
                    st.warning("Sem comprovantes.")

                st.markdown("---")
                with st.expander("➕ Adicionar Comprovantes Esquecidos"):
                    novos_arquivos = st.file_uploader("Selecione os arquivos extras:", accept_multiple_files=True, key="anexos_extras")
                    if st.button("Subir e Salvar Anexos", use_container_width=True):
                        if novos_arquivos:
                            with st.spinner('Fazendo upload...'):
                                if urls_atuais is None: urls_atuais = []
                                
                                novas_urls = []
                                for i, f in enumerate(novos_arquivos):
                                    ts = int(time.time())
                                    path = f"loja_{loja_id}/{data_sel}/extra_{ts}_{i}_{f.name}"
                                    db.fazer_upload_print(supabase, f, path)
                                    url_publica = supabase.storage.from_("comprovantes").get_public_url(path)
                                    novas_urls.append(url_publica)
                                
                                lista_final = list(urls_atuais) + novas_urls
                                if db.atualizar_auditoria(supabase, d['id'], {"urls_prints": lista_final}):
                                    st.success("Anexos adicionados!")
                                    time.sleep(1)
                                    st.rerun()
                        else:
                            st.warning("Selecione algum arquivo primeiro.")

            st.write("---")
            st.subheader("✍️ Parecer do Financeiro")
            if d.get('auditado_por'): st.success(f"✅ Auditado por: **{d['auditado_por']}**")
            else: st.warning("⚠️ Aguardando Auditoria")

            with st.form("form_auditoria_vFinal"):
                cx1, cx2, cx3 = st.columns(3)
                check_sis = cx1.checkbox("Comp. Sistema", value=d.get('check_sistema', False))
                check_dep = cx2.checkbox("Comp. Depósito", value=d.get('check_deposito', False))
                check_des = cx3.checkbox("Comp. Despesas", value=d.get('check_despesas', False))
                
                novo_feedback = st.text_area("Réplica / Feedback para o Gerente:", value=d.get('replica_gestor', ''))
                confirmar = st.checkbox("Marcar como CONFERIDO / AUDITADO", value=(d.get('status_auditoria') == 'Auditado'))
                
                if st.form_submit_button("💾 SALVAR PARECER E ENVIAR", use_container_width=True):
                    dados_update = {
                        "check_sistema": check_sis, "check_deposito": check_dep, "check_despesas": check_des,
                        "replica_gestor": novo_feedback, "status_auditoria": "Auditado" if confirmar else "Pendente",
                        "auditado_por": user['nome']
                    }
                    if db.atualizar_auditoria(supabase, d['id'], dados_update):
                        st.success("Auditoria salva!"); time.sleep(1); st.rerun()

        st.write("---")
        st.subheader("🛠️ Gestão de Erros")
        with st.expander("⚠️ Inativar este lançamento"):
            motivo_inativacao = st.text_input("Motivo da Inativação:")
            if st.button("🚫 CONFIRMAR INATIVAÇÃO"):
                dados_anular = {"ativo": False, "replica_gestor": f"INVALIDADO: {motivo_inativacao}", "auditado_por": user['nome'], "status_auditoria": "Inativado"}
                if supabase.table("fechamentos").update(dados_anular).eq("id", d['id']).execute():
                    st.success("Inativado!"); time.sleep(2); st.rerun()
    else:
        st.info(f"Nenhum lançamento encontrado para {loja_nome} em {data_sel.strftime('%d/%m/%Y')}.")
