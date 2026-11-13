import os
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

async def handle_image_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text and (text.startswith("http://") or text.startswith("https://")):
        try:
            # Pehla caption
            caption_text_1 = (
                "<tg-emoji emoji-id=\"6312234398943023797\">🆕</tg-emoji> <b>Pehla Caption Title</b> (2026) <tg-emoji emoji-id=\"5325670588461632571\">🔥</tg-emoji>\n\n"
                "<blockquote>" "<tg-emoji emoji-id=\"6312153851126354884\">➡️</tg-emoji> <b>4k</b> <tg-emoji emoji-id=\"5224607267797606837\">☄️</tg-emoji> Added <tg-emoji emoji-id=\"5274099962655816924\">❗️</tg-emoji>" "</blockquote>\n\n"
                " "
                "<tg-emoji emoji-id=\"6096080291347042802\">📥</tg-emoji> Added on <b>HDHub4u</b><tg-emoji emoji-id=\"5190758974135212829\">🕺</tg-emoji>"
            )
            
            # Dusra caption
            caption_text_2 = (
              "<tg-emoji emoji-id=\"6159046264253059501\">🤩</tg-emoji><tg-emoji emoji-id=\"6156621398732182933\">🤩</tg-emoji><tg-emoji emoji-id=\"6158777532444316203\">🤩</tg-emoji><tg-emoji emoji-id=\"6156843319692367185\">🤩</tg-emoji><tg-emoji emoji-id=\"6156552632010806111\">🤩</tg-emoji><tg-emoji emoji-id=\"6156520617324582815\">🤩</tg-emoji><tg-emoji emoji-id=\"6156728837339091660\">🤩</tg-emoji><tg-emoji emoji-id=\"6156477856630181980\">🤩</tg-emoji><tg-emoji emoji-id=\"6159046264253059501\">🤩</tg-emoji>\n\n"
                "✨ <b>Dusra Caption / Extra Details</b> ✨\n\n"
                "Yahan par aap kuch aur likh sakte hain jo doosre message mein jayega!"
            )

            # Pehla message send karega photo ke sath
            await update.message.reply_photo(
                photo=text, 
                caption=caption_text_1, 
                parse_mode="HTML"
            )

            # Turant baad doosra message send karega usi photo ke sath alag caption mein
            await update.message.reply_photo(
                photo=text, 
                caption=caption_text_2, 
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
