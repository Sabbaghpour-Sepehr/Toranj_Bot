import telebot
from telebot.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, InputMediaPhoto
from telebot.apihelper import ApiTelegramException
import DML
from threading import Timer
from config import *
from datetime import datetime, timedelta


# from requests_forwarder import setup_proxy
# setup_proxy(proxy_token="5cb3a6aae3c1f75479ba6994cbba00bb548e5672ad634f5472a3c11c5843225e")


CHANNEL_ID = -1004390152015

ADMIN_ID = 5890677297


user_steps = dict()
shopping_cart = dict()

bot = telebot.TeleBot(api_token, num_threads=5)

LOWER_LIMIT = 2
UPPER_LIMIT = 10
SPAM_LIMIT = 3
IGNORE_TIME = 1800


# دکمه های شیشه ای
markup = InlineKeyboardMarkup()
markup.add(InlineKeyboardButton('حساب کاربری', callback_data='نشان دادن اطلاعات حساب کاربری'),
           InlineKeyboardButton('پیش فاکتور', callback_data='نشان دادن پیش فاکتور'))
markup.add(InlineKeyboardButton('سبد خرید', callback_data='نشان دادن سبد خرید'))
markup.add(InlineKeyboardButton('درباره ما', callback_data='نشان دادن درباره ما'))


blocked_users = set(DML.get_blocked_customers())

spam_users = {}

album_storage = {}

message_ids = {
    "start"             :   2,
    "help"              :   3,
    "sign_up"           :   4,
    "about_us"          :   6,
    "under_start"       :   7,
    "support"           :   8,
    "support_answer"    :   9,
    "ban"               :   10,
    "answer_support"    :   11,
    "add_product"       :   12,
    "admin_help"        :   13,
    "ban_completed"     :   14,
    "unban"             :   15,
    "remove_product"    :   16,

}

support_messages = {}


def is_spam(cid):
    user_data = DML.get_customer_spam_data(cid)
    if user_data is None:
        return False
    current_time = datetime.now()
    spam_score = user_data["SPAM_SCORE"] or 0
    last_message = user_data["LAST_MESSAGE"]
    expire_spam = user_data["EXPIRE_SPAM"]
    if expire_spam is not None and current_time < expire_spam:
        return True
    if expire_spam is not None and current_time >= expire_spam:
        spam_score = 0
        expire_spam = None
    if last_message is None:
        DML.update_customer_spam_data(cid,spam_score,current_time,expire_spam)
        return False
    time_difference = (current_time - last_message).total_seconds()
    if time_difference < LOWER_LIMIT:
        spam_score += 1
    elif time_difference < UPPER_LIMIT:
        spam_score -= 1
        if spam_score < 0:
            spam_score = 0
    if spam_score >= SPAM_LIMIT:
        expire_spam = current_time + timedelta(seconds=IGNORE_TIME)
        DML.update_customer_spam_data(cid,spam_score,current_time,expire_spam)
        return True

    DML.update_customer_spam_data(cid,spam_score,current_time,expire_spam)
    return False


def gen_product_caption(pid, qty=1):
    product = DML.get_product_by_id(pid)
    if product is None:
        return None
    name = product["NAME"]
    description = product["DESCRIPTION"] or ""
    part_number = product["PART_NUMBER"] or "-"
    brand = product["BRAND"] or "-"
    price = product["PRICE"] or 0
    text = f"""نام: {name}
پارت نامبر: {part_number}
برند: {brand}

{description}

قیمت: {price:,}
تعداد: {qty}
مجموع: {price * qty:,}
"""
    return text


def gen_product_markup(pid, qty=1):
    product = DML.get_product_by_id(pid)
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton('➖', callback_data=f'change_{pid}_{qty-1}', style='danger'),
               InlineKeyboardButton(str(qty), callback_data=f'change_{pid}_1', style='primary'),
               InlineKeyboardButton('➕', callback_data=f'change_{pid}_{qty+1}', style='success'))
    markup.add(InlineKeyboardButton('add to basket', callback_data=f'add_{pid}_{qty}'))
    if product and product["LINK"]:
        markup.add(InlineKeyboardButton("مشاهده محصول", url=product["LINK"]))
    markup.add(InlineKeyboardButton("بازگشت", callback_data="بازگشت به ص اول شیشه ای"))
    return markup


