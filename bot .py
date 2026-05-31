import logging
import requests
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, ContextTypes, filters
)

# ============ CONFIGURATION ============
BOT_TOKEN = "8760942618:AAEscImksD1w4-lQbC7wcN91j2H9W4D7PxM"
GOOGLE_SHEET_URL = "https://script.google.com/macros/s/AKfycbxhdWxU1yqlCdIjFxPSv9Wwp3KMmWvwSBD3XL_LKdQPSj-fozDiv7E0CNnql5dkpuSAug/exec"
MANAGER_USERNAME = "India_medservice"
STARTING_SERIAL = 236

# Specialty groups — add more group IDs as you create them
SPECIALTY_GROUPS = {
    "oncology":    "-5107088561",
    "cardiology":  "-5107088561",  # Replace with real group IDs later
    "orthopedics": "-5107088561",
    "neurology":   "-5107088561",
    "other":       "-5107088561",
}

# ============ CONVERSATION STATES ============
LANGUAGE, FULL_NAME, GENDER_AGE, PHONE, SPECIALTY, COMPLAINTS, FILES, CONFIRM = range(8)

# ============ TRANSLATIONS ============
TEXTS = {
    "ru": {
        "welcome": (
            "👋 Добро пожаловать в *India Med Service!*\n\n"
            "Мы поможем вам получить консультацию у лучших врачей Индии.\n\n"
            "Выберите язык:"
        ),
        "ask_name": "📝 Введите ваше *полное имя (ФИО)*:",
        "ask_gender_age": "👤 Введите ваш *пол и возраст*:\n_(Пример: Мужской, 35)_",
        "ask_phone": "📞 Введите ваш *номер телефона*:\n_(Пример: +998901234567)_",
        "ask_specialty": "🏥 Выберите *направление*:",
        "ask_complaints": "🩺 Опишите ваши *жалобы и симптомы* подробно:",
        "ask_files": (
            "📎 Отправьте ваши *анализы и медицинские документы* (фото или файлы).\n\n"
            "Можно отправить несколько файлов по одному.\n\n"
            "Когда закончите — нажмите кнопку ✅ ниже."
        ),
        "files_done_btn": "✅ Все файлы отправлены",
        "file_received": "📎 Файл получен! Отправьте ещё или нажмите кнопку ниже.",
        "confirm": (
            "📋 *Проверьте ваши данные перед отправкой:*\n\n"
            "👤 Имя: *{name}*\n"
            "⚥ Пол/Возраст: *{gender_age}*\n"
            "📞 Телефон: *{phone}*\n"
            "🏥 Направление: *{specialty}*\n"
            "🩺 Жалобы: *{complaints}*\n"
            "📎 Файлов отправлено: *{files_count}*\n\n"
            "Всё верно? Отправить врачу?"
        ),
        "yes": "✅ Да, отправить врачу",
        "no": "❌ Нет, начать заново",
        "success": (
            "✅ *Ваша заявка успешно принята!*\n\n"
            "🔢 Ваш номер заявки: *#{serial}*\n\n"
            "📞 Наш менеджер свяжется с вами по номеру *{phone}* в ближайшее время.\n\n"
            "Спасибо, что обратились в *India Med Service!* 🙏"
        ),
        "cancelled": "❌ Заявка отменена. Напишите /start чтобы начать заново.",
        "specialties": {
            "oncology":    "🎗 Онкология",
            "cardiology":  "❤️ Кардиология",
            "orthopedics": "🦴 Ортопедия",
            "neurology":   "🧠 Неврология",
            "other":       "🏥 Другое",
        }
    },
    "uz": {
        "welcome": (
            "👋 *India Med Service* ga xush kelibsiz!\n\n"
            "Biz sizga Hindistonning eng yaxshi shifokorlari bilan maslahat olishga yordam beramiz.\n\n"
            "Tilni tanlang:"
        ),
        "ask_name": "📝 *To'liq ismingizni (FIO)* kiriting:",
        "ask_gender_age": "👤 *Jins va yoshingizni* kiriting:\n_(Misol: Erkak, 35)_",
        "ask_phone": "📞 *Telefon raqamingizni* kiriting:\n_(Misol: +998901234567)_",
        "ask_specialty": "🏥 *Yo'nalishni* tanlang:",
        "ask_complaints": "🩺 *Shikoyat va belgilaringizni* batafsil yozing:",
        "ask_files": (
            "📎 *Tahlil va tibbiy hujjatlaringizni* yuboring (rasm yoki fayl).\n\n"
            "Bir nechta fayl yuborish mumkin.\n\n"
            "Tugagach — pastdagi tugmani bosing ✅"
        ),
        "files_done_btn": "✅ Barcha fayllar yuborildi",
        "file_received": "📎 Fayl qabul qilindi! Yana yuboring yoki tugmani bosing.",
        "confirm": (
            "📋 *Yuborishdan oldin ma'lumotlaringizni tekshiring:*\n\n"
            "👤 Ism: *{name}*\n"
            "⚥ Jins/Yosh: *{gender_age}*\n"
            "📞 Telefon: *{phone}*\n"
            "🏥 Yo'nalish: *{specialty}*\n"
            "🩺 Shikoyatlar: *{complaints}*\n"
            "📎 Yuborilgan fayllar: *{files_count}*\n\n"
            "Hammasi to'g'rimi? Shifokorga yuborasizmi?"
        ),
        "yes": "✅ Ha, shifokorga yuborish",
        "no": "❌ Yo'q, qaytadan boshlash",
        "success": (
            "✅ *Arizangiz muvaffaqiyatli qabul qilindi!*\n\n"
            "🔢 Ariza raqamingiz: *#{serial}*\n\n"
            "📞 Menejerimiz *{phone}* raqamiga tez orada murojaat qiladi.\n\n"
            "*India Med Service* ga murojaat qilganingiz uchun rahmat! 🙏"
        ),
        "cancelled": "❌ Ariza bekor qilindi. Qaytadan boshlash uchun /start yozing.",
        "specialties": {
            "oncology":    "🎗 Onkologiya",
            "cardiology":  "❤️ Kardiologiya",
            "orthopedics": "🦴 Ortopediya",
            "neurology":   "🧠 Nevrologiya",
            "other":       "🏥 Boshqa",
        }
    },
    "kz": {
        "welcome": (
            "👋 *India Med Service* қызметіне қош келдіңіз!\n\n"
            "Біз сізге Үндістанның үздік дәрігерлерімен кеңес алуға көмектесеміз.\n\n"
            "Тілді таңдаңыз:"
        ),
        "ask_name": "📝 *Толық атыңызды (АӘТ)* енгізіңіз:",
        "ask_gender_age": "👤 *Жынысыңыз бен жасыңызды* енгізіңіз:\n_(Мысалы: Ер, 35)_",
        "ask_phone": "📞 *Телефон нөміріңізді* енгізіңіз:\n_(Мысалы: +77001234567)_",
        "ask_specialty": "🏥 *Бағытты* таңдаңыз:",
        "ask_complaints": "🩺 *Шағымдарыңыз бен белгілеріңізді* толық жазыңыз:",
        "ask_files": (
            "📎 *Талдау және медициналық құжаттарыңызды* жіберіңіз (сурет немесе файл).\n\n"
            "Бірнеше файл жіберуге болады.\n\n"
            "Аяқтағанда — төмендегі түймені басыңыз ✅"
        ),
        "files_done_btn": "✅ Барлық файлдар жіберілді",
        "file_received": "📎 Файл қабылданды! Тағы жіберіңіз немесе түймені басыңыз.",
        "confirm": (
            "📋 *Жіберер алдында деректеріңізді тексеріңіз:*\n\n"
            "👤 Аты: *{name}*\n"
            "⚥ Жынысы/Жасы: *{gender_age}*\n"
            "📞 Телефон: *{phone}*\n"
            "🏥 Бағыт: *{specialty}*\n"
            "🩺 Шағымдар: *{complaints}*\n"
            "📎 Жіберілген файлдар: *{files_count}*\n\n"
            "Бәрі дұрыс па? Дәрігерге жіберу керек пе?"
        ),
        "yes": "✅ Иә, дәрігерге жіберу",
        "no": "❌ Жоқ, қайтадан бастау",
        "success": (
            "✅ *Өтінішіңіз сәтті қабылданды!*\n\n"
            "🔢 Өтініш нөміріңіз: *#{serial}*\n\n"
            "📞 Менеджеріміз *{phone}* нөміріне жақын арада хабарласады.\n\n"
            "*India Med Service* қызметіне жүгінгеніңіз үшін рахмет! 🙏"
        ),
        "cancelled": "❌ Өтініш бас тартылды. Қайтадан бастау үшін /start жазыңыз.",
        "specialties": {
            "oncology":    "🎗 Онкология",
            "cardiology":  "❤️ Кардиология",
            "orthopedics": "🦴 Ортопедия",
            "neurology":   "🧠 Неврология",
            "other":       "🏥 Басқа",
        }
    }
}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def t(lang, key):
    return TEXTS.get(lang, TEXTS["ru"]).get(key, TEXTS["ru"].get(key, ""))

