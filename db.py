import mysql.connector


def connect_to_database():
    return mysql.connector.connect(
        host="localhost",
        user="sigma",
        password="password",
        database="sigma"
    )


def get_all_uids(cursor, tables):
    all_uids = {}
    for table in tables:
        cursor.execute(f"SELECT uid FROM {table}")
        uids = cursor.fetchall()
        for uid in uids:
            uid = uid[0]
            if uid in all_uids:
                all_uids[uid].append(table)
            else:
                all_uids[uid] = [table]
    return all_uids


def delete_duplicate_uids(cursor, tables, all_uids):
    for uid, table_list in all_uids.items():
        if len(table_list) > 1:
            for table in table_list[1:]:
                cursor.execute(f"DELETE FROM {table} WHERE uid = %s", (uid,))


def main():
    tables = [f"sitemap_prod_us_en_{i}" for i in range(1, 15)]

    db_connection = connect_to_database()
    cursor = db_connection.cursor()

    all_uids = get_all_uids(cursor, tables)
    delete_duplicate_uids(cursor, tables, all_uids)

    db_connection.commit()
    cursor.close()
    db_connection.close()


if __name__ == "__main__":
    main()
