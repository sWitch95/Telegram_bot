from typing import Final
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes
)
from rag.langchain_pipeline import answer_query
from tools.ocr_reader import extract_text_from_image
import os

TOKEN = '7677389671:AAE_ILH0WyacSU21vqUlLCIn_m-gSY-pNfg'
BOT_USERNAME: Final = '@medication_remider_and_info_bot'

# 🔹 Start Command
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hello! আমি আপনার bilingual ওষুধ সহকারী বট।\n"
        "আপনি ইংরেজি বা বাংলা যেকোনো ভাষায় প্রশ্ন করতে পারেন।\n"
        "ছবি পাঠালে আমি তা থেকে ওষুধ পড়েও তথ্য দিতে পারি।"
    )

# 🔹 Help Command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❓ উদাহরণ:\n"
        "- What is Paracetamol?\n"
        "- সেক্লোর পার্শ্বপ্রতিক্রিয়া কী?\n"
        "- Napa কিসের জন্য ব্যবহৃত হয়?\n"
        "- Or just send a medicine photo."
    )

# 🔹 Custom Command (optional)
async def custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚙️ Custom command active!")

# 🔄 Text message handler → Query LLM
def handle_response(text: str) -> str:
    try:
        return answer_query(text)
    except Exception as e:
        print("❌ handle_response error:", e)
        return "⚠️ I'm having trouble understanding. Please try again."

# 💬 Regular text message
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type = update.message.chat.type
    text = update.message.text.strip()

    print(f"📥 User ({update.message.chat.id}) in {message_type}: {text}")

    if message_type == 'group' and BOT_USERNAME in text:
        text = text.replace(BOT_USERNAME, '').strip()

    response = handle_response(text)
    await update.message.reply_text(response)

# 🖼️ Handle photo messages (OCR → Multiple query options)
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        photo = update.message.photo[-1]
        file = await photo.get_file()

        file_path = f"temp_{update.message.chat.id}.jpg"
        await file.download_to_drive(file_path)

        ocr_text = extract_text_from_image(file_path)
        os.remove(file_path)

        if not ocr_text:
            await update.message.reply_text("⚠️ Couldn't read any text. Please send a clearer image.")
            return

        # Store OCR text for follow-up button queries
        context.user_data['ocr_text'] = ocr_text

        keyboard = [
            [InlineKeyboardButton("💊 General Info", callback_data='general')],
            [InlineKeyboardButton("⚠️ Side Effects", callback_data='side_effects')],
            [InlineKeyboardButton("📘 Usage", callback_data='usage')],
            [InlineKeyboardButton("🧬 Pharmacology", callback_data='pharmacology')],
            [InlineKeyboardButton("👶 Pediatric Usage", callback_data='pediatric')],
            [InlineKeyboardButton("🏭 Manufacturer", callback_data='manufacturer')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"🧾 OCR Text:\n{ocr_text}\n\n🔍 এখন আপনি কী তথ্য জানতে চান সেটি নির্বাচন করুন:",
            reply_markup=reply_markup
        )

    except Exception as e:
        print(f"❌ Error in handle_photo: {e}")
        await update.message.reply_text("⚠️ Something went wrong while processing the image.")

# 🎯 Handle button clicks for specific queries
async def handle_photo_query_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    ocr_text = context.user_data.get('ocr_text', '')
    query_type = query.data

    if not ocr_text:
        await query.edit_message_text("⚠️ OCR result missing. Please resend the image.")
        return

    query_map = {
        "general": "What is this medicine?",
        "side_effects": "What are the side effects of this medicine?",
        "usage": "How is this medicine used?",
        "pharmacology": "Describe the pharmacology of this medicine.",
        "pediatric": "What is the pediatric usage of this medicine?",
        "manufacturer": "Who is the manufacturer of this medicine?",
    }

    selected_prompt = f"{query_map[query_type]}\n\n{ocr_text}"
    try:
        response = answer_query(selected_prompt)
    except Exception as e:
        print("❌ Query handler error:", e)
        response = "⚠️ Sorry, I couldn't process that query."

    await query.edit_message_text(
        f"🧾 OCR Text:\n{ocr_text}\n\n🔍 {query_map[query_type]}:\n{response}"
    )

# ⚠️ Error handler
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"⚠️ Error: {context.error}")

# 🚀 Run the bot
if __name__ == '__main__':
    print("🤖 Bot is starting...")
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler('start', start_command))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('custom', custom_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(CallbackQueryHandler(handle_photo_query_selection))  # Button clicks
    application.add_error_handler(error)

    print("✅ Bot is running...")
    application.run_polling(poll_interval=3)
