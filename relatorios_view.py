import streamlit as st
import pandas as pd
from datetime import date, timedelta
import database_utils as db
from io import BytesIO

# Importações para geração do PDF
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def gerar_pdf(df, colunas, labels):
    """Gera um PDF formatado em modo paisagem contendo a tabela de dados."""
    buffer = BytesIO()
    # Configura documento em modo paisagem (landscape) para caber todas as colunas
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=15
    )
    
    # Cabeçalho do PDF
    story.append(Paragraph("<b>Farma Gestor - Relatório Consolidado de Fechamentos</b>", title_style))
    story.append(Spacer(1, 10))
    
    # Preparação dos dados para a tabela do ReportLab
    dados_tabela = [labels] # Primeira linha é o cabeçalho amigável
    
    for _, row in df.iterrows():
        linha = []
        for col in colunas:
            val = row.get(col, "")
            # Formata valores flutuantes como moeda
            if isinstance(val, (int, float)) and col not in ['data_fechamento', 'loja_nome', 'status_auditoria', 'status_comps']:
                linha.append(f"R$ {val:,.2f}")
            elif col == 'data_fechamento':
                # Formata a string de data para DD/MM
                try:
                    linha.append(pd.to_datetime(val).strftime('%d/%m'))
                except:
                    linha.append(str(val))
            else:
                linha.append(str(val))
        dados_tabela.append(linha)
        
    # Estilização da tabela no PDF
    t = Table(dados_tabela, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e1e1e')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 8),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('TOPPADDING', (0,0), (-1,0), 6),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-1), 7),
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f9f9f9')])
    ]))
    
    story.append(t)
    doc.build(story)
    buffer.seek(0)
    return buffer

