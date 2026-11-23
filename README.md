# AsistIA para pruebas locales

Consulta la [documentación funcional y técnica completa](./DOCUMENTACION_APLICATIVO.md).

Prototipo web para preguntas institucionales, derivación a una dependencia, respuesta humana y revisión de conocimiento. El proyecto inicia con SQLite y un proveedor de IA simulado para que puedas probar el flujo sin credenciales externas. También incluye configuración para MySQL y Gemini.

> Los contactos de dependencias usan el dominio reservado `.invalid`; los artículos de conocimiento son de demostración. No son datos oficiales de TEINCO. Sustitúyelos por información aprobada antes de usar el sistema con estudiantes o funcionarios.

## Requisitos

- Python 3.11 o posterior.
- Windows PowerShell, macOS o Linux.
- Para usar MySQL de manera local: Docker Desktop o una instalación compatible de MySQL.
- Para respuestas generadas con Gemini: una clave de API configurada en el entorno.

## Inicio rápido en Windows

Desde la carpeta raíz del proyecto:

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

Abre `http://127.0.0.1:8000/` para usar la interfaz y `http://127.0.0.1:8000/docs` para consultar la API. La base SQLite se crea en `backend/asistia.db` al iniciar el servidor.

En Linux o macOS activa el entorno con `source .venv/bin/activate`.

## Cuenta local de demostración

- Correo: `admin@asistia.example.com`
- Contraseña: `AsistIA-demo-2026`

La cuenta es exclusivamente para desarrollo local. Cambia `DEV_ADMIN_PASSWORD` y `SECRET_KEY` antes de cualquier despliegue. No reutilices la clave de ejemplo.

## Abrir la interfaz

La interfaz está organizada en `frontend/index.html`, `frontend/styles.css` y `frontend/script.js`. En el chat, las consultas se clasifican automáticamente; si una requiere seguimiento humano, puedes dejar un correo electrónico o un número de teléfono en un único campo. Puedes abrir `frontend/index.html` directamente para explorar el modo de demostración. Para probar la conexión real con la API, inicia el backend y entra por `http://127.0.0.1:8000/`.

## Probar el flujo en el navegador

1. En Chat, pregunta `¿Qué es AsistIA?`. El servidor responde desde un artículo de demostración.
2. Envía una pregunta que no esté en el conocimiento, por ejemplo `Necesito revisar un caso particular de mi matrícula`. El sistema crea un caso y muestra el formulario de contacto opcional.
3. Si quieres seguimiento, registra un correo y acepta su uso. Luego podrás consultar el estado del caso desde el mismo navegador.
4. En Gestión interna, inicia sesión con la cuenta local, abre el caso y registra una respuesta.
5. Vuelve a Chat y selecciona `Consultar estado del caso` para ver la respuesta. Si SMTP está configurado, también llegará al correo registrado.
6. En Reportes, consulta las métricas. Para revisar respuestas, inicia sesión como líder o superadministrador.
7. El superadministrador puede crear cuentas de funcionarios y líderes desde `POST /api/v1/admin/users` en Swagger. Asigna el `department_id` correspondiente.

## Ejecutar las pruebas automatizadas incluidas

Desde `backend/` y con el entorno virtual activo:

```powershell
python -m pytest
```

Las pruebas usan SQLite y el proveedor simulado. No requieren una clave de Gemini ni correo SMTP.

## Usar MySQL en lugar de SQLite

1. Desde la raíz, inicia MySQL de desarrollo:

```powershell
docker compose up -d db
```

2. En `backend/.env`, cambia `DATABASE_URL` por:

```env
DATABASE_URL=mysql+pymysql://asistia_dev:asistia_dev_password@127.0.0.1:3307/asistia_teinco_db
```

El esquema se crea con SQLAlchemy al iniciar la API. `database/schema.sql` documenta el mismo modelo para revisión o ejecución manual.

## Activar Gemini

El SDK de Google GenAI está incluido. En `backend/.env`, configura:

```env
AI_PROVIDER=gemini
GEMINI_API_KEY=tu_clave
GEMINI_MODEL=gemini-3.8-flash
```

Gemini recibe la pregunta y un artículo aprobado que coincide con ella. Si no existe un artículo apropiado, AsistIA deriva el caso en vez de pedirle al modelo que invente una respuesta. En modo `mock`, las consultas no se envían a un proveedor externo. La API puede cambiar; consulta la documentación oficial antes de actualizar el modelo o el SDK.

## Correo de prueba

Sin servidor SMTP configurado, las notificaciones quedan registradas con estado `SIMULATED`. Para probar correo, completa `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` y `SMTP_USE_TLS` en `backend/.env`, y configura únicamente direcciones institucionales que TEINCO autorice para recibir notificaciones. El prototipo implementa correo; no integra WhatsApp ni Telegram.

## Estructura

```text
asistia-chatbot/
├── backend/app/       API FastAPI, modelos, seguridad, servicios y rutas
├── backend/tests/     Pruebas iniciales de humo
├── frontend/index.html Estructura de la interfaz
├── frontend/styles.css Estilos de la interfaz
├── frontend/script.js Lógica de la interfaz
├── database/          DDL de referencia para MySQL
├── docker-compose.yml MySQL de desarrollo opcional
└── README.md
```

## Alcance del prototipo

- Chat público y clasificación inicial por palabras clave/dependencia seleccionada.
- Respuesta de demostración o respuesta Gemini basada en conocimiento revisado.
- Casos pendientes y registro de contacto con consentimiento.
- Acceso por cuenta, rol y dependencia para gestión interna.
- Respuesta humana, auditoría de validación y alta de conocimiento aprobado.
- Reportes agregados por estado, tema y dependencia.
- Notificaciones por correo cuando SMTP esté configurado.

Antes de usarlo en producción faltan, entre otros, revisión de privacidad institucional, gestión formal de cuentas, controles contra abuso del endpoint público, pruebas de seguridad, configuración de copias de seguridad y despliegue. El proyecto está preparado para pruebas locales, no para publicar sin esa revisión.
