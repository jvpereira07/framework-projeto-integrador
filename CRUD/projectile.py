import tkinter as tk
from tkinter import Toplevel, messagebox
from ttkbootstrap import Style
from ttkbootstrap.widgets import Treeview, Frame, Label, Entry, Button
import sqlite3

# ===== BANCO DE DADOS =====

def connect_db():
    return sqlite3.connect("assets/data/data.db")  # Substitua se necessário

def create_projectile_table():
    conn = connect_db()
    cursor = conn.cursor()
    # Cria a tabela se não existir
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Projectile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            speed REAL,
            damage REAL,
            penetration REAL,
            sizex INTEGER,
            sizey INTEGER,
            time REAL,
            behavior TEXT,
            idTextura INTEGER
        )
    """)
    
    # Verifica e adiciona a coluna idTextura se não existir (caso a tabela seja antiga)
    cursor.execute("PRAGMA table_info(Projectile)")
    columns = [col[1] for col in cursor.fetchall()]
    if "idTextura" not in columns:
        cursor.execute("ALTER TABLE Projectile ADD COLUMN idTextura INTEGER")
    
    conn.commit()
    conn.close()

def get_all_projectiles():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Projectile")
    result = cursor.fetchall()
    conn.close()
    return result

def add_projectile(data):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Projectile (speed, damage, penetration, sizex, sizey, time, behavior, idTextura)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, data)
    conn.commit()
    conn.close()

def update_projectile(id, data):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE Projectile
        SET speed=?, damage=?, penetration=?, sizex=?, sizey=?, time=?, behavior=?, idTextura=?
        WHERE id=?
    """, (*data, id))
    conn.commit()
    conn.close()

def delete_projectile(id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Projectile WHERE id = ?", (id,))
    conn.commit()
    conn.close()

# ===== INTERFACE =====

def refresh_projectile_list():
    projectile_tree.delete(*projectile_tree.get_children())
    for p in get_all_projectiles():
        projectile_tree.insert('', 'end', values=p)

def open_projectile_form(title, values=None):
    form = Toplevel(root)
    form.title(title)
    form.geometry("420x550")
    form.resizable(False, False)

    labels = ['speed', 'damage', 'penetration', 'sizex', 'sizey', 'time', 'behavior', 'idTextura']
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
            update_projectile(values[0], data)
        else:
            add_projectile(data)
        refresh_projectile_list()
        form.destroy()

    Button(form, text="💾 Salvar", command=submit, bootstyle="success-outline").grid(row=len(labels), column=0, columnspan=2, pady=20)

def delete_selected_projectile():
    selected = projectile_tree.focus()
    if not selected:
        messagebox.showwarning("Nenhuma seleção", "Selecione um projétil para deletar.")
        return
    values = projectile_tree.item(selected, 'values')
    if messagebox.askyesno("Confirmar", f"Excluir projétil ID {values[0]}?"):
        delete_projectile(values[0])
        refresh_projectile_list()

def open_edit_projectile_form():
    selected = projectile_tree.focus()
    if not selected:
        messagebox.showwarning("Nenhuma seleção", "Selecione um projétil para editar.")
        return
    values = projectile_tree.item(selected, 'values')
    open_projectile_form("✏️ Editar Projétil", values)

def open_add_projectile_form():
    open_projectile_form("➕ Novo Projétil")

# ===== JANELA PRINCIPAL =====

# Cria tabela e adiciona coluna idTextura se necessário
create_projectile_table()

style = Style("darkly")
root = style.master
root.title("Gerenciador de Projéteis")
root.geometry("950x500")
root.resizable(False, False)

Label(root, text="🧨 Projéteis", font=("Arial", 16), bootstyle="inverse-dark").pack(pady=(20, 5))

projectile_columns = ['ID', 'speed', 'damage', 'penetration', 'sizex', 'sizey', 'time', 'behavior', 'idTextura']
projectile_tree = Treeview(root, columns=projectile_columns, show='headings', bootstyle="dark")
projectile_tree.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

for col in projectile_columns:
    projectile_tree.heading(col, text=col)
    projectile_tree.column(col, width=100, anchor='center')

btn_frame = Frame(root)
btn_frame.pack(pady=10)

Button(btn_frame, text="➕ Novo", command=open_add_projectile_form, bootstyle="primary-outline", width=12).pack(side=tk.LEFT, padx=10)
Button(btn_frame, text="✏️ Editar", command=open_edit_projectile_form, bootstyle="warning-outline", width=12).pack(side=tk.LEFT, padx=10)
Button(btn_frame, text="🗑️ Excluir", command=delete_selected_projectile, bootstyle="danger-outline", width=12).pack(side=tk.LEFT, padx=10)

refresh_projectile_list()
root.mainloop()
