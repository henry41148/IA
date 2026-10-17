# Boba Tea POS: Developer Manual

A guide to understanding and editing your own code. Read Parts 1 to 3 once. After that, use Part 4 as a lookup ("I want to change X, where do I go?"). Part 6 has exercises.

---

## Part 1: The Big Picture

```
main.py              <- starts the app, decides which screen to show
db.py                <- ALL database code (the only file that talks to SQLite)
screens/
    setup.py         <- first launch: set manager + employee codes
    login.py         <- enter code -> get a role
    home.py          <- menu of buttons (different for manager / employee)
    order.py         <- employee: take orders          (Order processing)
    items.py         <- manager: add/edit menu items   (Menu management)
    inventory.py     <- both: view stock, manager edits (Inventory management)
    reports.py       <- manager: charts                (Sales report)
boba_pos.db          <- the database file (created automatically)
```

**Golden rule of your design:** screens never write SQL. A screen calls a function in `db.py`
(e.g. `db.add_ingredient(...)`), and `db.py` does the SQL. This is called *separation of concerns*.
It means that when something is wrong you know where to look:

| Problem looks like...                         | Look in...        |
|-----------------------------------------------|-------------------|
| Something looks wrong on screen / button      | `screens/*.py`    |
| Wrong data saved / wrong numbers              | `db.py`           |
| Wrong screen shown / wrong permissions        | `main.py`         |

---

## Part 2: How the app runs (follow the flow)

### 2.1 `main.py`: the controller

1. `db.create_tables()` makes sure all tables exist.
2. `root = tk.Tk()` creates the one and only window.
3. **The screen-swapping trick:** every screen is a `tk.Frame`. To change screens, `clear()`
   destroys everything inside `root`, then a new Frame is created and `.pack()`ed.
4. **Callbacks.** `main.py` gives each screen a function to call when it needs to change screen:
   - `LoginScreen(root, on_login=after_login)`: when login succeeds, the screen calls `after_login(role)`.
   - Other screens get `navigate=navigate`, then call `navigate("home")`, `navigate("order")`, etc.
5. **Permissions** live in `navigate()`:
   ```python
   elif destination == "items" and current_role[0] == "manager":
   ```
   An employee cannot reach "items" even if a button existed, because this check blocks it.
6. `current_role = [None]` is a *list* on purpose: inner functions can change `current_role[0]`,
   but they can't reassign a plain variable from the outer function without `nonlocal`.
7. At the bottom: first launch -> `SetupScreen`, otherwise -> `LoginScreen`.

### 2.2 Anatomy of every screen

Every screen file follows the same pattern, so once you learn one you know them all:

```python
class SomethingScreen(tk.Frame):
    def __init__(self, master, navigate):
        super().__init__(master)      # create the Frame inside the window
        self.navigate = navigate      # keep the callback so other methods can use it
        self._build_ui()              # create widgets (Labels, Buttons, Listboxes...)
        self._load_data()             # fill widgets with data from db.py
```

Tkinter vocabulary you'll see:

| Widget / call                     | What it does                                              |
|-----------------------------------|-----------------------------------------------------------|
| `tk.Label(parent, text=...)`      | Static text                                               |
| `tk.Entry(parent)`                | One-line text box. `.get()` reads it, `.insert(0, x)` fills it |
| `tk.Button(parent, command=f)`    | Calls function `f` when clicked (no brackets after `f`!)  |
| `tk.Listbox(parent)`              | A list. `.insert(tk.END, text)`, `.delete(0, tk.END)`, `.curselection()` |
| `tk.Toplevel(self)`               | A popup window. `grab_set()` blocks the main window until closed |
| `.pack(...)`                      | Places the widget. `side`, `fill`, `expand`, `padx`, `pady`, `anchor` adjust it |
| `lambda: self.navigate("home")`   | A tiny function, needed when the command needs an argument |
| `messagebox.showerror/askyesno`   | Standard popups                                           |

**Pattern to remember: "refresh by clearing and refilling".** To update a list on screen you
`delete(0, END)` then loop and `insert` again (see `_load_items`, `_refresh_order_list`,
`_load_ingredients`). If you forget the delete, you get duplicates.

---

## Part 3: The database (`db.py`)

### 3.1 The tables (your ER diagram in code)

