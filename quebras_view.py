import streamlit as st
import pandas as pd
from datetime import date, timedelta
import calendar
import database_utils as db
import plotly.express as px

def renderizar_tela(supabase, user):
    st.title("📉 Quebras de Caixa")

    # --- 1. SELEÇÃO DE LOJA ---
    lojas_res = db.buscar_lojas(supabase)
    mapa_lojas = {l['nome']: l['id'] for l in lojas_res.data} if lojas_res.data else {}
    id_para_nome = {v: k for k, v in mapa_lojas.items()}

    if user['funcao'] not in ['admin', 'proprietario', 'financeiro']:
        loja_id_selecionada = user.get('unidade_id')
        lista_ids_busca = [loja_id_selecionada]
        st.info(f"Exibindo dados de: **{id_para_nome.get(loja_id_selecionada, 'Minha Unidade')}**")
    else:
        with st.container(border=True):
            loja_nome_sel = st.multiselect(
                "Selecione as Unidades:", 
                options=list(mapa_lojas.keys()),
                default=list(mapa_lojas.keys())[0] if mapa_lojas else None
            )
            lista_ids_busca = [mapa_lojas[n] for n in loja_nome_sel]

    # --- 2. CONFIGURAÇÃO DO PERÍODO ---
    tipo_filtro = st.radio("Tipo de Visualização:", ["Mensal", "Período Específico"], horizontal=True)

    if tipo_filtro == "Mensal":
        c1, c2 = st.columns(2)
        mes_sel = c1.selectbox("Mês:", list(range(1, 13)), index=date.today().month - 1)
        ano_sel = c2.selectbox("Ano:", [2025, 2026], index=1)
        ultimo_dia = calendar.monthrange(ano_sel, mes_sel)[1]
        dt_ini = date(ano_sel, mes_sel, 1)
        dt_fim = date(ano_sel, mes_sel, ultimo_dia)
    else:
        c1, c2 = st.columns(2)
        dt_ini = c1.date_input("Início:", value=date.today() - timedelta(days=30), format="DD/MM/YYYY")
        dt_fim = c2.date_input("Fim:", value=date.today(), format="DD/MM/YYYY")

    # --- 3. BUSCA E PROCESSAMENTO (LÓGICA CORRIGIDA) ---
    res = db.buscar_fechamento_multiplas_lojas(supabase, lista_ids_busca, str(dt_ini), str(dt_fim))

    if res and res.data:
        df_bruto = pd.DataFrame(res.data)
        df_bruto['data_dt'] = pd.to_datetime(df_bruto['data_fechamento']).dt.date
        
        # 1. Agrupar por dia (consolida várias lojas se houver)
        df_consolidado = df_bruto.groupby('data_dt')['valor_quebra'].sum().reset_index()

        # 2. CRIAR CALENDÁRIO COMPLETO (Para evitar saltos no gráfico)
        datas_cheias = pd.date_range(start=dt_ini, end=dt_fim).date
        df_timeline = pd.DataFrame({'data_dt': datas_cheias})

        # 3. MERGE (Une o calendário com os dados reais)
        df_final = pd.merge(df_timeline, df_consolidado, on='data_dt', how='left').fillna(0)
        
        # 4. ORDENAÇÃO E ACUMULADO REAL
        df_final = df_final.sort_values('data_dt')
        df_final['acumulado'] = df_final['valor_quebra'].cumsum()
        
        # Formatação para o Gráfico
        df_final['Data Formatada'] = pd.to_datetime(df_final['data_dt']).dt.strftime('%d/%m/%Y')
        df_final['Cor'] = df_final['valor_quebra'].apply(lambda x: 'Sobra' if x >= 0 else 'Falta')

        # --- 4. MÉTRICAS ---
        saldo_total = df_final['valor_quebra'].sum()
        st.metric("Saldo Acumulado Final", f"R$ {saldo_total:,.2f}", delta=f"{saldo_total:,.2f}", delta_color="inverse" if saldo_total < 0 else "normal")

        # --- 5. GRÁFICO DIÁRIO (BARRAS) ---
        st.subheader("📊 Quebras Diárias")
        fig_bar = px.bar(
            df_final, x='Data Formatada', y='valor_quebra',
            color='Cor', color_discrete_map={'Sobra': '#00ff00', 'Falta': '#ff4b4b'},
            text_auto='.2f', labels={'valor_quebra': 'R$', 'Data Formatada': 'Dia'}
        )
        st.plotly_chart(fig_bar, use_container_width=True)

        # --- 6. GRÁFICO ACUMULADO (LINHA) ---
        st.subheader("📉 Evolução do Saldo")
        fig_line = px.line(
            df_final, x='Data Formatada', y='acumulado',
            markers=True, labels={'acumulado': 'Saldo (R$)'},
            render_mode="svg" # Melhora a precisão visual
        )
        fig_line.add_hline(y=0, line_dash="dash", line_color="white")
        st.plotly_chart(fig_line, use_container_width=True)

        # --- 7. COMPARATIVO ADM ---
        if user['funcao'] in ['admin', 'proprietario', 'financeiro']:
            st.write("---")
            df_bruto['Loja'] = df_bruto['loja_id'].map(id_para_nome)
            ranking = df_bruto.groupby('Loja')['valor_quebra'].sum().reset_index().sort_values('valor_quebra')
            st.subheader("🏢 Ranking de Quebra por Unidade")
            st.plotly_chart(px.bar(ranking, x='Loja', y='valor_quebra', text_auto='.2f', color='valor_quebra', color_continuous_scale='RdYlGn'), use_container_width=True)
    else:
        st.info("Nenhum dado encontrado para o período.")
