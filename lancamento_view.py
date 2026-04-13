import streamlit as st
from datetime import date, timedelta
import database_utils as db

def renderizar_tela(supabase, user):
    st.title("📝 Lançamento de Caixa Diário")
    
    # --- LOGICA DE SELEÇÃO DE LOJA (ADMIN VS GERENTE) ---
    lojas_res = db.buscar_lojas(supabase)
    mapa_lojas = {l['nome']: l['id'] for l in lojas_res.data} if lojas_res.data else {}

    if user['funcao'] == 'admin':
        loja_nome_sel = st.selectbox("Selecione a Unidade para o Lançamento:", options=list(mapa_lojas.keys()))
        loja_id = mapa_lojas[loja_nome_sel]
    else:
        loja_id = user['unidade_id']
        if not loja_id:
            st.error("Erro: Usuário sem unidade vinculada.")
            st.stop()
        nome_loja = next((nome for nome, id in mapa_lojas.items() if id == loja_id), "Minha Unidade")
        st.info(f"Unidade: {nome_loja}")

    # --- STATUS DOS ÚLTIMOS 7 DIAS ---
    data_limite = date.today() - timedelta(days=7)
    res_check = db.buscar_fechamento_multiplas_lojas(supabase, [loja_id], str(data_limite), str(date.today()))
    datas_feitas = [d['data_fechamento'] for d in res_check.data] if res_check.data else []

    cols_status = st.columns(7)
    for i in range(7):
        dia = date.today() - timedelta(days=i)
        dia_s = str(dia)
        with cols_status[6-i]:
            status = "🟢" if dia_s in datas_feitas else "🔴"
            st.markdown(f"<div style='text-align:center; font-size:12px;'>{dia.strftime('%d/%m')}<br>{status}</div>", unsafe_allow_html=True)

    data_sel = st.date_input("Data do Movimento", value=date.today(), max_value=date.today())
    if str(data_sel) in datas_feitas:
        st.warning("⚠️ Já existe um lançamento para este dia.")

    st.write("---")
    
    # Cabeçalhos das Colunas
    c1, c2, c3, c4 = st.columns([2, 2, 2, 1.5])
    c1.write("**DESCRIÇÃO**"); c2.write("**VALOR DO SISTEMA**"); c3.write("**VALOR DE CONFERÊNCIA**"); c4.write("**ACERTO**")

    # --- FUNÇÃO PARA LINHAS DE ENTRADA ---
    def linha_entrada(label, key):
        col1, col2, col3, col4 = st.columns([2, 2, 2, 1.5])
        col1.markdown(f"<div style='padding-top:10px'><b>{label}</b></div>", unsafe_allow_html=True)
        v_s = col2.number_input("R$", key=f"s_{key}", format="%.2f", step=0.01, label_visibility="collapsed")
        v_c = col3.number_input("R$", key=f"c_{key}", format="%.2f", step=0.01, label_visibility="collapsed")
        ace = v_c - v_s
        cor = "white" if ace == 0 else ("#ff4b4b" if ace < 0 else "#00ff00")
        col4.markdown(f"<div style='padding-top:10px; color:{cor}; font-weight:bold;'>R$ {ace:.2f}</div>", unsafe_allow_html=True)
        return v_s, v_c, ace

    # --- FUNÇÃO PARA LINHAS DE SAÍDA (SEM ACERTO NA TELA) ---
    def linha_saida(label, key):
        col1, col2, col3, col4 = st.columns([2, 2, 2, 1.5])
        col1.markdown(f"<div style='padding-top:10px'><b>{label}</b></div>", unsafe_allow_html=True)
        # Sistema travado em 0
        col2.number_input("R$", key=f"s_{key}", value=0.0, disabled=True, label_visibility="collapsed")
        v_c = col3.number_input("R$", key=f"c_{key}", format="%.2f", step=0.01, label_visibility="collapsed")
        # Coluna de acerto vazia para saídas
        col4.write("")
        return v_c

    # --- GRUPO: ENTRADAS ---
    st.subheader("📥 Entradas")
    sc, cc, ac = linha_entrada("CARTÃO", "car")
    sr, cr, ar = linha_entrada("CREDIÁRIO", "cre")
    sd, cd, ad = linha_entrada("DINHEIRO", "din")
    si, ci, ai = linha_entrada("IFOOD", "ifo")
    sp, cp, ap = linha_entrada("PBM", "pbm")
    sx, cx, ax = linha_entrada("PIX / TRANSF", "pix")
    sv, cv, av = linha_entrada("VALE COMPRA", "vco")
    sf, cf, af = linha_entrada("FARMÁCIAS APP", "fap")
    sl, cl, al = linha_entrada("VIDA LINK", "vli")

    # TOTALIZADOR ENTRADAS
    t_sis_ent = sc+sr+sd+si+sp+sx+sv+sf+sl
    t_conf_ent = cc+cr+cd+ci+cp+cx+cv+cf+cl
    t_ace_ent = ac+ar+ad+ai+ap+ax+av+af+al

    st.markdown("""<style> .total-box { background-color: #1a1a1a; padding: 10px; border-radius: 5px; border: 1px solid #333; } </style>""", unsafe_allow_html=True)
    
    with st.container():
        st.markdown("<div class='total-box'>", unsafe_allow_html=True)
        ct1, ct2, ct3, ct4 = st.columns([2, 2, 2, 1.5])
        ct1.write("**SUBTOTAL ENTRADAS**")
        ct2.write(f"**R$ {t_sis_ent:,.2f}**")
        ct3.write(f"**R$ {t_conf_ent:,.2f}**")
        cor_ace = "#ff4b4b" if t_ace_ent < 0 else ("#00ff00" if t_ace_ent > 0 else "white")
        ct4.markdown(f"<span style='color:{cor_ace}; font-weight:bold;'>R$ {t_ace_ent:,.2f}</span>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.write("---")

    # --- GRUPO: SAÍDAS ---
    st.subheader("📤 Saídas")
    c_des = linha_saida("DESPESA", "des")
    c_vfu = linha_saida("VALE FUNC.", "vfu")
    c_dev = linha_saida("DEV. CARTÃO", "dev")
    c_out = linha_saida("OUTROS", "out")

    # TOTALIZADOR SAÍDAS
    t_conf_sai = c_des + c_vfu + c_dev + c_out

    with st.container():
        st.markdown("<div class='total-box'>", unsafe_allow_html=True)
        cs1, cs2, cs3, cs4 = st.columns([2, 2, 2, 1.5])
        cs1.write("**TOTAL SAÍDAS**")
        cs2.write("-")
        cs3.write(f"**R$ {t_conf_sai:,.2f}**")
        cs4.write("")
        st.markdown("</div>", unsafe_allow_html=True)

    # --- TOTALIZADOR GERAL ---
    st.write("---")
    saldo_final = t_conf_ent - t_conf_sai
    
    st.markdown("### 🏁 Resumo do Fechamento")
    res1, res2, res3 = st.columns(3)
    res1.metric("Total Entradas (Conf.)", f"R$ {t_conf_ent:,.2f}")
    res2.metric("Total Saídas", f"R$ {t_conf_sai:,.2f}", delta_color="inverse")
    res3.metric("SALDO FINAL CAIXA", f"R$ {saldo_final:,.2f}", delta=f"Acerto: {t_ace_ent:,.2f}")

    # --- FORMULÁRIO FINAL ---
    with st.form("f_final_caixa", clear_on_submit=True):
        imgs = st.file_uploader("Anexar Prints do Fechamento", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'])
        obs = st.text_area("Observações do Dia")
        
        if st.form_submit_button("✅ SALVAR FECHAMENTO NO BANCO", use_container_width=True):
            dados = {
                "loja_id": loja_id, "usuario_id": user['id'], "data_fechamento": str(data_sel),
                "sis_cartao": sc, "conf_cartao": cc, "sis_crediario": sr, "conf_crediario": cr,
                "sis_dinheiro": sd, "conf_dinheiro": cd, "sis_ifood": si, "conf_ifood": ci,
                "sis_pbm": sp, "conf_pbm": cp, "sis_pix": sx, "conf_pix": cx,
                "sis_vale_compra": sv, "conf_vale_compra": cv, "sis_fapp": sf, "conf_fapp": cf,
                "sis_vlink": sl, "conf_vlink": cl, "conf_despesa": c_des, "conf_vale_func": c_vfu,
                "conf_dev_cartao": c_dev, "conf_outros": c_out, "observacoes": obs
            }
            ok, res = db.salvar_fechamento(supabase, dados)
            if ok:
                if imgs:
                    urls = [db.fazer_upload_print(supabase, f, f"loja_{loja_id}/{data_sel}/p_{i}.jpg") for i, f in enumerate(imgs)]
                    supabase.table("fechamentos").update({"urls_prints": [u for u in urls if u]}).eq("id", res.data[0]['id']).execute()
                st.success("✅ Lançamento realizado com sucesso!")
                st.balloons()
                st.rerun()
            else:
                st.error(f"Erro ao salvar: {res}")
