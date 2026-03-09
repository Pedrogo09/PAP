# 🍽️ Bar Escolar - Sistema de Gestão (PAP)

> Sistema integrado de gestão de bar escolar desenvolvido em **Django 5.2**, permitindo pedidos online, pagamentos por saldo, gestão de stock inteligente e relatórios financeiros.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Django](https://img.shields.io/badge/Django-5.2.10-green)
![SQLite](https://img.shields.io/badge/Database-SQLite-yellow)
![Mobile](https://img.shields.io/badge/Mobile-Responsive-brightgreen)

---

## 📋 Guia Rápido de Instalação

### 1. Preparar o Ambiente
```powershell
# Ativar ambiente virtual
venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt
```

### 2. Configurar Base de Dados e Admin
```powershell
# Aplicar migrações
python manage.py migrate

# Criar conta de administrador (se necessário)
python manage.py createsuperuser
```

### 3. Iniciar o Servidor
```powershell
python manage.py runserver
```
Aceda em: [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## 🔄 Sincronização entre Computadores (Git)

Para garantir que tens sempre a mesma base de dados e imagens em diferentes PCs:

| Ação | Comandos |
|------|----------|
| **Antes de começar** (Pull) | `git pull origin main` |
| **Ao terminar** (Push) | `git add .` <br> `git commit -m "Update"` <br> `git push origin main` |

> [!IMPORTANT]
> Faz sempre `git pull` antes de abrir o projeto num PC novo para evitar conflitos na base de dados!

---

## ✨ Funcionalidades Principais

### 👥 Utilizadores (4 Níveis)
- **Aluno/Professor:** Faz pedidos, carrega saldo e vê histórico.
- **Staff:** Gere pedidos, adiciona stock e vê dashboard de vendas.
- **Admin:** Controlo total via Django Admin.

### 🛒 Pedidos e Pagamentos
- Carrinho de compras persistente.
- Agendamento de pedidos com validação de horários de funcionamento.
- **Pagamento Automático:** Dedução direta do saldo do utilizador.
- **Recibos em PDF:** Gerados automaticamente e disponíveis para download/email.

### 📦 Gestão de Stock e Finanças
- **Baixa Automática:** Stock reduzido no momento da compra.
- **Alertas Críticos:** Avisos no dashboard quando o stock está baixo.
- **Dedução Financeira:** Ao adicionar stock, o sistema desconta automaticamente 50% do valor da conta da escola para simular o custo de compra.

---

## 📧 Configuração de Email

Crie um ficheiro `.env` na raiz do projeto:

```env
# Para testar (emails aparecem no terminal):
EMAIL_USE_DEVELOPMENT=True

# Para enviar emails reais (Gmail):
EMAIL_HOST_USER=teu-email@gmail.com
EMAIL_HOST_PASSWORD=tua-app-password-de-16-digitos
EMAIL_USE_DEVELOPMENT=False
```

---

## 📁 Estrutura do Projeto

- `bar_app/`: Lógica principal (models, views, forms).
- `bar_escola/`: Configurações do Django.
- `media/`: Imagens de produtos e recibos PDF.
- `templates/`: Ficheiros HTML (Bootstrap 5).
- `db.sqlite3`: Base de dados (Sincronizada via Git).

---

## 🔐 Credenciais de Teste (Padrão)

| Tipo | Utilizador | Palavra-passe |
|------|------------|---------------|
| **Admin** | `admin` | `admin` |
| **Staff** | `staff` | `staff` |
| **Aluno** | `aluno` | `123456` |

---

## 📊 Endpoints API

- `/menu/` - Cardápio de produtos.
- `/orders/` - Meus pedidos.
- `/dashboard/` - Painel de controlo Staff (Gráficos e Stock).
- `/topup/` - Carregar saldo.
- `/admin/` - Gestão avançada.

---

**Desenvolvido para:** Prova de Aptidão Profissional (PAP)  
**Última Atualização:** Março 2026
