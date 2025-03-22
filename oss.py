import os
import json
import logging
import datetime
import random
import telebot
from telebot.apihelper import ApiException

TOKEN = '8182642876:AAFzCS1k985u0KQ2V0gsM6z9jYH7TkpApvE'
CHANNEL_USERNAME = "@King_1_elehteraf"

bot = telebot.TeleBot(TOKEN)

USERS_FILE = 'users.json'
REWARD_CODES_FILE = 'reward_codes.json'
IMPORTED_CODES_FILE = 'imported_codes.json'
LOG_FILE = 'log.txt'
ADMINS = ['5869877607', '6978558238']

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename=LOG_FILE, filemode='a')

def init_files():
    for file in [USERS_FILE, REWARD_CODES_FILE, IMPORTED_CODES_FILE]:
        if not os.path.exists(file):
            with open(file, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=4)
init_files()

def log_action(action):
    entry = f"{datetime.datetime.now()} - {action}"
    logging.info(entry)

def read_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        log_action(f"Error reading {file_path}: {e}")
        return {}

def write_json(file_path, data):
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        log_action(f"Error writing {file_path}: {e}")

def read_users():
    return read_json(USERS_FILE)
def write_users(data):
    write_json(USERS_FILE, data)
def read_reward_codes():
    return read_json(REWARD_CODES_FILE)
def write_reward_codes(data):
    write_json(REWARD_CODES_FILE, data)
def read_imported_codes():
    return read_json(IMPORTED_CODES_FILE)
def write_imported_codes(data):
    write_json(IMPORTED_CODES_FILE, data)

def is_user_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['creator', 'administrator', 'member']
    except ApiException as e:
        log_action(f"Error checking subscription for {user_id}: {e}")
        return False

def get_or_create_invite_link(user_id, users):
    if users[user_id].get("invite_link"):
        return users[user_id]["invite_link"]
    try:
        invite_link_obj = bot.create_chat_invite_link(chat_id=CHANNEL_USERNAME, name=f"{user_id}", expire_date=None, member_limit=0)
        link = invite_link_obj.invite_link
        users[user_id]["invite_link"] = link
        users[user_id]["invite_usage"] = 0
        write_users(users)
        log_action(f"Created invite link for {user_id}: {link}")
        return link
    except Exception as e:
        log_action(f"Error creating invite link for {user_id}: {e}")
        return None

def delete_previous_message(chat_id, message_id, preserve=False):
    if not preserve:
        try:
            bot.delete_message(chat_id, message_id)
        except Exception as e:
            log_action(f"Error deleting message: {e}")

def show_main_menu(chat_id, user_id):
    users = read_users()
    user = users.get(user_id, {"points":0, "invite_usage":0, "referrals":0, "invite_link": "لم يتم إنشاؤه"})
    try:
        user_info = bot.get_chat(user_id)
        first_name = user_info.first_name if user_info.first_name else "المستخدم"
        username = f"@{user_info.username}" if user_info.username else "غير معروف"
    except Exception as e:
        log_action(f"Error fetching user info for {user_id}: {e}")
        first_name = "المستخدم"
        username = "غير معروف"
    welcome_text = (
        "🌟 مرحباً بك في البوت! 🌟\n\n"
        f"🆔 معرفك: {user_id}\n"
        f"👤 اسمك: {first_name} ({username})\n\n"
        "💎 يمكنك كسب النقاط عن طريق الدعوات والمكافآت اليومية واستبدال النقاط لاشتراكات VIP.\n"
        "🔗 كل رابط دعوة يكون فريدًا ومخصصًا لك ويتم تتبعه بدقة.\n\n"
        "📝 الأوامر:\n"
        "/help - تعليمات الاستخدام\n"
        "/profile - عرض ملفك الشخصي\n"
        "/reward - استخدام كود المكافأة\n"
        "🏆 قائمة المتصدرين"
    )
    markup = telebot.types.InlineKeyboardMarkup()
    btn_profile = telebot.types.InlineKeyboardButton("👤 ملفي الشخصي", callback_data="profile")
    btn_earn = telebot.types.InlineKeyboardButton("💰 كسب النقاط", callback_data="earn_points")
    btn_daily = telebot.types.InlineKeyboardButton("⏰ النقاط اليومية", callback_data="daily_points")
    btn_redeem = telebot.types.InlineKeyboardButton("🎁 استبدال النقاط", callback_data="redeem_points")
    btn_import = telebot.types.InlineKeyboardButton("🔑 استيراد مكافأة", callback_data="import_reward")
    btn_top = telebot.types.InlineKeyboardButton("🏆 المتصدرين", callback_data="top_scorers")
    markup.row(btn_profile)
    markup.row(btn_earn, btn_daily)
    markup.row(btn_redeem, btn_import)
    markup.row(btn_top)
    if user_id in ADMINS:
        btn_admin = telebot.types.InlineKeyboardButton("🛡️ لوحة الأدمن", callback_data="admin_panel")
        markup.row(btn_admin)
    # زر start أسفل يسار الشاشة يمكن عرضه كأمر ثابت (يمكن استخدام الأمر /start أيضاً)
    bot.send_message(chat_id, welcome_text, reply_markup=markup)

