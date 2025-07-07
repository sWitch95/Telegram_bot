from typing import Final
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from rag.langchain_pipeline import answer_query

TOKEN = '7677389671:AAE_ILH0WyacSU21vqUlLCIn_m-gSY-pNfg'
BOT_USERNAME: Final = '@medication_remider_and_info_bot'

# 🔹 Start Command
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hello! আমি আপনার bilingual ওষুধ সহকারী বট।\n"
        "আপনি ইংরেজি বা বাংলা যেকোনো ভাষায় প্রশ্ন করতে পারেন।"
    )

# 🔹 Help Command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❓ উদাহরণ:\n"
        "- What is Paracetamol?\n"
        "- সেক্লোর পার্শ্বপ্রতিক্রিয়া কী?\n"
        "- Napa কিসের জন্য ব্যবহৃত হয়?"
    )

# 🔹 Custom Command (optional)
async def custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚙️ Custom command active!")

# 🔄 Main handler
def handle_response(text: str) -> str:
    try:
        return answer_query(text)  # handled inside langchain_pipeline
    except Exception as e:
        print("❌ handle_response error:", e)
        return "⚠️ I'm having trouble understanding. Please try again."

# 💬 Message handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type = update.message.chat.type
    text = update.message.text.strip()

    print(f"📥 User ({update.message.chat.id}) in {message_type}: {text}")

    if message_type == 'group' and BOT_USERNAME in text:
        text = text.replace(BOT_USERNAME, '').strip()

    response = handle_response(text)
    await update.message.reply_text(response)

# ⚠️ Error handler
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"⚠️ Error: {context.error}")

# 🚀 Run bot
if __name__ == '__main__':
    print("🤖 Bot is starting...")
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler('start', start_command))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('custom', custom_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error)

    print("✅ Bot is running...")
    application.run_polling(poll_interval=3)
