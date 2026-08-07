import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date, timedelta

DB = "studyline.db"

def init_db():
    with sqlite3.connect(DB) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS homework(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course TEXT NOT NULL,
            title TEXT NOT NULL,
            due_date TEXT NOT NULL,
            priority TEXT NOT NULL,
            hours REAL NOT NULL,
            completed INTEGER DEFAULT 0)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS exams(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course TEXT NOT NULL,
            name TEXT NOT NULL,
            exam_date TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            review_hours REAL NOT NULL)""")

class App:
    def __init__(self, root):
        self.root = root
        root.title("Studyline")
        root.geometry("1000x650")

        self.tabs = ttk.Notebook(root)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=10)

        self.dashboard = ttk.Frame(self.tabs)
        self.homework = ttk.Frame(self.tabs)
        self.exams = ttk.Frame(self.tabs)
        self.plan = ttk.Frame(self.tabs)

        self.tabs.add(self.dashboard, text="Dashboard")
        self.tabs.add(self.homework, text="Homework")
        self.tabs.add(self.exams, text="Exams")
        self.tabs.add(self.plan, text="Study Plan")

        self.build_dashboard()
        self.build_homework()
        self.build_exams()
        self.build_plan()
        self.refresh_all()
        root.after(500, self.reminders)

    def valid_date(self, s):
        try:
            datetime.strptime(s, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    # Dashboard
    def build_dashboard(self):
        ttk.Label(self.dashboard, text="Studyline Dashboard",
                  font=("Arial", 20, "bold")).pack(pady=15)
        self.summary = ttk.Label(self.dashboard, text="")
        self.summary.pack(pady=5)
        self.dash_text = tk.Text(self.dashboard, wrap="word")
        self.dash_text.pack(fill="both", expand=True, padx=20, pady=15)

    def refresh_dashboard(self):
        today = date.today()
        with sqlite3.connect(DB) as conn:
            hw = conn.execute("""SELECT course,title,due_date,priority
                                 FROM homework WHERE completed=0
                                 ORDER BY due_date""").fetchall()
            ex = conn.execute("""SELECT course,name,exam_date,difficulty
                                 FROM exams ORDER BY exam_date""").fetchall()

        upcoming_exams = [x for x in ex if datetime.strptime(x[2], "%Y-%m-%d").date() >= today]
        self.summary.config(text=f"Pending Homework: {len(hw)}     Upcoming Exams: {len(upcoming_exams)}")

        self.dash_text.delete("1.0", "end")
        self.dash_text.insert("end", "UPCOMING HOMEWORK\n\n")
        shown = False
        for c,t,d,p in hw:
            days = (datetime.strptime(d,"%Y-%m-%d").date()-today).days
            if days <= 7:
                shown = True
                label = "OVERDUE" if days < 0 else ("Due today" if days == 0 else f"{days} days left")
                self.dash_text.insert("end", f"- {c}: {t} | {d} | {p} | {label}\n")
        if not shown:
            self.dash_text.insert("end", "No homework due within 7 days.\n")

        self.dash_text.insert("end", "\nUPCOMING EXAMS\n\n")
        shown = False
        for c,n,d,diff in upcoming_exams:
            days = (datetime.strptime(d,"%Y-%m-%d").date()-today).days
            if days <= 14:
                shown = True
                self.dash_text.insert("end", f"- {c}: {n} | {d} | {diff} | {days} days left\n")
        if not shown:
            self.dash_text.insert("end", "No exams within 14 days.\n")

    # Homework
    def build_homework(self):
        self.hw_course = tk.StringVar()
        self.hw_title = tk.StringVar()
        self.hw_due = tk.StringVar()
        self.hw_priority = tk.StringVar(value="Medium")
        self.hw_hours = tk.StringVar()

        form = ttk.LabelFrame(self.homework, text="Add Homework", padding=10)
        form.pack(fill="x", padx=10, pady=10)

        names = ["Course","Assignment","Due Date","Priority","Hours"]
        for i,n in enumerate(names):
            ttk.Label(form,text=n).grid(row=0,column=i,sticky="w")

        ttk.Entry(form,textvariable=self.hw_course,width=16).grid(row=1,column=0,padx=4)
        ttk.Entry(form,textvariable=self.hw_title,width=22).grid(row=1,column=1,padx=4)
        ttk.Entry(form,textvariable=self.hw_due,width=16).grid(row=1,column=2,padx=4)
        ttk.Combobox(form,textvariable=self.hw_priority,
                     values=["High","Medium","Low"],state="readonly",width=10).grid(row=1,column=3,padx=4)
        ttk.Entry(form,textvariable=self.hw_hours,width=8).grid(row=1,column=4,padx=4)
        ttk.Button(form,text="Add",command=self.add_hw).grid(row=1,column=5,padx=4)

        cols = ("course","title","due","priority","hours","status")
        self.hw_tree = ttk.Treeview(self.homework,columns=cols,show="headings",height=18)
        for col,name in zip(cols,["Course","Assignment","Due Date","Priority","Hours","Status"]):
            self.hw_tree.heading(col,text=name)
            self.hw_tree.column(col,anchor="center",width=130 if col!="title" else 220)
        self.hw_tree.pack(fill="both",expand=True,padx=10)

        bar = ttk.Frame(self.homework)
        bar.pack(fill="x",padx=10,pady=10)
        ttk.Button(bar,text="Edit",command=self.edit_hw).pack(side="left")
        ttk.Button(bar,text="Mark Completed",command=self.complete_hw).pack(side="left",padx=8)
        ttk.Button(bar,text="Delete",command=self.delete_hw).pack(side="left")

    def add_hw(self):
        vals = [self.hw_course.get().strip(), self.hw_title.get().strip(),
                self.hw_due.get().strip(), self.hw_priority.get().strip(),
                self.hw_hours.get().strip()]
        if not all(vals):
            messagebox.showerror("Error","Complete all fields.")
            return
        if not self.valid_date(vals[2]):
            messagebox.showerror("Error","Date format must be YYYY-MM-DD.")
            return
        try:
            hours = float(vals[4])
            if hours <= 0: raise ValueError
        except ValueError:
            messagebox.showerror("Error","Hours must be positive.")
            return
        with sqlite3.connect(DB) as conn:
            conn.execute("""INSERT INTO homework(course,title,due_date,priority,hours)
                            VALUES(?,?,?,?,?)""",(vals[0],vals[1],vals[2],vals[3],hours))
        for v in [self.hw_course,self.hw_title,self.hw_due,self.hw_hours]: v.set("")
        self.hw_priority.set("Medium")
        self.refresh_all()

    def load_hw(self):
        for x in self.hw_tree.get_children(): self.hw_tree.delete(x)
        with sqlite3.connect(DB) as conn:
            rows = conn.execute("""SELECT id,course,title,due_date,priority,hours,completed
                                   FROM homework
                                   ORDER BY completed,due_date,
                                   CASE priority WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END""").fetchall()
        for r in rows:
            self.hw_tree.insert("", "end", iid=str(r[0]),
                                values=(r[1],r[2],r[3],r[4],r[5],"Completed" if r[6] else "Pending"))

    def selected_hw(self):
        s=self.hw_tree.selection()
        if not s:
            messagebox.showinfo("Select","Select homework first.")
            return None
        return s[0]

    def edit_hw(self):
        i=self.selected_hw()
        if i is None:return
        with sqlite3.connect(DB) as conn:
            r=conn.execute("SELECT course,title,due_date,priority,hours FROM homework WHERE id=?",(i,)).fetchone()
        w=tk.Toplevel(self.root); w.title("Edit Homework")
        vars=[tk.StringVar(value=x) for x in r]
        labels=["Course","Assignment","Due Date","Priority","Hours"]
        for n,l in enumerate(labels):
            ttk.Label(w,text=l).grid(row=n,column=0,padx=10,pady=8,sticky="w")
            if n==3:
                ttk.Combobox(w,textvariable=vars[n],values=["High","Medium","Low"],state="readonly").grid(row=n,column=1,padx=10,pady=8)
            else:
                ttk.Entry(w,textvariable=vars[n]).grid(row=n,column=1,padx=10,pady=8)
        def save():
            if not all(v.get().strip() for v in vars) or not self.valid_date(vars[2].get().strip()):
                messagebox.showerror("Error","Check all fields and date format."); return
            try:
                h=float(vars[4].get())
                if h<=0:raise ValueError
            except ValueError:
                messagebox.showerror("Error","Hours must be positive."); return
            with sqlite3.connect(DB) as conn:
                conn.execute("""UPDATE homework SET course=?,title=?,due_date=?,priority=?,hours=? WHERE id=?""",
                             (vars[0].get().strip(),vars[1].get().strip(),vars[2].get().strip(),vars[3].get(),h,i))
            w.destroy(); self.refresh_all()
        ttk.Button(w,text="Save",command=save).grid(row=5,column=0,columnspan=2,pady=12)

    def complete_hw(self):
        i=self.selected_hw()
        if i is None:return
        with sqlite3.connect(DB) as conn:
            conn.execute("UPDATE homework SET completed=1 WHERE id=?",(i,))
        self.refresh_all()

    def delete_hw(self):
        i=self.selected_hw()
        if i is None:return
        with sqlite3.connect(DB) as conn:
            conn.execute("DELETE FROM homework WHERE id=?",(i,))
        self.refresh_all()

    # Exams
    def build_exams(self):
        self.ex_course=tk.StringVar()
        self.ex_name=tk.StringVar()
        self.ex_date=tk.StringVar()
        self.ex_diff=tk.StringVar(value="Medium")
        self.ex_hours=tk.StringVar()

        form=ttk.LabelFrame(self.exams,text="Add Exam",padding=10)
        form.pack(fill="x",padx=10,pady=10)
        for i,n in enumerate(["Course","Exam","Exam Date","Difficulty","Review Hours"]):
            ttk.Label(form,text=n).grid(row=0,column=i,sticky="w")
        ttk.Entry(form,textvariable=self.ex_course,width=16).grid(row=1,column=0,padx=4)
        ttk.Entry(form,textvariable=self.ex_name,width=22).grid(row=1,column=1,padx=4)
        ttk.Entry(form,textvariable=self.ex_date,width=16).grid(row=1,column=2,padx=4)
        ttk.Combobox(form,textvariable=self.ex_diff,values=["High","Medium","Low"],state="readonly",width=10).grid(row=1,column=3,padx=4)
        ttk.Entry(form,textvariable=self.ex_hours,width=10).grid(row=1,column=4,padx=4)
        ttk.Button(form,text="Add",command=self.add_exam).grid(row=1,column=5,padx=4)

        cols=("course","name","date","difficulty","hours")
        self.ex_tree=ttk.Treeview(self.exams,columns=cols,show="headings",height=18)
        for c,n in zip(cols,["Course","Exam","Exam Date","Difficulty","Review Hours"]):
            self.ex_tree.heading(c,text=n); self.ex_tree.column(c,anchor="center",width=160)
        self.ex_tree.pack(fill="both",expand=True,padx=10)

        bar=ttk.Frame(self.exams); bar.pack(fill="x",padx=10,pady=10)
        ttk.Button(bar,text="Delete",command=self.delete_exam).pack(side="left")

    def add_exam(self):
        vals=[self.ex_course.get().strip(),self.ex_name.get().strip(),self.ex_date.get().strip(),
              self.ex_diff.get().strip(),self.ex_hours.get().strip()]
        if not all(vals) or not self.valid_date(vals[2]):
            messagebox.showerror("Error","Complete all fields and use YYYY-MM-DD."); return
        try:
            h=float(vals[4])
            if h<=0: raise ValueError
        except ValueError:
            messagebox.showerror("Error","Review hours must be positive."); return
        with sqlite3.connect(DB) as conn:
            conn.execute("""INSERT INTO exams(course,name,exam_date,difficulty,review_hours)
                            VALUES(?,?,?,?,?)""",(vals[0],vals[1],vals[2],vals[3],h))
        for v in [self.ex_course,self.ex_name,self.ex_date,self.ex_hours]:v.set("")
        self.ex_diff.set("Medium")
        self.refresh_all()

    def load_exams(self):
        for x in self.ex_tree.get_children():self.ex_tree.delete(x)
        with sqlite3.connect(DB) as conn:
            rows=conn.execute("SELECT id,course,name,exam_date,difficulty,review_hours FROM exams ORDER BY exam_date").fetchall()
        for r in rows:
            self.ex_tree.insert("","end",iid=str(r[0]),values=r[1:])

    def delete_exam(self):
        s=self.ex_tree.selection()
        if not s:
            messagebox.showinfo("Select","Select an exam first."); return
        with sqlite3.connect(DB) as conn:
            conn.execute("DELETE FROM exams WHERE id=?",(s[0],))
        self.refresh_all()

    # Plan
    def build_plan(self):
        top=ttk.Frame(self.plan); top.pack(fill="x",padx=15,pady=10)
        ttk.Label(top,text="Daily Study Plan",font=("Arial",18,"bold")).pack(side="left")
        ttk.Button(top,text="Refresh Plan",command=self.generate_plan).pack(side="right")
        self.plan_text=tk.Text(self.plan,wrap="word")
        self.plan_text.pack(fill="both",expand=True,padx=15,pady=(0,15))

    def generate_plan(self):
        today=date.today()
        with sqlite3.connect(DB) as conn:
            hw=conn.execute("""SELECT course,title,due_date,priority,hours FROM homework
                               WHERE completed=0 ORDER BY due_date""").fetchall()
            ex=conn.execute("""SELECT course,name,exam_date,difficulty,review_hours
                               FROM exams ORDER BY exam_date""").fetchall()

        plan={}
        for c,t,d,p,h in hw:
            due=datetime.strptime(d,"%Y-%m-%d").date()
            if due<today:
                plan.setdefault(today,[]).append(f"OVERDUE: {c} - {t} ({h:.1f}h)")
                continue
            days=(due-today).days+1
            each=h/days
            for k in range(days):
                day=today+timedelta(days=k)
                plan.setdefault(day,[]).append(f"Homework: {c} - {t} ({each:.1f}h, {p})")

        for c,n,d,diff,h in ex:
            exam_day=datetime.strptime(d,"%Y-%m-%d").date()
            days=(exam_day-today).days
            if days<0: continue
            if days==0:
                plan.setdefault(today,[]).append(f"EXAM TODAY: {c} - {n}")
            else:
                each=h/days
                for k in range(days):
                    day=today+timedelta(days=k)
                    plan.setdefault(day,[]).append(f"Exam Review: {c} - {n} ({each:.1f}h, {diff})")

        self.plan_text.delete("1.0","end")
        if not plan:
            self.plan_text.insert("end","No pending homework or upcoming exams.")
            return
        for day in sorted(plan):
            self.plan_text.insert("end",f"{day.strftime('%A, %Y-%m-%d')}\n")
            for task in plan[day]:
                self.plan_text.insert("end",f"  - {task}\n")
            self.plan_text.insert("end","\n")

    # Reminders
    def reminders(self):
        today=date.today()
        tomorrow=today+timedelta(days=1)
        msgs=[]
        with sqlite3.connect(DB) as conn:
            hw=conn.execute("SELECT course,title,due_date FROM homework WHERE completed=0").fetchall()
            ex=conn.execute("SELECT course,name,exam_date FROM exams").fetchall()

        for c,t,d in hw:
            dd=datetime.strptime(d,"%Y-%m-%d").date()
            if dd==today: msgs.append(f"Homework due today: {c} - {t}")
            elif dd==tomorrow: msgs.append(f"Homework due tomorrow: {c} - {t}")

        for c,n,d in ex:
            dd=datetime.strptime(d,"%Y-%m-%d").date()
            if dd==today: msgs.append(f"Exam today: {c} - {n}")
            elif dd==tomorrow: msgs.append(f"Exam tomorrow: {c} - {n}")

        if msgs:
            messagebox.showwarning("Studyline Reminder","\n\n".join(msgs))

    def refresh_all(self):
        self.load_hw()
        self.load_exams()
        self.refresh_dashboard()
        self.generate_plan()

if __name__=="__main__":
    init_db()
    root=tk.Tk()
    App(root)
    root.mainloop()
