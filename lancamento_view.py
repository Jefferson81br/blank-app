import streamlit as st
from datetime import date, timedelta
import database_utils as db

def renderizar_tela(supabase, user):
    # --- AJUSTE DE LARGURA PARA COMUNICAÇÃO ---
    margem_esq, centro, coluna_avisos = st.columns([0.1, 2, 2])

    loja_id = user['unidade_id']
    if user['funcao'] == 'admin':
        # (Sua lógica de selectbox para admin aqui se necessário...)
        pass

    with centro:
        st.title("📝 Lançamento Diário")
        
        # --- STATUS E DATA (Igual ao anterior) ---
        data_sel = st.date_input("Data do Movimento", value=date.today(), max_value=date.today())
        st.write("---")

        # ... (Suas funções linha_entrada e linha_saida continuam aqui) ...
        def linha_entrada(label, key):
            col1, col2, col3, col4 = st.columns([2, 2, 2, 1.5])
            col1.markdown(f"<div style='padding-top:10px'><b>{label}</b></div>", unsafe_allow_html=True)
            v_s = col2.number_input("R$", key=f"s_{key}", format="%.2f", step=0.01, label_visibility="collapsed")
            v_c = col3.number_input("R$", key=f"c_{key}", format="%.2f", step=0.01, label_visibility="collapsed")
            ace = v_c - v_s
            cor = "white" if ace == 0 else ("#ff4b4b" if ace < 0 else "#00ff00")
            col4.markdown(f"<div style='padding-top:10px; color:{cor}; font-weight:bold;'>R$ {ace:.2f}</div>", unsafe_allow_html=True)
            return v_s, v_c, ace

        # (Simulação dos campos para o exemplo não ficar incompleto)
        sc, cc, ac = linha_entrada("CARTÃO", "car")
        sr, cr, ar = linha_entrada("CREDIÁRIO", "cre")
        sd, cd, ad = linha_entrada("DINHEIRO", "din")
        sb, cb, ab = linha_entrada("BOLETO", "bol")
        si, ci, ai = linha_entrada("IFOOD", "ifo")
        sp, cp, ap = linha_entrada("PBM", "pbm")
        sx, cx, ax = linha_entrada("PIX / TRANSF", "pix")
        sv, cv, av = linha_entrada("VALE COMPRA", "vco")
        sf, cf, af = linha_entrada("FARMÁCIAS APP", "fap")
        sl, cl, al = linha_entrada("VIDA LINK", "vli")
        
        # ... (Cálculos de totais e botão de salvar aqui embaixo como no seu código atual) ...

    # --- COLUNA DA DIREITA: INSTRUÇÕES E RÉPLICAS ---
    with coluna_avisos:
        st.markdown("<br><br>", unsafe_allow_html=True) # Alinha com o início do formulário
        
        # 1. QUADRO DE INSTRUÇÕES (Fixo)
        st.info("""
        ### 📖 Instruções de Preenchimento
        1. **Valor Sistema:** Insira o valor exato extraído do relatório de fechamento do seu software.
        2. **Conferência:** Digite o valor físico contado ou o comprovante da maquininha.
        3. **Diferenças:** Caso o acerto fique vermelho, utilize o campo 'Observações' abaixo para explicar o motivo (ex: erro de operadora, falta de troco).
        4. **Anexos:** É obrigatório anexar o print do resumo de vendas do sistema.
        """)

        st.write("---")

        # 2. QUADRO DE RÉPLICAS DO FINANCEIRO (Dinâmico)
        st.subheader("💬 Feedback do Financeiro")
        
        # Buscamos os 2 últimos registros que contenham réplicas para esta loja
        feedback_res = supabase.table("fechamentos")\
            .select("data_fechamento, replica_gestor, observacoes")\
            .eq("loja_id", loja_id)\
            .not.is_("replica_gestor", "null")\
            .order("data_fechamento", desc=True)\
            .limit(2)\
            .execute()

        if feedback_res.data:
            for fb in feedback_res.data:
                with st.container(border=True):
                    data_pt = date.fromisoformat(fb['data_fechamento']).strftime('%d/%m')
                    st.caption(f"Referente ao dia {data_pt}")
                    st.markdown(f"**Gestor diz:** {fb['replica_gestor']}")
                    if fb['observacoes']:
                        st.markdown(f"*Sua Obs original:* {fb['observacoes']}")
        else:
            st.write("Nenhum apontamento recente.")

        # Campo de Observação do Gerente (movido para cá para ficar visível junto ao feedback)
        st.write("---")
        with st.form("f_final_caixa"):
            st.subheader("📝 Suas Observações")
            obs_gerente = st.text_area("Explique aqui eventuais diferenças ou responda ao financeiro:", height=150)
            imgs = st.file_uploader("Prints do Fechamento", accept_multiple_files=True)
            
            if st.form_submit_button("✅ SALVAR FECHAMENTO", use_container_width=True):
                # ... Lógica de salvamento enviando a 'obs_gerente' ...
                st.success("Enviado!")