def save_patient(data):
    try:
        requests.post(GOOGLE_SHEET_URL, json=data, timeout=10)
    except Exception as e:
        logger.error(f"Sheet save error: {e}")

def save_doctor_response(serial, response):
    try:
        requests.post(GOOGLE_SHEET_URL, json={
            "type": "doctor_response",
            "serial": f"#{serial}",
            "response": response
        }, timeout=10)
    except Exception as e:
        logger.error(f"Doctor response save error: {e}")

# ============ HANDLERS ============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton("🇺🇿 O'zbek", callback_data="lang_uz")],
        [InlineKeyboardButton("🇰🇿 Қазақша", callback_data="lang_kz")],
    ])
    await update.message.reply_text(TEXTS["ru"]["welcome"], reply_markup=keyboard, parse_mode="Markdown")
    return LANGUAGE

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data.split("_")[1]
    context.user_data["lang"] = lang
    await query.edit_message_text(t(lang, "ask_name"), parse_mode="Markdown")
    return FULL_NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data["lang"]
    context.user_data["full_name"] = update.message.text
    await update.message.reply_text(t(lang, "ask_gender_age"), parse_mode="Markdown")
    return GENDER_AGE

async def get_gender_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data["lang"]
    context.user_data["gender_age"] = update.message.text
    await update.message.reply_text(t(lang, "ask_phone"), parse_mode="Markdown")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data["lang"]
    context.user_data["phone"] = update.message.text
    specs = t(lang, "specialties")
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(v, callback_data=f"spec_{k}")] for k, v in specs.items()])
    await update.message.reply_text(t(lang, "ask_specialty"), reply_markup=keyboard, parse_mode="Markdown")
    return SPECIALTY

