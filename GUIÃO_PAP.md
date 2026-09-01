# 🎓 Guião para Apresentação da PAP

Este documento serve como guião para a apresentação da Prova de Aptidão Profissional. A demonstração deve seguir esta ordem para apresentar o problema, a solução, as tecnologias e depois mostrar o sistema na prática.

---

## 1. 🎤 Introdução

### Tema

Sistema de Gestão Digital para o Bar da Escola.

### Problema

O funcionamento tradicional de um bar escolar pode provocar filas, dificuldades na gestão dos pedidos, erros no controlo de stock e pouca visibilidade sobre as receitas e despesas.

### Solução

Foi desenvolvida uma aplicação web para centralizar a gestão do bar.

O sistema permite aos alunos e professores consultar o menu e realizar pedidos, enquanto os funcionários e administradores conseguem gerir pedidos, produtos, stock e informação financeira.

A aplicação inclui ainda um sistema de saldo digital e um assistente inteligente, o Barista AI.

---

## 2. 🛠️ Tecnologias Utilizadas

### Backend

Python com Django.

### Frontend

HTML5, CSS3 e TypeScript/JavaScript, de acordo com os componentes utilizados no projeto.

### Base de Dados

SQLite em ambiente de desenvolvimento.

### Funcionalidades complementares

* PWA, permitindo instalar a aplicação como uma app.
* Sistema de autenticação e diferentes níveis de permissões.
* Gestão de saldo digital.
* Gestão de produtos e categorias.
* Gestão de stock.
* Gestão de pedidos.
* Registo de transações.
* Relatórios e gráficos.
* Exportação de informação.
* Geração de documentos/QR Codes.
* Barista AI, utilizando a API Gemini.
* Previsão/análise de stock.

---

# 3. 🖥️ Demonstração Prática

A demonstração deve ser feita principalmente com duas sessões abertas:

* uma sessão de Aluno;
* uma sessão de Funcionário/Admin.

Desta forma é possível mostrar as diferenças de permissões e a interação entre as duas partes do sistema.

---

## A. 👨‍🎓 Lado do Aluno

### 1. Login

Entrar com a conta de teste:

`alunoteste`

Explicar que as contas não são criadas livremente pelo aluno.

A criação das contas é controlada pela administração, permitindo garantir que cada utilizador fica associado ao tipo correto.

Isto evita situações como um aluno escolher uma turma ou função incorreta durante o registo.

### 2. Página inicial

Mostrar:

* interface;
* navegação;
* responsividade;
* informações principais.

### 3. Menu

Mostrar:

* produtos disponíveis;
* categorias;
* preços;
* disponibilidade;
* favoritos.

Adicionar alguns produtos aos favoritos.

### 4. Carrinho

Adicionar vários produtos.

Mostrar:

* quantidades;
* subtotal;
* total;
* alteração das quantidades;
* remoção de produtos.

### 5. Checkout

Finalizar um pedido utilizando o saldo disponível.

Mostrar que:

* o pedido é criado;
* o saldo é atualizado;
* o pedido fica registado no histórico.

### 6. Pedido

Abrir a página do pedido.

Mostrar:

* número do pedido;
* produtos;
* quantidades;
* valor;
* estado;
* informação do utilizador.

Se o QR Code já estiver implementado, mostrar também o QR Code associado ao pedido.

### 7. Perfil

Mostrar:

* nome;
* tipo de utilizador;
* saldo;
* histórico;
* pedidos;
* transações.

---

# B. 👨‍💼 Lado do Funcionário

Entrar com:

`funcionarioteste`

### 1. Dashboard

Mostrar:

* resumo das vendas;
* pedidos;
* stock;
* informação financeira;
* gráficos.

Explicar que esta informação depende das permissões do utilizador.

### 2. Gestão de Pedidos

Abrir os pedidos.

Mostrar um pedido criado anteriormente pelo aluno.

Alterar o estado:

Pendente → Em preparação → Concluído

Explicar que isto permite ao funcionário acompanhar o processo de preparação do pedido.

### 3. Gestão de Produtos

