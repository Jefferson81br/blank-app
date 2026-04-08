import streamlit as st
from datetime import date
import database_utils as db

def renderizar_tela(supabase, user):
    st.title("📝 Fechamento de Caixa Diário")
    
    loja_id = user['unidade_id']
    if not loja_id and user['funcao'] != 'admin':
        st.error("Usuário sem loja vinculada.")
        st.stop()

    # Seleção de Data
    data_sel = st.date_input("Data do Movimento", value=date.today(), max_value=date.today())
    st.write("---")
    
    # --- CABEÇALHO TITULADO ---
    c_h1, c_h2, c_h3, c_h4 = st.columns([2, 2, 2, 1.5])
    c_h1.write("**DESCRIÇÃO**")
    c_h2.write("**VALOR DO SISTEMA**")
    c_h3.write("**VALOR DE CONFERÊNCIA**")
    c_h4.write("**ACERTO**")

    # Função auxiliar para gerar as linhas
    def linha_f(label, key, bloqueia_sistema=False):
        col_desc, col_sis, col_conf, col_acer = st.columns([2, 2, 2, 1.5])
        col_desc.markdown(f"<div style='padding-top:10px'><b>{label}</b></div>", unsafe_allow_html=True)
        
        # Se for saída, o valor do sistema é travado em 0
        val_sis = col_sis.number_input("R$", key=f"s_{key}", format="%.2f", step=0.01, 
                                       label_visibility="collapsed", disabled=bloqueia_sistema)
        
        val_conf = col_conf.number_input("R$", key=f"c_{key}", format="%.2f", step=0.01, 
                                        label_visibility="collapsed")
        
        # O cálculo do acerto muda se for saída: é 0 - Conferência (negativo)
        acerto = val_conf - val_sis if not bloqueia_sistema else -val_conf
        
        cor = "white" if acerto == 0 else ("#ff4b4b" if acerto < 0 else "#00ff00")
        col_acer.markdown(f"<div style='padding-top:10px; color:{cor}; font-weight:bold;'>R$ {acerto:.2f}</div>", unsafe_allow_html=True)
        
        return val_sis, val_conf, acerto

    # --- GRUPO 1: ENTRADAS ---
    st.subheader("📥 Entradas")
    s_cartao, c_cartao, a_cartao = linha_f("CARTÃO", "cartao")
    s_cred, c_cred, a_cred = linha_f("CREDIÁRIO", "cred")
    s_din, c_din, a_din = linha_f("DINHEIRO", "din")
    s_ifood, c_ifood, a_ifood = linha_f("IFOOD", "ifood")
    s_pbm, c_pbm, a_pbm = linha_f("PBM", "pbm")
    s_pix, c_pix, a_pix = linha_f("PIX / TRANSFERÊNCIA", "pix")
    s_vale_c, c_vale_c, a_vale_c = linha_f("VALE COMPRA", "valec")
    s_fapp, c_fapp, a_fapp = linha_f("FARMÁCIAS APP", "fapp")
    s_vlink, c_vlink, a_vlink = linha_f("VIDA LINK", "vlink")

    st.write("---")

    # --- GRUPO 2: SAÍDAS (Sistema Travado) ---
    st.subheader("📤 Saídas")
    _, c_despesa, a_despesa = linha_f("DESPESA", "desp", bloqueia_sistema=True)
    _, c_valefunc, a_valefunc = linha_f("VALE FUNCIONÁRIO", "vfunc", bloqueia_sistema=True)
    _, c_dev_cartao, a_dev_cartao = linha_f("DEVOLUÇÃO CARTÃO", "devc", bloqueia_sistema=True)
    _, c_outros, a_outros = linha_f("OUTROS", "outros", bloqueia_sistema=True)

    # --- CÁLCULOS TOTAIS ---
    total_sistema = s_cartao + s_cred + s_din + s_ifood + s_pbm + s_pix + s_vale_c + s_fapp + s_vlink
    
    total_conferencia = (c_cartao + c_cred + c_din + c_ifood + c_pbm + c_pix + c_vale_c + c_fapp + c_vlink) - \
                        (c_despesa + c_valefunc + c_dev_cartao + c_outros)
    
    total_acerto = (a_cartao + a_cred + a_din + a_ifood + a_pbm + a_pix + a_vale_c + a_fapp + a_vlink) + \
                   (a_despesa + a_valefunc + a_dev_cartao + a_outros)

    # Exibição do Rodapé de Totais
    st.markdown("---")
    r1, r2, r3, r4 = st.columns([2, 2, 2, 1.5])
    r1.subheader("TOTAL")
    r2.subheader(f"R$ {total_sistema:,.2f}")
    r3.subheader(f"R$ {total_conferencia:,.2f}")
    
    cor_tot = "white" if total_acerto == 0 else ("#ff4b4b" if total_acerto < 0 else "#00ff00")
    r4.markdown(f"<h3 style='color:{cor_tot};'>R$ {total_acerto:,.2f}</h3>", unsafe_allow_html=True)

    # --- FORMULÁRIO DE ENVIO ---
    with st.form("f_final", clear_on_submit=True):
        arquivos = st.file_uploader("Anexar Prints do Fechamento", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'])
        obs = st.text_area("Observações")
        
        if st.form_submit_button("✅ SALVAR FECHAMENTO NO BANCO", use_container_width=True):
            with st.spinner("Salvando..."):
                # Dicionário preparado para os novos campos
                dados = {
                    "loja_id": loja_id, "usuario_id": user['id'], "data_fechamento": str(data_sel),
                    "sis_cartao": s_cartao, "conf_cartao": c_cartao,
                    "sis_crediario": s_cred, "conf_crediario": c_cred,
                    "sis_dinheiro": s_din, "conf_dinheiro": c_din,
                    "sis_ifood": s_ifood, "conf_ifood": c_ifood,
                    "sis_pbm": s_pbm, "conf_pbm": c_pbm,
                    "sis_pix": s_pix, "conf_pix": c_pix,
                    "sis_vale_compra": s_vale_c, "conf_vale_compra": c_vale_c,
                    "sis_fapp": s_fapp, "conf_fapp": c_fapp,
                    "sis_vlink": s_vlink, "conf_vlink": c_vlink,
                    "conf_despesa": c_despesa, "conf_vale_func": c_valefunc,
                    "conf_dev_cartao": c_dev_cartao, "conf_outros": c_outros,
                    "observacoes": obs, "urls_prints": []
                }
                
                ok, res_m = db.salvar_fechamento(supabase, dados)
                
                if ok:
                    urls = [db.fazer_upload_print(supabase, f, f"loja_{loja_id}/{data_sel}/p_{i}.jpg") for i, f in enumerate(arquivos)]
                    supabase.table("fechamentos").update({"urls_prints": [u for u in urls if u]}).eq("id", res_m.data[0]['id']).execute()
                    st.success("✅ Salvo com sucesso!")
                    st.balloons()
                else:
                    st.error(f"❌ Erro ao salvar: {res_m}")
