import telebot
from telebot import types
import sqlite3

BOT_TOKEN = "9065721978:AAE4bSL77NmG9HJWOkmsWm9pHC_eKzZvjFE"
ADMIN_ID = 8514199623

bot = telebot.TeleBot(BOT_TOKEN)

conn = sqlite3.connect("ddr_system.db", check_same_thread=False)
cursor = conn.cursor()

# Database Tables
cursor.execute('''CREATE TABLE IF NOT EXISTS agents (
    agent_id INTEGER PRIMARY KEY,
    name TEXT,
    phone TEXT,
    balance INTEGER DEFAULT 0,
    credit_limit INTEGER DEFAULT 50000,
    status TEXT DEFAULT 'pending'
)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS packages (
    package_name TEXT PRIMARY KEY,
    price INTEGER
)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS vouchers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    package_name TEXT,
    voucher_code TEXT UNIQUE,
    is_used INTEGER DEFAULT 0,
    used_by INTEGER,
    used_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)''')

default_packages = [
    ("1GB", 400),
    ("2GB", 800),
    ("3GB", 1200),
    ("4GB", 1600),
    ("5GB", 2000),
    ("6GB", 2400),
    ("7GB", 2800),
    ("8GB", 3200),
    ("9GB", 3600),
    ("10GB", 4000)
]
cursor.executemany("INSERT OR IGNORE INTO packages VALUES (?, ?)", default_packages)
conn.commit()

# --- Keyboards ---
def get_admin_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("➕ Voucher ကုဒ်ထည့်ရန်"),
        types.KeyboardButton("🎟 Voucher ကုဒ်ထုတ်ယူရန်"),
        types.KeyboardButton("📦 Voucher လက်ကျန်စစ်ရန်"),
        types.KeyboardButton("📶 Wi-Fi ဈေးနှုန်းများ"),
        types.KeyboardButton("📊 Agent စာရင်းများ"),
        types.KeyboardButton("💳 Agent ငွေဖြည့်ရန်"),
        types.KeyboardButton("❌ Agent ထုတ်ပစ်ရန်"),
        types.KeyboardButton("ℹ️ Admin လမ်းညွှန်")
    )
    return markup

def get_agent_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("🎟 Voucher ဝယ်ယူရန်"),
        types.KeyboardButton("💰 လက်ကျန်ငွေစစ်ရန်"),
        types.KeyboardButton("📋 ဈေးနှုန်းစာရင်းကြည့်ရန်")
    )
    return markup

# --- Start Handler ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    
    if user_id == ADMIN_ID:
        bot.send_message(
            user_id, 
            "👑 **Admin Control Panel** မှ ကြိုဆိုပါသည်။\n\nလိုချင်သော လုပ်ဆောင်ချက်ကို အောက်ပါ Menu ခလုတ်များမှတစ်ဆင့် ရွေးချယ်နိုင်ပါပြီ။", 
            reply_markup=get_admin_keyboard(),
            parse_mode="Markdown"
        )
        return

    cursor.execute("SELECT status, balance FROM agents WHERE agent_id = ?", (user_id,))
    agent = cursor.fetchone()

    if agent and agent[0] == 'approved':
        bot.send_message(
            user_id, 
            f"မင်္ဂလာပါ Reseller Agent ခင်ဗျာ။\n💰 သင့်လက်ကျန်ငွေ: **{agent[1]} MMK**", 
            reply_markup=get_agent_keyboard(),
            parse_mode="Markdown"
        )
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(
            types.KeyboardButton("📝 Agent လျှောက်ထားရန်"),
            types.KeyboardButton("📋 ဈေးနှုန်းစာရင်းကြည့်ရန်")
        )
        bot.send_message(user_id, "DDR Fast Wi-Fi Agent System မှ ကြိုဆိုပါသည်။", reply_markup=markup)

