# 💎 Sistema POS para Joyería

Sistema completo de punto de venta especializado para joyerías con gestión de inventario, ventas, créditos y reportes.

## ✨ Características Principales

### 💰 Sistema de Precios Dinámicos
- Tasas de metal configurables (10K, 14K, 18K, Oro Italiano, Plata Gold/Silver)
- Cálculo automático: `Precio = (Tasa × Peso) - Descuento%`
- Opción de precio manual para casos especiales
- Recálculo automático al actualizar tasas de metal

### 🏪 Punto de Venta
- Tipos de venta: Contado y Crédito
- Selección de vendedor
- Cálculo automático de utilidad
- Información de cliente para ventas a crédito
- Múltiples métodos de pago

### 📦 Gestión de Inventario
- Productos con campos específicos para joyería:
  - Código, Marca, Modelo, Color
  - Quilataje, Base, Tipo de Joya, Talla
  - Peso en gramos, Descuento, Costo
- Importación masiva desde Excel
- Historial de movimientos (entradas/salidas)
- Control de stock

### 💳 Sistema de Créditos
- Gestión de pagos a plazos (abonos)
- Estados: Pendiente/Pagado
- Filtros por estado y cliente
- Impresión de recibos de pago

### 📊 Reportes
- **Corte de Caja**: Diario/Semanal/Mensual
  - Ventas por método de pago
  - Total de abonos
  - Efectivo y tarjeta
  - Utilidad total
- Ventas por vendedor
- Historial de ventas completo

### 🔐 Multi-Tenancy
- Sistema multi-inquilino
- Datos aislados por tenant
- Control de acceso por roles

## 🚀 Inicio Rápido

### Con Docker (Recomendado)

```bash
# Clonar repositorio
git clone <tu-repo>
cd erp-pos

# Iniciar servicios
docker-compose --profile dev up -d

# Acceder a la aplicación
# Frontend: http://localhost:5173
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Credenciales de Demo
- **Email**: owner@demo.com
- **Password**: secret123
- **Tenant**: demo

### Sin Docker

#### Backend
```bash
cd backend
pip install -r requirements.txt
python recreate_db.py  # Inicializar DB
uvicorn app.main:app --reload
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

## 📤 Importar Productos desde Excel

1. Ve a **"Productos/Joyería"**
2. Click en **"📥 Descargar Plantilla Excel"**
3. Llena la plantilla con tus productos
4. Click en **"📤 Importar Excel"**
5. Selecciona modo: **Agregar** o **Reemplazar**
6. Carga tu archivo y listo!

### Campos de la Plantilla
- `codigo` ⭐ (requerido)
- `name` ⭐ (requerido)
- `quilataje` (10k, 14k, 18k, oro_italiano, plata_gold, plata_silver)
- `peso_gramos` (para cálculo automático)
- `descuento_porcentaje` (0-100)
- `precio_manual` (dejar vacío para cálculo automático)
- `costo`, `stock`, `marca`, `modelo`, `color`, `tipo_joya`, `talla`

## 🌐 Deploy a Producción

### Railway (Recomendado)

Ver guía completa en [RAILWAY_DEPLOY.md](./RAILWAY_DEPLOY.md)

**Pasos rápidos:**
1. Sube tu código a GitHub
2. Crea proyecto en [Railway.app](https://railway.app)
3. Conecta tu repo
4. Configura 3 servicios: PostgreSQL, Backend, Frontend
5. Configura variables de entorno
6. ¡Deploy automático!

### Variables de Entorno

#### Backend
```env
DATABASE_URL=postgresql://...
SECRET_KEY=tu-secret-key
ALLOWED_ORIGINS=https://tu-frontend.railway.app
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

#### Frontend
```env
VITE_API_URL=https://tu-backend.railway.app
```

## 🏗️ Estructura del Proyecto

```
erp-pos/
├── backend/              # FastAPI Backend
│   ├── app/
│   │   ├── core/        # Config, security, database
│   │   ├── models/      # SQLAlchemy models
│   │   ├── routes/      # API endpoints
│   │   └── services/    # Business logic
│   ├── requirements.txt
│   └── railway.toml
│
├── frontend/            # React + Vite Frontend
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── pages/       # Page components
│   │   └── utils/       # API client
│   ├── package.json
│   └── railway.toml
│
└── docker-compose.yml
```

## 🛠️ Tecnologías

### Backend
- **FastAPI** - Framework web moderno
- **SQLAlchemy** - ORM
- **PostgreSQL** - Base de datos
- **JWT** - Autenticación
- **Pandas/OpenPyXL** - Importación Excel

### Frontend
- **React** - UI Library
- **TypeScript** - Tipado estático
- **Vite** - Build tool
- **Tailwind CSS** - Estilos
- **Axios** - HTTP client

## 📚 API Documentation

Una vez corriendo el backend, visita:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend (si se configura)
cd frontend
npm test
```

## 🔒 Seguridad

- Autenticación JWT
- Hashing de contraseñas con bcrypt
- CORS configurado
- Validación de datos con Pydantic
- Aislamiento multi-tenant

## 🤝 Contribuir

1. Fork el proyecto
2. Crea tu rama (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto es privado y propietario.

## 📞 Soporte

Para soporte, contacta a [tu email/contacto]

---

**¡Hecho con ❤️ para joyerías!** 💎
