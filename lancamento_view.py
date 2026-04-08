import streamlit as st
from datetime import date, timedelta
import database_utils as db

def renderizar_tela(supabase, user):
    st.title("📝 Lançamento e Edição de Fechamento")
    
    # --- LOGICA DE ACESSO A LOJAS ---
    lojas_res = db.buscar_lojas(supabase)
    mapa_lojas = {l['nome']: l['id'] for l in lojas_res.data} if lojas_res.data else {}
    
    if user['funcao'] in ['admin', 'proprietario']:
        loja_nome_sel = st.selectbox("Selecione a Unidade para Lançar/Editar:", options=list(mapa_lojas.keys()))
        loja_id = mapa_lojas[loja_nome_sel]
    else:
        loja_id = user['unidade_id']
        if not loja_id:
            st.error("Usuário sem loja vinculada.")
            st.stop()
        st.info(f"Unidade: {next((nome for nome, id in mapa_lojas.items() if id == loja_id), 'Não identificada')}")

    # Seleção de Data
    data_sel = st.date_input("Data do Movimento", value=date.today(), max_value=date.today())
    
    # --- BUSCA DADOS EXISTENTES PARA EDIÇÃO ---
    res_existente = supabase.table("fechamentos").select("*").eq("loja_id", loja_id).eq("data_fechamento", str(data_sel)).execute()
    dados_previos = res_existente.data[0] if res_existente.data else None

    if dados_previos:
        st.warning(f"⚠️ Editando lançamento existente do dia {data_sel.strftime('%d/%m/%Y')}")
    else:
        st.info(f"Novo lançamento para o dia {data_sel.strftime('%d/%m/%Y')}")

    st.write("---")
    
    # Cabeçalho
    c_h1, c_h2, c_h3, c_h4 = st.columns([2, 2, 2, 1.5])
    c_h1.write("**DESCRIÇÃO**")
    c_h2.write("**VALOR DO SISTEMA**")
    c_h3.write("**VALOR DE CONFERÊNCIA**")
    c_h4.write("**ACERTO**")

    def linha_f(label, key, bloqueia_sistema=False):
        col_desc, col_sis, col_conf, col_acer = st.columns([2, 2, 2, 1.5])
        col_desc.markdown(f"<div style='padding-top:10px'><b>{label}</b></div>", unsafe_allow_html=True)
        
        # Carrega valor do banco se existir, senão 0.0
        val_default_s = dados_previos.get(f"sis_{key}", 0.0) if dados_previos else 0.0
        val_default_c = dados_previos.get(f"conf_{key}", 0.0) if dados_previos else 0.0
        
        # Caso especial para campos de saída que não tem 'sis_' no banco
        if bloqueia_sistema:
            val_default_s = 0.0
            val_default_c = dados_previos.get(f"conf_{key}", 0.0) if dados_previos else 0.0

        val_sis = col_sis.number_input("R$", key=f"s_{key}", value=float(val_default_s), format="%.2f", step=0.01, label_visibility="collapsed", disabled=bloqueia_sistema)
        val_conf = col_conf.number_input("R$", key=f"c_{key}", value=float(val_default_c), format="%.2f", step=0.01, label_visibility="collapsed")
        
        acerto = val_conf - val_sis
        cor = "white" if acerto == 0 else ("#ff4b4b" if acerto < 0 else "#00ff00")
        col_acer.markdown(f"<div style='padding-top:10px; color:{cor}; font-weight:bold;'>R$ {acerto:.2f}</div>", unsafe_allow_html=True)
        return val_sis, val_conf, acerto

    # --- CAMPOS ---
    st.subheader("📥 Entradas")
    s_cartao, c_cartao, a_cartao = linha_f("CARTÃO", "cartao")
    s_cred, c_cred, a_cred = linha_f("CREDIÁRIO", "crediario") # ajuste conforme nome no SQL
    s_din, c_din, a_din = linha_f("DINHEIRO", "dinheiro")
    s_ifood, c_ifood, a_ifood = linha_f("IFOOD", "ifood")
    s_pbm, c_pbm, a_pbm = linha_f("PBM", "pbm")
    s_pix, c_pix, a_pix = linha_f("PIX / TRANSFERÊNCIA", "pix")
    s_vale_c, c_vale_c, a_vale_c = linha_f("VALE COMPRA", "vale_compra")
    s_fapp, c_fapp, a_fapp = linha_f("FARMÁCIAS APP", "fapp")
    s_vlink, c_vlink, a_vlink = linha_f("VIDA LINK", "vlink")

    st.write("---")
    st.subheader("📤 Saídas")
    _, c_despesa, a_despesa = linha_f("DESPESA", "despesa", bloqueia_sistema=True)
    _, c_valefunc, a_valefunc = linha_f("VALE FUNCIONÁRIO", "vale_func", bloqueia_sistema=True)
    _, c_dev_cartao, a_dev_cartao = linha_f("DEVOLUÇÃO CARTÃO", "dev_cartao", bloqueia_sistema=True)
    _, c_outros, a_outros = linha_f("OUTROS", "outros", bloqueia_sistema=True)

    # Totais
    total_sistema = s_cartao + s_cred + s_din + s_ifood + s_pbm + s_pix + s_vale_c + s_fapp + s_vlink
    total_conferencia = (c_cartao + c_cred + c_din + c_ifood + c_pbm + c_pix + c_vale_c + c_fapp + c_vlink) - (c_despesa + c_valefunc + c_dev_cartao + c_outros)
    total_acerto = a_cartao + a_cred + a_din + a_ifood + a_pbm + a_pix + a_vale_c + a_fapp + a_vlink + a_despesa + a_valefunc + a_dev_cartao + a_outros

    st.markdown("---")
    res1, res2, res3, res4 = st.columns([2, 2, 2, 1.5])
    res1.subheader("TOTAL")
    res2.subheader(f"R$ {total_sistema:,.2f}")
    res3.subheader(f"R$ {total_conferencia:,.2f}")
    cor_tot = "white" if total_acerto == 0 else ("#ff4b4b" if total_acerto < 0 else "#00ff00")
    res4.markdown(f"<h3 style='color:{cor_tot};'>R$ {total_acerto:,.2f}</h3>", unsafe_allow_html=True)

    with st.form("f_final"):
        arquivos = st.file_uploader("Anexar novos prints (substituem os antigos)", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'])
        obs_default = dados_previos.get("observacoes", "") if dados_previos else ""
        obs = st.text_area("Observações", value=obs_default)
        
        label_botao = "🚀 ATUALIZAR FECHAMENTO" if dados_previos else "✅ SALVAR NOVO FECHAMENTO"
        
        if st.form_submit_button(label_botao, use_container_width=True):
            dados = {
                "loja_id": loja_id, "usuario_id": user['id'], "data_fechamento": str(data_sel),
                "sis_cartao": s_cartao, "conf_cartao": c_cartao, "sis_crediario": s_cred, "conf_crediario": c_cred,
                "sis_dinheiro": s_din, "conf_dinheiro": c_din, "sis_ifood": s_ifood, "conf_ifood": c_ifood,
                "sis_pbm": s_pbm, "conf_pbm": c_pbm, "sis_pix": s_pix, "conf_pix": c_pix,
                "sis_vale_compra": s_vale_c, "conf_vale_compra": c_vale_c, "sis_fapp": s_fapp, "conf_fapp": c_fapp,
                "sis_vlink": s_vlink, "conf_vlink": c_vlink, "conf_despesa": c_despesa, "conf_vale_func": c_valefunc,
                "conf_dev_cartao": c_dev_cartao, "conf_outros": c_outros, "observacoes": obs
            }
            ok, res_m = db.salvar_fechamento(supabase, dados)
            if ok:
                if arquivos:
                    urls = [db.fazer_upload_print(supabase, f, f"loja_{loja_id}/{data_sel}/p_{i}.jpg") for i, f in enumerate(arquivos)]
                    supabase.table("fechamentos").update({"urls_prints": [u for u in urls if u]}).eq("id", res_m.data[0]['id']).execute()
                st.success("✅ Operação realizada com sucesso!")
                st.rerun()