# --- Admin: Agent တစ်ယောက်ချင်းစီ ထုတ်ပစ်ရန် (Delete Agent) ---
@bot.message_handler(func=lambda msg: msg.text == "❌ Agent ထုတ်ပစ်ရန်")
def delete_agent_menu(message):
    if message.chat.id != ADMIN_ID:
        return
    cursor.execute("SELECT agent_id, name FROM agents")
    rows = cursor.fetchall()
    if not rows:
        bot.send_message(message.chat.id, "⚠️ လတ်တလော စနစ်ထဲတွင် ထုတ်ပစ်စရာ Agent မရှိသေးပါ။")
        return

    markup = types.InlineKeyboardMarkup()
    for r in rows:
        btn_text = f"❌ {r[1]} (ID: {r[0]})"
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"delagent_{r[0]}"))

    bot.send_message(
        message.chat.id, 
        "⚠️ **ထုတ်ပစ်လိုသော Agent ကို ရွေးချယ်ပါ -**\n*(နှိပ်လိုက်ပါက စနစ်ထဲမှ အပြီးတိုင် ဖျက်ပစ်မည်ဖြစ်သည်)*", 
        reply_markup=markup, 
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("delagent_"))
def process_delete_agent(call):
    if call.message.chat.id != ADMIN_ID:
        return
    target_id = int(call.data.split("_")[1])
    
    cursor.execute("DELETE FROM agents WHERE agent_id = ?", (target_id,))
    conn.commit()

    bot.edit_message_text(
        f"🗑 **Agent ID `{target_id}` ကို စာရင်းမှ အပြီးတိုင် ထုတ်ပယ်ဖျက်ဆီးပြီးပါပြီ။**", 
        call.message.chat.id, 
        call.message.id, 
        parse_mode="Markdown"
    )
    try:
        bot.send_message(target_id, "⚠️ သင်၏ Reseller Agent အကောင့်ကို Admin မှ စနစ်ထဲမှ ပယ်ဖျက်လိုက်ပါပြီ။")
    except:
        pass

# --- Admin: Code ထုတ်ယူကြည့်ရှုခြင်း ---
@bot.message_handler(func=lambda msg: msg.text == "🎟 Voucher ကုဒ်ထုတ်ယူရန်")
def admin_get_code_menu(message):
    if message.chat.id != ADMIN_ID:
        return
    cursor.execute("SELECT package_name FROM packages")
    packages = cursor.fetchall()
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    for pkg in packages:
        cursor.execute("SELECT COUNT(*) FROM vouchers WHERE package_name = ? AND is_used = 0", (pkg[0],))
        stock = cursor.fetchone()[0]
        buttons.append(types.InlineKeyboardButton(f"{pkg[0]} ({stock} ခုကျန်)", callback_data=f"adminget_{pkg[0]}"))
    markup.add(*buttons)
    
    bot.send_message(message.chat.id, "👑 **Admin အတွက် စမ်းသပ်/ထုတ်ယူလိုသော Package ကို ရွေးပါ:**\n*(ငွေဖြတ်တောက်မှု မရှိဘဲ ကုဒ်တိုက်ရိုက် ထုတ်ပေးမည်ဖြစ်သည်)*", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("adminget_"))
def process_admin_get_code(call):
    if call.message.chat.id != ADMIN_ID:
        return
    pkg_name = call.data.split("_")[1]
    
    cursor.execute("SELECT id, voucher_code FROM vouchers WHERE package_name = ? AND is_used = 0 LIMIT 1", (pkg_name,))
    voucher = cursor.fetchone()
    if not voucher:
        bot.answer_callback_query(call.id, f"{pkg_name} လက်ကျန်ကုဒ် မရှိတော့ပါ။", show_alert=True)
        return

    voucher_id, voucher_code = voucher[0], voucher[1]
    cursor.execute("UPDATE vouchers SET is_used = 1, used_by = ? WHERE id = ?", (ADMIN_ID, voucher_id))
    conn.commit()

    bot.delete_message(chat_id=ADMIN_ID, message_id=call.message.message_id)
    receipt = (
        f"👑 **Admin ထုတ်ယူမှု အောင်မြင်ပါသည်!**\n\n"
        f"📦 Package အမျိုးအစား: `{pkg_name}`\n"
        f"🔑 Voucher Code: `{voucher_code}`\n\n"
        f"*(ဤကုဒ်ကို အသုံးပြုပြီးအဖြစ် မှတ်သားလိုက်ပါပြီ)*"
    )
    bot.send_message(ADMIN_ID, receipt, parse_mode="Markdown")

# --- Admin: Code ထည့်သွင်းခြင်းနှင့် လက်ကျန်စစ်ဆေးခြင်း ---
@bot.message_handler(func=lambda msg: msg.text == "➕ Voucher ကုဒ်ထည့်ရန်")
def add_voucher_guide(message):
    if message.chat.id != ADMIN_ID:
        return
    guide = (
        "📥 **Voucher ကုဒ် ထည့်သွင်းနည်း -**\n\n"
        "စာရိုက်သည့်နေရာတွင် အောက်ပါအတိုင်း အစုလိုက် ရိုက်ပို့နိုင်ပါသည်:\n\n"
        "`/addvoucher [Package_Name] [ကုဒ်၁] [ကုဒ်၂] [ကုဒ်၃]`\n\n"
        "**ဥပမာ -**\n"
        "`/addvoucher 1GB pass01 pass02 pass03`"
    )
    bot.send_message(message.chat.id, guide, parse_mode="Markdown")

