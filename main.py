from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
import uvicorn
import httpx
import os


app = FastAPI()
BITRIX_WEBHOOK_URL = os.getenv("BITRIX_WEBHOOK_URL")
PDF_PATH = os.getenv("PDF_PATH")


@app.get("/")
def index():
    return FileResponse("webapp/index.html")


@app.get("/style.css")
def css():
    return FileResponse("webapp/style.css")


@app.get("/script.js")
def js():
    return FileResponse("webapp/script.js")


# Новый маршрут для получения данных контакта
@app.post("/submit")
async def submit_contact(request: Request):
    data = await request.json()
    print("Новый контакт:", data)
    # Здесь можно интегрировать Bitrix24 или PDF генерацию
    return JSONResponse({"status": "ok"})


@app.get("/download")
def download_pdf():
    return FileResponse(PDF_PATH, media_type="application/pdf", filename="checklist.pdf")


@app.post("/submit")
async def submit_contact(request: Request):
    data = await request.json()
    print("Новый контакт:", data)

    lead_data = {
        "fields": {
            "TITLE": f"MiniApp: {data.get('scenario')}",
            "NAME": data.get("name"),
            "EMAIL": [{"VALUE": data.get("email"), "VALUE_TYPE": "WORK"}],
            "PHONE": [{"VALUE": data.get("telegram"), "VALUE_TYPE": "WORK"}],
            "COMMENTS": f"Сценарий: {data.get('scenario')}"
        }
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(BITRIX_WEBHOOK_URL, json=lead_data)
        print("Ответ Bitrix24:", response.status_code, response.text)

    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