@bot.message_handler(commands=['start'])
def start_handler(message):
    user_id = str(message.from_user.id)
    if user_id not in ADMINS:
        if not is_user_subscribed(user_id):
            markup = telebot.types.InlineKeyboardMarkup()
            btn_join = telebot.types.InlineKeyboardButton("🚀 اشترك الآن", url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}")
            markup.add(btn_join)
            bot.send_message(message.chat.id, "يرجى الاشتراك في القناة أولاً لاستكمال التسجيل:", reply_markup=markup)
            return
    users = read_users()
    if user_id not in users:
        users[user_id] = {"user_id": user_id, "points": 0, "referrals": 0, "referred_by": None, "invite_link": None, "invite_usage": 0, "last_daily": None}
        write_users(users)
        log_action(f"Registered new user: {user_id}")
    show_main_menu(message.chat.id, user_id)

@bot.message_handler(commands=['help'])
def help_handler(message):
    help_text = (
        "📝 تعليمات استخدام البوت:\n\n"
        "1. /start - بدء التسجيل والتحقق من الاشتراك في القناة.\n"
        "2. /profile - عرض ملفك الشخصي (النقاط، الدعوات، رابط الدعوة).\n"
        "3. /reward - استخدام كود المكافأة لزيادة النقاط.\n\n"
        "استخدم الأزرار المدمجة للتفاعل مع البوت."
    )
    bot.send_message(message.chat.id, help_text)

@bot.message_handler(commands=['profile'])
def profile_handler(message):
    user_id = str(message.from_user.id)
    users = read_users()
    if user_id not in users:
        bot.send_message(message.chat.id, "الملف غير موجود، استخدم /start للتسجيل.")
        return
    user = users[user_id]
    profile_text = (
        f"👤 ملفك الشخصي:\n"
        f"🆔 المعرف: {user_id}\n"
        f"⭐ النقاط: {user['points']}\n"
        f"👥 المستخدمين المنضمين: {user.get('invite_usage', 0)}\n"
        f"📈 الإحالات: {user['referrals']}\n"
        f"🔗 رابط الدعوة: {user.get('invite_link', 'لم يتم إنشاؤه')}"
    )
    bot.send_message(message.chat.id, profile_text)

@bot.message_handler(commands=['reward'])
def reward_command_handler(message):
    msg = bot.send_message(message.chat.id, "🔑 أدخل كود المكافأة:")
    bot.register_next_step_handler(msg, process_reward_code)

