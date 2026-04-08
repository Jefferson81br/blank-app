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

    c1, c2 = st.columns(2)
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
        
        # Filtro de abas por loja para não poluir a tela se houver muitas
        abas = st.tabs([id_para_nome.get(l_id, "Loja") for l_id in lista_ids])
        
        for idx, l_id in enumerate(lista_ids):
            with abas[idx]:
                df_l = df_geral[df_geral['loja_id'] == l_id]
                if not df_l.empty:
                    # Cálculo de Totais (Entradas)
                    colunas_sis = ['sis_cartao', 'sis_crediario', 'sis_dinheiro', 'sis_ifood', 'sis_pbm', 'sis_pix', 'sis_vale_compra', 'sis_fapp', 'sis_vlink']
                    colunas_conf = ['conf_cartao', 'conf_crediario', 'conf_dinheiro', 'conf_ifood', 'conf_pbm', 'conf_pix', 'conf_vale_compra', 'conf_fapp', 'conf_vlink']
                    colunas_saidas = ['conf_despesa', 'conf_vale_func', 'conf_dev_cartao', 'conf_outros']

                    t_sistema = df_l[colunas_sis].sum().sum()
                    t_conf_entradas = df_l[colunas_conf].sum().sum()
                    t_saidas = df_l[colunas_saidas].sum().sum()
                    
                    # Acerto Final = (Conf Entradas - Sis Entradas) - Saídas
                    # Ou simplesmente a soma dos acertos de cada linha
                    t_acerto = (t_conf_entradas - t_sistema) - t_saidas

                    m1, m2, m3 = st.columns(3)
                    m1.metric("Venda (Sistema)", f"R$ {t_sistema:,.2f}")
                    m2.metric("Total Saídas", f"R$ {t_saidas:,.2f}")
                    m3.metric("Acerto Líquido", f"R$ {t_acerto:,.2f}", delta=f"{t_acerto:,.2f}")

                    if periodo == "Dia":
                        d = df_l.iloc[0]
                        
                        st.markdown("### Detalhamento do Dia")
                        dados_tab = [
                            {"DESCRIÇÃO": "CARTÃO", "SISTEMA": d['sis_cartao'], "CONFERÊNCIA": d['conf_cartao']},
                            {"DESCRIÇÃO": "CREDIÁRIO", "SISTEMA": d['sis_crediario'], "CONFERÊNCIA": d['conf_crediario']},
                            {"DESCRIÇÃO": "DINHEIRO", "SISTEMA": d['sis_dinheiro'], "CONFERÊNCIA": d['conf_dinheiro']},
                            {"DESCRIÇÃO": "IFOOD", "SISTEMA": d['sis_ifood'], "CONFERÊNCIA": d['conf_ifood']},
                            {"DESCRIÇÃO": "PBM", "SISTEMA": d['sis_pbm'], "CONFERÊNCIA": d['conf_pbm']},
                            {"DESCRIÇÃO": "PIX", "SISTEMA": d['sis_pix'], "CONFERÊNCIA": d['conf_pix']},
                            {"DESCRIÇÃO": "VALE COMPRA", "SISTEMA": d['sis_vale_compra'], "CONFERÊNCIA": d['conf_vale_compra']},
                            {"DESCRIÇÃO": "FARMÁCIAS APP", "SISTEMA": d['sis_fapp'], "CONFERÊNCIA": d['conf_fapp']},
                            {"DESCRIÇÃO": "VIDA LINK", "SISTEMA": d['sis_vlink'], "CONFERÊNCIA": d['conf_vlink']},
                            {"DESCRIÇÃO": "DESPESA", "SISTEMA": 0.0, "CONFERÊNCIA": d['conf_despesa']},
                            {"DESCRIÇÃO": "VALE FUNC.", "SISTEMA": 0.0, "CONFERÊNCIA": d['conf_vale_func']},
                            {"DESCRIÇÃO": "DEV. CARTÃO", "SISTEMA": 0.0, "CONFERÊNCIA": d['conf_dev_cartao']},
                            {"DESCRIÇÃO": "OUTROS", "SISTEMA": 0.0, "CONFERÊNCIA": d['conf_outros']},
                        ]
                        
                        df_resumo = pd.DataFrame(dados_tab)
                        # Cálculo do acerto por linha para a tabela
                        df_resumo['ACERTO'] = df_resumo.apply(
                            lambda x: x['CONFERÊNCIA'] - x['SISTEMA'] if x['DESCRIÇÃO'] not in ['DESPESA', 'VALE FUNC.', 'DEV. CARTÃO', 'OUTROS'] 
                            else -x['CONFERÊNCIA'], axis=1
                        )
                        
                        st.table(df_resumo.style.format({"SISTEMA": "R$ {:.2f}", "CONFERÊNCIA": "R$ {:.2f}", "ACERTO": "R$ {:.2f}"}))
                        
                        if d['urls_prints']:
                            st.write("**Comprovantes anexados:**")
                            cols_img = st.columns(4)
                            for i, url_p in enumerate(d['urls_prints']):
                                with cols_img[i % 4]:
                                    st.markdown(f'''<a href="{url_p}" target="_blank">
                                        <img src="{url_p}" width="100%" style="border-radius:5px; border:1px solid #333;">
                                        </a>''', unsafe_allow_html=True)
                    else:
                        st.info("Selecione visualização por 'Dia' para ver a tabela detalhada e fotos.")
                else:
                    st.warning("Sem dados para esta unidade no período.")
    else:
        st.info("Nenhum lançamento encontrado para os filtros selecionados.")
