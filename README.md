# 🤖 Antilink Telegram Bot

บอทสำหรับลบข้อความที่มีลิงก์ในกลุ่ม Telegram อัตโนมัติ

## ✨ ฟีเจอร์

- ✅ ตรวจจับและลบลิงก์อัตโนมัติ (http://, https://, www., t.me/)
- ✅ ส่งข้อความเตือนผู้ใช้
- ✅ รองรับกลุ่มและซูเปอร์กรุ๊ป
- ✅ ใช้งานง่าย

## 📋 ข้อกำหนด

- Python 3.8 ขึ้นไป
- pip (Python package manager)

## 🚀 วิธีติดตั้ง

### 1. ติดตั้ง Dependencies

```bash
pip install -r requirements.txt
```

หรือติดตั้งแบบแยก:

```bash
pip install python-telegram-bot python-dotenv
```

### 2. ตั้งค่า Bot Token

ไฟล์ `.env` มี Bot Token อยู่แล้ว:

```
BOT_TOKEN=8058056389:AAEhCW2ZDxaV-3OqJDG3nIyTqsFzrZiWhyk
```

## ▶️ วิธีรันบอท

```bash
python bot.py
```

## 📱 วิธีใช้งาน

### เพิ่มบอทเข้ากลุ่ม

1. เปิด Telegram และค้นหาบอท: `@antilink_okka_bot`
2. เพิ่มบอทเข้ากลุ่มที่ต้องการ
3. ตั้งค่าให้บอทเป็น **Administrator**

### ตั้งค่าสิทธิ์ Admin

บอทต้องมีสิทธิ์นี้เพื่อทำงาน:

- ✅ **Delete Messages** - สำหรับลบข้อความที่มีลิงก์

สิทธิ์อื่นๆ สามารถปิดได้หมด

### ทดสอบบอท

ส่งคำสั่ง `/start` ในกลุ่มเพื่อดูว่าบอททำงานหรือไม่

## 🔧 โครงสร้างโปรเจ็กต์

```
Antilink Telegram/
│
├── bot.py              # ไฟล์หลักของบอท
├── .env                # เก็บ Bot Token
├── requirements.txt    # Python dependencies
├── .gitignore         # ไฟล์ที่ไม่ต้อง commit
└── README.md          # เอกสารนี้
```

## 💡 การทำงานของบอท

1. บอทจะตรวจสอบทุกข้อความในกลุ่ม
2. หากพบลิงก์ในข้อความ:
   - ลบข้อความนั้นทันที
   - ส่งข้อความเตือนผู้ส่ง
3. หากบอทไม่มีสิทธิ์ จะแจ้งเตือนให้ตั้งค่า Admin

## ⚠️ หมายเหตุ

- บอทต้องเป็น Admin และมีสิทธิ์ Delete Messages เท่านั้น
- ลิงก์ที่ตรวจจับได้: http://, https://, www., t.me/
- เก็บ Bot Token ให้ปลอดภัย อย่าแชร์ให้ใครรู้

## 🛠️ Troubleshooting

### บอทไม่ลบข้อความ

- ตรวจสอบว่าบอทเป็น Admin หรือไม่
- ตรวจสอบว่าเปิดสิทธิ์ "Delete Messages" หรือไม่

### บอทไม่ตอบสนอง

- ตรวจสอบว่ารันโปรแกรม `python bot.py` อยู่หรือไม่
- ตรวจสอบ Bot Token ในไฟล์ `.env`
- ตรวจสอบ internet connection

## 📞 การติดต่อ

Bot: [@antilink_okka_bot](https://t.me/antilink_okka_bot)

---

🤖 สร้างด้วย Python & python-telegram-bot
