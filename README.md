# Farma Gestor v1.3 💊

O **Farma Gestor** é uma aplicação corporativa de alta performance desenvolvida para automatizar, centralizar e auditar o processo de fechamento de caixa de redes de farmácias. O sistema mitiga fraudes e erros operacionais através de um fluxo contínuo de conciliação financeira entre os lançamentos das filiais e a validação do setor de Auditoria/Financeiro.

---

## 🚀 Funcionalidades Principais

* **Fechamento de Caixa Digital Interativo:** Registro detalhado e segmentado de entradas e saídas físicas e digitais por operadoras.
* **Sistema de Monitoramento Duplo (Conferência Estrita):** Módulo onde a auditoria valida de forma independente os dados inseridos pelo sistema das lojas contra os valores físicos contados.
* **Gestão Inteligente de Comprovantes:** Upload automatizado e armazenamento estruturado de múltiplos recibos e notas fiscais organizados por filial e data diretamente no *Supabase Storage*, com checagem de integridade visual (checks de Sistema, Depósito e Despesas).
* **Painel Dinâmico de Quebras de Caixa (Quebras de CX):** Gráficos analíticos diários e acumulados (mensais/anuais) gerados separadamente por unidade para acompanhamento de sobras e faltas financeiras.
* **Relatórios Avançados & Exportação:** Filtros globais por período, status de auditoria e integridade de documentos, com consolidação automática de totais e exportação nativa de relatórios estruturados em formatos CSV e PDF (modo paisagem com rodapé de paginação e assinatura).
* **Segurança de Dados Avançada (Enterprise):** Banco de dados totalmente protegido por políticas estritas de **Row-Level Security (RLS)** no nível do PostgreSQL, garantindo o isolamento completo de dados (Gerentes acessam apenas o escopo de suas respectivas filiais, enquanto Administradores e Auditores possuem visão macro da rede).
* **Histórico de Alterações Auditado (Soft Delete):** Inativação de registros em modo de segurança (coluna `ativo = False`) para permitir reenvios sem exclusão física do histórico de auditoria no banco.

---

## 🛠️ Tecnologias Utilizadas

* **Linguagem:** [Python 3.10+](https://www.python.org/)
* **Interface e Dashboard:** [Streamlit](https://streamlit.io/)
* **Banco de Dados & Storage Bucket:** [Supabase (PostgreSQL)](https://supabase.com/)
* **Processamento e Engenharia de Dados:** [Pandas](https://pandas.pydata.org/)
* **Gráficos e Visualizações:** [Plotly Express](https://plotly.com/python/)
* **Motor de Geração de PDFs:** [ReportLab](https://www.reportlab.com/)
* **Criptografia e Autenticação:** [Bcrypt](https://pypi.org/project/bcrypt/)

---

## 📋 Pré-requisitos

Antes de começar, você precisará ter instalado em seu ambiente de desenvolvimento:
* Python 3.10 ou superior
* Git
* Acesso administrativo a uma instância de projeto no Supabase

---

## 🔧 Instalação e Uso

1. **Clone o repositório:**
   ```bash
   git clone [https://github.com/seu-usuario/farma-gestor.git](https://github.com/seu-usuario/farma-gestor.git)
   cd farma-gestor

   Crie e ative um ambiente virtual (Virtualenv):

Bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
Instale todas as dependências do ecossistema:

Bash
pip install -r requirements.txt
Configuração de Variáveis de Ambiente e Credenciais:
Crie um diretório .streamlit/ na raiz do projeto (se não existir) e adicione o arquivo secrets.toml para o desenvolvimento local. Caso vá hospedar no Streamlit Cloud, configure estes campos na aba Advanced Settings -> Secrets:

Ini, TOML
SUPABASE_URL = "[https://seu-id-projeto.supabase.co](https://seu-id-projeto.supabase.co)"
SUPABASE_KEY = "sua_chave_anon_publica_do_supabase"
Inicie a aplicação:

Bash
streamlit run app.py
🗄️ Estrutura Arquitetural do Projeto
O projeto adota uma arquitetura modular baseada em Views independentes e scripts utilitários isolados para manipulação de persistência e autenticação:

├── .streamlit/
│   └── secrets.toml            # Credenciais e tokens de acesso (Ignorado no Git)
├── src/
│   ├── app.py                  # Ponto de entrada, fluxo de login e maestro de telas
│   ├── auth_utils.py           # Engine de criptografia, geração de hashes e verificação de senhas
│   ├── database_utils.py       # Queries Supabase, inserts, rotinas de auditoria e dump SQL
│   ├── inicio_view.py          # Dashboard/Home principal pós-login
│   ├── dashboard_view.py       # Telas de consolidação gerencial
│   ├── lancamento_view.py      # Módulo operacional de fechamento de caixa diário (Gerentes)
│   ├── usuarios_view.py        # Painel CRUD de gestão e criação de usuários (Níveis de Acesso)
│   ├── lojas_view.py           # Gestão cadastral das filiais e unidades da rede
│   ├── auditoria_view.py       # Painel crítico de conciliação e Soft Delete (Auditores)
│   ├── relatorios_view.py      # Motor de busca avançada e renderizador de PDFs/CSVs
│   ├── quebras_view.py         # Módulo visual de análise de saldo de caixa diário e acumulado
│   ├── ajuste_view.py          # Ajustes pontuais de valores e correções financeiras retroativas
│   └── tools_view.py           # Ferramentas técnicas exclusivas de Desenvolvimento (Backup SQL)
├── requirements.txt            # Manifesto de dependências do Python (ReportLab, Plotly, etc.)
└── README.md                   # Documentação do sistema


🔐 Configuração Crítica de Segurança (Banco de Dados)
Para o correto funcionamento do ecossistema de dados isolado por permissões, garanta que o Row-Level Security (RLS) esteja ativo no seu painel do Supabase para as tabelas usuarios, lojas e fechamentos.

Em caso de recuperação de desastres do banco, utilize o script .sql gerado pelo módulo Ferramentas do desenvolvedor. Se as tabelas forem recriadas, lembre-se de readequar o cast de tipos (auth.uid()::text = id::text) no editor SQL do Supabase para manter as políticas de acesso ativas.
