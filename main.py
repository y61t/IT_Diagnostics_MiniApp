import os
from dotenv import load_dotenv
import re
import httpx
import hmac
import hashlib
import urllib.parse
import json

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import WebAppInfo, KeyboardButton, ReplyKeyboardMarkup, Message
from aiogram.enums import ParseMode
from aiogram.client.bot import DefaultBotProperties

# Загружаем .env
load_dotenv()

# === Настройки ===
REQUIRED_ENVS = ["TELEGRAM_TOKEN", "RAILWAY_URL", "BITRIX_WEBHOOK_URL"]
for var in REQUIRED_ENVS:
    if not os.getenv(var):
        raise RuntimeError(f"❌ Env переменная {var} не задана!")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
RAILWAY_URL = os.getenv("RAILWAY_URL")
BITRIX_WEBHOOK_URL = os.getenv("BITRIX_WEBHOOK_URL")

# === FastAPI ===
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")

# Валидация init_data от Telegram
def validate_init_data(init_data_str: str) -> dict:
    params = dict(urllib.parse.parse_qsl(init_data_str))
    received_hash = params.pop('hash', None)
    data_check_string = '\n'.join(f"{k}={v}" for k, v in sorted(params.items()))
    secret_key = hashlib.sha256(TELEGRAM_TOKEN.encode()).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if calculated_hash == received_hash:
        user = json.loads(params['user'])
        return user
    raise ValueError("Invalid init_data hash")

# === Статика ===
@app.get("/")
def index():
    return FileResponse("webapp/index.html")

@app.get("/style.css")
def css():
    return FileResponse("webapp/style.css")

@app.get("/script.js")
def js():
    return FileResponse("webapp/script.js")

# === Submit формы ===
@app.post("/submit")
async def submit_contact(request: Request):
    data = await request.json()
    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    telegram = data.get("telegram", "").strip()
    scenario_id = str(data.get("scenario", "")).strip()
    init_data = data.get("init_data", "")

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

    user_id = None
    if init_data:
        try:
            user = validate_init_data(init_data)
            user_id = user['id']
        except Exception as e:
            print("⚠️ Ошибка валидации init_data:", e)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(BITRIX_WEBHOOK_URL, json=payload)
            result = r.json()

        if "error" in result:
            print("⚠️ Ошибка Bitrix:", result)
            return JSONResponse({"status": "error", "message": "Не удалось создать лид."}, status_code=400)

        # Отправка текста в Telegram
        if user_id:
            await bot.send_message(
                chat_id=user_id,
                text=f"Спасибо, {name}! Вы выбрали сценарий: {scenario}. Наш архитектор свяжется с вами для дальнейших шагов."
            )
        else:
            print("⚠️ Нет user_id, сообщение не отправлено в TG.")

        return JSONResponse({"status": "ok", "lead_id": result.get("result")})

    except Exception as e:
        print("⚠️ Ошибка:", e)
        return JSONResponse({"status": "error", "message": "Ошибка соединения с CRM."}, status_code=500)

# === Telegram Bot через Webhook ===
default_properties = DefaultBotProperties(parse_mode=ParseMode.HTML)
bot = Bot(token=TELEGRAM_TOKEN, default=default_properties)
dp = Dispatcher(bot=bot)

@dp.message(Command("start"))
async def start(message: Message):
    button = KeyboardButton(text="🚀 Открыть диагностику IT-рисков", web_app=WebAppInfo(url=RAILWAY_URL))
    keyboard = ReplyKeyboardMarkup(keyboard=[[button]], resize_keyboard=True)
    await message.answer("Привет! 👋 Нажми кнопку ниже, чтобы пройти диагностику IT-рисков:", reply_markup=keyboard)

# === Webhook для Telegram ===
@app.post("/webhook")
async def telegram_webhook(request: Request):
    body = await request.json()
    update = types.Update(**body)
    await dp.feed_update(bot, update)
    return JSONResponse({"ok": True})

# === Установка webhook при старте ===
@app.on_event("startup")
async def on_startup():
    webhook_url = f"{RAILWAY_URL}/webhook"
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(url=webhook_url)
    print(f"✅ Webhook установлен на {webhook_url}")

# === Запуск FastAPI ===
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)