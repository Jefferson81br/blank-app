# Farma Gestor 💊

O **Farma Gestor** é uma aplicação robusta desenvolvida para automatizar e centralizar o processo de fechamento de caixa de redes de farmácias. O sistema permite que gerentes de diferentes unidades realizem lançamentos financeiros, enviem comprovantes e monitorem o fluxo de caixa de forma integrada.

---

## 🚀 Funcionalidades Principais

* **Fechamento de Caixa Digital:** Registro detalhado de entradas, saídas, sangrias e suprimentos.
* **Gestão de Comprovantes:** Upload e armazenamento de fotos de recibos e notas fiscais diretamente no Supabase Storage.
* **Visão Multi-loja:** Interface adaptável para diferentes unidades da rede.
* **Relatórios em Tempo Real:** Dashboard para acompanhamento das vendas e movimentações diárias.
* **Segurança de Dados:** Integração segura com banco de dados PostgreSQL (via Supabase).

## 🛠️ Tecnologias Utilizadas

* **Linguagem:** [Python](https://www.python.org/)
* **Interface:** [Streamlit](https://streamlit.io/)
* **Banco de Dados & Storage:** [Supabase](https://supabase.com/)
* **Processamento de Dados:** [Pandas](https://pandas.pydata.org/)

## 📋 Pré-requisitos

Antes de começar, você precisará ter instalado:
* Python 3.8 ou superior
* Git

## 🔧 Instalação e Uso

1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/seu-usuario/farma-gestor.git](https://github.com/seu-usuario/farma-gestor.git)
    cd farma-gestor
    ```

2.  **Crie e ative um ambiente virtual:**
    ```bash
    # Windows
    python -m venv venv
    .\venv\Scripts\activate

    # Linux/Mac
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configuração de Variáveis de Ambiente:**
    Crie um arquivo `.env` na raiz do projeto ou configure os `Secrets` no Streamlit Cloud com as seguintes chaves:
    ```env
    SUPABASE_URL="sua_url_do_supabase"
    SUPABASE_KEY="sua_chave_anon_publica"
    ```

5.  **Inicie a aplicação:**
    ```bash
    streamlit run app.py
    ```

## 🗄️ Estrutura do Projeto

```text
├── .streamlit/          # Configurações do Streamlit
├── assets/             # Imagens e logos
├── src/                # Scripts de suporte (DB, Auth, Utils)
├── app.py              # Ponto de entrada da aplicação
├── requirements.txt    # Dependências do projeto
└── README.md           # Documentação