def gen_basket_view(cid):
    cart = DML.get_customer_basket(cid)
    markup = InlineKeyboardMarkup()
    if not cart:
        markup.add(InlineKeyboardButton("بازگشت", callback_data="بازگشت به ص اول شیشه ای"))
        return "سبد خرید شما خالی است", markup
    text = "**سبد خرید شما:**\n\n"
    total_price = 0
    for index, item in enumerate(cart, start=1):
        product_id = item["PRODUCT_ID"]
        name = item["NAME"]
        quantity = item["QUANTITY"]
        price = item["UNIT_PRICE"]
        markup.add(InlineKeyboardButton("➖", callback_data=f"cart_minus_{product_id}"),
                    InlineKeyboardButton(text=str(quantity), callback_data=f"cart_info_{product_id}"),
                    InlineKeyboardButton("➕", callback_data=f"cart_plus_{product_id}"))
        text += f"نام محصول: {name}\n"
        text += f"قیمت: {price}\n"
        text += f"💳 **مبلغ نهایی:** {total_price:,} تومان"
        markup.add(InlineKeyboardButton("گرفتن پیش فاکتور",callback_data="نشان دادن پیش فاکتور"))
        markup.add(InlineKeyboardButton("بازگشت",callback_data="بازگشت به ص اول شیشه ای"))
    return text, markup


def gen_invoice_text(cid):
    customer = DML.get_customer_by_id(cid)
    cart = DML.get_customer_basket(cid)
    if customer is None:
        return None
    if not cart:
        return None
    firstname = customer["FIRSTNAME"] or "-"
    lastname = customer["LASTNAME"] or "-"
    phone = customer["PHONE"] or "-"
    text = "🧾 **پیش فاکتور**\n\n"
    text += f"👤 نام مشتری: {firstname} {lastname}\n"
    text += f"📞 شماره تماس: {phone}\n"
    text += f"🆔 شناسه مشتری: {cid}\n\n"
    text += "--------------------\n\n"
    total_price = 0
    for index, item in enumerate(cart, start=1):
        name = item["NAME"]
        quantity = item["QUANTITY"]
        unit_price = item["UNIT_PRICE"]
        item_total = unit_price * quantity
        total_price += item_total
        text += f"**{index}. {name}**\n"
        text += f"تعداد: {quantity}\n"
        text += f"قیمت واحد: {unit_price:,} تومان\n"
        text += f"جمع: {item_total:,} تومان\n\n"

    text += "--------------------\n"
    text += f"💰 **مبلغ کل: {total_price:,} تومان**"
    return text


# only used for console output now
def listener(messages):
    """
    When new messages arrive TeleBot will call this function.
    """
    for m in messages:
        # print(m)
        if m.content_type == 'text':
            print(f"{m.chat.first_name} [{m.chat.id}]: {m.text}")
        elif m.content_type == 'photo':
            print(f"{m.chat.first_name} [{m.chat.id}]: new photo received.")
        elif m.content_type == 'document':
            print(f"{m.chat.first_name} [{m.chat.id}]: new document received.")
        elif m.content_type == 'contact':
            print(f"{m.chat.first_name} [{m.chat.id}]: new contact received.")

bot.set_update_listener(listener)  # register listener


def album_processor(mgid, cid):
    if mgid not in album_storage:
        return
    data = album_storage.pop(mgid)
    caption = data.get("caption")
    photos = data.get("photos", [])
    if not caption:
        bot.send_message(cid, "لطفا عکس های با کپشن ارسال کنید")
        return
    items = [item.strip() for item in caption.split("$")]
    if len(items) < 7:
        bot.send_message(cid,"فرمت کپشن نامعتبر است!")
        return
    try:
        category_id = int(items[0])
        name = items[1]
        part_number = items[2]
        brand = items[3]
        description = items[4]
        price = float(items[5])
        link = str(items[6])
        pic1 = photos[0] if len(photos) > 0 else None
        pic2 = photos[1] if len(photos) > 1 else None
        pic3 = photos[2] if len(photos) > 2 else None
        DML.insert_product_data(category_id, name, part_number, brand, description, pic1, pic2, pic3, price, link, cid)
        bot.send_message(cid, f" محصول **{name}** با موفقیت در دیتابیس ثبت شد.", parse_mode="Markdown")
        user_steps.pop(cid, None)
    except Exception as e:
        bot.send_message(cid, f" خطا در ثبت اطلاعات در دیتابیس:\n`{e}`", parse_mode="Markdown")



@bot.message_handler(commands=['start'])
def send_welcome(message):
    if message.chat.id in blocked_users:
        return
    cid = message.chat.id
    user = message.from_user
    DML.customer_exists(cid, user.first_name, user.last_name, user.username)
    if is_spam(cid):
        return
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('جستجوی محصولات با نام' , 'جستجوی محصولات با پارت نامبر')
    keyboard.add('چت با هوش مصنوعی')
    keyboard.add('دسته بندی محصولات')
    keyboard.add('لیست خدمات' , 'چت با پشتیبانی')
    bot.copy_message(cid, CHANNEL_ID, message_ids["start"],reply_markup= keyboard)
    bot.copy_message(cid, CHANNEL_ID, message_ids["under_start"], reply_markup=markup)
    print(spam_users)


