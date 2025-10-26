import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from decimal import Decimal
try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Warning: matplotlib not installed. Charts will not be available.")
    print("To install: pip install matplotlib")
import csv
from collections import defaultdict

class PersonalWallet:
    """Main wallet application class"""
    
    def __init__(self, data_file="wallet_data_v2.json"):
        self.data_file = data_file
        self.transactions = []
        self.balance = Decimal("0.00")
        self.budget = Decimal("0.00")
        self.categories = {
            "income": ["Salary", "Freelance", "Investment", "Bonus", "Other"],
            "expense": ["Food", "Transport", "Entertainment", "Utilities", "Shopping", "Healthcare", "Bills", "Other"]
        }
        self.load_data()
    
    def load_data(self):
        """Load wallet data from JSON file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.transactions = data.get('transactions', [])
                    self.balance = Decimal(str(data.get('balance', '0.00')))
                    self.budget = Decimal(str(data.get('budget', '0.00')))
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load data: {str(e)}")
        else:
            self.balance = Decimal("0.00")
            self.budget = Decimal("0.00")
            self.transactions = []
    
    def save_data(self):
        """Save wallet data to JSON file"""
        try:
            data = {
                'transactions': self.transactions,
                'balance': str(self.balance),
                'budget': str(self.budget),
                'last_updated': datetime.now().isoformat()
            }
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save data: {str(e)}")
    
    def add_transaction(self, amount, trans_type, category, description=""):
        """Add a new transaction"""
        try:
            amount = Decimal(str(amount))
            
            if amount <= 0:
                raise ValueError("Amount must be greater than 0")
            
            if trans_type == "income":
                self.balance += amount
            elif trans_type == "expense":
                if amount > self.balance:
                    raise ValueError("Insufficient balance for this expense")
                self.balance -= amount
            else:
                raise ValueError("Invalid transaction type")
            
            transaction = {
                'id': len(self.transactions) + 1,
                'amount': f"+${amount:.2f}" if trans_type == "income" else f"-${amount:.2f}",
                'raw_amount': float(amount),
                'type': trans_type.capitalize(),
                'category': category,
                'description': description if description else "No description",
                'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            self.transactions.append(transaction)
            self.save_data()
            return True, "Transaction added successfully"
        
        except ValueError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def get_balance(self):
        """Get current balance"""
        return f"${self.balance:.2f}"
    
    def get_transactions(self):
        """Get all transactions"""
        return sorted(self.transactions, key=lambda x: x['id'], reverse=True)
    
    def delete_transaction(self, trans_id):
        """Delete a transaction by ID"""
        try:
            trans = next((t for t in self.transactions if t['id'] == trans_id), None)
            if not trans:
                return False, "Transaction not found"
            
            # Reverse the transaction
            amount = Decimal(trans['amount'].replace('$', '').replace('+', '').replace('-', ''))
            if trans['type'] == "Income":
                self.balance -= amount
            else:
                self.balance += amount
            
            self.transactions = [t for t in self.transactions if t['id'] != trans_id]
            self.save_data()
            return True, "Transaction deleted successfully"
        except Exception as e:
            return False, str(e)
    
    def get_statistics(self):
        """Calculate financial statistics"""
        total_income = sum(Decimal(t['amount'].replace('$', '').replace('+', '')) 
                          for t in self.transactions if t['type'] == "Income")
        total_expenses = sum(Decimal(t['amount'].replace('$', '').replace('-', '')) 
                            for t in self.transactions if t['type'] == "Expense")
        
        expense_transactions = [t for t in self.transactions if t['type'] == "Expense"]
        avg_expense = total_expenses / len(expense_transactions) if expense_transactions else Decimal("0.00")
        
        largest_expense = max((Decimal(t['amount'].replace('$', '').replace('-', '')) 
                              for t in expense_transactions), default=Decimal("0.00"))
        
        return {
            'total_income': total_income,
            'total_expenses': total_expenses,
            'net_savings': total_income - total_expenses,
            'transaction_count': len(self.transactions),
            'avg_expense': avg_expense,
            'largest_expense': largest_expense
        }
    
    def get_expense_by_category(self):
        """Get expenses grouped by category"""
        expenses = defaultdict(float)
        for t in self.transactions:
            if t['type'] == "Expense":
                amount = float(t['amount'].replace('$', '').replace('-', ''))
                expenses[t['category']] += amount
        return dict(expenses)
    
    def get_monthly_data(self, months=6):
        """Get income and expense data for last N months"""
        monthly_data = defaultdict(lambda: {'income': 0, 'expense': 0})
        
        for t in self.transactions:
            trans_date = datetime.strptime(t['date'], "%Y-%m-%d %H:%M:%S")
            month_key = trans_date.strftime("%Y-%m")
            amount = abs(float(t['amount'].replace('$', '').replace('+', '').replace('-', '')))
            
            if t['type'] == "Income":
                monthly_data[month_key]['income'] += amount
            else:
                monthly_data[month_key]['expense'] += amount
        
        # Get last N months
        sorted_months = sorted(monthly_data.keys())[-months:]
        return {month: monthly_data[month] for month in sorted_months}
    
    def search_transactions(self, search_type=None, category=None, date_from=None, date_to=None):
        """Search transactions with filters"""
        results = self.transactions
        
        if search_type and search_type != "All":
            results = [t for t in results if t['type'] == search_type]
        
        if category and category != "All":
            results = [t for t in results if t['category'] == category]
        
        if date_from:
            results = [t for t in results 
                      if datetime.strptime(t['date'], "%Y-%m-%d %H:%M:%S") >= date_from]
        
        if date_to:
            results = [t for t in results 
                      if datetime.strptime(t['date'], "%Y-%m-%d %H:%M:%S") <= date_to]
        
        return sorted(results, key=lambda x: x['id'], reverse=True)
    
    def set_budget(self, amount):
        """Set monthly budget"""
        try:
            self.budget = Decimal(str(amount))
            self.save_data()
            return True, "Budget set successfully"
        except Exception as e:
            return False, str(e)
    
    def get_budget_status(self):
        """Get current budget status"""
        if self.budget == 0:
            return None
        
        # Get current month expenses
        current_month = datetime.now().strftime("%Y-%m")
        month_expenses = sum(
            Decimal(t['amount'].replace('$', '').replace('-', ''))
            for t in self.transactions
            if t['type'] == "Expense" and t['date'].startswith(current_month)
        )
        
        remaining = self.budget - month_expenses
        percentage = (month_expenses / self.budget * 100) if self.budget > 0 else 0
        
        return {
            'budget': self.budget,
            'spent': month_expenses,
            'remaining': remaining,
            'percentage': float(percentage)
        }


class WalletGUI:
    """GUI for the Personal Wallet application"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Personal Wallet - Advanced Version")
        self.root.geometry("1000x750")
        self.root.resizable(True, True)
        
        self.wallet = PersonalWallet()
        self.setup_ui()
        self.refresh_all()
    
    def setup_ui(self):
        """Setup the user interface"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.transactions_tab = tk.Frame(self.notebook, bg='white')
        self.analytics_tab = tk.Frame(self.notebook, bg='white')
        self.budget_tab = tk.Frame(self.notebook, bg='white')
        self.search_tab = tk.Frame(self.notebook, bg='white')
        
        self.notebook.add(self.transactions_tab, text="📊 Transactions")
        self.notebook.add(self.analytics_tab, text="📈 Analytics")
        self.notebook.add(self.budget_tab, text="💰 Budget")
        self.notebook.add(self.search_tab, text="🔍 Search")
        
        # Setup each tab
        self.setup_transactions_tab()
        self.setup_analytics_tab()
        self.setup_budget_tab()
        self.setup_search_tab()
    
    def setup_transactions_tab(self):
        """Setup the transactions tab"""
        # Main container
        main_frame = tk.Frame(self.transactions_tab, bg='white')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Balance display with dark background and Export button
        balance_frame = tk.Frame(main_frame, bg='#3a4f5c', relief=tk.FLAT, borderwidth=0)
        balance_frame.pack(fill=tk.X, pady=(0, 20))
        
        balance_left = tk.Frame(balance_frame, bg='#3a4f5c')
        balance_left.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        balance_text = tk.Label(balance_left, text=f"Current Balance: $0.00", 
                               font=("Arial", 24, "bold"), 
                               foreground="#4caf50", 
                               bg='#3a4f5c')
        balance_text.pack(pady=30, padx=20)
        
        self.balance_display = balance_text
        
        # Export CSV button
        export_btn = tk.Button(balance_frame, text="📊 Export CSV", command=self.export_to_csv,
                              bg='#2196f3', fg='white', font=("Arial", 10, "bold"),
                              relief=tk.RAISED, borderwidth=2, padx=15, pady=10,
                              cursor='hand2', activebackground='#1976d2')
        export_btn.pack(side=tk.RIGHT, padx=20, pady=20)
        
        # Add Transaction Section
        trans_frame = tk.LabelFrame(main_frame, text="Add Transaction", 
                                   font=("Arial", 12, "bold"),
                                   bg='white', fg='black',
                                   relief=tk.GROOVE, borderwidth=2, padx=15, pady=15)
        trans_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Amount
        tk.Label(trans_frame, text="Amount:", font=("Arial", 10), bg='white').grid(row=0, column=0, sticky=tk.W, padx=5, pady=8)
        self.amount_entry = tk.Entry(trans_frame, width=18, font=("Arial", 10))
        self.amount_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=8)
        
        # Type
        tk.Label(trans_frame, text="Type:", font=("Arial", 10), bg='white').grid(row=0, column=2, sticky=tk.W, padx=(30, 5), pady=8)
        self.type_var = tk.StringVar(value="expense")
        type_combo = ttk.Combobox(trans_frame, textvariable=self.type_var, 
                                  values=["income", "expense"], state="readonly", width=15, font=("Arial", 10))
        type_combo.grid(row=0, column=3, sticky=tk.W, padx=5, pady=8)
        type_combo.bind("<<ComboboxSelected>>", self.on_type_change)
        
        # Category
        tk.Label(trans_frame, text="Category:", font=("Arial", 10), bg='white').grid(row=1, column=0, sticky=tk.W, padx=5, pady=8)
        self.category_var = tk.StringVar(value="Food")
        self.category_combo = ttk.Combobox(trans_frame, textvariable=self.category_var, 
                                           values=self.wallet.categories["expense"], 
                                           state="readonly", width=15, font=("Arial", 10))
        self.category_combo.grid(row=1, column=1, sticky=tk.W, padx=5, pady=8)
        
        # Description
        tk.Label(trans_frame, text="Description:", font=("Arial", 10), bg='white').grid(row=1, column=2, sticky=tk.W, padx=(30, 5), pady=8)
        self.description_entry = tk.Entry(trans_frame, width=30, font=("Arial", 10))
        self.description_entry.grid(row=1, column=3, sticky=tk.EW, padx=5, pady=8)
        
        # Buttons with custom styling
        button_frame = tk.Frame(trans_frame, bg='white')
        button_frame.grid(row=2, column=0, columnspan=4, sticky=tk.W, pady=(15, 5))
        
        add_income_btn = tk.Button(button_frame, text="✚ Add Income", command=self.add_income,
                                   bg='#4caf50', fg='white', font=("Arial", 10, "bold"),
                                   relief=tk.RAISED, borderwidth=2, padx=20, pady=8,
                                   cursor='hand2', activebackground='#45a049')
        add_income_btn.pack(side=tk.LEFT, padx=5)
        
        add_expense_btn = tk.Button(button_frame, text="➖ Add Expense", command=self.add_expense,
                                    bg='#f44336', fg='white', font=("Arial", 10, "bold"),
                                    relief=tk.RAISED, borderwidth=2, padx=20, pady=8,
                                    cursor='hand2', activebackground='#da190b')
        add_expense_btn.pack(side=tk.LEFT, padx=5)
        
        clear_btn = tk.Button(button_frame, text="🗑 Clear Form", command=self.clear_form,
                             bg='#9e9e9e', fg='white', font=("Arial", 10, "bold"),
                             relief=tk.RAISED, borderwidth=2, padx=20, pady=8,
                             cursor='hand2', activebackground='#757575')
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        # Transaction History Section
        hist_frame = tk.LabelFrame(main_frame, text="Transaction History", 
                                  font=("Arial", 12, "bold"),
                                  bg='white', fg='black',
                                  relief=tk.GROOVE, borderwidth=2, padx=15, pady=15)
        hist_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create Treeview
        columns = ("#", "Amount", "Type", "Category", "Description", "Date")
        
        # Style configuration
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview", 
                       background="white",
                       foreground="black",
                       rowheight=25,
                       fieldbackground="white",
                       font=("Arial", 10))
        style.configure("Treeview.Heading", 
                       font=("Arial", 10, "bold"),
                       background="#e0e0e0",
                       foreground="black")
        style.map('Treeview', background=[('selected', '#0078d7')])
        
        self.tree = ttk.Treeview(hist_frame, columns=columns, height=10, show="headings")
        
        # Define headings and columns
        self.tree.column("#", width=40, anchor=tk.CENTER)
        self.tree.column("Amount", width=100, anchor=tk.CENTER)
        self.tree.column("Type", width=90, anchor=tk.CENTER)
        self.tree.column("Category", width=120, anchor=tk.CENTER)
        self.tree.column("Description", width=200, anchor=tk.W)
        self.tree.column("Date", width=160, anchor=tk.CENTER)
        
        self.tree.heading("#", text="#")
        self.tree.heading("Amount", text="Amount")
        self.tree.heading("Type", text="Type")
        self.tree.heading("Category", text="Category")
        self.tree.heading("Description", text="Description")
        self.tree.heading("Date", text="Date")
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(hist_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Right-click menu for deleting transactions
        self.tree.bind("<Button-3>", self.on_right_click)
    
    def on_type_change(self, event=None):
        """Update category dropdown when type changes"""
        trans_type = self.type_var.get()
        categories = self.wallet.categories.get(trans_type, [])
        self.category_combo['values'] = categories
        self.category_var.set(categories[0] if categories else "")
    
    def add_income(self):
        """Add income transaction"""
        self.add_transaction("income")
    
    def add_expense(self):
        """Add expense transaction"""
        self.add_transaction("expense")
    
    def add_transaction(self, trans_type):
        """Add a transaction"""
        try:
            amount = self.amount_entry.get().strip()
            category = self.category_var.get()
            description = self.description_entry.get().strip()
            
            if not amount:
                messagebox.showwarning("Validation Error", "Please enter an amount")
                return
            
            success, message = self.wallet.add_transaction(amount, trans_type, category, description)
            
            if success:
                messagebox.showinfo("Success", message)
                self.clear_form()
                self.refresh_all()
            else:
                messagebox.showerror("Error", message)
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add transaction: {str(e)}")
    
    def clear_form(self):
        """Clear the form fields only"""
        try:
            # Clear form fields
            self.amount_entry.delete(0, tk.END)
            self.description_entry.delete(0, tk.END)
            
            # Reset type to expense (default for v2)
            self.type_var.set("expense")
            
            # Update category dropdown based on type
            self.on_type_change()
            
            # Reset category to default
            self.category_var.set("Food")
            
            # Set focus back to amount entry
            self.amount_entry.focus_set()
        except Exception as e:
            print(f"Error clearing form: {str(e)}")
            messagebox.showerror("Error", f"Failed to clear form: {str(e)}")
    
    def setup_analytics_tab(self):
        """Setup the analytics tab"""
        main_frame = tk.Frame(self.analytics_tab, bg='white')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Financial Statistics
        stats_frame = tk.LabelFrame(main_frame, text="Financial Statistics",
                                   font=("Arial", 12, "bold"),
                                   bg='white', fg='black',
                                   relief=tk.GROOVE, borderwidth=2, padx=20, pady=15)
        stats_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Create statistics labels
        stats_grid = tk.Frame(stats_frame, bg='white')
        stats_grid.pack(fill=tk.X)
        
        # Row 1
        tk.Label(stats_grid, text="Total Income:", font=("Arial", 10, "bold"), bg='white').grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        self.total_income_label = tk.Label(stats_grid, text="$0.00", font=("Arial", 10), fg='#4caf50', bg='white')
        self.total_income_label.grid(row=0, column=1, sticky=tk.W, padx=10, pady=5)
        
        tk.Label(stats_grid, text="Total Expenses:", font=("Arial", 10, "bold"), bg='white').grid(row=0, column=2, sticky=tk.W, padx=10, pady=5)
        self.total_expenses_label = tk.Label(stats_grid, text="$0.00", font=("Arial", 10), fg='#f44336', bg='white')
        self.total_expenses_label.grid(row=0, column=3, sticky=tk.W, padx=10, pady=5)
        
        tk.Label(stats_grid, text="Net Savings:", font=("Arial", 10, "bold"), bg='white').grid(row=0, column=4, sticky=tk.W, padx=10, pady=5)
        self.net_savings_label = tk.Label(stats_grid, text="$0.00", font=("Arial", 10), fg='#2196f3', bg='white')
        self.net_savings_label.grid(row=0, column=5, sticky=tk.W, padx=10, pady=5)
        
        # Row 2
        tk.Label(stats_grid, text="Transactions:", font=("Arial", 10, "bold"), bg='white').grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        self.transactions_count_label = tk.Label(stats_grid, text="0", font=("Arial", 10), fg='#9c27b0', bg='white')
        self.transactions_count_label.grid(row=1, column=1, sticky=tk.W, padx=10, pady=5)
        
        tk.Label(stats_grid, text="Avg Monthly Expense:", font=("Arial", 10, "bold"), bg='white').grid(row=1, column=2, sticky=tk.W, padx=10, pady=5)
        self.avg_expense_label = tk.Label(stats_grid, text="$0.00", font=("Arial", 10), fg='#ff9800', bg='white')
        self.avg_expense_label.grid(row=1, column=3, sticky=tk.W, padx=10, pady=5)
        
        tk.Label(stats_grid, text="Largest Expense:", font=("Arial", 10, "bold"), bg='white').grid(row=1, column=4, sticky=tk.W, padx=10, pady=5)
        self.largest_expense_label = tk.Label(stats_grid, text="$0.00", font=("Arial", 10), fg='#ff5722', bg='white')
        self.largest_expense_label.grid(row=1, column=5, sticky=tk.W, padx=10, pady=5)
        
        # Charts Frame
        charts_frame = tk.LabelFrame(main_frame, text="Expense Analytics",
                                    font=("Arial", 12, "bold"),
                                    bg='white', fg='black',
                                    relief=tk.GROOVE, borderwidth=2, padx=15, pady=15)
        charts_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create frame for charts
        self.charts_container = tk.Frame(charts_frame, bg='white')
        self.charts_container.pack(fill=tk.BOTH, expand=True)
    
    def setup_budget_tab(self):
        """Setup the budget tab"""
        main_frame = tk.Frame(self.budget_tab, bg='white')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Budget Setup
        budget_setup_frame = tk.LabelFrame(main_frame, text="Monthly Budget Setup",
                                          font=("Arial", 12, "bold"),
                                          bg='white', fg='black',
                                          relief=tk.GROOVE, borderwidth=2, padx=20, pady=15)
        budget_setup_frame.pack(fill=tk.X, pady=(0, 15))
        
        setup_grid = tk.Frame(budget_setup_frame, bg='white')
        setup_grid.pack(fill=tk.X)
        
        tk.Label(setup_grid, text="Monthly Budget Amount:", font=("Arial", 10, "bold"), bg='white').grid(row=0, column=0, sticky=tk.W, padx=10, pady=10)
        self.budget_entry = tk.Entry(setup_grid, width=20, font=("Arial", 10))
        self.budget_entry.grid(row=0, column=1, sticky=tk.W, padx=10, pady=10)
        self.budget_entry.insert(0, "0.0")
        
        set_budget_btn = tk.Button(setup_grid, text="📊 Set Budget", command=self.set_budget,
                                  bg='#9c27b0', fg='white', font=("Arial", 10, "bold"),
                                  relief=tk.RAISED, borderwidth=2, padx=20, pady=8,
                                  cursor='hand2', activebackground='#7b1fa2')
        set_budget_btn.grid(row=0, column=2, sticky=tk.W, padx=10, pady=10)
        
        # Budget Progress
        progress_frame = tk.LabelFrame(main_frame, text="Budget Progress",
                                      font=("Arial", 12, "bold"),
                                      bg='white', fg='black',
                                      relief=tk.GROOVE, borderwidth=2, padx=20, pady=15)
        progress_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.budget_status_label = tk.Label(progress_frame, text="Budget: $0.00 | Spent: $0.00 | Remaining: $0.00",
                                           font=("Arial", 11), bg='white')
        self.budget_status_label.pack(pady=10)
        
        # Progress bar
        self.budget_progress = ttk.Progressbar(progress_frame, length=500, mode='determinate')
        self.budget_progress.pack(pady=10)
        
        self.budget_percentage_label = tk.Label(progress_frame, text="0%", font=("Arial", 10, "bold"), bg='white')
        self.budget_percentage_label.pack(pady=5)
        
        # Budget Alerts
        alerts_frame = tk.LabelFrame(main_frame, text="Budget Alerts",
                                    font=("Arial", 12, "bold"),
                                    bg='white', fg='black',
                                    relief=tk.GROOVE, borderwidth=2, padx=20, pady=15)
        alerts_frame.pack(fill=tk.BOTH, expand=True)
        
        self.alerts_text = tk.Text(alerts_frame, height=10, font=("Arial", 10), wrap=tk.WORD, bg='#f5f5f5')
        self.alerts_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def setup_search_tab(self):
        """Setup the search tab"""
        main_frame = tk.Frame(self.search_tab, bg='white')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Search Filters
        filter_frame = tk.LabelFrame(main_frame, text="Search Filters",
                                    font=("Arial", 12, "bold"),
                                    bg='white', fg='black',
                                    relief=tk.GROOVE, borderwidth=2, padx=20, pady=15)
        filter_frame.pack(fill=tk.X, pady=(0, 15))
        
        filter_grid = tk.Frame(filter_frame, bg='white')
        filter_grid.pack(fill=tk.X)
        
        # Type filter
        tk.Label(filter_grid, text="Type:", font=("Arial", 10), bg='white').grid(row=0, column=0, sticky=tk.W, padx=10, pady=8)
        self.search_type_var = tk.StringVar(value="All")
        type_search_combo = ttk.Combobox(filter_grid, textvariable=self.search_type_var,
                                        values=["All", "Income", "Expense"], state="readonly", width=15, font=("Arial", 10))
        type_search_combo.grid(row=0, column=1, sticky=tk.W, padx=10, pady=8)
        
        # Category filter
        tk.Label(filter_grid, text="Category:", font=("Arial", 10), bg='white').grid(row=0, column=2, sticky=tk.W, padx=10, pady=8)
        self.search_category_var = tk.StringVar(value="All")
        all_categories = ["All"] + self.wallet.categories["income"] + self.wallet.categories["expense"]
        category_search_combo = ttk.Combobox(filter_grid, textvariable=self.search_category_var,
                                            values=list(set(all_categories)), state="readonly", width=15, font=("Arial", 10))
        category_search_combo.grid(row=0, column=3, sticky=tk.W, padx=10, pady=8)
        
        # Search button
        search_btn = tk.Button(filter_grid, text="🔍 Search", command=self.perform_search,
                              bg='#2196f3', fg='white', font=("Arial", 10, "bold"),
                              relief=tk.RAISED, borderwidth=2, padx=20, pady=8,
                              cursor='hand2', activebackground='#1976d2')
        search_btn.grid(row=0, column=4, sticky=tk.W, padx=10, pady=8)
        
        # Search Results
        results_frame = tk.LabelFrame(main_frame, text="Search Results",
                                     font=("Arial", 12, "bold"),
                                     bg='white', fg='black',
                                     relief=tk.GROOVE, borderwidth=2, padx=15, pady=15)
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create Treeview for search results
        columns = ("#", "Amount", "Type", "Category", "Description", "Date")
        
        self.search_tree = ttk.Treeview(results_frame, columns=columns, height=15, show="headings")
        
        # Define headings and columns
        self.search_tree.column("#", width=40, anchor=tk.CENTER)
        self.search_tree.column("Amount", width=100, anchor=tk.CENTER)
        self.search_tree.column("Type", width=90, anchor=tk.CENTER)
        self.search_tree.column("Category", width=120, anchor=tk.CENTER)
        self.search_tree.column("Description", width=200, anchor=tk.W)
        self.search_tree.column("Date", width=160, anchor=tk.CENTER)
        
        self.search_tree.heading("#", text="#")
        self.search_tree.heading("Amount", text="Amount")
        self.search_tree.heading("Type", text="Type")
        self.search_tree.heading("Category", text="Category")
        self.search_tree.heading("Description", text="Description")
        self.search_tree.heading("Date", text="Date")
        
        # Add scrollbar
        search_scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.search_tree.yview)
        self.search_tree.configure(yscroll=search_scrollbar.set)
        
        self.search_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        search_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def refresh_display(self):
        """Refresh the transactions display"""
        # Update balance
        self.balance_display.config(text=f"Current Balance: {self.wallet.get_balance()}")
        
        # Clear and update transaction tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for trans in self.wallet.get_transactions():
            self.tree.insert("", "end", values=(
                trans['id'],
                trans['amount'],
                trans['type'],
                trans['category'],
                trans['description'],
                trans['date']
            ))
    
    def refresh_all(self):
        """Refresh all tabs"""
        self.refresh_display()
        self.update_analytics()
        self.update_budget_display()
    
    def update_analytics(self):
        """Update analytics tab with charts and statistics"""
        try:
            stats = self.wallet.get_statistics()
            
            # Update statistics labels
            self.total_income_label.config(text=f"${stats['total_income']:.2f}")
            self.total_expenses_label.config(text=f"${stats['total_expenses']:.2f}")
            self.net_savings_label.config(text=f"${stats['net_savings']:.2f}")
            self.transactions_count_label.config(text=str(stats['transaction_count']))
            self.avg_expense_label.config(text=f"${stats['avg_expense']:.2f}")
            self.largest_expense_label.config(text=f"${stats['largest_expense']:.2f}")
            
            # Update charts
            self.update_charts()
        except Exception as e:
            print(f"Error updating analytics: {str(e)}")
    
    def update_charts(self):
        """Update pie chart and bar graph"""
        try:
            # Clear existing charts
            for widget in self.charts_container.winfo_children():
                widget.destroy()
            
            if not MATPLOTLIB_AVAILABLE:
                # Show message if matplotlib is not installed
                msg_frame = tk.Frame(self.charts_container, bg='white')
                msg_frame.pack(fill=tk.BOTH, expand=True)
                
                msg = tk.Label(msg_frame, 
                              text="📊 Charts not available\n\nMatplotlib is not installed.\n\nTo enable charts, install matplotlib:\npip install matplotlib",
                              font=("Arial", 12),
                              bg='white',
                              fg='#666666',
                              justify=tk.CENTER)
                msg.pack(expand=True)
                return
            
            # Create figure with subplots
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
            fig.patch.set_facecolor('white')
            
            # Pie Chart - Expense Distribution by Category
            expense_data = self.wallet.get_expense_by_category()
            if expense_data:
                colors = ['#81c784', '#ffb74d', '#e57373', '#ba68c8', '#64b5f6', '#ffd54f', '#4dd0e1', '#aed581']
                ax1.pie(expense_data.values(), labels=expense_data.keys(), autopct='%1.1f%%',
                       startangle=90, colors=colors[:len(expense_data)])
                ax1.set_title('Expense Distribution by Category', fontsize=12, fontweight='bold')
            else:
                ax1.text(0.5, 0.5, 'No expense data', ha='center', va='center', transform=ax1.transAxes)
                ax1.set_title('Expense Distribution by Category', fontsize=12, fontweight='bold')
            
            # Bar Graph - Income vs Expense (Last 6 Months)
            monthly_data = self.wallet.get_monthly_data(6)
            if monthly_data:
                months = list(monthly_data.keys())
                income = [monthly_data[m]['income'] for m in months]
                expense = [monthly_data[m]['expense'] for m in months]
                
                x = range(len(months))
                width = 0.35
                
                ax2.bar([i - width/2 for i in x], income, width, label='Income', color='#4caf50')
                ax2.bar([i + width/2 for i in x], expense, width, label='Expense', color='#f44336')
                
                ax2.set_xlabel('Month', fontweight='bold')
                ax2.set_ylabel('Amount ($)', fontweight='bold')
                ax2.set_title('Income vs Expense (Last 6 Months)', fontsize=12, fontweight='bold')
                ax2.set_xticks(x)
                ax2.set_xticklabels(months, rotation=45, ha='right')
                ax2.legend()
                ax2.grid(axis='y', alpha=0.3)
            else:
                ax2.text(0.5, 0.5, 'No monthly data', ha='center', va='center', transform=ax2.transAxes)
                ax2.set_title('Income vs Expense (Last 6 Months)', fontsize=12, fontweight='bold')
            
            plt.tight_layout()
            
            # Embed in tkinter
            canvas = FigureCanvasTkAgg(fig, master=self.charts_container)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
        except Exception as e:
            print(f"Error updating charts: {str(e)}")
    
    def set_budget(self):
        """Set monthly budget"""
        try:
            amount = self.budget_entry.get().strip()
            if not amount:
                messagebox.showwarning("Validation Error", "Please enter a budget amount")
                return
            
            success, message = self.wallet.set_budget(amount)
            if success:
                messagebox.showinfo("Success", "Budget set successfully!")
                self.update_budget_display()
            else:
                messagebox.showerror("Error", message)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to set budget: {str(e)}")
    
    def update_budget_display(self):
        """Update budget progress and alerts"""
        try:
            status = self.wallet.get_budget_status()
            
            if status:
                # Update status label
                self.budget_status_label.config(
                    text=f"Budget: ${status['budget']:.2f} | Spent: ${status['spent']:.2f} | Remaining: ${status['remaining']:.2f}"
                )
                
                # Update progress bar
                self.budget_progress['value'] = min(status['percentage'], 100)
                self.budget_percentage_label.config(text=f"{status['percentage']:.1f}%")
                
                # Update alerts
                self.alerts_text.delete('1.0', tk.END)
                
                if status['percentage'] >= 100:
                    self.alerts_text.insert('1.0', "⚠️ WARNING: You have exceeded your budget!\n\n", 'warning')
                elif status['percentage'] >= 75:
                    self.alerts_text.insert('1.0', "⚠️ NOTICE: You have used 75% of your budget\n\n", 'notice')
                else:
                    self.alerts_text.insert('1.0', "✅ Budget is on track\n\n", 'success')
                
                self.alerts_text.tag_config('warning', foreground='#f44336', font=("Arial", 11, "bold"))
                self.alerts_text.tag_config('notice', foreground='#ff9800', font=("Arial", 11, "bold"))
                self.alerts_text.tag_config('success', foreground='#4caf50', font=("Arial", 11, "bold"))
            else:
                self.budget_status_label.config(text="No budget set")
                self.budget_progress['value'] = 0
                self.budget_percentage_label.config(text="0%")
                self.alerts_text.delete('1.0', tk.END)
                self.alerts_text.insert('1.0', "Set a monthly budget to track your spending")
                
        except Exception as e:
            print(f"Error updating budget display: {str(e)}")
    
    def perform_search(self):
        """Perform search with filters"""
        try:
            search_type = self.search_type_var.get()
            search_category = self.search_category_var.get()
            
            # Convert search type
            type_filter = None if search_type == "All" else search_type
            category_filter = None if search_category == "All" else search_category
            
            # Perform search
            results = self.wallet.search_transactions(
                search_type=type_filter,
                category=category_filter
            )
            
            # Clear search results
            for item in self.search_tree.get_children():
                self.search_tree.delete(item)
            
            # Display results
            for trans in results:
                self.search_tree.insert("", "end", values=(
                    trans['id'],
                    trans['amount'],
                    trans['type'],
                    trans['category'],
                    trans['description'],
                    trans['date']
                ))
            
            messagebox.showinfo("Search Complete", f"Found {len(results)} transaction(s)")
        except Exception as e:
            messagebox.showerror("Error", f"Search failed: {str(e)}")
    
    def export_to_csv(self):
        """Export transactions to CSV file"""
        try:
            if not self.wallet.transactions:
                messagebox.showwarning("No Data", "No transactions to export")
                return
            
            # Ask for file location
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialfile=f"transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )
            
            if file_path:
                with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    
                    # Write header
                    writer.writerow(['ID', 'Amount', 'Type', 'Category', 'Description', 'Date'])
                    
                    # Write data
                    for trans in self.wallet.get_transactions():
                        writer.writerow([
                            trans['id'],
                            trans['amount'],
                            trans['type'],
                            trans['category'],
                            trans['description'],
                            trans['date']
                        ])
                
                messagebox.showinfo("Success", f"Transactions exported to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export: {str(e)}")
    
    def on_right_click(self, event):
        """Handle right-click on transaction"""
        item = self.tree.selection()
        if not item:
            return
        
        # Create context menu
        menu = tk.Menu(self.root, tearoff=False)
        menu.add_command(label="Delete", command=lambda: self.delete_transaction(item[0]))
        menu.post(event.x_global, event.y_global)
    
    def delete_transaction(self, item_id):
        """Delete selected transaction"""
        try:
            values = self.tree.item(item_id)['values']
            trans_id = values[0]
            
            if messagebox.askyesno("Confirm", "Are you sure you want to delete this transaction?"):
                success, message = self.wallet.delete_transaction(trans_id)
                if success:
                    messagebox.showinfo("Success", message)
                    self.refresh_all()
                else:
                    messagebox.showerror("Error", message)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete transaction: {str(e)}")


def main():
    """Main entry point"""
    root = tk.Tk()
    app = WalletGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()