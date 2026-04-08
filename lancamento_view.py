import streamlit as st
from datetime import date
import database_utils as db

def renderizar_tela(supabase, user):
    st.title("📝 Fechamento de Caixa Diário")
    
    loja_id = user['unidade_id']
    if not loja_id and user['funcao'] != 'admin':
        st.error("Usuário sem loja vinculada.")
        st.stop()

    data_sel = st.date_input("Data do Movimento", value=date.today(), max_value=date.today())
    
    def linha(label, key):
        c_desc, c_sis, c_conf, c_ace = st.columns([2, 2, 2, 1.5])
        c_desc.markdown(f"<div style='padding-top:10px'><b>{label}</b></div>", unsafe_allow_html=True)
        v_s = c_sis.number_input("R$", key=f"s_{key}", format="%.2f", step=0.01, label_visibility="collapsed")
        v_c = c_conf.number_input("R$", key=f"c_{key}", format="%.2f", step=0.01, label_visibility="collapsed")
        ace = v_c - v_s
        cor = "white" if ace == 0 else ("#ff4b4b" if ace < 0 else "#00ff00")
        c_ace.markdown(f"<div style='padding-top:10px; color:{cor}; font-weight:bold;'>R$ {ace:.2f}</div>", unsafe_allow_html=True)
        return v_s, v_c

    s_car, c_car = linha("CARTÃO", "car")
    s_cre, c_cre = linha("CREDIÁRIO", "cre")
    s_din, c_din = linha("DINHEIRO", "din")
    s_ifo, c_ifo = linha("IFOOD", "ifo")
    s_pix, c_pix = linha("PIX/TRANSF", "pix")
    
    _, _, cl_l, cl_v = st.columns([2, 2, 2, 1.5])
    cl_l.write("**DESPESA (-)**")
    v_desp = cl_v.number_input("R$", key="dv", format="%.2f", step=0.01, label_visibility="collapsed")

    with st.form("f_final", clear_on_submit=True):
        imgs = st.file_uploader("Prints", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'])
        obs = st.text_area("Obs")
        if st.form_submit_button("✅ SALVAR NO BANCO", use_container_width=True):
            with st.spinner("Validando e salvando..."):
                d_ins = {
                    "loja_id": loja_id, "usuario_id": user['id'], "data_fechamento": str(data_sel),
                    "sis_cartao": s_car, "conf_cartao": c_car, "sis_crediario": s_cre, "conf_crediario": c_cre,
                    "sis_dinheiro": s_din, "conf_dinheiro": c_din, "sis_ifood": s_ifo, "conf_ifood": c_ifo,
                    "sis_pix": s_pix, "conf_pix": c_pix, "despesa": v_desp, "observacoes": obs, "urls_prints": []
                }
                ok, res_m = db.salvar_fechamento(supabase, d_ins)
                if ok:
                    urls = [db.fazer_upload_print(supabase, f, f"loja_{loja_id}/{data_sel}/p_{i}.jpg") for i, f in enumerate(imgs)]
                    db.supabase.table("fechamentos").update({"urls_prints": [u for u in urls if u]}).eq("id", res_m.data[0]['id']).execute()
                    st.success("✅ Salvo com sucesso!")
                    st.balloons()
                else:
                    st.error(f"❌ Erro: {res_m}")