@bot.message_handler(commands=['addvoucher'])
def handle_add_voucher(message):
    if message.chat.id != ADMIN_ID:
        return
    try:
        parts = message.text.split()
        if len(parts) < 3:
            bot.reply_to(message, "⚠️ ပုံစံမှားယွင်းနေပါသည်။\nဥပမာ: `/addvoucher 1GB Code1 Code2 Code3`", parse_mode="Markdown")
            return
        
        pkg = parts[1].upper()
        codes = parts[2:]
        inserted_count = 0
        
        for code in codes:
            try:
                cursor.execute("INSERT INTO vouchers (package_name, voucher_code) VALUES (?, ?)", (pkg, code))
                inserted_count += 1
            except sqlite3.IntegrityError:
                pass
        conn.commit()
        bot.reply_to(message, f"✅ `{pkg}` အတွက် Voucher ကုဒ် **({inserted_count})** ခု အောင်မြင်စွာ သိမ်းဆည်းပြီးပါပြီ။", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Error: {str(e)}")

@bot.message_handler(func=lambda msg: msg.text == "📦 Voucher လက်ကျန်စစ်ရန်")
def check_stock(message):
    if message.chat.id != ADMIN_ID:
        return
    cursor.execute("SELECT package_name, COUNT(*) FROM vouchers WHERE is_used = 0 GROUP BY package_name")
    rows = cursor.fetchall()
    if not rows:
        bot.send_message(message.chat.id, "⚠️ စနစ်ထဲတွင် မရောင်းရသေးသော Voucher လက်ကျန် မရှိသေးပါ။")
        return
    text = "📦 **လက်ရှိ Voucher ကုဒ်လက်ကျန်များ -**\n\n"
    for r in rows:
        text += f"🔹 `{r[0]}` = **{r[1]}** စောင် ကျန်ရှိ\n"
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

# --- Agent ဘက်မှ ဝယ်ယူခြင်း ---
@bot.message_handler(func=lambda msg: msg.text == "🎟 Voucher ဝယ်ယူရန်")
def agent_buy_prompt(message):
    user_id = message.chat.id
    cursor.execute("SELECT status, balance FROM agents WHERE agent_id = ?", (user_id,))
    agent = cursor.fetchone()
    if not agent or agent[0] != 'approved':
        bot.send_message(user_id, "⚠️ Reseller Agent များသာ ဝယ်ယူခွင့် ရှိပါသည်။")
        return

    cursor.execute("SELECT package_name, price FROM packages")
    packages = cursor.fetchall()
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    for pkg in packages:
        cursor.execute("SELECT COUNT(*) FROM vouchers WHERE package_name = ? AND is_used = 0", (pkg[0],))
        stock = cursor.fetchone()[0]
        btn_text = f"{pkg[0]} ({pkg[1]} Ks) [{stock} ခုကျန်]"
        buttons.append(types.InlineKeyboardButton(btn_text, callback_data=f"buy_{pkg[0]}"))
    markup.add(*buttons)
    
    bot.send_message(user_id, "🎟 **ဝယ်ယူလိုသော Package ကို ရွေးချယ်ပါ -**", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def process_voucher_purchase(call):
    user_id = call.message.chat.id
    pkg_name = call.data.split("_")[1]
    
    cursor.execute("SELECT balance, status FROM agents WHERE agent_id = ?", (user_id,))
    agent = cursor.fetchone()
    if not agent or agent[1] != 'approved':
        bot.answer_callback_query(call.id, "ခွင့်ပြုချက် မရှိသေးပါ။", show_alert=True)
        return
    
    balance = agent[0]
    cursor.execute("SELECT price FROM packages WHERE package_name = ?", (pkg_name,))
    pkg_row = cursor.fetchone()
    if not pkg_row:
        bot.answer_callback_query(call.id, "Package ရှာမတွေ့ပါ။", show_alert=True)
        return
    price = pkg_row[0]

    cursor.execute("SELECT id, voucher_code FROM vouchers WHERE package_name = ? AND is_used = 0 LIMIT 1", (pkg_name,))
    voucher = cursor.fetchone()
    if not voucher:
        bot.answer_callback_query(call.id, f"{pkg_name} လက်ကျန်ပြတ်နေပါသည်။", show_alert=True)
        return

    if balance < price:
        bot.answer_callback_query(call.id, f"လက်ကျန်ငွေ မလုံလောက်ပါ။ (လက်ကျန်: {balance} MMK)", show_alert=True)
        return

    voucher_id, voucher_code = voucher[0], voucher[1]
    new_balance = balance - price
    cursor.execute("UPDATE agents SET balance = ? WHERE agent_id = ?", (new_balance, user_id))
    cursor.execute("UPDATE vouchers SET is_used = 1, used_by = ? WHERE id = ?", (user_id, voucher_id))
    conn.commit()

    bot.delete_message(chat_id=user_id, message_id=call.message.message_id)
    receipt = (
        f"🎉 **Voucher ဝယ်ယူမှု အောင်မြင်ပါသည်!**\n\n"
        f"📦 အမျိုးအစား: `{pkg_name}`\n"
        f"🔑 Voucher Code: `{voucher_code}`\n"
        f"💰 ကျသင့်ငွေ: {price} MMK\n"
        f"💳 လက်ကျန်ငွေ: {new_balance} MMK\n\n"
        f"⚠️ ကုဒ်ကို ဖိနှိပ်၍ Copy ယူ အသုံးပြုနိုင်ပါပြီ။"
    )
    bot.send_message(user_id, receipt, parse_mode="Markdown")

# --- အထွေထွေ Admin & Agent Handlers ---
@bot.message_handler(func=lambda msg: msg.text == "💰 လက်ကျန်ငွေစစ်ရန်")
def check_agent_balance(message):
    cursor.execute("SELECT balance FROM agents WHERE agent_id = ?", (message.chat.id,))
    res = cursor.fetchone()
    if res:
        bot.send_message(message.chat.id, f"💰 သင့်လက်ကျန်ငွေ: **{res[0]} MMK**", parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, "စာရင်းမရှိသေးပါ။")

@bot.message_handler(func=lambda msg: msg.text in ["📶 Wi-Fi ဈေးနှုန်းများ", "📋 ဈေးနှုန်းစာရင်းကြည့်ရန်"])
def show_pricing(message):
    cursor.execute("SELECT package_name, price FROM packages")
    rows = cursor.fetchall()
    text = "📶 **Wi-Fi Package ဈေးနှုန်းများ -**\n\n"
    for row in rows:
        text += f"🔹 `{row[0]}` = **{row[1]} MMK**\n"
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text == "📊 Agent စာရင်းများ")
def view_agents(message):
    if message.chat.id != ADMIN_ID:
        return
    cursor.execute("SELECT agent_id, name, status, balance FROM agents")
    rows = cursor.fetchall()
    if not rows:
        bot.send_message(message.chat.id, "လတ်တလော စာရင်းသွင်းထားသော Agent မရှိသေးပါ။")
        return
    text = "📋 **လက်ရှိ စာရင်းဝင် Agent များ -**\n\n"
    for r in rows:
        status_icon = "✅" if r[2] == "approved" else "⏳"
        text += f"👤 **ID:** `{r[0]}`\n📝 **အမည်:** {r[1]}\n📊 **အခြေအနေ:** {status_icon} {r[2]}\n💰 **လက်ကျန် Balance:** {r[3]} MMK\n─────────────────\n"
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text == "💳 Agent ငွေဖြည့်ရန်")
def add_balance_prompt(message):
    if message.chat.id != ADMIN_ID:
        return
    bot.send_message(
        message.chat.id, 
        "💳 **Agent ထံ ငွေဖြည့်ပေးရန် ပုံစံ -**\n\n`/addbalance [Agent_ID] [ငွေပမာဏ]`\n\nဥပမာ: `/addbalance 123456789 50000`",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['addbalance'])
