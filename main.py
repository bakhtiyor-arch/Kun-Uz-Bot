import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from config_reader import config
from keyboards import home, get_categories_keyboard
from state import SearchState
import category
import search




bot = Bot(token=config.bot_token.get_secret_value())
dp = Dispatcher()

START_TEXT = """Salom! 👋
Men <b>kun.uz</b> saytidan tasdiqlangan ma'lumotlarni tashlayman.
"""

@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(START_TEXT, reply_markup=home, parse_mode="HTML")

@dp.message(F.text == "📂 Kategoriyalar")
async def categories(message: Message):
    await message.answer("Kategoriyani tanlang:", reply_markup=get_categories_keyboard())



@dp.message(F.text == "🔍 Qidiruv")
async def search_start(message: Message, state: FSMContext):
    await state.set_state(SearchState.waiting_for_query)
    await message.answer("🔍 Qidiruv so'zini yozing:")

async def main():
    print("Bot ishga tushdi...")
    dp.include_router(category.router)
    dp.include_router(search.router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())