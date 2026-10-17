import tkinter as tk
from tkinter import messagebox
import db


class ItemManagementScreen(tk.Frame):
    def __init__(self, master, navigate):
        super().__init__(master)
        self.navigate = navigate
        self.selected_item_id = None

        self.build_ui()
        self.load_items()

    def build_ui(self):
        tk.Button(self, text="<- Back", command=lambda: self.navigate("home")).pack(anchor="w", padx=10, pady=6)
        tk.Label(self, text="Item Management", font=("Segoe UI", 14, "bold")).pack()

        list_frame = tk.Frame(self)
        list_frame.pack(padx=10, pady=6, fill="both", expand=True)

        self.item_listbox = tk.Listbox(list_frame, width=50, height=12)
        self.item_listbox.pack(side="left", fill="both", expand=True)
        self.item_listbox.bind("<<ListboxSelect>>", self.on_select)

        button_frame = tk.Frame(self)
        button_frame.pack(pady=6)
        tk.Button(button_frame, text="Add Item", width=14, command=self.open_add).pack(side="left", padx=4)
        tk.Button(button_frame, text="Edit Item", width=14, command=self.open_edit).pack(side="left", padx=4)
        tk.Button(button_frame, text="Delete Item", width=14, command=self.delete_item).pack(side="left", padx=4)

    def load_items(self):
        self.item_listbox.delete(0, tk.END)
        self.items_data = db.get_all_items()
        for item in self.items_data:
            self.item_listbox.insert(tk.END, f"{item[1]}  —  {item[2]} VND")

    def on_select(self, event):
        selection = self.item_listbox.curselection()
        if selection:
            self.selected_item_id = self.items_data[selection[0]][0]

    def delete_item(self):
        if not self.selected_item_id:
            messagebox.showwarning("No Selection", "Please select an item first.")
            return
        if messagebox.askyesno("Confirm", "Delete this item and all its subcategories?"):
            db.delete_item(self.selected_item_id)
            self.selected_item_id = None
            self.load_items()

    def open_add(self):
        ItemFormPopup(self, item_id=None, on_save=self.load_items)

    def open_edit(self):
        if not self.selected_item_id:
            messagebox.showwarning("No Selection", "Please select an item first.")
            return
        ItemFormPopup(self, item_id=self.selected_item_id, on_save=self.load_items)


