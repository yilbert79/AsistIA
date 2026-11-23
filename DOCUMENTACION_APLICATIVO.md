# Documentacion de funcionamiento de AsistIA

## 1. Objetivo

AsistIA es un prototipo de asistente academico virtual para TEINCO. Permite:

- Recibir preguntas estudiantiles por una interfaz web.
- Clasificar la consulta por tema y dependencia.
- Buscar una respuesta aprobada en la base de conocimiento.
- Generar una respuesta con Gemini cuando esta configurado.
- Derivar consultas sin respuesta suficiente a una dependencia.
- Registrar casos y datos de contacto.
- Permitir respuestas humanas.
- Revisar, aprobar o corregir respuestas.
- Mostrar informacion agregada en reportes.

El proyecto no debe considerarse listo para produccion sin una revision institucional de privacidad, seguridad, autorizacion y datos oficiales.

## 2. Arquitectura

```text
Navegador
  -> frontend/index.html
  -> frontend/script.js
  -> API FastAPI
       -> app/routers/chat.py
       -> app/routers/auth.py
       -> app/routers/admin.py
       -> app/services/ai_service.py
       -> SQLAlchemy
            -> SQLite o MySQL
```

Componentes principales:

- `frontend/index.html`: estructura de las vistas de chat, gestion y auditoria.
- `frontend/script.js`: comunicacion con la API y renderizado dinamico.
- `frontend/styles.css`: estilos de la interfaz.
- `backend/app/main.py`: crea la aplicacion FastAPI, configura CORS y sirve el frontend.
- `backend/app/database.py`: crea el motor de base de datos.
- `backend/app/models.py`: define las tablas.
- `backend/app/services/ai_service.py`: clasifica temas y busca informacion aprobada.
- `backend/app/services/bootstrap.py`: crea dependencias y datos iniciales.
- `backend/app/routers/chat.py`: endpoints publicos de chat y casos.
- `backend/app/routers/auth.py`: inicio de sesion.
- `backend/app/routers/admin.py`: gestion, auditoria y conocimiento.

## 3. Requisitos

- Python 3.11 o posterior.
- Dependencias de `backend/requirements.txt`.
- Navegador moderno.
- Una base SQLite local o MySQL opcional.
- Opcionalmente, una clave de Gemini con cuota disponible.

## 4. Instalacion local

Desde la carpeta del proyecto:

```powershell
cd asistia-chatbot\backend
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Editar `backend/.env` antes de iniciar:

```env
DATABASE_URL=sqlite:///./asistia.db
SEED_DEMO_DATA=true
SECRET_KEY=cambiar-por-un-secreto-unico
AI_PROVIDER=mock
GEMINI_API_KEY=
GEMINI_MODEL=gemini-3.8-flash
```

Iniciar el servidor:

```powershell
python -m uvicorn app.main:app --reload
```

Acceder a:

- Interfaz: `http://127.0.0.1:8000/`
- Documentacion Swagger: `http://127.0.0.1:8000/docs`
- Estado del servicio: `http://127.0.0.1:8000/api/v1/health`

## 5. Configuracion de Gemini

La clave se configura en `backend/.env`:

```env
AI_PROVIDER=gemini
GEMINI_API_KEY=<clave_nueva>
GEMINI_MODEL=gemini-3.8-flash
```

La clave no debe compartirse ni almacenarse en Git. Para verificarla:

```powershell
cd backend
py -3 -c "from app.config import settings; from google import genai; r=genai.Client(api_key=settings.gemini_api_key.strip()).models.generate_content(model=settings.gemini_model.strip(), contents='Responde solamente: OK'); print(r.text)"
```

Errores comunes:

- `401/403`: clave invalida, revocada o sin acceso.
- `429`: cuota agotada o limites de frecuencia excedidos.
- `404`: el nombre del modelo no esta disponible.
- Sin clave: se utiliza la respuesta aprobada o se deriva si no existe coincidencia.

Revocar una clave expuesta es obligatorio. Una clave nueva no debe publicarse en mensajes, capturas, archivos compartidos ni commits.

## 6. Flujo de una consulta

1. El usuario escribe una pregunta.
2. `classify_topic()` detecta el tema.
3. El tema se relaciona con una dependencia.
4. `find_article()` consulta los artículos activos y calcula coincidencias.
5. Si existe coincidencia suficiente, recupera la respuesta aprobada.
6. En modo Gemini, la respuesta aprobada y las instrucciones se envian al modelo.
7. Si Gemini falla o supera los limites de cuota, se usa la respuesta aprobada como respaldo.
8. Si no existe una respuesta aprobada:
   - Se crea un caso.
   - Se asigna una dependencia.
   - Se informa al usuario que requiere revision humana.
9. El usuario puede registrar opcionalmente correo o telefono con consentimiento.

## 7. Clasificacion por dependencia

Las palabras clave principales se agrupan asi:

