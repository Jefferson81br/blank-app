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
        lojas_selecionadas = [id_para_nome.get(loja_id_selecionada)]
        st.info(f"Unidade: **{lojas_selecionadas[0]}**")
    else:
        with st.container(border=True):
            lojas_selecionadas = st.multiselect(
                "Selecione as Unidades:", 
                options=list(mapa_lojas.keys()),
                default=list(mapa_lojas.keys())[0] if mapa_lojas else None
            )

    if not lojas_selecionadas:
        st.warning("Selecione ao menos uma unidade.")
        return

    # --- 2. DEFINIÇÃO DO PERÍODO (Mês Atual Completo para a Grade) ---
    hoje = date.today()
    primeiro_dia = hoje.replace(day=1)
    ultimo_dia_mes = calendar.monthrange(hoje.year, hoje.month)[1]
    data_fim_mes = hoje.replace(day=ultimo_dia_mes)
    
    # Criar DataFrame base com TODOS os dias do mês para garantir a estética da grade
    datas_mes = pd.date_range(start=primeiro_dia, end=data_fim_mes)

    # --- 3. LOOP PARA GERAR GRÁFICOS SEPARADOS POR LOJA ---
    for nome_loja in lojas_selecionadas:
        id_loja = mapa_lojas[nome_loja]
        
        st.markdown(f"""
            <div style="background-color: #1e1e1e; padding: 10px; border-radius: 10px; border-left: 5px solid #00ff00; margin-top: 30px; margin-bottom: 10px;">
                <h3 style="margin:0; color: white;">🏢 Unidade: {nome_loja}</h3>
            </div>
        """, unsafe_allow_html=True)

        # Busca dados da loja específica
        res = db.buscar_fechamento_multiplas_lojas(supabase, [id_loja], str(primeiro_dia), str(hoje))

        # Preparação do DataFrame
        df_base = pd.DataFrame({'data_dt': datas_mes})
        if res and res.data:
            df_dados = pd.DataFrame(res.data)
            df_dados['data_dt'] = pd.to_datetime(df_dados['data_fechamento'])
            df_final = pd.merge(df_base, df_dados, on='data_dt', how='left').fillna({'valor_quebra': 0})
        else:
            df_final = df_base.copy()
            df_final['valor_quebra'] = 0

        df_final['Data_BR'] = df_final['data_dt'].dt.strftime('%d/%m/%Y')
        df_final['cor'] = df_final['valor_quebra'].apply(lambda x: '#00ff00' if x >= 0 else '#ff4b4b')
        df_final['acumulado'] = df_final['valor_quebra'].cumsum()

        # --- 4. GRÁFICO DE BARRAS (ESTÉTICA ORIGINAL) ---
        st.subheader(f"📊 Diferenças Diárias - {nome_loja}")
        fig_bar = px.bar(
            df_final, 
            x='data_dt', 
            y='valor_quebra',
            text='valor_quebra',
            hover_data={'data_dt': False, 'Data_BR': True, 'valor_quebra': ':.2f'}
        )

        fig_bar.update_traces(
            marker_color=df_final['cor'],
            texttemplate='%{text:.2f}', 
            textposition='outside',
            cliponaxis=False
        )

        # Estilização idêntica ao arquivo original
        fig_bar.update_xaxes(
            type='date',
            tickformat="%d/%m",
            tickmode='linear',
            dtick=86400000,
            tickangle=-45,
            showgrid=True,
            gridcolor='rgba(255, 255, 255, 0.1)',
            title="Dia"
        )

        max_val = df_final['valor_quebra'].abs().max()
        margem = max_val * 0.25 if max_val > 0 else 5
        fig_bar.update_yaxes(
            range=[df_final['valor_quebra'].min() - margem, df_final['valor_quebra'].max() + margem],
            showgrid=True,
            gridcolor='rgba(255, 255, 255, 0.1)',
            title="Diferença (R$)"
        )

        fig_bar.update_layout(
            margin=dict(t=30, b=50, l=10, r=10),
            height=400,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        
        st.plotly_chart(fig_bar, use_container_width=True)

        # --- 5. GRÁFICO DE LINHA (ACUMULADO) ---
        st.subheader(f"📉 Saldo Acumulado - {nome_loja}")
        fig_line = px.line(
            df_final, 
            x='data_dt', 
            y='acumulado',
            markers=True,
            hover_data={'data_dt': False, 'Data_BR': True, 'acumulado': ':.2f'}
        )
        
        fig_line.update_traces(line_color='#00ff00')
        fig_line.update_xaxes(type='date', tickformat="%d/%m", gridcolor='rgba(255, 255, 255, 0.1)')
        fig_line.update_yaxes(gridcolor='rgba(255, 255, 255, 0.1)')
        
        fig_line.update_layout(
            margin=dict(t=30, b=50, l=10, r=10),
            height=300,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        
        st.plotly_chart(fig_line, use_container_width=True)
        
        # Métrica de Resumo
        total_loja = df_final['valor_quebra'].sum()
        st.metric(f"Saldo Final {nome_loja}", f"R$ {total_loja:,.2f}", delta=f"{total_loja:,.2f}")
        st.divider()

    # --- 6. OPÇÃO DE TODOS (CONSOLIDADO) NO FINAL ---
    if len(lojas_selecionadas) > 1:
        with st.expander("🌍 VER TOTAL CONSOLIDADO (SOMA DA REDE SELECIONADA)"):
            ids_all = [mapa_lojas[n] for n in lojas_selecionadas]
            res_all = db.buscar_fechamento_multiplas_lojas(supabase, ids_all, str(primeiro_dia), str(hoje))
            
            if res_all and res_all.data:
                df_all = pd.DataFrame(res_all.data)
                df_all = df_all.groupby('data_fechamento')['valor_quebra'].sum().reset_index()
                df_all['data_dt'] = pd.to_datetime(df_all['data_fechamento'])
                
                # Merge para grade completa
                df_total = pd.merge(pd.DataFrame({'data_dt': datas_mes}), df_all, on='data_dt', how='left').fillna(0)
                df_total['cor'] = df_total['valor_quebra'].apply(lambda x: '#00ff00' if x >= 0 else '#ff4b4b')

                fig_all = px.bar(df_total, x='data_dt', y='valor_quebra', text='valor_quebra')
                fig_all.update_traces(marker_color=df_total['cor'], texttemplate='%{text:.2f}', textposition='outside')
                fig_all.update_xaxes(tickangle=-45, tickformat="%d/%m", dtick=86400000)
                st.plotly_chart(fig_all, use_container_width=True)
                st.metric("Total Geral da Rede", f"R$ {df_total['valor_quebra'].sum():,.2f}")
