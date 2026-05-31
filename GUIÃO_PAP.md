# 🎓 Guião para Apresentação da PAP

Este documento serve como guião para a apresentação da **Prova de Aptidão Profissional (PAP)**. Segue esta ordem para uma demonstração fluida e profissional.

---

## 1. 🎤 Introdução (Teoria)
- **Tema:** Sistema de Gestão para o Bar da Escola.
- **Problema:** Filas longas, dificuldade em gerir stock, falta de digitalização nos pagamentos.
- **Solução:** Uma Web App (PWA) que permite pedidos online, gestão de saldo digital e controlo total de stock e finanças.

## 2. 🛠️ Tecnologias Utilizadas
- **Backend:** Python com a framework **Django 5.2**.
- **Frontend:** HTML5, CSS3 (Vanilla) e **TypeScript** (para maior segurança e qualidade de código).
- **Base de Dados:** SQLite (em desenvolvimento).
- **Funcionalidades Extra:** PWA (instalável como app), Geração de PDFs, QR Codes, **Assistente de IA (Barista AI)** e Stock Predictor com Gráficos.

## 3. 🖥️ Demonstração Prática (O que mostrar)

### A. Lado do Aluno/Cliente
1.  **Página Inicial:** Mostrar o design responsivo e apelativo.
2.  **Registo/Login:** Explicar a segurança (passwords encriptadas).
3.  **Menu de Produtos:**
    *   Filtrar por categorias.
    *   Adicionar produtos ao carrinho.
    *   Marcar como favorito.
4.  **Carrinho e Checkout:**
    *   Finalizar pedido.
    *   Mostrar que o saldo é descontado automaticamente.
5.  **Perfil:**
    *   Mostrar o saldo atual.
    *   Mostrar o histórico de pedidos e transações.
    *   Fazer um "Carregamento" de saldo fictício.

### B. Lado do Staff (Dashboard)
*Acede a `/dashboard` ou `/admin`.*

1.  **Dashboard Principal:** Vista geral de vendas e pedidos pendentes.
2.  **Gestão de Pedidos:**
    *   Mudar o estado de um pedido (Pendente -> Em Preparação -> Concluído).
    *   Mostrar que o cliente recebe a atualização.
3.  **Gestão de Stock:**
    *   Mostrar a lista de produtos e o stock atual.
    *   Simular um reabastecimento.
4.  **Relatórios Financeiros:**
    *   Exportar transações em **PDF** ou **CSV**.
    *   Mostrar o gráfico de resumo financeiro.
    *   **Gráfico de Previsão de Stock:** Explicar como o sistema usa inteligência simples para prever o que comprar.
5.  **Reviews:** Mostrar o feedback deixado pelos alunos.
6.  **Barista AI (Chatbot):**
    *   Fazer uma pergunta como Aluno (ex: "O que há para lanchar?").
    *   Fazer uma pergunta como Staff (ex: "Qual o produto com menos stock?").
    *   Mostrar como a IA respeita as permissões.
7.  **Scan QR Code:** Explicar que o staff pode ler códigos para validar pedidos rapidamente.

## 4. 📂 Estrutura de Código (Breve)
- Mostrar os **Modelos** (`models.py`): Onde a base de dados é definida.
- Mostrar as **Views** (`views.py`): Onde a lógica do negócio acontece.
- Mostrar os **Templates**: Onde a interface é construída.

## 5. 🏁 Conclusão
- **Dificuldades:** (Ex: Implementar o sistema de saldo, gerir stock em tempo real).
- **Aprendizagem:** Domínio de Django, bases de dados e UX/UI.
- **Futuro:** Implementar pagamentos reais (MBWay/Stripe) e notificações Push.

---

> [!TIP]
> Durante a apresentação, mantém o servidor a correr com `python manage.py runserver` e tem o site aberto em dois separadores: um como **Staff** e outro como **Aluno** para mostrar a interação em tempo real.
