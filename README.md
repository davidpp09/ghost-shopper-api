# 👻 Ghost Shopper

> **LatAm GTM Hackathon — CDMX, Mayo 2026**  
> *¿Cómo atiende tu inmobiliaria a un cliente que llama hoy? Lo sabemos en minutos.*

---

## ¿Qué es?

**Ghost Shopper** es un agente de IA que se hace pasar por un cliente potencial, llama a inmobiliarias de forma automática, y genera un reporte de qué tan bien (o mal) los atendieron.

Sin visitantes misteriosos. Sin encuestas manuales. Sin sesgo humano.  
Solo llamadas reales, análisis de IA y un score del 0 al 100.

---

## El problema

Los equipos de ventas de inmobiliarias pierden deals todos los días por:
- No contestar a tiempo
- No dar precios cuando el cliente pregunta
- No hacer seguimiento
- No intentar cerrar

Nadie lo sabe porque **nadie lo mide**. Ghost Shopper lo mide.

---

## ¿Cómo funciona?

```
Webscraper detecta inmobiliaria
         ↓
POST /bot/call  { phone, context }
         ↓
IA arma el perfil de la empresa
         ↓
ElevenLabs marca el número → suena el teléfono 📞
         ↓
El agente de voz conversa como cliente real
         ↓
Groq analiza la llamada con IA
         ↓
Score + reporte automático generado
```

---

## Lo que evalúa la IA

| Criterio | Descripción |
|---|---|
| ✅ Respondieron | ¿Contestaron la llamada? |
| 💰 Dieron precio | ¿Informaron el costo sin rodeos? |
| 📅 Intentaron cerrar | ¿Propusieron agendar visita? |
| 📞 Hicieron seguimiento | ¿Llamaron de vuelta? |
| 🙋 Usaron el nombre | ¿Personalizaron la atención? |
| ⏱️ Tiempo de respuesta | Penalización si tardaron más de 30 min |
| 🏆 Score global | 0–100 con calificación A–F |

---

## Stack

| Capa | Tecnología |
|---|---|
| API | FastAPI + Python |
| Base de datos | Supabase (PostgreSQL) |
| Voz / Llamadas | ElevenLabs Conversational AI + Twilio |
| IA de análisis | Groq — llama-3.3-70b-versatile |
| IA de extracción | Groq — llama-3.1-8b-instant |
| Automatización | Make |
| Deploy | Railway |

---

## Endpoints principales

```
POST /bot/call                          → dispara todo el flujo con phone + context
POST /interactions/                     → lanza llamada a campaña existente
GET  /dashboard/summary                 → KPIs globales
GET  /campaigns/{id}                    → detalle de campaña
GET  /interactions/campaign/{id}        → interacciones + scores
GET  /reports/campaign/{id}             → reporte IA con métricas
POST /reports/generate/{campaign_id}    → genera reporte nuevo con IA
PATCH /companies/{id}                   → actualiza datos de empresa
```

Documentación interactiva completa en `/docs`.

---

## Ejemplo real

**Input:**
```bash
POST /bot/call
{
  "phone": "+525529196649",
  "context": "Inmobiliaria Residencial del Valle, depas en Roma Norte CDMX"
}
```

**Output (después de la llamada):**
```json
{
  "company_name": "Residencial del Valle",
  "quality_score": 34,
  "calificacion": "F",
  "responded": true,
  "gave_price": false,
  "attempted_close": false,
  "veredicto": "Atención reactiva: responden pero no venden.",
  "oportunidad_principal": "Dar precios proactivamente y agendar visita.",
  "reasoning": "La empresa contestó pero evadió dar precios y no intentó cerrar en ningún momento de la conversación."
}
```

---

## Correr localmente

```bash
# 1. Clonar y entrar
git clone https://github.com/davidpp09/ghost-shopper
cd ghost-shopper

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables de entorno
cp .env.example .env
# → llenar SUPABASE_URL, SUPABASE_KEY, GROQ_API_KEY, ELEVENLABS_*

# 4. Levantar
uvicorn main:app --reload
```

---

## Variables de entorno

| Variable | Descripción |
|---|---|
| `SUPABASE_URL` | URL del proyecto Supabase |
| `SUPABASE_KEY` | Service role key |
| `GROQ_API_KEY` | API key de Groq |
| `ELEVENLABS_API_KEY` | API key de ElevenLabs |
| `ELEVENLABS_AGENT_ID` | ID del agente de voz |
| `ELEVENLABS_PHONE_NUMBER_ID` | ID del número Twilio en ElevenLabs |
| `ENABLE_SCHEDULER` | `true` para scoring automático cada 10 min |

---

## El equipo

Construido en 24 horas en el **LatAm GTM Hackathon — CDMX 2026**

| Nombre |
|---|
| Luis Ernesto Merida de Leon |
| Hector Said Ferreira Rodríguez |
| Tlahuel Mendez Samuel Oswaldo |
| Peña Pedraza David |
| Paolo Flores |

---

*Hecho con 🌶️ en México*
