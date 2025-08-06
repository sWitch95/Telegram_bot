from dateutil import parser  # Install this if not done
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes
import re

scheduled_reminders = {}

async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
    job_data = context.job.data
    chat_id = job_data["chat_id"]
    message = job_data["message"]
    await context.bot.send_message(chat_id=chat_id, text=f"⏰ ওষুধ মনে করিয়ে দিচ্ছি:\n{message}")

async def add_reminder_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text.replace('/remind', '').strip()
        print(f"📝 Raw reminder text: {text}")

        match = re.search(r'at\s*([0-9]{1,2}:[0-9]{2}\s*(?:am|pm)?)', text, re.IGNORECASE)
        if not match:
            match = re.search(r'([0-9]{1,2}:[0-9]{2}\s*(?:am|pm)?)', text, re.IGNORECASE)

        if not match:
            await update.message.reply_text("⚠️ মনে করানোর সময় সঠিক ফরম্যাটে দিন (যেমন: 7:30 AM)")
            return

        time_str = match.group(1).replace(' ', '').strip()  # Remove spaces for parser compatibility
        medicine_name = re.sub(r'at\s*[0-9]{1,2}:[0-9]{2}\s*(?:am|pm)?', '', text, flags=re.IGNORECASE)
        medicine_name = medicine_name.replace('everyday', '').strip()

        now = datetime.now()
        parsed_time = parser.parse(time_str)
        reminder_time = now.replace(hour=parsed_time.hour, minute=parsed_time.minute, second=0, microsecond=0)

        if reminder_time < now:
            reminder_time += timedelta(days=1)

        delay = (reminder_time - now).total_seconds()

        if delay <= 0:
            await update.message.reply_text("⚠️ অনুগ্রহ করে ভবিষ্যতের সময় দিন।")
            return

        job_name = f"reminder_{update.message.chat_id}_{medicine_name}_{time_str}"
        context.job_queue.run_once(
            send_reminder,
            when=delay,
            data={"chat_id": update.message.chat_id, "message": medicine_name},
            name=job_name
        )

        scheduled_reminders[job_name] = {
            "user": update.message.chat_id,
            "medicine": medicine_name,
            "time": reminder_time.strftime("%I:%M %p")
        }

        await update.message.reply_text(
            f"✅ মনে করিয়ে দেয়া হবে: {medicine_name} @ {reminder_time.strftime('%I:%M %p')}"
        )

    except Exception as e:
        print(f"❌ Reminder setup failed: {e}")
        await update.message.reply_text("⚠️ মনে করানোর সময় সেট করতে ব্যর্থ। ফরম্যাট ঠিক আছে কিনা দেখুন।")