def process_reward_code(message):
    try:
        code = message.text.strip()
        reward_codes = read_reward_codes()
        imported_codes = read_imported_codes()
        user_id = str(message.from_user.id)
        if code in imported_codes:
            bot.send_message(message.chat.id, "⚠️ تم استخدام هذا الكود مسبقاً.")
            return
        if code in reward_codes:
            users = read_users()
            points = reward_codes[code]
            users[user_id]["points"] += points
            write_users(users)
            imported_codes[code] = user_id
            write_imported_codes(imported_codes)
            log_action(f"User {user_id} redeemed code {code} for {points} points")
            bot.send_message(message.chat.id, f"✅ تم إضافة {points} نقطة إلى حسابك.")
        else:
            bot.send_message(message.chat.id, "⚠️ كود غير صالح.")
    except Exception as e:
        log_action(f"Error in process_reward_code: {e}")

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    try:
        admin_commands = {"admin_panel", "set_channel_subscription", "create_reward_code", "modify_points", "delete_reward_code", "view_stats", "manage_users", "delete_user", "reset_user", "top_scorers"}
        user_id = str(call.from_user.id)
        users = read_users()
        if call.data == "profile":
            if user_id not in users:
                bot.answer_callback_query(call.id, "⚠️ الملف غير موجود، استخدم /start.")
                return
            user = users[user_id]
            profile_text = (
                f"👤 ملفك الشخصي:\n"
                f"🆔 المعرف: {user_id}\n"
                f"⭐ النقاط: {user['points']}\n"
                f"👥 المستخدمين المنضمين: {user.get('invite_usage', 0)}\n"
                f"📈 الإحالات: {user['referrals']}\n"
                f"🔗 رابط الدعوة: {user.get('invite_link', 'لم يتم إنشاؤه')}"
            )
            bot.send_message(call.message.chat.id, profile_text)
            bot.answer_callback_query(call.id, "✅ الملف تم عرضه")
        elif call.data == "earn_points":
            text = (
                "💰 تفاصيل كسب النقاط:\n"
                "📢 إحالة القناة = 150 نقطة\n"
                "🔔 إحالة الاشتراك = 2500 نقطة\n"
                "🏢 الوكالة (بدون إيداع) = 1000 نقطة"
            )
            markup = telebot.types.InlineKeyboardMarkup()
            btn_referral = telebot.types.InlineKeyboardButton("🔗 زر الإحالة", callback_data="referral_invite")
            btn_agency = telebot.types.InlineKeyboardButton("🏢 زر الوكالة", callback_data="agency")
            markup.row(btn_referral, btn_agency)
            bot.send_message(call.message.chat.id, text, reply_markup=markup)
            bot.answer_callback_query(call.id, "✅ اختر العملية المناسبة")
            if call.data not in admin_commands:
                delete_previous_message(call.message.chat.id, call.message.message_id)
        elif call.data == "referral_invite":
            try:
                link = get_or_create_invite_link(user_id, users)
                if link:
                    bot.answer_callback_query(call.id, "✅ الرابط تم عرضه")
                    bot.send_message(call.message.chat.id, f"🔗 رابط الدعوة:\n{link}")
                else:
                    bot.answer_callback_query(call.id, "⚠️ حدث خطأ في الرابط")
                if call.data not in admin_commands:
                    delete_previous_message(call.message.chat.id, call.message.message_id)
            except Exception as e:
                bot.answer_callback_query(call.id, "⚠️ خطأ أثناء معالجة الرابط")
                log_action(f"Error in referral_invite for {user_id}: {e}")
        elif call.data == "agency":
            bot.send_message(call.message.chat.id, "📞 تواصل مع @Server_Customer_service")
            bot.answer_callback_query(call.id, "🏢 تواصل مع الخدمة")
            if call.data not in admin_commands:
                delete_previous_message(call.message.chat.id, call.message.message_id)
        elif call.data == "daily_points":
            now = datetime.datetime.now()
            last_daily = users[user_id].get("last_daily")
            if last_daily:
                last_daily_dt = datetime.datetime.strptime(last_daily, "%Y-%m-%d %H:%M:%S")
                if (now - last_daily_dt).total_seconds() < 24 * 3600:
                    bot.answer_callback_query(call.id, "⏰ المكافأة اليومية مستلمة، انتظر 24 ساعة.")
                    return
            daily_points = random.randint(20, 100)
            users[user_id]["points"] += daily_points
            users[user_id]["last_daily"] = now.strftime("%Y-%m-%d %H:%M:%S")
            write_users(users)
            log_action(f"Granted {daily_points} daily points to {user_id}")
            bot.answer_callback_query(call.id, f"⏰ تم منحك {daily_points} نقطة يومية!")
            if call.data not in admin_commands:
                delete_previous_message(call.message.chat.id, call.message.message_id)
        elif call.data == "redeem_points":
            details = (
                "🎁 استبدال النقاط:\n"
                "5000 نقطة = اشتراك أسبوعي VIP\n"
                "10000 نقطة = اشتراك نصف شهر VIP\n"
                "15000 نقطة = شهر مجاني VIP"
            )
            bot.send_message(call.message.chat.id, details)
            if users[user_id]["points"] >= 5000:
                bot.send_message(call.message.chat.id, "📞 تواصل مع المشرف لاستبدال النقاط @Kareem8008")
            else:
                bot.send_message(call.message.chat.id, "⚠️ نقاطك أقل من المطلوب للاستبدال (5000 نقطة).")
            bot.answer_callback_query(call.id, "✅ التفاصيل تم عرضها")
            if call.data not in admin_commands:
                delete_previous_message(call.message.chat.id, call.message.message_id)
        elif call.data == "import_reward":
            msg = bot.send_message(call.message.chat.id, "🔑 أدخل كود المكافأة:")
            bot.register_next_step_handler(msg, process_reward_code)
            if call.data not in admin_commands:
                delete_previous_message(call.message.chat.id, call.message.message_id)
        elif call.data == "top_scorers":
            users_data = read_users()
            sorted_users = sorted(users_data.values(), key=lambda x: x.get("points", 0), reverse=True)
            top_10 = sorted_users[:10]
            scoreboard = "🏆 المتصدرين:\n"
            medals = ["🥇", "🥈", "🥉"] + ["🎖️"] * 7
            for idx, user in enumerate(top_10, start=1):
                scoreboard += f"{medals[idx-1]} {idx}. معرف: {user['user_id']} - نقاط: {user['points']}\n"
            bot.send_message(call.message.chat.id, scoreboard)
            bot.answer_callback_query(call.id, "🏆 المتصدرين")
            if call.data not in admin_commands:
                delete_previous_message(call.message.chat.id, call.message.message_id)
        elif call.data == "admin_panel":
            if user_id in ADMINS:
                markup = telebot.types.InlineKeyboardMarkup()
                btn_create_code = telebot.types.InlineKeyboardButton("✨ صنع كود", callback_data="create_reward_code")
                btn_modify_points = telebot.types.InlineKeyboardButton("✏️ تعديل نقاط", callback_data="modify_points")
                btn_delete_code = telebot.types.InlineKeyboardButton("🗑️ حذف كود", callback_data="delete_reward_code")
                btn_view_stats = telebot.types.InlineKeyboardButton("📊 إحصائيات", callback_data="view_stats")
                btn_manage_users = telebot.types.InlineKeyboardButton("👥 إدارة المستخدمين", callback_data="manage_users")
                btn_set_subscription = telebot.types.InlineKeyboardButton("📢 إعداد اشتراك", callback_data="set_channel_subscription")
                btn_top_scorers = telebot.types.InlineKeyboardButton("🏆 المتصدرين", callback_data="top_scorers")
                btn_back = telebot.types.InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")
                markup.row(btn_create_code, btn_modify_points)
                markup.row(btn_delete_code, btn_view_stats)
                markup.row(btn_manage_users, btn_set_subscription)
                markup.row(btn_top_scorers, btn_back)
                bot.send_message(call.message.chat.id, "🛡️ لوحة الأدمن:", reply_markup=markup)
            else:
                bot.answer_callback_query(call.id, "⚠️ ليس لديك صلاحية للوصول إلى لوحة الأدمن.")
        elif call.data == "set_channel_subscription":
            msg = bot.send_message(call.message.chat.id, "📢 أدخل رابط القناة الجديد:")
            bot.register_next_step_handler(msg, process_set_channel_subscription)
            if call.data not in admin_commands:
                delete_previous_message(call.message.chat.id, call.message.message_id)
        elif call.data == "create_reward_code":
            msg = bot.send_message(call.message.chat.id, "✨ أدخل الكود وقيمته (مثال: ABC123 500):")
            bot.register_next_step_handler(msg, process_create_reward_code)
            if call.data not in admin_commands:
                delete_previous_message(call.message.chat.id, call.message.message_id)
        elif call.data == "modify_points":
            msg = bot.send_message(call.message.chat.id, "✏️ أدخل معرف المستخدم والنقاط (مثال: 987654321 3000):")
            bot.register_next_step_handler(msg, process_modify_points)
            if call.data not in admin_commands:
                delete_previous_message(call.message.chat.id, call.message.message_id)
        elif call.data == "delete_reward_code":
            msg = bot.send_message(call.message.chat.id, "🗑️ أدخل كود المكافأة الذي تريد حذفه:")
            bot.register_next_step_handler(msg, process_delete_reward_code)
            if call.data not in admin_commands:
                delete_previous_message(call.message.chat.id, call.message.message_id)
        elif call.data == "view_stats":
            total_users = len(users)
            total_points = sum(user["points"] for user in users.values())
            bot.send_message(call.message.chat.id, f"📊 إحصائيات:\nعدد المستخدمين: {total_users}\nإجمالي النقاط: {total_points}")
            if call.data not in admin_commands:
                delete_previous_message(call.message.chat.id, call.message.message_id)
        elif call.data == "manage_users":
            markup = telebot.types.InlineKeyboardMarkup()
            btn_delete_user = telebot.types.InlineKeyboardButton("❌ حذف مستخدم", callback_data="delete_user")
            btn_reset_user = telebot.types.InlineKeyboardButton("🔄 إعادة تعيين", callback_data="reset_user")
            markup.row(btn_delete_user, btn_reset_user)
            bot.send_message(call.message.chat.id, "👥 إدارة المستخدمين:", reply_markup=markup)
            if call.data not in admin_commands:
                delete_previous_message(call.message.chat.id, call.message.message_id)
        elif call.data == "delete_user":
            msg = bot.send_message(call.message.chat.id, "❌ أدخل معرف المستخدم الذي تريد حذفه:")
            bot.register_next_step_handler(msg, process_delete_user)
            if call.data not in admin_commands:
                delete_previous_message(call.message.chat.id, call.message.message_id)
        elif call.data == "reset_user":
            msg = bot.send_message(call.message.chat.id, "🔄 أدخل معرف المستخدم لإعادة تعيين نقاطه:")
            bot.register_next_step_handler(msg, process_reset_user)
            if call.data not in admin_commands:
                delete_previous_message(call.message.chat.id, call.message.message_id)
        elif call.data == "back_to_main":
            show_main_menu(call.message.chat.id, user_id)
            bot.answer_callback_query(call.id, "🔙 رجوع")
    except Exception as e:
        log_action(f"Error in callback_query for {call.from_user.id}: {e}")

