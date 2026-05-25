# Ghost Shopper API — Documentación para Frontend

API que evalúa con IA cómo atienden las inmobiliarias a clientes potenciales (mystery shopping).
El flujo hace llamadas/WhatsApp automáticos, los analiza con IA y genera reportes por campaña.

---

## 1. Generalidades

### Base URL (local)
```
http://127.0.0.1:8000
```

### Documentación interactiva (Swagger)
La API expone su propia doc navegable y probable:
```
http://127.0.0.1:8000/docs
```

### Formato de respuesta
**TODAS** las respuestas vienen envueltas en este sobre:

**Éxito:**
```json
{
  "success": true,
  "status_code": 200,
  "data": { ... }      // aquí va el contenido real
}
```

**Error:**
```json
{
  "success": false,
  "status_code": 404,
  "error": "Mensaje describiendo el error"
}
```

> En los ejemplos de abajo solo se muestra el contenido de `data` para no repetir el sobre.

### Códigos de estado
| Código | Significado |
|---|---|
| 200 | OK |
| 201 | Creado |
| 400 | Petición mal formada |
| 404 | No encontrado |
| 422 | Datos inválidos / falta info para procesar |
| 500 | Error interno |
| 502 | Error de un servicio externo (IA / ElevenLabs) |

### Autenticación
Por ahora **no hay auth**. (Pendiente para producción.)

---

## 2. Modelos de datos

### Enums (valores permitidos)
| Campo | Valores |
|---|---|
| `campaign.status` | `active`, `paused`, `done` |
| `campaign.channels[]` | `call`, `whatsapp`, `email` |
| `interaction.channel` | `call`, `whatsapp`, `email` |
| `interaction.status` | `sent`, `answered`, `no_answer` |
| `message.role` | `agent` / `bot` = nuestro cliente incógnito · `user` / `human` = la empresa evaluada |
| `report.status` | `draft`, `sent` |
| `score.scored_by` | `ai`, `auto` |

### Entidades
**Company**
```json
{ "id": "uuid", "name": "str", "industry": "str|null", "website": "str|null",
  "phone": "str|null", "whatsapp_number": "str|null", "email": "str|null",
  "city": "str|null", "created_at": "datetime" }
```

**Campaign**
```json
{ "id": "uuid", "company_id": "uuid", "name": "str", "status": "active|paused|done",
  "channels": ["call","whatsapp"], "frequency_days": 7,
  "start_date": "date|null", "end_date": "date|null", "created_at": "datetime" }
```

**Interaction**
```json
{ "id": "uuid", "campaign_id": "uuid", "channel": "call|whatsapp|email",
  "status": "sent|answered|no_answer", "initiated_at": "datetime",
  "responded_at": "datetime|null", "response_time_sec": "int|null",
  "external_id": "str|null" }
```

**InteractionScore**
```json
{ "id": "uuid", "interaction_id": "uuid", "responded": true, "gave_price": false,
  "did_followup": false, "used_name": false, "attempted_close": false,
  "quality_score": 20, "reasoning": "explicación de la IA", "scored_by": "ai" }
```

**Report**
```json
{ "id": "uuid", "campaign_id": "uuid", "generated_at": "datetime",
  "period_start": "date|null", "period_end": "date",
  "metrics": { ... }, "findings": { ... }, "recommendations": { ... },
  "status": "draft|sent" }
```

**CallDetail**
```json
{ "id": "uuid", "interaction_id": "uuid", "duration_sec": 71, "outcome": "str|null",
  "transcript": [ { "role": "agent", "message": "...", "time_in_call_secs": 0, "interrupted": false } ] }
```

**Message**
```json
{ "id": "uuid", "interaction_id": "uuid", "role": "bot|human", "content": "str",
  "channel": "whatsapp", "sent_at": "datetime" }
```

---

## 3. Endpoints

### 🏠 DASHBOARD

#### `GET /dashboard/summary`
KPIs globales para el home.
```json
{
  "total_companies": 2, "total_campaigns": 2, "active_campaigns": 1,
  "total_interactions": 19, "scored_interactions": 3, "pending_scoring": 16,
  "avg_quality_score": 28.7, "response_rate_pct": 100.0, "total_reports": 1,
  "interactions_by_channel": { "call": 10, "whatsapp": 9 }
}
```

