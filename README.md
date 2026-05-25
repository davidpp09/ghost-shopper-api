# 👻 Ghost Shopper

> **LatAm GTM Hackathon — CDMX, Mayo 2026**

---

## El problema

Las inmobiliarias pierden deals todos los días sin saberlo.

Un cliente llama, nadie contesta. O contestan pero no dan precio. O dan precio pero nunca hacen seguimiento. El gerente de ventas no lo sabe porque **nadie lo mide en tiempo real**.

La única forma de saberlo hoy es contratar visitantes misteriosos o hacer llamadas manuales. Caro, lento, y no escala.

---

## La solución

**Ghost Shopper** automatiza el mystery shopping de equipos de ventas.

Llama a la empresa como un cliente real, graba la conversación, la analiza y genera un reporte con score y recomendaciones. Todo sin intervención humana. Todo en minutos.

Un gerente de ventas puede auditar a su equipo el lunes por la mañana antes de que empiece el día.

---

## ¿Cómo funciona?

```
1. El webscraper detecta una inmobiliaria  →  extrae nombre + teléfono
2. Manda el número a Ghost Shopper
3. Ghost Shopper llama al número como cliente potencial (voz real, conversación real)
4. Cuando termina la llamada, analiza la conversación
5. Genera un score + reporte con fortalezas, debilidades y recomendaciones
```

Funciona también por WhatsApp.

---

## Lo que mide

| Criterio | ¿Por qué importa? |
|---|---|
| ¿Contestaron? | El 30% de leads se pierden porque nadie contesta |
| ¿Dieron precio? | Sin precio, el cliente se va con la competencia |
| ¿Intentaron cerrar? | La mayoría de vendedores nunca pide el cierre |
| ¿Hicieron seguimiento? | El 80% de ventas requieren 5+ contactos |
| ¿Usaron el nombre? | Personalización básica que aumenta conversión |
| Tiempo de respuesta | Cada hora que pasa, bajan las chances de cierre |

El resultado es un **score de 0 a 100** con calificación **A–F** y un veredicto en lenguaje simple.

---

## Resultado de ejemplo

```
Score: 34 / 100   →   F

✅ Respondieron la llamada
❌ No dieron precio
❌ No intentaron cerrar
❌ No usaron el nombre del cliente

Veredicto: "Atención reactiva — responden pero no venden."
Oportunidad: "Dar precios proactivamente y proponer visita al inmueble."
```

---

## Por qué importa para GTM

- **Mueve pipeline**: detecta exactamente dónde se rompe el proceso de ventas
- **Ahorra horas**: lo que antes tomaba semanas de observación, ahora tarda minutos
- **Escala**: puede auditar 100 sucursales en el mismo tiempo que una
- **Reutilizable**: corre automáticamente cada N días por campaña — no es un one-shot

---

## Stack

| | |
|---|---|
| API | FastAPI + Python |
| Base de datos | Supabase |
| Llamadas de voz | ElevenLabs + Twilio |
| Análisis | Groq (llama-3.3-70b) |
| Automatización | Make |
| Deploy | Railway |

---

## Correr localmente

```bash
git clone https://github.com/davidpp09/ghost-shopper
cd ghost-shopper
pip install -r requirements.txt
cp .env.example .env   # llenar las keys
uvicorn main:app --reload
```

Ver doc completa de endpoints en `/docs`.

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

## Agradecimientos

Gracias a todos los que hicieron posible este hackathon en CDMX.

**Organizadores**  
[LatamBuilds](https://www.latambuilds.com) · [Makers Fellowship](https://makersfellowship.com) · [30X](https://30x.com) · Hack0 Community by Crafter Station

**Sede**  
[Tuhabi México](https://tuhabi.mx) — Paseo de la Reforma 333, CDMX

**Stack que nos dieron para construir esto**  
[ElevenLabs](https://elevenlabs.io) · [Supabase](https://supabase.com) · [Make](https://make.com) · [Groq](https://groq.com) · [Anthropic](https://anthropic.com) · [Cursor](https://cursor.com)