def add_balance(message):
    if message.chat.id != ADMIN_ID:
        return
    try:
        parts = message.text.split()
        target_id = int(parts[1])
        amount = int(parts[2])
        cursor.execute("UPDATE agents SET balance = balance + ? WHERE agent_id = ?", (amount, target_id))
        conn.commit()
        bot.reply_to(message, f"✅ Agent ID `{target_id}` ထံသို့ ငွေ **{amount} MMK** ဖြည့်သွင်းပေးပြီးပါပြီ။", parse_mode="Markdown")
        try:
            bot.send_message(target_id, f"🎉 Admin မှ သင့်အကောင့်သို့ ငွေ **{amount} MMK** ဖြည့်သွင်းပေးလိုက်ပါပြီ။")
        except:
            pass
    except Exception:
        bot.reply_to(message, "⚠️ ပုံစံမှားယွင်းနေပါသည်။\nဥပမာ - `/addbalance 123456789 50000` ဟု ရိုက်ပို့ပါ။")

@bot.message_handler(func=lambda msg: msg.text == "ℹ️ Admin လမ်းညွှန်")
def admin_help(message):
    if message.chat.id != ADMIN_ID:
        return
    help_text = (
        "⚙️ **Admin အသုံးပြုနိုင်သော Commands များ:**\n\n"
        "1. `/addvoucher [Package] [Codes...]`\n   - Voucher ကုဒ်များ သွင်းရန်\n"
        "2. `/addbalance [Agent_ID] [ငွေ]`\n   - Agent ထံ လက်ကျန်ငွေဖြည့်ရန်\n"
        "3. `/setprice [Package] [ဈေး]`\n   - Package ဈေးနှုန်း ပြင်ရန်\n"
        "4. `/delagent [Agent_ID]`\n   - ID ဖြင့် Agent ကို တိုက်ရိုက်ဖျက်ပစ်ရန်\n"
    )
    bot.send_message(message.chat.id, help_text, parse_mode="Markdown")

