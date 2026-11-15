import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from playwright.async_api import async_playwright

SECRET_PASSKEY = "2000"
authorized_users = set()
user_credentials = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if chat_id not in authorized_users:
        await update.message.reply_text(
            "🔒 **هذا البوت محمي!**\n\n"
            "من فضلك أدخل **مفتاح المرور** الخاص بالبوت لتفعيله:"
        )
    else:
        await update.message.reply_text("🔓 البوت مفعل لديك. أرسل اسم المستخدم وكلمة المرور للمنصة الآن.")

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    text = update.message.text.strip()

    if chat_id not in authorized_users:
        if text == SECRET_PASSKEY:
            authorized_users.add(chat_id)
            await update.message.reply_text(
                "✅ **مفتاح المرور صحيح!**\n\n"
                "الآن أرسل اسم المستخدم وكلمة المرور الخاصة بمنصة كوريو في رسالة واحدة بينهم مسافة:\n"
                "`user pass`",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("❌ مفتاح المرور خطأ!")
        return

    parts = text.split()
    if len(parts) < 2:
        await update.message.reply_text("⚠️ يرجى إرسال اسم المستخدم وكلمة المرور بالشكل الصحيح.")
        return

    user_credentials[chat_id] = {"username": parts[0], "password": parts[1]}

    keyboard = [
        [InlineKeyboardButton("💻 جافا سكريبت (JavaScript)", callback_data="solve_js")],
        [InlineKeyboardButton("🐍 بايثون (Python)", callback_data="solve_python")],
        [InlineKeyboardButton("📊 إدارة الأعمال / الثقافة المالية", callback_data="solve_business")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("✅ تم الحفظ! اختر القسم المراد حلّه:", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id

    if chat_id not in authorized_users or chat_id not in user_credentials:
        await query.edit_message_text("⚠️ الجلسة انتهت أو غير مصرح لك.")
        return

    creds = user_credentials[chat_id]
    choice = query.data
    await query.edit_message_text("⏳ جاري الدخول للمنصة والحل تلقائياً...")

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            await page.goto("https://qureo.education/")
            await page.fill("input[name='username']", creds["username"])
            await page.fill("input[name='password']", creds["password"])
            await page.click("button[type='submit']")
            await page.wait_for_load_state("networkidle")

            await asyncio.sleep(5)
            await browser.close()

        await query.message.reply_text("🎉 تم الانتهاء من حل الفصول بنجاح!")
    except Exception as e:
        await query.message.reply_text(f"❌ حدث خطأ أثناء التشغيل.")

def main():
    TOKEN = os.getenv("BOT_TOKEN")
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_messages))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()

if __name__ == "__main__":
    main()
