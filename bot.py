import os
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

# Conversation state maintain karne ke liye dictionary
USER_STATES = {}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text

    if not text:
        return

    # 1. Agar user ne movie/series ka naam diya hai
    if user_id in USER_STATES and USER_STATES[user_id]["step"] == "waiting_for_title":
        USER_STATES[user_id]["movie_title"] = text.strip()
        USER_STATES[user_id]["step"] = "waiting_for_year"
        
        await update.message.reply_text("ye kaunse jamane ka film hai ya ye kaunsa season hai, kahi ye wo 69 toh nahi ")
        return

    # 2. Agar user ne year/season ka reply diya hai
    elif user_id in USER_STATES and USER_STATES[user_id]["step"] == "waiting_for_year":
        USER_STATES[user_id]["movie_year"] = text.strip()
        USER_STATES[user_id]["step"] = "waiting_for_4k_choice"
        
        await update.message.reply_text("4k speed me 69 baar download hoga ya nahi")
        return

    # 3. Agar user ne 4k rakhne ka choice diya hai (Yes/No)
    elif user_id in USER_STATES and USER_STATES[user_id]["step"] == "waiting_for_4k_choice":
        choice = text.strip().lower()
        
        if choice in ["no", "n", "nahi"]:
            USER_STATES[user_id]["include_4k"] = False
            USER_STATES[user_id]["step"] = "waiting_for_custom_content"
            await update.message.reply_text("btaiye kya kya likha jaye")
            return
        else:
            USER_STATES[user_id]["include_4k"] = True
            USER_STATES[user_id]["step"] = "waiting_for_content"
            await update.message.reply_text("kuch andar ka baat btao na...")
            return

    # 4. Agar user ne "No" ke baad custom content ka reply diya hai
    elif user_id in USER_STATES and USER_STATES[user_id]["step"] == "waiting_for_custom_content":
        USER_STATES[user_id]["content_text"] = text.strip()
        
        # Sabhi data mil gaya, ab messages send karenge
        await send_movie_messages(update, user_id)
        return

    # 5. Agar user ne normal content ka reply diya hai (jab 4k included hai)
    elif user_id in USER_STATES and USER_STATES[user_id]["step"] == "waiting_for_content":
        USER_STATES[user_id]["content_text"] = text.strip()
        
        # Sabhi data mil gaya, ab messages send karenge
        await send_movie_messages(update, user_id)
        return

    # 6. Agar user ne Image/Photo ka Link bheja hai
    elif text.startswith("http://") or text.startswith("https://"):
        USER_STATES[user_id] = {
            "step": "waiting_for_title",
            "image_url": text
        }
        await update.message.reply_text("Dave Kumar ye film ya web series ka kya naam hai")


async def send_movie_messages(update: Update, user_id: int):
    state = USER_STATES[user_id]
    image_url = state["image_url"]
    movie_title = state["movie_title"]
    movie_year = state["movie_year"]
    include_4k = state.get("include_4k", True)
    content_text = state["content_text"]
    
    # State clear kar dete hain
    del USER_STATES[user_id]

    try:
        # Agar 'No' select kiya tha toh 4k aur comet emoji nahi rahega
        if include_4k:
            middle_block = f"<tg-emoji emoji-id=\"6312153851126354884\">➡️</tg-emoji> <b>4k</b> <tg-emoji emoji-id=\"5224607267797606837\">☄️</tg-emoji> {content_text} Added <tg-emoji emoji-id=\"5274099962655816924\">❗️</tg-emoji>"
        else:
            middle_block = f"<tg-emoji emoji-id=\"6312153851126354884\">➡️</tg-emoji> {content_text} Added <tg-emoji emoji-id=\"5274099962655816924\">❗️</tg-emoji>"

        # Pehla caption
        caption_text_1 = (
            f"<tg-emoji emoji-id=\"6312234398943023797\">🆕</tg-emoji> <b>{movie_title}</b> ({movie_year}) <tg-emoji emoji-id=\"5325670588461632571\">🔥</tg-emoji>\n\n"
            f"<blockquote>{middle_block}</blockquote>\n\n"
            " "
            "<tg-emoji emoji-id=\"6096080291347042802\">📥</tg-emoji> Added on <b>HDHub4u</b><tg-emoji emoji-id=\"5190758974135212829\">🕺</tg-emoji>"
        )
        
        # Dusra caption
        caption_text_2 = (
            "<tg-emoji emoji-id=\"6159046264253059501\">🤩</tg-emoji><tg-emoji emoji-id=\"6156621398732182933\">🤩</tg-emoji><tg-emoji emoji-id=\"6158777532444316203\">🤩</tg-emoji><tg-emoji emoji-id=\"6156843319692367185\">🤩</tg-emoji><tg-emoji emoji-id=\"6156552632010806111\">🤩</tg-emoji><tg-emoji emoji-id=\"6156520617324582815\">🤩</tg-emoji><tg-emoji emoji-id=\"6156728837339091660\">🤩</tg-emoji><tg-emoji emoji-id=\"6156477856630181980\">🤩</tg-emoji><tg-emoji emoji-id=\"6159046264253059501\">🤩</tg-emoji>\n\n"
            f"<tg-emoji emoji-id=\"6312234398943023797\">🆕</tg-emoji> <b>{movie_title}</b> ({movie_year}) <tg-emoji emoji-id=\"5325670588461632571\">🔥</tg-emoji>\n\n"
            f"<blockquote>{middle_block}</blockquote>\n\n"
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
        await update.message.reply_text("Image load karne mein error aayi, link check karein.")

def main():
    TOKEN = os.environ.get("TOKEN")
    
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("Bot start ho gaya hai...")
    app.run_polling()

if __name__ == '__main__':
    main()