@bot.message_handler(commands=['delagent'])
def direct_delete_agent(message):
    if message.chat.id != ADMIN_ID:
        return
    try:
        target_id = int(message.text.split()[1])
        cursor.execute("DELETE FROM agents WHERE agent_id = ?", (target_id,))
        conn.commit()
        bot.reply_to(message, f"🗑 Agent ID `{target_id}` ကို စာရင်းမှ ဖျက်ပစ်ပြီးပါပြီ။", parse_mode="Markdown")
    except:
        bot.reply_to(message, "⚠️ ပုံစံ: `/delagent 123456789`")

@bot.message_handler(func=lambda msg: msg.text == "📝 Agent လျှောက်ထားရန်")
def register_prompt(message):
    bot.send_message(message.chat.id, "Agent အဖြစ် လျှောက်ထားရန် သင်၏ အမည်နှင့် ဖုန်းနံပါတ်ကို ပေးပို့ပါ -\n\nဥပမာ: `Agent Ko Soe - 09123456789`")

@bot.message_handler(func=lambda msg: msg.text and msg.text.startswith("Agent "))
def handle_agent_registration(message):
    user_id = message.chat.id
    details = message.text.replace("Agent ", "").strip()
    cursor.execute("INSERT OR REPLACE INTO agents (agent_id, name, phone, status) VALUES (?, ?, ?, 'pending')", 
                   (user_id, details, details))
    conn.commit()

    bot.reply_to(message, "✅ Agent လျှောက်ထားလွှာ ပေးပို့ပြီးပါပြီ။ Admin ဘက်မှ အတည်ပြုပြီးပါက အကြောင်းကြားပေးပါမည်။")

    admin_markup = types.InlineKeyboardMarkup()
    approve_btn = types.InlineKeyboardButton("အတည်ပြုမည်", callback_data=f"approve_{user_id}")
    admin_markup.add(approve_btn)
    bot.send_message(ADMIN_ID, f"🔔 Agent အသစ် လျှောက်ထားလာပါသည် -\nID: `{user_id}`\nအချက်အလက်: {details}", reply_markup=admin_markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_"))
def approve_agent(call):
    if call.message.chat.id != ADMIN_ID:
        return
    agent_id = int(call.data.split("_")[1])
    cursor.execute("UPDATE agents SET status = 'approved' WHERE agent_id = ?", (agent_id,))
    conn.commit()

    bot.send_message(agent_id, "🎉 သင်၏ Reseller Agent အကောင့်ကို Admin မှ အတည်ပြုလိုက်ပါပြီ။ /start ကို ပြန်နှိပ်၍ စတင်သုံးနိုင်ပါပြီ။")
    bot.edit_message_text(f"✅ Agent ID {agent_id} ကို အတည်ပြုပြီးပါပြီ။", call.message.chat.id, call.message.id)

print("DDR Fast WiFi Bot is running...")
bot.infinity_polling()
