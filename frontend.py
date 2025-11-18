import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import csv
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import openpyxl
import nepali_datetime


from backend import FinanceManager, Transaction


class FinanceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Personal Finance Manager")
        self.root.geometry("900x600")

        self.fm = FinanceManager()
        self.selected_transaction: Transaction | None = None

        self.create_widgets()
        self.populate_table()
        self.update_summary_labels()

    def create_widgets(self):
        # --- Top Frame: Add Transaction Form ---
        form_frame = tk.LabelFrame(self.root, text="Add / Update Transaction", padx=10, pady=10)
        form_frame.pack(fill="x", padx=10, pady=10)

        tk.Label(form_frame, text="Amount:").grid(row=0, column=0, sticky="w")
        self.amount_entry = tk.Entry(form_frame, width=15)
        self.amount_entry.grid(row=0, column=1, padx=5)

        tk.Label(form_frame, text="Type:").grid(row=0, column=2, sticky="w")
        self.type_var = tk.StringVar(value="income")
        ttk.Combobox(form_frame, textvariable=self.type_var, values=["income", "expense"], width=12).grid(row=0, column=3)

        tk.Label(form_frame, text="Date (YYYY-MM-DD):").grid(row=0, column=4, sticky="w")
        self.date_entry = tk.Entry(form_frame, width=15)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.date_entry.grid(row=0, column=5, padx=5)

        tk.Label(form_frame, text="Remarks:").grid(row=1, column=0, sticky="w", pady=5)
        self.remarks_entry = tk.Entry(form_frame, width=40)
        self.remarks_entry.grid(row=1, column=1, columnspan=5, sticky="w")

        tk.Button(form_frame, text="Add Transaction", command=self.add_transaction).grid(row=2, column=1, pady=8)
        tk.Button(form_frame, text="Update Selected", command=self.update_transaction).grid(row=2, column=2, pady=8)
        tk.Button(form_frame, text="Delete Selected", command=self.delete_transaction).grid(row=2, column=3, pady=8)

        # --- Summary Frame ---
        summary_frame = tk.Frame(self.root)
        summary_frame.pack(fill="x", padx=10)

        self.balance_label = tk.Label(summary_frame, text="Balance: 0", font=("Arial", 12, "bold"))
        self.balance_label.pack(side="left", padx=10)

        self.income_label = tk.Label(summary_frame, text="Total Income: 0", fg="green")
        self.income_label.pack(side="left", padx=10)

        self.expense_label = tk.Label(summary_frame, text="Total Expense: 0", fg="red")
        self.expense_label.pack(side="left", padx=10)

        # NEW BUTTONS
        tk.Button(summary_frame, text="Show Graph", command=self.show_graph).pack(side="right", padx=5)
        tk.Button(summary_frame, text="Export CSV", command=self.export_csv).pack(side="right", padx=5)
        tk.Button(summary_frame, text="Bulk Upload Excel", command=self.bulk_upload_excel).pack(side="right", padx=5)


        # --- Table Frame ---
        table_frame = tk.Frame(self.root)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        columns = ("id", "amount", "type", "remarks", "date", "created_at")
        self.table = ttk.Treeview(table_frame, columns=columns, show="headings")
        self.table.pack(fill="both", expand=True)

        for col in columns:
            self.table.heading(col, text=col.capitalize())
            self.table.column(col, anchor=tk.CENTER, width=120)

        self.table.bind("<<TreeviewSelect>>", self.select_transaction)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.table.yview)
        self.table.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

    def populate_table(self):
        for row in self.table.get_children():
            self.table.delete(row)

        for tr in self.fm.get_transactions():
            self.table.insert("", tk.END, values=(tr.id, tr.amount, tr.type, tr.remarks, tr.date, tr.created_at))

    def select_transaction(self, event):
        selected = self.table.selection()
        if not selected:
            return
        values = self.table.item(selected[0])["values"]
        self.selected_transaction = Transaction(*values)

        # Populate form fields
        self.amount_entry.delete(0, tk.END)
        self.amount_entry.insert(0, values[1])

        self.type_var.set(values[2])

        self.remarks_entry.delete(0, tk.END)
        self.remarks_entry.insert(0, values[3])

        self.date_entry.delete(0, tk.END)
        self.date_entry.insert(0, values[4])

    def add_transaction(self):
        try:
            amount = float(self.amount_entry.get())
            type_ = self.type_var.get()
            remarks = self.remarks_entry.get()
            date = self.date_entry.get()

            self.fm.add_transaction(amount, type_, remarks, date)
            self.populate_table()
            self.update_summary_labels()
            self.clear_form()
        except ValueError:
            messagebox.showerror("Error", "Invalid amount")

    def update_transaction(self):
        if not self.selected_transaction:
            messagebox.showwarning("Warning", "No transaction selected")
            return

        try:
            self.fm.update_transaction(
                self.selected_transaction.id,
                amount=float(self.amount_entry.get()),
                type=self.type_var.get(),
                remarks=self.remarks_entry.get(),
                date=self.date_entry.get(),
            )
            self.populate_table()
            self.update_summary_labels()
        except ValueError:
            messagebox.showerror("Error", "Invalid amount")

    def delete_transaction(self):
        if not self.selected_transaction:
            messagebox.showwarning("Warning", "No transaction selected")
            return

        if messagebox.askyesno("Confirm", "Delete selected transaction?"):
            self.fm.delete_transaction(self.selected_transaction.id)
            self.populate_table()
            self.update_summary_labels()
            self.clear_form()

    def update_summary_labels(self):
        self.balance_label.config(text=f"Balance: {self.fm.get_balance():.2f}")
        self.income_label.config(text=f"Total Income: {self.fm.get_income_total():.2f}")
        self.expense_label.config(text=f"Total Expense: {self.fm.get_expense_total():.2f}")

    def clear_form(self):
        self.amount_entry.delete(0, tk.END)
        self.remarks_entry.delete(0, tk.END)
        self.date_entry.delete(0, tk.END)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.type_var.set("income")
        self.selected_transaction = None

    # ========================= CSV EXPORT =========================
    def export_csv(self):
        transactions = self.fm.get_transactions()
        if not transactions:
            messagebox.showinfo("Info", "No transactions to export.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
            initialfile=f"transactions_{datetime.now().strftime('%Y-%m-%d')}.csv"
        )
        if not file_path:
            return  # Cancelled

        with open(file_path, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["id", "amount", "type", "remarks", "date", "created_at"])
            for tr in transactions:
                writer.writerow([tr.id, tr.amount, tr.type, tr.remarks, tr.date, tr.created_at])

        messagebox.showinfo("Success", f"CSV exported successfully!\n{file_path}")

    # ========================= GRAPH WINDOW =========================
    def show_graph(self):
        transactions = self.fm.get_transactions()
        if not transactions:
            messagebox.showinfo("Info", "No data available for graph.")
            return

        transactions.sort(key=lambda t: t.date)

        dates = [t.date for t in transactions]
        balance_values = []
        balance = 0

        for tr in transactions:
            balance += tr.amount if tr.type == "income" else -tr.amount
            balance_values.append(balance)

        graph_window = tk.Toplevel(self.root)
        graph_window.title("Balance Over Time")
        graph_window.geometry("800x500")
        graph_window.resizable(True, True)  # ✅ resizable enabled

        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(dates, balance_values, marker="o")
        ax.set_title("Balance Over Time")
        ax.set_xlabel("Date")
        ax.set_ylabel("Balance")
        ax.grid(True)
        fig.autofmt_xdate()

        canvas = FigureCanvasTkAgg(fig, master=graph_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # ========================= Bulk Upload =========================
    def bulk_upload_excel(self):
        file_path = filedialog.askopenfilename(
            title="Select File",
            filetypes=[("Excel or CSV", "*.xlsx *.csv"), ("Excel", "*.xlsx"), ("CSV", "*.csv")]
        )

        if not file_path:
            return  # User cancelled

        count = 0

        try:
            # ---------------------------------------------------
            # CASE 1: CSV FILE
            # ---------------------------------------------------
            if file_path.lower().endswith(".csv"):
                import csv
                with open(file_path, newline="", encoding="utf-8") as f:
                    reader = csv.reader(f)
                    next(reader, None)  # skip header

                    for row in reader:
                        if len(row) < 4:
                            continue  # not enough columns

                        amount, type_, remarks, date = row

                        # Validate amount
                        try:
                            amount = float(amount)
                        except:
                            continue

                        type_ = type_.strip().lower()
                        remarks = remarks.strip()

                        # Fix date formatting
                        date = str(date).replace("/", "-")

                        self.fm.add_transaction(amount, type_, remarks, date)
                        count += 1

            # ---------------------------------------------------
            # CASE 2: EXCEL FILE
            # ---------------------------------------------------
            else:
                wb = openpyxl.load_workbook(file_path)
                sheet = wb.active

                for i, row in enumerate(sheet.iter_rows(values_only=True)):
                    if i == 0:
                        continue  # skip header

                    if row is None or len(row) < 4:
                        continue

                    amount, type_, remarks, date = row

                    if amount is None or type_ is None or date is None:
                        continue

                    # Amount must be numeric
                    try:
                        amount = float(amount)
                    except:
                        continue

                    type_ = str(type_).strip().lower()
                    remarks = remarks if remarks else ""

                    # Convert date to string
                    if isinstance(date, datetime):
                        date = date.strftime("%Y-%m-%d")
                    else:
                        date = str(date).replace("/", "-")

                    self.fm.add_transaction(amount, type_, remarks, date)
                    count += 1

            # ---------------------------------------------------
            # AFTER IMPORT
            # ---------------------------------------------------
            self.populate_table()
            self.update_summary_labels()
            messagebox.showinfo("Success", f"{count} transactions imported successfully!")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to import file:\n{e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = FinanceApp(root)
    root.mainloop()
