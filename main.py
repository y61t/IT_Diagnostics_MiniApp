import os
import re
import hmac
import hashlib
import httpx
from dotenv import load_dotenv
from typing import Any, Dict

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
    raise RuntimeError("❌ One of env vars TELEGRAM_TOKEN/RAILWAY_URL/BITRIX_WEBHOOK_URL is missing")

# === FastAPI ===
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")

# === Static files ===
@app.get("/")
def index():
    return FileResponse("webapp/index.html")

@app.get("/style.css")
def css():
    return FileResponse("webapp/style.css")

@app.get("/script.js")
def js():
    return FileResponse("webapp/script.js")

# === Images (absolute paths) ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
scenario_images = {
    "1": [os.path.join(BASE_DIR, "webapp", "images", "1.png")],
    "2": [os.path.join(BASE_DIR, "webapp", "images", "2.png")],
    "3": [os.path.join(BASE_DIR, "webapp", "images", "3.png")],
    "4": [os.path.join(BASE_DIR, "webapp", "images", "4.png")],
    "5": [os.path.join(BASE_DIR, "webapp", "images", "5.png")],
    "6": [os.path.join(BASE_DIR, "webapp", "images", "6.png")],
}

# === Telegram bot setup ===
default_properties = DefaultBotProperties(parse_mode=ParseMode.HTML)
bot = Bot(token=TELEGRAM_TOKEN, default=default_properties)
dp = Dispatcher()  # aiogram 3.x -> no args

# --- Helper: verify Telegram Login Widget payload ---
def verify_telegram_login(auth_data: Dict[str, Any]) -> bool:
    """
    Verify Telegram Login Widget auth_data dict.
    Returns True if signature valid.
    """
    try:
        data = {k: str(v) for k, v in auth_data.items() if k != "hash"}
        received_hash = auth_data.get("hash")
        if not received_hash:
            print("verify_telegram_login: no hash")
            return False

        # Build data_check_string
        data_check_arr = [f"{k}={data[k]}" for k in sorted(data.keys())]
        data_check_string = "\n".join(data_check_arr)

        # Secret key is SHA256(bot_token)
        secret_key = hashlib.sha256(TELEGRAM_TOKEN.encode()).digest()

        hmac_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()
        valid = hmac_hash == received_hash
        print(f"verify_telegram_login: valid={valid}")
        return valid
    except Exception as e:
        print("verify_telegram_login error:", e)
        return False

# === Send images (with logs) ===
async def send_scenario_image(chat_id: int, scenario_id: str):
    print(f"🔹 [send_scenario_image] chat_id={chat_id}, scenario_id={scenario_id}")
    images = scenario_images.get(scenario_id, [])
    if not images:
        print(f"❌ [send_scenario_image] No images for scenario {scenario_id}")
        return False

    sent_any = False
    for img_path in images:
        if not os.path.exists(img_path):
            print(f"❌ [send_scenario_image] File not found: {img_path}")
            continue
        try:
            print(f"📤 [send_scenario_image] Sending file: {img_path} to {chat_id}")
            photo = InputFile(img_path)
            msg = await bot.send_photo(chat_id=chat_id, photo=photo, caption=f"Чек-лист — сценарий {scenario_id}")
            print(f"✅ [send_scenario_image] Sent message_id={getattr(msg, 'message_id', None)}")
            sent_any = True
        except Exception as e:
            print(f"⚠️ [send_scenario_image] Error sending {img_path} -> {e}")
    return sent_any

