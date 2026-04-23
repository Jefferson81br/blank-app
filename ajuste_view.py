import streamlit as st
import database_utils as db
from datetime import date

def renderizar_tela(supabase, user):
    st.title("⚙️ Ajuste de Lançamentos")
    st.markdown("Esta tela permite corrigir valores específicos de um fechamento já realizado.")

    # --- 1. SELEÇÃO DE LOJA E DATA ---
    with st.container(border=True):
        col1, col2 = st.columns(2)
        
        lojas_res = db.buscar_lojas(supabase)
        mapa_lojas = {l['nome']: l['id'] for l in lojas_res.data} if lojas_res.data else {}
        
        loja_sel = col1.selectbox("Selecione a Unidade:", options=list(mapa_lojas.keys()))
        # Data no formato brasileiro via widget do Streamlit
        data_sel = col2.date_input("Selecione a Data:", value=date.today(), format="DD/MM/YYYY")

    # --- 2. MAPEAMENTO DE CAMPOS DO BANCO ---
    # Mapeamos o nome amigável para a coluna real na tabela 'fechamentos'
    opcoes_ajuste = {
        "Cartão (Sistema)": "sistema_cartao",
        "Cartão (Conferência)": "conf_cartao",
        "Crediário (Sistema)": "sistema_crediario",
        "Crediário (Conferência)": "conf_crediario",
        "Dinheiro (Sistema)": "sistema_dinheiro",
        "Dinheiro (Conferência)": "conf_dinheiro",
        "Boleto (Sistema)": "sistema_boleto",
        "Boleto (Conferência)": "conf_boleto",
        "iFood (Sistema)": "sistema_ifood",
        "iFood (Conferência)": "conf_ifood",
        "PBM (Sistema)": "sistema_pbm",
        "PBM (Conferência)": "conf_pbm",
        "PIX (Sistema)": "sistema_pix",
        "PIX (Conferência)": "conf_pix",
        "Vale Compra (Sistema)": "sistema_vale",
        "Vale Compra (Conferência)": "conf_vale",
        "FAPP (Sistema)": "sistema_fapp",
        "FAPP (Conferência)": "conf_fapp",
        "Vlink (Sistema)": "sistema_vlink",
        "Vlink (Conferência)": "conf_vlink",
        "Despesas (Total)": "conf_despesa",
        "Vale Funcionário": "vale_funcionario",
        "Devol. Cartão/Outros": "dev_cartao"
    }

    # --- 3. FORMULÁRIO DE AJUSTE ---
    with st.form("form_ajuste"):
        item_selecionado = st.selectbox("Selecione o campo para ajustar:", options=list(opcoes_ajuste.keys()))
        novo_valor = st.number_input("Informe o novo valor correto (R$):", min_value=0.0, format="%.2f")
        motivo = st.text_area("Motivo do Ajuste:", placeholder="Ex: Erro de digitação no lançamento original...")
        
        submit = st.form_submit_button("Atualizar Valor", use_container_width=True)

    if submit:
        loja_id = mapa_lojas[loja_sel]
        coluna_banco = opcoes_ajuste[item_selecionado]
        
        # Primeiro, buscamos se o registro existe para essa data/loja (Apenas Ativos)
        res_busca = db.buscar_fechamento_por_data(supabase, loja_id, str(data_sel), str(data_sel))
        
        if res_busca and res_busca.data:
            registro_id = res_busca.data[0]['id']
            
            # Preparamos os dados para atualização
            # Além do valor, atualizamos quem fez o ajuste e o status
            dados_update = {
                coluna_banco: novo_valor,
                "auditado_por": f"Ajuste por {user['nome']}",
                "replica_gestor": f"Ajuste Manual no campo {item_selecionado}: {motivo}",
                "status_auditoria": "Ajustado Manualmente"
            }
            
            sucesso = db.atualizar_auditoria(supabase, registro_id, dados_update)
            
            if sucesso:
                st.success(f"✅ {item_selecionado} atualizado para R$ {novo_valor:,.2f} com sucesso!")
                # Forçamos a limpeza do cache para refletir nos relatórios
                st.cache_data.clear()
            else:
                st.error("Erro ao tentar atualizar o banco de dados.")
        else:
            st.warning("⚠️ Nenhum lançamento ativo encontrado para esta loja nesta data. O gerente precisa realizar o lançamento primeiro.")
