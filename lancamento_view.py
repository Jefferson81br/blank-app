import streamlit as st
from datetime import date, timedelta
import database_utils as db

def linha_entrada(label, key):
    c1, c2, c3, c4 = st.columns([2, 2, 2, 1.5])
    c1.markdown(f"<div style='padding-top:10px'><b>{label}</b></div>", unsafe_allow_html=True)
    v_s = c2.number_input("R$", key=f"s_{key}", format="%.2f", step=0.01, label_visibility="collapsed")
    v_c = c3.number_input("R$", key=f"c_{key}", format="%.2f", step=0.01, label_visibility="collapsed")
    ace = v_c - v_s
    cor = "white" if ace == 0 else ("#ff4b4b" if ace < 0 else "#00ff00")
    c4.markdown(f"<div style='padding-top:10px; color:{cor}; font-weight:bold;'>R$ {ace:.2f}</div>", unsafe_allow_html=True)
    return v_s, v_c, ace

def linha_saida(label, key):
    c1, c2, c3, c4 = st.columns([2, 2, 2, 1.5])
    c1.markdown(f"<div style='padding-top:10px'><b>{label}</b></div>", unsafe_allow_html=True)
    c2.write("-")
    v_c = c3.number_input("R$", key=f"c_{key}", format="%.2f", step=0.01, label_visibility="collapsed")
    c4.write("")
    return v_c

def renderizar_tela(supabase, user):
    margem_esq, centro, coluna_avisos = st.columns([0.1, 2, 2])

    lojas_res = db.buscar_lojas(supabase)
    mapa_lojas = {l['nome']: l['id'] for l in lojas_res.data} if lojas_res.data else {}

    if user['funcao'] == 'admin':
        with centro:
            loja_nome_sel = st.selectbox("Unidade:", options=list(mapa_lojas.keys()))
            loja_id = mapa_lojas[loja_nome_sel]
    else:
        loja_id = user['unidade_id']
        if not loja_id: st.stop()

    with centro:
        st.title("📝 Lançamento Diário")
        
        data_limite = date.today() - timedelta(days=7)
        res_check = db.buscar_fechamento_multiplas_lojas(supabase, [loja_id], str(data_limite), str(date.today()))
        datas_feitas = [d['data_fechamento'] for d in res_check.data] if res_check.data else []

        cols_status = st.columns(7)
        for i in range(7):
            dia = date.today() - timedelta(days=i)
            with cols_status[6-i]:
                st.markdown(f"<div style='text-align:center; font-size:11px;'>{dia.strftime('%d/%m')}<br>{'🟢' if str(dia) in datas_feitas else '🔴'}</div>", unsafe_allow_html=True)

        data_sel = st.date_input("Data:", value=date.today(), max_value=date.today(), key="dt_p_principal")
        st.write("---")
        
        st.subheader("📥 Entradas")
        sc, cc, ac = linha_entrada("CARTÃO", "car")
        sr, cr, ar = linha_entrada("CREDIÁRIO", "cre")
        sd, cd, ad = linha_entrada("DINHEIRO", "din")
        sb, cb, ab = linha_entrada("BOLETO", "bol")
        si, ci, ai = linha_entrada("IFOOD", "ifo")
        sp, cp, ap = linha_entrada("PBM", "pbm")
        sx, cx, ax = linha_entrada("PIX", "pix")
        sv, cv, av = linha_entrada("VALE COMPRA", "vco")
        sf, cf, af = linha_entrada("FAPP", "fap")
        sl, cl, al = linha_entrada("VLINK", "vli")

        t_s_ent = sc+sr+sd+sb+si+sp+sx+sv+sf+sl
        t_c_ent = cc+cr+cd+cb+ci+cp+cx+cv+cf+cl
        t_a_ent = ac+ar+ad+ab+ai+ap+ax+av+af+al

        st.markdown(f"<div style='background-color:#1a1a1a; padding:10px; border-radius:5px; border:1px solid #333;'><b>SUBTOTAL ENTRADAS:</b> R$ {t_c_ent:,.2f}</div>", unsafe_allow_html=True)

        st.write("---")
        st.subheader("📤 Saídas")
        c_des = linha_saida("DESPESA", "des")
        c_vfu = linha_saida("VALE FUNC.", "vfu")
        c_dev = linha_saida("DEV. CARTÃO", "dev")
        c_out = linha_saida("OUTROS", "out")
        t_c_sai = c_des + c_vfu + c_dev + c_out

        saldo = t_c_ent - t_c_sai
        st.divider()
        st.metric("SALDO FINAL CAIXA", f"R$ {saldo:,.2f}", delta=f"Acerto: {t_a_ent:,.2f}")

    with coluna_avisos:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.info("### 📖 Instruções\n1. Confira os valores.\n2. Anexe prints.\n3. Justifique erros.")
        
        st.subheader("💬 Feedback do Financeiro")
        
        # AQUI FOI A CORREÇÃO DA LINHA 99
        try:
            fb_data = supabase.table("fechamentos").select("data_fechamento, replica_gestor").eq("loja_id", loja_id).neq("replica_gestor", "None").order("data_fechamento", desc=True).limit(2).execute()
            if fb_data.data:
                for f in fb_data.data:
                    with st.container(border=True):
                        st.caption(f"Ref. {f['data_fechamento']}")
                        st.write(f"**Gestor:** {f['replica_gestor']}")
            else:
                st.write("Sem feedback recente.")
        except:
            st.write("Não foi possível carregar feedbacks.")

        st.write("---")
        with st.form("f_final_envio_rev", clear_on_submit=True):
            imgs = st.file_uploader("Prints", accept_multiple_files=True)
            obs = st.text_area("Suas Observações")
            if st.form_submit_button("✅ SALVAR FECHAMENTO", use_container_width=True):
                dados = {
                    "loja_id": loja_id, "usuario_id": user['id'], "data_fechamento": str(data_sel),
                    "sis_cartao": sc, "conf_cartao": cc, "sis_crediario": sr, "conf_crediario": cr,
                    "sis_dinheiro": sd, "conf_dinheiro": cd, "sis_boleto": sb, "conf_boleto": cb,
                    "sis_ifood": si, "conf_ifood": ci, "sis_pbm": sp, "conf_pbm": cp, 
                    "sis_pix": sx, "conf_pix": cx, "sis_vale_compra": sv, "conf_vale_compra": cv, 
                    "sis_fapp": sf, "conf_fapp": cf, "sis_vlink": sl, "conf_vlink": cl, 
                    "conf_despesa": c_des, "conf_vale_func": c_vfu, "conf_dev_cartao": c_dev, "conf_outros": c_out, "observacoes": obs
                }
                ok, res = db.salvar_fechamento(supabase, dados)
                if ok:
                    st.success("Salvo!"); st.rerun()
