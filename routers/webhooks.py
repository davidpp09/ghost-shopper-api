from fastapi import APIRouter, Request

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

@router.post("/elevenlabs_post_call")
async def elevenlabs_post_call(request: Request):
    body = await request.json()
    print(body)
    return body
