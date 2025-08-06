from typing import Final
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes
)
from rag.langchain_pipeline import answer_query
from tools.ocr_reader import extract_text_from_image
from tools.voice_handler import voice_handler
from tools.reminder_handler import add_reminder_command
import os
import tempfile

TOKEN = '7677389671:AAE_ILH0WyacSU21vqUlLCIn_m-gSY-pNfg'
BOT_USERNAME: Final = '@medication_remider_and_info_bot'

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 হ্যালো! আমি আপনার bilingual ঃওষুধ সহয়কারী বট। ইংরেজি বা বাংলা ভাষায় প্রশ্ন করুন, ঃওষুধের ছবি বা ভয়েস মেসেজ পাঠান।"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            """❓ আপনি প্রশ্ন করতে পারেন:
    - What is Paracetamol?
    - সেক্লোর পার্শ্বপ্রতিক্রিয়া কী?
    - অথবা ঃওষুধের ছবি বা ভয়েস মেসেজ দিন।"""
        )

def handle_response(text: str) -> str:
    try:
        return answer_query(text)
    except Exception as e:
        print("❌ handle_response error:", e)
        return "⚠️ বুঝতে পারিনি। আবার চেষ্টা করুন।"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    response = handle_response(text)
    await update.message.reply_text(response)

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        voice = update.message.voice
        file = await voice.get_file()

        temp_ogg = tempfile.NamedTemporaryFile(delete=False, suffix='.ogg')
        await file.download_to_drive(temp_ogg.name)
        temp_ogg.close()

        recognized_text, detected_lang = voice_handler.speech_to_text(temp_ogg.name, return_lang=True)
        os.unlink(temp_ogg.name)

        if not recognized_text:
            await update.message.reply_text("❌ দুর্ভান, দ্যানি ভয়েস বুঝা যায়নি।")
            return

        await update.message.reply_text(f"🎙️ আপনি বলেছেন: {recognized_text}")
        answer = handle_response(recognized_text)
        await update.message.reply_text(f"📝 উত্তর:\n{answer}")

        tts_path = voice_handler.text_to_speech(answer, language=detected_lang)
        if tts_path and os.path.exists(tts_path):
            with open(tts_path, 'rb') as voice_file:
                await update.message.reply_voice(voice=voice_file)
            os.unlink(tts_path)
        else:
            await update.message.reply_text("⚠️ ভয়েসে উত্তর পাঠানো যায়নি।")

    except Exception as e:
        print(f"❌ Voice handling error: {e}")
        await update.message.reply_text("⚠️ ভয়েস মেসেজ প্রসেস করতে সমস্যা হয়েছে।")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        photo = update.message.photo[-1]
        file = await photo.get_file()
        file_path = f"temp_{update.message.chat.id}.jpg"
        await file.download_to_drive(file_path)

        ocr_text = extract_text_from_image(file_path)
        os.remove(file_path)

        if not ocr_text:
            await update.message.reply_text("⚠️ কোন লেখা পড়া যায়নি।")
            return

        context.user_data['ocr_text'] = ocr_text
        keyboard = [
            [InlineKeyboardButton("🇧🇫 বাংলা", callback_data='lang_ben')],
            [InlineKeyboardButton("🇬🇧 English", callback_data='lang_eng')],
        ]
        await update.message.reply_text(
            f"📜 OCR টেক্সট:\n{ocr_text}\n\n🌐 ভাষা বেছে নিন:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        print(f"❌ OCR error: {e}")
        await update.message.reply_text("⚠️ ছবি প্রসেস করতে সমস্যা হয়েছে।")

async def handle_language_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['lang'] = query.data.replace('lang_', '')

    keyboard = [
        [InlineKeyboardButton("💊 General Info", callback_data='query_general')],
        [InlineKeyboardButton("⚠️ Side Effects", callback_data='query_side_effects')],
        [InlineKeyboardButton("📘 Usage", callback_data='query_usage')],
    ]
    await query.edit_message_text("🔍 তথ্য বেছে নিন:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_query_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get('lang', 'eng')
    ocr_text = context.user_data.get('ocr_text', '')
    if not ocr_text:
        await query.edit_message_text("⚠️ OCR ডেটা পাওয়া যায়নি।")
        return

    prompts = {
        'general': {'eng': "What is this medicine?", 'ben': "এই ওষুধটি কী?"},
        'side_effects': {'eng': "What are the side effects?", 'ben': "পার্শ্বপ্রতিক্রিয়া কী?"},
        'usage': {'eng': "How to use this medicine?", 'ben': "ব্যবহারবিধি কী?"}
    }

    query_type = query.data.replace('query_', '')
    full_query = f"{prompts[query_type][lang]}\n\n{ocr_text}"

    try:
        response = answer_query(full_query)
    except:
        response = "⚠️ তথ্য আনতে সমস্যা হয়েছে।"

    await query.message.reply_text(response)

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"⚠️ Error: {context.error}")

if __name__ == '__main__':
    print("🤖 Bot is starting...")
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler('start', start_command))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('remind', add_reminder_command))
   

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    application.add_handler(CallbackQueryHandler(handle_language_selection, pattern='^lang_'))
    application.add_handler(CallbackQueryHandler(handle_query_selection, pattern='^query_'))
    application.add_error_handler(error)

    print("✅ Bot is running with full voice + reminder support")
    application.run_polling(poll_interval=3)