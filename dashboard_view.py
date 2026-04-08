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
        
        # --- LÓGICA DE MATRIZ (LADO A LADO) ---
        # Definimos 2 colunas por linha para não espremer os dados
        num_colunas = 2
        for i in range(0, len(lista_ids), num_colunas):
            cols = st.columns(num_colunas)
            for j in range(num_colunas):
                if i + j < len(lista_ids):
                    l_id = lista_ids[i + j]
                    with cols[j]:
                        st.markdown(f"### 🏢 {id_para_nome.get(l_id, 'Unidade')}")
                        df_l = df_geral[df_geral['loja_id'] == l_id]
                        
                        if not df_l.empty:
                            # Agrupamento de colunas para cálculo
                            colunas_sis = ['sis_cartao', 'sis_crediario', 'sis_dinheiro', 'sis_ifood', 'sis_pbm', 'sis_pix', 'sis_vale_compra', 'sis_fapp', 'sis_vlink']
                            colunas_conf = ['conf_cartao', 'conf_crediario', 'conf_dinheiro', 'conf_ifood', 'conf_pbm', 'conf_pix', 'conf_vale_compra', 'conf_fapp', 'conf_vlink']
                            colunas_saidas = ['conf_despesa', 'conf_vale_func', 'conf_dev_cartao', 'conf_outros']

                            t_sistema = df_l[colunas_sis].sum().sum()
                            t_conf_entradas = df_l[colunas_conf].sum().sum()
                            t_saidas = df_l[colunas_saidas].sum().sum()
                            t_acerto = (t_conf_entradas - t_sistema) - t_saidas

                            # Métricas Compactas para caber lado a lado
                            m1, m2, m3 = st.columns(3)
                            m1.metric("Venda", f"{t_sistema:,.2f}")
                            m2.metric("Saídas", f"{t_saidas:,.2f}")
                            
                            cor_delta = "normal" if t_acerto >= 0 else "inverse"
                            m3.metric("Acerto", f"{t_acerto:,.2f}")

                            if periodo == "Dia":
                                d = df_l.iloc[0]
                                dados_tab = [
                                    {"DESC": "CARTÃO", "S": d['sis_cartao'], "C": d['conf_cartao']},
                                    {"DESC": "DINHEIRO", "S": d['sis_dinheiro'], "C": d['conf_dinheiro']},
                                    {"DESC": "PIX", "S": d['sis_pix'], "C": d['conf_pix']},
                                    {"DESC": "SAÍDAS", "S": 0.0, "C": t_saidas}
                                ]
                                df_resumo = pd.DataFrame(dados_tab)
                                df_resumo['A'] = df_resumo.apply(lambda x: x['C'] - x['S'] if x['DESC'] != 'SAÍDAS' else -x['C'], axis=1)
                                
                                # Tabela reduzida para caber lado a lado
                                st.dataframe(df_resumo.style.format({"S": "{:.2f}", "C": "{:.2f}", "A": "{:.2f}"}), use_container_width=True, hide_index=True)
                                
                                if d['urls_prints']:
                                    with st.expander("Ver Comprovantes"):
                                        st.image(d['urls_prints'], width=100)
                            
                            st.markdown("---")
                        else:
                            st.info(f"Sem dados para {id_para_nome.get(l_id)}")
    else:
        st.info("Nenhum lançamento encontrado para os filtros selecionados.")
