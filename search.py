from aiogram import Router
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from state import SearchState
import aiohttp
from bs4 import BeautifulSoup
from storage import user_articles
from keyboards import search_list_keyboard, search_post_detail_keyboard

router = Router()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
}
# =====================
# Scraping
# =====================
async def search_posts(query: str, page: int = 1) -> dict:
    url = f"https://kun.uz/news/search?q={query}&page={page}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=HEADERS) as response:
            html = await response.text()

    soup = BeautifulSoup(html, "html.parser")
    news_block = soup.select_one("main .small-cards__default-list")
    articles = []

    if news_block:
        items = news_block.select(".small-cards__default-item")
        for item in items:
            title_tag = item.select_one(".small-cards__default-text")
            if not title_tag:
                continue

            title = title_tag.text.strip()
            href = item.get("href", "")
            post_url = "https://kun.uz" + href if href.startswith("/") else href

            date_tag = item.select_one(".gray-date p")
            date = date_tag.text.strip() if date_tag else ""

            img = item.select_one("img")
            image_url = img.get("src") if img else None

            articles.append({
                "title": title,
                "url": post_url,
                "image": image_url,
                "date": date
            })
    # Keyingi sahifa bormi tekshirish
    has_next = len(articles) >= 10

    return {
        "articles": articles,
        "page": page,
        "has_next": has_next
    }
# =====================
# Ro'yxatni ko'rsatish
# =====================
async def show_search_list(call: CallbackQuery, articles: list, page: int, has_next: bool, query: str):
    user_id = call.from_user.id
    user_articles[user_id] = articles

    text = f"🔍 <b>'{query}'</b> bo'yicha natijalar ({page}-sahifa):\n\n"
    for i, article in enumerate(articles):
        text += f"{i + 1}. {article['title']}\n"
        if article.get("date"):
            text += f"    🕐 {article['date']}\n"
        text += "\n"

    keyboard = search_list_keyboard(user_id, page, has_next, query)

    try:
        await call.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    except Exception:
        try:
            await call.message.delete()
        except Exception:
            pass
        await call.bot.send_message(
            chat_id=user_id,
            text=text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
# # =====================
# # Handlerlar
# # =====================
# @router.message(SearchState.waiting_for_query)
# async def search_handler(message: Message, state: FSMContext):
#     query = message.text.strip()
#     await state.clear()
#     await state.update_data(search_query=query)
#
#     msg = await message.answer(f"⏳ <b>'{query}'</b> qidirilmoqda...", parse_mode="HTML")
#
#     result = await search_posts(query, page=1)
#
#     if not result["articles"]:
#         await msg.edit_text("😕 Hech narsa topilmadi.")
#         return
#
#     user_articles[message.from_user.id] = result["articles"]
#
#     text = f"🔍 <b>'{query}'</b> bo'yicha natijalar (1-sahifa):\n\n"
#     for i, article in enumerate(result["articles"]):
#         text += f"{i + 1}. {article['title']}\n"
#         if article.get("date"):
#             text += f"    🕐 {article['date']}\n"
#         text += "\n"
#
#     keyboard = search_list_keyboard(message.from_user.id, 1, result["has_next"], query)
#
#     await msg.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
#
#
# @router.callback_query(lambda c: c.data and c.data.startswith("spage_"))
# async def search_page_handler(call: CallbackQuery):
#     await call.answer()
#     parts = call.data.split("_", 2)
#     page = int(parts[1])
#     query = parts[2]
#
#     await call.message.edit_text(f"⏳ <b>'{query}'</b> {page}-sahifa yuklanmoqda...", parse_mode="HTML")
#
#     result = await search_posts(query, page=page)
#
#     if not result["articles"]:
#         await call.message.edit_text("😕 Natija topilmadi.")
#         return
#
#     await show_search_list(call, result["articles"], page, result["has_next"], query)
#
#
# @router.callback_query(lambda c: c.data and c.data.startswith("spost_"))
# async def search_post_detail(call: CallbackQuery, state: FSMContext):
#     await call.answer()
#     user_id = call.from_user.id
#     index = int(call.data.split("_")[1])
#     articles = user_articles.get(user_id, [])
#
#     if not articles:
#         await call.message.edit_text("❌ Xatolik.")
#         return
#
#     article = articles[index]
#     text = f"📰 <b>{article['title']}</b>\n\n🕐 {article.get('date', '')}"
#
#     try:
#         if article.get("image"):
#             await call.message.delete()
#             await call.bot.send_photo(
#                 chat_id=user_id,
#                 photo=article["image"],
#                 caption=text,
#                 parse_mode="HTML",
#                 reply_markup=search_post_detail_keyboard(article["url"])
#             )
#         else:
#             await call.message.edit_text(
#                 text,
#                 parse_mode="HTML",
#                 reply_markup=search_post_detail_keyboard(article["url"])
#             )
#     except Exception:
#         await call.message.edit_text(
#             text,
#             parse_mode="HTML",
#             reply_markup=search_post_detail_keyboard(article["url"])
#         )
#
#
# @router.callback_query(lambda c: c.data == "back_to_search_list")
# async def back_to_search_list(call: CallbackQuery, state: FSMContext):
#     await call.answer()
#     user_id = call.from_user.id
#     articles = user_articles.get(user_id, [])
#
#     if not articles:
#         await call.message.answer("❌ Xatolik. Qaytadan qidiring.")
#         return
#
#     text = "🔍 <b>Qidiruv natijalari:</b>\n\n"
#     for i, article in enumerate(articles):
#         text += f"{i + 1}. {article['title']}\n"
#         if article.get("date"):
#             text += f"🕐 {article['date']}\n"
#         text += "\n"
#
#     builder = InlineKeyboardBuilder()
#     for i, _ in enumerate(articles):
#         builder.add(InlineKeyboardButton(text=str(i + 1), callback_data=f"spost_{i}"))
#     builder.adjust(5)
#
#     try:
#         await call.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
#     except Exception:
#         try:
#             await call.message.delete()
#         except Exception:
#             pass
#         await call.bot.send_message(
#             chat_id=user_id,
#             text=text,
#             parse_mode="HTML",
#             reply_markup=builder.as_markup()
#         )

from aiogram import Router
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from state import SearchState
import aiohttp
from bs4 import BeautifulSoup
from storage import user_articles, user_search
from keyboards import search_list_keyboard, search_post_detail_keyboard

router = Router()

HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}

