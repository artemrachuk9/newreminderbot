import telebot
import threading
import time
import re
import requests
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from telebot import types

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

reminders = []
user_locations = {}  # chat_id → (lat, lon)
user_languages = {}  # chat_id → 'uk', 'ru', 'en'

MESSAGES = {
    "uk": {
        "start": "Привіт! Я бот-нагадувач 📅\n\nПросто напиши щось типу:\n👉 завтра день народження мами\n👉 зустріч 12.09\nІ я нагадаю тобі у цей день + надішлю прогноз погоди!\n\nЩоб прогноз був точним — напиши своє місто:\n📝 приклад: \"місто Нью-Йорк\" або \"погода Київ\"",
        "choose_lang": "🌍 Обери мову / Choose your language:",
        "saved_city": "✅ Місто \"{}\" збережено!",
        "city_not_found": "⚠️ Не вдалося знайти місто \"{}\"",
        "weather": "🌦 Погода в \"{}\":\n{}",
        "reminder_saved": "✅ Нагадування збережено на {}\n🌦 Прогноз погоди: {}",
        "no_date": "🤔 Я не знайшов дату в повідомленні.\nНапиши щось типу: \"зустріч 12.09\" або \"завтра день народження мами\"",
        "today_reminder": "📌 Сьогодні: {}"
    },
    "ru": {
        "start": "Привет! Я бот-напоминалка 📅\n\nПросто напиши:\n👉 завтра день рождения мамы\n👉 встреча 12.09\nЯ напомню тебе в этот день + пришлю прогноз погоды!\n\nЧтобы прогноз был точным — напиши свой город:\n📝 пример: \"город Нью-Йорк\" или \"погода Киев\"",
        "choose_lang": "🌍 Выбери язык / Choose your language:",
        "saved_city": "✅ Город \"{}\" сохранён!",
        "city_not_found": "⚠️ Не удалось найти город \"{}\"",
        "weather": "🌦 Погода в \"{}\":\n{}",
        "reminder_saved": "✅ Напоминание сохранено на {}\n🌦 Прогноз погоды: {}",
        "no_date": "🤔 Я не нашёл дату в сообщении.\nНапиши что-то вроде: \"встреча 12.09\" или \"завтра день рождения мамы\"",
        "today_reminder": "📌 Сегодня: {}"
    },
    "en": {
        "start": "Hi! I'm your reminder bot 📅\n\nJust type something like:\n👉 tomorrow is mom's birthday\n👉 meeting on 12.09\nI'll remind you on that day + send the weather forecast!\n\nTo get accurate weather — tell me your city:\n📝 example: \"city New York\" or \"weather Kyiv\"",
        "choose_lang": "🌍 Choose your language:",
        "saved_city": "✅ City \"{}\" saved!",
        "city_not_found": "⚠️ Couldn't find city \"{}\"",
        "weather": "🌦 Weather in \"{}\":\n{}",
        "reminder_saved": "✅ Reminder saved for {}\n🌦 Weather forecast: {}",
        "no_date": "🤔 I couldn't find a date in your message.\nTry something like: \"meeting on 12.09\" or \"tomorrow is mom's birthday\"",
        "today_reminder": "📌 Today: {}"
    }
}

@bot.message_handler(commands=['start'])
def start_message(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("Українська 🇺🇦", "Русский 🇷🇺", "English 🇬🇧")
    bot.send_message(message.chat.id, MESSAGES["uk"]["choose_lang"], reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.text in ["Українська 🇺🇦", "Русский 🇷🇺", "English 🇬🇧"])
def set_language(msg):
    lang_map = {
        "Українська 🇺🇦": "uk",
        "Русский 🇷🇺": "ru",
        "English 🇬🇧": "en"
    }
    user_languages[msg.chat.id] = lang_map[msg.text]
    lang = user_languages[msg.chat.id]
    bot.send_message(msg.chat.id, MESSAGES[lang]["start"])

def extract_date(text):
    text = text.lower()
    today = datetime.now().date()

    if "завтра" in text or "tomorrow" in text:
        return today + timedelta(days=1)

    months_uk = {
        'січня': 1, 'лютого': 2, 'березня': 3, 'квітня': 4,
        'травня': 5, 'червня': 6, 'липня': 7, 'серпня': 8,
        'вересня': 9, 'жовтня': 10, 'листопада': 11, 'грудня': 12
    }

    months_en = {
        'january': 1, 'february': 2, 'march': 3, 'april': 4,
        'may': 5, 'june': 6, 'july': 7, 'august': 8,
        'september': 9, 'october': 10, 'november': 11, 'december': 12
    }

    match = re.search(r'(\d{1,2})[.\-/](\d{1,2})', text)
    if match:
        day, month = int(match.group(1)), int(match.group(2))
        try:
            return datetime(datetime.now().year, month, day).date()
        except:
            return None

    match = re.search(r'(\d{1,2})\s+(січня|лютого|березня|квітня|травня|червня|липня|серпня|вересня|жовтня|листопада|грудня)', text)
    if match:
        day = int(match.group(1))
        month = months_uk.get(match.group(2))
        try:
            return datetime(datetime.now().year, month, day).date()
        except:
            return None

    match = re.search(r'(\d{1,2})\s+(january|february|march|april|may|june|july|august|september|october|november|december)', text)
    if match:
        day = int(match.group(1))
        month = months_en.get(match.group(2))
        try:
            return datetime(datetime.now().year, month, day).date()
        except:
            return None

    match = re.search(r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})', text)
    if match:
        month = months_en.get(match.group(1))
        day = int(match.group(2))
        try:
            return datetime(datetime.now().year, month, day).date()
        except:
            return None

    return None

