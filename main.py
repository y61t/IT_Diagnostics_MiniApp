import logging
import os
from dotenv import load_dotenv
import re
import aiohttp
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import WebAppInfo, KeyboardButton, ReplyKeyboardMarkup, Message
from aiogram.enums import ParseMode
from aiogram.client.bot import DefaultBotProperties
from aiogram.types.input_file import FSInputFile

# === Логирование ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
async def submit_form(request: Request):
    data = await request.json()
    name = data.get("name")
    email = data.get("email")
    telegram = data.get("telegram")
    scenario = data.get("scenario")
    user_id = data.get("user_id")

    logger.info(f"/submit получен: name={name}, email={email}, telegram={telegram}, scenario={scenario}, user_id={user_id}")

    # --- 1. Отправляем данные в Bitrix ---
    bitrix_payload = {
        "fields": {
            "TITLE": f"IT Диагностика — {name}",
            "NAME": name,
            "EMAIL": [{"VALUE": email, "VALUE_TYPE": "WORK"}],
            "COMMENTS": f"Сценарий: {scenario}\nTelegram: {telegram}",
        },
        "params": {"REGISTER_SONET_EVENT": "Y"}
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(BITRIX_WEBHOOK_URL, json=bitrix_payload) as resp:
                logger.info(f"Лид отправлен в Bitrix, status={resp.status}")
    except Exception as e:
        logger.warning(f"Ошибка отправки в Bitrix: {e}")

    # --- 2. Отправляем пользователю картинки ---
    if user_id:
        try:
            main_img_path = "webapp/images/main.png"
            scenario_img_path = f"webapp/images/{scenario}.png"

            if not os.path.exists(main_img_path):
                logger.warning(f"main.png не найден по пути {main_img_path}")
            if not os.path.exists(scenario_img_path):
                logger.warning(f"сценарий {scenario}.png не найден, используем 1.png")
                scenario_img_path = "webapp/images/1.png"

            main_img = FSInputFile(main_img_path)
            scenario_img = FSInputFile(scenario_img_path)

            logger.info(f"Отправка main.png и сценария {scenario}.png пользователю {user_id}")

            await bot.send_photo(chat_id=int(user_id), photo=main_img, caption="📋 Ваш чек-лист готов!")
            await bot.send_photo(chat_id=int(user_id), photo=scenario_img, caption=f"🧩 Ваш сценарий: {scenario}")

            logger.info(f"Фото успешно отправлены пользователю {user_id}")
        except Exception as e:
            logger.error(f"Ошибка при отправке пользователю {user_id}: {e}")
    else:
        logger.warning("user_id отсутствует, фото не отправлено")

    return JSONResponse({"status": "ok"})


# === Telegram Bot ===
default_properties = DefaultBotProperties(parse_mode=ParseMode.HTML)
bot = Bot(token=TELEGRAM_TOKEN, default=default_properties)
dp = Dispatcher(bot=bot)


@dp.message(Command("start"))
async def start(message: Message):
    user_id = message.from_user.id
    webapp_url = f"{RAILWAY_URL}?user_id={user_id}"
    button = KeyboardButton(text="🚀 Открыть диагностику IT-рисков", web_app=WebAppInfo(url=webapp_url))
    logger.info(f"{button}")
    keyboard = ReplyKeyboardMarkup(keyboard=[[button]], resize_keyboard=True)
    await message.answer("Привет! 👋 Нажми кнопку ниже, чтобы пройти диагностику IT-рисков:", reply_markup=keyboard)


# === Webhook для Telegram ===
@app.post("/webhook")
async def telegram_webhook(request: Request):
    body = await request.json()
    update = types.Update(**body)
    await dp.feed_update(bot, update)
    return JSONResponse({"ok": True})


@app.on_event("startup")
async def on_startup():
    webhook_url = f"{RAILWAY_URL}/webhook"
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(url=webhook_url)
    logger.info(f"Webhook установлен на {webhook_url}")


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
