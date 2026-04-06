import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import shutil
import threading
from collections import defaultdict

def ext_folder(ext):
    """Devolve nome da pasta dinâmico. Ex: .jpg → Ficheiros jpg / sem ext → Sem ext"""
    return ("Ficheiros " + ext[1:]).lower() if ext else "Sem ext"


def unique_path(dest):
    base, suffix = os.path.splitext(dest)
    counter = 1
    path = dest
    while os.path.exists(path):
        path = f"{base}_{counter}{suffix}"
        counter += 1
    return path


# ── Janela principal ───────────────────────────────────────────────
BG       = "#1e1e2f"
SURFACE   = "#2b2b40"
FG        = "#e0e0e8"
ACCENT_BG = "#e67e22"
ACCENT_HV = "#d35400"
DISABLED  = "#555560"
PROGRESS_BG = "#333345"


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Organizador de Ficheiros")
        self.root.geometry("480x660")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

        self.folder    = tk.StringVar()
        self.preview   = []          # [(folder_name, count), ...]
        self.undo_log  = []          # [(src, dest), ...]  para desfazer
        self.moving    = False

        # ── Fontes ──
        self.fnt_main = ("Segoe UI", 9)
        self.fnt_bold = ("Segoe UI", 9, "bold")

        self._build()

    # ── Construção dos widgets ──────────────────────────────────
    def _build(self):
        pad = dict(padx=18)

        # Title
        tk.Label(self.root, text="Organizador de Ficheiros", bg=BG, fg=FG,
                 font=("Segoe UI", 16, "bold")).pack(pady=(16, 6), **pad)

        # ── Folder frame ──
        frm = tk.Frame(self.root, bg=SURFACE)
        frm.pack(fill="x", padx=18, pady=4)

        tk.Label(frm, text="Pasta:", bg=SURFACE, fg=FG,
                 font=self.fnt_main).pack(anchor="w", padx=(12, 0), pady=(8, 2))

        row = tk.Frame(frm, bg=SURFACE)
        row.pack(fill="x", padx=12, pady=(0, 8))
        self.entry_folder = tk.Entry(
            row, textvariable=self.folder, bg="#3a3a50", fg=FG,
            insertbackground=FG, relief="flat", font=self.fnt_main)
        self.entry_folder.pack(side="left", fill="x", expand=True, ipady=5)

        self.btn_browse = tk.Button(
            row, text="Procurar…", command=self._browse, bg="#3a3a50", fg=FG,
            activebackground="#4a4a60", activeforeground=FG, relief="flat",
            font=self.fnt_main, cursor="hand2")
        self.btn_browse.pack(side="left", padx=(8, 0), ipadx=12, ipady=2)

        # ── Preview frame ──
        tk.Label(self.root, text="Pré-visualização", bg=BG, fg=FG,
                 font=self.fnt_bold).pack(anchor="w", padx=20, pady=(10, 2))
        self.lst_preview = tk.Listbox(
            self.root, bg="#3a3a50", fg=FG, relief="flat",
            font=("Consolas", 9), height=7, highlightthickness=0)
        self.lst_preview.pack(fill="x", padx=18, pady=2)

        # ── Progress ──
        self.progress_var = tk.DoubleVar(value=0)
        self.progress = ttk.Progressbar(
            self.root, variable=self.progress_var, maximum=100)
        self.progress.pack(fill="x", padx=18, pady=(4, 2))

        for bar in self.progress.winfo_children():
            bar.configure(background=ACCENT_BG)
        self.progress.configure(style="Rufus.Horizontal.TProgressbar")

        self.lbl_pct = tk.Label(self.root, text="0%", bg=BG, fg=FG, font=self.fnt_main)
        self.lbl_pct.pack(anchor="e", padx=20)

        # ── Log ──
        tk.Label(self.root, text="Registo de atividade", bg=BG, fg=FG,
                 font=self.fnt_bold).pack(anchor="w", padx=20, pady=(10, 2))
        self.txt_log = tk.Text(
            self.root, bg="#1a1a28", fg=FG, relief="flat",
            font=("Consolas", 8), height=8, wrap="word", state="disabled")
        self.txt_log.pack(fill="both", expand=True, padx=18, pady=2)

        # ── Bottom buttons ──
        btn_frame = tk.Frame(self.root, bg=BG)
        btn_frame.pack(fill="x", padx=18, pady=(6, 14))

        self.btn_undo = tk.Button(
            btn_frame, text="Desfazer", command=self._undo,
            bg="#3a3a50", fg=FG, activebackground="#4a4a60",
            activeforeground=FG, relief="flat",
            font=("Segoe UI", 10, "bold"), cursor="hand2", state="disabled",
            width=14)
        self.btn_undo.pack(side="left", ipady=8)

        self.btn_org = tk.Button(
            btn_frame, text="ORGANIZAR", command=self._organize,
            bg=ACCENT_BG, fg="white", activebackground=ACCENT_HV,
            activeforeground="white", relief="flat",
            font=("Segoe UI", 10, "bold"), cursor="hand2",
            width=14)
        self.btn_org.pack(side="right", ipady=8)

    # ── Helpers UI ──────────────────────────────────────────────
    def _log(self, text):
        self.txt_log.configure(state="normal")
        self.txt_log.insert("end", text + "\n")
        self.txt_log.see("end")
        self.txt_log.configure(state="disabled")

    def _set_folder(self, path):
        self.folder.set(path)
        self._scan()

    def _clear_preview(self):
        self.lst_preview.delete(0, tk.END)
        self.preview = []

    def _show_preview(self, counts):
        self._clear_preview()
        self.preview = []
        for folder_name in sorted(counts):
            cnt = counts[folder_name]
            line = f"  {cnt:>4} ficheiros  →  {folder_name}/"
            self.lst_preview.insert(tk.END, line)
            self.preview.append((folder_name, cnt))

    # ── Browser pasta ─────────────────────────────────────────
    def _browse(self):
        path = filedialog.askdirectory()
        if path:
            self._set_folder(path)

    # ── Scan folder → preview ─────────────────────────────────
    def _scan(self):
        self._clear_preview()
        path = self.folder.get()
        if not path or not os.path.isdir(path):
            return
        counts = defaultdict(int)
        for f in os.listdir(path):
            full = os.path.join(path, f)
            if os.path.isfile(full):
                ext = os.path.splitext(f)[1].lower()
                folder = ext_folder(ext)
                counts[folder] += 1
        self._show_preview(counts)
        total = sum(counts.values())
        self._log(f"A pasta contém {total} ficheiro(s) a organizar.")

    # ── Organizar (threaded) ──────────────────────────────────
    def _organize(self):
        path = self.folder.get()
        if not path or not os.path.isdir(path):
            messagebox.showwarning("Caminho inválido",
                                   "Seleciona uma pasta válida.")
            return
        if not self.preview:
            messagebox.showinfo("Nada a fazer",
                                "Nenhum ficheiro encontrado na pasta.")
            return

        ok = messagebox.askyesno(
            "Confirmar",
            "Vais mover os ficheiros para subpastas. Continuar?")
        if not ok:
            return

        self.moving = True
        self.undo_log.clear()
        self.btn_org.configure(state="disabled", bg=DISABLED)
        self.btn_browse.configure(state="disabled")
        self.progress_var.set(0)
        self.lbl_pct["text"] = "0%"
        self._log("─── Início ───")

        t = threading.Thread(target=self._do_move, args=(path,), daemon=True)
        t.start()

    # ── Thread de movimentação ────────────────────────────────
    def _do_move(self, path):
        # contar total antes
        total = sum(c for _, c in self.preview)
        done = 0

        for entry in os.listdir(path):
            if not self.moving:
                break
            src = os.path.join(path, entry)
            if not os.path.isfile(src):
                continue

            ext  = os.path.splitext(entry)[1].lower()
            dest_folder = ext_folder(ext)
            dest_dir = os.path.join(path, dest_folder)

            os.makedirs(dest_dir, exist_ok=True)
            final = unique_path(os.path.join(dest_dir, entry))

            try:
                shutil.move(src, final)
                self.undo_log.append((final, src))   # (para_onde, de_onde)
                self.root.after(0, self._log, f"> Movido: {entry}")
            except Exception as exc:
                self.root.after(0, self._log, f"! Erro em {entry}: {exc}")

            done += 1
            pct = round(done / total * 100) if total else 100
            self.root.after(0, self._progress_tick, pct)

        self.root.after(0, self._after_move)

    def _progress_tick(self, pct):
        self.progress_var.set(pct)
        self.lbl_pct["text"] = f"{pct}%"

    def _after_move(self):
        self.moving = False
        self.btn_org.configure(state="normal", bg=ACCENT_BG)
        self.btn_browse.configure(state="normal")
        self.progress_var.set(100)
        self.lbl_pct["text"] = "100%"
        self._log("─── Concluído ───")
        self.btn_undo.configure(state="normal" if self.undo_log else "disabled")
        self._scan()

    # ── Undo ──────────────────────────────────────────────────
    def _undo(self):
        if not self.undo_log:
            return
        ok = messagebox.askyesno(
            "Desfazer",
            f"Mover de volta {len(self.undo_log)} ficheiro(s)?")
        if not ok:
            return

        self.btn_undo.configure(state="disabled")
        for _src, _dst in self.undo_log:
            try:
                # garantir pasta de origem
                os.makedirs(os.path.dirname(_dst), exist_ok=True)
                shutil.move(_src, _dst)
                self._log(f"< Restituído: {os.path.basename(_src)}")
            except Exception as exc:
                self._log(f"! Erro a desfazer: {exc}")
        self.undo_log.clear()
        self._log("─── Undo concluído ───")
        self._scan()

    # ── Arranque ──────────────────────────────────────────────
    def run(self):
        self._log("Seleciona uma pasta para começar.")
        self.root.mainloop()


if __name__ == "__main__":
    App().run()
