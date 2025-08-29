import sqlite3
import tkinter as tk
from tkinter import messagebox
from ttkbootstrap import Style
from ttkbootstrap.widgets import Treeview, Button, Entry, Label, Frame
from tkinter import Toplevel

DB_PATH = 'assets/data/data.db'

def connect_db():
    return sqlite3.connect(DB_PATH)

def get_all_creatures():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Creature")
    creatures = cursor.fetchall()
    conn.close()
    return creatures

def add_creature(data):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Creature (
            maxHp, regenHp, maxMana, regenMana, maxStamina, regenStamina,
            damage, critical, defense, speed, name, behaviors,
            aceleration, sizex, sizey, idTextura
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, data)
    conn.commit()
    conn.close()

def update_creature(id, data):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE Creature
        SET maxHp=?, regenHp=?, maxMana=?, regenMana=?, maxStamina=?, regenStamina=?,
            damage=?, critical=?, defense=?, speed=?, name=?, behaviors=?,
            aceleration=?, sizex=?, sizey=?, idTextura=?
        WHERE id=?
    """, (*data, id))
    conn.commit()
    conn.close()

def delete_creature(id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Creature WHERE id = ?", (id,))
    conn.commit()
    conn.close()

def refresh_list():
    tree.delete(*tree.get_children())
    for creature in get_all_creatures():
        tree.insert('', 'end', values=creature)

def open_form(title, values=None):
    form = Toplevel(root)
    form.title(title)
    form.geometry("400x850")
    form.resizable(False, False)

    labels = [
        'maxHp', 'regenHp', 'maxMana', 'regenMana', 'maxStamina', 'regenStamina',
        'damage', 'critical', 'defense', 'speed', 'name', 'behaviors',
        'aceleration', 'sizex', 'sizey', 'idTextura'
    ]
    entries = []

    for i, label in enumerate(labels):
        Label(form, text=label, bootstyle="secondary").grid(row=i, column=0, padx=10, pady=6, sticky="w")
        entry = Entry(form, width=30, bootstyle="dark")
        entry.grid(row=i, column=1, padx=10, pady=6)
        if values:
            entry.insert(0, values[i + 1])
        entries.append(entry)

    def submit():
        data = [e.get() for e in entries]
        if values:
            update_creature(values[0], data)
        else:
            add_creature(data)
        refresh_list()
        form.destroy()

    btn = Button(form, text="💾 Save", command=submit, bootstyle="success-outline")
    btn.grid(row=len(labels), column=0, columnspan=2, pady=20)

def delete_selected():
    selected = tree.focus()
    if not selected:
        messagebox.showwarning("No Selection", "Please select a creature to delete.")
        return
    values = tree.item(selected, 'values')
    if messagebox.askyesno("Confirm", f"Delete creature '{values[11]}'?"):
        delete_creature(values[0])
        refresh_list()

def open_edit_form():
    selected = tree.focus()
    if not selected:
        messagebox.showwarning("No Selection", "Please select a creature to edit.")
        return
    values = tree.item(selected, 'values')
    open_form("✏️ Edit Creature", values)

def open_add_form():
    open_form("➕ Add Creature")

# ========== INTERFACE ==========
style = Style("darkly")
root = style.master
root.title("🧙‍♂️ Creature Manager")
root.geometry("1500x600")

columns = [
    'ID', 'maxHp', 'regenHp', 'maxMana', 'regenMana', 'maxStamina', 'regenStamina',
    'damage', 'critical', 'defense', 'speed', 'name', 'behaviors',
    'aceleration', 'sizex', 'sizey', 'idTextura'
]
tree = Treeview(root, columns=columns, show='headings', bootstyle="dark")
tree.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

for col in columns:
    tree.heading(col, text=col)
    width = 100
    if col in ['name', 'behaviors']:
        width = 150
    tree.column(col, width=width, anchor='center')

btn_frame = Frame(root)
btn_frame.pack(pady=10)

Button(btn_frame, text="➕ Add", command=open_add_form, bootstyle="primary-outline", width=12).pack(side=tk.LEFT, padx=10)
Button(btn_frame, text="✏️ Edit", command=open_edit_form, bootstyle="warning-outline", width=12).pack(side=tk.LEFT, padx=10)
Button(btn_frame, text="🗑️ Delete", command=delete_selected, bootstyle="danger-outline", width=12).pack(side=tk.LEFT, padx=10)

refresh_list()
root.mainloop()
