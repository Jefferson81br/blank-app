import streamlit as st
import database_utils as db
from datetime import date

def renderizar_tela(supabase, user):
    st.title("⚙️ Ajuste de Lançamentos")
    st.markdown("Esta tela permite corrigir valores específicos de um fechamento já realizado e recalcula o saldo automaticamente.")

    # --- 1. SELEÇÃO DE LOJA E DATA ---
    with st.container(border=True):
        col1, col2 = st.columns(2)
        
        lojas_res = db.buscar_lojas(supabase)
        mapa_lojas = {l['nome']: l['id'] for l in lojas_res.data} if lojas_res.data else {}
        
        loja_sel = col1.selectbox("Selecione a Unidade:", options=list(mapa_lojas.keys()))
        # Data no formato brasileiro
        data_sel = col2.date_input("Selecione a Data:", value=date.today(), format="DD/MM/YYYY")

    # --- 2. MAPEAMENTO DE CAMPOS DO BANCO ---
    # Ajustado para refletir os nomes de colunas padrão do seu banco
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
        
        submit = st.form_submit_button("Atualizar e Recalcular Saldo", use_container_width=True)

    if submit:
        loja_id = mapa_lojas[loja_sel]
        coluna_banco = opcoes_ajuste[item_selecionado]
        
        # 1. Busca o registro original
        res_busca = db.buscar_fechamento_por_data(supabase, loja_id, str(data_sel), str(data_sel))
        
        if res_busca and res_busca.data:
            reg = res_busca.data[0]
            registro_id = reg['id']
            
            # 2. Simula o novo estado do registro para recalcular a quebra
            reg_simulado = reg.copy()
            reg_simulado[coluna_banco] = novo_valor

            # Cálculo de Entradas (Conferência)
            t_c_ent = (
                reg_simulado.get('conf_cartao', 0) + reg_simulado.get('conf_crediario', 0) + 
                reg_simulado.get('conf_dinheiro', 0) + reg_simulado.get('conf_boleto', 0) + 
                reg_simulado.get('conf_ifood', 0) + reg_simulado.get('conf_pbm', 0) + 
                reg_simulado.get('conf_pix', 0) + reg_simulado.get('conf_vale', 0) + 
                reg_simulado.get('conf_fapp', 0) + reg_simulado.get('conf_vlink', 0)
            )

            # Cálculo de Saídas/Justificativas
            t_c_sai = (
                reg_simulado.get('conf_despesa', 0) + reg_simulado.get('vale_funcionario', 0) + 
                reg_simulado.get('dev_cartao', 0)
            )

            # Cálculo do Sistema (Vendas Brutas)
            t_s_ent = (
                reg_simulado.get('sistema_cartao', 0) + reg_simulado.get('sistema_crediario', 0) + 
                reg_simulado.get('sistema_dinheiro', 0) + reg_simulado.get('sistema_boleto', 0) + 
                reg_simulado.get('sistema_ifood', 0) + reg_simulado.get('sistema_pbm', 0) + 
                reg_simulado.get('sistema_pix', 0) + reg_simulado.get('sistema_vale', 0) + 
                reg_simulado.get('sistema_fapp', 0) + reg_simulado.get('sistema_vlink', 0)
            )

            # Recálculo Final: (Dinheiro em mãos + Despesas pagas) - O que o sistema diz que vendeu
            nova_quebra = round((t_c_ent + t_c_sai) - t_s_ent, 2)

            # 3. Prepara o pacote de atualização
            dados_update = {
                coluna_banco: novo_valor,
                "valor_quebra": nova_quebra,
                "auditado_por": f"Ajuste por {user['nome']}",
                "replica_gestor": f"Ajuste Manual: {item_selecionado} alterado. Motivo: {motivo}",
                "status_auditoria": "Ajustado Manualmente"
            }
            
            # 4. Envia ao banco
            sucesso = db.atualizar_auditoria(supabase, registro_id, dados_update)
            
            if sucesso:
                st.success(f"✅ Sucesso! {item_selecionado} atualizado. Novo Saldo de Quebra: R$ {nova_quebra:,.2f}")
                st.cache_data.clear()
            else:
                st.error("Erro técnico ao atualizar o banco de dados.")
        else:
            st.warning("⚠️ Nenhum lançamento ativo encontrado para esta data. Não há o que ajustar.")
