import sqlite3
from datetime import date

DB_PATH = "boba_pos.db"


def get_connection(): # function for opening the database file so python can read and write to it
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def execute(query, params=()): # change data
    conn = get_connection()
    cursor = conn.cursor() # creates tool for executing commands
    cursor.execute(query, params)
    conn.commit()
    conn.close()
    return cursor


def fetchall(query, params=()): # reading data but all
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    result = cursor.fetchall()
    conn.close()
    return result


def fetchone(query, params=()): # reading data but only one
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    result = cursor.fetchone()
    conn.close()
    return result



def create_tables():
    conn = get_connection()
    cursor = conn.cursor()
    # uses executescript since need to run multiple commands at once
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS Users (
            id          INTEGER PRIMARY KEY,
            role        TEXT    NOT NULL,
            access_code TEXT
        );

        CREATE TABLE IF NOT EXISTS Items (
            item_id  INTEGER PRIMARY KEY AUTOINCREMENT,
            name     TEXT    NOT NULL,
            price    REAL    NOT NULL
        );

        CREATE TABLE IF NOT EXISTS Subcategories (
            subcategory_id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id        INTEGER NOT NULL,
            name           TEXT    NOT NULL,
            price          REAL    NOT NULL DEFAULT 0,
            FOREIGN KEY (item_id) REFERENCES Items(item_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS Orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            date     TEXT    NOT NULL,
            price    REAL    NOT NULL
        );

        CREATE TABLE IF NOT EXISTS Ordered_Items (
            ordered_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id        INTEGER NOT NULL,
            item_id         INTEGER NOT NULL,
            FOREIGN KEY (order_id) REFERENCES Orders(order_id) ON DELETE CASCADE,
            FOREIGN KEY (item_id)  REFERENCES Items(item_id)
        );

        CREATE TABLE IF NOT EXISTS Ordered_Items_Subcategories (
            ordered_item_id INTEGER NOT NULL,
            subcategory_id  INTEGER NOT NULL,
            PRIMARY KEY (ordered_item_id, subcategory_id),
            FOREIGN KEY (ordered_item_id) REFERENCES Ordered_Items(ordered_item_id) ON DELETE CASCADE,
            FOREIGN KEY (subcategory_id)  REFERENCES Subcategories(subcategory_id)
        );

        CREATE TABLE IF NOT EXISTS Ingredients (
            ingredient_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT    NOT NULL,
            current_stock REAL    NOT NULL DEFAULT 0,
            reorder_level REAL    NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS Items_Ingredients (
            item_id       INTEGER NOT NULL,
            ingredient_id INTEGER NOT NULL,
            quantity_used REAL    NOT NULL,
            PRIMARY KEY (item_id, ingredient_id),
            FOREIGN KEY (item_id)       REFERENCES Items(item_id) ON DELETE CASCADE,
            FOREIGN KEY (ingredient_id) REFERENCES Ingredients(ingredient_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS Subcategories_Ingredients (
            subcategory_id INTEGER NOT NULL,
            ingredient_id  INTEGER NOT NULL,
            quantity_used  REAL    NOT NULL,
            PRIMARY KEY (subcategory_id, ingredient_id),
            FOREIGN KEY (subcategory_id)  REFERENCES Subcategories(subcategory_id) ON DELETE CASCADE,
            FOREIGN KEY (ingredient_id)   REFERENCES Ingredients(ingredient_id) ON DELETE CASCADE
        );
    """)

    # Seed the two user roles if not already present
    cursor.execute("SELECT COUNT(*) FROM Users") # count how many rows, if 0 then add 2 to that table
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO Users (id, role, access_code) VALUES (1, 'manager', NULL)")
        cursor.execute("INSERT INTO Users (id, role, access_code) VALUES (2, 'employee', NULL)")

    conn.commit()
    conn.close()


# Authentication

def is_first_launch(): # checks if Null then true, main.py uses this
    row = fetchone("SELECT access_code FROM Users WHERE id = 1")
    return row is None or row[0] is None


def set_access_codes(manager_code, employee_code):
    execute("UPDATE Users SET access_code = ? WHERE id = 1", (manager_code,))
    execute("UPDATE Users SET access_code = ? WHERE id = 2", (employee_code,))


def check_login(code): # login.py runs this function, it returns 'manager', 'employee', or None.
    row = fetchone("SELECT role FROM Users WHERE access_code = ?", (code,)) # runs an SQL query to select the role for the matching access code
    if row is None:
        return None
    elif row[0] == "manager":
        return "manager"
    elif row[0] == "employee":
        return "employee"
    


# Items

def get_all_items(): # used in order screen to display menu list
    return fetchall("SELECT item_id, name, price FROM Items ORDER BY name")


def search_items(query): # filters by name using LIKE
    return fetchall(
        "SELECT item_id, name, price FROM Items WHERE name LIKE ? ORDER BY name",
        (f"%{query}%",)
    )


def get_subcategories(item_id): # gets all subcategories that belong to an item
    return fetchall(
        "SELECT subcategory_id, name, price FROM Subcategories WHERE item_id = ?",
        (item_id,)
    )


def add_item(name, price):
    cursor = execute("INSERT INTO Items (name, price) VALUES (?, ?)", (name, price))
    return cursor.lastrowid # returns ID immediately


def update_item(item_id, name, price):
    execute("UPDATE Items SET name = ?, price = ? WHERE item_id = ?", (name, price, item_id))


def delete_item(item_id):
    execute("DELETE FROM Items WHERE item_id = ?", (item_id,))


def add_subcategory(item_id, name, price):
    cursor = execute(
        "INSERT INTO Subcategories (item_id, name, price) VALUES (?, ?, ?)",
        (item_id, name, price)
    )
    return cursor.lastrowid


def delete_subcategory(subcategory_id):
    execute("DELETE FROM Subcategories WHERE subcategory_id = ?", (subcategory_id,))


def get_all_ingredients():
    return fetchall("SELECT ingredient_id, name, current_stock, reorder_level FROM Ingredients ORDER BY name")


def get_item_ingredients(item_id):
    return fetchall(
        """SELECT i.ingredient_id, i.name, ii.quantity_used
           FROM Items_Ingredients ii
           JOIN Ingredients i ON i.ingredient_id = ii.ingredient_id
           WHERE ii.item_id = ?""",
        (item_id,)
    )


def set_item_ingredient(item_id, ingredient_id, quantity_used):
    delete_item_ingredient(item_id, ingredient_id)  # remove existing link if there is one
    execute(
        "INSERT INTO Items_Ingredients (item_id, ingredient_id, quantity_used) VALUES (?, ?, ?)",
        (item_id, ingredient_id, quantity_used)
    )


def delete_item_ingredient(item_id, ingredient_id):
    execute(
        "DELETE FROM Items_Ingredients WHERE item_id = ? AND ingredient_id = ?",
        (item_id, ingredient_id)
    )


# Orders

def create_order(total_price):
    cursor = execute(
        "INSERT INTO Orders (date, price) VALUES (?, ?)",
        (date.today().isoformat(), total_price)
    )
    return cursor.lastrowid


def add_ordered_item(order_id, item_id):
    cursor = execute(
        "INSERT INTO Ordered_Items (order_id, item_id) VALUES (?, ?)",
        (order_id, item_id)
    )
    return cursor.lastrowid


def add_ordered_item_subcategory(ordered_item_id, subcategory_id):
    execute(
        "INSERT INTO Ordered_Items_Subcategories (ordered_item_id, subcategory_id) VALUES (?, ?)",
        (ordered_item_id, subcategory_id)
    )


def deduct_inventory(item_id):
    rows = fetchall(
        "SELECT ingredient_id, quantity_used FROM Items_Ingredients WHERE item_id = ?",
        (item_id,)
    )
    for row in rows:
        ingredient_id = row[0]
        quantity = row[1]
        execute(
            "UPDATE Ingredients SET current_stock = current_stock - ? WHERE ingredient_id = ?",
            (quantity, ingredient_id)
        )


def get_low_stock_ingredients():
    return fetchall(
        "SELECT name FROM Ingredients WHERE current_stock <= reorder_level"
    )


# Inventory

def add_ingredient(name, current_stock, reorder_level):
    execute(
        "INSERT INTO Ingredients (name, current_stock, reorder_level) VALUES (?, ?, ?)",
        (name, current_stock, reorder_level)
    )


def update_ingredient(ingredient_id, name, current_stock, reorder_level):
    execute(
        "UPDATE Ingredients SET name = ?, current_stock = ?, reorder_level = ? WHERE ingredient_id = ?",
        (name, current_stock, reorder_level, ingredient_id)
    )


def delete_ingredient(ingredient_id):
    execute("DELETE FROM Ingredients WHERE ingredient_id = ?", (ingredient_id,))


# Reports

def get_revenue_by_item():
    # get item name -> count how many times it was ordered -> multiply by price to get revenue
    # start from ordered items table -> connect to Items table to get name and price -> connect to Orders table to get date
    # only include from last 30 days -> group rows by same item to count
    return fetchall("""
        SELECT i.name,
               COUNT(oi.ordered_item_id) * i.price AS revenue
        FROM Ordered_Items oi
        JOIN Items i ON i.item_id = oi.item_id
        JOIN Orders o ON o.order_id = oi.order_id
        WHERE o.date >= date('now', '-30 days')
        GROUP BY i.item_id
        ORDER BY revenue DESC
    """)


def get_revenue_by_day():
    return fetchall("""
        SELECT date, SUM(price) AS revenue
        FROM Orders
        WHERE date >= date('now', '-30 days')
        GROUP BY date
        ORDER BY date ASC
    """)
