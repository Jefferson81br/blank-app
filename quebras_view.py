import streamlit as st
import pandas as pd
from datetime import date, timedelta
import calendar
import database_utils as db
import plotly.express as px  # Importação necessária para cores dinâmicas

def renderizar_tela(supabase, user):
    st.title("📉 Quebras de Caixa")

    # --- 1. DEFINIÇÃO DE PERMISSÕES E SELEÇÃO DE LOJA ---
    lojas_res = db.buscar_lojas(supabase)
    mapa_lojas = {l['nome']: l['id'] for l in lojas_res.data} if lojas_res.data else {}
    id_para_nome = {v: k for k, v in mapa_lojas.items()}

    if user['funcao'] not in ['admin', 'proprietario', 'financeiro']:
        loja_id_selecionada = user.get('unidade_id')
        nome_loja_selecionada = id_para_nome.get(loja_id_selecionada, "Minha Unidade")
        st.info(f"Exibindo dados de: **{nome_loja_selecionada}**")
        lista_ids_busca = [loja_id_selecionada]
    else:
        with st.container(border=True):
            loja_nome_sel = st.multiselect(
                "Selecione as Unidades para análise:", 
                options=list(mapa_lojas.keys()),
                default=list(mapa_lojas.keys())[0] if mapa_lojas else None
            )
            lista_ids_busca = [mapa_lojas[n] for n in loja_nome_sel]

    # --- 2. CONFIGURAÇÃO DO PERÍODO ---
    st.write("---")
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

    # --- 3. BUSCA E PROCESSAMENTO DE DADOS ---
    res = db.buscar_fechamento_multiplas_lojas(supabase, lista_ids_busca, str(dt_ini), str(dt_fim))

    if res and res.data:
        df = pd.DataFrame(res.data)
        # Ajuste da data para formato datetime e string brasileira
        df['data_dt'] = pd.to_datetime(df['data_fechamento'])
        df['Data Formatada'] = df['data_dt'].dt.strftime('%d/%m/%Y')
        
        # Agrupar dados por dia
        df_diario = df.groupby(['data_dt', 'Data Formatada'])['valor_quebra'].sum().reset_index()
        
        # Lógica de Cores: Verde para >= 0, Vermelho para < 0
        df_diario['Cor'] = df_diario['valor_quebra'].apply(lambda x: 'Sobra' if x >= 0 else 'Falta')

        # --- 4. MÉTRICAS ---
        saldo_total = df_diario['valor_quebra'].sum()
        m1, m2 = st.columns(2)
        m1.metric("Diferença Total no Período", f"R$ {saldo_total:,.2f}")
        m2.metric("Média de Quebra/Dia", f"R$ {df_diario['valor_quebra'].mean():,.2f}")

        # --- 5. GRÁFICO DE BARRAS COM PLOTLY ---
        st.subheader("📊 Quebras Diárias")
        
        fig = px.bar(
            df_diario,
            x='Data Formatada',
            y='valor_quebra',
            color='Cor',
            color_discrete_map={'Sobra': '#00ff00', 'Falta': '#ff4b4b'},
            text_auto='.2f',  # Mostra o valor em cima da barra
            labels={'valor_quebra': 'Diferença (R$)', 'Data Formatada': 'Dia'},
            hover_data={'Cor': False, 'Data Formatada': True, 'valor_quebra': ':.2f'}
        )
        
        fig.update_traces(textposition='outside', cliponaxis=False)
        fig.update_layout(showlegend=False, margin=dict(t=20, b=20, l=10, r=10))
        
        st.plotly_chart(fig, use_container_width=True)

        # --- 6. GRÁFICO DE LINHA (ACUMULADO) ---
        st.subheader("📉 Saldo Acumulado no Tempo")
        df_diario = df_diario.sort_values('data_dt')
        df_diario['acumulado'] = df_diario['valor_quebra'].cumsum()
        
        fig_line = px.line(
            df_diario, 
            x='Data Formatada', 
            y='acumulado',
            markers=True,
            labels={'acumulado': 'Saldo Acumulado (R$)'}
        )
        st.plotly_chart(fig_line, use_container_width=True)

        # --- 7. VISÃO ADMINISTRATIVA ---
        if user['funcao'] in ['admin', 'proprietario', 'financeiro']:
            st.write("---")
            st.subheader("🏢 Comparativo por Unidade")
            df['Loja'] = df['loja_id'].map(id_para_nome)
            comp_lojas = df.groupby('Loja')['valor_quebra'].sum().reset_index().sort_values('valor_quebra')
            
            fig_comp = px.bar(
                comp_lojas, x='Loja', y='valor_quebra', 
                color='valor_quebra', 
                color_continuous_scale=['#ff4b4b', '#00ff00'],
                text_auto='.2f'
            )
            st.plotly_chart(fig_comp, use_container_width=True)
            
    else:
        st.info("Nenhum dado de quebra encontrado para os filtros selecionados.")