```
Users                 id, role, access_code(hashed)
Items                 item_id, name, price
Subcategories         subcategory_id, item_id -> Items, name, price     (e.g. "Large +5000", "Extra pearls")
Orders                order_id, date, price                             (one row per customer order)
Ordered_Items         ordered_item_id, order_id -> Orders, item_id -> Items   (one row per drink in an order)
Ordered_Items_Subcategories   (ordered_item_id, subcategory_id)         (options chosen on that drink)
Ingredients           ingredient_id, name, current_stock, reorder_level
Items_Ingredients     (item_id, ingredient_id, quantity_used)           (recipe: how much of each ingredient one item uses)
Subcategories_Ingredients     (subcategory_id, ingredient_id, quantity_used)   <- created but NOT used yet
```

Key ideas:
- **Primary key** (`PRIMARY KEY`): unique ID of a row.
- **Foreign key** (`FOREIGN KEY ... REFERENCES`): a column that points to a row in another table.
- **Many-to-many** relationships (an item uses many ingredients, an ingredient is in many items)
  need a **junction table** (`Items_Ingredients`, `Ordered_Items_Subcategories`).
- `ON DELETE CASCADE`: deleting an Item automatically deletes its Subcategories and recipe rows.

### 3.2 The four helper functions

Everything else in `db.py` is built from these:

| Function                    | Use for                      | Returns                              |
|-----------------------------|------------------------------|--------------------------------------|
| `execute(query, params)`    | INSERT / UPDATE / DELETE     | the cursor (use `.lastrowid` for new ID) |
| `fetchall(query, params)`   | SELECT many rows             | list of tuples `[(1,'Milk Tea',35000), ...]` |
| `fetchone(query, params)`   | SELECT one row               | one tuple, or `None`                 |
| `hash_code(code)`           | passwords                    | SHA-256 hex string                   |

**Always use `?` placeholders**, never put variables directly into the SQL string:
```python
execute("UPDATE Items SET price = ? WHERE item_id = ?", (price, item_id))   # correct
execute(f"UPDATE Items SET price = {price} ...")                            # NEVER: SQL injection risk
```
The parameters must be a tuple. A single value needs a trailing comma: `(item_id,)`.

### 3.3 Reading a SQL query: `get_revenue_by_item`

```sql
SELECT i.name, COUNT(oi.ordered_item_id) * i.price AS revenue   -- what to show
FROM Ordered_Items oi                                            -- start here
JOIN Items i  ON i.item_id  = oi.item_id                         -- attach item name/price
JOIN Orders o ON o.order_id = oi.order_id                        -- attach order date
WHERE o.date >= date('now', '-30 days')                          -- last 30 days only
GROUP BY i.item_id                                               -- one row per item
ORDER BY revenue DESC                                            -- biggest first
```
`i`, `oi`, `o` are *aliases* (short names). `GROUP BY` + `COUNT/SUM` collapses many rows into one per group.

---

## Part 4: "I want to change X": lookup guide

### Order processing (`screens/order.py`)
Flow of one order:
1. `_load_items` fills the left list from `db.get_all_items()` (or `db.search_items` if the search box has text).
2. Double-click an item -> `_on_item_select`. It looks up the row using `self.items_data[index]`
   (the listbox and `items_data` have the **same order**, so index N in one = index N in the other).
3. If the item has subcategories -> `_show_subcategory_popup` (checkboxes). Otherwise `_add_to_order` directly.
4. `_add_to_order` appends a **dictionary** to `self.order` and calls `_refresh_order_list`.
5. **Confirm Order** (`_confirm_order`) does 4 things in order:
   `create_order` -> for each drink `add_ordered_item` -> for each option `add_ordered_item_subcategory` -> `deduct_inventory`.
   Then it checks low stock, clears the order, and shows a message.

| To change...                         | Edit...                                                       |
|--------------------------------------|---------------------------------------------------------------|
| Currency text ("VND")                | the f-strings in `order.py` (search `VND`)                    |
| Text shown for each order line       | `_refresh_order_list`                                         |
| Add a quantity / discount feature    | store extra keys in the dict in `_add_to_order`, use them in `_refresh_order_list` and `_confirm_order` |
| What happens when an order is saved  | `_confirm_order` and the `db.*` functions it calls            |

### Inventory (`screens/inventory.py` + `db.py`)
- Rows show **LOW** (red) when `stock <= reorder_level`; this logic is in `_load_ingredients`.
  The same rule is in SQL in `db.get_low_stock_ingredients`. If you change one, change the other.