@bot.message_handler(commands=['help'])
def command_help_handler(message):
    if message.chat.id in blocked_users:
        return
    cid = message.chat.id
    if is_spam(cid):
        return
    if DML.is_admin(cid):
        bot.copy_message(cid, CHANNEL_ID, message_ids["admin_help"])
    else:
        bot.copy_message(cid, CHANNEL_ID, message_ids["help"])


@bot.message_handler(commands=['sign_up'])
def command_get_info_handler(message):
    if message.chat.id in blocked_users:
        return
    cid = message.chat.id
    if is_spam(cid):
        return
    bot.copy_message(cid, CHANNEL_ID, message_ids["sign_up"])
    user_steps[cid] = 'SIGN_UP'


@bot.message_handler(commands=['ban'])
def command_ban_handler(message):
    cid = message.chat.id
    if is_spam(cid):
        return
    if not DML.is_admin(cid):
        echo_message(message)
    else:
        bot.copy_message(cid, CHANNEL_ID, message_ids["ban"])
        user_steps[cid] = 'BAN_USER'


@bot.message_handler(commands=['unban'])
def command_unban_handler(message):
    cid = message.chat.id
    if is_spam(cid):
        return
    if not DML.is_admin(cid):
        echo_message(message)
    else:
        bot.copy_message(cid, CHANNEL_ID, message_ids["unban"])
        user_steps[cid] = 'UNBAN_USER'


@bot.message_handler(commands=['add_product'])
def command_add_product_handler(message):
    cid = message.chat.id
    if not DML.is_admin(cid):
        echo_message(message)
    else:
        bot.copy_message(cid, CHANNEL_ID, message_ids["add_product"])
        user_steps[cid] = "ADD_PRODUCT"


@bot.message_handler(commands=['remove_product'])
def command_remove_product_handler(message):
    cid = message.chat.id
    if not DML.is_admin(cid):
        echo_message(message)
    else:
        bot.copy_message(cid, CHANNEL_ID, message_ids["remove_product"])
        user_steps[cid] = "REMOVE_PRODUCT"


@bot.message_handler(func=lambda m: (m.chat.id == ADMIN_ID and m.reply_to_message is not None),
                     content_types=["text", "photo", "video", "document", "voice"])
def support_reply_handler(message):
    replied_message_id = message.reply_to_message.message_id
    cid = support_messages.get(replied_message_id)
    if cid is None:
        bot.reply_to(message, "کاربر این پیام پیدا نشد")
        return
    if is_spam(cid):
        return
    new_keyboard = InlineKeyboardMarkup()
    new_keyboard.add(InlineKeyboardButton("پاسخ دادن", callback_data="فرستادن پاسخ به ادمین"))
    bot.copy_message(cid, ADMIN_ID, message.message_id)
    try:
        bot.send_message(cid, "برای جواب دادن به ادمین دکمه زیر را کلیک کنید", reply_markup=new_keyboard)
    except ApiTelegramException as error:
        print("خطای تلگرام:", error)
    bot.reply_to(message, "پاسخ برای کاربر ارسال شد")


