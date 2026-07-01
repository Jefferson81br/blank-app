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
