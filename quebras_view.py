import streamlit as st
import pandas as pd
from datetime import date, timedelta
import calendar
import database_utils as db

def renderizar_tela(supabase, user):
    st.title("📉 Quebras de Caixa")

    # --- 1. DEFINIÇÃO DE PERMISSÕES E SELEÇÃO DE LOJA ---
    lojas_res = db.buscar_lojas(supabase)
    mapa_lojas = {l['nome']: l['id'] for l in lojas_res.data} if lojas_res.data else {}
    id_para_nome = {v: k for k, v in mapa_lojas.items()}

    # Se for gerente, trava na unidade dele. Se for admin/prop/financeiro, escolhe.
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

    # --- 2. CONFIGURAÇÃO DO PERÍODO (MENSAL OU ESPECÍFICO) ---
    st.write("---")
    tipo_filtro = st.radio("Tipo de Visualização:", ["Mensal", "Período Específico"], horizontal=True)

    if tipo_filtro == "Mensal":
        c1, c2 = st.columns(2)
        mes_sel = c1.selectbox("Mês:", list(range(1, 13)), index=date.today().month - 1)
        ano_sel = c2.selectbox("Ano:", [2025, 2026], index=1)
        
        # Define primeiro e último dia do mês
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
        df['data_fechamento'] = pd.to_datetime(df['data_fechamento']).dt.date
        
        # Criamos um range completo de datas para o gráfico não ter "buracos"
        idx = pd.date_range(dt_ini, dt_fim)
        df_completo = pd.DataFrame({'data_fechamento': idx.date})
        
        # Agrupar dados por dia (somando se houver mais de uma loja selecionada)
        df_diario = df.groupby('data_fechamento')['valor_quebra'].sum().reset_index()
        
        # Merge para garantir que todos os dias do mês apareçam
        df_final = pd.merge(df_completo, df_diario, on='data_fechamento', how='left').fillna(0)
        df_final['acumulado'] = df_final['valor_quebra'].cumsum()

        # --- 4. VISUALIZAÇÃO PRINCIPAL ---
        m1, m2 = st.columns(2)
        saldo_total = df_final['valor_quebra'].sum()
        cor_saldo = "normal" if saldo_total >= 0 else "inverse"
        
        m1.metric("Diferença Total no Período", f"R$ {saldo_total:,.2f}", delta_color=cor_saldo)
        m2.metric("Maior Falta Registrada", f"R$ {df_final['valor_quebra'].min():,.2f}")

        st.subheader("📈 Linha do Tempo e Acumulado")
        # Gráfico de barras (Dia a Dia) e Linha (Acumulado)
        st.bar_chart(df_final.set_index('data_fechamento')['valor_quebra'])
        
        st.subheader("📉 Evolução do Saldo Acumulado")
        st.line_chart(df_final.set_index('data_fechamento')['acumulado'])

        # --- 5. VISÃO ADMINISTRATIVA (COMPARATIVO ENTRE LOJAS) ---
        if user['funcao'] in ['admin', 'proprietario', 'financeiro']:
            st.write("---")
            st.subheader("🏢 Comparativo de Quebra por Unidade")
            
            df['Loja'] = df['loja_id'].map(id_para_nome)
            comp_lojas = df.groupby('Loja')['valor_quebra'].sum().sort_values()
            
            st.bar_chart(comp_lojas)
            
            with st.expander("Ver detalhes por loja"):
                st.dataframe(
                    df.groupby('Loja')['valor_quebra'].agg(['sum', 'mean', 'count']).rename(
                        columns={'sum': 'Total Quebra', 'mean': 'Média/Dia', 'count': 'Dias Lançados'}
                    ), use_container_width=True
                )
    else:
        st.info("Nenhum dado de quebra encontrado para os filtros selecionados.")
