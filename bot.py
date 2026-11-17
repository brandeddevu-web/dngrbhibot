import os
import yt_dlp
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

# Conversation state maintain karne ke liye dictionary
USER_STATES = {}

# Instagram reel se views nikalne ka function (Bina cookies ke)
def get_insta_reel_views(url: str):
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'skip_download': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            # Views ya play count nikalne ki koshish karein
            views = info.get('view_count') or info.get('play_count')
            if views:
                return views
    except Exception as e:
        print(f"Error fetching views: {e}")
    return None

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

    # 0. Agar user ne shuru mein "insta", "ig", ya "instagram" bheja hai
    if text and text.strip().lower() in ["insta", "ig", "instagram"]:
        USER_STATES[user_id] = {
            "step": "waiting_for_insta_link"
        }
        await update.message.reply_text("Bhai, Instagram reel ka link bhejo na!")
        return

    # Instagram link ka reply handle karne ke liye aur views fetch karne ke liye
    if user_id in USER_STATES and USER_STATES[user_id]["step"] == "waiting_for_insta_link":
        reel_link = text.strip() if text else ""
        
        await update.message.reply_text("🔍 Reel se views check kiye ja rahe hain, thoda wait karo...")
        
        # Views fetch karein
        views = get_insta_reel_views(reel_link)
        
        if views is not None:
            formatted_views = f"{views:,}"
            await update.message.reply_text(f"📊 Is Instagram reel par total **{formatted_views}** views hain! 🔥")
        else:
            await update.message.reply_text("❌ Views fetch nahi ho paye. Railway IP ko Instagram ne block kar diya hai, isliye bina cookies ke views show hona mushkil hai.")
        
        # State clear kar dein
        del USER_STATES[user_id]
        return

    # 1. Agar user ne movie/series ka naam diya hai[span_1](start_span)[span_1](end_span)
    if user_id in USER_STATES and USER_STATES[user_id]["step"] == "waiting_for_title":
        USER_STATES[user_id]["movie_title"] = text.strip() if text else ""
        USER_STATES[user_id]["step"] = "waiting_for_year"
        
        await update.message.reply_text("ye kaunse jamane ka film hai ya ye kaunsa season hai batao na")
        return

    # 2. Agar user ne year/season ka reply diya hai[span_2](start_span)[span_2](end_span)
    elif user_id in USER_STATES and USER_STATES[user_id]["step"] == "waiting_for_year":
        USER_STATES[user_id]["movie_year"] = text.strip() if text else ""
        USER_STATES[user_id]["step"] = "waiting_for_4k_choice"
        
        await update.message.reply_text("4k speed me 69 baar download hoga ya nahi")
        return

    # 3. Agar user ne 4k rakhne ka choice diya hai[span_3](start_span)[span_3](end_span)
    elif user_id in USER_STATES and USER_STATES[user_id]["step"] == "waiting_for_4k_choice":
        choice = text.strip().lower() if text else ""
        
        if choice == "4k":
            USER_STATES[user_id]["include_4k"] = True
            USER_STATES[user_id]["skip_content_prompt"] = True
            USER_STATES[user_id]["content_text"] = ""
            await send_movie_messages(update, user_id)
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

    # 4. Agar user ne "No" ke baad custom content ka reply diya hai[span_4](start_span)[span_4](end_span)
    elif user_id in USER_STATES and USER_STATES[user_id]["step"] == "waiting_for_custom_content":
        USER_STATES[user_id]["content_text"] = text.strip() if text else ""
        await send_movie_messages(update, user_id)
        return

    # 5. Agar user ne normal content ka reply diya hai[span_5](start_span)[span_5](end_span)
    elif user_id in USER_STATES and USER_STATES[user_id]["step"] == "waiting_for_content":
        USER_STATES[user_id]["content_text"] = text.strip() if text else ""
        await send_movie_messages(update, user_id)
        return

    # 6. Agar user ne nayi shuruwat ki hai aur Photo bheji hai[span_6](start_span)[span_6](end_span)
    elif image_input:
        USER_STATES[user_id] = {
            "step": "waiting_for_title",
            "image_source": image_input,
            "is_file_id": bool(photo)
        }
        await update.message.reply_text("Dave Kumar ye film ya web series ka kya naam hai")


