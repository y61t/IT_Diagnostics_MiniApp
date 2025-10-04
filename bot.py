import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import WebAppInfo, KeyboardButton, ReplyKeyboardMarkup, Message
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.client.bot import DefaultBotProperties

# 🔹 Твой токен
TOKEN = "8359824125:AAHHLNhEyTqYr7jYmJWEXAAOP3EapVnNOKE"

# 🔹 Создаём объект бота с дефолтными свойствами
default_properties = DefaultBotProperties(parse_mode=ParseMode.HTML)
bot = Bot(token=TOKEN, default=default_properties)

# 🔹 Создаём диспетчер (без передачи bot!)
dp = Dispatcher()


# 🔹 Обработчик команды /start
@dp.message(Command("start"))
async def start(message: Message):
    button = KeyboardButton(
        text="🚀 Открыть диагностику IT-рисков",
        web_app=WebAppInfo(url="http://127.0.0.1:8000")
    )

    keyboard = ReplyKeyboardMarkup(
        keyboard=[[button]],
        resize_keyboard=True
    )

    await message.answer(
        "Привет! 👋 Нажми кнопку ниже, чтобы пройти диагностику IT-рисков:",
        reply_markup=keyboard
    )



# 🔹 Основная функция запуска бота
async def main():
    print("Бот запущен ✅")
    # Передаём bot при старте polling
    await dp.start_polling(bot)


# 🔹 Точка входа
if __name__ == "__main__":
    asyncio.run(main())
