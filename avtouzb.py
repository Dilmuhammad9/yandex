
import asyncio
import logging
import sqlite3
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import urllib.parse
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

conn = sqlite3.connect('cars.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    year TEXT,
    brand TEXT,
    language TEXT
)
''')
conn.commit()

user_lang = {}

texts = {
    "ru": {
        "welcome": "Выберите действие:",
        "my_car": "Моя машина",
        "service": "Ближайший сервис",
        "tow": "Вызвать эвакуатор",
        "shop": "Ближайший авто-магазин",
        "buy_sell": "Купить/продать авто",
        "help": "Жалобы/Помощь",
        "main_menu": "Главное меню",
        "enter_year": "Укажите год выпуска:",
        "enter_brand": "Марка вашей машины:",
        "saved": "Сохранено:",
        "your_car": "Ваша машина:",
        "send_location": "Отправьте вашу геолокацию:",
        "nearest_service": "🔧 Ближайшие автосервисы",
        "nearest_shop": "🛒 Ближайшие автомагазины",
        "tow_number": "🚗 Для вызова эвакуатора: +79669936595",
        "recommend_sites": "🚘 Auto.ru",
        "support": "📞 @dilmuhammad9",
        "choose_action": "Выберите действие:"
    },
    "uz": {
        "welcome": "Harakatni tanlang:",
        "my_car": "Mening mashinam",
        "service": "Yaqin servis",
        "tow": "Evakutor",
        "shop": "Yaqin avto-do'kon",
        "buy_sell": "Sotib olish/sotish",
        "help": "Yordam",
        "main_menu": "Bosh menyu",
        "enter_year": "Yilni kiriting:",
        "enter_brand": "Mashina markasi:",
        "saved": "Saqlangan:",
        "your_car": "Sizning mashinangiz:",
        "send_location": "Geolokatsiyani yuboring:",
        "nearest_service": "🔧 Yaqin servislar",
        "nearest_shop": "🛒 Yaqin do'konlar",
        "tow_number": "🚗 Evakuator: +79669936595",
        "recommend_sites": "🚘 Auto.ru",
        "support": "📞 @dilmuhammad9",
        "choose_action": "Harakatni tanlang:"
    }
}

def get_text(user_id, key):
    lang = user_lang.get(user_id, "ru")
    return texts[lang].get(key, texts["ru"][key])

lang_button_ru = KeyboardButton(text="🇷🇺 Русский")
lang_button_uz = KeyboardButton(text="🇺🇿 O'zbekcha")

lang_keyboard = ReplyKeyboardMarkup(
    keyboard=[[lang_button_ru, lang_button_uz]],
    resize_keyboard=True
)

def get_main_keyboard(user_id):
    lang = user_lang.get(user_id, "ru")
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=texts[lang]["my_car"])],
            [KeyboardButton(text=texts[lang]["service"]), KeyboardButton(text=texts[lang]["tow"])],
            [KeyboardButton(text=texts[lang]["shop"])],
            [KeyboardButton(text=texts[lang]["buy_sell"])],
            [KeyboardButton(text=texts[lang]["help"])],
            [KeyboardButton(text=texts[lang]["main_menu"])]
        ],
        resize_keyboard=True
    )

def get_temp_keyboard(user_id):
    lang = user_lang.get(user_id, "ru")
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=texts[lang]["main_menu"])]],
        resize_keyboard=True
    )

geo_button = KeyboardButton(text="📍 Отправить геолокацию", request_location=True)
location_state = {}

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Выберите язык / Tilni tanlang:", reply_markup=lang_keyboard)

@dp.message(lambda message: message.text in ["🇷🇺 Русский", "🇺🇿 O'zbekcha"])
async def set_language(message: types.Message):
    user = message.from_user.id
    if message.text == "🇷🇺 Русский":
        user_lang[user] = "ru"
    else:
        user_lang[user] = "uz"

    cursor.execute("INSERT OR REPLACE INTO users (user_id, language) VALUES (?, ?)", (user, user_lang[user]))
    conn.commit()

    await message.answer(get_text(user, "welcome"), reply_markup=get_main_keyboard(user))

@dp.message()
async def handle(message: types.Message):
    user = message.from_user.id

    if user not in user_lang:
        await message.answer("Выберите язык / Tilni tanlang:", reply_markup=lang_keyboard)
        return

    lang = user_lang.get(user, "ru")

    if message.text == texts[lang]["main_menu"]:
        await message.answer(get_text(user, "choose_action"), reply_markup=get_main_keyboard(user))
        if user in location_state:
            del location_state[user]

    elif message.text == texts[lang]["my_car"]:
        cursor.execute("SELECT year, brand FROM users WHERE user_id = ?", (user,))
        car_data = cursor.fetchone()

        if car_data and car_data[0] and car_data[1]:
            await message.answer(f"{get_text(user, 'your_car')} {car_data[1]} {car_data[0]}", reply_markup=get_main_keyboard(user))
        else:
            await message.answer(get_text(user, "enter_year"), reply_markup=get_temp_keyboard(user))
            location_state[user] = "year"

    elif user in location_state and location_state[user] == "year":
        cursor.execute("INSERT OR REPLACE INTO users (user_id, year) VALUES (?, ?)", (user, message.text))
        conn.commit()
        await message.answer(get_text(user, "enter_brand"), reply_markup=get_temp_keyboard(user))
        location_state[user] = "brand"

    elif user in location_state and location_state[user] == "brand":
        cursor.execute("UPDATE users SET brand = ? WHERE user_id = ?", (message.text, user))
        conn.commit()
        await message.answer(f"{get_text(user, 'saved')} {message.text}")
        del location_state[user]
        await message.answer(get_text(user, "choose_action"), reply_markup=get_main_keyboard(user))

    elif message.text == texts[lang]["service"]:
        await message.answer(get_text(user, "send_location"), reply_markup=ReplyKeyboardMarkup(
            keyboard=[[geo_button], [KeyboardButton(text=get_text(user, "main_menu"))]], resize_keyboard=True
        ))
        location_state[user] = "service"

    elif message.text == texts[lang]["shop"]:
        await message.answer(get_text(user, "send_location"), reply_markup=ReplyKeyboardMarkup(
            keyboard=[[geo_button], [KeyboardButton(text=get_text(user, "main_menu"))]], resize_keyboard=True
        ))
        location_state[user] = "shop"

    elif message.location:
        lat = message.location.latitude
        lon = message.location.longitude
        search_type = location_state.get(user)

        if search_type == "service":
            query = "автосервис"
            answer_text = get_text(user, "nearest_service")
        elif search_type == "shop":
            query = "автомагазин"
            answer_text = get_text(user, "nearest_shop")
        else:
            await message.answer("Сначала выберите 'Ближайший сервис' или 'Ближайший авто-магазин'", reply_markup=get_main_keyboard(user))
            return

        yandex_url = f"https://yandex.ru/maps/?text={urllib.parse.quote(query)}&ll={lon},{lat}&z=15"

        await message.answer(
            f"{answer_text}:\n[Открыть в Яндекс.Картах]({yandex_url})",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard(user)
        )

        if user in location_state:
            del location_state[user]

    elif message.text == texts[lang]["tow"]:
        await message.answer(get_text(user, "tow_number"), reply_markup=get_main_keyboard(user))

    elif message.text == texts[lang]["buy_sell"]:
        await message.answer(get_text(user, "recommend_sites"), reply_markup=get_main_keyboard(user))

    elif message.text == texts[lang]["help"]:
        await message.answer(get_text(user, "support"), reply_markup=get_main_keyboard(user))

async def main():
    await dp.start_polling(bot)

await main()
