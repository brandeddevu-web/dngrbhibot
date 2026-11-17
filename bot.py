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

    # 0. Jab user nayi photo ya link bhejta hai -> 1st question (New & Exclusive / Old is Gold)
    if image_input:
        USER_STATES[user_id] = {
            "step": "waiting_for_category",
            "image_source": image_input,
            "is_file_id": bool(photo)
        }
        
        keyboard = [
            [
                InlineKeyboardButton("New and Exclusive", callback_data="cat_new"),
                InlineKeyboardButton("Old is Gold", callback_data="cat_old")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Kripya category select karein:", reply_markup=reply_markup)
        return

    # 1. Agar user movie/series ka naam type kare
    if user_id in USER_STATES and USER_STATES[user_id]["step"] == "waiting_for_title":
        USER_STATES[user_id]["movie_title"] = text.strip() if text else ""
        USER_STATES[user_id]["step"] = "waiting_for_year"
        
        await update.message.reply_text("ye kaunse jamane ka film hai ya ye kaunsa season hai batao na")
        return

    # 2. Agar user year/season ka reply de
    elif user_id in USER_STATES and USER_STATES[user_id]["step"] == "waiting_for_year":
        USER_STATES[user_id]["movie_year"] = text.strip() if text else ""
        USER_STATES[user_id]["step"] = "waiting_for_4k_buttons"
        
        # 3rd question ke buttons: Yes 4k hai, No 4k nhi hai, 4k only
        keyboard = [
            [InlineKeyboardButton("Yes 4k hai", callback_data="4k_yes")],
            [InlineKeyboardButton("No 4k nhi hai", callback_data="4k_no")],
            [InlineKeyboardButton("4k only", callback_data="4k_only")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Kripya 4k ka option select karein:", reply_markup=reply_markup)
        return

    # 4. Agar user "No 4k nhi hai" ke baad custom content text bhejta hai
    elif user_id in USER_STATES and USER_STATES[user_id]["step"] == "waiting_for_custom_content":
        USER_STATES[user_id]["content_text"] = text.strip() if text else ""
        await send_movie_messages(update, user_id)
        return

    # 5. Agar user "Yes 4k hai" ke baad normal content text bhejta hai
    elif user_id in USER_STATES and USER_STATES[user_id]["step"] == "waiting_for_content":
        USER_STATES[user_id]["content_text"] = text.strip() if text else ""
        await send_movie_messages(update, user_id)
        return

    else:
        if user_id not in USER_STATES:
            await update.message.reply_text("Kripya pehle koi movie/series ka photo ya image link bhejein.")


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if user_id not in USER_STATES:
        await query.edit_message_text("Session expire ho gaya hai. Kripya dubara photo bhejein.")
        return

    # Step 1: Category selection (New & Exclusive vs Old is Gold)
    if USER_STATES[user_id]["step"] == "waiting_for_category":
        if data == "cat_new":
            USER_STATES[user_id]["category"] = "new"
        elif data == "cat_old":
            USER_STATES[user_id]["category"] = "old"
            
        USER_STATES[user_id]["step"] = "waiting_for_title"
        await query.edit_message_text(f"Selected: {query.message.text}\n\nDave Kumar ye film ya web series ka kya naam hai")
        return

    # Step 3: 4K Buttons handling ("Yes 4k hai", "No 4k nhi hai", "4k only")
    elif USER_STATES[user_id]["step"] == "waiting_for_4k_buttons":
        if data == "4k_only":
            # 4k only wala hisab
            USER_STATES[user_id]["include_4k"] = True
            USER_STATES[user_id]["skip_content_prompt"] = True
            USER_STATES[user_id]["content_text"] = ""
            await query.edit_message_text("4k only selected.")
            await send_movie_messages(update, user_id)
            return

        elif data == "4k_no":
            # No 4k nhi hai wala hisab
            USER_STATES[user_id]["include_4k"] = False
            USER_STATES[user_id]["skip_content_prompt"] = False
            USER_STATES[user_id]["step"] = "waiting_for_custom_content"
            await query.edit_message_text("No 4k nhi hai selected. Btaiye kya kya likha jaye")
            return

        elif data == "4k_yes":
            # Yes 4k hai wala hisab
            USER_STATES[user_id]["include_4k"] = True
            USER_STATES[user_id]["skip_content_prompt"] = False
            USER_STATES[user_id]["step"] = "waiting_for_content"
            await query.edit_message_text("Yes 4k hai selected. Kuch andar ka baat btao na...")
            return


async def send_movie_messages(update: Update, user_id: int):
    state = USER_STATES[user_id]
    image_source = state["image_source"]
    movie_title = state["movie_title"]
    movie_year = state["movie_year"]
    include_4k = state.get("include_4k", True)
    content_text = state.get("content_text", "")
    category = state.get("category", "new")
    
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

        # Pehla caption
        caption_text_1 = (
            f"<tg-emoji emoji-id=\"6312234398943023797\">🆕</tg-emoji> <b>{movie_title}</b> ({movie_year}) <tg-emoji emoji-id=\"5325670588461632571\">🔥</tg-emoji>\n\n"
            f"<blockquote>{middle_block}</blockquote>\n\n"
            " "
            "<tg-emoji emoji-id=\"5371081166013078244\">🍿</tg-emoji> Visit <b>HDHub4u</b><tg-emoji emoji-id=\"5190758974135212829\">🕺</tg-emoji>"
        )
        
        # Dusra caption
        caption_text_2 = (
            "<tg-emoji emoji-id=\"6159046264253059501\">🤩</tg-emoji><tg-emoji emoji-id=\"6156621398732182933\">🤩</tg-emoji><tg-emoji emoji-id=\"6158777532444316203\">🤩</tg-emoji><tg-emoji emoji-id=\"6156843319692367185\">🤩</tg-emoji><tg-emoji emoji-id=\"6156552632010806111\">🤩</tg-emoji><tg-emoji emoji-id=\"6156520617324582815\">🤩</tg-emoji><tg-emoji emoji-id=\"6156728837339091660\">🤩</tg-emoji><tg-emoji emoji-id=\"6156477856630181980\">🤩</tg-emoji><tg-emoji emoji-id=\"6159046264253059501\">🤩</tg-emoji>\n\n"
            f"<tg-emoji emoji-id=\"6312234398943023797\">🆕</tg-emoji> <b>{movie_title}</b> ({movie_year}) <tg-emoji emoji-id=\"5325670588461632571\">🔥</tg-emoji>\n\n"
            f"<blockquote>{middle_block}</blockquote>\n\n"
            " "
            "<tg-emoji emoji-id=\"5371081166013078244\">🍿</tg-emoji> Visit <b>HDHub4u</b><tg-emoji emoji-id=\"5190758974135212829\">🕺</tg-emoji>"
        )

        # Teesra caption
        caption_text_3 = (
            f"<tg-emoji emoji-id=\"6098177227524936926\">↗️</tg-emoji> <b>{movie_title}</b> ({movie_year}) <tg-emoji emoji-id=\"5325670588461632571\">🔥</tg-emoji>\n\n"
            f"<blockquote>{middle_block}</blockquote>\n\n"
            " "
            "<tg-emoji emoji-id=\"5371081166013078244\">🍿</tg-emoji> Visit <b>HDHub4u</b><tg-emoji emoji-id=\"5190758974135212829\">🕺</tg-emoji>"
        )

        target_message = update.message or update.callback_query.message

        # Messages send karein (Chahe "New and Exclusive" ho ya "Old is Gold", pehle 2 replies hi jayenge kyunki 3rd output post nahi karna hai)
        await target_message.reply_photo(photo=image_source, caption=caption_text_1, parse_mode="HTML")
        await target_message.reply_photo(photo=image_source, caption=caption_text_2, parse_mode="HTML")
        
        # Agar aap chahein ki 3rd output ko conditionally rokna hai toh ye check laga diya hai:
        # (Yahan user ki requirement ke mutabiq dono button options ke liye sirf pehle 2 replies hi bhej rahe hain)

    except Exception as e:
        target_message = update.message or update.callback_query.message
        await target_message.reply_text("Image load karne mein error aayi, link ya photo check karein.")

def main():
    TOKEN = os.environ.get("TOKEN")
    
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler((filters.TEXT | filters.PHOTO) & (~filters.COMMAND), handle_message))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    print("Bot start ho gaya hai...")
    app.run_polling()

if __name__ == '__main__':
    main()