async def send_movie_messages(update: Update, user_id: int):
    state = USER_STATES[user_id]
    image_source = state["image_source"]
    movie_title = state["movie_title"]
    movie_year = state["movie_year"]
    include_4k = state.get("include_4k", True)
    content_text = state.get("content_text", "")
    
    del USER_STATES[user_id]

    try:
        if not include_4k:
            middle_block = f"<tg-emoji emoji-id=\"6312153851126354884\">➡️</tg-emoji> {content_text} Added <tg-emoji emoji-id=\"5274099962655816924\">❗️</tg-emoji>"
        else:
            if content_text.strip():
                emoji_4k_part = f"<tg-emoji emoji-id=\"5224607267797606837\">☄️</tg-emoji> <b>4k</b>"
                middle_block = f"<tg-emoji emoji-id=\"6312153851126354884\">➡️</tg-emoji> {content_text} {emoji_4k_part} Added <tg-emoji emoji-id=\"5274099962655816924\">❗️</tg-emoji>"
            else:
                middle_block = f"<tg-emoji emoji-id=\"6312153851126354884\">➡️</tg-emoji> <b>4k</b> Added <tg-emoji emoji-id=\"5274099962655816924\">❗️</tg-emoji>"

        caption_text_1 = (
            f"<tg-emoji emoji-id=\"6312234398943023797\">🆕</tg-emoji> <b>{movie_title}</b> ({movie_year}) <tg-emoji emoji-id=\"5325670588461632571\">🔥</tg-emoji>\n\n"
            f"<blockquote>{middle_block}</blockquote>\n\n"
            " "
            "<tg-emoji emoji-id=\"6096080291347042802\">📥</tg-emoji> Added on <b>HDHub4u</b><tg-emoji emoji-id=\"5190758974135212829\">🕺</tg-emoji>"
        )
        
        caption_text_2 = (
            "<tg-emoji emoji-id=\"6159046264253059501\">🤩</tg-emoji><tg-emoji emoji-id=\"6156621398732182933\">🤩</tg-emoji><tg-emoji emoji-id=\"6158777532444316203\">🤩</tg-emoji><tg-emoji emoji-id=\"6156843319692367185\">🤩</tg-emoji><tg-emoji emoji-id=\"6156552632010806111\">🤩</tg-emoji><tg-emoji emoji-id=\"6156520617324582815\">🤩</tg-emoji><tg-emoji emoji-id=\"6156728837339091660\">🤩</tg-emoji><tg-emoji emoji-id=\"6156477856630181980\">🤩</tg-emoji><tg-emoji emoji-id=\"6159046264253059501\">🤩</tg-emoji>\n\n"
            f"<tg-emoji emoji-id=\"6312234398943023797\">🆕</tg-emoji> <b>{movie_title}</b> ({movie_year}) <tg-emoji emoji-id=\"5325670588461632571\">🔥</tg-emoji>\n\n"
            f"<blockquote>{middle_block}</blockquote>\n\n"
            " "
            "<tg-emoji emoji-id=\"6096080291347042802\">📥</tg-emoji> Added on <b>HDHub4u</b><tg-emoji emoji-id=\"5190758974135212829\">🕺</tg-emoji>"
        )

        await update.message.reply_photo(photo=image_source, caption=caption_text_1, parse_mode="HTML")
        await update.message.reply_photo(photo=image_source, caption=caption_text_2, parse_mode="HTML")

    except Exception as e:
        await update.message.reply_text("Image load karne mein error aayi, link ya photo check karein.")

def main():
    TOKEN = os.environ.get("TOKEN")
    
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler((filters.TEXT | filters.PHOTO) & (~filters.COMMAND), handle_message))
    
    print("Bot start ho gaya hai...")
    app.run_polling()

if __name__ == '__main__':
    main()
