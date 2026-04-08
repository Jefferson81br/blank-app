import streamlit as st
import pandas as pd
from datetime import date, timedelta
import database_utils as db

def renderizar_tela(supabase, user):
    st.title("📊 Painel de Performance")
    
    lojas_res = db.buscar_lojas(supabase)
    mapa_lojas = {l['nome']: l['id'] for l in lojas_res.data} if lojas_res.data else {}
    
    if user['funcao'] in ['admin', 'proprietario']:
        lojas_sel_nomes = st.multiselect("Unidades:", options=list(mapa_lojas.keys()), default=list(mapa_lojas.keys())[:1])
        lista_ids = [mapa_lojas[n] for n in lojas_sel_nomes]
    else:
        if not user['unidade_id']: st.stop()
        lista_ids = [user['unidade_id']]

    if not lista_ids: st.stop()

    c1, c2 = st.columns([2, 1])
    periodo = c2.selectbox("Período:", ["Dia", "Semana", "Mês"])
    hoje = date.today()
    if periodo == "Dia": 
        d_ini = c1.date_input("Data:", hoje, max_value=hoje)
        d_fim = d_ini
    elif periodo == "Semana": 
        d_ini = hoje - timedelta(days=hoje.weekday())
        d_fim = hoje
    else: 
        d_ini = hoje.replace(day=1)
        d_fim = hoje

    res = db.buscar_fechamento_multiplas_lojas(supabase, lista_ids, str(d_ini), str(d_fim))
    
    if res and res.data:
        df_geral = pd.DataFrame(res.data)
        id_para_nome = {v: k for k, v in mapa_lojas.items()}
        
        # --- CONFIGURAÇÃO DA MATRIZ ---
        # 2 colunas por linha é o ideal para leitura. Se quiser 3, altere o número abaixo.
        num_colunas_matriz = 2
        for i in range(0, len(lista_ids), num_colunas_matriz):
            cols = st.columns(num_colunas_matriz)
            for j in range(num_colunas_matriz):
                if i + j < len(lista_ids):
                    l_id = lista_ids[i + j]
                    with cols[j]:
                        st.markdown(f"### 🏢 {id_para_nome.get(l_id, 'Unidade')}")
                        df_l = df_geral[df_geral['loja_id'] == l_id]
                        
                        if not df_l.empty:
                            # Colunas para cálculo de Totais
                            colunas_sis = ['sis_cartao', 'sis_crediario', 'sis_dinheiro', 'sis_ifood', 'sis_pbm', 'sis_pix', 'sis_vale_compra', 'sis_fapp', 'sis_vlink']
                            colunas_conf = ['conf_cartao', 'conf_crediario', 'conf_dinheiro', 'conf_ifood', 'conf_pbm', 'conf_pix', 'conf_vale_compra', 'conf_fapp', 'conf_vlink']
                            colunas_saidas = ['conf_despesa', 'conf_vale_func', 'conf_dev_cartao', 'conf_outros']

                            t_sistema = df_l[colunas_sis].sum().sum()
                            t_conf_entradas = df_l[colunas_conf].sum().sum()
                            t_saidas = df_l[colunas_saidas].sum().sum()
                            t_acerto = (t_conf_entradas - t_sistema) - t_saidas

                            # Métricas de topo da loja
                            m1, m2, m3 = st.columns(3)
                            m1.metric("Venda (Sis)", f"{t_sistema:,.2f}")
                            m2.metric("Saídas", f"{t_saidas:,.2f}")
                            m3.metric("Acerto", f"{t_acerto:,.2f}")

                            if periodo == "Dia":
                                d = df_l.iloc[0]
                                # LISTA COMPLETA DE TODOS OS ITENS DE LANÇAMENTO
                                dados_completos = [
                                    {"DESC": "CARTÃO", "S": d['sis_cartao'], "C": d['conf_cartao']},
                                    {"DESC": "CREDIÁRIO", "S": d['sis_crediario'], "C": d['conf_crediario']},
                                    {"DESC": "DINHEIRO", "S": d['sis_dinheiro'], "C": d['conf_dinheiro']},
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
                                
                                df_tab = pd.DataFrame(dados_completos)
                                # Lógica de acerto: entradas (C-S), saídas (-C)
                                df_tab['A'] = df_tab.apply(
                                    lambda x: x['C'] - x['S'] if x['DESC'] not in ["DESPESA", "VALE FUNC.", "DEV. CARTÃO", "OUTROS"] 
                                    else -x['C'], axis=1
                                )
                                
                                # Exibição da tabela completa com rolagem se necessário
                                st.dataframe(
                                    df_tab.style.format({"S": "{:.2f}", "C": "{:.2f}", "A": "{:.2f}"}),
                                    use_container_width=True,
                                    hide_index=True
                                )
                                
                                if d['urls_prints']:
                                    with st.expander("🖼️ Ver Comprovantes"):
                                        st.image(d['urls_prints'], use_column_width=True)
                            
                            st.markdown("---")
                        else:
                            st.info(f"Sem dados para {id_para_nome.get(l_id)}")
    else:
        st.info("Nenhum lançamento encontrado para os filtros selecionados.")
