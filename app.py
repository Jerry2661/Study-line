import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

DB_NAME = "studyline.db"


def init_db():
    """Create the homework table if it does not exist."""
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS homework (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course TEXT NOT NULL,
                title TEXT NOT NULL,
                due_date TEXT NOT NULL,
                priority TEXT NOT NULL,
                estimated_hours REAL NOT NULL,
                completed INTEGER NOT NULL DEFAULT 0
            )
        """)


class StudylineApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Studyline")
        self.root.geometry("850x520")

        self.course_var = tk.StringVar()
        self.title_var = tk.StringVar()
        self.due_date_var = tk.StringVar()
        self.priority_var = tk.StringVar(value="Medium")
        self.hours_var = tk.StringVar()

        self.build_ui()
        self.load_homework()

    def build_ui(self):
        form = ttk.LabelFrame(self.root, text="Add Homework", padding=12)
        form.pack(fill="x", padx=12, pady=10)

        ttk.Label(form, text="Course").grid(row=0, column=0, sticky="w")
        ttk.Entry(form, textvariable=self.course_var, width=22).grid(row=1, column=0, padx=(0, 10))

        ttk.Label(form, text="Assignment").grid(row=0, column=1, sticky="w")
        ttk.Entry(form, textvariable=self.title_var, width=25).grid(row=1, column=1, padx=(0, 10))

        ttk.Label(form, text="Due date (YYYY-MM-DD)").grid(row=0, column=2, sticky="w")
        ttk.Entry(form, textvariable=self.due_date_var, width=18).grid(row=1, column=2, padx=(0, 10))

        ttk.Label(form, text="Priority").grid(row=0, column=3, sticky="w")
        ttk.Combobox(
            form,
            textvariable=self.priority_var,
            values=["High", "Medium", "Low"],
            state="readonly",
            width=10,
        ).grid(row=1, column=3, padx=(0, 10))

        ttk.Label(form, text="Hours").grid(row=0, column=4, sticky="w")
        ttk.Entry(form, textvariable=self.hours_var, width=8).grid(row=1, column=4, padx=(0, 10))

        ttk.Button(form, text="Add", command=self.add_homework).grid(row=1, column=5)

        columns = ("course", "title", "due_date", "priority", "hours", "status")
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings", height=15)

        headings = {
            "course": "Course",
            "title": "Assignment",
            "due_date": "Due Date",
            "priority": "Priority",
            "hours": "Hours",
            "status": "Status",
        }

        widths = {
            "course": 120,
            "title": 220,
            "due_date": 110,
            "priority": 90,
            "hours": 70,
            "status": 90,
        }

        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="center")

        self.tree.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        buttons = ttk.Frame(self.root)
        buttons.pack(fill="x", padx=12, pady=(0, 12))

        ttk.Button(buttons, text="Mark Completed", command=self.mark_completed).pack(side="left")
        ttk.Button(buttons, text="Delete Selected", command=self.delete_selected).pack(side="left", padx=8)
        ttk.Button(buttons, text="Refresh", command=self.load_homework).pack(side="left")

    def add_homework(self):
        course = self.course_var.get().strip()
        title = self.title_var.get().strip()
        due_date = self.due_date_var.get().strip()
        priority = self.priority_var.get().strip()
        hours_text = self.hours_var.get().strip()

        if not course or not title or not due_date or not hours_text:
            messagebox.showerror("Missing information", "Please complete all fields.")
            return

        try:
            datetime.strptime(due_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Invalid date", "Use YYYY-MM-DD format.")
            return

        try:
            hours = float(hours_text)
            if hours <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid hours", "Estimated hours must be a positive number.")
            return

        with sqlite3.connect(DB_NAME) as conn:
            conn.execute(
                """
                INSERT INTO homework
                (course, title, due_date, priority, estimated_hours)
                VALUES (?, ?, ?, ?, ?)
                """,
                (course, title, due_date, priority, hours),
            )

        self.course_var.set("")
        self.title_var.set("")
        self.due_date_var.set("")
        self.priority_var.set("Medium")
        self.hours_var.set("")
        self.load_homework()

    def load_homework(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        with sqlite3.connect(DB_NAME) as conn:
            rows = conn.execute(
                """
                SELECT id, course, title, due_date, priority,
                       estimated_hours, completed
                FROM homework
                ORDER BY completed ASC,
                         due_date ASC,
                         CASE priority
                             WHEN 'High' THEN 1
                             WHEN 'Medium' THEN 2
                             ELSE 3
                         END
                """
            ).fetchall()

        for row in rows:
            homework_id, course, title, due_date, priority, hours, completed = row
            status = "Completed" if completed else "Pending"
            self.tree.insert(
                "",
                "end",
                iid=str(homework_id),
                values=(course, title, due_date, priority, hours, status),
            )

    def mark_completed(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("No selection", "Select a homework item first.")
            return

        homework_id = selected[0]
        with sqlite3.connect(DB_NAME) as conn:
            conn.execute(
                "UPDATE homework SET completed = 1 WHERE id = ?",
                (homework_id,),
            )

        self.load_homework()

    def delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("No selection", "Select a homework item first.")
            return

        homework_id = selected[0]
        with sqlite3.connect(DB_NAME) as conn:
            conn.execute("DELETE FROM homework WHERE id = ?", (homework_id,))

        self.load_homework()


if __name__ == "__main__":
    init_db()
    root = tk.Tk()
    app = StudylineApp(root)
    root.mainloop()
