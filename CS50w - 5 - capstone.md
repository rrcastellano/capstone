# CS50w - Final Project (Capstone) - EVChargeLog

## Resumo do Projeto

Este documento apresenta um resumo do **EVChargeLog**, uma aplicação web desenvolvida como projeto final (Capstone) para o curso CS50 Web Programming. O EVChargeLog permite que proprietários de veículos elétricos gerenciem suas recargas, visualizem custos e comparem economias em relação a veículos a combustão.

---

### 1. Estrutura de Arquivos

| Arquivo/Pasta | Descrição | Componentes Chave |
| :--- | :--- | :--- |
| **capstone/** | Configuração do Projeto | `settings.py` (i18n, WhiteNoise), `urls.py` (i18n_patterns) |
| **core/models.py** | Modelagem do Banco | `Recharge` (histórico), `Settings` (parâmetros usuário), `ContactLog` (suporte) |
| **core/views.py** | Lógica Backend | Agregação de KPIs, Dashboard, Parser CSV, Gestão de Auth, i18n |
| **core/forms.py** | Formulários Django | `RechargeForm`, `SettingsForm`, `ContactForm` |
| **core/admin.py** | Painel Administrativo | Personalização com filtros, search fields e totalizadores |
| **core/templatetags/custom_filters.py** | Filtros Customizados | Formatação de moeda/data sensível ao locale (R$ vs $) |
| **static/core/js/** | Scripts Frontend | `dashboard_charts.js` (Chart.js), `manage_recharges.js` (Fetch API, CRUD) |
| **static/core/css/** | Estilos | `styles.css` (Variáveis CSS, Dark-themed charts, Media Queries) |
| **templates/core/** | Templates HTML | `dashboard.html`, `manage_recharges.html`, `bulk_recharge.html`, `layout.html` |
| **deployment/** | Scripts de Deploy | `build.sh` (Render.com), `create_superuser_prod.py` |

---

### 2. Detalhamento das Implementações

#### A. Banco de Dados (`models.py`)
*   **Recharge:** Armazena sessões de recarga com data, kWh, custo, hodômetro, local e flags (isento).
*   **Settings:** Armazena preferências do usuário para cálculos de economia (preço gasolina, consumo do carro a combustão comparativo).
*   **ContactLog:** Registra feedback e solicitações de suporte via formulário.

#### B. Funcionalidades de Backend (`views.py` & `urls.py`)
*   **Dashboard Analytics:** Agrega dados de recargas para calcular KPIs em tempo real: Custo Total, Consumo Médio (kWh/100km), Economia Gerada (vs Gasolina) e KM Percorridos.
*   **Bulk Import (CSV):** Implementa um parser robusto que detecta encoding (UTF-8/Latin-1), normaliza quebras de linha e valida dados para importação em massa.
*   **Internacionalização (i18n):** Suporte completo para **PT-BR, EN-US e ES**. Middleware detecta preferência do usuário e formata saídas numéricas/monetárias.
*   **API Endpoints:** Rotas REST-like para operações AJAX no gerenciamento de recargas.

#### C. Frontend e Interatividade (JavaScript)
*   **Dashboard Interativo (`dashboard_charts.js`):** Utiliza Chart.js para renderizar gráficos de Custo Mensal e Consumo kWh, alimentados por dados JSON injetados pelo Django.
*   **Gestão Dinâmica (`manage_recharges.js`):** Tabela de recargas com ordenação, filtro e paginação via AJAX (Fetch API). Edição e exclusão ocorrem em modais sem recarregar a página.
*   **Responsividade:** Interface adaptável via Bootstrap 5 e CSS Grid, otimizada para mobile com touch-targets aumentados.

#### D. Templates (`templates/core/`)
*   **Layout Base:** Navbar responsiva com seletor de idioma.
*   **Filtros Customizados:** Uso de `custom_filters.py` para exibir moedas corretamente (e.g., `R$ 1.000,00` vs `$ 1,000.00`) dependendo do idioma ativo.

---

## Verificação de Requisitos (CS50W)

Com base na implementação e documentação, o projeto atende a todos os requisitos do Capstone.

**Veredito: WPROJECTO FINAL APROVADO PARA SUBMISSÃO**

### 1. Distinctiveness and Complexity (Distinção e Complexidade)
*   **Status:** ✅ **Atendido**
*   **Justificativa:** O projeto **não** é uma rede social, e-commerce ou clone do projeto Pizza.
    *   **Complexidade:** Envolve agregação de dados complexa (não apenas CRUD), parsing de arquivos CSV com heurística de encoding, e internacionalização completa (i18n) afetando formatação de dados e UI.
    *   **Distinção:** Focado em nicho específico (EVs) com lógica de negócios própria (cálculo de economia vs combustão).

### 2. Django Backend & JavaScript Frontend
*   **Status:** ✅ **Atendido**
*   **Backend:** Utiliza Django 5.x/6.x com pelo menos 3 modelos.
*   **Frontend:** JavaScript vanilla moderno para manipulação do DOM e chamadas assíncronas, além de biblioteca externa (Chart.js) para visualização de dados.

### 3. Mobile-Responsive
*   **Status:** ✅ **Atendido**
*   **Implementação:** Layout fluido com Bootstrap 5. Media queries em `styles.css` ajustam o grid de KPIs e gráficos para telas pequenas. Menu de navegação colapsável.

### 4. README.md Documentation
*   **Status:** ✅ **Atendido**
*   **Conteúdo:** O arquivo `README.md` contém:
    *   Seção explícita "Distinctiveness and Complexity".
    *   Estrutura de arquivos detalhada.
    *   Instruções passo-a-passo de instalação e execução.
    *   Lista de dependências (`requirements.txt`).

### Destaques / Extras

1.  **Deployment Ready:** Scripts `build.sh` e configuração para Render.com inclusos.
2.  **i18n Completo:** Tradução de interface E formatação de dados (L10n).
3.  **Segurança:** Dados isolados por usuário (`request.user`), CSRF protection em chamadas AJAX.
