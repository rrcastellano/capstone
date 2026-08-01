# Roteiro de Vídeo - CS50W Capstone (EVChargeLog)

**Tempo Estimado:** 3 a 4 minutos.
**Objetivo:** Demonstrar as funcionalidades, complexidade e distinção do projeto "EVChargeLog".

---

## 1. Introdução (0:00 - 0:30)
**[Visual: Tela inicial do projeto (Login ou Home Deslogada)]**

*   "Olá, meu nome é [Seu Nome], esta é minha submissão final para o CS50 Web Programming com Python e JavaScript."
*   "Meu projeto se chama **EVChargeLog**. É uma aplicação web robusta projetada para proprietários de veículos elétricos (EVs) gerenciarem seus históricos de recarga, custos e eficiência."
*   "Diferente de projetos anteriores como e-commerce ou redes sociais, este é um **Data Tracker e Dashboard Analítico** que foca em agregação de dados e cálculos em tempo real."

---

## 2. Dashboard e Complexidade (0:30 - 1:15)
**[Visual: Fazer login e cair no Dashboard]**

*   "Ao fazer login, somos recebidos por este Dashboard interativo. Aqui reside grande parte da complexidade do back-end."
*   "O Django agrega todas as recargas registradas para calcular KPIs em tempo real, como:"
    *   **[Aponte para os KPIs]**: "Custo Total, Consumo Médio em kWh/100km e, o mais importante, a **Economia Estimada** em comparação com um veículo a gasolina."
*   "Esses gráficos (Custo Mensal e Eficiência) são renderizados via **Chart.js**, alimentados por dados JSON processados no servidor."

---

## 3. Gestão de Dados e Bulk Import (1:15 - 2:15)
**[Visual: Navegar para 'Minhas Recargas' / 'Gerenciar']**

*   "Na área de gerenciamento, temos uma tabela completa com paginação e ordenação assíncrona via JavaScript (Fetch API)."
*   **[Ação: Clique em 'Adicionar Recarga' e preencha rapidamente]**
*   "Podemos adicionar recargas manualmente..."
*   **[Ação: Vá para a aba/página de Importação CSV]**
*   "...mas a funcionalidade mais complexa é o **Importador CSV Inteligente/Bulk Import**."
*   "Implementei um parser heurístico no back-end que detecta automaticamente a codificação do arquivo (UTF-8 ou Latin-1) e normaliza formatos de data, permitindo que usuários importem históricos longos de outros apps de uma só vez."

---

## 4. Internacionalização (i18n) e Configurações (2:15 - 3:00)
**[Visual: Vá para Configurações e depois troque o idioma]**

*   "O projeto foi construído com suporte total a **Internacionalização (i18n)**."
*   **[Ação: Troque o idioma de Inglês para Português no menu]**
*   "Observe que ao mudar para Português, não apenas o texto da interface muda, mas a **formatação de dados** também se adapta."
    *   "Os valores monetários mudam de Dólar (`$ 1,000.00`) para Real (`R$ 1.000,00`) e as datas mudam de `MM/DD` para `DD/MM`."
*   "Isso é gerenciado pelo `LocaleMiddleware` do Django e filtros de template personalizados que criei."

---

## 5. Responsividade Mobile (3:00 - 3:30)
**[Visual: Abra as ferramentas de desenvolvedor do navegador (F12) e mude para visualização mobile (iPhone/Pixel)]**

*   "Como requerido, a aplicação é totalmente responsiva."
*   "No modo mobile, o menu de navegação colapsa, a grade de KPIs se ajusta para uma coluna única e as tabelas escondem colunas menos importantes para caber na tela."
*   "Botões e inputs têm áreas de toque aumentadas para facilitar o uso em smartphones."

---

## 6. Conclusão (3:30 - Final)
**[Visual: Voltar para a Home ou Dashboard]**

*   "O EVChargeLog utiliza Django no back-end para lógica complexa de dados e i18n, e JavaScript no front-end para gráficos dinâmicos e operações assíncronas, cumprindo todos os requisitos de distinção e complexidade."
*   "Este foi o EVChargeLog."
*   "Obrigado por assistir."
