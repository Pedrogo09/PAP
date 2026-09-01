# 🍽️ Bar Escolar - Sistema de Gestão (PAP)

Sistema de gestão de bar escolar desenvolvido em **Django 5.2**, com suporte a pedidos online, pagamentos por saldo, gestão de stock e relatórios.

---

## 📊 Linguagens do Projeto

* 🟠 **HTML:** 44.3%

* 🐍 **Python:** 43.2%

* 🎨 **CSS:** 5.0%

* 🔵 **TypeScript:** 5.8%

* ⚪ **Outros:** 1.7%

---

## 🚀 Como Executar (forma rápida)

1. **Executar os scripts na ordem seguinte**

   ```powershell
   .\start.bat
   .\up.bat
   ```

---

## 🚀 Como Executar (sem utilizar scripts)

1. **Ativar Ambiente Virtual:**

   ```powershell
   .\venv\Scripts\activate
   ```

2. **Instalar Dependências:**

   ```powershell
   pip install -r requirements.txt
   ```

3. **Migrar Base de Dados:**

   ```powershell
   python manage.py migrate
   ```

4. **Iniciar Servidor:**

   ```powershell
   python manage.py runserver
   ```

   Aceda em: http://127.0.0.1:8000

---

## 🔗 Como Ligar ao GitHub e Atualizar

Se ainda não tens o repositório ligado:

1. **Criar Repositório no GitHub** (sem README nem .gitignore).

2. **No terminal do projeto:**

   ```powershell
   git init
   git remote add origin https://github.com/O_TEU_USER/O_TEU_REPO.git
   git add .
   git commit -m "Primeiro commit"
   git branch -M main
   git push -u origin main
   ```

### 🔄 Como Atualizar o Repositório (Sempre que fizeres mudanças):

```powershell
# 1. Adicionar todas as mudanças

git add .

# 2. Criar uma nota sobre o que mudaste

git commit -m "Atualização do projeto"

# 3. Enviar para o GitHub

git push
```

---

**Nota:** Toda a gestão pode ser feita através do `/dashboard` ou do painel `/admin` padrão.