| Tema | Dependencia |
|---|---|
| Admisiones e inscripciones | Admisiones y Comercial |
| Certificados, notas y homologacion | Registro y Control |
| Bienestar y psicologia | Bienestar Institucional |
| Horarios y clases | Coordinacion Academica |
| Pagos y facturacion | Tesoreria y Facturacion |
| Grado e investigacion | Investigacion y Opciones de Grado |
| Temas generales | Atencion General |

La clasificacion puede ser reemplazada por una seleccion manual enviando `department_id` en la solicitud.

## 8. Base de conocimiento

Cada respuesta aprobada contiene:

- Pregunta o palabras clave.
- Respuesta oficial.
- Fuente oficial.
- Dependencia asociada o alcance global.
- Estado activo.
- Usuario que aprobó, si proviene de auditoria.

La carga inicial crea artículos de demostracion para pruebas. Antes de usar el aplicativo con usuarios reales, deben reemplazarse por informacion aprobada por TEINCO.

La busqueda SQL selecciona:

```sql
SELECT *
FROM base_conocimiento
WHERE active = true;
```

La coincidencia se calcula por palabras normalizadas y no por coincidencia exacta. Si no supera el umbral definido en `find_article()`, se deriva a revision humana.

## 9. Uso de la interfaz

### Chat

- Escribe una pregunta o selecciona un tema.
- Recibe una respuesta aprobada o genera un caso humano.
- Para seguimiento, completa el formulario de contacto y acepta el consentimiento.
- Si la consulta ya tiene caso, puede consultar su estado con el enlace interno generado por el prototipo.

### Gestion por division

Inicia sesion con una cuenta autorizada.

Cuenta local de demostracion:

- Correo: `admin@asistia.example.com`
- Contraseña: definida por `DEV_ADMIN_PASSWORD`

Las acciones disponibles dependen del rol:

- `DIVISION_AGENT`: gestiona casos de su dependencia.
- `DIVISION_LEADER`: responde y revisa respuestas de su dependencia.
- `SUPERADMIN`: gestiona toda la plataforma.

Desde Gestion se pueden:

- Consultar casos pendientes.
- Consultar casos respondidos.
- Seleccionar una consulta.
- Redactar una respuesta humana.
- Registrar el seguimiento.

### Auditoria y aprendizaje

Solo disponible para `DIVISION_LEADER` y `SUPERADMIN`.

Permite:

- Consultar métricas.
- Revisar respuestas por dependencia.
- Aprobar una respuesta.
- Guardar una correccion.
- Rechazar una respuesta.
- Agregar o editar conocimiento oficial, sus preguntas clave y sus fuentes.
- Desactivar respuestas que hayan quedado obsoletas y reactivar contenido vigente.
- Visualizar artículos activos e inactivos.
- Consultar temas y dependencias mas frecuentes.

Al guardar una corrección o editar un artículo, el contenido actualizado se utiliza en las consultas futuras cuando coincide con la pregunta. Los artículos desactivados se conservan para auditoría, pero no se consideran al generar respuestas. Los líderes pueden administrar únicamente el conocimiento de su dependencia; el superadministrador puede administrar todos los alcances.

Esta intervención no vuelve a entrenar ni modifica los parámetros del modelo Gemini: ajusta la información institucional que el sistema recupera y proporciona al modelo como contexto.

## 10. Cuenta local y autenticacion

Los usuarios administradores se almacenan en la base.

- Las contraseñas usan PBKDF2-HMAC-SHA256 con 310000 iteraciones.
- Las sesiones usan tokens firmados con `SECRET_KEY`.
- Los tokens caducan segun `TOKEN_TTL_MINUTES`.
- Las rutas administrativas validan autenticacion y roles.
- Los lideres solo pueden operar sobre su dependencia.

Configuraciones recomendadas:

- Cambiar `SECRET_KEY`.
- Cambiar `DEV_ADMIN_PASSWORD`.
- Cambiar la contraseña de demostracion antes de cualquier despliegue.
- No reutilizar una clave o contraseña publicada.

## 11. Base de datos

### SQLite

Configuracion predeterminada:

```env
DATABASE_URL=sqlite:///./asistia.db
```

La base se crea al iniciar el servidor. Los datos de demostracion se generan segun `SEED_DEMO_DATA`.

### MySQL

Desde la raiz del proyecto:

```powershell
docker compose up -d db
```

Ejemplo de configuracion:

```env
DATABASE_URL=mysql+pymysql://asistia_dev:asistia_dev_password@127.0.0.1:3307/asistia_teinco_db
```

El esquema se crea automaticamente con SQLAlchemy.

## 12. Datos registrados

Tablas principales:

- `dependencias`: areas de atencion.
- `usuarios_admin`: cuentas internas.
- `conversaciones`: sesiones publicas.
- `mensajes_chat`: preguntas y respuestas.
- `contactos_usuario`: datos de seguimiento.
- `respuestas_division`: respuestas humanas.
- `validaciones_lider`: aprobaciones y correcciones.
- `base_conocimiento`: respuestas aprobadas.
- `notificaciones`: registros de correo y estado.