@bot.callback_query_handler(func=lambda call: True)
def callback_query_handler_method(call):
    cid = call.message.chat.id
    if cid in blocked_users:
        return
    if is_spam(cid):
        return
    mid = call.message.message_id
    call_id = call.id
    data = call.data
    print(f'cid: {cid}, mid: {mid}, call_id: {call_id}, data: {data}')

    if data == "نشان دادن اطلاعات حساب کاربری":
        bot.answer_callback_query(call_id,"اطلاعات حساب کاربری شما:")
        user = call.from_user
        DML.customer_exists(cid, user.first_name, user.last_name, user.username)
        customer = DML.get_customer_by_id(cid)
        if customer is None:
            bot.answer_callback_query(call_id, "اطلاعات کاربر پیدا نشد")
            return
        firstname = customer["FIRSTNAME"] or "-"
        lastname = customer["LASTNAME"] or "-"
        phone = customer["PHONE"] or "ثبت نشده"
        username = customer["USERNAME"] or "ندارد"
        text = f"""**حساب کاربری**

        نام: {firstname}
        نام خانوادگی: {lastname}

        یوزرنیم: @{username}
        شماره تلفن: {phone}

        شناسه تلگرام:
        `{cid}`
        """
        new_markup = InlineKeyboardMarkup()
        new_markup.add(InlineKeyboardButton("بازگشت", callback_data="بازگشت به ص اول شیشه ای"))
        try:
            bot.edit_message_text(chat_id=cid, message_id=mid, text=text, reply_markup=new_markup, parse_mode="Markdown")
        except ApiTelegramException as error:
            print("خطای تلگرام:", error)

    elif data == "نشان دادن پیش فاکتور":
        bot.answer_callback_query(call_id, "پیش فاکتور شما:")
        cart = DML.get_customer_basket(cid)
        if not cart:
            bot.delete_message(cid, call.message.message_id)
            try:
                bot.send_message(cid, "سبد خرید شما خالی است")
            except ApiTelegramException as error:
                print("خطای تلگرام:", error)
            return
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        keyboard.add(KeyboardButton("ارسال شماره", request_contact=True))
        bot.delete_message(cid, call.message.message_id)
        try:
            bot.send_message(cid,"لطفا جهت احراز هویت و ارتباط با شما شماره خود را ارسال نمایید", reply_markup=keyboard)
        except ApiTelegramException as error:
            print("خطای تلگرام:", error)
        user_steps[cid] = 'INVOICE_PHONE'

    elif data == "نشان دادن سبد خرید":
        bot.answer_callback_query(call_id, "سبد خرید شما:")
        text, basket_markup = gen_basket_view(cid)
        try:
            bot.edit_message_text(
                chat_id=cid,
                message_id=call.message.message_id,
                text=text,
                reply_markup=basket_markup,
                parse_mode="Markdown",
            )
        except ApiTelegramException as error:
            print("پیام ادیت نشد:", error)

    elif data == "نشان دادن درباره ما":
        bot.answer_callback_query(call_id, "درباره شرکت تدبیر پردازان ترنج:")
        new_markup = InlineKeyboardMarkup()
        new_markup.add(InlineKeyboardButton("بازگشت", callback_data="بازگشت به ص اول شیشه ای"))
        bot.delete_message(cid, mid)
        bot.copy_message(cid, CHANNEL_ID, message_ids["about_us"], reply_markup=new_markup)

    elif data == "بازگشت به ص اول شیشه ای":
        bot.answer_callback_query(call_id, "شما به صفحه اول بازگشتید:")
        bot.edit_message_reply_markup(cid, mid, reply_markup=markup)
        try:
            bot.edit_message_text(chat_id=cid, message_id=call.message.message_id,text= "چه کاری میخواهید انجام بدهید؟", reply_markup=markup)
        except ApiTelegramException as error:
            print("پیام ادیت نشد:", error)

    elif data.startswith('change'):
        _, pid, qty = data.split('_')
        pid = int(pid)
        qty = int(qty)
        if qty <= 0:
            bot.answer_callback_query(call_id, 'quantity can not be zero')
            return
        new_caption = gen_product_caption(pid, qty)
        new_markup = gen_product_markup(int(pid), int(qty))
        try:
            if call.message.photo:
                bot.edit_message_caption(chat_id=cid, message_id=mid, caption=new_caption, reply_markup=new_markup)
            else:
                bot.edit_message_text(chat_id=cid, message_id=mid, text=new_caption, reply_markup=new_markup)
        except ApiTelegramException as error:
            print("خطا در تغییر عدد سبد خرید", error)
        bot.answer_callback_query(call_id, f'quantity changed to {qty}')

    elif data.startswith('add_'):
        _, pid, qty = data.split('_')
        pid = int(pid)
        qty = int(qty)
        user = call.from_user
        DML.customer_exists(cid, user.first_name, user.last_name, user.username)
        result = DML.add_to_basket(cid, pid, qty)
        if result:
            bot.answer_callback_query(call_id, f'به سبد خرید اضافه شد')
            print(shopping_cart)
        else:
            bot.answer_callback_query(call_id, "محصول به سبد خزید اضافه نشد!")

    elif data == "فرستادن پاسخ به ادمین":
        new_markup = InlineKeyboardMarkup()
        new_markup.add(InlineKeyboardButton("بازگشت", callback_data="بازگشت به ص اول شیشه ای"))
        bot.copy_message(cid, CHANNEL_ID, message_ids["answer_support"], reply_markup=new_markup)
        bot.answer_callback_query(call_id, "لطفا پاسخ خود به ادمین را وارد نمایید:")
        user_steps[cid] = 'SUPPORT_REPLY'

    elif data.startswith("cart_plus_"):
        product_id = int(data.split("_")[2])
        DML.increase_basket_quantity(cid, product_id)
        text, basket_markup = gen_basket_view(cid)
        try:
            bot.edit_message_text(
                chat_id=cid,
                message_id=mid,
                text=text,
                reply_markup=basket_markup,
                parse_mode="Markdown")
        except ApiTelegramException as error:
            print("سبد خرید آپدیت نشد:", error)
        bot.answer_callback_query(call_id,"تعداد افزایش یافت ➕")

    elif data.startswith("cart_minus_"):
        product_id = int(data.split("_")[2])
        changed = DML.decrease_basket_quantity(cid, product_id)
        if not changed:
            bot.answer_callback_query(call_id, "حداقل تعداد 1 است")
            return
        text, basket_markup = gen_basket_view(cid)
        try:
            bot.edit_message_text(
                chat_id=cid,
                message_id=mid,
                text=text,
                reply_markup=basket_markup,
                parse_mode="Markdown")
        except ApiTelegramException as error:
            print("سبد خرید آپدیت نشد:", error)
        bot.answer_callback_query(call_id, "تعداد کاهش یافت ➖")

    elif data.startswith("cart_info_"):
        product_id = int(data.split("_")[2])
        DML.remove_from_basket(cid, product_id)
        text, basket_markup = gen_basket_view(cid)
        try:
            bot.edit_message_text(
                chat_id=cid,
                message_id=mid,
                text=text,
                reply_markup=basket_markup,
                parse_mode="Markdown")
        except ApiTelegramException as error:
            print("سبد خرید آپدیت نشد:", error)
        bot.answer_callback_query(call_id, "محصول از سبد خرید حذف شد")