# =====================
# Scraping
# =====================
async def search_posts(query: str, page: int = 1) -> dict:
    url = f"https://kun.uz/news/search?q={query}&page={page}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=HEADERS) as response:
            html = await response.text()

    soup = BeautifulSoup(html, "html.parser")
    news_block = soup.select_one("main .small-cards__default-list")
    articles = []

    if news_block:
        items = news_block.select(".small-cards__default-item")
        for item in items:
            title_tag = item.select_one(".small-cards__default-text")
            if not title_tag:
                continue

            title = title_tag.text.strip()
            href = item.get("href", "")
            post_url = "https://kun.uz" + href if href.startswith("/") else href

            date_tag = item.select_one(".gray-date p")
            date = date_tag.text.strip() if date_tag else ""

            img = item.select_one("img")
            image_url = img.get("src") if img else None

            articles.append({
                "title": title,
                "url": post_url,
                "image": image_url,
                "date": date
            })

    return {
        "articles": articles,
        "page": page,
        "has_next": len(articles) >= 10
    }

# =====================
# Ro'yxatni ko'rsatish
# =====================
async def show_search_list(call: CallbackQuery, articles: list, page: int, has_next: bool, query: str, start_num: int):
    user_id = call.from_user.id
    user_articles[user_id] = articles

    user_search[user_id] = {
        "query": query,
        "page": page,
        "has_next": has_next,
        "start_num": start_num      # ← shu sahifa boshlang'ich raqami
    }

    text = f"🔍 <b>'{query}'</b> bo'yicha natijalar ({page}-sahifa):\n\n"
    for i, article in enumerate(articles):
        text += f"{start_num + i}. {article['title']}\n"
        if article.get("date"):
            text += f"🕐 {article['date']}\n"
        text += "\n"

    keyboard = search_list_keyboard(user_id, page, has_next, query, start_num)

    try:
        await call.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    except Exception:
        try:
            await call.message.delete()
        except Exception:
            pass
        await call.bot.send_message(
            chat_id=user_id,
            text=text,
            parse_mode="HTML",
            reply_markup=keyboard
        )

