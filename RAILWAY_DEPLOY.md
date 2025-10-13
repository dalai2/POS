# 🚂 Deploy to Railway - Guía Paso a Paso

## 📋 Prerequisitos

1. Cuenta en [Railway.app](https://railway.app)
2. GitHub account (opcional pero recomendado)
3. Railway CLI (opcional): `npm i -g @railway/cli`

## 🚀 Opción 1: Deploy desde GitHub (Recomendado)

### 1. Sube tu código a GitHub

```bash
git init
git add .
git commit -m "Initial commit - Jewelry Store POS"
git branch -M main
git remote add origin <TU_REPO_URL>
git push -u origin main
```

### 2. En Railway Dashboard

1. **Ve a [Railway.app](https://railway.app)** y haz login
2. **Click en "New Project"**
3. **Selecciona "Deploy from GitHub repo"**
4. **Autoriza Railway** a acceder a tu repo
5. **Selecciona tu repositorio**

### 3. Configura los Servicios

Railway detectará automáticamente los servicios. Necesitas crear **3 servicios**:

#### 🗄️ **Servicio 1: PostgreSQL Database**
1. Click en **"+ New"** → **"Database"** → **"PostgreSQL"**
2. Railway creará la base de datos automáticamente
3. Copia la **DATABASE_URL** de las variables de entorno

#### 🔧 **Servicio 2: Backend (FastAPI)**
1. Click en **"+ New"** → **"GitHub Repo"** → Selecciona tu repo
2. En **Settings**:
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   
3. En **Variables**:
   ```
   DATABASE_URL = <Copia de tu servicio PostgreSQL>
   SECRET_KEY = <genera uno aleatorio>
   ACCESS_TOKEN_EXPIRE_MINUTES = 1440
   REFRESH_TOKEN_EXPIRE_MINUTES = 10080
   ALLOWED_ORIGINS = https://<TU_FRONTEND_URL>.railway.app,http://localhost:5173
   ```

4. En **Networking**:
   - **Generate Domain** para obtener una URL pública
   - Copia la URL (ej: `https://tu-backend.railway.app`)

#### 🎨 **Servicio 3: Frontend (React + Vite)**
1. Click en **"+ New"** → **"GitHub Repo"** → Selecciona tu repo
2. En **Settings**:
   - **Root Directory**: `frontend`
   - **Build Command**: `npm install && npm run build`
   - **Start Command**: `npm run preview -- --host 0.0.0.0 --port $PORT`

3. En **Variables**:
   ```
   VITE_API_URL = https://<TU_BACKEND_URL>.railway.app
   NODE_ENV = production
   ```

4. En **Networking**:
   - **Generate Domain** para obtener una URL pública

### 4. Actualiza las Variables de Entorno

Vuelve al **Backend** y actualiza `ALLOWED_ORIGINS`:
```
ALLOWED_ORIGINS = https://<TU_FRONTEND_URL>.railway.app
```

### 5. Inicializa la Base de Datos

Opción A - Desde Railway CLI:
```bash
railway login
railway link
railway run python backend/recreate_db.py
```

Opción B - Temporalmente agrega al start command del backend:
```bash
python recreate_db.py && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```
(Después de correr una vez, quita `python recreate_db.py &&`)

---

## 🚀 Opción 2: Deploy Directo (Sin GitHub)

### Usando Railway CLI:

```bash
# Instala Railway CLI
npm i -g @railway/cli

# Login
railway login

# Crea un nuevo proyecto
railway init

# Deploy Backend
cd backend
railway up

# Deploy Frontend
cd ../frontend
railway up
```

---

## 📊 Variables de Entorno Completas

### **Backend Service**
```env
DATABASE_URL=postgresql://user:pass@host:port/dbname
SECRET_KEY=<tu-secret-key-super-seguro>
ACCESS_TOKEN_EXPIRE_MINUTES=1440
REFRESH_TOKEN_EXPIRE_MINUTES=10080
ALLOWED_ORIGINS=https://tu-frontend.railway.app
```

### **Frontend Service**
```env
VITE_API_URL=https://tu-backend.railway.app
NODE_ENV=production
```

---

## ✅ Verificación

1. **Backend Health Check**: 
   - Visita: `https://tu-backend.railway.app/health`
   - Debe responder: `{"status": "ok"}`

2. **Frontend**:
   - Visita: `https://tu-frontend.railway.app`
   - Login con: `owner@demo.com` / `secret123`

3. **API Docs**:
   - Visita: `https://tu-backend.railway.app/docs`

---

## 🔒 Producción - Mejores Prácticas

1. **Genera un SECRET_KEY seguro**:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Cambia las credenciales por defecto**:
   - Email: `owner@demo.com`
   - Password: `secret123`

3. **Configura dominio personalizado** (opcional):
   - En Railway Settings → Domains
   - Agrega tu dominio custom

4. **Backups automáticos**:
   - Railway hace backups de PostgreSQL automáticamente
   - También puedes configurar backups manuales

---

## 🐛 Troubleshooting

### Error: "Application failed to respond"
- Verifica que el PORT sea `$PORT` (variable de Railway)
- Revisa los logs: `railway logs`

### Error: CORS
- Asegúrate que `ALLOWED_ORIGINS` incluye tu frontend URL
- Debe ser HTTPS en producción

### Error: Database connection
- Verifica que `DATABASE_URL` esté correctamente copiada
- Asegura que el servicio de PostgreSQL esté corriendo

### Frontend no carga datos
- Verifica `VITE_API_URL` apunte al backend correcto
- Debe incluir `https://` y NO terminar en `/`

---

## 💰 Costos

- **Hobby Plan**: $5/mes por servicio (después de trial)
- **Database**: Incluida en el plan
- **Bandwidth**: 100GB incluidos

Railway ofrece **$5 de crédito gratis** para empezar.

---

## 🔗 URLs Útiles

- Railway Dashboard: https://railway.app/dashboard
- Docs: https://docs.railway.app
- Status: https://status.railway.app

---

## 📝 Credenciales de Demo

Una vez desplegado:
- **Email**: owner@demo.com
- **Password**: secret123
- **Tenant**: demo

**¡Recuerda cambiar estas credenciales en producción!** 🔒