#این جواب دکمه های منوی پایین
@bot.message_handler(func=lambda m: m.text == 'جستجوی محصولات با نام')
def name_search_handler(message):
    if message.chat.id in blocked_users:
        return
    cid = message.chat.id
    if is_spam(cid):
        return
    try:
        bot.send_message(cid, "نام محصول مورد نظر را وارد کنید", reply_markup=ReplyKeyboardRemove())
        user_steps[cid] = "SEARCH_PRODUCT_BY_NAME"
    except ApiTelegramException as error:
        print("خطای تلگرام:", error)

@bot.message_handler(func=lambda m: m.text == 'جستجوی محصولات با پارت نامبر')
def name_search_handler(message):
    if message.chat.id in blocked_users:
        return
    cid = message.chat.id
    if is_spam(cid):
        return
    try:
        bot.send_message(cid, "پارت نامبر محصول مورد نظر را وارد کنید", reply_markup=ReplyKeyboardRemove())
        user_steps[cid] = "SEARCH_PRODUCT_BY_PART_NUMBER"
    except ApiTelegramException as error:
        print("خطای تلگرام:", error)


@bot.message_handler(func=lambda m: m.text == 'چت با هوش مصنوعی')
def name_search_handler(message):
    if message.chat.id in blocked_users:
        return
    cid = message.chat.id
    if is_spam(cid):
        return
    try:
        bot.send_message(cid, "سلام من دستیار هوش مصنوعی هستم سوالتون رو یپرسید", reply_markup=ReplyKeyboardRemove())
    except ApiTelegramException as error:
        print("خطای تلگرام:", error)


@bot.message_handler(func=lambda m: m.text == 'دسته بندی محصولات')
def category_handler(message):
    cid = message.chat.id
    if cid in blocked_users:
        return
    if is_spam(cid):
        return
    category_data = DML.get_all_categories()
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    category_names = []
    for category_id, category_name in category_data:
        category_names.append(category_name)
    for i in range(0, len(category_names), 2):
        keyboard.add(*category_names[i:i + 2])
    try:
        bot.send_message(cid, "لطفا یکی از دسته بندی های زیر را انتخاب کنید", reply_markup=keyboard)
    except ApiTelegramException as error:
        print("خطای تلگرام:", error)
    user_steps[cid] = 'SELECT_PRODUCT_CATEGORY'


@bot.message_handler(func=lambda m: m.text == 'لیست خدمات')
def name_search_handler(message):
    cid = message.chat.id
    if cid in blocked_users:
        return
    if is_spam(cid):
        return
    services = DML.get_all_services()
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    service_names = []
    for service in services:
        service_names.append(service["NAME"])
    for i in range(0, len(service_names), 2):
        keyboard.add(*service_names[i:i + 2])
        bot.send_message(cid, "لطفاً یکی از خدمات زیر را انتخاب کنید:", reply_markup=keyboard)
        user_steps[cid] = "SELECT_SERVICE"


@bot.message_handler(func=lambda m: m.text == 'چت با پشتیبانی')
def name_search_handler(message):
    if message.chat.id in blocked_users:
        return
    cid = message.chat.id
    if is_spam(cid):
        return
    new_markup = InlineKeyboardMarkup()
    new_markup.add(InlineKeyboardButton("بازگشت", callback_data="بازگشت به ص اول شیشه ای"))
    bot.copy_message(cid, CHANNEL_ID, message_ids["support"], reply_markup=new_markup)
    user_steps[cid] = 'SUPPORT_MESSAGE'


