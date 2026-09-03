import mysql.connector
from config import *


def insert_customer_data(cid, firstname, lastname, phone, username):
    conn = mysql.connector.connect(**database_config, database=database_name)
    cur = conn.cursor()

    SQL_QUERY = "INSERT INTO customers (CID, FIRSTNAME, LASTNAME, PHONE, USERNAME) VALUES (%s, %s, %s, %s, %s)"
    cur.execute(SQL_QUERY, (cid, firstname, lastname, phone, username))

    conn.commit()
    cur.close()
    conn.close()
    print(f"customer {username} created successfully")
    return True


def insert_admin_data(admin_cid, firstname, lastname, username, role):
    conn = mysql.connector.connect(**database_config, database=database_name)
    cur = conn.cursor()

    # اصلاح نام ستون‌ها به FIRST_NAME و LAST_NAME
    SQL_QUERY = "INSERT INTO admins (ADMIN_CID, FIRST_NAME, LAST_NAME, USERNAME, ROLE) VALUES (%s, %s, %s, %s, %s)"
    cur.execute(SQL_QUERY, (admin_cid, firstname, lastname, username, role))

    conn.commit()
    cur.close()
    conn.close()
    print(f"admin {username} added successfully")
    return True


def insert_category_data(name):
    conn = mysql.connector.connect(**database_config, database=database_name)
    cur = conn.cursor()

    SQL_QUERY = "INSERT INTO categories (NAME) VALUES (%s)"
    # اضافه شدن ویرگول برای ساخت tuple تک‌عنصری
    cur.execute(SQL_QUERY, (name,))

    conn.commit()
    cur.close()
    conn.close()
    return True


