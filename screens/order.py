import tkinter as tk
from tkinter import messagebox
import db


class OrderScreen(tk.Frame):
    def __init__(self, master, navigate):
        super().__init__(master)
        self.navigate = navigate
        self.order = []  # list of dicts {item_id, name, price, subcategory_ids, subcategory_names}

        self.build_ui()
        self.load_items()

    def build_ui(self):
        tk.Button(self, text="<- Back", command=lambda: self.navigate("home")).pack(anchor="w", padx=10, pady=6) # back button

        left = tk.Frame(self)
        left.pack(side="left", fill="both", expand=True, padx=10, pady=10) # creates blank screen on left side

        tk.Label(left, text="Menu Items", font=("Segoe UI", 12, "bold")).pack(anchor="w") # label inside left screen

        self.search_var = tk.StringVar() # allows Tkinter to auto detect changes

        def on_search_change(name, index, mode): # called every time the search box changes
            self.load_items()

        self.search_var.trace("w", on_search_change)
        tk.Entry(left, textvariable=self.search_var, width=30).pack(anchor="w", pady=(4, 8))

        self.item_listbox = tk.Listbox(left, width=35, height=20) # creates menu list
        self.item_listbox.pack(fill="both", expand=True)
        self.item_listbox.bind("<Double-Button-1>", self.on_item_select)

        right = tk.Frame(self) # creates right panel
        right.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        tk.Label(right, text="Current Order", font=("Segoe UI", 12, "bold")).pack(anchor="w")

        self.order_listbox = tk.Listbox(right, width=35, height=18) # list of chosen items
        self.order_listbox.pack(fill="both", expand=True)

        tk.Button(right, text="Remove", command=self.remove_item).pack(anchor="w", pady=4)

        self.total_label = tk.Label(right, text="Total: 0 VND", font=("Segoe UI", 11, "bold"))
        self.total_label.pack(anchor="w", pady=8)

        tk.Button(right, text="Confirm Order", command=self.confirm_order).pack(anchor="w")

    def load_items(self):
        query = self.search_var.get().strip()
        if query:
            items = db.search_items(query) # filter out matching items, stored in items as a list of tuples
        else:
            items = db.get_all_items() # returns all items

        self.item_listbox.delete(0, tk.END) # delete list so items don't duplicate
        self.items_data = items  # saves list of tuples
        for item in items:
            self.item_listbox.insert(tk.END, f"{item[1]}  —  {item[2]} VND") # loops through item, displaying names and prices

    def on_item_select(self, event):
        selection = self.item_listbox.curselection() # gets row number of selected item as a tuple
        if not selection: # if nothing is selected, return nothing
            return
        row_number = selection[0] # extracts row number from tuple
        item = self.items_data[row_number] # gets tuple of item based on row number
        item_id, item_name, item_price = item # unpacks each component of the tuple

        subcategories = db.get_subcategories(item_id) # checks whether it has any subcategories

        if subcategories:
            self.show_subcategory_popup(item_id, item_name, item_price, subcategories)
        else:
            self.add_to_order(item_id, item_name, item_price, [], [])

    def show_subcategory_popup(self, item_id, item_name, item_price, subcategories): # opens small separate window
        popup = tk.Toplevel(self)
        popup.title(f"Options for {item_name}")
        popup.grab_set() # locks focus so can't click on anything else until this window is closed

        tk.Label(popup, text=f"Select options for {item_name}:", font=("Segoe UI", 11, "bold")).pack(pady=10)

        checks = []
        for subcategory in subcategories: # loops through each tuple in the subcategories list
            subcategory_id, subcategory_name, subcategory_price = subcategory # unpacks tuple
            var = tk.BooleanVar()
            if subcategory_price > 0:
                label = f"{subcategory_name}  (+{subcategory_price} VND)"
            else:
                label = subcategory_name
            tk.Checkbutton(popup, text=label, variable=var).pack(anchor="w", padx=20) # shows box
            checks.append((subcategory_id, subcategory_name, subcategory_price, var)) # adds tuple to checks

        def confirm():
            selected_ids = []
            selected_names = []
            extra = 0
            for subcategory_id, subcategory_name, subcategory_price, var in checks:
                if var.get(): # checks if checkbox ticked, returns T/F
                    selected_ids.append(subcategory_id)
                    selected_names.append(subcategory_name)
                    extra += subcategory_price # adds together price of all selected
            self.add_to_order(item_id, item_name, item_price + extra, selected_ids, selected_names)
            popup.destroy()

        tk.Button(popup, text="Add to Order", command=confirm).pack(pady=16)

    def add_to_order(self, item_id, item_name, total_price, subcategory_ids, subcategory_names):
        self.order.append({"item_id": item_id, "name": item_name, "price": total_price, "subcategory_ids": subcategory_ids, "subcategory_names": subcategory_names}) # adds dict to order list
        self.refresh_order_list()

    def refresh_order_list(self):
        self.order_listbox.delete(0, tk.END) # clears listbox
        total = 0
        for entry in self.order: # entry is a dictionary, loops through each dict in order list
            subcategory_text = ""
            for name in entry["subcategory_names"]:
                if subcategory_text != "":
                    subcategory_text = subcategory_text + ", "
                subcategory_text = subcategory_text + name
            if subcategory_text == "":
                subcategory_text = "no options"
            self.order_listbox.insert(tk.END, f"{entry['name']} ({subcategory_text})  —  {entry['price']} VND") # add to right panel's list
            total += entry["price"]
        self.total_label.config(text=f"Total: {total} VND")

    def remove_item(self):
        selection = self.order_listbox.curselection() # gets index of clicked item
        if not selection:
            return
        self.order.pop(selection[0]) # removes item from self.order
        self.refresh_order_list()

    def confirm_order(self):
        if not self.order:
            messagebox.showwarning("Empty Order", "No items in the order.")
            return

        total = 0
        for entry in self.order:
            total += entry["price"]
        order_id = db.create_order(total)

        for entry in self.order: # loops through every item in the order, records in database
            ordered_item_id = db.add_ordered_item(order_id, entry["item_id"])
            for subcategory_id in entry["subcategory_ids"]: # loops through every subcategory, records in database
                db.add_ordered_item_subcategory(ordered_item_id, subcategory_id)
            db.deduct_inventory(entry["item_id"])

        # Check for low stock and clears order and right panel's list
        low_stock = db.get_low_stock_ingredients()
        self.order = []
        self.refresh_order_list()

        message = f"Order confirmed! Total: {total} VND"
        if low_stock:
            names_text = ""
            for ingredient in low_stock:
                if names_text != "":
                    names_text = names_text + ", "
                names_text = names_text + ingredient[0]
            message = message + "\n\nLow stock warning: " + names_text
        messagebox.showinfo("Order Confirmed", message)