@bot.message_handler(func=lambda m: user_steps.get(m.chat.id) == 'SIGN_UP')
def user_step_sign_up_handler(message):
    if message.chat.id in blocked_users:
        return
    cid = message.chat.id
    if is_spam(cid):
        return
    if message.text is None:
        try:
            bot.send_message(message.chat.id, "لطفاً فقط متن ارسال کنید.")
        except ApiTelegramException as error:
            print("خطای تلگرام:", error)
        return
    username = message.text
    try:
        bot.send_message(cid, 'نام شما ثبت شد.')
    except ApiTelegramException as error:
        print("خطای تلگرام:", error)
    user_steps.pop(cid)


@bot.message_handler(func=lambda m: user_steps.get(m.chat.id) == 'SELECT_PRODUCT_CATEGORY')
def user_step_select_product_category_handler(message):
    if message.chat.id in blocked_users:
        return
    cid = message.chat.id
    if is_spam(cid):
        return
    selected_category = message.text
    category_data = DML.get_all_categories()
    category_names = []
    for category_id, category_name in category_data:
        category_names.append(category_name)
    if selected_category not in category_names:
        try:
            bot.send_message(cid, "لطفا از کنگوری های زیر یکی را انتخاب کنید")
        except ApiTelegramException as error:
            print("خطای تلگرام:", error)
        return
    products_data = DML.get_products(selected_category)
    if not products_data:
        try:
            bot.send_message(cid, "در حال حاضر محصولی در این دسته بندی وجود ندارد")
        except ApiTelegramException as error:
            print("خطای تلگرام", error)
        user_steps.pop(cid, None)
        return
    new_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    product_names = []
    for product_id, product_name in products_data:
        product_names.append(product_name)
    for i in range(0, len(product_names), 2):
        new_keyboard.add(*product_names[i:i + 2])
    try:
        bot.send_message(cid, "لطفا یکی ازمحصولات زیر را انتخاب کنید", reply_markup=new_keyboard)
    except ApiTelegramException as  e:
        print("خطای تلگرام", e)
    user_steps[cid] = "SELECT_PRODUCTS"


@bot.message_handler(func=lambda m: user_steps.get(m.chat.id) == 'SELECT_SERVICE')
def user_step_select_service_category_handler(message):
    cid = message.chat.id
    if cid in blocked_users:
        return
    if is_spam(cid):
        return
    if message.text is None:
        bot.send_message(message.chat.id, "لطفا از سرویس های زیر یکی را انتخاب کنید")
    service = DML.get_service_by_name(message.text)
    if service is None:
        bot.send_message(cid, "لطفا از سرویس های زیر یکی را انتخاب کنید")
        return
    name = service["NAME"]
    description = service["DESCRIPTION"] or ""
    text = f"""**{name}**

    {description}
    """
    new_markup = InlineKeyboardMarkup()
    new_markup.add(InlineKeyboardButton("بازگشت", callback_data="بازگشت به صفحه اول شیشه ای"))
    bot.send_message(cid, text, reply_markup=new_markup, parse_mode="Markdown")
    user_steps.pop(cid, None)


@bot.message_handler(func=lambda m: user_steps.get(m.chat.id) == 'SUPPORT_MESSAGE',
                     content_types=['text', 'photo', 'document', 'voice', 'video'])
def user_step_support_message_handler(message):
    if message.chat.id in blocked_users:
        return
    cid = message.chat.id
    if is_spam(cid):
        return
    mid = message.message_id
    user = message.from_user
    name = user.first_name
    last_name = user.last_name if user.last_name else "نام خانوادگی وارد نشده"
    username = user.username if user.username else "یوزرنیم ندارد"
    user_id = user.id
    text = f"""
نام = {name} {last_name}
یوزرنیم = @{username}
آیدی عددی = {user_id}
برای پاسخ دادن دکمه زیر را فشار دهید.
    """
    forwarded_message = bot.forward_message(chat_id=ADMIN_ID, from_chat_id=cid, message_id=mid)
    support_messages[forwarded_message.message_id] = cid
    try:
        bot.send_message(ADMIN_ID, text)
    except ApiTelegramException as error:
        print("خطای تلگرام:", error)
    bot.copy_message(cid, CHANNEL_ID, message_ids["support_answer"])
    print(support_messages)
    user_steps.pop(cid)


