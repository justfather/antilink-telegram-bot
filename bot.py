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
    r'|tg://[^\s]+'
    r'|@[a-zA-Z0-9_]{5,}'
    r'|[a-zA-Z0-9-]+\.(com|net|org|io|me|co|xyz|info|biz|link|click|site|online|top|pro|vip)'
    r'|[a-zA-Z0-9]+\s*\.\s*[a-zA-Z]{2,}'
)

# เก็บข้อมูลการเตือนของผู้ใช้ {chat_id: {user_id: warning_count}}
user_warnings = {}

# เก็บข้อมูล forward spam {chat_id: {user_id: [timestamps]}}
forward_tracker = {}

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
    if update.message:
        message = update.message
        user = message.from_user
        chat_id = message.chat_id
        user_id = user.id

        # ตรวจสอบว่าเป็น Admin หรือไม่ (ยกเว้น admin ทันที)
        if await is_user_admin(update, context, user_id):
            return

        # รวบรวมข้อความที่ต้องตรวจสอบ
        text_to_check = []

        # ตรวจสอบข้อความธรรมดา
        if message.text:
            text_to_check.append(message.text)

        # ตรวจสอบ caption ของรูปภาพ/วิดีโอ/เอกสาร
        if message.caption:
            text_to_check.append(message.caption)

        # ตรวจสอบ inline buttons
        if message.reply_markup and message.reply_markup.inline_keyboard:
            for row in message.reply_markup.inline_keyboard:
                for button in row:
                    if button.url:
                        text_to_check.append(button.url)

        # ตรวจสอบ URL entities (ลิงก์ที่ซ่อนอยู่ใน text)
        if message.entities:
            for entity in message.entities:
                if entity.type in ['url', 'text_link']:
                    if entity.type == 'text_link' and entity.url:
                        text_to_check.append(entity.url)

        # ตรวจสอบ caption entities
        if message.caption_entities:
            for entity in message.caption_entities:
                if entity.type in ['url', 'text_link']:
                    if entity.type == 'text_link' and entity.url:
                        text_to_check.append(entity.url)

        # ตรวจสอบว่ามีลิงก์หรือไม่
        has_link = any(LINK_PATTERN.search(text) for text in text_to_check if text)

        # ตรวจสอบ forward message (รองรับทั้ง v20 และ v21+)
        is_forwarded = (
            hasattr(message, 'forward_origin') and message.forward_origin is not None  # v21+
        ) or (
            hasattr(message, 'forward_date') and message.forward_date is not None  # v20
        )
        is_forwarded_with_link = is_forwarded and has_link

        # ตรวจสอบ Forward Spam Flooding
        if is_forwarded:
            import time
            current_time = time.time()

            # สร้าง dictionary สำหรับกลุ่มนี้ถ้ายังไม่มี
            if chat_id not in forward_tracker:
                forward_tracker[chat_id] = {}
            if user_id not in forward_tracker[chat_id]:
                forward_tracker[chat_id][user_id] = []

            # เพิ่ม timestamp
            forward_tracker[chat_id][user_id].append(current_time)

            # ลบ timestamp เก่าที่เกิน 30 วินาที
            forward_tracker[chat_id][user_id] = [
                t for t in forward_tracker[chat_id][user_id]
                if current_time - t <= 30
            ]

            # นับจำนวน forward ใน 30 วินาที
            forward_count = len(forward_tracker[chat_id][user_id])

            # ถ้า forward มากกว่า 3 ครั้งใน 30 วินาที = spam flooding
            if forward_count >= 3:
                try:
                    await message.delete()
                    await context.bot.ban_chat_member(chat_id=chat_id, user_id=user_id)

                    username = f"@{user.username}" if user.username else user.first_name
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=f"🔨 {username} ถูกแบนอัตโนมัติเนื่องจาก Forward Spam Flooding!\n\n"
                             f"⚠️ ตรวจพบการ forward ข้อความ {forward_count} ครั้งภายใน 30 วินาที"
                    )
                    print(f"แบน {username} เนื่องจาก forward spam ({forward_count} ครั้ง)")

                    # ลบข้อมูล tracker
                    del forward_tracker[chat_id][user_id]
                    return
                except Exception as e:
                    print(f"ข้อผิดพลาดในการแบน forward spammer: {e}")

        if has_link:

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
                    warning_reason = "ส่งลิงก์/forward message" if is_forwarded_with_link else "ส่งลิงก์"
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=f"⚠️ {username} ห้าม{warning_reason}ในกลุ่มนี้!\n\n"
                             f"🔴 นี่คือการเตือนครั้งแรก หากฝ่าฝืนอีกครั้งจะถูกแบนทันที!"
                    )
                    print(f"เตือนผู้ใช้ {username} ครั้งที่ 1 ({warning_reason})")

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

    # เพิ่ม Message Handler สำหรับตรวจสอบข้อความทั้งหมด (รวมรูปภาพ/วิดีโอ/เอกสาร)
    application.add_handler(MessageHandler(
        (filters.TEXT | filters.PHOTO | filters.VIDEO | filters.Document.ALL | filters.ANIMATION) & ~filters.COMMAND,
        check_message
    ))

    # เริ่มรันบอท
    print("✅ บอทเริ่มทำงานแล้ว!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
