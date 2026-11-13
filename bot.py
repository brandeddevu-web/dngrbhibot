import os
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

# Conversation state maintain karne ke liye dictionary
USER_STATES = {}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text
    photo = update.message.photo

    # 1. Agar user ne movie/series ka naam diya hai
    if user_id in USER_STATES and USER_STATES[user_id]["step"] == "waiting_for_title":
        if not text:
            return
        USER_STATES[user_id]["movie_title"] = text.strip()
        USER_STATES[user_id]["step"] = "waiting_for_year"
        
        await update.message.reply_text("ye kaunse jamane ka film hai ya ye kaunsa season hai, kahi ye wo 69 toh nahi ")
        return

    # 2. Agar user ne year/season ka reply diya hai
    elif user_id in USER_STATES and USER_STATES[user_id]["step"] == "waiting_for_year":
        if not text:
            return
        USER_STATES[user_id]["movie_year"] = text.strip()
        USER_STATES[user_id]["step"] = "waiting_for_content"
        
        await update.message.reply_text("kuch andar ka baat btao na...")
        return

    # 3. Agar user ne content ka reply diya hai
    elif user_id in USER_STATES and USER_STATES[user_id]["step"] == "waiting_for_content":
        if not text:
            return
        image_url = USER_STATES[user_id]["image_url"]
        movie_title = USER_STATES[user_id]["movie_title"]
        movie_year = USER_STATES[user_id]["movie_year"]
        content_text = text.strip()
        
        # State clear kar dete hain
        del USER_STATES[user_id]

        try:
            # Pehla caption
            caption_text_1 = (
                f"<tg-emoji emoji-id=\"6312234398943023797\">🆕</tg-emoji> <b>{movie_title}</b> ({movie_year}) <tg-emoji emoji-id=\"5325670588461632571\">🔥</tg-emoji>\n\n"
                "<blockquote>" f"<tg-emoji emoji-id=\"6312153851126354884\">➡️</tg-emoji> <b>{content_text}</b> <tg-emoji emoji-id=\"5224607267797606837\">☄️</tg-emoji> Added <tg-emoji emoji-id=\"5274099962655816924\">❗️</tg-emoji>" "</blockquote>\n\n"
                " "
                "<tg-emoji emoji-id=\"6096080291347042802\">📥</tg-emoji> Added on <b>HDHub4u</b><tg-emoji emoji-id=\"5190758974135212829\">🕺</tg-emoji>"
            )
            
            # Dusra caption
            caption_text_2 = (
                "<tg-emoji emoji-id=\"6159046264253059501\">🤩</tg-emoji><tg-emoji emoji-id=\"6156621398732182933\">🤩</tg-emoji><tg-emoji emoji-id=\"6158777532444316203\">🤩</tg-emoji><tg-emoji emoji-id=\"6156843319692367185\">🤩</tg-emoji><tg-emoji emoji-id=\"6156552632010806111\">🤩</tg-emoji><tg-emoji emoji-id=\"6156520617324582815\">🤩</tg-emoji><tg-emoji emoji-id=\"6156728837339091660\">🤩</tg-emoji><tg-emoji emoji-id=\"6156477856630181980\">🤩</tg-emoji><tg-emoji emoji-id=\"6159046264253059501\">🤩</tg-emoji>\n\n"
                f"<tg-emoji emoji-id=\"6312234398943023797\">🆕</tg-emoji> <b>{movie_title}</b> ({movie_year}) <tg-emoji emoji-id=\"5325670588461632571\">🔥</tg-emoji>\n\n"
                "<blockquote>" f"<tg-emoji emoji-id=\"6312153851126354884\">➡️</tg-emoji> <b>{content_text}</b> <tg-emoji emoji-id=\"5224607267797606837\">☄️</tg-emoji> Added <tg-emoji emoji-id=\"5274099962655816924\">❗️</tg-emoji>" "</blockquote>\n\n"
                " "
                "<tg-emoji emoji-id=\"6096080291347042802\">📥</tg-emoji> Added on <b>HDHub4u</b><tg-emoji emoji-id=\"5190758974135212829\">🕺</tg-emoji>"
            )

            # Pehla message photo ke sath send karega
            await update.message.reply_photo(
                photo=image_url, 
                caption=caption_text_1, 
                parse_mode="HTML"
            )

            # Turant baad doosra message send karega usi photo ke sath
            await update.message.reply_photo(
                photo=image_url, 
                caption=caption_text_2, 
                parse_mode="HTML"
            )

        except Exception as e:
            await update.message.reply_text("Image load karne mein error aayi, media check karein.")

    # 4. Agar user ne direct PHOTO bheji hai
    elif photo:
        # Telegram multiple sizes bhejta hai, sabse badi wali image ki file_id lenge
        photo_file_id = photo[-1].file_id
        USER_STATES[user_id] = {
            "step": "waiting_for_title",
            "image_url": photo_file_id
        }
        await update.message.reply_text("Dave Kumar ye film ya web series ka kya naam hai")

    # 5. Agar user ne Image/Photo ka Link bheja hai
    elif text and (text.startswith("http://") or text.startswith("https://")):
        USER_STATES[user_id] = {
            "step": "waiting_for_title",
            "image_url": text
        }
        await update.message.reply_text("Dave Kumar ye film ya web series ka kya naam hai")

def main():
    TOKEN = os.environ.get("TOKEN")
    
    app = ApplicationBuilder().token(TOKEN).build()
    
    # Ab handlers me TEXT ke sath-sath PHOTO ko bhi allow kar diya gaya hai
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO & (~filters.COMMAND), handle_message))
    
    print("Bot start ho gaya hai...")
    app.run_polling()

if __name__ == '__main__':
    main()
