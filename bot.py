import os
import requests
import json
import time

TOKEN = os.environ.get("BOT_TOKEN", "")
SHEET_URL = "https://script.google.com/macros/s/AKfycbxhdWxU1yqlCdIjFxPSv9Wwp3KMmWvwSBD3XL_LKdQPSj-fozDiv7E0CNnql5dkpuSAug/exec"
MANAGER_USERNAME = "India_medservice"
ONCO_GROUP = "-5107088561"
STARTING_SERIAL = 236

API = f"https://api.telegram.org/bot{TOKEN}"

serial_counter = STARTING_SERIAL
user_states = {}

def send(chat_id, text, keyboard=None):
    data = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    if keyboard:
        data["reply_markup"] = json.dumps(keyboard)
    requests.post(f"{API}/sendMessage", json=data)

def send_photo(chat_id, file_id, caption=""):
    requests.post(f"{API}/sendPhoto", json={"chat_id": chat_id, "photo": file_id, "caption": caption})

def send_doc(chat_id, file_id, caption=""):
    requests.post(f"{API}/sendDocument", json={"chat_id": chat_id, "document": file_id, "caption": caption})

def inline_kb(buttons):
    return {"inline_keyboard": [[{"text": b[0], "callback_data": b[1]}] for b in buttons]}

def reply_kb(buttons):
    return {"keyboard": [[{"text": b}] for b in buttons], "resize_keyboard": True, "one_time_keyboard": True}

LANGS = {
    "ru": {
        "welcome": "👋 Добро пожаловать в *India Med Service!*\n\nВыберите язык:",
        "name": "📝 Введите ваше *полное имя (ФИО)*:",
        "gender_age": "👤 Введите *пол и возраст*:\n_(Пример: Мужской, 35)_",
        "phone": "📞 Введите *номер телефона*:",
        "specialty": "🏥 Выберите *направление*:",
        "complaints": "🩺 Опишите ваши *жалобы* подробно:",
        "files": "📎 Отправьте *анализы и документы*.\nКогда закончите нажмите кнопку ниже 👇",
        "files_btn": "✅ Все файлы отправлены",
        "file_ok": "📎 Файл получен! Отправьте ещё или нажмите кнопку.",
        "confirm": "📋 *Проверьте данные:*\n\n👤 {name}\n⚥ {ga}\n📞 {phone}\n🏥 {spec}\n🩺 {comp}\n📎 Файлов: {files}\n\nОтправить врачу?",
        "yes": "✅ Да, отправить",
        "no": "❌ Начать заново",
        "done": "✅ *Заявка принята!*\n\n🔢 Номер: *#{serial}*\n\nМенеджер свяжется с вами по номеру {phone}. 🙏",
        "specs": [("🎗 Онкология","onco"),("❤️ Кардиология","cardio"),("🦴 Ортопедия","ortho"),("🧠 Неврология","neuro"),("🏥 Другое","other")]
    },
    "uz": {
        "welcome": "👋 *India Med Service* ga xush kelibsiz!\n\nTilni tanlang:",
        "name": "📝 *To'liq ismingizni (FIO)* kiriting:",
        "gender_age": "👤 *Jins va yoshingizni* kiriting:\n_(Misol: Erkak, 35)_",
        "phone": "📞 *Telefon raqamingizni* kiriting:",
        "specialty": "🏥 *Yo'nalishni* tanlang:",
        "complaints": "🩺 *Shikoyatlaringizni* batafsil yozing:",
        "files": "📎 *Tahlil va hujjatlaringizni* yuboring.\nTugagach quyidagi tugmani bosing 👇",
        "files_btn": "✅ Barcha fayllar yuborildi",
        "file_ok": "📎 Fayl qabul qilindi! Yana yuboring yoki tugmani bosing.",
        "confirm": "📋 *Ma'lumotlarni tekshiring:*\n\n👤 {name}\n⚥ {ga}\n📞 {phone}\n🏥 {spec}\n🩺 {comp}\n📎 Fayllar: {files}\n\nShifokorga yuborasizmi?",
        "yes": "✅ Ha, yuborish",
        "no": "❌ Qaytadan boshlash",
        "done": "✅ *Ariza qabul qilindi!*\n\n🔢 Raqam: *#{serial}*\n\nMenejer {phone} ga murojaat qiladi. 🙏",
        "specs": [("🎗 Onkologiya","onco"),("❤️ Kardiologiya","cardio"),("🦴 Ortopediya","ortho"),("🧠 Nevrologiya","neuro"),("🏥 Boshqa","other")]
    },
    "kz": {
        "welcome": "👋 *India Med Service* қызметіне қош келдіңіз!\n\nТілді таңдаңыз:",
        "name": "📝 *Толық атыңызды (АӘТ)* енгізіңіз:",
        "gender_age": "👤 *Жынысыңыз бен жасыңызды* енгізіңіз:\n_(Мысалы: Ер, 35)_",
        "phone": "📞 *Телефон нөміріңізді* енгізіңіз:",
        "specialty": "🏥 *Бағытты* таңдаңыз:",
        "complaints": "🩺 *Шағымдарыңызды* толық жазыңыз:",
        "files": "📎 *Талдау және құжаттарыңызды* жіберіңіз.\nАяқтағанда түймені басыңыз 👇",
        "files_btn": "✅ Барлық файлдар жіберілді",
        "file_ok": "📎 Файл қабылданды! Тағы жіберіңіз немесе түймені басыңыз.",
        "confirm": "📋 *Деректерді тексеріңіз:*\n\n👤 {name}\n⚥ {ga}\n📞 {phone}\n🏥 {spec}\n🩺 {comp}\n📎 Файлдар: {files}\n\nДәрігерге жіберу керек пе?",
        "yes": "✅ Иә, жіберу",
        "no": "❌ Қайтадан бастау",
        "done": "✅ *Өтініш қабылданды!*\n\n🔢 Нөмір: *#{serial}*\n\nМенеджер {phone} нөміріне хабарласады. 🙏",
        "specs": [("🎗 Онкология","onco"),("❤️ Кардиология","cardio"),("🦴 Ортопедия","ortho"),("🧠 Неврология","neuro"),("🏥 Басқа","other")]
    }
}

