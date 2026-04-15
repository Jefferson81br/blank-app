import streamlit as st
from datetime import date, timedelta
import database_utils as db

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
        
        # STATUS DOS 7 DIAS
        data_limite = date.today() - timedelta(days=7)
        res_check = db.buscar_fechamento_multiplas_lojas(supabase, [loja_id], str(data_limite), str(date.today()))
        datas_feitas = [d['data_fechamento'] for d in res_check.data] if res_check.data else []

        cols_status = st.columns(7)
        for i in range(7):
            dia = date.today() - timedelta(days=i)
            with cols_status[6-i]:
                status = "🟢" if str(dia) in datas_feitas else "🔴"
                st.markdown(f"<div style='text-align:center; font-size:11px;'>{dia.strftime('%d/%m')}<br>{status}</div>", unsafe_allow_html=True)

        data_sel = st.date_input("Data do Movimento", value=date.today(), max_value=date.today(), key="dt_mov_revision")
        
        ja_existe = str(data_sel) in datas_feitas
        if ja_existe:
            st.error(f"❌ ERRO: Já existe um lançamento para o dia {data_sel.strftime('%d/%m/%Y')}.")
        
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

        # --- TOTAIS ALINHADOS ABAIXO DAS COLUNAS ---
        st.markdown("---")
        col_t1, col_t2, col_t3, col_t4 = st.columns([2, 2, 2, 1.5])
        col_t1.markdown("**TOTAIS GERAIS:**")
        col_t2.markdown(f"**R$ {t_s_ent:,.2f}**")
        col_t3.markdown(f"<span style='color:#00ff00; font-weight:bold; font-size:18px;'>R$ {t_c_ent:,.2f}</span>", unsafe_allow_html=True)
        
        cor_final_ace = "#ff4b4b" if t_a_ent < 0 else ("#00ff00" if t_a_ent > 0 else "white")
        col_t4.markdown(f"<span style='color:{cor_final_ace}; font-weight:bold; font-size:18px;'>R$ {t_a_ent:,.2f}</span>", unsafe_allow_html=True)

        st.markdown(f"""
            <div style='background-color: #1a1a1a; padding: 12px; border-radius: 8px; border: 1px solid #444; margin-top:15px; border-left: 5px solid #555;'>
                <small style='color:#bbb; font-weight:bold; text-transform: uppercase;'>Resumo das Vendas do Sistema:</small><br>
                <span style='font-size:15px;'>Sistema: R$ {t_s_ent:,.2f} | <span style='color:#00ff00;'>Conf.: R$ {t_c_ent:,.2f}</span> | <span style='color:#ff4b4b;'>Diferença: R$ {t_a_ent:,.2f}</span></span>
            </div>
        """, unsafe_allow_html=True)

        st.write("---")
        
        # --- SAÍDAS ---
        st.subheader("📤 Saídas (Justificativa da Diferença)")
        c_des = linha_saida("DESPESA", "des")
        c_vfu = linha_saida("VALE FUNC.", "vfu")
        c_dev = linha_saida("DEV. CARTÃO", "dev")
        c_out = linha_saida("OUTROS", "out")
        
        t_c_sai = c_des + c_vfu + c_dev + c_out

        divergencia_final = (t_c_ent + t_c_sai) - t_s_ent
        
        if -0.01 <= divergencia_final <= 0.01:
            cor_div = "#00ff00"; label_div = "Caixa Ajustado (OK)"
        elif divergencia_final < 0:
            cor_div = "#ff4b4b"; label_div = "Divergência: FALTA"
        else:
            cor_div = "#33ccff"; label_div = "Divergência: SOBRA"

        st.markdown(f"""
            <div style='background-color: #1a1a1a; padding: 10px; border-radius: 5px; border: 1px solid #333;'>
                <table style='width:100%; border:none;'>
                    <tr>
                        <td style='width:30%'><b>TOTAL JUSTIFICADO</b></td>
                        <td style='width:25%'>-</td>
                        <td style='width:25%; color:#00ff00; font-weight:bold;'>R$ {t_c_sai:,.2f}</td>
                        <td style='width:20%; color:{cor_div}; font-weight:bold;'>{label_div}: R$ {divergencia_final:,.2f}</td>
                    </tr>
                </table>
            </div>
        """, unsafe_allow_html=True)

        st.divider()
        
        # --- CARD FINAL: CAIXA TOTAL DO DIA ---
        st.markdown(f"""
            <div style="background-color:#141414; padding:25px; border-radius:15px; border-left: 8px solid #00ff00; box-shadow: 2px 2px 10px rgba(0,0,0,0.5);">
                <p style="margin:0; font-size:18px; color:#00ff00; font-weight:bold; letter-spacing: 1px;">CAIXA TOTAL DO DIA (VALOR CONFERIDO)</p>
                <h1 style="margin:5px 0; color:white; font-size:52px; font-weight:900;">R$ {t_c_ent:,.2f}</h1>
                <hr style="border: 0; border-top: 1px solid #333; margin: 15px 0;">
                <p style="margin:0; font-size:22px; color:{cor_div}; font-weight:bold; text-transform: uppercase;">
                    Status da Auditoria: {label_div} (R$ {divergencia_final:,.2f})
                </p>
            </div>
            <br>
        """, unsafe_allow_html=True)

    with coluna_avisos:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.info("### 📖 Instruções\nO valor **Conferido** deve ser o que sobrou no caixa.\nAs **Saídas** justificam o que foi pago com esse dinheiro.")
        
        st.subheader("💬 Feedback do Financeiro")
        try:
            fb = supabase.table("fechamentos").select("data_fechamento, replica_gestor").eq("loja_id", loja_id).neq("replica_gestor", "None").order("data_fechamento", desc=True).limit(2).execute()
            if fb.data:
                for f in fb.data:
                    with st.container(border=True):
                        st.caption(f"Ref. {f['data_fechamento']}")
                        st.write(f"**Gestor:** {f['replica_gestor']}")
        except:
            pass

        st.write("---")
        
        if not ja_existe:
            with st.form("f_final_vFinal_v2", clear_on_submit=True):
                imgs = st.file_uploader("Prints do Fechamento", accept_multiple_files=True)
                obs = st.text_area("Observações do Gerente")
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
                        if imgs:
                            for i, f in enumerate(imgs):
                                db.fazer_upload_print(supabase, f, f"loja_{loja_id}/{data_sel}/p_{i}.jpg")
                        st.success("✅ Fechamento gravado!"); st.rerun()
