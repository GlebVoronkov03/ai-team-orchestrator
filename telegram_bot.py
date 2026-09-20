import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from orchestrator import app, TeamState

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь задачу, и AI-команда начнёт работу.")

async def handle_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    task = update.message.text
    await update.message.reply_text("Запускаю команду агентов (язык Python)...")
    state = TeamState(task=task, context={}, next_agent="", step_by_step=False, programming_language="python")
    final = app.invoke(state)
    code = final["context"].get("code", "Код не сгенерирован")
    if len(code) > 4000:
        code = code[:4000] + "\n...(обрезано)"
    await update.message.reply_text(f"Результат:\n```python\n{code}\n```", parse_mode="Markdown")

def main():
    if not BOT_TOKEN:
        print("Установите TELEGRAM_BOT_TOKEN в .env")
        return
    app_bot = Application.builder().token(BOT_TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_task))
    app_bot.run_polling()

if __name__ == "__main__":
    main()