---

### 🏢 COMPANIES

#### `GET /companies/`
Lista de empresas. Query: `?limit=50&offset=0`
```json
{ "items": [ { "id": "...", "name": "Inmobiliaria Test", "phone": "+52..." } ],
  "limit": 50, "offset": 0 }
```

#### `GET /companies/{company_id}`
Empresa + sus campañas anidadas.
```json
{ "id": "...", "name": "Inmobiliaria Test", "phone": "+52...",
  "campaigns": [ { "id": "...", "name": "Campaña Q2", "status": "active" } ] }
```

#### `POST /companies/`  → 201
```json
{ "name": "Inmobiliaria Test", "phone": "+525529196649",
  "whatsapp_number": "+52...", "email": "info@test.com", "city": "CDMX" }
```
Solo `name` es obligatorio.

---

### 📋 CAMPAIGNS

#### `GET /campaigns/`
Lista de campañas. Query: `?limit=50&offset=0`
```json
{ "items": [ { "id": "...", "company_id": "...", "name": "Campaña Q2",
  "status": "active", "channels": ["call","whatsapp"], "companies": { "name": "..." } } ],
  "limit": 50, "offset": 0 }
```

#### `GET /campaigns/{campaign_id}`
Campaña + empresa + interacciones.
```json
{ "id": "...", "name": "Campaña Q2", "status": "active",
  "companies": { "id": "...", "name": "Inmobiliaria Test" },
  "interactions": [ { "id": "...", "channel": "call", "status": "answered" } ] }
```

#### `POST /campaigns/`  → 201
```json
{ "company_id": "uuid-de-la-empresa", "name": "Campaña Q2",
  "channels": ["call","whatsapp"], "frequency_days": 7,
  "start_date": "2026-06-01", "end_date": "2026-06-30" }
```
Obligatorios: `company_id`, `name`. `status` default = `paused`.

---

### 🔄 INTERACTIONS

#### `GET /interactions/campaign/{campaign_id}`
Interacciones de una campaña, **cada una con su score anidado** (para la tabla principal).
```json
[
  { "id": "...", "channel": "call", "status": "answered",
    "initiated_at": "2026-05-25T00:03:40Z",
    "interaction_scores": [ { "quality_score": 20, "responded": true, "reasoning": "..." } ] },
  { "id": "...", "channel": "whatsapp", "status": "no_answer",
    "interaction_scores": [] }
]
```
> `interaction_scores` es un array: vacío si aún no se ha evaluado, con 1 objeto si ya.

#### `GET /interactions/{interaction_id}`
Detalle + mensajes (útil para whatsapp).
```json
{ "id": "...", "channel": "whatsapp", "status": "answered",
  "campaigns": { "name": "..." },
  "messages": [ { "role": "bot", "content": "hola, busco depa...", "sent_at": "..." },
                { "role": "human", "content": "claro, ¿presupuesto?", "sent_at": "..." } ] }
```

#### `POST /interactions/`  → 201  ⭐ (dispara la evaluación)
```json
{ "campaign_id": "uuid-de-la-campaña", "channel": "call" }
```
Si `channel = "call"` **lanza la llamada automáticamente** y devuelve también:
```json
{ "id": "...", "channel": "call", "status": "sent",
  "call": { "conversation_id": "conv_...", "to_number": "+52...", "status": "calling" } }
```

---

### 🤖 INTERACTION SCORES (análisis IA)

#### `GET /interaction-scores/interaction/{interaction_id}`
Score de una interacción + la interacción anidada.
```json
[ { "id": "...", "interaction_id": "...", "responded": true, "gave_price": false,
    "did_followup": false, "used_name": false, "attempted_close": false,
    "quality_score": 20, "reasoning": "La empresa respondió pero nunca dio precio ni intentó cerrar.",
    "scored_by": "ai",
    "interactions": { "channel": "call", "campaigns": { "name": "..." } } } ]
```

#### `POST /interaction-scores/analyze/{interaction_id}`  → 201
Analiza UNA interacción a mano (normalmente es automático). Devuelve el score creado.

