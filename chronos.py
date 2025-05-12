import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
from datetime import datetime, timedelta
import calendar
import threading
import time

class Task:
    def __init__(self, title, description="", due_date=None, priority="Medium", recurring=False, recurrence_interval=None):
        self.title = title
        self.description = description
        self.due_date = due_date
        self.priority = priority
        self.completed = False
        self.recurring = recurring
        self.recurrence_interval = recurrence_interval
        self.created_at = datetime.now()

    def to_dict(self):
        return {
            "title": self.title,
            "description": self.description,
            "due_date": self.due_date.strftime("%Y-%m-%d %H:%M") if self.due_date else None,
            "priority": self.priority,
            "completed": self.completed,
            "recurring": self.recurring,
            "recurrence_interval": self.recurrence_interval,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M")
        }

class ChronosApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Chronos - Time Management System")
        self.tasks = []
        self.current_month = datetime.now().month
        self.current_year = datetime.now().year
        
        self.load_tasks()
        self.setup_ui()
        self.start_reminder_daemon()

    def setup_ui(self):
        # Main container
        self.main_frame = ttk.Frame(self.root, padding=20)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Task Input Section
        self.task_input_frame = ttk.LabelFrame(self.main_frame, text="New Task")
        self.task_input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        ttk.Label(self.task_input_frame, text="Title:").grid(row=0, column=0)
        self.title_entry = ttk.Entry(self.task_input_frame, width=30)
        self.title_entry.grid(row=0, column=1)

        ttk.Label(self.task_input_frame, text="Description:").grid(row=1, column=0)
        self.desc_entry = ttk.Entry(self.task_input_frame, width=30)
        self.desc_entry.grid(row=1, column=1)

        ttk.Label(self.task_input_frame, text="Due Date (YYYY-MM-DD HH:MM):").grid(row=2, column=0)
        self.due_entry = ttk.Entry(self.task_input_frame)
        self.due_entry.grid(row=2, column=1)

        ttk.Label(self.task_input_frame, text="Priority:").grid(row=3, column=0)
        self.priority_var = tk.StringVar()
        self.priority_combobox = ttk.Combobox(self.task_input_frame, textvariable=self.priority_var, 
                                            values=["Low", "Medium", "High"])
        self.priority_combobox.current(1)
        self.priority_combobox.grid(row=3, column=1)

        ttk.Button(self.task_input_frame, text="Add Task", command=self.add_task).grid(row=4, columnspan=2, pady=5)

        # Task List Section
        self.task_list_frame = ttk.LabelFrame(self.main_frame, text="Tasks")
        self.task_list_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        self.tree = ttk.Treeview(self.task_list_frame, columns=("Title", "Due Date", "Priority", "Status"), show="headings")
        self.tree.heading("Title", text="Title")
        self.tree.heading("Due Date", text="Due Date")
        self.tree.heading("Priority", text="Priority")
        self.tree.heading("Status", text="Status")
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Calendar Section
        self.calendar_frame = ttk.LabelFrame(self.main_frame, text="Calendar")
        self.calendar_frame.grid(row=0, column=1, rowspan=2, padx=10, pady=10, sticky="nsew")

        self.calendar_header = ttk.Frame(self.calendar_frame)
        self.calendar_header.pack(pady=5)
        
        ttk.Button(self.calendar_header, text="<", command=self.prev_month).pack(side=tk.LEFT)
        self.month_label = ttk.Label(self.calendar_header, text="", width=20)
        self.month_label.pack(side=tk.LEFT)
        ttk.Button(self.calendar_header, text=">", command=self.next_month).pack(side=tk.LEFT)

        self.calendar_grid = ttk.Frame(self.calendar_frame)
        self.calendar_grid.pack()
        self.update_calendar()

        # Configure grid weights
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(1, weight=1)

        self.update_task_list()

    def add_task(self):
        title = self.title_entry.get()
        description = self.desc_entry.get()
        due_date = self.due_entry.get()
        priority = self.priority_var.get()

        try:
            due_date = datetime.strptime(due_date, "%Y-%m-%d %H:%M") if due_date else None
        except ValueError:
            messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD HH:MM")
            return

        new_task = Task(title, description, due_date, priority)
        self.tasks.append(new_task)
        self.save_tasks()
        self.update_task_list()
        self.clear_input_fields()

    def update_task_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        for task in self.tasks:
            status = "Completed" if task.completed else "Pending"
            self.tree.insert("", "end", values=(
                task.title,
                task.due_date.strftime("%Y-%m-%d %H:%M") if task.due_date else "No due date",
                task.priority,
                status
            ), tags=(task.priority,))

        self.tree.tag_configure("High", background="#ffcccc")
        self.tree.tag_configure("Medium", background="#ffffcc")
        self.tree.tag_configure("Low", background="#ccffcc")

    def clear_input_fields(self):
        self.title_entry.delete(0, tk.END)
        self.desc_entry.delete(0, tk.END)
        self.due_entry.delete(0, tk.END)
        self.priority_combobox.current(1)

    def save_tasks(self):
        with open("tasks.json", "w") as f:
            json.dump([task.to_dict() for task in self.tasks], f, indent=2)

    def load_tasks(self):
        try:
            with open("tasks.json", "r") as f:
                tasks_data = json.load(f)
                self.tasks = []
                for task_data in tasks_data:
                    task = Task(
                        title=task_data["title"],
                        description=task_data["description"],
                        due_date=datetime.strptime(task_data["due_date"], "%Y-%m-%d %H:%M") if task_data["due_date"] else None,
                        priority=task_data["priority"]
                    )
                    task.completed = task_data["completed"]
                    self.tasks.append(task)
        except FileNotFoundError:
            pass

    def update_calendar(self):
        for widget in self.calendar_grid.winfo_children():
            widget.destroy()

        cal = calendar.monthcalendar(self.current_year, self.current_month)
        month_name = calendar.month_name[self.current_month]
        self.month_label.config(text=f"{month_name} {self.current_year}")

        # Create day headers
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i, day in enumerate(days):
            ttk.Label(self.calendar_grid, text=day, width=10, relief="ridge").grid(row=0, column=i)

        # Create calendar days
        for week_num, week in enumerate(cal, start=1):
            for day_num, day in enumerate(week):
                if day != 0:
                    day_frame = ttk.Frame(self.calendar_grid, relief="ridge", borderwidth=1)
                    day_frame.grid(row=week_num, column=day_num, sticky="nsew", padx=2, pady=2)
                    ttk.Label(day_frame, text=str(day)).pack()
                    # Add task indicators here

    def prev_month(self):
        self.current_month -= 1
        if self.current_month < 1:
            self.current_month = 12
            self.current_year -= 1
        self.update_calendar()

    def next_month(self):
        self.current_month += 1
        if self.current_month > 12:
            self.current_month = 1
            self.current_year += 1
        self.update_calendar()

    def start_reminder_daemon(self):
        def reminder_check():
            while True:
                now = datetime.now()
                for task in self.tasks:
                    if task.due_date and not task.completed:
                        if now >= task.due_date - timedelta(minutes=15) and now < task.due_date:
                            messagebox.showwarning(
                                "Task Reminder",
                                f"Task due soon: {task.title}\nDue at: {task.due_date.strftime('%Y-%m-%d %H:%M')}"
                            )
                time.sleep(60)

        reminder_thread = threading.Thread(target=reminder_check, daemon=True)
        reminder_thread.start()

if __name__ == "__main__":
    root = tk.Tk()
    app = ChronosApp(root)
    root.mainloop()