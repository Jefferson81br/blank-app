import streamlit as st
from datetime import date, timedelta
import database_utils as db

def renderizar_tela(supabase, user):
    st.title("📝 Lançamento de Caixa Diário")
    
    # --- LÓGICA DE SELEÇÃO DE LOJA PARA ADMIN ---
    lojas_res = db.buscar_lojas(supabase)
    mapa_lojas = {l['nome']: l['id'] for l in lojas_res.data} if lojas_res.data else {}

    if user['funcao'] == 'admin':
        # Se for admin, permite escolher a loja antes de lançar
        loja_nome_sel = st.selectbox("Selecione a Unidade para o Lançamento:", options=list(mapa_lojas.keys()))
        loja_id = mapa_lojas[loja_nome_sel]
    else:
        # Se for gerente, usa a loja vinculada ao perfil
        loja_id = user['unidade_id']
        if not loja_id:
            st.error("Erro: Usuário sem unidade vinculada no cadastro.")
            st.stop()
        nome_loja = next((nome for nome, id in mapa_lojas.items() if id == loja_id), "Minha Unidade")
        st.info(f"Unidade: {nome_loja}")

    # --- STATUS DOS ÚLTIMOS 7 DIAS ---
    st.subheader("📅 Status de Lançamentos")
    data_limite = date.today() - timedelta(days=7)
    res_check = db.buscar_fechamento_multiplas_lojas(supabase, [loja_id], str(data_limite), str(date.today()))
    datas_feitas = [d['data_fechamento'] for d in res_check.data] if res_check.data else []

    cols = st.columns(7)
    for i in range(7):
        dia = date.today() - timedelta(days=i)
        dia_s = str(dia)
        with cols[6-i]:
            status = "🟢" if dia_s in datas_feitas else "🔴"
            st.markdown(f"<div style='text-align:center; font-size:12px;'>{dia.strftime('%d/%m')}<br>{status}</div>", unsafe_allow_html=True)

    data_sel = st.date_input("Data do Movimento", value=date.today(), max_value=date.today(), key="data_gerente")
    
    if str(data_sel) in datas_feitas:
        st.warning("⚠️ Já existe um lançamento para este dia. Use a tela de Auditoria para correções.")

    st.write("---")
    
    # Cabeçalhos das Colunas
    c1, c2, c3, c4 = st.columns([2, 2, 2, 1.5])
    c1.write("**DESCRIÇÃO**"); c2.write("**SISTEMA**"); c3.write("**CONFERÊNCIA**"); c4.write("**ACERTO**")

    def linha_f(label, key, bloqueia=False):
        col1, col2, col3, col4 = st.columns([2, 2, 2, 1.5])
        col1.markdown(f"<div style='padding-top:10px'><b>{label}</b></div>", unsafe_allow_html=True)
        v_s = col2.number_input("R$", key=f"s_{key}", format="%.2f", step=0.01, label_visibility="collapsed", disabled=bloqueia)
        v_c = col3.number_input("R$", key=f"c_{key}", format="%.2f", step=0.01, label_visibility="collapsed")
        ace = v_c - v_s
        cor = "white" if ace == 0 else ("#ff4b4b" if ace < 0 else "#00ff00")
        col4.markdown(f"<div style='padding-top:10px; color:{cor}; font-weight:bold;'>R$ {ace:.2f}</div>", unsafe_allow_html=True)
        return v_s, v_c, ace

    st.subheader("📥 Entradas")
    sc, cc, ac = linha_f("CARTÃO", "car")
    sr, cr, ar = linha_f("CREDIÁRIO", "cre")
    sd, cd, ad = linha_f("DINHEIRO", "din")
    si, ci, ai = linha_f("IFOOD", "ifo")
    sp, cp, ap = linha_f("PBM", "pbm")
    sx, cx, ax = linha_f("PIX / TRANSF", "pix")
    sv, cv, av = linha_f("VALE COMPRA", "vco")
    sf, cf, af = linha_f("FARMÁCIAS APP", "fap")
    sl, cl, al = linha_f("VIDA LINK", "vli")

    st.subheader("📤 Saídas")
    _, cdes, ades = linha_f("DESPESA", "des", True)
    _, cvfu, avfu = linha_f("VALE FUNC.", "vfu", True)
    _, cdev, adev = linha_f("DEV. CARTÃO", "dev", True)
    _, cout, aout = linha_f("OUTROS", "out", True)

    with st.form("f_gerente", clear_on_submit=True):
        imgs = st.file_uploader("Prints", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'])
        obs = st.text_area("Observações")
        if st.form_submit_button("✅ ENVIAR FECHAMENTO", use_container_width=True):
            if str(data_sel) in datas_feitas:
                st.error("Erro: Já existe um lançamento para esta data. Use a Auditoria para alterar.")
            else:
                dados = {
                    "loja_id": loja_id, "usuario_id": user['id'], "data_fechamento": str(data_sel),
                    "sis_cartao": sc, "conf_cartao": cc, "sis_crediario": sr, "conf_crediario": cr,
                    "sis_dinheiro": sd, "conf_dinheiro": cd, "sis_ifood": si, "conf_ifood": ci,
                    "sis_pbm": sp, "conf_pbm": cp, "sis_pix": sx, "conf_pix": cx,
                    "sis_vale_compra": sv, "conf_vale_compra": cv, "sis_fapp": sf, "conf_fapp": cf,
                    "sis_vlink": sl, "conf_vlink": cl, "conf_despesa": cdes, "conf_vale_func": cvfu,
                    "conf_dev_cartao": cdev, "conf_outros": cout, "observacoes": obs
                }
                ok, res = db.salvar_fechamento(supabase, dados)
                if ok:
                    if imgs:
                        urls = [db.fazer_upload_print(supabase, f, f"loja_{loja_id}/{data_sel}/p_{i}.jpg") for i, f in enumerate(imgs)]
                        supabase.table("fechamentos").update({"urls_prints": [u for u in urls if u]}).eq("id", res.data[0]['id']).execute()
                    st.success("✅ Lançamento realizado com sucesso!")
                    st.rerun()
                else: st.error(f"Erro ao salvar: {res}")
