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
        "👋 হ্যালো! আমি আপনার bilingual ওষুধ সহকারী বট।\n"
        "ইংরেজি বা বাংলা যেকোনো ভাষায় প্রশ্ন করুন বা ওষুধের ছবি দিন।"
    )

# 🔹 Help Command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❓ আপনি নিচের মত প্রশ্ন করতে পারেন:\n"
        "- What is Napa?\n"
        "- সেক্লোর পার্শ্বপ্রতিক্রিয়া কী?\n"
        "- Napa কিসের জন্য ব্যবহৃত হয়?\n"
        "- অথবা শুধু ওষুধের লেবেলের ছবি দিন।"
    )

# 🔄 Query processor
def handle_response(text: str) -> str:
    try:
        return answer_query(text)
    except Exception as e:
        print("❌ handle_response error:", e)
        return "⚠️ বুঝতে পারিনি। আবার চেষ্টা করুন।"

# 💬 Text
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    print(f"📥 User ({update.message.chat.id}): {text}")
    response = handle_response(text)
    await update.message.reply_text(response)

# 🖼️ Handle Photo with OCR
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        photo = update.message.photo[-1]
        file = await photo.get_file()

        file_path = f"temp_{update.message.chat.id}.jpg"
        await file.download_to_drive(file_path)

        ocr_text = extract_text_from_image(file_path)
        os.remove(file_path)

        if not ocr_text:
            await update.message.reply_text("⚠️ কোন লেখা পড়া যায়নি। অনুগ্রহ করে স্পষ্ট ছবি দিন।")
            return

        # Save OCR text
        context.user_data['ocr_text'] = ocr_text

        # Language selection keyboard
        keyboard = [
            [InlineKeyboardButton("🇧🇩 বাংলা", callback_data='lang_ben')],
            [InlineKeyboardButton("🇬🇧 English", callback_data='lang_eng')],
        ]
        await update.message.reply_text(
            f"🧾 OCR টেক্সট:\n{ocr_text}\n\n🌐 আপনি কোন ভাষায় তথ্য পেতে চান?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception as e:
        print(f"❌ Error in handle_photo: {e}")
        await update.message.reply_text("⚠️ ছবি প্রসেস করতে সমস্যা হয়েছে। পরে আবার চেষ্টা করুন।")

# 🌐 Language Selection Handler
async def handle_language_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    lang_code = query.data.replace('lang_', '')  # 'ben' or 'eng'
    context.user_data['lang'] = lang_code

    # Query type buttons
    keyboard = [
        [InlineKeyboardButton("💊 General Info / সাধারণ তথ্য", callback_data='query_general')],
        [InlineKeyboardButton("⚠️ Side Effects / পার্শ্বপ্রতিক্রিয়া", callback_data='query_side_effects')],
        [InlineKeyboardButton("📘 Usage / ব্যবহারের নিয়ম", callback_data='query_usage')],
        [InlineKeyboardButton("🧬 Pharmacology / ফার্মাকোলজি", callback_data='query_pharmacology')],
        [InlineKeyboardButton("👶 Pediatric Use / শিশুদের ব্যবহার", callback_data='query_pediatric')],
        [InlineKeyboardButton("🏭 Manufacturer / প্রস্তুতকারক", callback_data='query_manufacturer')],
    ]
    await query.edit_message_text(
        "🔍 এখন আপনি কোন তথ্য জানতে চান তা বেছে নিন (একাধিক বার ক্লিক করা যাবে):",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# 📌 Query Execution Handler (multiple clicks allowed)
async def handle_query_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    ocr_text = context.user_data.get('ocr_text', '')
    lang = context.user_data.get('lang', 'eng')  # Default to English

    if not ocr_text:
        await query.edit_message_text("⚠️ OCR ফলাফল পাওয়া যায়নি। আবার ছবি পাঠান।")
        return

    query_type = query.data.replace('query_', '')

    # Language-wise prompts
    prompts = {
        'general': {
            'eng': "What is this medicine?",
            'ben': "এই ওষুধটি কী?"
        },
        'side_effects': {
            'eng': "What are the side effects of this medicine?",
            'ben': "এই ওষুধের পার্শ্বপ্রতিক্রিয়া কী?"
        },
        'usage': {
            'eng': "How is this medicine used?",
            'ben': "এই ওষুধটি কীভাবে ব্যবহার করা হয়?"
        },
        'pharmacology': {
            'eng': "Describe the pharmacology of this medicine.",
            'ben': "এই ওষুধের ফার্মাকোলজিকাল বিবরণ দিন।"
        },
        'pediatric': {
            'eng': "What is the pediatric usage of this medicine?",
            'ben': "শিশুদের ক্ষেত্রে এই ওষুধের ব্যবহার কেমন?"
        },
        'manufacturer': {
            'eng': "Who manufactures this medicine?",
            'ben': "এই ওষুধটি কোন কোম্পানি তৈরি করে?"
        },
    }

    prompt = prompts[query_type][lang]
    full_query = f"{prompt}\n\n{ocr_text}"

    try:
        response = answer_query(full_query)
    except Exception as e:
        print("❌ Error:", e)
        response = "⚠️ তথ্য আনতে সমস্যা হয়েছে।"

    await query.message.reply_text(f"🔍 {prompt}\n\n{response}")

# ⚠️ Error
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"⚠️ Error: {context.error}")

# 🚀 Run Bot
if __name__ == '__main__':
    print("🤖 Bot is starting...")
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler('start', start_command))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    application.add_handler(CallbackQueryHandler(handle_language_selection, pattern='^lang_'))
    application.add_handler(CallbackQueryHandler(handle_query_selection, pattern='^query_'))
    application.add_error_handler(error)

    print("✅ Bot is running...")
    application.run_polling(poll_interval=3)
