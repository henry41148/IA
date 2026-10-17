import tkinter as tk
from tkinter import messagebox
import db


class LoginScreen(tk.Frame):
    def __init__(self, master, on_login): # receives root and show_login() from main.py
        super().__init__(master) # runs Frame's constructor and attaches this frame to the main window
        
        self.on_login = on_login # variable to store function on_login, which is after_login() on main.py

        tk.Label(self, text="Boba Tea POS", font=("Segoe UI", 16, "bold")).pack(pady=20)
        tk.Label(self, text="Enter your access code:").pack()

        self.code_entry = tk.Entry(self, show="*", width=30)
        self.code_entry.pack(pady=10)

        tk.Button(self, text="Login", command=self.login).pack() # when clicked

    def login(self):
        code = self.code_entry.get().strip()
        role = db.check_login(code) # sends to db.py to check which code this belongs to

        if role is None:
            messagebox.showerror("Error", "Incorrect access code.")
            self.code_entry.delete(0, tk.END)
        else:
            self.on_login(role) # runs after_login from main.py