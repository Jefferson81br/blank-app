import streamlit as st
import pandas as pd
from datetime import date
import database_utils as db

def renderizar_tela(supabase, user):
    st.title("📊 Resumo Fechamento de Caixa")
    
    lojas_res = db.buscar_lojas(supabase)
    mapa_lojas = {l['nome']: l['id'] for l in lojas_res.data} if lojas_res.data else {}
    
    # Seleção de Unidades e Data
    col_filtros_1, col_filtros_2 = st.columns([2, 1])
    
    if user['funcao'] in ['admin', 'proprietario']:
        lojas_sel_nomes = col_filtros_1.multiselect("Unidades:", options=list(mapa_lojas.keys()), default=list(mapa_lojas.keys())[:1])
        lista_ids = [mapa_lojas[n] for n in lojas_sel_nomes]
    else:
        if not user['unidade_id']: st.stop()
        lista_ids = [user['unidade_id']]
        col_filtros_1.info(f"Unidade: {user['unidade_id']}")

    data_sel = col_filtros_2.date_input("Data do Movimento:", value=date.today(), max_value=date.today())

    if not lista_ids: st.stop()

    # Busca os dados no banco para o dia selecionado
    res = db.buscar_fechamento_multiplas_lojas(supabase, lista_ids, str(data_sel), str(data_sel))
    
    if res and res.data:
        df_geral = pd.DataFrame(res.data)
        id_para_nome = {v: k for k, v in mapa_lojas.items()}
        
        # --- LOOP DE LOJAS SELECIONADAS ---
        for l_id in lista_ids:
            df_l = df_geral[df_geral['loja_id'] == l_id]
            nome_loja = id_para_nome.get(l_id, "Unidade")
            
            st.markdown(f"## 🏢 {nome_loja}")
            
            if not df_l.empty:
                d = df_l.iloc[0]
                
                # Layout de Matriz similar ao lançamento [Margem, Dados, Info Direita]
                # Ajustado para [0.1, 2, 2] como no lançamento
                m_esq, col_dados, col_info = st.columns([0.1, 2, 2])
                
                with col_dados:
                    st.subheader("📋 Valores Lançados")
                    
                    # Tabela com todos os campos (incluindo o novo campo BOLETO)
                    dados_tabela = [
                        {"DESC": "CARTÃO", "S": d['sis_cartao'], "C": d['conf_cartao']},
                        {"DESC": "CREDIÁRIO", "S": d['sis_crediario'], "C": d['conf_crediario']},
                        {"DESC": "DINHEIRO", "S": d['sis_dinheiro'], "C": d['conf_dinheiro']},
                        {"DESC": "BOLETO", "S": d['sis_boleto'], "C": d['conf_boleto']},
                        {"DESC": "IFOOD", "S": d['sis_ifood'], "C": d['conf_ifood']},
                        {"DESC": "PBM", "S": d['sis_pbm'], "C": d['conf_pbm']},
                        {"DESC": "PIX / TRANSF", "S": d['sis_pix'], "C": d['conf_pix']},
                        {"DESC": "VALE COMPRA", "S": d['sis_vale_compra'], "C": d['conf_vale_compra']},
                        {"DESC": "FARMÁCIAS APP", "S": d['sis_fapp'], "C": d['conf_fapp']},
                        {"DESC": "VIDA LINK", "S": d['sis_vlink'], "C": d['conf_vlink']},
                        {"DESC": "DESPESA", "S": 0.0, "C": d['conf_despesa']},
                        {"DESC": "VALE FUNC.", "S": 0.0, "C": d['conf_vale_func']},
                        {"DESC": "DEV. CARTÃO", "S": 0.0, "C": d['conf_dev_cartao']},
                        {"DESC": "OUTROS", "S": 0.0, "C": d['conf_outros']}
                    ]
                    
                    df_viz = pd.DataFrame(dados_tabela)
                    # Cálculo do acerto por linha
                    df_viz['A'] = df_viz.apply(
                        lambda x: x['C'] - x['S'] if x['DESC'] not in ["DESPESA", "VALE FUNC.", "DEV. CARTÃO", "OUTROS"] 
                        else -x['C'], axis=1
                    )
                    
                    st.dataframe(
                        df_viz.style.format({"S": "{:.2f}", "C": "{:.2f}", "A": "{:.2f}"}),
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    # Totais rápidos em baixo da tabela
                    t_sai = d['conf_despesa'] + d['conf_vale_func'] + d['conf_dev_cartao'] + d['conf_outros']
                    t_conf_ent = df_viz.iloc[:10]['C'].sum()
                    saldo = t_conf_ent - t_sai
                    
                    st.success(f"**Saldo Final Caixa: R$ {saldo:,.2f}**")

                with col_info:
                    # 1. Observação e Feedback no topo direito
                    st.subheader("💬 Comunicação")
                    with st.container(border=True):
                        st.markdown("**📝 Obs. do Gerente:**")
                        st.write(d['observacoes'] if d['observacoes'] else "*Sem observações.*")
                        
                        st.divider()
                        
                        st.markdown("**⚖️ Feedback Financeiro (Réplica):**")
                        st.write(d['replica_gestor'] if d['replica_gestor'] else "*Aguardando auditoria.*")

                    # 2. Miniaturas dos Anexos
                    st.subheader("🖼️ Comprovantes")
                    if d['urls_prints']:
                        # Exibe as imagens em uma grade de miniaturas
                        cols_img = st.columns(3)
                        for idx, url in enumerate(d['urls_prints']):
                            with cols_img[idx % 3]:
                                st.image(url, use_container_width=True)
                    else:
                        st.info("Nenhum anexo enviado.")
                
                st.markdown("---")
            else:
                st.warning(f"Sem fechamento realizado para {nome_loja} nesta data.")
    else:
        st.info("Selecione as unidades e a data para visualizar os fechamentos.")