Mostrar:

* produtos;
* categorias;
* preços;
* disponibilidade;
* stock;
* stock mínimo.

Se for possível, alterar uma informação de um produto e mostrar a atualização.

### 4. Gestão de Stock

Mostrar um produto com stock reduzido.

Demonstrar um reabastecimento.

Explicar que o sistema permite acompanhar as quantidades disponíveis e identificar produtos que necessitam de reposição.

### 5. Informação Financeira

Mostrar:

* receitas;
* despesas/custos;
* transações;
* saldo;
* gráficos.

Se estiver disponível:

* exportação para CSV;
* exportação para PDF.

Explicar que estes dados permitem ter uma visão geral do funcionamento financeiro do bar.

### 6. Reviews

Mostrar as avaliações deixadas pelos utilizadores.

Explicar que permitem recolher feedback sobre a experiência no bar.

---

# C. 🤖 Barista AI

Esta é uma das funcionalidades que vale a pena demonstrar com atenção.

### Como Aluno

Perguntar:

"O que há para lanchar?"

ou:

"Que produtos estão disponíveis?"

Mostrar que a IA responde utilizando os dados disponíveis no sistema.

### Como Funcionário/Admin

Perguntar algo como:

"Qual o produto com menos stock?"

ou:

"Quanto foi faturado hoje?"

Mostrar que o Barista AI consegue utilizar informação administrativa quando o utilizador tem permissões para a consultar.

### Teste de permissões

Como aluno, fazer uma pergunta sobre informação financeira ou stock administrativo.

Mostrar que o sistema não fornece informação que o aluno não tem autorização para consultar.

Explicar:

"O Barista AI não recebe apenas a pergunta. Antes de consultar a IA, o sistema constrói um contexto de acordo com o tipo de utilizador e apenas disponibiliza os dados que esse utilizador pode consultar."

Esta é uma boa parte para explicar tecnicamente.

---

# D. 🔐 Segurança e Permissões

Mostrar uma funcionalidade administrativa enquanto autenticado como aluno.

Por exemplo:

aceder a `/admin` ou a uma área exclusiva de funcionários.

O sistema deve impedir o acesso e apresentar a mensagem de falta de permissões.

Explicar que existem diferentes níveis de acesso:

* Aluno
* Professor
* Funcionário
* Administrador

Cada tipo de utilizador possui permissões diferentes.

Também explicar que as passwords são armazenadas através do sistema de hashing do Django e não em texto simples.

---

# E. 👑 Administrador

Entrar com a conta de administrador.

Mostrar a área administrativa.

Demonstrar a criação de uma conta.

Criar, por exemplo:

* um aluno;
* um professor;
* um funcionário.

Explicar que o administrador controla a criação das contas, garantindo que os dados e o tipo de utilizador são definidos corretamente.

Mostrar também a gestão dos restantes dados administrativos disponíveis.

---

# F. 📱 PWA

Se estiver disponível no navegador:

Mostrar a opção de instalar a aplicação.

Explicar que a aplicação pode ser instalada no dispositivo e utilizada com uma experiência semelhante à de uma aplicação tradicional.

---

# G. 📧 Emails Automáticos

Demonstrar uma funcionalidade que envie email, caso esteja configurada.

Explicar que existe uma conta de email dedicada ao projeto para o envio das notificações automáticas.

Mostrar apenas o resultado do envio.

NUNCA mostrar a password da conta, palavra-passe de aplicação ou API keys durante a apresentação.

---

# H. 📷 QR Code dos Pedidos

Se a funcionalidade estiver implementada:

Criar um pedido como aluno.

Abrir o pedido.

Mostrar o QR Code.

Explicar que o QR Code permite ao funcionário identificar rapidamente o pedido.

Idealmente, o QR Code deve representar um identificador seguro do pedido e não expor diretamente informação sensível.

No lado do funcionário:

* abrir o leitor;
* ler o QR Code;
* identificar o pedido;
* confirmar os dados;
* alterar o estado do pedido.

---

# 4. 💻 Estrutura do Código

