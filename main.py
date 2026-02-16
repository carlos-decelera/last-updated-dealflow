import os
from fastapi import FastAPI, Request, HTTPException
import httpx
from datetime import datetime

app = FastAPI()

# CONFIGURACION INICIAL
ATTIO_API_KEY = os.getenv("ATTIO_API_KEY")
ATTRIBUTE_SLUG = "last_modified"
DEALFLOW_ID = "54265eb6-d53d-465d-ad35-4e823e135629"

HEADERS = {
    "Authorization": f"Bearer {ATTIO_API_KEY}",
    "Content-Type": "application/json"
}

@app.post("/last-updated")
async def handle_attio_webhook(request: Request):
    payload = await request.json()
    
    events = payload.get("events", [])
    if isinstance(events, list) and len(events) > 0:
        event_data = events[0]
    else:
        event_data = {}

    actor = event_data.get("actor", {}).get("type", "")
    list_id = event_data.get("id", {}).get("list_id", "")
    entry_id = event_data.get("id", {}).get("entry_id", "")

    if list_id and actor:
        if list_id != DEALFLOW_ID:
            print(f"No es dealflow, es la lista de id {list_id}")
            return
        elif actor != "workspace-member":
            print(f"Cambio hecho por el sistema, lo ignoramos. Actor: {actor}")
            return
        else:
            now_iso = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

            async with httpx.AsyncClient() as client:
                url = f"https://api.attio.com/v2/lists/{list_id}/entries/{entry_id}"

                payload = {
                    "data": {
                        "entry_values": {
                            ATTRIBUTE_SLUG: now_iso
                        }
                    }
                }

                response = await client.patch(url=url, json=payload, headers=HEADERS)

                if response.is_success:
                    return {"status": "success", "updated_entry": entry_id}
                else:
                    print(f"Error de Attio: {response.text}")
                    raise HTTPException(status_code=response.status_code, detail="Error al actualizar")