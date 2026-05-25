import json


def _unwrap(value):
    """Si viene envuelto como {"array": [...]} (formato de Make), saca la lista."""
    if isinstance(value, dict) and isinstance(value.get("array"), list):
        return value["array"]
    return value


def _to_list(raw) -> list:
    """
    Convierte el raw transcript a una lista de dicts sin importar el formato:
      1. Ya es una lista                          → se usa directo
      2. Objeto Make    {"array": [...]}          → se saca el array
      3. String JSON con array   "[{...}]"        → json.loads
      4. String Make    "{\"array\":[...]}"       → json.loads + sacar array
      5. String JSON sin array   "{...},{...}"    → se envuelve en [] y se parsea
      6. Doble serialización     "\"[{...}]\""    → dos json.loads
    """
    raw = _unwrap(raw)
    if isinstance(raw, list):
        return raw

    if not isinstance(raw, str) or not raw.strip():
        return []

    # Intento 1: parseo directo (cubre casos 3, 4 y 6)
    try:
        parsed = json.loads(raw)
        parsed = _unwrap(parsed)
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, str):
            # Doble serialización — un parse más
            parsed = _unwrap(json.loads(parsed))
            if isinstance(parsed, list):
                return parsed
    except (json.JSONDecodeError, ValueError):
        pass

    # Intento 2: el string es objetos JSON sin corchetes "{...}, {...}"
    # Se envuelve en [] para hacerlo un array válido
    try:
        wrapped = f"[{raw.strip()}]"
        parsed = json.loads(wrapped)
        if isinstance(parsed, list):
            return parsed
    except (json.JSONDecodeError, ValueError):
        pass

    return []


def parse_transcript(raw_transcript) -> list[dict]:
    """
    Parsea y limpia el transcript crudo de ElevenLabs.
    Devuelve solo los campos útiles de cada turno.
    """
    turns = _to_list(raw_transcript)

    clean = []
    for turn in turns:
        if not isinstance(turn, dict):
            continue

        # ElevenLabs guarda el mensaje final en original_message
        # y el procesado (con pausas, etc.) en message
        message = turn.get("original_message") or turn.get("message") or ""

        clean.append({
            "role": turn.get("role"),
            "message": message.strip(),
            "time_in_call_secs": turn.get("time_in_call_secs"),
            "interrupted": turn.get("interrupted", False),
        })

    return clean
