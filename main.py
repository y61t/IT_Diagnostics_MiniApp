import os
import re
import httpx
from dotenv import load_dotenv

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import WebAppInfo, KeyboardButton, ReplyKeyboardMarkup, Message, InputFile
from aiogram.enums import ParseMode
from aiogram.client.bot import DefaultBotProperties

# === Load environment ===
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
BITRIX_WEBHOOK_URL = os.getenv("BITRIX_WEBHOOK_URL")
RAILWAY_URL = os.getenv("RAILWAY_URL")

if not TELEGRAM_TOKEN or not BITRIX_WEBHOOK_URL or not RAILWAY_URL:
    raise RuntimeError("❌ Не найдены переменные окружения. Проверь .env")

# === FastAPI ===
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")

# === Static ===
@app.get("/")
def index():
    return FileResponse("webapp/index.html")

@app.get("/style.css")
def css():
    return FileResponse("webapp/style.css")

@app.get("/script.js")
def js():
    return FileResponse("webapp/script.js")

# === Scenarios & Images ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
scenario_images = {
    "1": [os.path.join(BASE_DIR, "webapp/images/1.png")],
    "2": [os.path.join(BASE_DIR, "webapp/images/2.png")],
    "3": [os.path.join(BASE_DIR, "webapp/images/3.png")],
    "4": [os.path.join(BASE_DIR, "webapp/images/4.png")],
    "5": [os.path.join(BASE_DIR, "webapp/images/5.png")],
    "6": [os.path.join(BASE_DIR, "webapp/images/6.png")],
}

# === Telegram Bot ===
default_properties = DefaultBotProperties(parse_mode=ParseMode.HTML)
bot = Bot(token=TELEGRAM_TOKEN, default=default_properties)
dp = Dispatcher()

async def send_scenario_image(chat_id: int, scenario_id: str):
    print(f"🔹 Отправка картинок пользователю {chat_id} (сценарий {scenario_id})")
    images = scenario_images.get(scenario_id, [])
    if not images:
        print("❌ Нет изображений для сценария:", scenario_id)
        return
    for img_path in images:
        if not os.path.exists(img_path):
            print(f"❌ Файл не найден: {img_path}")
            continue
        print(f"📤 Отправка файла: {img_path}")
        await bot.send_photo(chat_id=chat_id, photo=InputFile(img_path), caption="Ваш чек-лист по сценарию")

# === Form submit ===
@app.post("/submit")
async def submit_contact(request: Request):
    data = await request.json()
    print("📥 Получены данные формы:", data)

    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    telegram_user_id = data.get("telegram_user_id")
    scenario_id = str(data.get("scenario", "")).strip()

    if not name or not email or not EMAIL_REGEX.match(email):
        return JSONResponse({"status": "error", "message": "Некорректные данные"}, status_code=400)

    try:
        # === Отправка лида в Bitrix ===
        print("📤 Отправка лида в Bitrix...")
        payload = {
            "fields": {
                "TITLE": f"Диагностика IT-рисков — {scenario_id}",
                "NAME": name,
                "EMAIL": [{"VALUE": email, "VALUE_TYPE": "WORK"}],
                "COMMENTS": f"Сценарий: {scenario_id}"
            },
            "params": {"REGISTER_SONET_EVENT": "Y"}
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(BITRIX_WEBHOOK_URL, json=payload)
            result = r.json()
        print("📌 Bitrix ответ:", result)

        # === Отправка картинки пользователю ===
        if telegram_user_id:
            await send_scenario_image(int(telegram_user_id), scenario_id)
        else:
            print("❌ Telegram user_id не указан")

        return JSONResponse({"status": "ok", "lead_id": result.get("result")})
    except Exception as e:
        print("⚠️ Ошибка submit:", e)
        return JSONResponse({"status": "error", "message": "Ошибка на сервере"}, status_code=500)

# === Telegram /start ===
@dp.message(Command("start"))
async def start(message: Message):
    button = KeyboardButton(text="🚀 Пройти диагностику", web_app=WebAppInfo(url=RAILWAY_URL))
    keyboard = ReplyKeyboardMarkup(keyboard=[[button]], resize_keyboard=True)
    await message.answer("Привет! 👋 Нажми кнопку ниже, чтобы пройти диагностику:", reply_markup=keyboard)

# === Telegram webhook ===
@app.post("/webhook")
async def telegram_webhook(request: Request):
    body = await request.json()
    update = types.Update(**body)
    await dp.feed_update(bot, update)
    return JSONResponse({"ok": True})

# === Startup: set webhook ===
@app.on_event("startup")
async def on_startup():
    webhook_url = f"{RAILWAY_URL}/webhook"
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(url=webhook_url)
    print(f"✅ Webhook установлен на {webhook_url}")

# === Run ===
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
