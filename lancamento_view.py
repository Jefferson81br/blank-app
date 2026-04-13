import streamlit as st
from datetime import date, timedelta
import database_utils as db

def renderizar_tela(supabase, user):
    st.title("📝 Lançamento de Caixa Diário")
    
    lojas_res = db.buscar_lojas(supabase)
    mapa_lojas = {l['nome']: l['id'] for l in lojas_res.data} if lojas_res.data else {}

    if user['funcao'] == 'admin':
        loja_nome_sel = st.selectbox("Selecione a Unidade:", options=list(mapa_lojas.keys()))
        loja_id = mapa_lojas[loja_nome_sel]
    else:
        loja_id = user['unidade_id']
        if not loja_id: st.stop()

    # --- STATUS ---
    data_limite = date.today() - timedelta(days=7)
    res_check = db.buscar_fechamento_multiplas_lojas(supabase, [loja_id], str(data_limite), str(date.today()))
    datas_feitas = [d['data_fechamento'] for d in res_check.data] if res_check.data else []

    cols_status = st.columns(7)
    for i in range(7):
        dia = date.today() - timedelta(days=i)
        with cols_status[6-i]:
            status = "🟢" if str(dia) in datas_feitas else "🔴"
            st.markdown(f"<div style='text-align:center; font-size:12px;'>{dia.strftime('%d/%m')}<br>{status}</div>", unsafe_allow_html=True)

    data_sel = st.date_input("Data do Movimento", value=date.today(), max_value=date.today())
    st.write("---")
    
    # Cabeçalhos
    c1, c2, c3, c4 = st.columns([2, 2, 2, 1.5])
    c1.write("**DESCRIÇÃO**"); c2.write("**VALOR SISTEMA**"); c3.write("**CONFERÊNCIA**"); c4.write("**ACERTO**")

    def linha_entrada(label, key):
        col1, col2, col3, col4 = st.columns([2, 2, 2, 1.5])
        col1.markdown(f"<div style='padding-top:10px'><b>{label}</b></div>", unsafe_allow_html=True)
        v_s = col2.number_input("R$", key=f"s_{key}", format="%.2f", step=0.01, label_visibility="collapsed")
        v_c = col3.number_input("R$", key=f"c_{key}", format="%.2f", step=0.01, label_visibility="collapsed")
        ace = v_c - v_s
        cor = "white" if ace == 0 else ("#ff4b4b" if ace < 0 else "#00ff00")
        col4.markdown(f"<div style='padding-top:10px; color:{cor}; font-weight:bold;'>R$ {ace:.2f}</div>", unsafe_allow_html=True)
        return v_s, v_c, ace

    def linha_saida(label, key):
        col1, col2, col3, col4 = st.columns([2, 2, 2, 1.5])
        col1.markdown(f"<div style='padding-top:10px'><b>{label}</b></div>", unsafe_allow_html=True)
        col2.write("-")
        v_c = col3.number_input("R$", key=f"c_{key}", format="%.2f", step=0.01, label_visibility="collapsed")
        col4.write("")
        return v_c

    st.subheader("📥 Entradas")
    sc, cc, ac = linha_entrada("CARTÃO", "car")
    sr, cr, ar = linha_entrada("CREDIÁRIO", "cre")
    sd, cd, ad = linha_entrada("DINHEIRO", "din")
    sb, cb, ab = linha_entrada("BOLETO", "bol") # <-- NOVO CAMPO
    si, ci, ai = linha_entrada("IFOOD", "ifo")
    sp, cp, ap = linha_entrada("PBM", "pbm")
    sx, cx, ax = linha_entrada("PIX / TRANSF", "pix")
    sv, cv, av = linha_entrada("VALE COMPRA", "vco")
    sf, cf, af = linha_entrada("FARMÁCIAS APP", "fap")
    sl, cl, al = linha_entrada("VIDA LINK", "vli")

    # Cálculos atualizados com Boleto (sb, cb, ab)
    t_s_ent = sc+sr+sd+sb+si+sp+sx+sv+sf+sl
    t_c_ent = cc+cr+cd+cb+ci+cp+cx+cv+cf+cl
    t_a_ent = ac+ar+ad+ab+ai+ap+ax+av+af+al

    # Subtotal Entradas com Cores
    st.markdown("<div style='background-color: #1a1a1a; padding: 10px; border-radius: 5px; border: 1px solid #333;'>", unsafe_allow_html=True)
    st1, st2, st3, st4 = st.columns([2, 2, 2, 1.5])
    st1.write("**SUBTOTAL ENTRADAS**")
    st2.write(f"R$ {t_s_ent:,.2f}")
    st3.markdown(f"<span style='color:#00ff00; font-weight:bold;'>R$ {t_c_ent:,.2f}</span>", unsafe_allow_html=True)
    st4.markdown(f"<span style='color:#ff4b4b; font-weight:bold;'>R$ {t_a_ent:,.2f}</span>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.write("---")
    st.subheader("📤 Saídas")
    c_des = linha_saida("DESPESA", "des")
    c_vfu = linha_saida("VALE FUNC.", "vfu")
    c_dev = linha_saida("DEV. CARTÃO", "dev")
    c_out = linha_saida("OUTROS", "out")
    
    t_c_sai = c_des + c_vfu + c_dev + c_out

    # Total Saídas
    st.markdown("<div style='background-color: #1a1a1a; padding: 10px; border-radius: 5px; border: 1px solid #333;'>", unsafe_allow_html=True)
    ss1, ss2, ss3, ss4 = st.columns([2, 2, 2, 1.5])
    ss1.write("**TOTAL SAÍDAS**")
    ss2.write("-")
    ss3.markdown(f"<span style='color:#00ff00; font-weight:bold;'>R$ {t_c_sai:,.2f}</span>", unsafe_allow_html=True)
    ss4.write("-")
    st.markdown("</div>", unsafe_allow_html=True)

    st.divider()
    saldo = t_c_ent - t_c_sai
    
    st.markdown("### 🏁 Resumo do Fechamento")
    res1, res2, res3 = st.columns(3)
    res1.metric("Entradas (Conf.)", f"R$ {t_c_ent:,.2f}")
    res2.metric("Total Saídas", f"R$ {t_c_sai:,.2f}")
    
    st.markdown(f"""
        <div style="background-color:#1a1a1a; padding:15px; border-radius:10px; border-left: 5px solid #00ff00;">
            <p style="margin:0; font-size:14px; color:#aaa;">SALDO FINAL CAIXA</p>
            <h2 style="margin:0; color:#00ff00;">R$ {saldo:,.2f}</h2>
            <p style="margin:0; font-size:12px; color:#888;">Acerto de Entradas: R$ {t_a_ent:,.2f}</p>
        </div>
        <br>
    """, unsafe_allow_html=True)

    with st.form("f_final_new", clear_on_submit=True):
        imgs = st.file_uploader("Prints", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'])
        obs = st.text_area("Obs")
        if st.form_submit_button("✅ SALVAR FECHAMENTO", use_container_width=True):
            dados = {
                "loja_id": loja_id, "usuario_id": user['id'], "data_fechamento": str(data_sel),
                "sis_cartao": sc, "conf_cartao": cc, "sis_crediario": sr, "conf_crediario": cr,
                "sis_dinheiro": sd, "conf_dinheiro": cd, 
                "sis_boleto": sb, "conf_boleto": cb, # <-- SALVANDO BOLETO NO BANCO
                "sis_ifood": si, "conf_ifood": ci, "sis_pbm": sp, "conf_pbm": cp, 
                "sis_pix": sx, "conf_pix": cx, "sis_vale_compra": sv, "conf_vale_compra": cv, 
                "sis_fapp": sf, "conf_fapp": cf, "sis_vlink": sl, "conf_vlink": cl, 
                "conf_despesa": c_des, "conf_vale_func": c_vfu, "conf_dev_cartao": c_dev, 
                "conf_outros": c_out, "observacoes": obs
            }
            ok, res = db.salvar_fechamento(supabase, dados)
            if ok:
                if imgs:
                    urls = [db.fazer_upload_print(supabase, f, f"loja_{loja_id}/{data_sel}/p_{i}.jpg") for i, f in enumerate(imgs)]
                    supabase.table("fechamentos").update({"urls_prints": [u for u in urls if u]}).eq("id", res.data[0]['id']).execute()
                st.success("Salvo!"); st.rerun()