- The first listbox row is a header, so a selected index N matches `ingredient_data[N - 1]` (see `_on_select`).
- The role check `if self.role == "manager":` hides the Add/Edit/Delete buttons from employees.
- `IngredientFormPopup` is used for both Add and Edit: if `ingredient` is `None` it's Add, otherwise it pre-fills fields and updates.
- To add a column (e.g. "unit" = ml, g): add it in `CREATE TABLE`, update `add_ingredient/update_ingredient/get_all_ingredients`, then the form and the listbox row.
  **Important:** `CREATE TABLE IF NOT EXISTS` will NOT alter an existing table. Delete `boba_pos.db` while developing (you'll lose test data), or use `ALTER TABLE`.

### Reports (`screens/reports.py`)
- Data comes from `db.get_revenue_by_item()` and `db.get_revenue_by_day()`, as lists of tuples.
- The screen splits them into two lists (`names`, `revenues`), then `ax.bar(names, revenues)` draws a bar chart.
- Change the period: edit `'-30 days'` in both SQL queries (and the chart title).
- New chart (e.g. orders per day): write a `db.get_orders_per_day()` using `COUNT(*)`, then copy `_build_day_chart` and change the data and labels.

### Login / roles (`login.py`, `setup.py`, `main.py`)
- Codes are stored hashed. `check_login` hashes what was typed and compares hashes; the real code is never stored.
- To add a new role: add a row in `create_tables` seeding, a branch in `HomeScreen`, and allowed destinations in `navigate()` in `main.py`.

---

## Part 5: How to work on this code safely

1. **Change one thing, then run it.** Run with `python main.py` in the CS IA folder.
2. **Read the error from the bottom up.** The last line is the error type, and the lines above show the file and line number.
3. **Print to see data.** Put `print(self.items_data)` somewhere to see exactly what a variable holds.
4. **Inspect the database.** Install "DB Browser for SQLite" (free), open `boba_pos.db`, and look at the tables after placing an order.
5. **Back up before experiments.** Copy the folder (OneDrive isn't version control). Better: `git init` and commit after each working change.
6. **Common mistakes:**
   - `command=self.save()`, which calls it immediately. It should be `command=self.save`.
   - Forgetting `.pack()`, so the widget never shows.
   - Wrong tuple unpacking count: `a, b = row` when the row has 3 columns.
   - Mixing `pack` and `grid` in the same parent.
   - Forgetting to refresh the list after changing the database.

---

## Part 6: Practice exercises (easiest to hardest)

Several of these are real gaps in your current code, which makes them good for your IA's "evaluation / future improvements" section.

1. **Easy:** Change the window title and all "VND" text to another currency.
2. **Easy:** In `inventory.py`, make the "LOW" row text orange instead of red.
3. **Easy:** Add a "Total orders today" label on the home screen. You'll need a new `db.get_orders_today()` using `SELECT COUNT(*) FROM Orders WHERE date = ?`.
4. **Medium:** *Bug:* `get_revenue_by_item` ignores subcategory prices, so item revenue can be lower than daily revenue. Add the subcategory prices to the sum (join `Ordered_Items_Subcategories` and `Subcategories`).
5. **Medium:** *Gap:* `deduct_inventory` only uses `Items_Ingredients`. The table `Subcategories_Ingredients` exists but is unused. Extend `deduct_inventory(item_id, subcategory_ids)` so choosing "extra pearls" also reduces pearls.
6. **Medium:** *Bug:* stock can go negative. Before confirming an order, check that enough stock exists and warn if not.
7. **Medium:** Add a quantity ("x2") to an order line instead of adding the same drink twice.
8. **Medium:** Modern Tkinter: `search_var.trace("w", ...)` is deprecated. Replace with `trace_add("write", ...)`.
9. **Hard:** Add a "Sales History" screen listing orders with their items (needs JOINs across Orders, Ordered_Items, Items).
10. **Hard:** Make `execute` safe if an error occurs mid-way. Order saving currently uses many separate commits, so a crash halfway leaves a half-saved order. Fix: use one connection and commit once in a `save_order(...)` function in `db.py`.
11. **Hard:** Wrap `_confirm_order`'s database work into that single transaction function, then move the stock check there too.

When you're stuck, ask me about a specific function or exercise and I'll explain it line by line without giving the full answer, if you prefer.