class ItemFormPopup(tk.Toplevel):

    def __init__(self, master, item_id, on_save):
        super().__init__(master)
        self.item_id = item_id
        self.on_save = on_save
        if item_id:
            self.title("Edit Item")
        else:
            self.title("Add Item")
        self.geometry("500x600")
        self.grab_set()

        self.build_ui()
        if item_id:
            self.populate()

    def build_ui(self):
        tk.Label(self, text="Item Name:").pack(anchor="w", padx=16, pady=(12, 0))
        self.name_entry = tk.Entry(self, width=40)
        self.name_entry.pack(anchor="w", padx=16)

        tk.Label(self, text="Price (VND):").pack(anchor="w", padx=16, pady=(8, 0))
        self.price_entry = tk.Entry(self, width=20)
        self.price_entry.pack(anchor="w", padx=16)

        tk.Button(self, text="Save Name & Price", command=self.save_item).pack(anchor="w", padx=16, pady=8)

        tk.Label(self, text="Subcategories:").pack(anchor="w", padx=16, pady=(6, 0))

        self.subcategory_listbox = tk.Listbox(self, width=50, height=5)
        self.subcategory_listbox.pack(anchor="w", padx=16, pady=4)

        subcategory_input_frame = tk.Frame(self)
        subcategory_input_frame.pack(anchor="w", padx=16)
        tk.Label(subcategory_input_frame, text="Name:").pack(side="left")
        self.subcategory_name_entry = tk.Entry(subcategory_input_frame, width=16)
        self.subcategory_name_entry.pack(side="left", padx=4)
        tk.Label(subcategory_input_frame, text="Price:").pack(side="left")
        self.subcategory_price_entry = tk.Entry(subcategory_input_frame, width=8)
        self.subcategory_price_entry.pack(side="left", padx=4)
        tk.Button(subcategory_input_frame, text="Add", command=self.add_subcategory).pack(side="left", padx=4)

        tk.Button(self, text="Remove Selected Subcategory", command=self.remove_subcategory).pack(anchor="w", padx=16, pady=2)

        tk.Label(self, text="Ingredient Costs:").pack(anchor="w", padx=16, pady=(6, 0))

        self.ingredient_listbox = tk.Listbox(self, width=50, height=5)
        self.ingredient_listbox.pack(anchor="w", padx=16, pady=4)

        ingredient_input_frame = tk.Frame(self)
        ingredient_input_frame.pack(anchor="w", padx=16)

        self.ingredient_data = db.get_all_ingredients()
        ingredient_names = []
        for ingredient in self.ingredient_data:
            ingredient_names.append(ingredient[1])

        tk.Label(ingredient_input_frame, text="Ingredient:").pack(side="left")
        if ingredient_names:
            self.ingredient_var = tk.StringVar(value=ingredient_names[0])
            self.ingredient_dropdown = tk.OptionMenu(ingredient_input_frame, self.ingredient_var, *ingredient_names)
        else:
            self.ingredient_var = tk.StringVar(value="")
            self.ingredient_dropdown = tk.OptionMenu(ingredient_input_frame, self.ingredient_var, "None")
        self.ingredient_dropdown.pack(side="left", padx=4)

        tk.Label(ingredient_input_frame, text="Quantity used:").pack(side="left")
        self.ingredient_qty_entry = tk.Entry(ingredient_input_frame, width=8)
        self.ingredient_qty_entry.pack(side="left", padx=4)
        tk.Button(ingredient_input_frame, text="Set", command=self.set_ingredient).pack(side="left", padx=4)

        tk.Button(self, text="Remove Selected Ingredient", command=self.remove_ingredient).pack(anchor="w", padx=16, pady=2)

    def populate(self):
        item = db.fetchone("SELECT name, price FROM Items WHERE item_id = ?", (self.item_id,))
        if item:
            self.name_entry.insert(0, item[0])
            self.price_entry.insert(0, item[1])
        self.reload_subcategories()
        self.reload_ingredients()

    def save_item(self):
        name = self.name_entry.get().strip()
        try:
            price = float(self.price_entry.get().strip())
        except ValueError:
            messagebox.showerror("Error", "Price must be a number.")
            return
        if not name:
            messagebox.showerror("Error", "Item name cannot be empty.")
            return

        if self.item_id:
            db.update_item(self.item_id, name, price)
        else:
            self.item_id = db.add_item(name, price)

        self.on_save()
        messagebox.showinfo("Saved", "Item saved.")

    def reload_subcategories(self):
        self.subcategory_listbox.delete(0, tk.END)
        if not self.item_id:
            return
        self.subcategories_data = db.get_subcategories(self.item_id)
        for subcategory in self.subcategories_data:
            self.subcategory_listbox.insert(tk.END, f"{subcategory[1]}  —  {subcategory[2]} VND")

    def add_subcategory(self):
        if not self.item_id:
            messagebox.showwarning("Save Item First", "Save the item name and price first.")
            return
        name = self.subcategory_name_entry.get().strip()
        price_text = self.subcategory_price_entry.get().strip()
        if not price_text:
            price_text = "0"
        try:
            price = float(price_text)
        except ValueError:
            messagebox.showerror("Error", "Subcategory price must be a number.")
            return
        if not name:
            messagebox.showerror("Error", "Subcategory name cannot be empty.")
            return
        db.add_subcategory(self.item_id, name, price)
        self.subcategory_name_entry.delete(0, tk.END)
        self.subcategory_price_entry.delete(0, tk.END)
        self.reload_subcategories()

    def remove_subcategory(self):
        selection = self.subcategory_listbox.curselection()
        if not selection:
            return
        subcategory_id = self.subcategories_data[selection[0]][0]
        db.delete_subcategory(subcategory_id)
        self.reload_subcategories()

    def reload_ingredients(self):
        self.ingredient_listbox.delete(0, tk.END)
        if not self.item_id:
            return
        self.item_ingredient_data = db.get_item_ingredients(self.item_id)
        for row in self.item_ingredient_data:
            self.ingredient_listbox.insert(tk.END, f"{row[1]}  —  {row[2]} units")

    def set_ingredient(self):
        if not self.item_id:
            messagebox.showwarning("Save Item First", "Save the item name and price first.")
            return
        ingredient_name = self.ingredient_var.get()
        match = None
        for ingredient in self.ingredient_data:
            if ingredient[1] == ingredient_name:
                match = ingredient
                break
        if not match:
            messagebox.showerror("Error", "No ingredients exist yet. Add them in Inventory first.")
            return
        try:
            quantity = float(self.ingredient_qty_entry.get().strip())
        except ValueError:
            messagebox.showerror("Error", "Quantity must be a number.")
            return
        db.set_item_ingredient(self.item_id, match[0], quantity)
        self.ingredient_qty_entry.delete(0, tk.END)
        self.reload_ingredients()

    def remove_ingredient(self):
        selection = self.ingredient_listbox.curselection()
        if not selection:
            return
        ingredient_id = self.item_ingredient_data[selection[0]][0]
        db.delete_item_ingredient(self.item_id, ingredient_id)
        self.reload_ingredients()
