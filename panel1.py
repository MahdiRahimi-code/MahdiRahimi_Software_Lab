import tkinter as tk
from tkinter import messagebox
from datetime import datetime

class TaskPanel(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Task Panel")
        self.geometry("460x420")
        self.minsize(420, 360)

        # ===== Top area: entry + Add button =====
        # ===== Top area: entry + Category + Add button =====
        top = tk.Frame(self, padx=8, pady=8)
        top.pack(fill="x")

        self.task_var = tk.StringVar()
        self.entry = tk.Entry(top, textvariable=self.task_var, font=("Segoe UI", 11))
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.entry.bind("<Return>", lambda _e: self.add_task())

        # Category selector (Menubutton)
        self.category_var = tk.StringVar(value="Category")  # default prompt
        cat_btn = tk.Menubutton(
            top,
            textvariable=self.category_var,
            relief="raised",
            padx=12, pady=6,
            bg="#e5e7eb", activebackground="#d1d5db"
        )
        cat_menu = tk.Menu(cat_btn, tearoff=0)
        for cat in ("Home", "Gym", "College"):
            cat_menu.add_radiobutton(label=cat, variable=self.category_var, value=cat)
        cat_btn.configure(menu=cat_menu)
        cat_btn.pack(side="left", padx=(0, 8))

        add_btn = tk.Button(
            top,
            text="Add Task",
            command=self.add_task,
            bg="#22c55e",        # green
            fg="white",
            activebackground="#16a34a",
            activeforeground="white",
            relief="raised",
            padx=12, pady=6
        )
        add_btn.pack(side="left")


        # ===== Middle area: listbox + scrollbar =====
        mid = tk.Frame(self, padx=8)
        mid.pack(fill="both", expand=True)

        self.list_var = tk.Variable(value=[])
        self.listbox = tk.Listbox(
            mid,
            listvariable=self.list_var,
            selectmode="extended",
            font=("Segoe UI", 11),
            activestyle="none"
        )
        self.listbox.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(mid, orient="vertical", command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox.config(yscrollcommand=scrollbar.set)

        # Keyboard shortcuts
        self.bind("<Delete>", lambda _e: self.delete_selected())

        # ===== Bottom area: action buttons =====
        # ===== Bottom area: action buttons =====
        bottom = tk.Frame(self, pady=10)
        bottom.pack(side="bottom", fill="x")

        # Inner frame to center the buttons
        btn_frame = tk.Frame(bottom)
        btn_frame.pack(anchor="center")

        del_btn = tk.Button(
            btn_frame,
            text="Delete task",
            command=self.delete_selected,
            bg="#ef4444",          # red
            fg="white",
            activebackground="#dc2626",
            activeforeground="white",
            padx=12, pady=6
        )
        del_btn.pack(side="left", padx=8)

        mark_btn = tk.Button(
            btn_frame,
            text="Mark one",
            command=self.mark_one,
            bg="#facc15",          # yellow
            fg="black",
            activebackground="#eab308",
            activeforeground="black",
            padx=12, pady=6
        )
        mark_btn.pack(side="left", padx=8)

        clear_btn = tk.Button(
            btn_frame,
            text="Clear all",
            command=self.clear_all,
            bg="#9ca3af",          # gray
            fg="white",
            activebackground="#6b7280",
            activeforeground="white",
            padx=12, pady=6
        )
        clear_btn.pack(side="left", padx=8)


        # Focus on the entry at start
        self.entry.focus_set()

    # --------- actions ----------
    def add_task(self):
        text = self.task_var.get().strip()
        cat = self.category_var.get().strip()

        if not text:
            messagebox.showinfo("Nothing to add", "Please type a task first.")
            return
        if cat == "Category":  # ensure user selected a category
            messagebox.showinfo("Pick a category", "Please select a category (Home, Gym, College).")
            return

        stamp = datetime.now().strftime("%Y-%m-%d %H:%M")  # e.g., 2025-10-12 14:37
        label = f"[{cat}] {text}  —  {stamp}"

        self.listbox.insert(tk.END, label)
        self.task_var.set("")
        idx = self.listbox.size() - 1
        self.listbox.itemconfig(idx, foreground="black")


    def delete_selected(self):
        sel = list(self.listbox.curselection())
        if not sel:
            messagebox.showinfo("No selection", "Select one or more tasks to delete.")
            return
        # Delete from bottom to top so indices don't shift
        for idx in reversed(sel):
            self.listbox.delete(idx)

    def clear_all(self):
        if self.listbox.size() == 0:
            return
        if messagebox.askyesno("Clear all", "Delete all tasks?"):
            self.listbox.delete(0, tk.END)

    def mark_one(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showinfo("No selection", "Select one task to mark.")
            return
        if len(sel) > 1:
            messagebox.showinfo("Multiple selected", "Please select only one task to mark/unmark.")
            return

        idx = sel[0]
        text = self.listbox.get(idx)

        # Toggle marked state by prefix and color
        if text.startswith("✓ "):
            # unmark
            new_text = text[2:]
            self.listbox.delete(idx)
            self.listbox.insert(idx, new_text)
            self.listbox.itemconfig(idx, foreground="black")
            self.listbox.selection_set(idx)
        else:
            # mark
            new_text = "✓ " + text
            self.listbox.delete(idx)
            self.listbox.insert(idx, new_text)
            self.listbox.itemconfig(idx, foreground="gray")
            self.listbox.selection_set(idx)

if __name__ == "__main__":
    app = TaskPanel()
    app.mainloop()
