# 🛡️ TuriSafe — Mapeo Inteligente de Zonas de Riesgo

**Build with AI · GDG La Paz · Bolivia**

---

## ¿Cómo ejecutar el proyecto?

### 1. Instalar dependencias

```bash
pip install flask
```

### 2. Ejecutar la aplicación

```bash
python app.py
```

### 3. Abrir en el navegador

Ve a: **http://localhost:5000**

---

## Usuarios de prueba

| Rol           | Email                   | Contraseña  |
|---------------|-------------------------|-------------|
| Administrador | admin@turisafe.bo       | admin123    |
| Policía       | policia@turisafe.bo     | policia123  |
| Turista       | turista@demo.com        | turista123  |

---

## Novedades v2.0

- **Login rediseñado** con tabs: Iniciar sesión / Crear cuenta
- **Auto-registro público** para turistas y policías
- **Mapa inteligente** con heatmap de densidad de incidentes
- **Chat IA** integrado: responde preguntas sobre zonas de riesgo
- **Filtros interactivos** como chips visuales
- **Marcadores personalizados** con color según nivel de riesgo
- **Animación flyTo** al seleccionar zona del panel lateral

---

## Módulos del sistema

| Módulo | Descripción | Ruta |
|--------|-------------|------|
| 1. Gestión de usuarios | Login, registro, roles, admin | `/login`, `/registro`, `/usuarios` |
| 2. Registro de casos | Reportar incidentes | `/casos`, `/casos/nuevo` |
| 3. Visualización en mapa | Mapa + heatmap + chat IA | `/mapa` |
| 4. Reportes y análisis | Estadísticas, exportar | `/estadisticas` |

---

## Estructura del proyecto

```
turisafe/
├── app.py                  ← Backend principal (Flask)
├── requirements.txt        ← Dependencias
├── README.md
├── .gitignore
├── data/
│   └── db.json             ← Base de datos JSON
└── templates/
    ├── base.html           ← Layout general
    ├── login.html          ← Login + registro (v2)
    ├── mapa.html           ← Mapa inteligente + chat IA (v2)
    ├── casos.html          ← Lista de casos
    ├── nuevo_caso.html     ← Formulario de reporte
    ├── estadisticas.html   ← Dashboard
    └── usuarios.html       ← Gestión de usuarios
```

---

## API disponible

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/zonas` | GET | Zonas de riesgo (filtrable por `?nivel=alto`) |
| `/api/casos` | GET | Todos los casos para el mapa |
| `/api/exportar/json` | GET | Exportar reporte en JSON |
| `/registro` | POST | Auto-registro público |

---

## Tecnologías

- **Backend**: Python + Flask
- **Base de datos**: JSON (migrable a PostgreSQL/MySQL)
- **Mapa**: Leaflet.js + Leaflet.heat + OpenStreetMap
- **Chat IA**: Motor contextual (listo para conectar Gemini API)
- **Frontend**: HTML5 + CSS3 puro
- **Metodología**: RUP
