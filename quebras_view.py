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
        modo_visao = "Individual"
    else:
        with st.container(border=True):
            col_l, col_m = st.columns([3, 1])
            loja_nome_sel = col_l.multiselect(
                "Selecione as Unidades:", 
                options=list(mapa_lojas.keys()),
                default=list(mapa_lojas.keys())[0] if mapa_lojas else None
            )
            lista_ids_busca = [mapa_lojas[n] for n in loja_nome_sel]
            
            modo_visao = col_m.radio("Modo de Visão:", ["Comparativo", "Consolidado (Soma)"])

    # --- 2. DEFINIÇÃO DO PERÍODO ---
    hoje = date.today()
    data_inicio = hoje - timedelta(days=30)
    data_fim = hoje

    # --- 3. BUSCA E TRATAMENTO DE DADOS ---
    res = db.buscar_fechamento_multiplas_lojas(supabase, lista_ids_busca, str(data_inicio), str(data_fim))

    if res and res.data:
        df = pd.DataFrame(res.data)
        df['data_dt'] = pd.to_datetime(df['data_fechamento'])
        df['loja_nome'] = df['loja_id'].map(id_para_nome)
        df = df.sort_values(by='data_dt')

        # Lógica de Consolidado vs Comparativo
        if modo_visao == "Consolidado (Soma)":
            # Agrupa por data somando os valores de todas as lojas selecionadas
            df_plot = df.groupby('data_dt')['valor_quebra'].sum().reset_index()
            df_plot['loja_nome'] = "TOTAL CONSOLIDADO"
        else:
            # Mantém as lojas separadas para o gráfico comparativo
            df_plot = df.copy()

        # Cálculo do Acumulado (por loja ou total)
        if modo_visao == "Consolidado (Soma)":
            df_plot['acumulado'] = df_plot['valor_quebra'].cumsum()
        else:
            df_plot['acumulado'] = df_plot.groupby('loja_nome')['valor_quebra'].cumsum()

        # Formatação de Data para o Hover
        df_plot['Data_BR'] = df_plot['data_dt'].dt.strftime('%d/%m/%Y')

        # --- 4. GRÁFICO DE BARRAS (DIÁRIO) ---
        st.subheader("📊 Diferenças Diárias")
        
        fig_bar = px.bar(
            df_plot, 
            x='data_dt', 
            y='valor_quebra',
            color='loja_nome' if modo_visao == "Comparativo" else None,
            barmode='group', # Coloca as barras uma ao lado da outra
            color_discrete_sequence=px.colors.qualitative.Bold,
            hover_data={'data_dt': False, 'Data_BR': True, 'valor_quebra': ':.2f'}
        )

        # Estilização do Gráfico
        fig_bar.update_layout(
            xaxis_title="Dia",
            yaxis_title="Valor (R$)",
            legend_title="Unidades",
            hovermode="x unified"
        )
        
        st.plotly_chart(fig_bar, use_container_width=True)

        # --- 5. GRÁFICO DE LINHA (EVOLUÇÃO ACUMULADA) ---
        st.subheader("📉 Saldo Acumulado no Período")
        
        fig_line = px.line(
            df_plot, 
            x='data_dt', 
            y='acumulado',
            color='loja_nome' if modo_visao == "Comparativo" else None,
            markers=True,
            hover_data={'data_dt': False, 'Data_BR': True, 'acumulado': ':.2f'}
        )

        fig_line.update_layout(
            xaxis_title="Dia",
            yaxis_title="Acumulado (R$)",
            legend_title="Unidades"
        )
        
        st.plotly_chart(fig_line, use_container_width=True)

        # --- 6. RESUMO DE TOTAIS ---
        st.write("---")
        st.markdown("**Resumo Final do Período Selecionado:**")
        cols = st.columns(len(loja_nome_sel) if modo_visao == "Comparativo" else 1)
        
        if modo_visao == "Comparativo":
            for i, nome in enumerate(loja_nome_sel):
                total_loja = df[df['loja_nome'] == nome]['valor_quebra'].sum()
                cor = "green" if total_loja >= 0 else "red"
                cols[i].metric(nome, f"R$ {total_loja:,.2f}", delta=f"{total_loja:,.2f}", delta_color="normal")
        else:
            total_geral = df['valor_quebra'].sum()
            st.metric("Total de Todas as Unidades", f"R$ {total_geral:,.2f}")

    else:
        st.info("Nenhum dado encontrado para o período e lojas selecionadas.")
