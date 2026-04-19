import streamlit as st
import pandas as pd
from datetime import date, timedelta
import database_utils as db

def renderizar_tela(supabase, user):
    st.title("📉 Quebras de Caixa")
    st.markdown("Consulte as divergências registradas entre o sistema e o valor físico.")

    # --- FILTROS NO TOPO ---
    with st.container(border=True):
        c1, c2, c3 = st.columns([2, 1, 1])
        
        # Busca lojas para o filtro
        lojas_res = db.buscar_lojas(supabase)
        mapa_lojas = {l['nome']: l['id'] for l in lojas_res.data} if lojas_res.data else {}
        
        loja_sel = c1.multiselect(
            "Filtrar Unidades:", 
            options=list(mapa_lojas.keys()),
            default=list(mapa_lojas.keys())
        )
        
        # Padrão: últimos 7 dias
        dt_ini = c2.date_input("Início:", value=date.today() - timedelta(days=7), format="DD/MM/YYYY")
        dt_fim = c3.date_input("Fim:", value=date.today(), format="DD/MM/YYYY")

    if not loja_sel:
        st.warning("Selecione uma unidade para visualizar as quebras.")
        st.stop()

    # Busca os dados no banco
    lista_ids = [mapa_lojas[n] for n in loja_sel]
    res = db.buscar_fechamento_multiplas_lojas(supabase, lista_ids, str(dt_ini), str(dt_fim))

    if res and res.data:
        df = pd.DataFrame(res.data)
        
        # Mapeamento do nome da loja
        id_para_nome = {v: k for k, v in mapa_lojas.items()}
        df['Loja'] = df['loja_id'].map(id_para_nome)
        
        # Tratamento da data
        df['Data'] = pd.to_datetime(df['data_fechamento']).dt.strftime('%d/%m/%Y')

        # --- BLOCO DE MÉTRICAS ---
        # Separamos o que é falta (negativo) e o que é sobra (positivo)
        faltas = df[df['valor_quebra'] < 0]['valor_quebra'].sum()
        sobras = df[df['valor_quebra'] > 0]['valor_quebra'].sum()
        saldo_final = df['valor_quebra'].sum()

        m1, m2, m3 = st.columns(3)
        m1.metric("Total de Faltas", f"R$ {faltas:,.2f}", delta_color="inverse")
        m2.metric("Total de Sobras", f"R$ {sobras:,.2f}")
        m3.metric("Saldo Líquido", f"R$ {saldo_final:,.2f}", 
                  delta="OK" if -0.01 <= saldo_final <= 0.01 else f"{saldo_final:,.2f}")

        st.write("---")

        col_graf, col_tab = st.columns([1.5, 2])

        with col_graf:
            st.subheader("📊 Ranking por Unidade")
            # Agrupa por loja para ver quem tem mais quebra acumulada no período
            ranking = df.groupby('Loja')['valor_quebra'].sum().sort_values()
            st.bar_chart(ranking)

        with col_tab:
            st.subheader("📝 Detalhamento")
            # Exibe os dados de forma tabular para conferência rápida
            df_view = df[['Data', 'Loja', 'valor_quebra', 'status_auditoria']].copy()
            
            # Ordena pela data mais recente
            df_view = df_view.sort_values(by='Data', ascending=False)

            st.dataframe(
                df_view,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "valor_quebra": st.column_config.NumberColumn(
                        "Divergência (R$)",
                        format="R$ %.2f",
                        help="Valores negativos indicam falta no caixa."
                    ),
                    "status_auditoria": "Status"
                }
            )

        # --- ALERTA DE QUEBRAS CRÍTICAS ---
        # Mostra apenas quebras maiores que R$ 10,00 (exemplo) para foco imediato
        quebras_criticas = df[df['valor_quebra'].abs() > 10.00]
        if not quebras_criticas.empty:
            st.error(f"⚠️ Identificamos {len(quebras_criticas)} lançamentos com divergência superior a R$ 10,00.")
            
    else:
        st.info("Nenhuma quebra registrada no período selecionado.")
