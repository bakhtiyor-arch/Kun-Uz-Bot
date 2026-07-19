from aiogram import Router
from aiogram.types import CallbackQuery, InputMediaPhoto
import aiohttp
from bs4 import BeautifulSoup
from keyboards import (
    CategoryCallback,
    get_categories_keyboard,
    news_list_keyboard,
    post_detail_keyboard
)
from storage import user_articles

router = Router()
BASE_URL = "https://kun.uz/news/category"


# =====================
# Scraping
# =====================

async def get_posts(slug: str) -> list[dict]:
    url = f"https://kun.uz/news/category/{slug}"
    headers = {"User-Agent": "Mozilla/5.0"}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            html = await response.text()

    soup = BeautifulSoup(html, "html.parser")

    # ← Shu selektor to'g'ri
    news_list = soup.select("a.news-page__item")
    articles = []

    for item in news_list[:10]:
        # Title
        h3 = item.select_one("h3")
        if not h3:
            continue

        title = h3.text.strip()

        # URL
        href = item.get("href", "")
        post_url = "https://kun.uz" + href if href.startswith("/") else href

        # Rasm
        img = item.select_one("img")
        image_url = None
        if img:
            image_url = img.get("src") or img.get("data-src")

        articles.append({
            "title": title,
            "url": post_url,
            "image": image_url,
        })

    return articles

# =====================
# Ro'yxatni ko'rsatish
# =====================
async def show_list(call: CallbackQuery):
    user_id = call.from_user.id
    articles = user_articles.get(user_id, [])

    if not articles:
        await call.message.answer("❌ Xatolik. Qaytadan urinib ko'ring.")
        return

    text = "📋 <b>Yangiliklar ro'yxati:</b>\n\n"
    for i, article in enumerate(articles):
        text += f"{i + 1}. {article['title']}\n"

    try:
        await call.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=news_list_keyboard(user_id)
        )
    except Exception:
        # Rasm bo'lgan xabar — o'chirib yangi yuborish
        try:
            await call.message.delete()
        except Exception:
            pass
        await call.bot.send_message(
            chat_id=user_id,
            text=text,
            parse_mode="HTML",
            reply_markup=news_list_keyboard(user_id)
        )

# =====================
# Handlerlar
# =====================
@router.callback_query(CategoryCallback.filter())
async def category_handler(call: CallbackQuery, callback_data: CategoryCallback):
    await call.answer()
    await call.message.edit_text(f"⏳ <b>{callback_data.name}</b> yuklanmoqda...", parse_mode="HTML")

    articles = await get_posts(callback_data.slug)

    if not articles:
        await call.message.edit_text("😕 Yangiliklar topilmadi.", reply_markup=get_categories_keyboard())
        return

    user_articles[call.from_user.id] = articles
    await show_list(call)

@router.callback_query(lambda c: c.data and c.data.startswith("post_"))
async def post_detail_handler(call: CallbackQuery):
    await call.answer()
    user_id = call.from_user.id
    index = int(call.data.split("_")[1])
    articles = user_articles.get(user_id, [])
    if not articles:
        await call.message.edit_text("❌ Xatolik.")
        return
    article = articles[index]
    text = f"📰 <b>{article['title']}</b>"

    try:
        if article.get("image"):
            await call.message.delete()
            await call.bot.send_photo(
                chat_id=user_id,
                photo=article["image"],
                caption=text,
                parse_mode="HTML",
                reply_markup=post_detail_keyboard(article["url"])
            )
        else:
            await call.message.edit_text(
                text,
                parse_mode="HTML",
                reply_markup=post_detail_keyboard(article["url"])
            )
    except Exception:
        await call.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=post_detail_keyboard(article["url"])
        )

@router.callback_query(lambda c: c.data == "back_to_list")
async def back_to_list_handler(call: CallbackQuery):
    await call.answer()
    await show_list(call)

@router.callback_query(lambda c: c.data == "back_to_categories")
async def back_to_categories_handler(call: CallbackQuery):
    await call.answer()
    await call.message.edit_text(
        "Kategoriyani tanlang:",
        reply_markup=get_categories_keyboard()
    )

@router.callback_query(lambda c: c.data == "none")
async def none_handler(call: CallbackQuery):
    await call.answer()
