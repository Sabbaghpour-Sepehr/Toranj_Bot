import mysql.connector
from config import *

def create_database(database_name):
    conn = mysql.connector.connection.MySQLConnection(**database_config)
    cur = conn.cursor()

    cur.execute(f"DROP DATABASE IF EXISTS {database_name}")
    cur.execute(f"CREATE DATABASE IF NOT EXISTS {database_name};")

    conn.commit()
    cur.close()
    conn.close()

    print("done")


def create_table_customers():
    conn = mysql.connector.connection.MySQLConnection(**database_config, database= database_name)
    cur = conn.cursor()

    cur.execute(f"""
CREATE TABLE customers (
	`CID`               BIGINT UNSIGNED NOT NULL PRIMARY KEY,
	`FIRSTNAME`         VARCHAR(100) NOT NULL,
	`LASTNAME`          VARCHAR(100),
	`PHONE`             VARCHAR(30),
	`USERNAME`          VARCHAR(100),
	`IS_BLOCKED`        ENUM('YES', 'NO') DEFAULT 'NO',
    `EXPIRE_SPAM`       DATETIME NULL,
	`SPAM_SCORE`        TINYINT UNSIGNED NOT NULL DEFAULT 0,
	`LAST_MESSAGE`      DATETIME NULL,
	`CREATED_AT`        DATETIME DEFAULT CURRENT_TIMESTAMP,
    `LAST_UPDATE`       DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);""")

    conn.commit()
    cur.close()
    conn.close()

    print("table customer successfully created")


def create_table_admins():
    conn = mysql.connector.connection.MySQLConnection(**database_config, database= database_name)
    cur = conn.cursor()

    cur.execute(f"""
CREATE TABLE admins (
	`ADMIN_CID`         BIGINT UNSIGNED PRIMARY KEY,
	`FIRST_NAME`        VARCHAR(150) NOT NULL,
	`LAST_NAME`         VARCHAR(150) NULL,
	`USERNAME`          VARCHAR(100) NOT NULL UNIQUE,
	`ROLE`              ENUM('OWNER', 'ADMIN') NOT NULL DEFAULT 'ADMIN',
	`CREATED_AT`        DATETIME DEFAULT CURRENT_TIMESTAMP,
	`LAST_UPDATE`       DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);""")

    conn.commit()
    cur.close()
    conn.close()

    print("table Admin created")


def create_table_categories():
    conn = mysql.connector.connection.MySQLConnection(**database_config, database= database_name)
    cur = conn.cursor()

    cur.execute(f"""
CREATE TABLE categories (
	`CATEGORY_ID`       BIGINT UNSIGNED AUTO_INCREMENT,
	`NAME`              VARCHAR(150) NOT NULL,
	`CREATED_AT`        DATETIME DEFAULT CURRENT_TIMESTAMP,
	`LAST_UPDATE`       DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	PRIMARY KEY (CATEGORY_ID)
);
""")

    print("table categories successfully created")


    conn.commit()
    cur.close()
    conn.close()

def create_table_products():
    conn = mysql.connector.connection.MySQLConnection(**database_config, database= database_name)
    cur = conn.cursor()

    cur.execute(f"""
CREATE TABLE products (
	`PRODUCT_ID`            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
	`CATEGORY_ID`           BIGINT UNSIGNED NULL,
	`NAME`                  VARCHAR(100) NOT NULL,
	`PART_NUMBER`           VARCHAR(50),
	`BRAND`                 VARCHAR(50),
	`DESCRIPTION`           TEXT,
	`PIC1`                  VARCHAR(150),
    `PIC2`                  VARCHAR(150),
	`PIC3`                  VARCHAR(150),
	`PRICE`                 DECIMAL(15,0) DEFAULT 0,
	`LINK`                  VARCHAR(500),
	`IS_ACTIVE`             ENUM('YES', 'NO') DEFAULT 'YES',
	`ADMIN_CID`             BIGINT UNSIGNED NULL,
	`CREATED_AT`            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	`LAST_UPDATE`           TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	PRIMARY KEY (PRODUCT_ID),
    FOREIGN KEY (CATEGORY_ID)
    REFERENCES categories(CATEGORY_ID)
    ON DELETE SET NULL
    ON UPDATE CASCADE,
    FOREIGN KEY (`ADMIN_CID`)
    REFERENCES admins(`ADMIN_CID`)
    ON DELETE SET NULL
    ON UPDATE CASCADE
);
""")

    print("table products successfully created")

    conn.commit()
    cur.close()
    conn.close()


def create_table_order_basket():
    conn = mysql.connector.connection.MySQLConnection(**database_config, database= database_name)
    cur = conn.cursor()

    cur.execute(f"""
CREATE TABLE order_basket (
    `CID`                   BIGINT UNSIGNED NOT NULL,
	`ORDER_BASKET`          BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
	`PRODUCT_ID`            BIGINT UNSIGNED NOT NULL,
	`QUANTITY`              INT UNSIGNED NOT NULL DEFAULT 1,
	`UNIT_PRICE`            DECIMAL(15,0) NOT NULL DEFAULT 0,
	`CREATED_AT`            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	`LAST_UPDATE`           TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	UNIQUE (`CID`, `PRODUCT_ID`),
	FOREIGN KEY (`PRODUCT_ID`) REFERENCES products(`PRODUCT_ID`),
	FOREIGN KEY (`CID`) REFERENCES customers(`CID`)
);
""")

    print("table basket successfully created")

    conn.commit()
    cur.close()
    conn.close()


def create_table_services():
    conn = mysql.connector.connection.MySQLConnection(**database_config, database= database_name)
    cur = conn.cursor()

    cur.execute("""
CREATE TABLE services(
    `SERVICE_ID`        BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    `NAME`              VARCHAR(150) NOT NULL,
    `DESCRIPTION`       TEXT,
    `LINK`              TEXT,
    `CREATED_AT`        DATETIME DEFAULT CURRENT_TIMESTAMP,
    `LAST_UPDATE`       DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
""")
    print("table services successfully created")

    conn.commit()
    cur.close()
    conn.close()



if __name__ == "__main__":
    create_database(database_name)
    create_table_customers()
    create_table_admins()
    create_table_categories()
    create_table_products()
    create_table_order_basket()
    create_table_services()