# === Submit endpoint ===
@app.post("/submit")
async def submit_contact(request: Request):
    data = await request.json()
    print("📥 [submit] received:", data)

    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    telegram_field = data.get("telegram", "").strip() if data.get("telegram") else ""
    scenario_id = str(data.get("scenario", "")).strip()

    # optional: telegram auth object from widget
    telegram_auth = data.get("telegram_auth")  # should be dict {id, first_name, auth_date, hash, ...}
    # optional: webapp user id (from WebApp initDataUnsafe)
    webapp_user_id = data.get("telegram_user_id")

    if not name:
        return JSONResponse({"status": "error", "message": "Введите имя."}, status_code=400)
    if not email or not EMAIL_REGEX.match(email):
        return JSONResponse({"status": "error", "message": "Введите корректный email."}, status_code=400)

    # send lead to Bitrix
    try:
        print("📤 [submit] sending lead to Bitrix...")
        payload = {
            "fields": {
                "TITLE": f"Диагностика IT-рисков — {scenario_id}",
                "NAME": name,
                "EMAIL": [{"VALUE": email, "VALUE_TYPE": "WORK"}],
                "PHONE": [{"VALUE": telegram_field, "VALUE_TYPE": "WORK"}] if telegram_field else [],
                "COMMENTS": f"Сценарий: {scenario_id}\nTelegram/Phone: {telegram_field or 'не указан'}\nEmail: {email}",
                "SOURCE_ID": "WEB",
            },
            "params": {"REGISTER_SONET_EVENT": "Y"}
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(BITRIX_WEBHOOK_URL, json=payload)
            result = r.json()
        print("📌 [submit] Bitrix response:", result)
    except Exception as e:
        print("⚠️ [submit] Bitrix error:", e)
        return JSONResponse({"status": "error", "message": "Ошибка соединения с CRM."}, status_code=500)

    # Determine chat_id to send images
    chat_id = None
    # 1) If telegram_auth provided -> verify and use id
    if telegram_auth and isinstance(telegram_auth, dict):
        print("🔎 [submit] telegram_auth provided, verifying...")
        try:
            if verify_telegram_login(telegram_auth):
                chat_id = int(telegram_auth.get("id"))
                print(f"✅ [submit] telegram_auth valid, chat_id={chat_id}")
            else:
                print("❌ [submit] telegram_auth verification failed")
        except Exception as e:
            print("⚠️ [submit] telegram_auth check error:", e)

    # 2) Else if webapp_user_id provided (from Telegram WebApp)
    if not chat_id and webapp_user_id:
        try:
            chat_id = int(webapp_user_id)
            print(f"✅ [submit] using webapp_user_id={chat_id}")
        except Exception as e:
            print("❌ [submit] webapp_user_id invalid:", e)

    # 3) Else fallback to 'telegram' field (user might paste chat_id or @username)
    if not chat_id and telegram_field:
        t = telegram_field.strip()
        # numeric id
        if t.isdigit():
            chat_id = int(t)
            print(f"✅ [submit] using numeric telegram field as chat_id={chat_id}")
        else:
            username = t.lstrip("@")
            print(f"🔎 [submit] trying to resolve username @{username} via get_chat...")
            try:
                chat = await bot.get_chat(username)
                chat_id = chat.id
                print(f"✅ [submit] resolved username @{username} -> chat_id={chat_id}")
            except Exception as e:
                print(f"❌ [submit] get_chat failed for @{username} -> {e}")

    # If we have chat_id -> send images
    if chat_id:
        try:
            sent = await send_scenario_image(chat_id, scenario_id)
            if not sent:
                print("❌ [submit] no images were sent (files missing or errors)")
        except Exception as e:
            print("⚠️ [submit] error sending images:", e)
    else:
        print("⚠️ [submit] No chat_id available — skipping sending images")

    return JSONResponse({"status": "ok", "lead_id": result.get("result")})

# === Telegram /start handler (WebApp button) ===
@dp.message(Command("start"))
async def start(message: Message):
    print(f"📥 [telegram] /start from user_id={message.from_user.id}")
    button = KeyboardButton(text="🚀 Открыть диагностику IT-рисков", web_app=WebAppInfo(url=RAILWAY_URL))
    keyboard = ReplyKeyboardMarkup(keyboard=[[button]], resize_keyboard=True)
    await message.answer("Привет! 👋 Нажми кнопку ниже, чтобы пройти диагностику:", reply_markup=keyboard)

# === webhook ===
@app.post("/webhook")
async def telegram_webhook(request: Request):
    body = await request.json()
    print("📥 [webhook] update:", body)
    update = types.Update(**body)
    await dp.feed_update(bot, update)
    return JSONResponse({"ok": True})

# === startup: set webhook ===
@app.on_event("startup")
async def on_startup():
    webhook_url = f"{RAILWAY_URL}/webhook"
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(url=webhook_url)
    print(f"✅ [startup] Webhook установлен на {webhook_url}")

# === run ===
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