async def get_specialty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data["lang"]
    key = query.data.replace("spec_", "")
    context.user_data["specialty_key"] = key
    context.user_data["specialty"] = t(lang, "specialties").get(key, key)
    await query.edit_message_text(t(lang, "ask_complaints"), parse_mode="Markdown")
    return COMPLAINTS

async def get_complaints(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data["lang"]
    context.user_data["complaints"] = update.message.text
    context.user_data["files"] = []
    context.user_data["file_ids"] = []
    keyboard = ReplyKeyboardMarkup([[KeyboardButton(t(lang, "files_done_btn"))]], resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(t(lang, "ask_files"), reply_markup=keyboard, parse_mode="Markdown")
    return FILES

async def get_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data["lang"]
    done_btn = t(lang, "files_done_btn")

    if update.message.text and update.message.text == done_btn:
        return await show_confirm(update, context)

    if update.message.photo:
        fid = update.message.photo[-1].file_id
        context.user_data["file_ids"].append(("photo", fid))
        context.user_data["files"].append("[Фото]")
        await update.message.reply_text(t(lang, "file_received"))
    elif update.message.document:
        fid = update.message.document.file_id
        fname = update.message.document.file_name or "document"
        context.user_data["file_ids"].append(("document", fid))
        context.user_data["files"].append(f"[{fname}]")
        await update.message.reply_text(t(lang, "file_received"))

    return FILES

async def show_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data["lang"]
    files_count = len(context.user_data.get("files", []))
    text = t(lang, "confirm").format(
        name=context.user_data.get("full_name", ""),
        gender_age=context.user_data.get("gender_age", ""),
        phone=context.user_data.get("phone", ""),
        specialty=context.user_data.get("specialty", ""),
        complaints=context.user_data.get("complaints", ""),
        files_count=files_count
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(t(lang, "yes"), callback_data="confirm_yes")],
        [InlineKeyboardButton(t(lang, "no"), callback_data="confirm_no")],
    ])
    await update.message.reply_text(text, reply_markup=ReplyKeyboardRemove(), parse_mode="Markdown")
    await update.message.reply_text("👆", reply_markup=keyboard)
    return CONFIRM

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data["lang"]

    if query.data == "confirm_no":
        await query.edit_message_text(t(lang, "cancelled"))
        return ConversationHandler.END

    # Generate serial
    if "serial_counter" not in context.bot_data:
        context.bot_data["serial_counter"] = STARTING_SERIAL
    else:
        context.bot_data["serial_counter"] += 1
    serial = context.bot_data["serial_counter"]

    files_str = ", ".join(context.user_data.get("files", [])) or "—"
    specialty_key = context.user_data.get("specialty_key", "other")
    group_id = SPECIALTY_GROUPS.get(specialty_key, SPECIALTY_GROUPS["other"])

    # Save to Google Sheets
    save_patient({
        "type": "patient",
        "serial": f"#{serial}",
        "full_name": context.user_data.get("full_name", ""),
        "gender_age": context.user_data.get("gender_age", ""),
        "phone": context.user_data.get("phone", ""),
        "complaints": context.user_data.get("complaints", ""),
        "files": files_str,
    })

    # Send to doctors group
    msg = (
        f"🆕 *НОВАЯ ЗАЯВКА — #{serial}*\n\n"
        f"👤 *Имя:* {context.user_data.get('full_name', '')}\n"
        f"⚥ *Пол/Возраст:* {context.user_data.get('gender_age', '')}\n"
        f"📞 *Телефон:* {context.user_data.get('phone', '')}\n"
        f"🏥 *Направление:* {context.user_data.get('specialty', '')}\n"
        f"🩺 *Жалобы:* {context.user_data.get('complaints', '')}\n"
        f"📎 *Файлы:* {files_str}\n\n"
        f"💬 *Для ответа:* `/reply {serial} ваш ответ`"
    )
    try:
        await context.bot.send_message(chat_id=group_id, text=msg, parse_mode="Markdown")
        for ftype, fid in context.user_data.get("file_ids", []):
            cap = f"📎 Пациент #{serial}"
            if ftype == "photo":
                await context.bot.send_photo(chat_id=group_id, photo=fid, caption=cap)
            else:
                await context.bot.send_document(chat_id=group_id, document=fid, caption=cap)
    except Exception as e:
        logger.error(f"Group send error: {e}")

    # Confirm to patient
    await query.edit_message_text(
        t(lang, "success").format(serial=serial, phone=context.user_data.get("phone", "")),
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def reply_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Doctor replies: /reply <serial> <response text>"""
    if not context.args or len(context.args) < 2:
        await update.message.reply_text("❌ Формат: /reply <номер> <ответ>\nПример: /reply 236 Рекомендуем консультацию онколога")
        return

    serial = context.args[0].replace("#", "")
    response_text = " ".join(context.args[1:])
    doctor = update.effective_user.full_name or "Доктор"

    save_doctor_response(serial, response_text)

    manager_msg = (
        f"📋 *ОТВЕТ ВРАЧА — Заявка #{serial}*\n\n"
        f"👨‍⚕️ *Врач:* {doctor}\n"
        f"💬 *Ответ:* {response_text}\n\n"
        f"📞 Позвоните пациенту."
    )
    try:
        await context.bot.send_message(chat_id=f"@{MANAGER_USERNAME}", text=manager_msg, parse_mode="Markdown")
        await update.message.reply_text(f"✅ Ответ по заявке #{serial} отправлен менеджеру @{MANAGER_USERNAME}!")
    except Exception as e:
        logger.error(f"Manager send error: {e}")
        await update.message.reply_text(f"✅ Ответ сохранён в таблицу! Ошибка отправки менеджеру: {e}")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "ru")
    await update.message.reply_text(t(lang, "cancelled"))
    return ConversationHandler.END

# ============ MAIN ============
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANGUAGE:   [CallbackQueryHandler(set_language, pattern="^lang_")],
            FULL_NAME:  [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            GENDER_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_gender_age)],
            PHONE:      [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            SPECIALTY:  [CallbackQueryHandler(get_specialty, pattern="^spec_")],
            COMPLAINTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_complaints)],
            FILES: [
                MessageHandler(filters.PHOTO | filters.Document.ALL, get_files),
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_files),
            ],
            CONFIRM: [CallbackQueryHandler(confirm, pattern="^confirm_")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    app.add_handler(conv)
    app.add_handler(CommandHandler("reply", reply_cmd))

    print("🚀 India Med Service Bot is running!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
