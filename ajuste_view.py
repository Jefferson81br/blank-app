import streamlit as st
import database_utils as db
from datetime import date

def renderizar_tela(supabase, user):
    st.title("⚙️ Ajuste de Lançamentos")
    st.markdown("Esta tela permite corrigir valores específicos e recalcula o saldo de quebra automaticamente.")

    # --- 1. SELEÇÃO DE LOJA E DATA ---
    with st.container(border=True):
        col1, col2 = st.columns(2)
        
        lojas_res = db.buscar_lojas(supabase)
        mapa_lojas = {l['nome']: l['id'] for l in lojas_res.data} if lojas_res.data else {}
        
        loja_sel = col1.selectbox("Selecione a Unidade:", options=list(mapa_lojas.keys()))
        data_sel = col2.date_input("Selecione a Data:", value=date.today(), format="DD/MM/YYYY")

    # --- 2. MAPEAMENTO CORRIGIDO (CONFORME LANCAMENTO_VIEW) ---
    opcoes_ajuste = {
        "Cartão (Sistema)": "sis_cartao",
        "Cartão (Conferência)": "conf_cartao",
        "Crediário (Sistema)": "sis_crediario",
        "Crediário (Conferência)": "conf_crediario",
        "Dinheiro (Sistema)": "sis_dinheiro",
        "Dinheiro (Conferência)": "conf_dinheiro",
        "Boleto (Sistema)": "sis_boleto",
        "Boleto (Conferência)": "conf_boleto",
        "iFood (Sistema)": "sis_ifood",
        "iFood (Conferência)": "conf_ifood",
        "PBM (Sistema)": "sis_pbm",
        "PBM (Conferência)": "conf_pbm",
        "PIX (Sistema)": "sis_pix",
        "PIX (Conferência)": "conf_pix",
        "Vale Compra (Sistema)": "sis_vale_compra",
        "Vale Compra (Conferência)": "conf_vale_compra",
        "FAPP (Sistema)": "sis_fapp",
        "FAPP (Conferência)": "conf_fapp",
        "Vlink (Sistema)": "sis_vlink",
        "Vlink (Conferência)": "conf_vlink",
        "Despesas (Total)": "conf_despesa",
        "Vale Funcionário": "conf_vale_func",
        "Devol. Cartão/Outros": "conf_dev_cartao"
    }

    # --- 3. FORMULÁRIO DE AJUSTE ---
    with st.form("form_ajuste"):
        item_selecionado = st.selectbox("Campo para ajustar:", options=list(opcoes_ajuste.keys()))
        novo_valor = st.number_input("Novo valor (R$):", min_value=0.0, format="%.2f", step=0.01)
        motivo = st.text_area("Justificativa:", placeholder="Explique o motivo da alteração...")
        
        submit = st.form_submit_button("Atualizar e Recalcular Saldo", use_container_width=True)

    if submit:
        loja_id = mapa_lojas[loja_sel]
        coluna_banco = opcoes_ajuste[item_selecionado]
        
        # 1. Busca o registro atual
        res_busca = db.buscar_fechamento_por_data(supabase, loja_id, str(data_sel), str(data_sel))
        
        if res_busca and res_busca.data:
            reg = res_busca.data[0]
            registro_id = reg['id']
            
            # 2. Simulação para Recálculo
            reg_simulado = reg.copy()
            reg_simulado[coluna_banco] = novo_valor

            # Soma Conferências (Entradas)
            t_c_ent = (
                reg_simulado.get('conf_cartao', 0) + reg_simulado.get('conf_crediario', 0) + 
                reg_simulado.get('conf_dinheiro', 0) + reg_simulado.get('conf_boleto', 0) + 
                reg_simulado.get('conf_ifood', 0) + reg_simulado.get('conf_pbm', 0) + 
                reg_simulado.get('conf_pix', 0) + reg_simulado.get('conf_vale_compra', 0) + 
                reg_simulado.get('conf_fapp', 0) + reg_simulado.get('conf_vlink', 0)
            )

            # Soma Saídas
            t_c_sai = (
                reg_simulado.get('conf_despesa', 0) + reg_simulado.get('conf_vale_func', 0) + 
                reg_simulado.get('conf_dev_cartao', 0) + reg_simulado.get('conf_outros', 0)
            )

            # Soma Sistema
            t_s_ent = (
                reg_simulado.get('sis_cartao', 0) + reg_simulado.get('sis_crediario', 0) + 
                reg_simulado.get('sis_dinheiro', 0) + reg_simulado.get('sis_boleto', 0) + 
                reg_simulado.get('sis_ifood', 0) + reg_simulado.get('sis_pbm', 0) + 
                reg_simulado.get('sis_pix', 0) + reg_simulado.get('sis_vale_compra', 0) + 
                reg_simulado.get('sis_fapp', 0) + reg_simulado.get('sis_vlink', 0)
            )

            # Recálculo: (Dinheiro + Despesas) - Sistema
            nova_quebra = round((t_c_ent + t_c_sai) - t_s_ent, 2)

            # 3. Preparação do Update
            dados_update = {
                coluna_banco: novo_valor,
                "valor_quebra": nova_quebra,
                "auditado_por": f"Ajuste por {user['nome']}",
                "replica_gestor": f"Ajuste em {item_selecionado}: {motivo}",
                "status_auditoria": "Ajustado"
            }
            
            # 4. Gravação
            sucesso = db.atualizar_auditoria(supabase, registro_id, dados_update)
            
            if sucesso:
                st.success(f"✅ Campo '{item_selecionado}' atualizado. Nova Quebra: R$ {nova_quebra:,.2f}")
                st.cache_data.clear()
            else:
                st.error("Erro ao atualizar. Verifique a conexão ou se o campo existe no banco.")
        else:
            st.warning("⚠️ Lançamento não encontrado para esta data.")