def process_set_channel_subscription(message):
    global CHANNEL_USERNAME
    try:
        new_channel = message.text.strip()
        CHANNEL_USERNAME = new_channel
        log_action(f"Updated channel link to: {new_channel}")
        bot.send_message(message.chat.id, f"📢 إعداد الاشتراك تم تحديثه إلى: {new_channel}")
    except Exception as e:
        log_action(f"Error in process_set_channel_subscription: {e}")

def process_create_reward_code(message):
    try:
        text = message.text.strip().split()
        if len(text) != 2:
            bot.send_message(message.chat.id, "تنسيق غير صحيح، حاول مرة أخرى.")
            return
        code, value = text
        try:
            value = int(value)
        except:
            bot.send_message(message.chat.id, "القيمة يجب أن تكون رقمًا.")
            return
        reward_codes = read_reward_codes()
        reward_codes[code] = value
        write_reward_codes(reward_codes)
        log_action(f"Created reward code {code} with {value} points by admin")
        bot.send_message(message.chat.id, f"✨ تم إنشاء كود {code} بقيمة {value} نقطة.")
    except Exception as e:
        log_action(f"Error in process_create_reward_code: {e}")

def process_modify_points(message):
    try:
        text = message.text.strip().split()
        if len(text) != 2:
            bot.send_message(message.chat.id, "تنسيق غير صحيح، حاول مرة أخرى.")
            return
        target_user, new_points = text
        users = read_users()
        if target_user not in users:
            bot.send_message(message.chat.id, "المستخدم غير موجود.")
            return
        try:
            new_points = int(new_points)
        except:
            bot.send_message(message.chat.id, "النقاط يجب أن تكون رقمًا.")
            return
        users[target_user]["points"] = new_points
        write_users(users)
        log_action(f"Modified points of user {target_user} to {new_points} by admin")
        bot.send_message(message.chat.id, f"✏️ نقاط المستخدم {target_user} تم تعديلها إلى {new_points} نقطة.")
    except Exception as e:
        log_action(f"Error in process_modify_points: {e}")

