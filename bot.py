import os
import time
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from pydub import AudioSegment

TOKEN = "8254175129:AAFDAAiQL2ZfRYKYBOZPXNbt3UyHgOMzo_Y"
DOWNLOAD_PATH = "downloads"
os.makedirs(DOWNLOAD_PATH, exist_ok=True)

pending_files = {}  # {user_id: {"path": file_path, "type": "audio/video"}}

# ==================== توابع ====================

# اسم فایل هوشمند
def get_filename(file):
    if getattr(file, "file_name", None):
        base_name = os.path.splitext(file.file_name)[0]
    else:
        # موبایل: voice, audio, video_note یا دیگر فایل‌ها
        ext = "mp3" if getattr(file, "audio", False) or getattr(file, "voice", False) else "mp4"
        timestamp = int(time.time())
        base_name = f"{file.file_unique_id}_{timestamp}"
    return base_name

# تبدیل فایل صوتی
def convert_audio(file_path, output_format):
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    output_path = os.path.join(DOWNLOAD_PATH, f"{base_name}.{output_format}")
    sound = AudioSegment.from_file(file_path)
    sound.export(output_path, format=output_format)
    return output_path

# استخراج صدا از ویدئو
async def convert_video_async(file_path, output_format):
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    output_path = os.path.join(DOWNLOAD_PATH, f"{base_name}.{output_format}")
    process = await asyncio.create_subprocess_exec(
        "ffmpeg", "-i", file_path, "-vn", "-ab", "192k", output_path, "-y",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    await process.communicate()
    return output_path

# دریافت فایل و نمایش منوی فرمت
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = (
        update.message.document
        or update.message.audio
        or update.message.video
        or update.message.voice
        or update.message.video_note
    )

    if not file:
        await update.message.reply_text("فقط فایل‌های صوتی یا ویدیویی پشتیبانی می‌شن 🎵🎥")
        return

    tg_file = await file.get_file()
    base_name = get_filename(file)
    
    # تعیین پسوند اولیه دانلود برای دانلود فایل اصلی
    if getattr(file, "audio", False) or getattr(file, "voice", False):
        ext = "ogg" if getattr(file, "voice", False) else "mp3"
    elif getattr(file, "video_note", False):
        ext = "mp4"
    elif getattr(file, "video", False):
        ext = os.path.splitext(file.file_name)[1][1:] if getattr(file, "file_name", None) else "mp4"
    else:
        ext = os.path.splitext(file.file_name)[1][1:] if getattr(file, "file_name", None) else "dat"

    file_path = os.path.join(DOWNLOAD_PATH, f"{base_name}.{ext}")
    await tg_file.download_to_drive(file_path)
    await update.message.reply_text(f"فایل دریافت شد ✅")

    # تشخیص نوع فایل
    if getattr(file, "voice", False) or getattr(file, "audio", False):
        file_type = "audio"
    else:
        file_type = "video"

    # ذخیره موقت برای callback
    pending_files[update.effective_user.id] = {"path": file_path, "type": file_type}

    # دکمه‌های انتخاب فرمت
    keyboard = [
        [
            InlineKeyboardButton("MP3", callback_data="mp3"),
            InlineKeyboardButton("WAV", callback_data="wav"),
            InlineKeyboardButton("OGG", callback_data="ogg"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("کدوم فرمت میخوای؟", reply_markup=reply_markup)

# پردازش دکمه‌ها
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if user_id not in pending_files:
        await query.edit_message_text("هیچ فایلی برای تبدیل موجود نیست ⚠️")
        return

    data = pending_files.pop(user_id)
    file_path = data["path"]
    file_type = data["type"]
    output_format = query.data.lower()

    await query.edit_message_text(f"در حال تبدیل فایل به {output_format}... ⏳")

    try:
        if file_type == "audio":
            out = convert_audio(file_path, output_format)
        else:
            out = await convert_video_async(file_path, output_format)

        with open(out, "rb") as f:
            await context.bot.send_document(chat_id=query.message.chat_id, document=f)

        await context.bot.send_message(chat_id=query.message.chat_id, text="✅ تبدیل انجام شد!")
    except Exception as e:
        await context.bot.send_message(chat_id=query.message.chat_id, text=f"خطا در تبدیل فایل ⚠️: {e}")

# ==================== اجرای بات ====================
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    # دریافت همه فایل‌ها
    app.add_handler(MessageHandler(
        filters.Document.ALL | filters.AUDIO | filters.VIDEO | filters.VOICE | filters.VIDEO_NOTE,
        handle_file
    ))

    # دکمه‌ها
    app.add_handler(CallbackQueryHandler(button))

    print("Bot is running...")
    app.run_polling()
