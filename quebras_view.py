import streamlit as st
import pandas as pd
from datetime import date, timedelta
import calendar
import database_utils as db
import plotly.express as px

def renderizar_tela(supabase, user):
    st.title("📉 Quebras de Caixa")

    # --- 1. SELEÇÃO DE UNIDADES E PERMISSÕES ---
    lojas_res = db.buscar_lojas(supabase)
    mapa_lojas = {l['nome']: l['id'] for l in lojas_res.data} if lojas_res.data else {}
    id_para_nome = {v: k for k, v in mapa_lojas.items()}

    if user['funcao'] not in ['admin', 'proprietario', 'financeiro']:
        loja_id_selecionada = user.get('unidade_id')
        lista_ids_busca = [loja_id_selecionada]
        st.info(f"Unidade: **{id_para_nome.get(loja_id_selecionada, 'Minha Unidade')}**")
    else:
        with st.container(border=True):
            loja_nome_sel = st.multiselect(
                "Selecione as Unidades:", 
                options=list(mapa_lojas.keys()),
                default=list(mapa_lojas.keys())[0] if mapa_lojas else None
            )
            lista_ids_busca = [mapa_lojas[n] for n in loja_nome_sel]

    # --- 2. DEFINIÇÃO DO PERÍODO ---
    filtro_tempo = st.radio("Filtro:", ["Mensal", "Período Específico"], horizontal=True)

    if filtro_tempo == "Mensal":
        c1, c2 = st.columns(2)
        mes_sel = c1.selectbox("Mês:", list(range(1, 13)), index=date.today().month - 1)
        ano_sel = c2.selectbox("Ano:", [2025, 2026], index=1)
        ultimo_dia = calendar.monthrange(ano_sel, mes_sel)[1]
        dt_ini = date(ano_sel, mes_sel, 1)
        dt_fim = date(ano_sel, mes_sel, ultimo_dia)
    else:
        c1, c2 = st.columns(2)
        dt_ini = c1.date_input("Início:", value=date.today() - timedelta(days=30))
        dt_fim = c2.date_input("Fim:", value=date.today())

    # --- 3. PROCESSAMENTO DOS DADOS (O SEGREDO DA SOMA) ---
    res = db.buscar_fechamento_multiplas_lojas(supabase, lista_ids_busca, str(dt_ini), str(dt_fim))

    if res and res.data:
        df_raw = pd.DataFrame(res.data)
        # Converte para objeto de data puro do Python
        df_raw['data_dt'] = pd.to_datetime(df_raw['data_fechamento']).dt.date
        
        # A. Consolida os valores por dia (soma se houver várias lojas selecionadas)
        df_diario = df_raw.groupby('data_dt')['valor_quebra'].sum().reset_index()

        # B. Cria a linha do tempo completa (Todos os dias do período)
        datas_full = pd.date_range(start=dt_ini, end=dt_fim).date
        df_timeline = pd.DataFrame({'data_dt': datas_full})

        # C. Merge: Quem não tem registro recebe 0.00
        df_final = pd.merge(df_timeline, df_diario, on='data_dt', how='left')
        df_final['valor_quebra'] = df_final['valor_quebra'].fillna(0).astype(float)

        # D. Ordenação rigorosa antes do Acumulado
        df_final = df_final.sort_values('data_dt')
        df_final['acumulado'] = df_final['valor_quebra'].cumsum()

        # E. Formatação para exibição nos gráficos
        df_final['Data_BR'] = pd.to_datetime(df_final['data_dt']).dt.strftime('%d/%m/%Y')
        df_final['Cor'] = df_final['valor_quebra'].apply(lambda x: 'Sobra' if x >= 0 else 'Falta')

        # --- 4. EXIBIÇÃO ---
        saldo = df_final['valor_quebra'].sum()
        st.metric("Saldo Final do Período", f"R$ {saldo:,.2f}", delta_color="inverse" if saldo < 0 else "normal")

        # Gráfico de Barras (Diário) - MELHORADO
        st.subheader("📊 Quebra Diária (Sobra/Falta)")
        fig_bar = px.bar(
            df_final, 
            x='data_dt', 
            y='valor_quebra',
            color='Cor',
            color_discrete_map={'Sobra': '#00ff00', 'Falta': '#ff4b4b'},
            text='valor_quebra', # Mudamos para usar a coluna diretamente
            hover_data={'data_dt': False, 'Data_BR': True, 'valor_quebra': ':.2f'}
        )

        # Ajustes de estilo do texto nas barras
        fig_bar.update_traces(
            texttemplate='<b>R$ %{text:.2f}</b>', # Texto em negrito e com R$
            textposition='outside',               # Força o texto para fora da barra
            cliponaxis=False,                     # Impede que o texto seja cortado no topo
            textfont=dict(size=15, color="white") # Aumenta o tamanho da fonte
        )

        # Ajuste do eixo Y para dar espaço ao texto no topo
        margem = df_final['valor_quebra'].abs().max() * 0.2
        fig_bar.update_yaxes(range=[df_final['valor_quebra'].min() - margem, df_final['valor_quebra'].max() + margem])
        
        fig_bar.update_xaxes(type='date', tickformat="%d/%m")
        st.plotly_chart(fig_bar, use_container_width=True)
        # Gráfico de Linha (Acumulado)
        st.subheader("📉 Saldo Acumulado (Evolução)")
        fig_line = px.line(
            df_final, 
            x='data_dt', 
            y='acumulado',
            markers=True,
            hover_data={'data_dt': False, 'Data_BR': True, 'acumulado': ':.2f'}
        )
        fig_line.update_xaxes(type='date', tickformat="%d/%m")
        fig_line.add_hline(y=0, line_dash="dash", line_color="white")
        st.plotly_chart(fig_line, use_container_width=True)

        # Tabela Detalhada
        with st.expander("🔎 Ver tabela de dados"):
            st.dataframe(df_final[['Data_BR', 'valor_quebra', 'acumulado']], use_container_width=True, hide_index=True)

    else:
        st.info("Nenhum lançamento encontrado para este período.")
