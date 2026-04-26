import streamlit as st
import pandas as pd
from datetime import date, timedelta
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
        lojas_para_renderizar = [id_para_nome.get(loja_id_selecionada)]
        st.info(f"Unidade: **{lojas_para_renderizar[0]}**")
    else:
        with st.container(border=True):
            lojas_para_renderizar = st.multiselect(
                "Selecione as Unidades para Comparação:", 
                options=list(mapa_lojas.keys()),
                default=list(mapa_lojas.keys())[0] if mapa_lojas else None
            )

    if not lojas_para_renderizar:
        st.warning("Selecione pelo menos uma unidade.")
        return

    # --- 2. DEFINIÇÃO DO PERÍODO ---
    hoje = date.today()
    data_inicio = hoje - timedelta(days=30)
    data_fim = hoje

    # --- 3. LOOP POR LOJA (GERANDO GRÁFICOS INDIVIDUAIS) ---
    for nome_loja in lojas_para_renderizar:
        id_loja = mapa_lojas[nome_loja]
        
        st.markdown(f"""
            <div style="background-color: #1e1e1e; padding: 10px; border-radius: 10px; border-left: 5px solid #00ff00; margin-top: 30px;">
                <h3 style="margin:0;">🏢 Unidade: {nome_loja}</h3>
            </div>
        """, unsafe_allow_html=True)

        # Busca dados específicos desta loja
        res = db.buscar_fechamento_multiplas_lojas(supabase, [id_loja], str(data_inicio), str(data_fim))

        if res and res.data:
            df = pd.DataFrame(res.data)
            df['data_dt'] = pd.to_datetime(df['data_fechamento'])
            df = df.sort_values(by='data_dt')
            df['Data_BR'] = df['data_dt'].dt.strftime('%d/%m/%Y')
            df['acumulado'] = df['valor_quebra'].cumsum()
            
            # --- LÓGICA DE CORES (VERDE/VERMELHO) ---
            df['cor'] = df['valor_quebra'].apply(lambda x: '#00ff00' if x >= 0 else '#ff4b4b')

            # --- 4. GRÁFICO DE BARRAS DIÁRIO ---
            fig_bar = px.bar(
                df, 
                x='data_dt', 
                y='valor_quebra',
                title=f"Diferenças Diárias - {nome_loja}",
                hover_data={'data_dt': False, 'Data_BR': True, 'valor_quebra': ':.2f'}
            )
            
            fig_bar.update_traces(marker_color=df['cor']) # Aplica as cores individuais

            fig_bar.update_layout(
                xaxis_title="Dia",
                yaxis_title="Valor (R$)",
                margin=dict(t=50, b=20, l=10, r=10),
                height=350
            )
            
            st.plotly_chart(fig_bar, use_container_width=True)

            # --- 5. GRÁFICO DE LINHA ACUMULADO ---
            fig_line = px.line(
                df, 
                x='data_dt', 
                y='acumulado',
                title=f"Evolução do Saldo - {nome_loja}",
                markers=True,
                hover_data={'data_dt': False, 'Data_BR': True, 'acumulado': ':.2f'}
            )
            
            fig_line.update_traces(line_color='#00ff00') # Linha principal em verde

            fig_line.update_layout(
                xaxis_title="Dia",
                yaxis_title="Acumulado (R$)",
                margin=dict(t=50, b=20, l=10, r=10),
                height=300
            )
            
            st.plotly_chart(fig_line, use_container_width=True)
            
            # Resumo em métrica
            total = df['valor_quebra'].sum()
            st.metric(f"Saldo Final {nome_loja}", f"R$ {total:,.2f}", delta=f"{total:,.2f}")
            st.divider()

        else:
            st.caption(f"ℹ️ Nenhum dado encontrado para {nome_loja} no período.")

    # --- 6. OPÇÃO DE CONSOLIDADO (TODOS) ---
    if len(lojas_para_renderizar) > 1:
        with st.expander("📊 VER TOTAL CONSOLIDADO (SOMA DE TODAS AS LOJAS)"):
            all_ids = [mapa_lojas[n] for n in lojas_para_renderizar]
            res_total = db.buscar_fechamento_multiplas_lojas(supabase, all_ids, str(data_inicio), str(data_fim))
            
            if res_total and res_total.data:
                df_total = pd.DataFrame(res_total.data)
                df_total = df_total.groupby('data_fechamento')['valor_quebra'].sum().reset_index()
                df_total['data_dt'] = pd.to_datetime(df_total['data_fechamento'])
                df_total = df_total.sort_values(by='data_dt')
                df_total['cor'] = df_total['valor_quebra'].apply(lambda x: '#00ff00' if x >= 0 else '#ff4b4b')
                
                fig_total = px.bar(df_total, x='data_dt', y='valor_quebra')
                fig_total.update_traces(marker_color=df_total['cor'])
                st.plotly_chart(fig_total, use_container_width=True)
                st.metric("Total Geral Acumulado", f"R$ {df_total['valor_quebra'].sum():,.2f}")