def insert_product_data(category_id, name, part_number, brand, description, pic1, pic2, pic3, price, link, admin_cid):
    conn = mysql.connector.connect(**database_config, database=database_name)
    cur = conn.cursor()

    SQL_QUERY = """
                INSERT INTO products 
                (CATEGORY_ID, NAME, PART_NUMBER, BRAND, DESCRIPTION, PIC1, PIC2, PIC3, PRICE,LINK, ADMIN_CID) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
    cur.execute(SQL_QUERY, (category_id, name, part_number, brand, description, pic1, pic2, pic3, price, link, admin_cid))


    conn.commit()
    cur.close()
    conn.close()
    print(f"product {name} created successfully")
    return True


def remove_product(product_id):
    conn = mysql.connector.connect(**database_config,database=database_name)
    cur = conn.cursor()

    SQL_QUERY = "UPDATE products SET IS_ACTIVE = 'NO' WHERE PRODUCT_ID = %s AND IS_ACTIVE = 'YES'"

    cur.execute(SQL_QUERY, (product_id,))
    removed = cur.rowcount > 0
    conn.commit()
    cur.close()
    conn.close()
    return removed


def get_all_categories():
    conn = mysql.connector.connect(**database_config, database=database_name)
    cur = conn.cursor()

    SQL_QUERY = "SELECT CATEGORY_ID, NAME FROM categories ORDER BY CATEGORY_ID"
    cur.execute(SQL_QUERY)
    categories = cur.fetchall()


    cur.close()
    conn.close()
    return categories


def get_products(category_name):
    conn = mysql.connector.connect(**database_config, database=database_name)
    cur = conn.cursor()

    SQL_QUERY = """
        SELECT products.PRODUCT_ID, products.NAME FROM products INNER JOIN categories
                   ON products.CATEGORY_ID = categories.CATEGORY_ID
        WHERE categories.NAME = %s AND products.IS_ACTIVE = 'YES' ORDER BY products.PRODUCT_ID
                    """

    cur.execute(SQL_QUERY, (category_name,))

    products = cur.fetchall()
    cur.close()
    conn.close()
    return products


def get_product_by_id(product_id):
    conn = mysql.connector.connect(**database_config, database=database_name)
    cur = conn.cursor(dictionary=True)

    SQL_QUERY = "SELECT PRODUCT_ID, CATEGORY_ID, NAME, PART_NUMBER, BRAND, DESCRIPTION, PIC1, PIC2, PIC3, PRICE, LINK, ADMIN_CID FROM products WHERE PRODUCT_ID = %s AND products.IS_ACTIVE = 'YES'"

    cur.execute(SQL_QUERY, (product_id,))
    product = cur.fetchone()
    cur.close()
    conn.close()
    return product


def get_product_by_name(product_name):
    conn = mysql.connector.connect(**database_config, database=database_name)
    cur = conn.cursor(dictionary=True)

    SQL_QUERY = "SELECT PRODUCT_ID, NAME FROM products WHERE NAME = %s AND products.IS_ACTIVE = 'YES' LIMIT 1"

    cur.execute(SQL_QUERY, (product_name,))
    product = cur.fetchone()
    cur.close()
    conn.close()
    return product


def customer_exists(cid, firstname, lastname, username):
    conn = mysql.connector.connect(**database_config, database=database_name)
    cur = conn.cursor()

    SQL_QUERY = """
        INSERT INTO customers(CID, FIRSTNAME, LASTNAME, USERNAME) VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            FIRSTNAME = %s,
            LASTNAME = %s,
            USERNAME = %s
    """

    cur.execute(SQL_QUERY,(cid, firstname, lastname, username, firstname, lastname, username))

    conn.commit()
    cur.close()
    conn.close()

    return True


def add_to_basket(cid, product_id, quantity):
    conn = mysql.connector.connect(**database_config, database=database_name)
    cur = conn.cursor()

    SQL_PRICE_QUERY = "SELECT PRICE FROM products WHERE PRODUCT_ID = %s"

    cur.execute(SQL_PRICE_QUERY, (product_id,))
    result = cur.fetchone()
    if result is None:
        cur.close()
        conn.close()
        return False

    unit_price = result[0]

    SQL_QUERY = """
        INSERT INTO order_basket (CID, PRODUCT_ID, QUANTITY, UNIT_PRICE) VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            QUANTITY = QUANTITY + %s,
            UNIT_PRICE = %s
    """

    cur.execute(SQL_QUERY,(cid, product_id, quantity, unit_price, quantity, unit_price))
    conn.commit()
    cur.close()
    conn.close()
    return True


def get_customer_basket(cid):
    conn = mysql.connector.connect(**database_config, database=database_name)
    cur = conn.cursor(dictionary=True)

    SQL_QUERY = """
        SELECT order_basket.PRODUCT_ID, products.NAME, order_basket.QUANTITY, order_basket.UNIT_PRICE FROM order_basket
        INNER JOIN products
            ON order_basket.PRODUCT_ID = products.PRODUCT_ID WHERE order_basket.CID = %s
        ORDER BY order_basket.ORDER_BASKET
    """

    cur.execute(SQL_QUERY, (cid,))
    basket = cur.fetchall()
    cur.close()
    conn.close()
    return basket


def increase_basket_quantity(cid, product_id):
    conn = mysql.connector.connect(**database_config, database=database_name)
    cur = conn.cursor()

    SQL_QUERY = """
        UPDATE order_basket
        SET QUANTITY = QUANTITY + 1 WHERE CID = %s AND PRODUCT_ID = %s
    """

    cur.execute(SQL_QUERY, (cid, product_id))
    changed = cur.rowcount > 0
    conn.commit()
    cur.close()
    conn.close()
    return changed


def decrease_basket_quantity(cid, product_id):
    conn = mysql.connector.connect(**database_config, database=database_name)
    cur = conn.cursor()

    SQL_QUERY = """
        UPDATE order_basket
        SET QUANTITY = QUANTITY - 1 WHERE CID = %s AND PRODUCT_ID = %s AND QUANTITY > 1
    """

    cur.execute(SQL_QUERY, (cid, product_id))
    changed = cur.rowcount > 0
    conn.commit()
    cur.close()
    conn.close()
    return changed


def remove_from_basket(cid, product_id):
    conn = mysql.connector.connect(**database_config, database=database_name)
    cur = conn.cursor()

    SQL_QUERY = "DELETE FROM order_basket WHERE CID = %s AND PRODUCT_ID = %s"

    cur.execute(SQL_QUERY, (cid, product_id))
    deleted = cur.rowcount > 0
    conn.commit()
    cur.close()
    conn.close()
    return deleted


def update_customer_phone(cid, phone):
    conn = mysql.connector.connect(**database_config, database=database_name)
    cur = conn.cursor()

    SQL_QUERY = "UPDATE customers SET PHONE = %s WHERE CID = %s"

    cur.execute(SQL_QUERY, (phone, cid))
    conn.commit()
    cur.close()
    conn.close()
    return True


def get_customer_by_id(cid):
    conn = mysql.connector.connect(**database_config, database=database_name)
    cur = conn.cursor(dictionary=True)

    SQL_QUERY = "SELECT CID, FIRSTNAME, LASTNAME, PHONE, USERNAME FROM customers WHERE CID = %s"

    cur.execute(SQL_QUERY,(cid,))
    customer = cur.fetchone()
    cur.close()
    conn.close()
    return customer


def search_products_by_name(product_name):
    conn = mysql.connector.connect(**database_config, database=database_name)
    cur = conn.cursor(dictionary=True)

    SQL_QUERY = "SELECT PRODUCT_ID, NAME FROM products WHERE NAME LIKE %s AND products.IS_ACTIVE = 'YES' ORDER BY NAME"

    search_value = f"%{product_name}%"

    cur.execute(SQL_QUERY,(search_value,))
    products = cur.fetchall()
    cur.close()
    conn.close()
    return products


def search_products_by_part_number(part_number):
    conn = mysql.connector.connect(**database_config, database=database_name)
    cur = conn.cursor(dictionary=True)

    SQL_QUERY = "SELECT PRODUCT_ID, NAME, PART_NUMBER FROM products WHERE PART_NUMBER LIKE %s AND products.IS_ACTIVE = 'YES' ORDER BY NAME"

    search_value = f"%{part_number}%"

    cur.execute(SQL_QUERY,(search_value,))
    products = cur.fetchall()
    cur.close()
    conn.close()
    return products


def block_customer(cid):
    conn = mysql.connector.connect(**database_config,database=database_name)
    cur = conn.cursor()

    SQL_QUERY = "UPDATE customers SET IS_BLOCKED = 'YES' WHERE CID = %s"

    cur.execute(SQL_QUERY, (cid,))
    changed = cur.rowcount > 0
    conn.commit()
    cur.close()
    conn.close()
    return changed


def unblock_customer(cid):
    conn = mysql.connector.connect(**database_config,database=database_name)
    cur = conn.cursor()

    SQL_QUERY = "UPDATE customers SET IS_BLOCKED = 'NO' WHERE CID = %s"

    cur.execute(SQL_QUERY, (cid,))
    changed = cur.rowcount > 0
    conn.commit()
    cur.close()
    conn.close()
    return changed


def get_blocked_customers():
    conn = mysql.connector.connect(**database_config, database=database_name)
    cur = conn.cursor()

    SQL_QUERY = "SELECT CID FROM customers WHERE IS_BLOCKED = 'YES'"

    cur.execute(SQL_QUERY)
    results = cur.fetchall()
    cur.close()
    conn.close()
    blocked_customers = []
    for row in results:
        blocked_customers.append(row[0])
    return blocked_customers


def get_customer_spam_data(cid):
    conn = mysql.connector.connect(**database_config,database=database_name)
    cur = conn.cursor(dictionary=True)

    SQL_QUERY = "SELECT SPAM_SCORE, LAST_MESSAGE, EXPIRE_SPAM FROM customers WHERE CID = %s"

    cur.execute(SQL_QUERY, (cid,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result


def update_customer_spam_data(cid, spam_score, last_message, expire_spam):
    conn = mysql.connector.connect(**database_config,database=database_name)
    cur = conn.cursor()

    SQL_QUERY = "UPDATE customers SET SPAM_SCORE = %s, LAST_MESSAGE = %s, EXPIRE_SPAM = %s WHERE CID = %s"

    cur.execute(SQL_QUERY,(spam_score,last_message,expire_spam,cid))
    conn.commit()
    cur.close()
    conn.close()
    return True

def get_admin_role(admin_cid):
    conn = mysql.connector.connect(**database_config,database=database_name)
    cur = conn.cursor()

    SQL_QUERY = "SELECT ROLE FROM admins WHERE ADMIN_CID = %s"

    cur.execute(SQL_QUERY, (admin_cid,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    if result is None:
        return None
    return result[0]


def is_admin(admin_cid):
    conn = mysql.connector.connect(**database_config,database=database_name)
    cur = conn.cursor()

    SQL_QUERY = "SELECT ADMIN_CID FROM admins WHERE ADMIN_CID = %s LIMIT 1"

    cur.execute(SQL_QUERY, (admin_cid,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result is not None


def is_owner(admin_cid):
    return get_admin_role(admin_cid) == "OWNER"


def insert_service_data(name,description):
    conn = mysql.connector.connect(**database_config,database=database_name)
    cur = conn.cursor()

    SQL_QUERY = "INSERT INTO services(NAME, DESCRIPTION) VALUES (%s, %s)"

    cur.execute(SQL_QUERY,(name,description,))
    conn.commit()
    cur.close()
    conn.close()
    return True


def get_all_services():
    conn = mysql.connector.connect(**database_config,database=database_name)
    cur = conn.cursor(dictionary=True)

    SQL_QUERY = "SELECT SERVICE_ID, NAME FROM services ORDER BY SERVICE_ID"

    cur.execute(SQL_QUERY)
    services = cur.fetchall()
    cur.close()
    conn.close()
    return services


def get_service_by_name(service_name):
    conn = mysql.connector.connect(**database_config,database=database_name)
    cur = conn.cursor(dictionary=True)

    SQL_QUERY = "SELECT SERVICE_ID, NAME, DESCRIPTION FROM services WHERE NAME = %s LIMIT 1"

    cur.execute(SQL_QUERY,(service_name,))
    service = cur.fetchone()
    cur.close()
    conn.close()
    return service



if __name__ == "__main__":
    insert_admin_data(5890677297, "Sepehr", None, "JustCallMeAgent", "OWNER")

    insert_category_data("Server")
    insert_category_data("HDD")
    insert_category_data("SSD")

    insert_product_data(
        1,
        "HPE PROLIANT DL380 GEN10 SERVER 8SFF",
        "P50751-B21",
        "HPE",
        """سرور HPE ProLiant DL380 Gen10 8SFF یکی از قدرتمندترین...""",
        "AgACAgQAAxkBAAN7al9rHcwZg560Zw7p4SDCsg4cLEYAApwNaxuzvflSjhudVNIP1foBAAMCAAN5AAM9BA",
        "AgACAgQAAxkBAAN8al9rQyAt0BgJhZ1KmuLFB867f_MAAp4NaxuzvflSqo-uMwUSSPwBAAMCAAN5AAM9BA",
        "AgACAgQAAxkBAAN9al9rS5OvOghdFbfwTrzO3DwxkbYAAp8NaxuzvflSatVKH64m8BYBAAMCAAN5AAM9BA",
        0,
        "https://toranjco.net/product/amd-ryzen-5-7600x/",
        5890677297
    )
#
#     insert_product_data(
#         2,
#         1,
#         0,
#         "HPE PROLIANT DL380 GEN 10 SERVER 12LFF",
#         "نسل سرور = G10",
#         "شگل ظاهری = dl/رکمونت",
#         "P20172-B21",
#         "HPE",
#         "DL380",
#         """
#                         سرور HPE ProLiant DL380 Gen10 12LFF یکی از قدرتمندترین و پرکاربردترین سرورهای رکمونت نسل دهم اچ‌پی است که برای پاسخگویی به نیازهای متنوع سازمانی، دیتاسنترها و زیرساخت‌های فناوری اطلاعات طراحی شده است. این سرور با بهره‌گیری از معماری پیشرفته پردازشی، قابلیت ارتقاء گسترده و امکانات مدیریتی حرفه‌ای، بستری پایدار و مطمئن برای اجرای بارهای کاری سنگین فراهم می‌کند.
#
# نسخه 12LFF این سرور دارای 12 جایگاه هارد 3.5 اینچی در جلو است که تعادل مناسبی میان ظرفیت بالای ذخیره‌سازی، عملکرد پردازشی قوی و فضای اشغالی در رک ایجاد می‌کند. به همین دلیل یکی از محبوب‌ترین پیکربندی‌های DL380 Gen10 در میان سازمان‌ها و شرکت‌های در حال توسعه به شمار می‌رود.
# """ ,
#         "AgACAgQAAxkBAAN-al9r6vov66J7rSOXp96eF_FysTsAAqANaxuzvflSMre2nbV8WD4BAAMCAAN5AAM9BA",
#         "AgACAgQAAxkBAAN8al9rQyAt0BgJhZ1KmuLFB867f_MAAp4NaxuzvflSqo-uMwUSSPwBAAMCAAN5AAM9BA",
#         "AgACAgQAAxkBAAN9al9rS5OvOghdFbfwTrzO3DwxkbYAAp8NaxuzvflSatVKH64m8BYBAAMCAAN5AAM9BA",
#         0
#     )
#
#     insert_product_data(
#         3,
#         1,
#         0,
#         "HPE PROLIANT DL380 GEN 10 plus SERVER 8SFF",
#         "نسل سرور = G10",
#         "شکل ظاهری = dl/رکمونت",
#         "P55246-B21",
#         "HPE",
#         "DL380",
#         """
#         سرور HPE ProLiant DL380 Gen10 Plus جدیدترین عضو خانواده HPE ProLiant DL380 است که برای پاسخگویی به نیازهای متنوع و حساس سازمانی طراحی شده است. این نسخه «Gen10 Plus» بر پایه معماری موفق نسل دهم HPE ساخته شده اما از سخت‌افزارهای جدیدتر و سریع‌تری بهره می‌برد. مهم‌ترین تغییرات شامل پشتیبانی از پردازنده‌های نسل سوم Intel Xeon Scalable (معروف به Ice Lake)، حافظه DDR4 سریع‌تر و رابط‌های PCIe نسخه چهارم است. این ارتقاءهای سخت‌افزاری باعث می‌شوند که سرور DL380 Gen10 Plus توان پردازشی و پهنای‌باند بیشتری را ارائه کرده و برای وظایف سنگین از قبیل مجازی‌سازی، پردازش ابری، تحلیل‌های Big Data و پایگاه‌های داده سازمانی بسیار مناسب باشد.
#
# همچنان ثبات و قابلیت اطمینان بالای سری DL380 حفظ شده است؛ این سرور با اجزای ماژولار و پیکربندی منعطف، امکان توسعه آینده را بدون نیاز به جایگزینی کل پلتفرم فراهم می‌کند.
#         """,
#         "AgACAgQAAxkBAAN-al9r6vov66J7rSOXp96eF_FysTsAAqANaxuzvflSMre2nbV8WD4BAAMCAAN5AAM9BA",
#         "AgACAgQAAxkBAAOBal9s6JAOdgbIW67LII7QcKBYE20AAqMNaxuzvflS2r4lHsExY0wBAAMCAAN5AAM9BA",
#         "AgACAgQAAxkBAAN9al9rS5OvOghdFbfwTrzO3DwxkbYAAp8NaxuzvflSatVKH64m8BYBAAMCAAN5AAM9BA",
#         0
#     )
#
#     insert_product_data(
#         4,
#         1,
#         0,
#         "HPE PROLIANT DL380 GEN 11 SERVER 8SFF",
#         "نسل سرور = G11",
#         "شکل ظاهری = dl/رکموند",
#         "P52560-421",
#         "HPE",
#         "DL380",
#         """
#         سرور HPE ProLiant DL380 Gen11 8SFF نسل جدیدی از سرورهای رکمونت 2U اچ‌پی است که برای پشتیبانی از بارهای کاری متنوع در محیط‌های سازمانی، ابری و مراکز داده طراحی شده است. این سرور با ترکیب توان پردازشی بسیار بالا و قابلیت‌های امنیتی پیشرفته، بستر امن و مطمئنی را برای اجرای برنامه‌های مهم سازمانی فراهم می‌آورد. هِدِر (Heiser) این سرور نسبت به نسل قبل، بهبودهای چشمگیری در پهنای باند حافظه و سرعت ارتباطات ورودی/خروجی دارد و از فناوری‌های نوین پردازش مانند تسریع‌دهنده‌های هوش مصنوعی و کارت‌های GPU نیز پشتیبانی می‌کند.
#
# نسخه 8SFF این سرور دارای ۸ جایگاه هارد ۲.۵ اینچی در پنل جلویی است که امکان نصب هارد و SSD از انواع مختلف را می‌دهد. این چیدمان بهینه به سازمان‌ها اجازه می‌دهد تا در فضای رک کم، توان ذخیره‌سازی بالایی فراهم کنند و از مزایای سرعت و مقیاس‌پذیری فناوری‌های NVMe بهره‌مند شوند.
#         """,
#         "AgACAgQAAxkBAAOCal9tRcmOwg3p0zfe5Z1SuOb39ckAAqQNaxuzvflSkB9WrXwXJ4cBAAMCAAN5AAM9BA",
#         "AgACAgQAAxkBAAODal9tZ--JL0G2gzUo99eY5P-yj4wAAqUNaxuzvflSM-w38-nXGk0BAAMCAAN5AAM9BA",
#         "AgACAgQAAxkBAAOEal9tciv57_Bk7DIQXQS3FJW_epwAAqYNaxuzvflShWUYc870-ikBAAMCAAN5AAM9BA",
#         0
#     )
#
#     insert_product_data(
#         5,
#         1,
#         0,
#         "HPE ProLiant DL380 Gen11 Server 12LFF",
#         "نسل سرور = G11",
#         "شکل ظاهری = dl/رکموند",
#         "P52562-421",
#         "HPE",
#         "DL380",
#         """
#         سرور HPE ProLiant DL380 Gen11 12LFF نسل جدیدی از سرورهای رکمونت دو سوکته شرکت اچ‌پی است که برای ارائه عملکرد بالا و قابلیت اطمینان در پردازش‌های سنگین سازمانی طراحی شده است. این سرور در فرم‌فاکتور ۲U (دو یونیت رک) عرضه می‌شود و با پشتیبانی از حداکثر ۱۲ درایو ۳.۵ اینچی هات‌پلاگ، تعادل مناسبی بین ظرفیت ذخیره‌سازی و فضای رک ایجاد می‌کند. DL380 Gen11 با معماری بهبودیافته خود نسبت به نسل‌های پیشین، امکان اجرای بارهای کاری گسترده‌ای مانند مجازی‌سازی، پایگاه داده، پردازش ابری و ماشین‌های مجازی را با کارایی بالاتر فراهم می‌سازد.
#
# ارتقاء به پردازنده‌های نسل چهارم و پنجم Intel Xeon Scalable و حافظه DDR5، همراه با فناوری‌های امنیتی سخت‌افزاری، این سرور را به گزینه‌ای ایده‌آل برای مراکز داده و شرکت‌های متوسط تا بزرگ تبدیل کرده است.
#         """,
#         "AgACAgQAAxkBAAOCal9tRcmOwg3p0zfe5Z1SuOb39ckAAqQNaxuzvflSkB9WrXwXJ4cBAAMCAAN5AAM9BA",
#         "AgACAgQAAxkBAAODal9tZ--JL0G2gzUo99eY5P-yj4wAAqUNaxuzvflSM-w38-nXGk0BAAMCAAN5AAM9BA",
#         "AgACAgQAAxkBAAOEal9tciv57_Bk7DIQXQS3FJW_epwAAqYNaxuzvflShWUYc870-ikBAAMCAAN5AAM9BA",
#         0
#     )
#
#     insert_product_data(
#         6,
#         1,
#         0,
#         "HPE PROLIANT DL380 GEN 12 SERVER 8SFF",
#         "نسل سرور = G12",
#         "شکل ظاهری = dl/رکموند",
#         "P73282-B21",
#         "HPE",
#         "DL380",
#         """
#         سرور HPE ProLiant DL380 Gen12 8SFF یکی از قدرتمندترین و جدیدترین سرورهای رکمونت 2U اچ‌پی است که برای پاسخگویی به نیازهای پیچیده و متنوع سازمان‌ها و مراکز داده مدرن طراحی شده است. این سرور با بهره‌گیری از معماری پیشرفته، قابلیت ارتقاء گسترده و امکانات مدیریتی نسل جدید، بستری پایدار و مطمئن برای اجرای بارهای کاری سنگین فراهم می‌کند.
#
# نسخه 8SFF این سرور دارای ۸ جایگاه هارد ۲.۵ اینچی در جلوی رک است که تعادل مناسبی میان سرعت ذخیره‌سازی، عملکرد پردازشی و اشغال فضای رک ایجاد می‌کند. به همین دلیل این پیکربندی در میان شرکت‌های در حال توسعه و دیتاسنترها بسیار محبوب است.
#         """,
#         "AgACAgQAAxkBAAOCal9tRcmOwg3p0zfe5Z1SuOb39ckAAqQNaxuzvflSkB9WrXwXJ4cBAAMCAAN5AAM9BA",
#         "AgACAgQAAxkBAAOIal9uSusmgYZinWiKXiummj-HG74AAqcNaxuzvflSAAFMDFhxdEUGAQADAgADeQADPQQ",
#         "AgACAgQAAxkBAAODal9tZ--JL0G2gzUo99eY5P-yj4wAAqUNaxuzvflSM-w38-nXGk0BAAMCAAN5AAM9BA",
#         0
#     )
#
#
#
# خدمات طراحی شبکه (Network Design Services)
# یک شبکه سازمانی کارآمد، پیش از اجرا و راه‌اندازی، نیازمند طراحی اصولی و برنامه‌ریزی دقیق است. طراحی غیراستاندارد شبکه می‌تواند منجر به ایجاد گلوگاه‌های ارتباطی، کاهش سرعت دسترسی به منابع، افزایش ریسک‌های امنیتی و تحمیل هزینه‌های اضافی در آینده شود.
#
# طراحی شبکه، فرآیندی فراتر از انتخاب تجهیزات و تعیین مسیرهای ارتباطی است. در این فرآیند، تمامی نیازهای عملیاتی سازمان، ساختار فیزیکی محیط، ظرفیت مورد نیاز، الزامات امنیتی و برنامه توسعه آینده مورد بررسی قرار می‌گیرند تا زیرساختی پایدار، ایمن و توسعه‌پذیر ایجاد شود.
#
# برای هماهنگ سازی با آیدی زیر تماس حاصل کنید:
# @JustCallMeAgent

#     insert_service_data("خدمات طراحی شبکه", """
#     خدمات طراحی شبکه (Network Design Services)
#     یک شبکه سازمانی کارآمد، پیش از اجرا و راه‌اندازی، نیازمند طراحی اصولی و برنامه‌ریزی دقیق است. طراحی غیراستاندارد شبکه می‌تواند منجر به ایجاد گلوگاه‌های ارتباطی، کاهش سرعت دسترسی به منابع، افزایش ریسک‌های امنیتی و تحمیل هزینه‌های اضافی در آینده شود.
#
# طراحی شبکه، فرآیندی فراتر از انتخاب تجهیزات و تعیین مسیرهای ارتباطی است. در این فرآیند، تمامی نیازهای عملیاتی سازمان، ساختار فیزیکی محیط، ظرفیت مورد نیاز، الزامات امنیتی و برنامه توسعه آینده مورد بررسی قرار می‌گیرند تا زیرساختی پایدار، ایمن و توسعه‌پذیر ایجاد شود.
#
# برای هماهنگ سازی با آیدی زیر تماس حاصل کنید:
#     @JustCallMeAgent
#     """)


