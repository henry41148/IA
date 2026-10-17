import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import db


class ReportsScreen(tk.Frame):
    def __init__(self, master, navigate):
        super().__init__(master)

        tk.Button(self, text="<- Back", command=lambda: navigate("home")).pack(anchor="w", padx=10, pady=6)
        tk.Label(self, text="Business Reports", font=("Segoe UI", 14, "bold")).pack()

        self.build_item_chart()
        self.build_day_chart()

    def build_item_chart(self):
        data = db.get_revenue_by_item()

        if not data:
            tk.Label(self, text="No sales data yet.", font=("Segoe UI", 11)).pack(expand=True)
            return

        names = []
        revenues = []
        for row in data:
            names.append(row[0])
            revenues.append(row[1])

        fig, ax = plt.subplots(figsize=(8, 3.5))
        ax.bar(names, revenues)
        ax.set_title("Revenue by Item")
        ax.set_xlabel("Item")
        ax.set_ylabel("Revenue (VND)")
        ax.ticklabel_format(style="plain", axis="y")
        plt.xticks(rotation=30)
        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="x", padx=10)

    def build_day_chart(self):
        data = db.get_revenue_by_day()

        if not data:
            tk.Label(self, text="No sales data yet.", font=("Segoe UI", 11)).pack(expand=True)
            return

        dates = []
        revenues = []
        for row in data:
            dates.append(row[0])
            revenues.append(row[1])

        fig, ax = plt.subplots(figsize=(8, 3.5))
        ax.bar(dates, revenues)
        ax.set_title("Daily Revenue (Last 30 Days)")
        ax.set_xlabel("Date")
        ax.set_ylabel("Revenue (VND)")
        ax.ticklabel_format(style="plain", axis="y")
        plt.xticks(rotation=45)
        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="x", padx=10)