def process_delete_reward_code(message):
    try:
        code = message.text.strip()
        reward_codes = read_reward_codes()
        if code not in reward_codes:
            bot.send_message(message.chat.id, "الكود غير موجود.")
            return
        del reward_codes[code]
        write_reward_codes(reward_codes)
        log_action(f"Deleted reward code {code} by admin")
        bot.send_message(message.chat.id, f"🗑️ كود {code} تم حذفه.")
    except Exception as e:
        log_action(f"Error in process_delete_reward_code: {e}")

def process_delete_user(message):
    try:
        target_user = message.text.strip()
        users = read_users()
        if target_user not in users:
            bot.send_message(message.chat.id, "المستخدم غير موجود.")
            return
        del users[target_user]
        write_users(users)
        log_action(f"Deleted user {target_user} by admin")
        bot.send_message(message.chat.id, f"❌ المستخدم {target_user} تم حذفه.")
    except Exception as e:
        log_action(f"Error in process_delete_user: {e}")

def process_reset_user(message):
    try:
        target_user = message.text.strip()
        users = read_users()
        if target_user not in users:
            bot.send_message(message.chat.id, "المستخدم غير موجود.")
            return
        users[target_user]["points"] = 0
        write_users(users)
        log_action(f"Reset points for user {target_user} by admin")
        bot.send_message(message.chat.id, f"🔄 نقاط المستخدم {target_user} تم إعادة تعيينها إلى 0.")
    except Exception as e:
        log_action(f"Error in process_reset_user: {e}")

@bot.message_handler(content_types=['new_chat_members'])
def new_member_handler(message):
    try:
        invite_link = getattr(message, 'invite_link', None)
        if not invite_link:
            return
        for member in message.new_chat_members:
            if invite_link.name and invite_link.name.startswith("ref_"):
                referrer_id = invite_link.name.split("ref_")[-1]
                users = read_users()
                if referrer_id in users:
                    users[referrer_id]["points"] += 150
                    users[referrer_id]["referrals"] += 1
                    users[referrer_id]["invite_usage"] = users[referrer_id].get("invite_usage", 0) + 1
                    write_users(users)
                    log_action(f"User {referrer_id} received 150 points for referring {member.id}")
                    bot.send_message(message.chat.id, f"شكرًا لانضمام {member.first_name}! تمت إضافة 150 نقطة للمُحيل.")
    except Exception as e:
        log_action(f"Error in new_member_handler: {e}")

bot.run = lambda: bot.polling(none_stop=True)
if __name__ == '__main__':
    bot.run()
