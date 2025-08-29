import tkinter as tk
from ttkbootstrap import Style
from ttkbootstrap.constants import *
from tkinter import ttk, messagebox
import sqlite3

DB_NAME = "assets/data/data.db"

class ItemCRUDApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gerenciador de Itens")
        self.selected_type = tk.StringVar(value="Consumable")
        self.current_item_id = None

        self.conn = sqlite3.connect(DB_NAME)
        self.create_table()
        self.build_interface()
        self.load_items()

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS itens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_type TEXT,
                name TEXT,
                texture TEXT,
                description TEXT,
                heal REAL,
                mana REAL,
                stamina REAL,
                effect TEXT,
                defense REAL,
                resistance REAL,
                regen REAL,
                speed REAL,
                attack REAL,
                critical REAL,
                mana_regen REAL,
                classe TEXT,
                condition TEXT,
                special TEXT,
                slot TEXT,
                damage REAL,
                range REAL,
                move REAL,
                ability TEXT,
                texture_action TEXT
            )
        """)
        # Add texture_action column if it doesn't exist
        try:
            cursor.execute("ALTER TABLE itens ADD COLUMN texture_action TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists
        self.conn.commit()

    def build_interface(self):
        frame = ttk.Frame(self.root, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Tipo de Item:").grid(row=0, column=0, sticky=tk.W)
        type_combo = ttk.Combobox(frame, textvariable=self.selected_type, values=["Consumable", "Equipment", "KeyItem", "Weapon"], state="readonly")
        type_combo.grid(row=0, column=1, sticky=tk.W)
        type_combo.bind("<<ComboboxSelected>>", lambda e: self.update_fields())

        self.form_frame = ttk.LabelFrame(frame, text="Detalhes do Item")
        self.form_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=10)
        self.form_entries = {}
        self.update_fields()

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=2, column=0, columnspan=3, pady=10)

        ttk.Button(btn_frame, text="Salvar", command=self.save_item, bootstyle=SUCCESS).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Limpar", command=self.clear_form).pack(side=tk.LEFT)

        self.tree = ttk.Treeview(frame, columns=["ID", "Tipo", "Nome"], show="headings")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Tipo", text="Tipo")
        self.tree.heading("Nome", text="Nome")
        self.tree.grid(row=3, column=0, columnspan=3, pady=10, sticky="nsew")
        self.tree.bind("<Double-1>", self.on_item_select)

        ttk.Button(frame, text="Excluir Selecionado", command=self.delete_selected, bootstyle=DANGER).grid(row=4, column=0, columnspan=3, pady=5)

    def update_fields(self):
        for widget in self.form_frame.winfo_children():
            widget.destroy()
        self.form_entries.clear()

        item_type = self.selected_type.get()
        fields = {
            "Consumable": ["name", "texture", "description", "heal", "mana", "stamina", "effect"],
            "Equipment": ["name", "texture", "description", "defense", "resistance", "regen", "speed", "attack", "critical", "stamina", "mana", "mana_regen", "classe", "condition", "special", "slot"],
            "KeyItem": ["name", "texture", "description", "special"],
            "Weapon": ["name", "texture", "texture_action", "description", "classe", "damage", "critical", "range", "speed", "move", "special", "ability"]
        }

        for i, field in enumerate(fields[item_type]):
            ttk.Label(self.form_frame, text=field.capitalize()+":").grid(row=i, column=0, sticky=tk.W)
            entry = ttk.Entry(self.form_frame)
            entry.grid(row=i, column=1, sticky=tk.W)
            self.form_entries[field] = entry

    def get_form_data(self):
        data = {k: v.get() for k, v in self.form_entries.items()}
        for k in data:
            if k not in ["name", "description", "effect", "classe", "condition", "special", "ability", "slot", "texture", "texture_action"]:
                try:
                    data[k] = float(data[k])
                except:
                    data[k] = 0
        return data

    def save_item(self):
        data = self.get_form_data()
        data["item_type"] = self.selected_type.get()
        cursor = self.conn.cursor()

        placeholders = {
            "Consumable": ("name", "texture", "description", "heal", "mana", "stamina", "effect"),
            "Equipment": ("name", "texture", "description", "defense", "resistance", "regen", "speed", "attack", "critical", "stamina", "mana", "mana_regen", "classe", "condition", "special", "slot"),
            "KeyItem": ("name", "texture", "description", "special"),
            "Weapon": ("name", "texture", "texture_action", "description", "classe", "damage", "critical", "range", "speed", "move", "special", "ability")
        }

        fields = ["item_type"] + list(placeholders[data["item_type"]])
        values = [data.get(f, None) for f in fields[1:]]
        values.insert(0, data["item_type"])

        if self.current_item_id:
            set_clause = ", ".join(f"{f}=?" for f in fields)
            cursor.execute(f"UPDATE itens SET {set_clause} WHERE id = ?", (*values, self.current_item_id))
        else:
            columns = ", ".join(fields)
            qs = ", ".join("?" for _ in fields)
            cursor.execute(f"INSERT INTO itens ({columns}) VALUES ({qs})", values)

        self.conn.commit()
        self.load_items()
        self.clear_form()

    def load_items(self):
        self.tree.delete(*self.tree.get_children())
        cursor = self.conn.cursor()
        for row in cursor.execute("SELECT id, item_type, name FROM itens"):
            self.tree.insert("", "end", iid=row[0], values=row)

    def on_item_select(self, event):
        selected_id = self.tree.focus()
        if not selected_id:
            return
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM itens WHERE id=?", (selected_id,))
        row = cursor.fetchone()
        if row:
            columns = [desc[0] for desc in cursor.description]
            item_dict = dict(zip(columns, row))
            self.current_item_id = item_dict["id"]
            self.selected_type.set(item_dict["item_type"])
            self.update_fields()
            for k, entry in self.form_entries.items():
                entry.delete(0, tk.END)
                if item_dict.get(k) is not None:
                    entry.insert(0, str(item_dict[k]))

    def delete_selected(self):
        selected_id = self.tree.focus()
        if not selected_id:
            return
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM itens WHERE id=?", (selected_id,))
        self.conn.commit()
        self.load_items()
        self.clear_form()

    def clear_form(self):
        for entry in self.form_entries.values():
            entry.delete(0, tk.END)
        self.current_item_id = None

if __name__ == "__main__":
    root = tk.Tk()
    Style("morph")
    app = ItemCRUDApp(root)
    root.mainloop()
