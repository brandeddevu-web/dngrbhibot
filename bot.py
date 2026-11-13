import os
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

async def handle_image_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text and (text.startswith("http://") or text.startswith("https://")):
        try:
            # Sirf specific words ko <b> aur </b> ke andar rakha hai taaki woh bold rahein
            caption_text = (
                "🆕 <b>Title</b> (2026) 🔥\n\n"
                " "
                "<blockquote>" "➡️  <b>4k</b> ☄️ Added ❗️" "</blockquote>\n\n"
                " "
                "📥 Added on <b>HDHub4u</b>🕺"
            )
            await update.message.reply_photo(
                photo=text, 
                caption=caption_text, 
                parse_mode="HTML"
            )
        except Exception as e:
            await update.message.reply_text("Image load karne mein error aayi, link check karein.")

def main():
    TOKEN = os.environ.get("TOKEN")
    
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_image_link))
    
    print("Bot start ho gaya hai...")
    app.run_polling()

if __name__ == '__main__':
    main()
