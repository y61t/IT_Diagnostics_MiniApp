from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
from dotenv import load_dotenv
import uvicorn
import re

load_dotenv()

app = FastAPI()

# Разрешаем фронтенду обращаться к API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Настройки ===
BITRIX_WEBHOOK_URL = os.getenv("BITRIX_WEBHOOK_URL")
PDF_PATH = os.getenv("PDF_PATH", "webapp/checklist.pdf")

# === Маршруты для статики ===
@app.get("/")
def index():
    return FileResponse("webapp/index.html")

@app.get("/style.css")
def css():
    return FileResponse("webapp/style.css")

@app.get("/script.js")
def js():
    return FileResponse("webapp/script.js")

# === Валидация email ===
EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")

@app.post("/submit")
async def submit_contact(request: Request):
    data = await request.json()

    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    telegram = data.get("telegram", "").strip()
    scenario_id = str(data.get("scenario", "")).strip()

    if not name:
        return JSONResponse({"status": "error", "message": "Введите имя."}, status_code=400)
    if not email or not EMAIL_REGEX.match(email):
        return JSONResponse({"status": "error", "message": "Введите корректный email."}, status_code=400)

    scenario_texts = {
        "1": "Проект в кризисе",
        "2": "Подготовка запуска ИТ-проекта",
        "3": "Импортозамещение и стратегия",
        "4": "Проверка подрядчика и команды",
        "5": "Цифровая зрелость бизнеса",
        "6": "Проверка бюджета проекта (CFO)"
    }

    scenario = scenario_texts.get(scenario_id, "Не указан сценарий")

    payload = {
        "fields": {
            "TITLE": f"Диагностика ИТ-рисков — {scenario}",
            "NAME": name,
            "EMAIL": [{"VALUE": email, "VALUE_TYPE": "WORK"}],
            "PHONE": [{"VALUE": telegram, "VALUE_TYPE": "WORK"}] if telegram else [],
            "COMMENTS": f"Сценарий: {scenario}\nTelegram/Phone: {telegram or 'не указан'}\nEmail: {email}",
            "SOURCE_ID": "WEB",
        },
        "params": {"REGISTER_SONET_EVENT": "Y"}
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(BITRIX_WEBHOOK_URL, json=payload)
            result = r.json()

        if "error" in result:
            print("⚠️ Ошибка Bitrix:", result)
            return JSONResponse({
                "status": "error",
                "message": "Не удалось создать лид. Проверьте данные."
            }, status_code=400)

        print(f"✅ Лид создан: {result.get('result')} — {scenario}")
        # Возвращаем ссылку на PDF вместе с результатом
        return JSONResponse({
            "status": "ok",
            "lead_id": result.get("result"),
            "pdf_url": "/download"
        })

    except Exception as e:
        print("⚠️ Ошибка при отправке в Bitrix:", e)
        return JSONResponse({"status": "error", "message": "Ошибка соединения с CRM."}, status_code=500)

# === Скачивание PDF ===
@app.get("/download")
def download_pdf():
    return FileResponse(PDF_PATH, media_type="application/pdf", filename="checklist.pdf")


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