SPEC_NAMES = {
    "onco": {"ru":"🎗 Онкология","uz":"🎗 Onkologiya","kz":"🎗 Онкология"},
    "cardio": {"ru":"❤️ Кардиология","uz":"❤️ Kardiologiya","kz":"❤️ Кардиология"},
    "ortho": {"ru":"🦴 Ортопедия","uz":"🦴 Ortopediya","kz":"🦴 Ортопедия"},
    "neuro": {"ru":"🧠 Неврология","uz":"🧠 Nevrologiya","kz":"🧠 Неврология"},
    "other": {"ru":"🏥 Другое","uz":"🏥 Boshqa","kz":"🏥 Басқа"},
}

def t(lang, key):
    return LANGS.get(lang, LANGS["ru"]).get(key, "")

def save_patient(data):
    try:
        requests.post(SHEET_URL, json=data, timeout=10)
    except:
        pass

def update_response(serial, response):
    try:
        requests.post(SHEET_URL, json={"type":"doctor_response","serial":serial,"response":response}, timeout=10)
    except:
        pass

def process_update(update):
    global serial_counter

    # Handle callback queries
    if "callback_query" in update:
        cq = update["callback_query"]
        chat_id = cq["message"]["chat"]["id"]
        data = cq["data"]
        msg_id = cq["message"]["message_id"]

        requests.post(f"{API}/answerCallbackQuery", json={"callback_query_id": cq["id"]})

        state = user_states.get(chat_id, {})

        if data.startswith("lang_"):
            lang = data.split("_")[1]
            user_states[chat_id] = {"step": "name", "lang": lang}
            send(chat_id, t(lang, "name"))

        elif data.startswith("spec_"):
            spec = data.split("_")[1]
            lang = state.get("lang", "ru")
            state["specialty"] = spec
            state["specialty_name"] = SPEC_NAMES[spec][lang]
            state["step"] = "complaints"
            user_states[chat_id] = state
            send(chat_id, t(lang, "complaints"))

        elif data == "confirm_yes":
            lang = state.get("lang", "ru")
            serial_counter += 1
            serial = serial_counter
            state["serial"] = serial
            files_str = ", ".join(state.get("files", [])) or "—"

            save_patient({
                "type": "patient",
                "serial": f"#{serial}",
                "full_name": state.get("name",""),
                "gender_age": state.get("gender_age",""),
                "phone": state.get("phone",""),
                "complaints": state.get("complaints",""),
                "files": files_str,
            })

            group_msg = (
                f"🆕 *НОВАЯ ЗАЯВКА — #{serial}*\n\n"
                f"👤 *Имя:* {state.get('name','')}\n"
                f"⚥ *Пол/Возраст:* {state.get('gender_age','')}\n"
                f"📞 *Телефон:* {state.get('phone','')}\n"
                f"🏥 *Направление:* {state.get('specialty_name','')}\n"
                f"🩺 *Жалобы:* {state.get('complaints','')}\n"
                f"📎 *Файлы:* {files_str}\n\n"
                f"💬 Ответить: `/reply {serial} ваш ответ`"
            )
            try:
                requests.post(f"{API}/sendMessage", json={"chat_id": ONCO_GROUP, "text": group_msg, "parse_mode": "Markdown"})
                for ftype, fid in state.get("file_ids", []):
                    cap = f"📎 Пациент #{serial}"
                    if ftype == "photo":
                        send_photo(ONCO_GROUP, fid, cap)
                    else:
                        send_doc(ONCO_GROUP, fid, cap)
            except:
                pass

            send(chat_id, t(lang, "done").format(serial=serial, phone=state.get("phone","")))
            user_states[chat_id] = {}

        elif data == "confirm_no":
            lang = state.get("lang", "ru")
            user_states[chat_id] = {}
            send(chat_id, "❌ Отменено. Напишите /start")

        return

    # Handle messages
    if "message" not in update:
        return

    msg = update["message"]
    chat_id = msg["chat"]["id"]
    text = msg.get("text", "")
    
    # Handle /reply command from doctors
    if text.startswith("/reply") and msg["chat"].get("type") in ["group","supergroup"]:
        parts = text.split(" ", 2)
        if len(parts) >= 3:
            serial = parts[1].replace("#","")
            response = parts[2]
            doctor = msg.get("from",{}).get("first_name","Доктор")
            update_response(f"#{serial}", response)
            manager_msg = (
                f"📋 *ОТВЕТ ВРАЧА — Заявка #{serial}*\n\n"
                f"👨‍⚕️ *Врач:* {doctor}\n"
                f"💬 *Ответ:* {response}\n\n"
                f"📞 Позвоните пациенту."
            )
            try:
                requests.post(f"{API}/sendMessage", json={"chat_id": f"@{MANAGER_USERNAME}", "text": manager_msg, "parse_mode": "Markdown"})
            except:
                pass
            requests.post(f"{API}/sendMessage", json={"chat_id": chat_id, "text": f"✅ Ответ по заявке #{serial} отправлен менеджеру!"})
        return

    if text == "/start":
        user_states[chat_id] = {}
        kb = inline_kb([("🇷🇺 Русский","lang_ru"),("🇺🇿 O'zbek","lang_uz"),("🇰🇿 Қазақша","lang_kz")])
        send(chat_id, LANGS["ru"]["welcome"], kb)
        return

    state = user_states.get(chat_id, {})
    lang = state.get("lang", "ru")
    step = state.get("step", "")

    if step == "name":
        state["name"] = text
        state["step"] = "gender_age"
        user_states[chat_id] = state
        send(chat_id, t(lang, "gender_age"))

    elif step == "gender_age":
        state["gender_age"] = text
        state["step"] = "phone"
        user_states[chat_id] = state
        send(chat_id, t(lang, "phone"))

    elif step == "phone":
        state["phone"] = text
        state["step"] = "specialty"
        user_states[chat_id] = state
        specs = t(lang, "specs")
        kb = inline_kb([(s[0], f"spec_{s[1]}") for s in specs])
        send(chat_id, t(lang, "specialty"), kb)

    elif step == "complaints":
        state["complaints"] = text
        state["step"] = "files"
        state["files"] = []
        state["file_ids"] = []
        user_states[chat_id] = state
        kb = reply_kb([t(lang, "files_btn")])
        send(chat_id, t(lang, "files"), kb)

    elif step == "files":
        files_btn = t(lang, "files_btn")
        if text == files_btn:
            # Show confirmation
            state["step"] = "confirm"
            user_states[chat_id] = state
            files_count = len(state.get("files", []))
            confirm_text = t(lang, "confirm").format(
                name=state.get("name",""),
                ga=state.get("gender_age",""),
                phone=state.get("phone",""),
                spec=state.get("specialty_name",""),
                comp=state.get("complaints",""),
                files=files_count
            )
            kb = inline_kb([(t(lang,"yes"),"confirm_yes"),(t(lang,"no"),"confirm_no")])
            send(chat_id, confirm_text, kb)
        elif "photo" in msg:
            fid = msg["photo"][-1]["file_id"]
            state["file_ids"].append(("photo", fid))
            state["files"].append("[Фото]")
            user_states[chat_id] = state
            send(chat_id, t(lang, "file_ok"))
        elif "document" in msg:
            fid = msg["document"]["file_id"]
            fname = msg["document"].get("file_name","document")
            state["file_ids"].append(("document", fid))
            state["files"].append(f"[{fname}]")
            user_states[chat_id] = state
            send(chat_id, t(lang, "file_ok"))
        else:
            send(chat_id, t(lang, "file_ok"))

def main():
    print("🚀 Bot started!")
    offset = 0
    while True:
        try:
            resp = requests.get(f"{API}/getUpdates", params={"offset": offset, "timeout": 30}, timeout=35)
            updates = resp.json().get("result", [])
            for update in updates:
                offset = update["update_id"] + 1
                try:
                    process_update(update)
                except Exception as e:
                    print(f"Error processing update: {e}")
        except Exception as e:
            print(f"Error getting updates: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
