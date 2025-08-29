import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import json
import os
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from assets.behaviors.actions import actions
from assets.behaviors.conditions import conditions

# Simulando ações, condições e estruturas carregadas de arquivos externos
actions = actions  # Agora é um dicionário {nome: função}
conditions = conditions  # Agora é um dicionário {nome: função}
structures = ["Sequence", "Selector", "Inverter", "Succeeder"]

os.makedirs("data", exist_ok=True)

with sqlite3.connect("assets/data/data.db") as conn:
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS BehaviorTree (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        structure TEXT NOT NULL
    );
    """)
    conn.commit()

class BehaviorTreeEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Editor de Árvores de Comportamento")
        self.root.geometry("1200x700")
        style = tb.Style("darkly")

        self.selected_nodes = []
        self.tree_name_var = tk.StringVar()

        main_frame = ttk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Top
        frame_top = ttk.Frame(left_frame)
        frame_top.pack(pady=5)

        ttk.Label(frame_top, text="Nome da Árvore:").pack(side=tk.LEFT, padx=5)
        self.name_entry = ttk.Entry(frame_top, textvariable=self.tree_name_var, width=40)
        self.name_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_top, text="Salvar Árvore", command=self.save_tree, bootstyle=SUCCESS).pack(side=tk.LEFT, padx=5)

        # Lista de nós
        self.node_listbox = tk.Listbox(left_frame, width=60, height=14)
        self.node_listbox.pack(pady=5)

        # Botões de nós
        frame_buttons = ttk.Frame(left_frame)
        frame_buttons.pack(pady=5)

        self.action_var = tk.StringVar()
        self.condition_var = tk.StringVar()
        self.structure_var = tk.StringVar()

        # Alteração aqui: usar list(actions.keys()) para obter os nomes das ações
        self.action_cb = ttk.Combobox(frame_buttons, textvariable=self.action_var, values=list(actions.keys()), width=15)
        # Alteração aqui: usar list(conditions.keys()) para obter os nomes das condições
        self.condition_cb = ttk.Combobox(frame_buttons, textvariable=self.condition_var, values=list(conditions.keys()), width=15)
        self.structure_cb = ttk.Combobox(frame_buttons, textvariable=self.structure_var, values=structures, width=15)

        self.action_cb.pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_buttons, text="Ação", command=self.add_action, bootstyle=PRIMARY).pack(side=tk.LEFT, padx=5)

        self.condition_cb.pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_buttons, text="Condição", command=self.add_condition, bootstyle=PRIMARY).pack(side=tk.LEFT, padx=5)

        self.structure_cb.pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_buttons, text="Estrutura", command=self.add_structure, bootstyle=SECONDARY).pack(side=tk.LEFT, padx=5)

        frame_extra = ttk.Frame(left_frame)
        frame_extra.pack(pady=5)

        ttk.Button(frame_extra, text="Início de Bloco", command=self.add_block_start, bootstyle=INFO).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_extra, text="Fim de Bloco", command=self.add_block_end, bootstyle=INFO).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_extra, text="Remover Selecionado", command=self.remove_selected, bootstyle=DANGER).pack(side=tk.LEFT, padx=5)

        # Separador
        ttk.Separator(left_frame).pack(fill='x', pady=10)
        ttk.Label(left_frame, text="Árvores Existentes:").pack()

        # Lista de árvores
        frame_list = ttk.Frame(left_frame)
        frame_list.pack(pady=5)

        self.tree_listbox = tk.Listbox(frame_list, width=40, height=8)
        self.tree_listbox.pack(side=tk.LEFT)
        self.tree_listbox.bind("<Double-Button-1>", self.load_tree)

        scrollbar = ttk.Scrollbar(frame_list, orient="vertical", command=self.tree_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill="y")
        self.tree_listbox.config(yscrollcommand=scrollbar.set)

        # Botões de manipulação
        frame_bottom = ttk.Frame(left_frame)
        frame_bottom.pack(pady=5)

        ttk.Button(frame_bottom, text="Excluir", command=self.delete_tree, bootstyle=DANGER).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_bottom, text="Editar", command=self.edit_tree, bootstyle=WARNING).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_bottom, text="Limpar", command=self.clear_fields, bootstyle=SECONDARY).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_bottom, text="Visualizar Árvore", command=self.draw_tree_visualization, bootstyle=INFO).pack(side=tk.LEFT, padx=5)

        # Canvas para visualização da árvore
        ttk.Label(right_frame, text="Visualização da Árvore").pack()
        self.canvas = tk.Canvas(right_frame, bg="#1e1e1e", width=550, height=600, scrollregion=(0, 0, 1000, 2000))
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.load_tree_list()

    # Métodos de adição de nós
    def add_action(self):
        action = self.action_var.get()
        if action:
            self.selected_nodes.append(("action", action))
            self.node_listbox.insert(tk.END, f"Ação: {action}")

    def add_condition(self):
        cond = self.condition_var.get()
        if cond:
            self.selected_nodes.append(("condition", cond))
            self.node_listbox.insert(tk.END, f"Condição: {cond}")

    def add_structure(self):
        struct = self.structure_var.get()
        if struct:
            self.selected_nodes.append(("structure", struct))
            self.node_listbox.insert(tk.END, f"Estrutura: {struct}")

    def add_block_start(self):
        self.selected_nodes.append(("block_start", "{"))
        self.node_listbox.insert(tk.END, "Início de Bloco")

    def add_block_end(self):
        self.selected_nodes.append(("block_end", "}"))
        self.node_listbox.insert(tk.END, "Fim de Bloco")

    def remove_selected(self):
        selection = self.node_listbox.curselection()
        if selection:
            index = selection[0]
            self.node_listbox.delete(index)
            del self.selected_nodes[index]

    def save_tree(self):
        name = self.tree_name_var.get()
        if not name:
            messagebox.showerror("Erro", "Dê um nome à árvore.")
            return
        if not self.selected_nodes:
            messagebox.showerror("Erro", "Adicione ao menos um nó.")
            return

        structure = json.dumps(self.selected_nodes)
        with sqlite3.connect("data/data.db") as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO BehaviorTree (name, structure) VALUES (?, ?)", (name, structure))
            conn.commit()
        self.clear_fields()
        self.load_tree_list()
        messagebox.showinfo("Sucesso", "Árvore salva com sucesso!")

    def load_tree_list(self):
        self.tree_listbox.delete(0, tk.END)
        with sqlite3.connect("data/data.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM BehaviorTree")
            for row in cursor.fetchall():
                self.tree_listbox.insert(tk.END, f"{row[0]} - {row[1]}")

    def delete_tree(self):
        selection = self.tree_listbox.curselection()
        if selection:
            tree_id = int(self.tree_listbox.get(selection[0]).split(" - ")[0])
            with sqlite3.connect("data/data.db") as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM BehaviorTree WHERE id = ?", (tree_id,))
                conn.commit()
            self.load_tree_list()
            messagebox.showinfo("Removido", "Árvore excluída com sucesso.")

    def load_tree(self, event):
        selection = self.tree_listbox.curselection()
        if selection:
            tree_id = int(self.tree_listbox.get(selection[0]).split(" - ")[0])
            with sqlite3.connect("data/data.db") as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name, structure FROM BehaviorTree WHERE id = ?", (tree_id,))
                row = cursor.fetchone()
                if row:
                    self.tree_name_var.set(row[0])
                    self.selected_nodes = json.loads(row[1])
                    self.node_listbox.delete(0, tk.END)
                    for tipo, nome in self.selected_nodes:
                        label = {
                            "action": f"Ação: {nome}",
                            "condition": f"Condição: {nome}",
                            "structure": f"Estrutura: {nome}",
                            "block_start": "Início de Bloco",
                            "block_end": "Fim de Bloco"
                        }.get(tipo, nome)
                        self.node_listbox.insert(tk.END, label)

    def edit_tree(self):
        selection = self.tree_listbox.curselection()
        if selection:
            tree_id = int(self.tree_listbox.get(selection[0]).split(" - ")[0])
            name = self.tree_name_var.get()
            structure = json.dumps(self.selected_nodes)
            with sqlite3.connect("data/data.db") as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE BehaviorTree SET name = ?, structure = ? WHERE id = ?", (name, structure, tree_id))
                conn.commit()
            self.load_tree_list()
            messagebox.showinfo("Atualizado", "Árvore atualizada com sucesso.")

    def clear_fields(self):
        self.tree_name_var.set("")
        self.node_listbox.delete(0, tk.END)
        self.selected_nodes.clear()
        self.canvas.delete("all")

    def draw_tree_visualization(self):
        self.canvas.delete("all")
        x, y = 300, 20
        stack = []
        level = 0

        for tipo, nome in self.selected_nodes:
            if tipo == "block_start":
                stack.append((x, y))
                level += 1
                continue
            elif tipo == "block_end":
                if stack:
                    x, y = stack.pop()
                level = max(0, level - 1)
                continue

            node_text = {
                "action": f"Ação: {nome}",
                "condition": f"Condição: {nome}",
                "structure": f"Estrutura: {nome}"
            }.get(tipo, nome)

            box_x = x + level * 40
            self.canvas.create_rectangle(box_x - 80, y, box_x + 80, y + 40, fill="#292929", outline="#55aaff", width=2)
            self.canvas.create_text(box_x, y + 20, text=node_text, fill="white", font=("Helvetica", 10))

            if y > 20:
                self.canvas.create_line(box_x, y - 20, box_x, y, fill="#55aaff", arrow=tk.FIRST)

            y += 70

if __name__ == "__main__":
    root = tb.Window(themename="darkly")
    app = BehaviorTreeEditor(root)
    root.mainloop()