import tkinter as tk
from tkinter import messagebox
import db


class InventoryScreen(tk.Frame):
    def __init__(self, master, role, navigate):
        super().__init__(master)
        self.role = role
        self.navigate = navigate
        self.selected_id = None

        self.build_ui()
        self.load_ingredients()

    def build_ui(self):
        tk.Button(self, text="<- Back", command=lambda: self.navigate("home")).pack(anchor="w", padx=10, pady=6)
        tk.Label(self, text="Inventory", font=("Segoe UI", 14, "bold")).pack()

        self.warning_label = tk.Label(self, text="")

        self.listbox = tk.Listbox(self, width=70, height=16, font=("Courier", 10))
        self.listbox.pack(padx=10, pady=4, fill="both", expand=True)
        self.listbox.bind("<<ListboxSelect>>", self.on_select)

        if self.role == "manager":
            button_frame = tk.Frame(self)
            button_frame.pack(pady=6)
            tk.Button(button_frame, text="Add Ingredient", width=16, command=self.open_add).pack(side="left", padx=4)
            tk.Button(button_frame, text="Edit Selected", width=16, command=self.open_edit).pack(side="left", padx=4)
            tk.Button(button_frame, text="Delete Selected", width=16, command=self.delete).pack(side="left", padx=4)

    def load_ingredients(self):
        self.listbox.delete(0, tk.END)
        self.listbox.insert(tk.END, "Ingredient".ljust(20) + "Current Stock".ljust(20) + "Reorder Level".ljust(20) + "Status")
        self.ingredient_data = db.get_all_ingredients() # gets list of tuple containing information about each ingredient
        low_stock_names = []

        for ingredient in self.ingredient_data: # loops through the tuples
            ingredient_id, name, stock, reorder = ingredient # unpacks the components of the tuple
            if stock > reorder: # determines the status of each ingredient
                status = "OK"
            else:
                status = "LOW"
            row = name.ljust(20) + str(stock).ljust(20) + str(reorder).ljust(20) + status
            self.listbox.insert(tk.END, row)
            if status == "LOW": # based on status, determines whether to highlight ingredient in red or green
                index = self.listbox.size() - 1
                self.listbox.itemconfig(index, foreground="red")
                low_stock_names.append(name)
            else:
                index = self.listbox.size() - 1
                self.listbox.itemconfig(index, foreground="green")

        if low_stock_names: # displays the names of ingredients that is low on stock
            warning_text = ""
            for name in low_stock_names:
                if warning_text != "":
                    warning_text = warning_text + ", "
                warning_text = warning_text + name
            self.warning_label.config(text="Low stock: " + warning_text)
            self.warning_label.pack(fill="x", padx=10, pady=4)
        else:
            self.warning_label.pack_forget()

    def on_select(self, event):
        selection = self.listbox.curselection()
        if selection and selection[0] > 0:
            self.selected_id = self.ingredient_data[selection[0] - 1][0]

    def delete(self):
        if not self.selected_id:
            messagebox.showwarning("No Selection", "Please select an ingredient first.")
            return
        if messagebox.askyesno("Confirm", "Delete this ingredient?"):
            db.delete_ingredient(self.selected_id)
            self.selected_id = None
            self.load_ingredients()

    def open_add(self):
        IngredientFormPopup(self, ingredient=None, on_save=self.load_ingredients)

    def open_edit(self):
        if not self.selected_id:
            messagebox.showwarning("No Selection", "Please select an ingredient first.")
            return
        match = None
        for ingredient in self.ingredient_data:
            if ingredient[0] == self.selected_id:
                match = ingredient
                break
        IngredientFormPopup(self, ingredient=match, on_save=self.load_ingredients)


class IngredientFormPopup(tk.Toplevel):
    def __init__(self, master, ingredient, on_save):
        super().__init__(master)
        self.ingredient = ingredient
        self.on_save = on_save
        if ingredient:
            self.title("Edit Ingredient")
        else:
            self.title("Add Ingredient")
        self.grab_set()

        tk.Label(self, text="Name:").pack(anchor="w", padx=16, pady=(14, 0))
        self.name_entry = tk.Entry(self, width=30)
        self.name_entry.pack(anchor="w", padx=16)

        tk.Label(self, text="Current Stock:").pack(anchor="w", padx=16, pady=(8, 0))
        self.stock_entry = tk.Entry(self, width=20)
        self.stock_entry.pack(anchor="w", padx=16)

        tk.Label(self, text="Reorder Level:").pack(anchor="w", padx=16, pady=(8, 0))
        self.reorder_entry = tk.Entry(self, width=20)
        self.reorder_entry.pack(anchor="w", padx=16)

        tk.Button(self, text="Save", command=self.save).pack(pady=14)

        if ingredient:
            self.name_entry.insert(0, ingredient[1])
            self.stock_entry.insert(0, ingredient[2])
            self.reorder_entry.insert(0, ingredient[3])

    def save(self):
        name = self.name_entry.get().strip()
        try:
            stock = float(self.stock_entry.get().strip())
            reorder = float(self.reorder_entry.get().strip())
        except ValueError:
            messagebox.showerror("Error", "Stock and reorder level must be numbers.")
            return
        if not name:
            messagebox.showerror("Error", "Name cannot be empty.")
            return

        if self.ingredient:
            db.update_ingredient(self.ingredient[0], name, stock, reorder)
        else:
            db.add_ingredient(name, stock, reorder)

        self.on_save()
        self.destroy()
