from aiogram.types import InlineKeyboardButton, KeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from storage import user_articles
from aiogram.filters.callback_data import CallbackData



base = ReplyKeyboardBuilder()
base.add(KeyboardButton(text="📂 Kategoriyalar"))
base.add(KeyboardButton(text="🔍 Qidiruv"))

home = base.as_markup(
    resize_keyboard=True,
)

class CategoryCallback(CallbackData, prefix="category"):
    slug: str
    name: str


CATEGORIES = [
    {"name": "🇺🇿 O'zbekiston", "slug": "uzbekiston"},
    {"name": "🌍 Dunyo", "slug": "jahon"},
    {"name": "💰 Iqtisodiyot", "slug": "iqtisodiyot"},
    {"name": "⚽ Sport", "slug": "sport"},
    {"name": "🏛 Jamiyat", "slug": "jamiyat"},
    {"name": "💻 Texnologiya", "slug": "texnologiya"},
]


def get_categories_keyboard():
    builder = InlineKeyboardBuilder()
    for cat in CATEGORIES:
        builder.add(InlineKeyboardButton(text=cat["name"],
            callback_data=CategoryCallback(
                slug=cat["slug"],
                name=cat["name"]
            ).pack()))
    builder.adjust(2)  # ← 2 ustun
    return builder.as_markup()



def news_list_keyboard(user_id: int) -> InlineKeyboardMarkup:
    articles = user_articles.get(user_id, [])
    post = InlineKeyboardBuilder()

    for i, _ in enumerate(articles):
        post.add(InlineKeyboardButton(
            text=str(i + 1),
            callback_data=f"post_{i}"
        ))
    post.adjust(5)

    post.row(InlineKeyboardButton(
        text="🔙 Kategoriyalarga",
        callback_data="back_to_categories"
    ))
    return post.as_markup()

def post_detail_keyboard(url: str) -> InlineKeyboardMarkup:
    post_detail = InlineKeyboardBuilder()
    post_detail.add(InlineKeyboardButton(
        text="🔗 Batafsil",
        url=url
    ))
    post_detail.add(InlineKeyboardButton(
        text="🔙 Ro'yxatga",
        callback_data="back_to_list"
    ))
    post_detail.adjust(1)
    return post_detail.as_markup()






def search_list_keyboard(user_id: int, page: int, has_next: bool, query: str, start_num: int = 1) -> InlineKeyboardMarkup:
    articles = user_articles.get(user_id, [])
    builder = InlineKeyboardBuilder()

    for i, _ in enumerate(articles):
        builder.add(InlineKeyboardButton(
            text=str(start_num + i),
            callback_data=f"spost_{i}"
        ))
    builder.adjust(5)

    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton(
            text="⬅️ Oldingi",
            callback_data=f"spage_{page - 1}_{query}"
        ))
    nav.append(InlineKeyboardButton(
        text=f"{page}-sahifa",
        callback_data="none"
    ))
    if has_next:
        nav.append(InlineKeyboardButton(
            text="Keyingi ➡️",
            callback_data=f"spage_{page + 1}_{query}"
        ))
    if nav:
        builder.row(*nav)

    return builder.as_markup()


def search_post_detail_keyboard(url: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🔗 Batafsil", url=url))
    builder.add(InlineKeyboardButton(text="🔙 Ro'yxatga", callback_data="back_to_search_list"))
    builder.adjust(1)
    return builder.as_markup()