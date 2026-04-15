import streamlit as st
from datetime import date, timedelta
import database_utils as db
from streamlit_paste_button import paste_image_button
import io
from PIL import Image

# --- FUNÇÕES DE INTERFACE ---
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
    margem_esq, centro, coluna_avisos = st.columns([0.2, 2, 3])

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
                status = "🟢" if str(dia) in datas_feitas else "🔴"
                st.markdown(f"<div style='text-align:center; font-size:11px;'>{dia.strftime('%d/%m')}<br>{status}</div>", unsafe_allow_html=True)

        data_sel = st.date_input("Data do Movimento", value=date.today(), max_value=date.today(), key="dt_mov_fix_v2")
        
        ja_existe = str(data_sel) in datas_feitas
        if ja_existe:
            st.error(f"❌ ERRO: Já existe um lançamento para este dia.")
        
        st.write("---")
        
        # --- ENTRADAS ---
        st.subheader("📥 Entradas")
        sc, cc, ac = linha_entrada("CARTÃO", "car")
        sr, cr, ar = linha_entrada("CREDIÁRIO", "cre")
        sd, cd, ad = linha_entrada("DINHEIRO", "din")
        sb, cb, ab = linha_entrada("BOLETO", "bol")
        si, ci, ai = linha_entrada("IFOOD", "ifo")
        sp, cp, ap = linha_entrada("PBM", "pbm")
        sx, cx, ax = linha_entrada("PIX / TRANSF", "pix")
        sv, cv, av = linha_entrada("VALE COMPRA", "vco")
        sf, cf, af = linha_entrada("FAPP", "fap")
        sl, cl, al = linha_entrada("VLINK", "vli")

        t_s_ent = sc+sr+sd+sb+si+sp+sx+sv+sf+sl
        t_c_ent = cc+cr+cd+cb+ci+cp+cx+cv+cf+cl
        t_a_ent = ac+ar+ad+ab+ai+ap+ax+av+af+al

        st.write("")
        ct1, ct2, ct3, ct4 = st.columns([2, 2, 2, 1.5])
        ct1.write("**TOTAIS:**")
        ct2.write(f"**R$ {t_s_ent:,.2f}**")
        ct3.markdown(f"<span style='color:#00ff00; font-weight:bold;'>R$ {t_c_ent:,.2f}</span>", unsafe_allow_html=True)
        cor_t_ace = "#ff4b4b" if t_a_ent < 0 else ("#00ff00" if t_a_ent > 0 else "white")
        ct4.markdown(f"<span style='color:{cor_t_ace}; font-weight:bold;'>R$ {t_a_ent:,.2f}</span>", unsafe_allow_html=True)

        st.write("---")
        
        # --- SAÍDAS ---
        st.subheader("📤 Saídas (Justificativa)")
        c_des = linha_saida("DESPESA", "des")
        c_vfu = linha_saida("VALE FUNC.", "vfu")
        c_dev = linha_saida("DEV. CARTÃO", "dev")
        c_out = linha_saida("OUTROS", "out")
        
        t_c_sai = c_des + c_vfu + c_dev + c_out
        divergencia_final = (t_c_ent + t_c_sai) - t_s_ent
        
        cor_div = "#00ff00" if -0.01 <= divergencia_final <= 0.01 else ("#ff4b4b" if divergencia_final < 0 else "#33ccff")
        label_div = "Caixa Ajustado (OK)" if -0.01 <= divergencia_final <= 0.01 else ("Divergência: FALTA" if divergencia_final < 0 else "Divergência: SOBRA")

        # CARD FINAL
        st.markdown(f"""
            <div style="background-color:#1a1a1a; padding:25px; border-radius:15px; border-left: 8px solid #00ff00;">
                <p style="margin:0; font-size:18px; color:#00ff00; font-weight:bold;">CAIXA TOTAL DO DIA (VALOR CONFERIDO)</p>
                <h1 style="margin:5px 0; color:white; font-size:52px; font-weight:900;">R$ {t_c_ent:,.2f}</h1>
                <p style="margin:0; font-size:22px; color:{cor_div}; font-weight:bold; text-transform: uppercase;">
                    Status: {label_div} (R$ {divergencia_final:,.2f})
                </p>
            </div>
            <br>
        """, unsafe_allow_html=True)

    with coluna_avisos:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        
        # --- ÁREA DE PRINTS (CTRL+V) ---
        st.subheader("🖼️ Galeria de Prints")
        
        if 'lista_prints' not in st.session_state:
            st.session_state.lista_prints = []

        col_p1, col_p2 = st.columns([1,1])
        with col_p1:
            # Simplificando a chamada para evitar o TypeError
            pasted_img = paste_image_button(label="📋 COLAR PRINT (CTRL+V)")
        with col_p2:
            if st.button("🗑️ Limpar Galeria"):
                st.session_state.lista_prints = []
                st.rerun()

        if pasted_img and pasted_img.image_data is not None:
            # O componente retorna uma imagem PIL. Convertemos para bytes para comparar e guardar.
            img = pasted_img.image_data
            if img not in st.session_state.lista_prints:
                st.session_state.lista_prints.append(img)
                st.toast("Print adicionado!", icon="✅")

        if st.session_state.lista_prints:
            cols = st.columns(3)
            for i, img_data in enumerate(st.session_state.lista_prints):
                with cols[i % 3]:
                    st.image(img_data, use_container_width=True)

        st.write("---")
        
        if not ja_existe:
            with st.form("f_final_caixa_vFinal", clear_on_submit=True):
                imgs_file = st.file_uploader("Ou anexe arquivos:", accept_multiple_files=True)
                obs = st.text_area("Observações")
                
                if st.form_submit_button("✅ SALVAR FECHAMENTO", use_container_width=True):
                    dados = {
                        "loja_id": loja_id, "usuario_id": user['id'], "data_fechamento": str(data_sel),
                        "sis_cartao": sc, "conf_cartao": cc, "sis_crediario": sr, "conf_crediario": cr,
                        "sis_dinheiro": sd, "conf_dinheiro": cd, "sis_boleto": sb, "conf_boleto": cb,
                        "sis_ifood": si, "conf_ifood": ci, "sis_pbm": sp, "conf_pbm": cp, 
                        "sis_pix": sx, "conf_pix": cx, "sis_vale_compra": sv, "conf_vale_compra": cv, 
                        "sis_fapp": sf, "conf_fapp": cf, "sis_vlink": sl, "conf_vlink": cl, 
                        "conf_despesa": c_des, "conf_vale_func": c_vfu, "conf_dev_cartao": c_dev, 
                        "conf_outros": c_out, "observacoes": obs, "status_auditoria": "Pendente"
                    }
                    
                    ok, res = db.salvar_fechamento(supabase, dados)
                    if ok:
                        # Upload dos prints colados
                        for i, img in enumerate(st.session_state.lista_prints):
                            buf = io.BytesIO()
                            img.save(buf, format="JPEG", quality=80)
                            db.fazer_upload_print(supabase, buf.getvalue(), f"loja_{loja_id}/{data_sel}/v_{i}.jpg")
                        
                        # Upload dos arquivos
                        if imgs_file:
                            for i, f in enumerate(imgs_file):
                                db.fazer_upload_print(supabase, f, f"loja_{loja_id}/{data_sel}/f_{i}.jpg")
                        
                        st.session_state.lista_prints = []
                        st.success("✅ Enviado!"); st.rerun()
