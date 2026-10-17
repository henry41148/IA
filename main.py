import tkinter as tk
import db
from screens.setup import SetupScreen
from screens.login import LoginScreen
from screens.home import HomeScreen
from screens.order import OrderScreen
from screens.items import ItemManagementScreen
from screens.inventory import InventoryScreen
from screens.reports import ReportsScreen

def main():
    db.create_tables() # runs function in db.py to create tables in database

    root = tk.Tk() # creates main window
    root.title("Boba Tea POS")
    root.state("zoomed")

    current_role = [None] # list where role would be later stated in

    def clear(): # used to destroy screen when changing between screens
        for widget in root.winfo_children():
            widget.destroy()

    def navigate(destination): # let the application know which screen to go to next
        clear()
        if destination == "home": # does not have a condition regarding roles so everyone can go 
            screen = HomeScreen(root, role=current_role[0], navigate=navigate)
            screen.pack(expand=True, fill="both")

        elif destination == "order" and current_role[0] == "employee": # only available when destination is order and role is employee
            screen = OrderScreen(root, navigate=navigate)
            screen.pack(expand=True, fill="both")

        elif destination == "items" and current_role[0] == "manager": # only available when destination is items and role is manager
            screen = ItemManagementScreen(root, navigate=navigate)
            screen.pack(expand=True, fill="both")

        elif destination == "inventory": # does not have a condition regarding roles so everyone can go 
            screen = InventoryScreen(root, role=current_role[0], navigate=navigate)
            screen.pack(expand=True, fill="both")

        elif destination == "reports" and current_role[0] == "manager": # only available when destination is reports and role is manager
            screen = ReportsScreen(root, navigate=navigate)
            screen.pack(expand=True, fill="both")

        elif destination == "logout": # does not have a condition regarding roles so everyone can go 
            current_role[0] = None
            show_login()


    def show_login():
        clear()
        screen = LoginScreen(root, on_login=after_login)
        screen.pack(expand=True, fill="both")

    def after_login(role):
        current_role[0] = role # role taken from login where the function in db.py is run to determine role
        clear()
        screen = HomeScreen(root, role=current_role[0], navigate=navigate)
        screen.pack(expand=True, fill="both")

    if db.is_first_launch():
        clear()
        screen = SetupScreen(root, on_complete=show_login)
        screen.pack(expand=True, fill="both")
    else:
        show_login()

    root.mainloop() # keeps window opened

if __name__ == "__main__":
    main()