def get_coordinates_by_city(city_name):
    url = f"https://nominatim.openstreetmap.org/search?format=json&q={city_name}"
    try:
        response = requests.get(url, headers={"User-Agent": "weather-bot"})
        data = response.json()
        if data:
            lat = float(data[0]['lat'])
            lon = float(data[0]['lon'])
            return lat, lon
    except:
        pass
    return None

def get_weather_forecast(date_obj, lat=52.4420, lon=4.8292, hour=12):
    date_str = date_obj.strftime('%Y-%m-%d')
    hour_str = f"{hour:02d}:00"
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}&hourly=temperature_2m,"
        f"relative_humidity_2m,wind_speed_10m&timezone=Europe/Amsterdam"
    )

    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            target_time = f"{date_str}T{hour_str}"
            if target_time in data['hourly']['time']:
                index = data['hourly']['time'].index(target_time)
                temp = data['hourly']['temperature_2m'][index]
                humidity = data['hourly']['relative_humidity_2m'][index]
                wind = data['hourly']['wind_speed_10m'][index]

                if temp >= 20 and humidity < 60:
                    comment = "☀ Гарний день! Не забудь окуляри 😎"
                elif humidity > 80 or wind > 10:
                    comment = "🌧 Може бути непогода — будь обережний!"
                else:
                    comment = "🌤 Звичайна погода, все ок!"

                return f"{temp}°C, вологість {humidity}%, вітер {wind} км/год\n{comment}"
        return "⚠️ Не вдалося отримати прогноз погоди"
    except:
        return "⚠️ Помилка при отриманні прогнозу погоди"

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text.strip()
    lang = user_languages.get(message.chat.id, "uk")

    if any(text.lower().startswith(prefix) for prefix in ["місто ", "город ", "city "]):
        city_name = re.sub(r"^(місто|город|city)\s+", "", text, flags=re.IGNORECASE).strip()
        coords = get_coordinates_by_city(city_name)
        if coords:
            user_locations[message.chat.id] = coords
            bot.send_message(message.chat.id, MESSAGES[lang]["saved_city"].format(city_name))
        else:
            bot.send_message(message.chat.id, MESSAGES[lang]["city_not_found"].format(city_name))
        return

    if text.lower().startswith("погода ") or text.lower().startswith("weather "):
        city_name = re.sub(r"^(погода|weather)\s+", "", text, flags=re.IGNORECASE).strip()
        coords = get_coordinates_by_city(city_name)
        if coords:
            user_locations[message.chat.id] = coords
            forecast = get_weather_forecast(datetime.now().date(), lat=coords[0], lon=coords[1])
            bot.send_message(message.chat.id, MESSAGES[lang]["weather"].format(city_name, forecast))
        else:
            bot.send_message(message.chat.id, MESSAGES[lang]["city_not_found"].format(city_name))
        return

    date = extract_date(text)
    if date:
        reminders.append((message.chat.id, date, text))
        latlon = user_locations.get(message.chat.id, (52.4420, 4.8292))
        forecast = get_weather_forecast(date, lat=latlon[0], lon=latlon[1])
        bot.send_message(message.chat.id, MESSAGES[lang]["reminder_saved"].format(date.strftime('%d.%m'), forecast))
    else:
        bot.send_message(message.chat.id, MESSAGES[lang]["no_date"])

def reminder_checker():
    while True:
        today = datetime.now().date()
        for r in reminders[:]:
            chat_id, r_date, text = r
            if r_date == today:
                lang = user_languages.get(chat_id, "uk")
                bot.send_message(chat_id, MESSAGES[lang]["today_reminder"].format(text))
                reminders.remove(r)
        time.sleep(3600)

threading.Thread(target=reminder_checker).start()
bot.polling()