@bot.message_handler(func=lambda m: user_steps.get(m.chat.id) == 'BAN_USER')
def user_step_ban_user_handler(message):
    cid = message.chat.id
    if message.text is None:
        bot.send_message(cid, "لطفاً فقط آیدی عددی کاربر را وارد کنید.")
        return
    try:
        user_id = int(message.text)
    except ValueError:
        bot.send_message(cid, "لطفا فقط آیدی عددی کاربر را وارد کنید")
        return
    result = DML.block_customer(user_id)
    if not result:
        bot.send_message(cid, "کاربری با این آیدی در دیتابیس پیدا نشد")
        return
    blocked_users.add((user_id))
    bot.copy_message(cid, CHANNEL_ID, message_ids["ban_completed"])
    user_steps.pop(cid, None)


@bot.message_handler(func=lambda m: user_steps.get(m.chat.id) == 'SUPPORT_REPLY')
def user_step_support_reply_handler(message):
    cid = message.chat.id
    if is_spam(cid):
        return
    if message.text is None:
        try:
            bot.send_message(message.chat.id, "لطفاً فقط متن ارسال کنید.")
        except ApiTelegramException as error:
            print("خطای تلگرام:", error)
        return
    mid = message.message_id
    user = message.from_user
    name = user.first_name
    last_name = user.last_name if user.last_name else "نام خانوادگی وارد نشده"
    username = user.username if user.username else "یوزرنیم ندارد"
    user_id = user.id
    text = f"""
    نام = {name} {last_name}
    یوزرنیم = @{username}
    آیدی عددی = {user_id}
        """
    forwarded_message = bot.forward_message(chat_id=ADMIN_ID, from_chat_id=cid, message_id=mid)
    support_messages[forwarded_message.message_id] = cid
    bot.reply_to(forwarded_message, text)
    bot.copy_message(cid, CHANNEL_ID, message_ids["support_answer"])
    print(support_messages)
    user_steps.pop(cid)


@bot.message_handler(content_types=['contact'], func=lambda m: user_steps.get(m.chat.id) == 'INVOICE_PHONE')
def user_step_invoice_phone_handler(message):
    cid = message.chat.id
    if is_spam(cid):
        return
    if message.contact is None:
        bot.send_message(message.chat.id, "لطفا یک مخاطب ارسال کنید یا از دکمه زیر استفاده کنید.")
        return
    phone_number = message.contact.phone_number
    user_cid = message.contact.user_id
    if cid != user_cid:
        bot.send_message(cid,"لطفاً شماره تلفن متعلق به خودتان را ارسال کنید.")
        return
    DML.update_customer_phone(cid, phone_number)
    invoice_text = gen_invoice_text(cid)
    if invoice_text is None:
        bot.send_message(cid,"خطا در ساخت پیش فاکتور.")
        return
    try:
        bot.send_message(cid, invoice_text, parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())

    except ApiTelegramException as error:
        print("خطای تلگرام:", error)

    user_steps.pop(cid, None)


@bot.message_handler(func=lambda m: user_steps.get(m.chat.id) == "SELECT_PRODUCTS")
def user_step_select_products_handler(message):
    if message.chat.id in blocked_users:
        return
    cid = message.chat.id
    if is_spam(cid):
        return
    if message.text is None:
        try:
            bot.send_message(cid,"لطفاً یکی از محصولات را انتخاب کنید.")
        except ApiTelegramException as error:
            print("خطای تلگرام:", error)
        return
    selected_product = DML.get_product_by_name(message.text)
    if selected_product is None:
        try:
            bot.send_message(cid,"محصول مورد نظر پیدا نشد.")
        except ApiTelegramException as error:
            print("خطای تلگرام:", error)
        return
    product_id = selected_product["PRODUCT_ID"]
    product = DML.get_product_by_id(product_id)
    caption = gen_product_caption(product_id)
    photos = []
    if product["PIC1"]:
        photos.append(product["PIC1"])
    if product["PIC2"]:
        photos.append(product["PIC2"])
    if product["PIC3"]:
        photos.append(product["PIC3"])
    try:
        if len(photos) > 1:
            media = []
            for photo in photos:
                media.append(InputMediaPhoto(media=photo))
            bot.send_media_group(cid,media)
            bot.send_message(cid, caption, reply_markup=gen_product_markup(product_id))
        elif len(photos) == 1:
            bot.send_photo(cid, photos[0], caption=caption, reply_markup=gen_product_markup(product_id))
        else:
            bot.send_message(cid,caption,reply_markup=gen_product_markup(product_id))
    except ApiTelegramException as error:
        print("خطای تلگرام:", error)
    user_steps.pop(cid, None)


