import os
import logging
from dotenv import load_dotenv
import re
import httpx
import hmac
import hashlib
import urllib.parse
import json

from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import WebAppInfo, KeyboardButton, ReplyKeyboardMarkup
from aiogram.enums import ParseMode
from aiogram.client.bot import DefaultBotProperties
from aiogram.exceptions import TelegramBadRequest

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Словарь для хранения chat_id по user_id
user_chat_map = {}

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

# === Инициализация бота и диспетчера ===
default_properties = DefaultBotProperties(parse_mode=ParseMode.HTML)
bot = Bot(token=TELEGRAM_TOKEN, default=default_properties)
dp = Dispatcher(bot=bot)

# === FastAPI ===
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")

# Health-эндпоинт для проверки порта
@app.get("/health")
async def health_check():
    logger.info("Health check requested")
    return JSONResponse({"status": "healthy"})

# Валидация init_data от Telegram
def validate_init_data(init_data_str: str) -> dict:
    params = dict(urllib.parse.parse_qsl(init_data_str))
    received_hash = params.pop('hash', None)
    data_check_string = '\n'.join(f"{k}={v}" for k, v in sorted(params.items()))
    secret_key = hashlib.sha256(TELEGRAM_TOKEN.encode()).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if calculated_hash == received_hash:
        user = json.loads(params['user'])
        logger.info(f"✅ Успешная валидация init_data. User ID: {user['id']}")
        return user
    else:
        logger.error(f"❌ Ошибка валидации init_data. Received hash: {received_hash}, Calculated hash: {calculated_hash}")
        raise ValueError("Invalid init_data hash")

# === Статика ===
@app.get("/")
def index():
    logger.info("Serving index.html")
    return FileResponse("webapp/index.html")

@app.get("/style.css")
def css():
    logger.info("Serving style.css")
    return FileResponse("webapp/style.css")

@app.get("/script.js")
def js():
    logger.info("Serving script.js")
    return FileResponse("webapp/script.js")

# === Submit формы ===
@app.post("/submit")
async def submit_contact(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    telegram = data.get("telegram", "").strip()
    scenario_id = str(data.get("scenario", "")).strip()
    init_data = data.get("init_data", "")

    logger.info(f"Получены данные: name={name}, email={email}, telegram={telegram}, scenario={scenario_id}, init_data={init_data}")

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
    chat_id = None
    if init_data:
        try:
            user = validate_init_data(init_data)
            user_id = user['id']
            chat_id = user_chat_map.get(user_id, user_id)
        except Exception as e:
            logger.error(f"⚠️ Ошибка валидации init_data: {str(e)}")
    else:
        logger.warning("init_data отсутствует, пытаемся использовать последний известный chat_id")
        for uid, cid in user_chat_map.items():
            if uid == 8100687321:  # Жёсткая привязка для теста, потом доработаем
                chat_id = cid
                user_id = uid
                break

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(BITRIX_WEBHOOK_URL, json=payload)
            result = r.json()

        if "error" in result:
            logger.error(f"⚠️ Ошибка Bitrix: {result}")
            return JSONResponse({"status": "error", "message": "Не удалось создать лид."}, status_code=400)

        if chat_id:
            background_tasks.add_task(send_telegram_photos, chat_id, scenario_id)

        return JSONResponse({"status": "ok", "lead_id": result.get("result")})

    except Exception as e:
        logger.error(f"⚠️ Ошибка: {str(e)}")
        return JSONResponse({"status": "error", "message": "Ошибка соединения с CRM."}, status_code=500)

# Функция для отправки фото в Telegram
async def send_telegram_photos(chat_id: int, scenario_id: str):
    try:
        main_photo_path = "webapp/images/main.png"
        scenario_photo_path = f"webapp/images/{scenario_id}.png"

        if os.path.exists(main_photo_path):
            await bot.send_photo(chat_id=chat_id, photo=types.FSInputFile(main_photo_path))
            logger.info(f"✅ Основное фото отправлено в Telegram для chat_id={chat_id}")
        else:
            logger.warning(f"⚠️ Фото main.png не найдено для chat_id={chat_id}")

        if os.path.exists(scenario_photo_path):
            await bot.send_photo(
                chat_id=chat_id,
                photo=types.FSInputFile(scenario_photo_path),
                caption=f"Вот общие материалы🔥 Наш архитектор свяжется✍️"
            )
            logger.info(f"✅ Фото сценария отправлено в Telegram для chat_id={chat_id}")
        else:
            logger.warning(f"⚠️ Фото {scenario_id}.png не найдено для chat_id={chat_id}")

    except Exception as e:
        logger.error(f"❌ Ошибка при отправке фото в Telegram: {str(e)}")

# === Telegram Bot через Webhook ===
@dp.message(Command("start"))
async def start(message: types.Message):
    button = KeyboardButton(text="🚀 Открыть диагностику IT-рисков", web_app=WebAppInfo(url=RAILWAY_URL))
    keyboard = ReplyKeyboardMarkup(keyboard=[[button]], resize_keyboard=True)
    await message.answer("Привет! 👋 Нажми кнопку ниже, чтобы пройти диагностику IT-рисков:", reply_markup=keyboard)
    user_chat_map[message.from_user.id] = message.chat.id
    logger.info(f"Сохранён chat_id {message.chat.id} для user_id {message.from_user.id}")

# === Webhook для Telegram ===
@app.post("/webhook")
async def telegram_webhook(request: Request):
    body = await request.json()
    if 'message' in body and 'from' in body['message'] and 'chat' in body['message']:
        user_id = body['message']['from']['id']
        chat_id = body['message']['chat']['id']
        user_chat_map[user_id] = chat_id
        logger.info(f"Обновлён chat_id {chat_id} для user_id {user_id}")
    logger.info(f"Получен webhook: {body}")
    update = types.Update(**body)
    await dp.feed_update(bot, update)
    return JSONResponse({"ok": True})

# === Установка webhook при старте с обработкой ошибок ===
@app.on_event("startup")
async def on_startup():
    port = os.getenv("PORT", "8000")
    logger.info(f"🚀 Server starting on port {port}")
    webhook_url = f"{RAILWAY_URL}/webhook"
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await bot.set_webhook(url=webhook_url)
        logger.info(f"✅ Webhook установлен на {webhook_url}")
    except TelegramBadRequest as e:
        logger.error(f"❌ Ошибка установки вебхука: {str(e)}. Проверьте RAILWAY_URL.")
    except Exception as e:
        logger.error(f"❌ Неизвестная ошибка при установке вебхука: {str(e)}")