# =====================
# Handlerlar
# =====================
@router.message(SearchState.waiting_for_query)
async def search_handler(message: Message, state: FSMContext):
    query = message.text.strip()
    await state.clear()

    msg = await message.answer(f"⏳ <b>'{query}'</b> qidirilmoqda...", parse_mode="HTML")
    result = await search_posts(query, page=1)

    if not result["articles"]:
        await msg.edit_text("😕 Hech narsa topilmadi.")
        return

    user_id = message.from_user.id
    user_articles[user_id] = result["articles"]
    user_search[user_id] = {
        "query": query,
        "page": 1,
        "has_next": result["has_next"],
        "start_num": 1              # ← 1-sahifa har doim 1 dan boshlanadi
    }

    text = f"🔍 <b>'{query}'</b> bo'yicha natijalar (1-sahifa):\n\n"
    for i, article in enumerate(result["articles"]):
        text += f"{i + 1}. {article['title']}\n"
        if article.get("date"):
            text += f"    🕐 {article['date']}\n"
        text += "\n"

    keyboard = search_list_keyboard(user_id, 1, result["has_next"], query, 1)
    await msg.edit_text(text, parse_mode="HTML", reply_markup=keyboard)


@router.callback_query(lambda c: c.data and c.data.startswith("spage_"))
async def search_page_handler(call: CallbackQuery):
    await call.answer()
    parts = call.data.split("_", 2)
    page = int(parts[1])
    query = parts[2]

    await call.message.edit_text(
        f"⏳ <b>'{query}'</b> {page}-sahifa yuklanmoqda...",
        parse_mode="HTML"
    )

    result = await search_posts(query, page=page)

    if not result["articles"]:
        await call.message.edit_text("😕 Natija topilmadi.")
        return

    # Oldingi sahifaning oxirgi raqamini bilish uchun
    user_id = call.from_user.id
    prev_data = user_search.get(user_id, {})
    prev_start = prev_data.get("start_num", 1)
    prev_count = len(user_articles.get(user_id, []))

    if page > prev_data.get("page", 1):
        # Oldinga ketdi → davom etadi
        start_num = prev_start + prev_count
    else:
        # Orqaga ketdi → oldingi start_num dan prev_count ayiramiz
        start_num = max(1, prev_start - len(result["articles"]))

    await show_search_list(call, result["articles"], page, result["has_next"], query, start_num)


@router.callback_query(lambda c: c.data and c.data.startswith("spost_"))
async def search_post_detail(call: CallbackQuery):
    await call.answer()
    user_id = call.from_user.id
    index = int(call.data.split("_")[1])
    articles = user_articles.get(user_id, [])

    if not articles:
        await call.message.edit_text("❌ Xatolik.")
        return

    article = articles[index]
    text = f"📰 <b>{article['title']}</b>\n\n🕐 {article.get('date', '')}"

    try:
        if article.get("image"):
            await call.message.delete()
            await call.bot.send_photo(
                chat_id=user_id,
                photo=article["image"],
                caption=text,
                parse_mode="HTML",
                reply_markup=search_post_detail_keyboard(article["url"])
            )
        else:
            await call.message.edit_text(
                text,
                parse_mode="HTML",
                reply_markup=search_post_detail_keyboard(article["url"])
            )
    except Exception:
        await call.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=search_post_detail_keyboard(article["url"])
        )


@router.callback_query(lambda c: c.data == "back_to_search_list")
async def back_to_search_list(call: CallbackQuery):
    await call.answer()
    user_id = call.from_user.id
    articles = user_articles.get(user_id, [])
    search_data = user_search.get(user_id, {})

    if not articles or not search_data:
        await call.message.answer("❌ Xatolik. Qaytadan qidiring.")
        return

    query = search_data["query"]
    page = search_data["page"]
    has_next = search_data["has_next"]
    start_num = search_data["start_num"]

    text = f"🔍 <b>'{query}'</b> bo'yicha natijalar ({page}-sahifa):\n\n"
    for i, article in enumerate(articles):
        text += f"{start_num + i}. {article['title']}\n"
        if article.get("date"):
            text += f"    🕐 {article['date']}\n"
        text += "\n"

    keyboard = search_list_keyboard(user_id, page, has_next, query, start_num)

    try:
        await call.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    except Exception:
        try:
            await call.message.delete()
        except Exception:
            pass
        await call.bot.send_message(
            chat_id=user_id,
            text=text,
            parse_mode="HTML",
            reply_markup=keyboard
        )