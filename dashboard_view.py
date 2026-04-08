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
    periodo = c1.selectbox("Período:", ["Dia", "Semana", "Mês"])
    hoje = date.today()
    if periodo == "Dia": d_ini = c2.date_input("Data:", hoje, max_value=hoje); d_fim = d_ini
    elif periodo == "Semana": d_ini = hoje - timedelta(days=hoje.weekday()); d_fim = hoje
    else: d_ini = hoje.replace(day=1); d_fim = hoje

    res = db.buscar_fechamento_multiplas_lojas(supabase, lista_ids, str(d_ini), str(d_fim))
    
    if res and res.data:
        df_geral = pd.DataFrame(res.data)
        id_para_nome = {v: k for k, v in mapa_lojas.items()}
        cols_dash = st.columns(len(lista_ids))
        
        for idx, l_id in enumerate(lista_ids):
            with cols_dash[idx]:
                st.subheader(f"🏢 {id_para_nome.get(l_id)}")
                df_l = df_geral[df_geral['loja_id'] == l_id]
                if not df_l.empty:
                    t_s = df_l[['sis_cartao', 'sis_crediario', 'sis_dinheiro', 'sis_ifood', 'sis_pix']].values.sum()
                    t_c = df_l[['conf_cartao', 'conf_crediario', 'conf_dinheiro', 'conf_ifood', 'conf_pix', 'despesa']].values.sum()
                    t_d = df_l['despesa'].sum()
                    t_a = t_c - t_s - (t_d * 2)
                    st.metric("Venda (Sis)", f"R$ {t_s:,.2f}")
                    st.metric("Acerto", f"R$ {t_a:,.2f}", delta=f"{t_a:,.2f}")
                    if periodo == "Dia":
                        d = df_l.iloc[0]
                        df_tab = pd.DataFrame([
                            {"ITEM": "CARTÃO", "SIS": d['sis_cartao'], "CONF": d['conf_cartao']},
                            {"ITEM": "CREDIÁRIO", "SIS": d['sis_crediario'], "CONF": d['conf_crediario']},
                            {"ITEM": "DINHEIRO", "SIS": d['sis_dinheiro'], "CONF": d['conf_dinheiro']},
                            {"ITEM": "IFOOD", "SIS": d['sis_ifood'], "CONF": d['conf_ifood']},
                            {"ITEM": "PIX/TRANSF", "SIS": d['sis_pix'], "CONF": d['conf_pix']},
                            {"ITEM": "DESPESA", "SIS": 0.0, "CONF": d['despesa']}
                        ])
                        st.table(df_tab.style.format({"SIS": "R$ {:.2f}", "CONF": "R$ {:.2f}", "ACERTO": "R$ {:.2f}"}))
                        if d['urls_prints']:
                            for url_p in d['urls_prints']:
                                st.markdown(f'<a href="{url_p}" target="_blank"><img src="{url_p}" width="150" height="150" style="object-fit: cover; border-radius: 5px; margin-bottom:5px;"></a>', unsafe_allow_html=True)
                else: st.caption("Sem dados.")
    else: st.info("Nenhum lançamento encontrado.")