Los datos de contacto requieren consentimiento antes de almacenarse.

## 13. Endpoints principales

| Metodo | Endpoint | Uso |
|---|---|---|
| GET | `/api/v1/health` | Estado del servicio |
| GET | `/api/v1/dependencies` | Directorio de dependencias |
| POST | `/api/v1/chat/messages` | Enviar una consulta |
| POST | `/api/v1/chat/cases/{id}/contact` | Registrar seguimiento |
| POST | `/api/v1/chat/cases/{id}/status` | Consultar estado |
| POST | `/api/v1/auth/login` | Iniciar sesion |
| GET | `/api/v1/admin/cases` | Consultar casos |
| POST | `/api/v1/admin/cases/{id}/responses` | Responder un caso |
| GET | `/api/v1/admin/reviews` | Consultar respuestas para revision |
| POST | `/api/v1/admin/reviews/{id}` | Aprobar, corregir o rechazar |
| GET | `/api/v1/admin/departments` | Consultar dependencias |
| GET | `/api/v1/admin/knowledge` | Consultar conocimiento |
| POST | `/api/v1/admin/knowledge` | Agregar conocimiento |
| GET | `/api/v1/reports/dashboard` | Consultar metricas |

La referencia interactiva completa esta disponible en `/docs`.

## 14. Pruebas

Ejecutar desde `backend/`:

```powershell
python -m pytest
```

Las pruebas cubren:

- Estado de salud.
- Respuesta de conocimiento.
- Creacion de casos humanos.
- Contacto por correo o telefono.
- Gestion de respuestas.
- Directorio de dependencias.
- Revisión de auditoria.
- Artículos aprobados.

Se recomienda agregar pruebas al cambiar reglas de coincidencia, roles, protecciones o estructura de la base.

## 15. Evaluacion del aplicativo

### Modulos evaluados

| Modulo | Tecnologia o alcance |
|---|---|
| Chatbot web | HTML5, CSS y JavaScript |
| API REST | FastAPI |
| Base de datos | MySQL como motor evaluado; el valor de `DATABASE_URL` determina el motor activo. La configuracion de ejemplo usa SQLite. |
| Inteligencia artificial | Integracion con Gemini |

### Tipos de pruebas

- **Pruebas funcionales:** flujos principales del chat, gestion y auditoria.
- **Validacion de historias:** HU-01, HU-04 y HU-05.
- **Seguridad:** pruebas de prompt injection y validacion/sanitizacion de entradas para reducir riesgos de inyeccion SQL.
- **Rendimiento:** medicion de latencia de IA con objetivo menor a 3,0 segundos.
- **Usabilidad:** revision del diseno responsivo en dispositivos moviles.

Las pruebas de seguridad descritas son verificaciones de comportamiento; no sustituyen una auditoria de seguridad especializada ni demuestran por si solas que el sistema sea invulnerable.

### Resultados reportados

Los siguientes resultados fueron proporcionados para la evaluacion del proyecto y se registran como resultados reportados, no como una ejecucion independiente de esta documentacion:

| Elemento | Resultado reportado |
|---|---|
| HU-01 | 100 % OK |
| HU-04 | 100 % OK |
| HU-05, aprobacion «Chulito» | OK |
| Latencia promedio de IA | 1,8 s |
| Objetivo de latencia | Menos de 3,0 s |

No se proporcionaron resultados numericos o criterios de aprobacion individuales para prompt injection, validacion de entradas SQL y usabilidad movil. Para completar el informe, registrar casos ejecutados, ambiente, fecha, dispositivo/navegador, numero de mediciones y resultados observados. La latencia puede variar por red, disponibilidad del proveedor y cuota de Gemini.

## 16. Control de calidad antes de desplegar

Antes de publicar el sistema se debe:

- Sustituir todos los datos de demostracion por contenido aprobado.
- Definir responsables institucionales por dependencia.
- Configurar copias de seguridad.
- Configurar HTTPS y dominios reales.
- Configurar correo SMTP autorizado.
- Cambiar secretos y contraseñas.
- Restringir CORS a los dominios reales.
- Revisar privacidad y consentimiento.
- Limitar intentos de inicio de sesion y abuso publico.
- Revisar registros y datos personales.
- Definir una politica de conservacion de casos.
- Validar el comportamiento de Gemini contra respuestas institucionales.
- Realizar pruebas de seguridad y permisos.
- Definir un proceso formal de auditoria de contenido.

## 17. Riesgos conocidos del prototipo

- Las respuestas iniciales son contenido de demostracion.
- La clasificacion es por palabras clave.
- Gemini puede tener cuotas o indisponibilidad.
- El flujo usa SQLite por defecto.
- El correo puede quedar simulando una operacion si SMTP no esta configurado.
- Los canales demo requieren validacion institucional.
- CORS y credenciales deben endurecerse para produccion.
