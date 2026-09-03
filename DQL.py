import mysql.connector
from config import *

def get_customer_data(customer_id):
    conn = mysql.connector.connection.MySQLConnection(**database_config, database=database)
    cur = conn.cursor(dictionary=True)
    SQL_QUERY = "SELECT * FROM CUSTOMERS WHERE customer_id = %s"
    cur.execute(SQL_QUERY, (customer_id,))
    # result = cur.fetchall()
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result

if __name__ == "__main__":
    deta = get_customer_data(1)
    print(deta)