Fazer uma explicação curta, sem entrar em demasiado detalhe.

### Models

Mostrar `models.py`.

Explicar que os modelos representam a estrutura dos dados da aplicação:

* utilizadores;
* produtos;
* categorias;
* pedidos;
* itens dos pedidos;
* transações;
* stock;
* etc.

### Views

Mostrar algumas das views principais.

Explicar que contêm a lógica responsável por processar os pedidos do utilizador e comunicar com os modelos.

### Templates

Mostrar alguns templates.

Explicar que representam a interface apresentada ao utilizador.

### URLs

Mostrar como as URLs ligam os pedidos às respetivas views.

### Barista AI

Mostrar brevemente a view responsável pelo Barista AI.

Explicar:

Pergunta → criação do contexto → API Gemini → resposta → processamento da resposta → apresentação ao utilizador.

---

# 5. 🧪 Demonstração de um Fluxo Completo

Se houver tempo, esta deve ser a demonstração principal.

### Passo 1

Entrar como aluno.

### Passo 2

Consultar o menu.

### Passo 3

Adicionar produtos ao carrinho.

### Passo 4

Finalizar o pedido.

### Passo 5

Mostrar o pedido criado.

### Passo 6

Mudar para a sessão do funcionário.

### Passo 7

Mostrar o novo pedido no dashboard.

### Passo 8

Abrir o pedido.

### Passo 9

Alterar o estado para "Em preparação".

### Passo 10

Concluir o pedido.

### Passo 11

Voltar ao aluno e mostrar a atualização.

### Passo 12

Mostrar a alteração no histórico/transações.

Este fluxo demonstra praticamente todo o ciclo da aplicação.

---

# 6. 🧠 Principais Dificuldades

Escolher 2 ou 3 dificuldades reais que aconteceram durante o desenvolvimento.

Exemplos:

* implementação do sistema de saldo;
* gestão das permissões;
* gestão do stock;
* integração com a API Gemini;
* comunicação entre frontend e backend;
* gestão das relações entre pedidos, produtos e utilizadores;
* criação dos relatórios e gráficos.

Não inventar dificuldades que não tenham acontecido.

---

# 7. 📚 Aprendizagens

Durante o desenvolvimento foram aprofundados conhecimentos em:

* Python;
* Django;
* bases de dados;
* desenvolvimento web;
* autenticação;
* gestão de permissões;
* APIs;
* JavaScript/TypeScript;
* organização de projetos;
* Git/GitHub;
* UX/UI;
* integração de inteligência artificial.

---

# 8. 🚀 Trabalho Futuro

Possíveis melhorias:

* integração de pagamentos reais;
* MB WAY/Stripe;
* notificações Push;
* melhoria do sistema de QR Codes;
* aplicação mobile dedicada;
* integração com sistemas reais da escola;
* melhorias no sistema de previsão de stock;
* utilização de uma base de dados de produção;
* funcionalidades adicionais de análise financeira.

---

# 9. 🏁 Conclusão

Terminar reforçando a ideia principal:

O objetivo do projeto foi desenvolver uma solução digital para modernizar a gestão do bar escolar, tornando o processo de pedidos mais simples para os utilizadores e fornecendo aos funcionários e administradores ferramentas para gerir pedidos, produtos, stock e informação financeira.

A aplicação procura centralizar todo o funcionamento do bar numa única plataforma, reduzindo processos manuais e permitindo uma gestão mais eficiente.

---

## ⚠️ Antes da apresentação

Preparar:

* servidor a funcionar;
* base de dados limpa;
* contas de teste;
* produtos com stock;
* saldo suficiente para o aluno;
* email de teste configurado;
* Barista AI funcional;
* duas sessões de navegador abertas;
* uma como aluno;
* outra como funcionário/admin.

Não utilizar API keys, passwords ou outras credenciais reais durante a apresentação.

Ter também uma cópia de segurança da base de dados antes de começar.

A melhor demonstração é fazer primeiro um fluxo completo Aluno → Pedido → Funcionário → Conclusão e só depois mostrar as funcionalidades individuais.
