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

# === Load env ===
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
RAILWAY_URL = os.getenv("RAILWAY_URL")
BITRIX_WEBHOOK_URL = os.getenv("BITRIX_WEBHOOK_URL")

if not TELEGRAM_TOKEN or not RAILWAY_URL or not BITRIX_WEBHOOK_URL:
    raise RuntimeError("❌ Missing env vars")

print("✅ ENV loaded: TELEGRAM_TOKEN, RAILWAY_URL, BITRIX_WEBHOOK_URL")

# === FastAPI app ===
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")

# === Static files ===
@app.get("/")
def index():
    print("📥 Serving index.html")
    return FileResponse("webapp/index.html")

@app.get("/style.css")
def css():
    return FileResponse("webapp/style.css")

@app.get("/script.js")
def js():
    return FileResponse("webapp/script.js")

# === Images ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
scenario_images = {str(i): [os.path.join(BASE_DIR, "webapp", "images", f"{i}.png")] for i in range(1, 7)}
print(f"✅ Scenario images loaded: {scenario_images}")

# === Telegram bot ===
default_props = DefaultBotProperties(parse_mode=ParseMode.HTML)
bot = Bot(token=TELEGRAM_TOKEN, default=default_props)
dp = Dispatcher()
print("✅ Telegram bot initialized")

# === Helper: send scenario image ===
async def send_scenario_image(chat_id: int, scenario_id: str):
    print(f"🔹 [send_scenario_image] chat_id={chat_id}, scenario_id={scenario_id}")
    images = scenario_images.get(str(scenario_id), [])
    if not images:
        print(f"⚠️ No images found for scenario {scenario_id}")
        return False
    sent_any = False
    for path in images:
        if not os.path.exists(path):
            print(f"❌ Missing image file: {path}")
            continue
        try:
            msg = await bot.send_photo(chat_id, InputFile(path), caption=f"Чек-лист — сценарий {scenario_id}")
            print(f"✅ Photo sent: {path}, message_id={msg.message_id}")
            sent_any = True
        except Exception as e:
            print(f"⚠️ Error sending photo: {e}")
    return sent_any

# === Submit endpoint ===
@app.post("/submit")
async def submit_contact(request: Request):
    data = await request.json()
    print("📥 Received form:", data)

    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    scenario_id = str(data.get("scenario", "")).strip()
    chat_id = data.get("telegram_user_id")  # Telegram WebApp user.id

    print(f"🔹 Parsed data -> name: {name}, email: {email}, scenario: {scenario_id}, chat_id: {chat_id}")

    if not name:
        return JSONResponse({"status": "error", "message": "Введите имя."}, status_code=400)
    if not EMAIL_REGEX.match(email):
        return JSONResponse({"status": "error", "message": "Введите корректный email."}, status_code=400)

    # === Send to Bitrix ===
    try:
        payload = {
            "fields": {
                "TITLE": f"Диагностика IT-рисков — {scenario_id}",
                "NAME": name,
                "EMAIL": [{"VALUE": email, "VALUE_TYPE": "WORK"}],
                "COMMENTS": f"Сценарий: {scenario_id}\nEmail: {email}",
                "SOURCE_ID": "WEB",
            },
            "params": {"REGISTER_SONET_EVENT": "Y"},
        }
        print(f"📤 Sending lead to Bitrix: {payload}")
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(BITRIX_WEBHOOK_URL, json=payload)
            bitrix_res = r.json()
        print("📌 Bitrix response:", bitrix_res)
    except Exception as e:
        print("⚠️ Bitrix error:", e)
        return JSONResponse({"status": "error", "message": "Ошибка при отправке в CRM."}, status_code=500)

    # === Send Telegram photo ===
    if chat_id:
        try:
            chat_id_int = int(chat_id)
            print(f"🔹 Sending scenario image to chat_id={chat_id_int}")
            sent = await send_scenario_image(chat_id_int, scenario_id)
            if not sent:
                print("⚠️ No images sent")
        except Exception as e:
            print(f"⚠️ Error sending images: {e}")
    else:
        print("⚠️ No telegram_user_id — cannot send photo")

    return JSONResponse({"status": "ok", "lead_id": bitrix_res.get("result")})

# === Telegram /start handler ===
@dp.message(Command("start"))
async def start(message: Message):
    print(f"📥 /start from user_id={message.from_user.id}")
    btn = KeyboardButton(text="🚀 Открыть диагностику IT-рисков", web_app=WebAppInfo(url=RAILWAY_URL))
    kb = ReplyKeyboardMarkup(keyboard=[[btn]], resize_keyboard=True)
    await message.answer("Привет! 👋 Нажми кнопку ниже, чтобы пройти диагностику:", reply_markup=kb)

# === Webhook ===
@app.post("/webhook")
async def telegram_webhook(request: Request):
    body = await request.json()
    print("📥 /webhook received:", body)
    update = types.Update(**body)
    await dp.feed_update(bot, update)
    return JSONResponse({"ok": True})

# === Startup webhook ===
@app.on_event("startup")
async def on_startup():
    webhook_url = f"{RAILWAY_URL}/webhook"
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(url=webhook_url)
    print(f"✅ Webhook установлен на {webhook_url}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print(f"🚀 Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
