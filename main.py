import os
import zipfile
import telebot
from telebot import types
from dotenv import load_dotenv

# .env faylini yuklash (Railway Environment Variables-ni tanib olish uchun)
load_dotenv()

# TOKEN ni Environment Variables dan olish
# Railway'da sozlaganingizga ishonch hosil qiling!
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN muhit o'zgaruvchisi topilmadi!")

bot = telebot.TeleBot(BOT_TOKEN)

# Foydalanuvchi ma'lumotlarini (ID va yuborilgan fayllar) saqlash uchun lug'at
user_data = {}

# Vaqtinchalik fayllar saqlanadigan katalog
TEMP_DIR = "temp_files"

# Agar TEMP_DIR mavjud bo'lmasa, uni yaratish
if not os.path.isdir(TEMP_DIR):
    os.makedirs(TEMP_DIR)


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """
    /start va /help komandalari uchun javob
    """
    text = (
        "Assalomu alaykum! Men yuborilgan fayllarni bitta ZIP papkasiga yig'ib beruvchi botman.\n\n"
        "Fayllarni yuborishni boshlash uchun /yuborish komandasini bosing, so'ngra barcha kerakli fayllarni (rasm, video, hujjat) menga yuboring.\n\n"
        "Fayllarni yig'ishni tugatish va ZIP arxivini olish uchun /tugatish komandasini bosing."
    )
    bot.reply_to(message, text)


@bot.message_handler(commands=['yuborish'])
def start_collection(message):
    """
    Fayl yig'ish jarayonini boshlash
    """
    user_id = message.chat.id
    # Agar avvalgi jarayon bo'lsa, uni tozalash
    user_data[user_id] = []
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    item = types.KeyboardButton('/tugatish')
    markup.add(item)
    
    bot.reply_to(
        message, 
        "Fayllarni qabul qilish boshlandi. Iltimos, kerakli fayllarni yuboring.",
        reply_markup=markup
    )


@bot.message_handler(content_types=['document', 'photo', 'video', 'audio', 'voice'])
def handle_files(message):
    """
    Yuborilgan fayllarni qabul qilish va saqlash
    """
    user_id = message.chat.id
    
    # Agar foydalanuvchi yig'ishni boshlamagan bo'lsa
    if user_id not in user_data:
        bot.send_message(user_id, "Iltimos, avval /yuborish komandasini bosing.")
        return

    # Fayl haqida ma'lumotni olish
    if message.document:
        file_info = message.document
        file_id = file_info.file_id
        original_file_name = file_info.file_name
    elif message.photo:
        # Eng yuqori sifatli rasmni olish
        file_info = message.photo[-1] 
        file_id = file_info.file_id
        # Rasmlar uchun fayl nomini avtomatik yaratish
        original_file_name = f"photo_{file_id}.jpg"
    elif message.video:
        file_info = message.video
        file_id = file_info.file_id
        original_file_name = message.video.file_name or f"video_{file_id}.mp4"
    elif message.audio:
        file_info = message.audio
        file_id = file_info.file_id
        original_file_name = message.audio.file_name or f"audio_{file_id}.mp3"
    elif message.voice:
        file_info = message.voice
        file_id = file_info.file_id
        original_file_name = f"voice_{file_id}.ogg"
    else:
        # Boshqa turdagi kontentni e'tiborsiz qoldirish
        return

    # Telegram fayl ma'lumotlarini olish
    try:
        file_info_full = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info_full.file_path)
    except Exception as e:
        print(f"Faylni yuklab olishda xato: {e}")
        bot.send_message(user_id, "Faylni yuklab olishda xato yuz berdi. Iltimos, boshqa fayl yuboring.")
        return

    # Faylni vaqtinchalik saqlash joyi
    temp_file_path = os.path.join(TEMP_DIR, original_file_name)
    
    # Bir xil nomli fayllar uchun nomini o'zgartirish
    if os.path.exists(temp_file_path):
        base, ext = os.path.splitext(original_file_name)
        i = 1
        while os.path.exists(temp_file_path):
            original_file_name = f"{base}_{i}{ext}"
            temp_file_path = os.path.join(TEMP_DIR, original_file_name)
            i += 1
            
    # Faylni yozish
    with open(temp_file_path, 'wb') as new_file:
        new_file.write(downloaded_file)

    # Fayl yo'lini foydalanuvchi ro'yxatiga qo'shish
    user_data[user_id].append(temp_file_path)
    
    bot.send_message(user_id, f"✅ Fayl qabul qilindi: {original_file_name}")


@bot.message_handler(commands=['tugatish'])
def finish_collection(message):
    """
    Fayl yig'ish jarayonini tugatish va ZIP faylini yuborish
    """
    user_id = message.chat.id
    
    if user_id not in user_data or not user_data[user_id]:
        bot.send_message(user_id, "Siz hali hech qanday fayl yubormadingiz yoki /yuborish komandasini ishga tushirmadingiz.")
        return

    file_paths = user_data[user_id]
    
    if not file_paths:
        bot.send_message(user_id, "Hech qanday fayl topilmadi. Yig'ish bekor qilindi.")
        del user_data[user_id] # Xotirani tozalash
        return

    bot.send_message(user_id, f"{len(file_paths)} ta fayl topildi. ZIP arxivini yaratmoqdaman...")

    # ZIP fayli nomini yaratish
    zip_file_name = f"fayllar_{user_id}_{telebot.util.time.time()}.zip"
    zip_file_path = os.path.join(TEMP_DIR, zip_file_name)
    
    try:
        # ZIP arxivini yaratish
        with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in file_paths:
                # Arxiv ichidagi fayl nomi
                arcname = os.path.basename(file_path) 
                zipf.write(file_path, arcname)

        # Foydalanuvchiga ZIP arxivini yuborish
        with open(zip_file_path, 'rb') as zip_file:
            bot.send_document(user_id, zip_file, caption=f"Tayyor ZIP papkasi: {len(file_paths)} ta fayl.")
            
    except Exception as e:
        print(f"ZIP yaratish/yuborishda xato: {e}")
        bot.send_message(user_id, "ZIP arxivini yaratishda yoki yuborishda kutilmagan xato yuz berdi.")
        
    finally:
        # Xotirani tozalash: barcha vaqtinchalik fayllarni o'chirish
        for file_path in file_paths:
            try:
                os.remove(file_path)
            except OSError as e:
                print(f"Faylni o'chirishda xato: {file_path} - {e}")
                
        # ZIP faylini o'chirish
        try:
            os.remove(zip_file_path)
        except OSError as e:
            print(f"ZIP faylini o'chirishda xato: {zip_file_path} - {e}")
            
        # Foydalanuvchi ma'lumotlarini tozalash
        if user_id in user_data:
            del user_data[user_id]
        
        # Tugatish xabarini yuborish
        bot.send_message(
            user_id, 
            "✅ Fayllar yig'ish jarayoni tugatildi va xotira tozalandi. Yangi jarayonni boshlash uchun /yuborish komandasini bosing."
        )


# Boshqa barcha matn xabarlarini e'tiborsiz qoldirish
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    user_id = message.chat.id
    if user_id in user_data:
        bot.send_message(user_id, "Iltimos, faqat fayllar yoki /tugatish komandasini yuboring.")
    elif message.text not in ['/start', '/help', '/yuborish', '/tugatish']:
        bot.send_message(user_id, "Noma'lum komanda. Fayllar yig'ishni boshlash uchun /yuborish ni bosing.")


# Botni ishga tushirish
print("Bot ishga tushmoqda...")
bot.infinity_polling()


