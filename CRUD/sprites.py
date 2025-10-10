import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import json
from PIL import Image, ImageTk

DB_NAME = 'assets/data/data.db'

class SpriteEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Editor de Sprites")
        self.root.configure(bg="#121212")

        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("TFrame", background="#121212")
        style.configure("TLabel", background="#121212", foreground="white")
        style.configure("TButton", background="#2c2c2c", foreground="white")
        style.configure("TEntry", fieldbackground="#1f1f1f", foreground="white")
        style.configure("Treeview", background="#1f1f1f", foreground="white", fieldbackground="#1f1f1f")
        style.configure("Treeview.Heading", background="#2c2c2c", foreground="white")

        self.edicao_id = None
        # Estado para edição/remoção de quadros
        self._list_index_map = []  # lista de refs para cada item do listbox
        self._selected_ref = None  # ref selecionada no listbox
        # Limites para o tamanho visível do canvas (para não atrapalhar a listagem)
        self.max_canvas_w = 640
        self.max_canvas_h = 360

        self.frame = ttk.Frame(root)
        self.frame.pack(padx=10, pady=10)

        self.setup_widgets()
        self.setup_db()
        self.load_data()

    def setup_widgets(self):
        ttk.Label(self.frame, text="Caminho da imagem:").grid(row=0, column=0, sticky="w")
        self.src_entry = ttk.Entry(self.frame, width=40)
        self.src_entry.grid(row=0, column=1)
        ttk.Button(self.frame, text="Buscar", command=self.browse_image).grid(row=0, column=2, padx=5)
        ttk.Button(self.frame, text="Carregar Imagem", command=self.load_image).grid(row=0, column=3, padx=5)

        ttk.Label(self.frame, text="Linhas:").grid(row=1, column=0, sticky="w")
        self.linhas_entry = ttk.Entry(self.frame, width=10)
        self.linhas_entry.grid(row=1, column=1, sticky="w")

        ttk.Label(self.frame, text="Colunas:").grid(row=2, column=0, sticky="w")
        self.colunas_entry = ttk.Entry(self.frame, width=10)
        self.colunas_entry.grid(row=2, column=1, sticky="w")

        self.animations = []          # [[ [r,c], ... ], ...]
        self.current_animation = []   # [ [r,c], ... ]

        ttk.Button(self.frame, text="Adicionar Linha de Animação", command=self.add_animation_line).grid(row=3, column=0, columnspan=2, pady=5)
        ttk.Button(self.frame, text="Remover Linha Selecionada", command=self.remove_selected_anim_line).grid(row=3, column=2, columnspan=2, pady=5)

        self.anim_listbox = tk.Listbox(self.frame, height=6, width=60, bg="#1f1f1f", fg="white")
        self.anim_listbox.grid(row=4, column=0, columnspan=4, sticky="ew")
        self.anim_listbox.bind("<<ListboxSelect>>", self.on_listbox_select)

        # Canvas com barras de rolagem
        canvas_frame = ttk.Frame(self.frame)
        canvas_frame.grid(row=5, column=0, columnspan=4, pady=10, sticky="nsew")
        self.canvas = tk.Canvas(canvas_frame, bg="black", highlightthickness=0)
        self.h_scroll = ttk.Scrollbar(canvas_frame, orient="horizontal", command=self.canvas.xview)
        self.v_scroll = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=self.h_scroll.set, yscrollcommand=self.v_scroll.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.v_scroll.grid(row=0, column=1, sticky="ns")
        self.h_scroll.grid(row=1, column=0, sticky="ew")
        canvas_frame.rowconfigure(0, weight=1)
        canvas_frame.columnconfigure(0, weight=1)
        self.canvas.bind("<Button-1>", self.select_frame)

        ttk.Button(self.frame, text="Salvar Sprite", command=self.save_sprite).grid(row=6, column=0, pady=5)
        ttk.Button(self.frame, text="Editar Selecionado", command=self.edit_selected).grid(row=6, column=1, pady=5)
        ttk.Button(self.frame, text="Remover Quadro Selecionado", command=self.remove_selected_frame).grid(row=6, column=2, columnspan=2, pady=5)

        self.tree = ttk.Treeview(self.frame, columns=("id", "src", "linhas", "colunas", "animations"), show='headings', height=8)
        self.tree.heading("id", text="ID")
        self.tree.heading("src", text="Imagem")
        self.tree.heading("linhas", text="Linhas")
        self.tree.heading("colunas", text="Colunas")
        self.tree.heading("animations", text="Animações")
        self.tree.grid(row=7, column=0, columnspan=4, pady=10, sticky="ew")

        ttk.Button(self.frame, text="Deletar Selecionado", command=self.delete_selected).grid(row=8, column=0, columnspan=4, pady=5)

    def browse_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Imagens", "*.png;*.jpg;*.jpeg;*.bmp")])
        if file_path:
            self.src_entry.delete(0, tk.END)
            self.src_entry.insert(0, file_path)

    def load_image(self, preserve: bool = False):
        path = self.src_entry.get()
        try:
            img = Image.open(path)
            linhas = int(self.linhas_entry.get())
            colunas = int(self.colunas_entry.get())

            self.sheet_img = img
            self.tk_img = ImageTk.PhotoImage(img)

            # Define tamanho visível e imagem (limitado para não atrapalhar a listagem)
            self.canvas.config(
                width=min(img.width, self.max_canvas_w),
                height=min(img.height, self.max_canvas_h)
            )
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, image=self.tk_img, anchor="nw")

            self.cell_w = img.width // colunas
            self.cell_h = img.height // linhas

            for i in range(linhas):
                self.canvas.create_line(0, i*self.cell_h, img.width, i*self.cell_h, fill="gray")
            for j in range(colunas):
                self.canvas.create_line(j*self.cell_w, 0, j*self.cell_w, img.height, fill="gray")

            self.canvas.config(scrollregion=self.canvas.bbox("all"))

            if not preserve:
                self.animations = []
                self.current_animation = []
            self.rebuild_anim_listbox()

        except Exception as e:
            messagebox.showerror("Erro ao carregar imagem", str(e))

    def select_frame(self, event):
        # Considera o deslocamento das barras de rolagem
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        try:
            linha = int(canvas_y // self.cell_h)
            coluna = int(canvas_x // self.cell_w)
        except Exception:
            return

        if self._selected_ref and self._selected_ref[0] in ("saved", "current"):
            kind = self._selected_ref[0]
            if kind == "saved":
                _, li, fi = self._selected_ref
                if 0 <= li < len(self.animations) and 0 <= fi < len(self.animations[li]):
                    self.animations[li][fi] = [linha, coluna]
            else:  # current
                _, idx = self._selected_ref
                if 0 <= idx < len(self.current_animation):
                    self.current_animation[idx] = [linha, coluna]
            self._selected_ref = None
            self.anim_listbox.selection_clear(0, tk.END)
        else:
            self.current_animation.append([linha, coluna])

        self.rebuild_anim_listbox()

    def add_animation_line(self):
        if self.current_animation:
            self.animations.append(self.current_animation)
            self.current_animation = []
            self.rebuild_anim_listbox()
        else:
            messagebox.showinfo("Nada para adicionar", "Selecione quadros antes de adicionar a linha de animação")

    def save_sprite(self):
        src = self.src_entry.get()
        linhas = self.linhas_entry.get()
        colunas = self.colunas_entry.get()
        try:
            linhas = int(linhas)
            colunas = int(colunas)
            anim_json = json.dumps(self.animations)
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

            if self.edicao_id:
                cursor.execute("UPDATE Sprite SET src=?, linhas=?, colunas=?, animations=? WHERE id=?",
                               (src, linhas, colunas, anim_json, self.edicao_id))
                self.edicao_id = None
            else:
                cursor.execute("INSERT INTO Sprite (src, linhas, colunas, animations) VALUES (?, ?, ?, ?)",
                               (src, linhas, colunas, anim_json))

            conn.commit()
            conn.close()
            self.load_data()
            self.clear_entries()
        except Exception as e:
            messagebox.showerror("Erro ao salvar", str(e))

    def edit_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Seleção vazia", "Selecione um sprite para editar.")
            return

        item = self.tree.item(selected[0])
        values = item['values']
        sprite_id = values[0]
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Sprite WHERE id = ?", (sprite_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            self.edicao_id = row[0]
            self.src_entry.delete(0, tk.END)
            self.src_entry.insert(0, row[1])
            self.linhas_entry.delete(0, tk.END)
            self.linhas_entry.insert(0, row[2])
            self.colunas_entry.delete(0, tk.END)
            self.colunas_entry.insert(0, row[3])
            try:
                self.animations = json.loads(row[4]) if row[4] else []
            except Exception:
                self.animations = []
            self.current_animation = []
            # Carrega a imagem com grade e preserva animações
            self.load_image(preserve=True)
            self.rebuild_anim_listbox()

    def clear_entries(self):
        self.src_entry.delete(0, tk.END)
        self.linhas_entry.delete(0, tk.END)
        self.colunas_entry.delete(0, tk.END)
        self.canvas.delete("all")
        self.anim_listbox.delete(0, tk.END)
        self.animations = []
        self.current_animation = []
        self.edicao_id = None
        self._list_index_map = []
        self._selected_ref = None

    def load_data(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Sprite")
        for row in cursor.fetchall():
            self.tree.insert("", tk.END, values=row)
        conn.close()

    def delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            return
        item = self.tree.item(selected[0])
        values = item['values']
        sprite_id = values[0]
        if not messagebox.askyesno("Confirmação", f"Deseja realmente deletar o sprite ID {sprite_id}?"):
            return
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Sprite WHERE id = ?", (sprite_id,))
        conn.commit()
        conn.close()
        self.load_data()

    def on_listbox_select(self, event=None):
        sel = self.anim_listbox.curselection()
        if not sel:
            self._selected_ref = None
            return
        idx = sel[0]
        if 0 <= idx < len(self._list_index_map):
            self._selected_ref = self._list_index_map[idx]
        else:
            self._selected_ref = None

    def remove_selected_anim_line(self):
        if not self._list_index_map:
            return
        sel = self.anim_listbox.curselection()
        if not sel:
            messagebox.showinfo("Seleção vazia", "Selecione um quadro ou separador da linha que deseja remover.")
            return
        ref = self._list_index_map[sel[0]]
        if ref[0] == "saved":
            _, li, _ = ref
        elif ref[0] == "sep":
            _, li = ref
        elif ref[0] == "current":
            self.current_animation = []
            self.rebuild_anim_listbox()
            return
        else:
            return
        if 0 <= li < len(self.animations):
            if not messagebox.askyesno("Confirmar", f"Remover toda a linha #{li+1}?"):
                return
            del self.animations[li]
            self.rebuild_anim_listbox()

    def remove_selected_frame(self):
        sel = self.anim_listbox.curselection()
        if not sel:
            messagebox.showinfo("Seleção vazia", "Selecione um quadro para remover.")
            return
        ref = self._list_index_map[sel[0]] if sel[0] < len(self._list_index_map) else None
        if not ref:
            return
        if ref[0] == "saved":
            _, li, fi = ref
            if 0 <= li < len(self.animations) and 0 <= fi < len(self.animations[li]):
                del self.animations[li][fi]
                if not self.animations[li]:
                    del self.animations[li]
        elif ref[0] == "current":
            _, idx = ref
            if 0 <= idx < len(self.current_animation):
                del self.current_animation[idx]
        else:
            return
        self._selected_ref = None
        self.anim_listbox.selection_clear(0, tk.END)
        self.rebuild_anim_listbox()

    def rebuild_anim_listbox(self):
        self.anim_listbox.delete(0, tk.END)
        self._list_index_map = []
        for li, linha in enumerate(self.animations):
            for fi, frame in enumerate(linha):
                self.anim_listbox.insert(tk.END, f"Quadro salvo L{li+1} #{fi+1}: {frame}")
                self._list_index_map.append(("saved", li, fi))
            self.anim_listbox.insert(tk.END, f"--- Linha {li+1} ---")
            self._list_index_map.append(("sep", li))
        if self.current_animation:
            for idx, frame in enumerate(self.current_animation):
                self.anim_listbox.insert(tk.END, f"Quadro atual #{idx+1}: {frame}")
                self._list_index_map.append(("current", idx))
        self.render_animation_overlays()

    def render_animation_overlays(self):
        try:
            self.canvas.delete("overlay")
        except Exception:
            pass
        if not hasattr(self, "cell_w") or not hasattr(self, "cell_h"):
            return
        for linha in self.animations:
            for (r, c) in linha:
                x0 = c * self.cell_w
                y0 = r * self.cell_h
                x1 = x0 + self.cell_w
                y1 = y0 + self.cell_h
                self.canvas.create_rectangle(x0, y0, x1, y1, outline="lime", width=2, tags=("overlay", "saved"))
        for (r, c) in self.current_animation:
            x0 = c * self.cell_w
            y0 = r * self.cell_h
            x1 = x0 + self.cell_w
            y1 = y0 + self.cell_h
            self.canvas.create_rectangle(x0, y0, x1, y1, outline="yellow", width=2, dash=(3, 2), tags=("overlay", "current"))

    def setup_db(self):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS Sprite (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            src TEXT,
                            linhas INTEGER,
                            colunas INTEGER,
                            animations TEXT
                          )''')
        conn.commit()
        conn.close()

if __name__ == '__main__':
    root = tk.Tk()
    app = SpriteEditorApp(root)
    root.mainloop()
