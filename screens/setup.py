import tkinter as tk
from tkinter import messagebox
import db


class SetupScreen(tk.Frame): # inherits from Tkinter's Frame, allows holding widgets like labels, buttons, inputs
    def __init__(self, master, on_complete):
        super().__init__(master) # runs tk.Frame's constructor
        self.on_complete = on_complete

        # builds visual layout, two labels; two input; one button

        tk.Label(self, text="First-Time Setup", font=("Segoe UI", 16, "bold")).pack(pady=20)
        tk.Label(self, text="Set the access codes for each role.").pack()

        tk.Label(self, text="Manager Code:").pack(pady=(20, 2))
        self.manager_entry = tk.Entry(self, show="*", width=30)
        self.manager_entry.pack()

        tk.Label(self, text="Employee Code:").pack(pady=(10, 2))
        self.employee_entry = tk.Entry(self, show="*", width=30)
        self.employee_entry.pack()

        tk.Button(self, text="Confirm", command=self.confirm).pack(pady=20)

    def confirm(self):
        manager_code = self.manager_entry.get().strip() # removes spaces or tab around number
        employee_code = self.employee_entry.get().strip()

        if not manager_code or not employee_code:
            messagebox.showerror("Error", "Both fields must be filled in.")
            return # shows error if either is empty

        db.set_access_codes(manager_code, employee_code)
        self.on_complete() # runs show_login from main.py
