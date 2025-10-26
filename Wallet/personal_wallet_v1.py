import tkinter as tk
from tkinter import messagebox
import json
from datetime import datetime

class BasicWalletGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Personal Wallet - Basic Version")
        self.root.geometry("600x600")
        self.balance = 3629.50  # Starting balance (can be loaded from file)
        self.transactions = []
        
        self.load_data()  # Load data from file if exists

        # Current Balance Label
        self.balance_label = tk.Label(self.root, text=f"Current Balance: ${self.balance:.2f}", font=("Arial", 16), bg="#4CAF50", fg="white")
        self.balance_label.pack(fill="both")

        # Frame for Transaction Input
        self.transaction_frame = tk.Frame(self.root, pady=10)
        self.transaction_frame.pack()

        # Amount Entry
        self.amount_label = tk.Label(self.transaction_frame, text="Amount:", font=("Arial", 12))
        self.amount_label.grid(row=0, column=0, padx=10)
        self.amount_entry = tk.Entry(self.transaction_frame, font=("Arial", 12))
        self.amount_entry.grid(row=0, column=1)

        # Transaction Type (Income/Expense)
        self.type_label = tk.Label(self.transaction_frame, text="Type:", font=("Arial", 12))
        self.type_label.grid(row=1, column=0, padx=10)
        self.type_var = tk.StringVar(value="income")
        self.type_income_rb = tk.Radiobutton(self.transaction_frame, text="Income", variable=self.type_var, value="income", font=("Arial", 12))
        self.type_expense_rb = tk.Radiobutton(self.transaction_frame, text="Expense", variable=self.type_var, value="expense", font=("Arial", 12))
        self.type_income_rb.grid(row=1, column=1)
        self.type_expense_rb.grid(row=1, column=2)

        # Category Dropdown
        self.category_label = tk.Label(self.transaction_frame, text="Category:", font=("Arial", 12))
        self.category_label.grid(row=2, column=0, padx=10)
        self.category_var = tk.StringVar()
        self.category_dropdown = tk.OptionMenu(self.transaction_frame, self.category_var, "Salary", "Entertainment", "Food", "Other")
        self.category_dropdown.config(font=("Arial", 12))
        self.category_dropdown.grid(row=2, column=1)

        # Description Entry
        self.description_label = tk.Label(self.transaction_frame, text="Description:", font=("Arial", 12))
        self.description_label.grid(row=3, column=0, padx=10)
        self.description_entry = tk.Entry(self.transaction_frame, font=("Arial", 12))
        self.description_entry.grid(row=3, column=1)

        # Add Transaction Buttons
        self.add_income_button = tk.Button(self.transaction_frame, text="Add Income", command=self.add_income, bg="#4CAF50", fg="white", font=("Arial", 12))
        self.add_income_button.grid(row=4, column=0, padx=10, pady=10)
        self.add_expense_button = tk.Button(self.transaction_frame, text="Add Expense", command=self.add_expense, bg="#F44336", fg="white", font=("Arial", 12))
        self.add_expense_button.grid(row=4, column=1, padx=10)

        # Clear Form Button
        self.clear_form_button = tk.Button(self.transaction_frame, text="Clear Form", command=self.clear_form, font=("Arial", 12))
        self.clear_form_button.grid(row=4, column=2)

        # Transaction History Section
        self.history_label = tk.Label(self.root, text="Transaction History", font=("Arial", 14, "bold"))
        self.history_label.pack()

        self.history_tree = tk.Listbox(self.root, height=10, width=60, font=("Arial", 12))
        self.history_tree.pack(pady=10)

        # Refresh the history display
        self.refresh_history()

    def add_income(self):
        self.add_transaction("Income")

    def add_expense(self):
        self.add_transaction("Expense")

    def add_transaction(self, type_):
        try:
            amount = float(self.amount_entry.get())
            category = self.category_var.get()
            description = self.description_entry.get() or "No description"
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if type_ == "Income":
                self.balance += amount
            elif type_ == "Expense":
                self.balance -= amount

            transaction = {
                "amount": amount,
                "type": type_,
                "category": category,
                "description": description,
                "date": date
            }

            self.transactions.append(transaction)
            self.refresh_history()
            self.balance_label.config(text=f"Current Balance: ${self.balance:.2f}")

            # Clear the form
            self.clear_form()
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid amount.")

    def clear_form(self):
        self.amount_entry.delete(0, tk.END)
        self.category_var.set("Salary")
        self.description_entry.delete(0, tk.END)

    def refresh_history(self):
        # Clear the current list
        self.history_tree.delete(0, tk.END)

        # Add transactions to the list
        for idx, trans in enumerate(self.transactions, 1):
            self.history_tree.insert(tk.END, f"{idx}. ${trans['amount']:.2f} | {trans['type']} | {trans['category']} | {trans['description']} | {trans['date']}")

        self.save_data()

    def save_data(self):
        data = {
            "balance": self.balance,
            "transactions": self.transactions
        }
        try:
            with open("wallet_data.json", "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            messagebox.showerror("Error", f"Error saving data: {e}")

    def load_data(self):
        try:
            with open("wallet_data.json", "r") as f:
                data = json.load(f)
                self.balance = data.get("balance", 0)
                self.transactions = data.get("transactions", [])
        except FileNotFoundError:
            pass  # If no data file is found, start fresh
        except Exception as e:
            messagebox.showerror("Error", f"Error loading data: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    wallet = BasicWalletGUI(root)
    root.mainloop()
