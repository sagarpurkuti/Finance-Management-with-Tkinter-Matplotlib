import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from datetime import datetime
from collections import defaultdict
import csv

from backend import FinanceManager


class FinanceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Finance Tracker")
        self.root.geometry("900x600")
        self.root.resizable(True, True)

        # Backend finance manager instance
        self.fm = FinanceManager()

        self.create_widgets()
        self.populate_table()

    def create_widgets(self):
        columns = ("id", "amount", "type", "remarks", "date", "created_at")
        self.table = ttk.Treeview(self.root, columns=columns, show="headings", height=18)
        for col in columns:
            self.table.heading(col, text=col.capitalize())
            self.table.column(col, anchor=tk.CENTER, width=120)
        self.table.pack(fill="both", expand=True)

        btn_frame = tk.Frame(self.root)
        btn_frame.pack(fill="x", pady=10)

        tk.Button(btn_frame, text="Add Transaction", command=self.open_add_window).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Delete Selected", command=self.delete_selected).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Export CSV", command=self.export_csv).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Show Graph", command=self.show_graph).pack(side="left", padx=5)

    def populate_table(self):
        for row in self.table.get_children():
            self.table.delete(row)

        transactions = self.fm.get_transactions()
        for t in transactions:
            self.table.insert("", "end", values=(t.id, t.amount, t.type, t.remarks, t.date, t.created_at))

    def export_csv(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
            title="Save CSV File"
        )
        if not file_path:
            return

        transactions = self.fm.get_transactions()
        try:
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["id", "amount", "type", "remarks", "date", "created_at"])
                for t in transactions:
                    writer.writerow([t.id, t.amount, t.type, t.remarks, t.date, t.created_at])

            messagebox.showinfo("Success", f"CSV exported successfully:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export CSV:\n{e}")

    def show_graph(self):
        transactions = self.fm.get_transactions()

        monthly_income = defaultdict(float)
        monthly_expense = defaultdict(float)

        for t in transactions:
            dt = datetime.fromisoformat(t.created_at)
            key = dt.strftime("%Y-%m")

            if t.type == "income":
                monthly_income[key] += t.amount
            elif t.type == "expense":
                monthly_expense[key] += t.amount

        months = sorted(set(list(monthly_income.keys()) + list(monthly_expense.keys())))
        income_values = [monthly_income[m] for m in months]
        expense_values = [monthly_expense[m] for m in months]

        graph_win = tk.Toplevel(self.root)
        graph_win.title("Monthly Income vs Expense")
        graph_win.geometry("900x600")
        graph_win.resizable(True, True)

        fig = Figure(figsize=(10, 5))
        ax = fig.add_subplot(111)

        ax.bar(months, expense_values, label="Expense", color="#E53935")
        ax.bar(months, income_values, bottom=expense_values, label="Income", color="#4CAF50")

        ax.set_xlabel("Month")
        ax.set_ylabel("Amount")
        ax.set_title("Monthly Income vs Expense (Stacked Bar Chart)")
        ax.legend()

        fig.autofmt_xdate()

        canvas = FigureCanvasTkAgg(fig, master=graph_win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def open_add_window(self):
        add_win = tk.Toplevel(self.root)
        add_win.title("Add Transaction")
        add_win.geometry("400x300")
        add_win.resizable(False, False)

        # Labels and inputs
        tk.Label(add_win, text="Amount:").pack(pady=(20, 5))
        amount_entry = tk.Entry(add_win)
        amount_entry.pack()

        tk.Label(add_win, text="Type:").pack(pady=(20, 5))
        type_var = tk.StringVar(value="income")
        ttk.Combobox(add_win, textvariable=type_var, values=["income", "expense"], state="readonly").pack()

        tk.Label(add_win, text="Remarks:").pack(pady=(20, 5))
        remarks_entry = tk.Entry(add_win)
        remarks_entry.pack()

        tk.Label(add_win, text="Date (YYYY-MM-DD):").pack(pady=(20, 5))
        date_entry = tk.Entry(add_win)
        date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        date_entry.pack()

        def save_transaction():
            try:
                amount = float(amount_entry.get())
            except ValueError:
                messagebox.showerror("Error", "Amount must be a number")
                return

            txn_type = type_var.get()
            remarks = remarks_entry.get()
            date_str = date_entry.get()

            # Validate date format
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Error", "Date must be in YYYY-MM-DD format")
                return

            success = self.fm.add_transaction(amount, txn_type, remarks, date_str)
            if success:
                messagebox.showinfo("Success", "Transaction added successfully")
                add_win.destroy()
                self.populate_table()
            else:
                messagebox.showerror("Error", "Failed to add transaction")

        tk.Button(add_win, text="Save", command=save_transaction).pack(pady=20)

    def delete_selected(self):
        selected = self.table.selection()
        if not selected:
            messagebox.showwarning("Warning", "No row selected to delete.")
            return

        confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete the selected transaction?")
        if not confirm:
            return

        for sel in selected:
            values = self.table.item(sel)["values"]
            transaction_id = values[0]
            success = self.fm.delete_transaction(transaction_id)
            if not success:
                messagebox.showerror("Error", f"Failed to delete transaction with ID {transaction_id}")
        self.populate_table()


if __name__ == "__main__":
    root = tk.Tk()
    app = FinanceApp(root)
    root.mainloop()
