import os
import ffmpeg
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! فایل صوتی یا ویدیویی خودت رو بفرست تا تبدیل کنم.")

async def convert_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = None
    if update.message.audio:
        file = await update.message.audio.get_file()
        ext = ".mp3"
    elif update.message.voice:
        file = await update.message.voice.get_file()
        ext = ".ogg"
    elif update.message.video:
        file = await update.message.video.get_file()
        ext = ".mp3"  # تبدیل ویدیو به صوت
    else:
        await update.message.reply_text("فقط فایل صوتی یا ویدیویی قبول می‌کنم.")
        return

    filename = file.file_path.split("/")[-1]
    name, _ = os.path.splitext(filename)
    input_path = f"{name}_input"
    output_path = f"{name}{ext}"

    await file.download_to_drive(input_path)

    # تبدیل با ffmpeg
    ffmpeg.input(input_path).output(output_path).run(overwrite_output=True)

    # ارسال فایل تبدیل‌شده
    with open(output_path, "rb") as f:
        await update.message.reply_document(f)

    # پاک کردن فایل‌ها بعد از ارسال
    os.remove(input_path)
    os.remove(output_path)

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL, convert_file))
    print("Bot is running...")
    app.run_polling()
