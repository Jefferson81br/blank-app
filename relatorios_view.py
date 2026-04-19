import streamlit as st
import pandas as pd
from datetime import date, timedelta
import database_utils as db

def renderizar_tela(supabase, user):
    st.title("📋 Relatórios Consolidados")
    st.markdown("Extraia dados detalhados de fechamentos por período e unidade.")

    # --- BLOCO DE FILTROS ---
    with st.container(border=True):
        col1, col2, col3 = st.columns([2, 1, 1])
        
        # Busca lojas para o filtro
        lojas_res = db.buscar_lojas(supabase)
        mapa_lojas = {l['nome']: l['id'] for l in lojas_res.data} if lojas_res.data else {}
        
        lojas_sel = col1.multiselect(
            "Filtrar por Unidades:", 
            options=list(mapa_lojas.keys()),
            default=list(mapa_lojas.keys())
        )
        
        data_inicio = col2.date_input("Data Início:", value=date.today() - timedelta(days=30), format="DD/MM/YYYY")
        data_fim = col3.date_input("Data Fim:", value=date.today(), format="DD/MM/YYYY")

    if not lojas_sel:
        st.warning("Selecione ao menos uma unidade para gerar o relatório.")
        st.stop()

    # IDs das lojas selecionadas
    lista_ids = [mapa_lojas[n] for n in lojas_sel]

    # --- BUSCA DE DADOS ---
    res = db.buscar_fechamento_multiplas_lojas(supabase, lista_ids, str(data_inicio), str(data_fim))

    if res and res.data:
        df = pd.DataFrame(res.data)
        
        # Mapeando ID da loja para Nome Amigável
        id_para_nome = {v: k for k, v in mapa_lojas.items()}
        df['loja_nome'] = df['loja_id'].map(id_para_nome)

        # Reorganizando colunas principais para o relatório (Adicionado valor_quebra)
        colunas_relatorio = [
            'data_fechamento', 'loja_nome', 'conf_cartao', 'conf_dinheiro', 
            'conf_pix', 'conf_despesa', 'valor_quebra', 'status_auditoria'
        ]
        
        # --- RESUMO RÁPIDO NO TOPO (Agora com 4 colunas) ---
        st.write("---")
        c1, c2, c3, c4 = st.columns(4)
        
        c1.metric("Total Cartão", f"R$ {df['conf_cartao'].sum():,.2f}")
        c2.metric("Total Dinheiro", f"R$ {df['conf_dinheiro'].sum():,.2f}")
        c3.metric("Total Despesas", f"R$ {df['conf_despesa'].sum():,.2f}")
        
        # 4º Elemento: Quebra de Caixa
        total_quebra = df['valor_quebra'].sum()
        c4.metric(
            "Quebra de Caixa", 
            f"R$ {total_quebra:,.2f}",
            delta=f"{total_quebra:,.2f}",
            delta_color="inverse" if total_quebra < 0 else "normal"
        )

        # --- TABELA DE DADOS ---
        st.subheader("Visualização dos Dados")
        st.dataframe(
            df[colunas_relatorio], 
            use_container_width=True,
            hide_index=True,
            column_config={
                "data_fechamento": "Data",
                "loja_nome": "Unidade",
                "conf_cartao": st.column_config.NumberColumn("Cartão", format="R$ %.2f"),
                "conf_dinheiro": st.column_config.NumberColumn("Dinheiro", format="R$ %.2f"),
                "conf_pix": st.column_config.NumberColumn("PIX", format="R$ %.2f"),
                "conf_despesa": st.column_config.NumberColumn("Despesas", format="R$ %.2f"),
                "valor_quebra": st.column_config.NumberColumn("Quebra (R$)", format="R$ %.2f"),
                "status_auditoria": "Status"
            }
        )

        # --- EXPORTAÇÃO ---
        st.write("---")
        # Garante que o CSV exportado contenha a coluna de quebra
        csv = df[colunas_relatorio].to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Baixar Relatório em CSV",
            data=csv,
            file_name=f"relatorio_caixa_{data_inicio}_a_{data_fim}.csv",
            mime="text/csv",
        )
    else:
        st.info("Nenhum dado encontrado para o período e unidades selecionadas.")
