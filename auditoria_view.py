import streamlit as st
import database_utils as db

def renderizar_tela(supabase, user):
    st.title("⚖️ Auditoria e Correção")
    
    lojas = db.buscar_lojas(supabase)
    mapa_lojas = {l['nome']: l['id'] for l in lojas.data} if lojas.data else {}
    
    c1, c2 = st.columns(2)
    loja_sel = c1.selectbox("Loja:", options=list(mapa_lojas.keys()))
    data_sel = c2.date_input("Data:", key="data_auditoria")
    
    # Busca dados no banco
    res = supabase.table("fechamentos").select("*").eq("loja_id", mapa_lojas[loja_sel]).eq("data_fechamento", str(data_sel)).execute()
    
    if not res.data:
        st.info("Nenhum dado encontrado para esta data nesta loja.")
        st.stop()
    
    d = res.data[0]
    st.warning(f"Editando dados de: {loja_sel} - {data_sel}")

    with st.form("f_auditoria"):
        # Aqui usamos o valor vindo do banco 'd' como value inicial
        def campo_auditoria(label, key_db, bloqueia=False):
            col1, col2, col3 = st.columns([2, 2, 2])
            col1.write(f"**{label}**")
            v_s = col2.number_input("Sistema", value=float(d.get(f'sis_{key_db}', 0)), key=f"as_{key_db}", disabled=bloqueia)
            v_c = col3.number_input("Conferência", value=float(d.get(f'conf_{key_db}', 0)), key=f"ac_{key_db}")
            return v_s, v_c

        sc, cc = campo_auditoria("CARTÃO", "cartao")
        sr, cr = campo_auditoria("CREDIÁRIO", "crediario")
        sd, cd = campo_auditoria("DINHEIRO", "dinheiro")
        si, ci = campo_auditoria("IFOOD", "ifood")
        sp, cp = campo_auditoria("PBM", "pbm")
        sx, cx = campo_auditoria("PIX", "pix")
        sv, cv = campo_auditoria("VALE COMPRA", "vale_compra")
        sf, cf = campo_auditoria("FAPP", "fapp")
        sl, cl = campo_auditoria("VLINK", "vlink")
        
        st.divider()
        _, cdes = campo_auditoria("DESPESA", "despesa", True)
        _, cvfu = campo_auditoria("VALE FUNC.", "vale_func", True)
        _, cdev = campo_auditoria("DEV. CARTÃO", "dev_cartao", True)
        _, cout = campo_auditoria("OUTROS", "outros", True)
        
        obs = st.text_area("Observações", value=d.get('observacoes', ''))
        
        if st.form_submit_button("💾 ATUALIZAR DADOS", use_container_width=True):
            novos_dados = {
                "sis_cartao": sc, "conf_cartao": cc, "sis_crediario": sr, "conf_crediario": cr,
                "sis_dinheiro": sd, "conf_dinheiro": cd, "sis_ifood": si, "conf_ifood": ci,
                "sis_pbm": sp, "conf_pbm": cp, "sis_pix": sx, "conf_pix": cx,
                "sis_vale_compra": sv, "conf_vale_compra": cv, "sis_fapp": sf, "conf_fapp": cf,
                "sis_vlink": sl, "conf_vlink": cl, "conf_despesa": cdes, "conf_vale_func": cvfu,
                "conf_dev_cartao": cdev, "conf_outros": cout, "observacoes": obs
            }
            supabase.table("fechamentos").update(novos_dados).eq("id", d['id']).execute()
            st.success("Dados atualizados com sucesso!"); st.rerun()