@bot.message_handler(func=lambda m: user_steps.get(m.chat.id) == "SEARCH_PRODUCT_BY_NAME")
def search_product_by_name_handler(message):
    cid = message.chat.id
    if cid in blocked_users:
        return
    if is_spam(cid):
        return
    if message.text is None:
        bot.send_message(cid, "لطفا نام محصول را وارد کنید")
        return
    search_text = message.text.strip()
    results = DML.search_products_by_name(search_text)
    if not results:
        bot.send_message(cid, "محصولی با این نام پیدا نشد")
        return
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    for product in results:
        keyboard.add(product["NAME"])
    bot.send_message(cid, "نتایج جست و جو:", reply_markup=keyboard)
    user_steps[cid] = "SELECT_PRODUCTS"


@bot.message_handler(func=lambda m: user_steps.get(m.chat.id) == "SEARCH_PRODUCT_BY_PART_NUMBER")
def search_product_by_part_number_handler(message):
    cid = message.chat.id
    if cid in blocked_users:
        return
    if is_spam(cid):
        return
    if message.text is None:
        bot.send_message(cid, "لطفا پارت نامبر را به صورت متنی وارد کنید")
        return
    search_text = message.text.strip()
    results = DML.search_products_by_part_number(search_text)
    if not results:
        bot.send_message(cid, "محصولی با این پارت نامبر پیدا نشد")
        return
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    for product in results:
        keyboard.add(product["NAME"])
    bot.send_message(cid, "نتایج جست و جو:", reply_markup=keyboard)
    user_steps[cid] = "SELECT_PRODUCTS"


@bot.message_handler(func=lambda m: user_steps.get(m.chat.id) == 'UNBAN_USER')
def user_step_ban_user_handler(message):
    cid = message.chat.id
    if message.text is None:
        bot.send_message(cid, "لطفاً فقط آیدی عددی کاربر را وارد کنید.")
        return
    try:
        user_id = int(message.text)
    except ValueError:
        bot.send_message(cid, "لطفا فقط آیدی عددی کاربر را وارد کنید")
        return
    result = DML.unblock_customer(user_id)
    if not result:
        bot.send_message(cid, "کاربری با یان آیدی در دیتابیس پیدا نشد")
        return
    blocked_users.discard(user_id)
    bot.send_message(cid, f"کاربر {user_id} از بن خارج شد ")
    user_steps.pop(cid, None)


@bot.message_handler(func=lambda m: user_steps.get(m.chat.id) == 'REMOVE_PRODUCT')
def user_step_remove_product_handler(message):
    cid = message.chat.id
    try:
        product_id = int(message.text)
    except (ValueError, TypeError):
        bot.send_message(cid, "لطفا آیدی محصولات رو به صورت عدد وارد کنید")
        return
    result = DML.remove_product(product_id)
    if result:
        bot.send_message(cid, "محصول با موفقیت حذف شد")
    else:
        bot.send_message(cid, "محصول پیدا نشد")
    user_steps.pop(cid, None)


@bot.message_handler(content_types=['photo'])
def photo_handler(message):
    cid = message.chat.id
    if is_spam(cid):
        return
    file_id = message.photo[-1].file_id
    if user_steps.get(cid) == "ADD_PRODUCT":
        mgid = message.media_group_id
        photo_id = message.photo[-1].file_id
        if not mgid:
            bot.send_message(cid, "لطفا عکس چندتایی استفاده نمایید")
            return
        if mgid not in album_storage:
            album_storage[mgid] = {
                "photos" : [photo_id],
                "caption" : message.caption,
                "timer" : None
            }
        else:
            album_storage[mgid]["photos"].append(photo_id)
            if message.caption:
                album_storage[mgid]["caption"] = message.caption
            if album_storage[mgid]["timer"]:
                album_storage[mgid]["timer"].cancel()
        timer = Timer(1.0, album_processor, args=[mgid, cid])
        album_storage[mgid]["timer"] = timer
        timer.start()
    else:
        file_id = message.photo[-1].file_id
        print(f"Photo received from {cid}: {file_id}")


@bot.message_handler(content_types=['document'])
def document_handler(message):
    cid = message.chat.id
    if is_spam(cid):
        return
    file_id = message.document.file_id
    print(file_id)


@bot.message_handler(content_types=['contact'])
def contact_handler(message):
    cid = message.chat.id
    if is_spam(cid):
        return
    print(message.contact)


@bot.message_handler(func=lambda message: True)
def echo_message(message):
    if message.chat.id in blocked_users:
        return
    cid = message.chat.id
    if is_spam(cid):
        return
    if message.text is None:
        try:
            bot.send_message(message.chat.id, "لطفاً فقط متن ارسال کنید.")
        except ApiTelegramException as error:
            print("خطای تلگرام:", error)
        return
    bot.reply_to(message, message.text)




bot.infinity_polling(skip_pending=True)
