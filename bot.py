import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# Conversation state maintain karne ke liye dictionary
USER_STATES = {}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    # Check karein ki message mein text hai ya photo (attachment)
    text = update.message.text or update.message.caption
    photo = update.message.photo

    # Image URL ya Direct Photo handle karne ke liye
    image_input = None
    if photo:
        image_input = photo[-1].file_id
    elif text and (text.startswith("http://") or text.startswith("https://")):
        image_input = text.strip()

    # 1. Agar user ne movie/series ka naam diya hai
    if user_id in USER_STATES and USER_STATES[user_id]["step"] == "waiting_for_title":
        USER_STATES[user_id]["movie_title"] = text.strip() if text else ""
        USER_STATES[user_id]["step"] = "waiting_for_year"
        
        await update.message.reply_text("ye kaunse jamane ka film hai ya ye kaunsa season hai batao na")
        return

    # 2. Agar user ne year/season ka reply diya hai
    elif user_id in USER_STATES and USER_STATES[user_id]["step"] == "waiting_for_year":
        USER_STATES[user_id]["movie_year"] = text.strip() if text else ""
        USER_STATES[user_id]["step"] = "waiting_for_4k_choice"
        
        await update.message.reply_text("4k speed me 69 baar download hoga ya nahi")
        return

    # 3. Agar user ne 4k rakhne ka choice diya hai (No/nahi/nhi/naa/na ya "4k")
    elif user_id in USER_STATES and USER_STATES[user_id]["step"] == "waiting_for_4k_choice":
        choice = text.strip().lower() if text else ""
        
        if choice == "4k":
            USER_STATES[user_id]["include_4k"] = True
            USER_STATES[user_id]["skip_content_prompt"] = True
            USER_STATES[user_id]["content_text"] = ""
            await ask_format_choice(update, user_id)
            return
        elif choice in ["no", "n", "nahi", "nhi", "naa", "na"]:
            USER_STATES[user_id]["include_4k"] = False
            USER_STATES[user_id]["skip_content_prompt"] = False
            USER_STATES[user_id]["step"] = "waiting_for_custom_content"
            await update.message.reply_text("btaiye kya kya likha jaye")
            return
        else:
            USER_STATES[user_id]["include_4k"] = True
            USER_STATES[user_id]["skip_content_prompt"] = False
            USER_STATES[user_id]["step"] = "waiting_for_content"
            await update.message.reply_text("kuch andar ka baat btao na...")
            return

    # 4. Agar user ne "No" ke baad custom content ka reply diya hai
    elif user_id in USER_STATES and USER_STATES[user_id]["step"] == "waiting_for_custom_content":
        USER_STATES[user_id]["content_text"] = text.strip() if text else ""
        await ask_format_choice(update, user_id)
        return

    # 5. Agar user ne normal content ka reply diya hai (jab 4k included hai)
    elif user_id in USER_STATES and USER_STATES[user_id]["step"] == "waiting_for_content":
        USER_STATES[user_id]["content_text"] = text.strip() if text else ""
        await ask_format_choice(update, user_id)
        return

    # 6. Agar user ne nayi shuruwat ki hai aur Photo (Link ya Direct Image) bheji hai
    elif image_input:
        USER_STATES[user_id] = {
            "step": "waiting_for_title",
            "image_source": image_input,
            "is_file_id": bool(photo)
        }
        await update.message.reply_text("Dave Kumar ye film ya web series ka kya naam hai")
    else:
        # Agar user bina kisi process ke achanak text bhej de ya bot kholte hi message kare
        keyboard = [
            [
                InlineKeyboardButton("old is gold", callback_data="btn_old_gold"),
                InlineKeyboardButton("naya maal", callback_data="btn_naya_maal")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if user_id not in USER_STATES:
            await update.message.reply_text(
                "Kripya pehle koi movie/series ka photo ya image link bhejein, ya fir niche diye gaye option ko chunein:",
                reply_markup=reply_markup
            )

async def ask_format_choice(update: Update, user_id: int):
    """Data collect hone ke baad user se buttons ke through format poochta hai"""
    keyboard = [
        [
            InlineKeyboardButton("old is gold", callback_data=f"old_{user_id}"),
            InlineKeyboardButton("naya maal", callback_data=f"naya_{user_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Kaunsa format chahiye select karein:", reply_markup=reply_markup)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    # Agar direct start/welcome par button dabaya gaya ho
    if data == "btn_old_gold":
        await query.message.reply_text("Aapne 'old is gold' chuna hai. Kripya pehle movie ka photo ya link bhejein.")
        return
    elif data == "btn_naya_maal":
        await query.message.reply_text("Aapne 'naya maal' chuna hai. Kripya pehle movie ka photo ya link bhejein.")
        return

    # Dynamic data extraction (old_<user_id> ya naya_<user_id>)
    try:
        action, uid_str = data.split("_", 1)
        user_id = int(uid_str)
    except ValueError:
        return

    if user_id not in USER_STATES:
        await query.message.reply_text("Session expire ho gaya hai. Kripya dobara shuru karein.")
        return

    state = USER_STATES[user_id]
    image_source = state["image_source"]
    movie_title = state["movie_title"]
    movie_year = state["movie_year"]
    include_4k = state.get("include_4k", True)
    content_text = state.get("content_text", "")
    
    # State clear kar dete hain
    del USER_STATES[user_id]

    try:
        if not include_4k:
            middle_block = f"<tg-emoji emoji-id=\"6043992250831082249\">✅</tg-emoji> {content_text} Added"
        else:
            if content_text.strip():
                emoji_4k_part = f"<tg-emoji emoji-id=\"5224607267797606837\">☄️</tg-emoji> <b>4k</b>"
                middle_block = f"<tg-emoji emoji-id=\"6043992250831082249\">✅</tg-emoji> {content_text} {emoji_4k_part} Added"
            else:
                middle_block = f"<tg-emoji emoji-id=\"6043992250831082249\">✅</tg-emoji> <b>4k</b> Added"

        # Pehla aur Dusra caption (Naya Maal ke liye)
        caption_text_1 = (
            f"<tg-emoji emoji-id=\"6312234398943023797\">🆕</tg-emoji> <b>{movie_title}</b> ({movie_year}) <tg-emoji emoji-id=\"5325670588461632571\">🔥</tg-emoji>\n\n"
            f"<blockquote>{middle_block}</blockquote>\n\n"
            " "
            "<tg-emoji emoji-id=\"5371081166013078244\">🍿</tg-emoji> Visit <b>HDHub4u</b><tg-emoji emoji-id=\"5190758974135212829\">🕺</tg-emoji>"
        )
        
        caption_text_2 = (
            "<tg-emoji emoji-id=\"6159046264253059501\">🤩</tg-emoji><tg-emoji emoji-id=\"6156621398732182933\">🤩</tg-emoji><tg-emoji emoji-id=\"6158777532444316203\">🤩</tg-emoji><tg-emoji emoji-id=\"6156843319692367185\">🤩</tg-emoji><tg-emoji emoji-id=\"6156552632010806111\">🤩</tg-emoji><tg-emoji emoji-id=\"6156520617324582815\">🤩</tg-emoji><tg-emoji emoji-id=\"6156728837339091660\">🤩</tg-emoji><tg-emoji emoji-id=\"6156477856630181980\">🤩</tg-emoji><tg-emoji emoji-id=\"6159046264253059501\">🤩</tg-emoji>\n\n"
            f"<tg-emoji emoji-id=\"6312234398943023797\">🆕</tg-emoji> <b>{movie_title}</b> ({movie_year}) <tg-emoji emoji-id=\"5325670588461632571\">🔥</tg-emoji>\n\n"
            f"<blockquote>{middle_block}</blockquote>\n\n"
            " "
            "<tg-emoji emoji-id=\"5371081166013078244\">🍿</tg-emoji> Visit <b>HDHub4u</b><tg-emoji emoji-id=\"5190758974135212829\">🕺</tg-emoji>"
        )

        # Teesra caption (Old is Gold ke liye)
        caption_text_3 = (
            f"<tg-emoji emoji-id=\"6098177227524936926\">↗️</tg-emoji> <b>{movie_title}</b> ({movie_year}) <tg-emoji emoji-id=\"5325670588461632571\">🔥</tg-emoji>\n\n"
            f"<blockquote>{middle_block}</blockquote>\n\n"
            " "
            "<tg-emoji emoji-id=\"5371081166013078244\">🍿</tg-emoji> Visit <b>HDHub4u</b><tg-emoji emoji-id=\"5190758974135212829\">🕺</tg-emoji>"
        )

        # Button selection ke hisaab se messages send karein
        if action == "old":
            # Sirf 3rd caption wala output
            await context.bot.send_photo(chat_id=query.message.chat_id, photo=image_source, caption=caption_text_3, parse_mode="HTML")
        elif action == "naya":
            # 1st aur 2nd caption wala output
            await context.bot.send_photo(chat_id=query.message.chat_id, photo=image_source, caption=caption_text_1, parse_mode="HTML")
            await context.bot.send_photo(chat_id=query.message.chat_id, photo=image_source, caption=caption_text_2, parse_mode="HTML")

    except Exception as e:
        await query.message.reply_text("Image load karne mein error aayi, link ya photo check karein.")

def main():
    TOKEN = os.environ.get("TOKEN")
    
    app = ApplicationBuilder().token(TOKEN).build()
    
    # Handlers add karna
    app.add_handler(MessageHandler((filters.TEXT | filters.PHOTO) & (~filters.COMMAND), handle_message))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    print("Bot start ho gaya hai...")
    app.run_polling()

if __name__ == '__main__':
    main()