def renderizar_tela(supabase, user):
    st.title("📋 Relatórios Consolidados2")
    st.markdown("Extraia dados detalhados de fechamentos por período, unidade e status de conferência.")

    # --- 1. BLOCO DE FILTROS ---
    with st.container(border=True):
        col1, col2, col3 = st.columns([2, 1, 1])
        
        lojas_res = db.buscar_lojas(supabase)
        mapa_lojas = {l['nome']: l['id'] for l in lojas_res.data} if lojas_res.data else {}
        
        lojas_sel = col1.multiselect(
            "Filtrar por Unidades:", 
            options=list(mapa_lojas.keys()),
            default=list(mapa_lojas.keys())
        )
        
        data_inicio = col2.date_input("Data Início:", value=date.today() - timedelta(days=30), format="DD/MM/YYYY")
        data_fim = col3.date_input("Data Fim:", value=date.today(), format="DD/MM/YYYY")

        col_f1, col_f2 = st.columns(2)
        filtro_status = col_f1.multiselect(
            "Status da Auditoria:",
            options=["Pendente", "Auditado"],
            default=["Pendente", "Auditado"]
        )
        
        filtro_comprovantes = col_f2.selectbox(
            "Integridade dos Comprovantes:",
            options=["Todos", "Completos (Os 3 OK)", "Pendentes (Algum faltando)"]
        )

    if not lojas_sel:
        st.warning("Selecione ao menos uma unidade para gerar o relatório.")
        st.stop()

    lista_ids = [mapa_lojas[n] for n in lojas_sel]

    # --- 2. BUSCA DE DADOS ---
    res = db.buscar_fechamento_multiplas_lojas(supabase, lista_ids, str(data_inicio), str(data_fim))

    if res and res.data:
        df = pd.DataFrame(res.data)
        
        id_para_nome = {v: k for k, v in mapa_lojas.items()}
        df['loja_nome'] = df['loja_id'].map(id_para_nome)

        # --- 3. APLICAÇÃO DOS FILTROS NO DATAFRAME ---
        df = df[df['status_auditoria'].isin(filtro_status)]

        df['comps_ok'] = df.apply(lambda x: all([
            x.get('check_sistema', False),
            x.get('check_deposito', False),
            x.get('check_despesas', False)
        ]), axis=1)

        if filtro_comprovantes == "Completos (Os 3 OK)":
            df = df[df['comps_ok'] == True]
        elif filtro_comprovantes == "Pendentes (Algum faltando)":
            df = df[df['comps_ok'] == False]

        if df.empty:
            st.info("Nenhum dado corresponde aos filtros selecionados.")
            st.stop()

        # --- CÁLCULO DA COLUNA 'TOTAL CONFERIDO' ---
        colunas_soma_total = [
            'conf_cartao', 'conf_crediario', 'conf_dinheiro', 'conf_boleto', 
            'conf_ifood', 'conf_pbm', 'conf_pix', 'conf_vale_compra', 
            'conf_fapp', 'conf_vlink'
        ]
        # Garante que campos nulos ou ausentes sejam computados como 0.0
        for col in colunas_soma_total:
            if col not in df.columns:
                df[col] = 0.0
            else:
                df[col] = df[col].fillna(0.0)

        # Soma matemática horizontal de todas as modalidades conferidas
        df['total_conferido'] = df[colunas_soma_total].sum(axis=1)

        # Reorganizando colunas conforme solicitado
        df['status_comps'] = df['comps_ok'].apply(lambda x: "✅ OK" if x else "🟡 Pendente")
        
        colunas_relatorio = [
            'data_fechamento', 'loja_nome', 'conf_cartao', 'conf_crediario', 'conf_dinheiro', 
            'conf_boleto', 'conf_ifood', 'conf_pbm', 'conf_pix', 'conf_vale_compra', 
            'conf_fapp', 'conf_vlink', 'total_conferido', 'conf_despesa', 'valor_quebra', 
            'status_auditoria', 'status_comps'
        ]
        
        # --- 4. RESUMO RÁPIDO NO TOPO ---
        st.write("---")
        c1, c2, c3, c4 = st.columns(4)
        
        c1.metric("Total Movimentação", f"R$ {df['total_conferido'].sum():,.2f}")
        c2.metric("Total Dinheiro", f"R$ {df['conf_dinheiro'].sum():,.2f}")
        c3.metric("Total Despesas", f"R$ {df['conf_despesa'].sum():,.2f}")
        
        total_quebra = df['valor_quebra'].sum()
        c4.metric(
            "Quebra de Caixa", 
            f"R$ {total_quebra:,.2f}",
            delta=f"{total_quebra:,.2f}",
            delta_color="inverse" if total_quebra < 0 else "normal"
        )

        # --- 5. TABELA DE DADOS ---
        st.subheader("Visualização dos Dados")
        st.dataframe(
            df[colunas_relatorio], 
            use_container_width=True,
            hide_index=True,
            column_config={
                "data_fechamento": "Data",
                "loja_nome": "Unidade",
                "conf_cartao": st.column_config.NumberColumn("Cartão", format="R$ %.2f"),
                "conf_crediario": st.column_config.NumberColumn("Crediário", format="R$ %.2f"),
                "conf_dinheiro": st.column_config.NumberColumn("Dinheiro", format="R$ %.2f"),
                "conf_boleto": st.column_config.NumberColumn("Boleto", format="R$ %.2f"),
                "conf_ifood": st.column_config.NumberColumn("Ifood", format="R$ %.2f"),
                "conf_pbm": st.column_config.NumberColumn("PBM", format="R$ %.2f"),
                "conf_pix": st.column_config.NumberColumn("Pix", format="R$ %.2f"),
                "conf_vale_compra": st.column_config.NumberColumn("VC", format="R$ %.2f"),
                "conf_fapp": st.column_config.NumberColumn("FAPP", format="R$ %.2f"),
                "conf_vlink": st.column_config.NumberColumn("Vlink", format="R$ %.2f"),
                "total_conferido": st.column_config.NumberColumn("Total", format="R$ %.2f"),
                "conf_despesa": st.column_config.NumberColumn("Despesas", format="R$ %.2f"),
                "valor_quebra": st.column_config.NumberColumn("Quebra", format="R$ %.2f"),
                "status_auditoria": "Auditado",
                "status_comps": "Comprovantes"
            }
        )

        # --- 6. EXPORTAÇÃO (CSV & PDF) ---
        st.write("---")
        exp_col1, exp_col2 = st.columns(2)
        
        with exp_col1:
            csv = df[colunas_relatorio].to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Baixar Relatório em CSV",
                data=csv,
                file_name=f"relatorio_caixa_{data_inicio}_a_{data_fim}.csv",
                mime="text/csv",
                use_container_width=True
            )
            
        with exp_col2:
            labels_pdf = ["Data", "Unidade", "Cartão", "Cred.", "Dinh.", "Boleto", "Ifood", "PBM", "Pix", "VC", "FAPP", "Vlink", "Total", "Desp.", "Quebra", "Audit.", "Comps"]
            pdf_data = gerar_pdf(df, colunas_relatorio, labels_pdf)
            st.download_button(
                label="📄 Baixar Relatório em PDF",
                data=pdf_data,
                file_name=f"relatorio_caixa_{data_inicio}_a_{data_fim}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            
    else:
        st.info("Nenhum dado encontrado para o período e unidades selecionadas.")
