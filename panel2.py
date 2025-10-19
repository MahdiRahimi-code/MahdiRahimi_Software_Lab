import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from datetime import datetime
import json, os

CATEGORIES = ["Home", "Gym", "College"]
DATA_FILE = "tasks.json"
PRIORITY_SYMBOLS = {
    "Low": "◻",
    "Medium": "●",
    "High": "◯",
    "Urgent": "🔴",
}


class TaskPanel(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Task Panel")
        self.geometry("700x660")
        self.minsize(640, 620)
        self.configure(bg="#f3f4f6")

        # Structured storage
        self.tasks_data = {c: [] for c in CATEGORIES}

        # Master list for Treeview rows
        # item = {"id": int, "cat": str, "priority": str, "task": str, "time": str, "done": bool}
        self.items = []
        self._next_id = 1

        # Tree row metadata map: iid -> json string of task
        self.metas = {}

        # ===== Header + Search + Filters + Treeview =====
        self.setup_ui()

        # ===== Entry row for creating tasks =====
        top = tk.Frame(self, padx=8, pady=8, bg="#f3f4f6")
        top.pack(fill="x")

        self.task_var = tk.StringVar()
        self.entry = tk.Entry(top, textvariable=self.task_var, font=("Segoe UI", 11))
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.entry.bind("<Return>", lambda _e: self.add_task())

        self.category_var = tk.StringVar(value="Category")
        cat_btn = tk.Menubutton(
            top, textvariable=self.category_var, relief="raised",
            padx=12, pady=6, bg="#e5e7eb", activebackground="#d1d5db"
        )
        cat_menu = tk.Menu(cat_btn, tearoff=0)
        for cat in CATEGORIES:
            cat_menu.add_radiobutton(label=cat, variable=self.category_var, value=cat)
        cat_btn.configure(menu=cat_menu)
        cat_btn.pack(side="left", padx=(0, 8))

        add_btn = tk.Button(
            top, text="Add Task", command=self.add_task,
            bg="#22c55e", fg="white", activebackground="#16a34a",
            activeforeground="white", relief="raised", padx=12, pady=6
        )
        add_btn.pack(side="left")

        # ===== Bottom actions =====
        bottom = tk.Frame(self, pady=10, bg="#f3f4f6")
        bottom.pack(side="bottom", fill="x")

        # Status bar (live stats)
        self.stats_label = tk.Label(bottom, text="📊 Tasks: 0 Completed | 0 Pending | 0 Total",
                                    bg="#f3f4f6", fg="#111827", anchor="w")
        self.stats_label.pack(fill="x", padx=8, pady=(0, 8))

        btn_frame = tk.Frame(bottom, bg="#f3f4f6")
        btn_frame.pack(anchor="center")

        tk.Button(
            btn_frame, text="Delete task", command=self.delete_selected,
            bg="#ef4444", fg="white", activebackground="#dc2626",
            activeforeground="white", padx=12, pady=6
        ).pack(side="left", padx=8)

        tk.Button(
            btn_frame, text="Mark one", command=self.mark_one,
            bg="#facc15", fg="black", activebackground="#eab308",
            activeforeground="black", padx=12, pady=6
        ).pack(side="left", padx=8)

        tk.Button(
            btn_frame, text="Clear all", command=self.clear_all,
            bg="#9ca3af", fg="white", activebackground="#6b7280",
            activeforeground="white", padx=12, pady=6
        ).pack(side="left", padx=8)

        tk.Button(
            btn_frame, text="Show stats", command=self.show_stats,
            bg="#3b82f6", fg="white", activebackground="#2563eb",
            activeforeground="white", padx=12, pady=6
        ).pack(side="left", padx=8)

        tk.Button(
            btn_frame, text="Save now", command=self.save_tasks,
            bg="#10b981", fg="white", activebackground="#059669",
            activeforeground="white", padx=12, pady=6
        ).pack(side="left", padx=8)

        # Keyboard shortcuts
        self.bind("<Delete>", lambda _e: self.delete_selected())
        self.entry.focus_set()

        # Load persisted tasks (if any)
        self.load_tasks()

    # ================= UI (Phase 2–5) =================
    def setup_ui(self):
        # Header
        header_frame = tk.Frame(self, bg='#2c3e50', height=100)
        header_frame.pack(fill='x', padx=15, pady=(15, 5))
        header_frame.pack_propagate(False)
        tk.Label(
            header_frame, text="🚀 Advanced Task Manager",
            font=('Arial', 18, 'bold'), bg='#2c3e50', fg='white'
        ).pack(pady=20)

        # Search / Filters
        search_frame = tk.Frame(self, bg='#f8f9fa')
        search_frame.pack(fill='x', padx=20, pady=(5, 6))

        tk.Label(search_frame, text="🔍 Search:", font=('Arial', 10, 'bold'), bg='#f8f9fa')\
            .grid(row=0, column=0, sticky='w')

        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(
            search_frame, textvariable=self.search_var,
            font=('Arial', 10), width=22, bd=1, relief='solid'
        )
        self.search_entry.grid(row=0, column=1, padx=5)
        self.search_entry.bind('<KeyRelease>', self.filter_tasks)

        tk.Label(search_frame, text="Status:", font=('Arial', 10, 'bold'), bg='#f8f9fa')\
            .grid(row=0, column=2, padx=(16, 5), sticky='e')
        self.filter_var = tk.StringVar(value="All")
        status_combo = ttk.Combobox(
            search_frame, textvariable=self.filter_var,
            values=["All", "Pending", "Completed"], state="readonly", width=12
        )
        status_combo.grid(row=0, column=3, padx=5, sticky='w')
        status_combo.bind('<<ComboboxSelected>>', self.filter_tasks)

        tk.Label(search_frame, text="Category:", font=('Arial', 10, 'bold'), bg='#f8f9fa')\
            .grid(row=0, column=4, padx=(16, 5), sticky='e')
        self.category_filter_var = tk.StringVar(value="All")
        category_combo = ttk.Combobox(
            search_frame, textvariable=self.category_filter_var,
            values=["All"] + CATEGORIES, state="readonly", width=12
        )
        category_combo.grid(row=0, column=5, padx=5, sticky='w')
        category_combo.bind('<<ComboboxSelected>>', self.filter_tasks)

        search_frame.grid_columnconfigure(6, weight=1)

        # Priority picker (for adding tasks)
        options_frame = tk.Frame(self, bg='#f8f9fa')
        options_frame.pack(fill='x', padx=20, pady=(0, 10))

        tk.Label(options_frame, text="Priority:", font=('Arial', 10), bg='#f8f9fa')\
            .pack(side='left', padx=(0, 10))

        self.priority_var = tk.StringVar(value="Medium")
        priorities = ["Low", "Medium", "High", "Urgent"]
        ttk.Combobox(
            options_frame, textvariable=self.priority_var,
            values=priorities, state="readonly", width=10
        ).pack(side='left')

        # Treeview
        list_frame = tk.Frame(self, bg='#f8f9fa')
        list_frame.pack(fill='both', expand=True, padx=20, pady=10)

        self.tree = ttk.Treeview(
            list_frame,
            columns=('Status', 'Priority', 'Category', 'Task', 'Time'),
            show='headings', height=15
        )
        self.tree.heading('Status', text='📊 Status')
        self.tree.heading('Priority', text='🎯 Priority')
        self.tree.heading('Category', text='📁 Category')
        self.tree.heading('Task', text='📝 Task')
        self.tree.heading('Time', text='⏰ Created')

        self.tree.column('Status', width=90, anchor='center')
        self.tree.column('Priority', width=90, anchor='center')
        self.tree.column('Category', width=100, anchor='center')
        self.tree.column('Task', width=360, anchor='w')
        self.tree.column('Time', width=140, anchor='center')

        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        style = ttk.Style(self)
        style.configure("Treeview.Heading", font=('Arial', 10, 'bold'))
        self.tree.tag_configure("done", foreground="#6b7280")
        self.tree.tag_configure("active", foreground="#111827")

    # ==================== Helpers & filtering ====================
    def _status_emoji(self, done: bool) -> str:
        return "✅" if done else "⏳"

    def _priority_emoji(self, pr: str) -> str:
        return PRIORITY_SYMBOLS.get(pr, "●")  # پیش‌فرض: ●

    def display_task(self, task: dict):
        """درخت را با ایموجی‌های وضعیت/اولویت به‌روزرسانی می‌کند و متادیتا ذخیره می‌شود."""
        status = "✅" if task.get("done") else "⏳"
        # استفاده از شکل‌های جدید
        priority = PRIORITY_SYMBOLS.get(task.get('priority', 'Medium'), "●")
        values = (
            status,
            priority,
            task.get('category', 'General'),
            task['text'],
            task['created']
        )
        iid = self.tree.insert('', 'end', values=values,
                            tags=("done",) if task.get("done") else ("active",))
        self.metas[str(iid)] = json.dumps(task)


    def _passes_filters(self, item):
        q = self.search_var.get().strip().lower()
        cat_filter = self.category_filter_var.get()
        status_filter = self.filter_var.get()

        if cat_filter != "All" and item["cat"] != cat_filter:
            return False

        status_label = "Completed" if item["done"] else "Pending"
        if status_filter != "All" and status_filter != status_label:
            return False

        if q:
            hay = f'{item["task"]} {item["cat"]} {item["priority"]} {item["time"]}'.lower()
            if q not in hay:
                return False
        return True

    def filter_tasks(self, event=None):
        self._rebuild_tree()  # rebuild also updates live stats

    def _rebuild_tree(self):
        # Clear rows & metas
        self.tree.delete(*self.tree.get_children())
        self.metas.clear()

        # Reinsert rows that pass filters
        for it in self.items:
            if not self._passes_filters(it):
                continue
            status_ico = self._status_emoji(it["done"])
            priority_ico = self._priority_emoji(it["priority"])
            tags = ("done",) if it["done"] else ("active",)
            iid = str(it["id"])
            self.tree.insert(
                "", tk.END, iid=iid,
                values=(status_ico, priority_ico, it["cat"], it["task"], it["time"]),
                tags=tags
            )
            # Keep JSON snapshot for stats/save
            self.metas[iid] = json.dumps({
                "id": it["id"],
                "category": it["cat"],
                "priority": it["priority"],
                "text": it["task"],
                "created": it["time"],
                "done": it["done"]
            })

        # Live stats after every UI rebuild
        self.update_stats()

    # ============== Phase 6: Statistics & Persistence ==============
    def show_stats(self):
        """Display comprehensive statistics in a dialog."""
        total = len(self.metas)
        completed = sum(1 for meta in self.metas.values() if json.loads(meta).get('done', False))
        pending = total - completed

        # Category counts
        category_stats = {}
        for meta in self.metas.values():
            data = json.loads(meta)
            cat = data.get('category', 'General')
            category_stats[cat] = category_stats.get(cat, 0) + 1

        stats_text = "📊 Statistics:\n"
        stats_text += f"✅ Completed: {completed}\n"
        stats_text += f"⏳ Pending: {pending}\n"
        stats_text += f"📈 Total: {total}\n"
        if category_stats:
            cats_line = ', '.join([f'{k}({v})' for k, v in category_stats.items()])
        else:
            cats_line = "None"
        stats_text += f"📁 Categories: {cats_line}"
        messagebox.showinfo("Detailed Statistics", stats_text)

    def save_tasks(self):
        """Save tasks to JSON file (error-safe)."""
        try:
            tasks = []
            for item_id in self.tree.get_children():
                if item_id in self.metas:
                    tasks.append(json.loads(self.metas[item_id]))
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(tasks, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save tasks: {e}")

    def load_tasks(self):
        """Load tasks from JSON file at startup, if present."""
        if not os.path.exists(DATA_FILE):
            self._rebuild_tree()
            return
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                tasks = json.load(f)
            # Rebuild internal structures
            self.items.clear()
            self._next_id = 1
            for t in tasks:
                item = {
                    "id": self._next_id,
                    "cat": t.get("category", "General"),
                    "priority": t.get("priority", "Medium"),
                    "task": t.get("text", ""),
                    "time": t.get("created", datetime.now().strftime("%Y-%m-%d %H:%M")),
                    "done": bool(t.get("done", False)),
                }
                self.items.append(item)
                # structured store (optional but kept consistent)
                cat = item["cat"]
                if cat not in self.tasks_data:
                    self.tasks_data[cat] = []
                self.tasks_data[cat].append({
                    "task": item["task"],
                    "timestamp": item["time"],
                    "done": item["done"],
                    "priority": item["priority"],
                })
                self._next_id += 1
            self._rebuild_tree()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load tasks: {e}")
            self._rebuild_tree()

    def update_stats(self):
        """Update status-bar with live totals."""
        total = len(self.metas)
        completed = sum(1 for meta in self.metas.values() if json.loads(meta).get('done', False))
        pending = total - completed
        self.stats_label.config(text=f"📊 Tasks: {completed} Completed | {pending} Pending | {total} Total")

    # ==================== Actions (auto-save) ====================
    def add_task(self):
        text = self.task_var.get().strip()
        cat = self.category_var.get().strip()
        pr = self.priority_var.get().strip() or "Medium"

        if not text:
            messagebox.showinfo("Nothing to add", "Please type a task first.")
            return
        if cat == "Category":
            messagebox.showinfo("Pick a category", "Please select a category.")
            return

        stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        item = {"id": self._next_id, "cat": cat, "priority": pr, "task": text, "time": stamp, "done": False}
        self._next_id += 1

        self.tasks_data.setdefault(cat, []).append({"task": text, "timestamp": stamp, "done": False, "priority": pr})
        self.items.append(item)

        self.task_var.set("")
        self._rebuild_tree()
        self.save_tasks()

    def delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("No selection", "Select one or more tasks to delete.")
            return

        ids_to_remove = set(int(i) for i in sel)
        removed = [it for it in self.items if it["id"] in ids_to_remove]
        self.items = [it for it in self.items if it["id"] not in ids_to_remove]

        for it in removed:
            self.tasks_data[it["cat"]] = [d for d in self.tasks_data[it["cat"]] if d["task"] != it["task"]]

        self._rebuild_tree()
        self.save_tasks()

    def clear_all(self):
        if not self.items:
            return
        if messagebox.askyesno("Clear all", "Delete all tasks?"):
            self.items.clear()
            for cat in self.tasks_data:
                self.tasks_data[cat].clear()
            self._rebuild_tree()
            self.save_tasks()

    def mark_one(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("No selection", "Select one task to mark.")
            return
        if len(sel) > 1:
            messagebox.showinfo("Multiple selected", "Please select only one task to mark/unmark.")
            return

        iid = int(sel[0])
        for it in self.items:
            if it["id"] == iid:
                it["done"] = not it["done"]
                # also flip in structured storage
                for d in self.tasks_data.setdefault(it["cat"], []):
                    if d["task"] == it["task"]:
                        d["done"] = it["done"]
                        break
                break
        self._rebuild_tree()
        self.save_tasks()

if __name__ == "__main__":
    app = TaskPanel()
    app.mainloop()
