import os
import re
from dotenv import load_dotenv
from telegram import Update, ChatMember
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# โหลด environment variables
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Pattern สำหรับตรวจจับลิงก์
LINK_PATTERN = re.compile(
    r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    r'|www\.[a-zA-Z0-9.-]+'
    r'|t\.me/[a-zA-Z0-9_]+'
)

# เก็บข้อมูลการเตือนของผู้ใช้ {chat_id: {user_id: warning_count}}
user_warnings = {}

async def is_user_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    """ตรวจสอบว่าผู้ใช้เป็น Admin หรือไม่"""
    try:
        chat_id = update.message.chat_id
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]
    except Exception as e:
        print(f"ข้อผิดพลาดในการตรวจสอบ admin: {e}")
        return False

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """คำสั่ง /start"""
    await update.message.reply_text(
        "🤖 สวัสดีครับ! ผมเป็นบอท Antilink\n\n"
        "ผมจะช่วยลบข้อความที่มีลิงก์ในกลุ่มอัตโนมัติ\n\n"
        "📌 วิธีใช้งาน:\n"
        "1. เพิ่มบอทเข้ากลุ่ม\n"
        "2. ตั้งค่าให้บอทเป็น Admin\n"
        "3. เปิดสิทธิ์ 'Delete Messages' และ 'Ban Users'\n"
        "4. เสร็จแล้ว! บอทจะทำงานอัตโนมัติ\n\n"
        "⚠️ กฎการลงโทษ:\n"
        "• ครั้งที่ 1: เตือน\n"
        "• ครั้งที่ 2: แบนออกจากกลุ่ม\n"
        "• Admin ไม่ถูกลงโทษ"
    )

async def check_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ตรวจสอบข้อความว่ามีลิงก์หรือไม่"""
    if update.message and update.message.text:
        message = update.message
        text = message.text
        user = message.from_user
        chat_id = message.chat_id
        user_id = user.id

        # ตรวจสอบว่าข้อความมีลิงก์หรือไม่
        if LINK_PATTERN.search(text):
            # ตรวจสอบว่าผู้ใช้เป็น Admin หรือไม่
            if await is_user_admin(update, context, user_id):
                print(f"Admin {user.first_name} ส่งลิงก์ - ไม่ดำเนินการ")
                return

            try:
                # ลบข้อความที่มีลิงก์
                await message.delete()

                # เตรียมข้อมูลผู้ใช้
                username = f"@{user.username}" if user.username else user.first_name

                # สร้าง dictionary สำหรับเก็บ warning ของกลุ่มนี้ถ้ายังไม่มี
                if chat_id not in user_warnings:
                    user_warnings[chat_id] = {}

                # เพิ่มจำนวนการเตือน
                if user_id not in user_warnings[chat_id]:
                    user_warnings[chat_id][user_id] = 0

                user_warnings[chat_id][user_id] += 1
                warning_count = user_warnings[chat_id][user_id]

                # ตรวจสอบจำนวนการเตือน
                if warning_count == 1:
                    # ครั้งแรก: เตือน
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=f"⚠️ {username} ห้ามส่งลิงก์ในกลุ่มนี้!\n\n"
                             f"🔴 นี่คือการเตือนครั้งแรก หากส่งลิงก์อีกครั้งจะถูกแบนทันที!"
                    )
                    print(f"เตือนผู้ใช้ {username} ครั้งที่ 1")

                elif warning_count >= 2:
                    # ครั้งที่สอง: แบน
                    await context.bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=f"🔨 {username} ถูกแบนออกจากกลุ่มเนื่องจากส่งลิงก์ซ้ำ!"
                    )
                    print(f"แบนผู้ใช้ {username} (ส่งลิงก์ {warning_count} ครั้ง)")

                    # ลบข้อมูลการเตือนออก
                    del user_warnings[chat_id][user_id]

            except Exception as e:
                print(f"ข้อผิดพลาด: {e}")
                # ถ้าบอทไม่มีสิทธิ์
                if "not enough rights" in str(e).lower():
                    await message.reply_text(
                        "❌ บอทไม่มีสิทธิ์เพียงพอ\n"
                        "กรุณาตั้งค่าให้บอทเป็น Admin และเปิดสิทธิ์:\n"
                        "• Delete Messages\n"
                        "• Ban Users"
                    )

def main():
    """ฟังก์ชันหลักสำหรับรันบอท"""
    print("🤖 กำลังเริ่มบอท Antilink...")

    # สร้าง Application
    application = Application.builder().token(BOT_TOKEN).build()

    # เพิ่ม Command Handlers
    application.add_handler(CommandHandler("start", start_command))

    # เพิ่ม Message Handler สำหรับตรวจสอบข้อความทั้งหมด
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_message))

    # เริ่มรันบอท
    print("✅ บอทเริ่มทำงานแล้ว!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
