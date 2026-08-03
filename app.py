import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

DB_NAME = "studyline.db"


def init_db():
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
        self.root.geometry("950x560")
        self.course_var = tk.StringVar()
        self.title_var = tk.StringVar()
        self.due_date_var = tk.StringVar()
        self.priority_var = tk.StringVar(value="Medium")
        self.hours_var = tk.StringVar()
        self.build_ui()
        self.load_homework()

    def build_ui(self):
        ttk.Label(self.root, text="Studyline - Homework Planner", font=("Arial", 18, "bold")).pack(pady=(12, 4))
        form = ttk.LabelFrame(self.root, text="Homework Information", padding=12)
        form.pack(fill="x", padx=12, pady=8)

        labels = ["Course", "Assignment", "Due Date (YYYY-MM-DD)", "Priority", "Estimated Hours"]
        for i, label in enumerate(labels):
            ttk.Label(form, text=label).grid(row=0, column=i, sticky="w")

        ttk.Entry(form, textvariable=self.course_var, width=18).grid(row=1, column=0, padx=(0,10))
        ttk.Entry(form, textvariable=self.title_var, width=24).grid(row=1, column=1, padx=(0,10))
        ttk.Entry(form, textvariable=self.due_date_var, width=18).grid(row=1, column=2, padx=(0,10))
        ttk.Combobox(form, textvariable=self.priority_var, values=["High","Medium","Low"], state="readonly", width=10).grid(row=1, column=3, padx=(0,10))
        ttk.Entry(form, textvariable=self.hours_var, width=12).grid(row=1, column=4, padx=(0,10))
        ttk.Button(form, text="Add Homework", command=self.add_homework).grid(row=1, column=5)

        columns = ("course", "title", "due_date", "priority", "hours", "status")
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings", height=15)
        headings = {"course":"Course","title":"Assignment","due_date":"Due Date","priority":"Priority","hours":"Hours","status":"Status"}
        widths = {"course":130,"title":230,"due_date":110,"priority":90,"hours":80,"status":100}
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="center")
        self.tree.pack(fill="both", expand=True, padx=12, pady=(0,8))

        buttons = ttk.Frame(self.root)
        buttons.pack(fill="x", padx=12, pady=(0,12))
        ttk.Button(buttons, text="Edit Selected", command=self.edit_selected).pack(side="left")
        ttk.Button(buttons, text="Mark Completed", command=self.mark_completed).pack(side="left", padx=8)
        ttk.Button(buttons, text="Delete Selected", command=self.delete_selected).pack(side="left")
        ttk.Button(buttons, text="Generate Plan", command=self.generate_plan).pack(side="left", padx=8)
        ttk.Button(buttons, text="Refresh", command=self.load_homework).pack(side="left")

    def validate_input(self):
        course = self.course_var.get().strip()
        title = self.title_var.get().strip()
        due_date = self.due_date_var.get().strip()
        priority = self.priority_var.get().strip()
        hours_text = self.hours_var.get().strip()
        if not course or not title or not due_date or not hours_text:
            messagebox.showerror("Missing Information", "Please complete all fields.")
            return None
        try:
            datetime.strptime(due_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Invalid Date", "Please use YYYY-MM-DD format.")
            return None
        try:
            hours = float(hours_text)
            if hours <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Hours", "Estimated hours must be a positive number.")
            return None
        return course, title, due_date, priority, hours

    def clear_form(self):
        self.course_var.set("")
        self.title_var.set("")
        self.due_date_var.set("")
        self.priority_var.set("Medium")
        self.hours_var.set("")

    def add_homework(self):
        data = self.validate_input()
        if data is None:
            return
        with sqlite3.connect(DB_NAME) as conn:
            conn.execute("INSERT INTO homework (course, title, due_date, priority, estimated_hours) VALUES (?, ?, ?, ?, ?)", data)
        self.clear_form()
        self.load_homework()

    def load_homework(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        with sqlite3.connect(DB_NAME) as conn:
            rows = conn.execute("""
                SELECT id, course, title, due_date, priority, estimated_hours, completed
                FROM homework
                ORDER BY completed ASC, due_date ASC,
                CASE priority WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END
            """).fetchall()
        for row in rows:
            homework_id, course, title, due_date, priority, hours, completed = row
            status = "Completed" if completed else "Pending"
            self.tree.insert("", "end", iid=str(homework_id), values=(course, title, due_date, priority, hours, status))

    def get_selected_id(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("No Selection", "Please select a homework item first.")
            return None
        return selected[0]

    def edit_selected(self):
        homework_id = self.get_selected_id()
        if homework_id is None:
            return
        with sqlite3.connect(DB_NAME) as conn:
            row = conn.execute("SELECT course, title, due_date, priority, estimated_hours FROM homework WHERE id = ?", (homework_id,)).fetchone()
        if row is None:
            return

        edit = tk.Toplevel(self.root)
        edit.title("Edit Homework")
        edit.geometry("420x300")
        edit.resizable(False, False)
        course_var = tk.StringVar(value=row[0])
        title_var = tk.StringVar(value=row[1])
        due_var = tk.StringVar(value=row[2])
        priority_var = tk.StringVar(value=row[3])
        hours_var = tk.StringVar(value=str(row[4]))

        fields = [("Course", course_var), ("Assignment", title_var), ("Due Date (YYYY-MM-DD)", due_var), ("Estimated Hours", hours_var)]
        for i, (label, var) in enumerate(fields):
            ttk.Label(edit, text=label).grid(row=i, column=0, padx=15, pady=10, sticky="w")
            ttk.Entry(edit, textvariable=var, width=28).grid(row=i, column=1, padx=15, pady=10)
        ttk.Label(edit, text="Priority").grid(row=4, column=0, padx=15, pady=10, sticky="w")
        ttk.Combobox(edit, textvariable=priority_var, values=["High","Medium","Low"], state="readonly", width=25).grid(row=4, column=1, padx=15, pady=10)

        def save_changes():
            course, title, due_date, priority, hours_text = course_var.get().strip(), title_var.get().strip(), due_var.get().strip(), priority_var.get().strip(), hours_var.get().strip()
            if not course or not title or not due_date or not hours_text:
                messagebox.showerror("Missing Information", "Please complete all fields.")
                return
            try:
                datetime.strptime(due_date, "%Y-%m-%d")
                hours = float(hours_text)
                if hours <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Invalid Input", "Check the date format and estimated hours.")
                return
            with sqlite3.connect(DB_NAME) as conn:
                conn.execute("UPDATE homework SET course=?, title=?, due_date=?, priority=?, estimated_hours=? WHERE id=?", (course, title, due_date, priority, hours, homework_id))
            edit.destroy()
            self.load_homework()

        ttk.Button(edit, text="Save Changes", command=save_changes).grid(row=5, column=0, columnspan=2, pady=15)

    def mark_completed(self):
        homework_id = self.get_selected_id()
        if homework_id is None:
            return
        with sqlite3.connect(DB_NAME) as conn:
            conn.execute("UPDATE homework SET completed = 1 WHERE id = ?", (homework_id,))
        self.load_homework()

    def delete_selected(self):
        homework_id = self.get_selected_id()
        if homework_id is None:
            return
        if messagebox.askyesno("Delete Homework", "Are you sure you want to delete this homework?"):
            with sqlite3.connect(DB_NAME) as conn:
                conn.execute("DELETE FROM homework WHERE id = ?", (homework_id,))
            self.load_homework()

    def generate_plan(self):
        with sqlite3.connect(DB_NAME) as conn:
            rows = conn.execute("""
                SELECT course, title, due_date, priority, estimated_hours
                FROM homework
                WHERE completed = 0
                ORDER BY due_date ASC,
                CASE priority WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END,
                estimated_hours ASC
            """).fetchall()
        if not rows:
            messagebox.showinfo("Study Plan", "There are no pending homework assignments.")
            return

        plan = tk.Toplevel(self.root)
        plan.title("Recommended Homework Plan")
        plan.geometry("650x400")
        ttk.Label(plan, text="Recommended Homework Order", font=("Arial", 16, "bold")).pack(pady=12)
        text = tk.Text(plan, wrap="word", width=75, height=18)
        text.pack(padx=15, pady=10, fill="both", expand=True)
        today = datetime.now().date()
        for index, row in enumerate(rows, start=1):
            course, title, due_date, priority, hours = row
            due = datetime.strptime(due_date, "%Y-%m-%d").date()
            days_left = (due - today).days
            if days_left < 0:
                deadline_text = "OVERDUE"
            elif days_left == 0:
                deadline_text = "Due today"
            elif days_left == 1:
                deadline_text = "Due tomorrow"
            else:
                deadline_text = f"{days_left} days left"
            text.insert("end", f"{index}. {course} - {title}\n   Due: {due_date} ({deadline_text})\n   Priority: {priority} | Estimated time: {hours} hours\n\n")
        text.config(state="disabled")


if __name__ == "__main__":
    init_db()
    root = tk.Tk()
    StudylineApp(root)
    root.mainloop()