#### `POST /interaction-scores/run-pending`
Evalúa **todas** las pendientes que ya estén listas (lo mismo que corre el scheduler solo).
```json
{ "scored":  [ { "id": "...", "quality_score": 45 } ],
  "skipped": [ { "id": "...", "reason": "conversación whatsapp aún activa" } ],
  "errors":  [] }
```

---

### 📊 REPORTS

#### `GET /reports/campaign/{campaign_id}`
Reportes de una campaña.
```json
[ {
  "id": "...", "campaign_id": "...", "status": "draft", "generated_at": "...",
  "metrics": {
    "total_interactions": 1, "response_rate_pct": 100.0, "gave_price_pct": 0,
    "followup_rate_pct": 0, "used_name_pct": 0, "attempted_close_pct": 0,
    "avg_quality_score": 20, "calificacion": "F"
  },
  "findings": {
    "veredicto": "Atención reactiva: responden pero no venden.",
    "oportunidad_principal": "Dar precios proactivamente y agendar visita.",
    "resumen": "...", "fortalezas": ["..."], "debilidades": ["..."]
  },
  "recommendations": { "prioritarias": ["..."], "secundarias": ["..."] }
} ]
```
> `metrics.calificacion` (A–F) y `findings.veredicto` / `oportunidad_principal` aparecen en reportes nuevos.

#### `POST /reports/generate/{campaign_id}`  → 201
Genera un reporte nuevo con IA. Devuelve el reporte creado.

---

### 📞 CALL DETAILS

#### `GET /call-details/interaction/{interaction_id}`
Transcript ya limpio (lista de turnos).
```json
[ { "id": "...", "duration_sec": 71, "outcome": null,
    "transcript": [ { "role": "agent", "message": "Hola, busco departamento...", "time_in_call_secs": 0, "interrupted": false },
                    { "role": "user",  "message": "Claro, ¿qué busca?", "time_in_call_secs": 16, "interrupted": false } ] } ]
```

---

### 💬 MESSAGES

#### `GET /messages/interaction/{interaction_id}`
Mensajes de WhatsApp ordenables por `sent_at`.
```json
[ { "id": "...", "role": "bot", "content": "hola, busco depa", "channel": "whatsapp", "sent_at": "..." },
  { "id": "...", "role": "human", "content": "claro, ¿presupuesto?", "channel": "whatsapp", "sent_at": "..." } ]
```

---

### 🔌 WEBHOOKS (interno — NO lo usa el front)
`POST /webhooks/elevenlabs_post_call` — lo consume Make tras una llamada.

---

## 4. Mapa: pantalla del dashboard → endpoints

| Pantalla | Endpoints a llamar |
|---|---|
| **Home** | `GET /dashboard/summary` |
| **Lista de campañas** | `GET /campaigns/` |
| **Detalle de campaña** | `GET /campaigns/{id}` + `GET /interactions/campaign/{id}` + `GET /reports/campaign/{id}` |
| **Detalle de interacción (llamada)** | `GET /interactions/{id}` + `GET /call-details/interaction/{id}` + `GET /interaction-scores/interaction/{id}` |
| **Detalle de interacción (whatsapp)** | `GET /interactions/{id}` (ya trae messages) + `GET /interaction-scores/interaction/{id}` |
| **Lanzar evaluación** | `POST /interactions/` con `{campaign_id, channel}` |

---

## 5. Notas importantes para el front

1. **Roles en conversaciones:** `agent`/`bot` = NUESTRO cliente incógnito · `user`/`human` = la EMPRESA evaluada. Mapea las etiquetas en la UI según eso.
2. **`interaction_scores` es un array:** vacío = sin evaluar aún (muestra "Pendiente"), con 1 objeto = ya evaluado.
3. **`reasoning`** explica el porqué del score — ideal para un tooltip o panel de detalle.
4. **`calificacion` (A–F)** sirve para un badge de color. **`veredicto`** para un encabezado grande.
5. **El scoring es automático** (cada ~10 min). Una interacción recién creada puede tardar en tener score; refresca o haz polling.
6. **Score 0 con `scored_by: "auto"`** = la empresa nunca respondió (no se gastó IA).
