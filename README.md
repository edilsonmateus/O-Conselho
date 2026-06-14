# 77Gira · Conselho Digital de Negócios

Aplicativo web do corpo de conselheiros digitais da 77Gira.
Deploy gratuito no Render.com em ~5 minutos.

---

## PASSO A PASSO PARA DEPLOY NO RENDER

### 1. Criar conta no GitHub (se não tiver)
Acesse https://github.com e crie uma conta gratuita.

### 2. Criar um repositório no GitHub
1. Clique em **New repository** (botão verde no canto superior direito)
2. Nome: `conselho-77gira`
3. Deixe como **Public** (necessário no plano gratuito do Render)
4. Clique em **Create repository**

### 3. Fazer upload dos arquivos
Na página do repositório recém-criado, clique em **uploading an existing file** e envie:
- `app.py`
- `requirements.txt`
- `render.yaml`

Clique em **Commit changes**.

### 4. Criar conta no Render
Acesse https://render.com e crie uma conta gratuita (pode entrar com o GitHub).

### 5. Criar o serviço web no Render
1. No painel do Render, clique em **New +** → **Web Service**
2. Clique em **Connect a repository**
3. Conecte sua conta GitHub e selecione o repositório `conselho-77gira`
4. Preencha os campos:
   - **Name:** conselho-77gira
   - **Region:** Oregon (padrão)
   - **Branch:** main
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app --workers 2 --timeout 120`
   - **Instance Type:** Free

### 6. Configurar a chave da API Anthropic
1. Ainda na tela de configuração, desça até **Environment Variables**
2. Clique em **Add Environment Variable**
3. Preencha:
   - **Key:** `ANTHROPIC_API_KEY`
   - **Value:** sua chave (obtida em https://console.anthropic.com → API Keys)
4. Clique em **Save**

### 7. Adicionar disco persistente (para salvar o histórico)
1. No menu à esquerda do serviço, clique em **Disks**
2. Clique em **Add Disk**
3. Preencha:
   - **Name:** dados-77gira
   - **Mount Path:** /data
   - **Size:** 1 GB
4. Clique em **Save**
> ⚠️ O disco persistente custa ~$0,25/mês. Se não quiser pagar, pule esta etapa
> (o histórico será perdido a cada redeploy, mas o app funciona normalmente).

### 8. Fazer o deploy
Clique em **Create Web Service**. O Render vai:
- Baixar o código do GitHub
- Instalar as dependências (~1-2 minutos)
- Iniciar o servidor

Quando aparecer **"Your service is live"**, o app estará rodando em:
`https://conselho-77gira.onrender.com` (ou nome similar)

---

## ATUALIZAÇÕES FUTURAS

Para atualizar o app depois, basta fazer upload do `app.py` atualizado no GitHub.
O Render detecta automaticamente e faz o redeploy.

---

## CUSTO

| Item | Custo |
|------|-------|
| Render Free Tier | Grátis |
| Disco persistente (opcional) | ~$0,25/mês |
| API Anthropic (por consulta) | ~$0,02–0,10 por consulta |

> O plano gratuito do Render "dorme" após 15 min de inatividade.
> A primeira requisição após o sleep pode demorar ~30 segundos para acordar.
> Para uso contínuo, considere o plano Starter ($7/mês).

---

## RODAR LOCALMENTE (alternativa)

```bash
pip install flask anthropic reportlab
export ANTHROPIC_API_KEY="sk-ant-..."
python app.py
# Acesse: http://localhost:5001
```
