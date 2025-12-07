import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import threading
import datetime
# Import modified sorter
from llama_sorter import get_all_files_list, query_llama_for_categories, query_llama_for_chunk


class ChaosManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Chaos Manager - MiniHackathon 3.0 (LLaMA) - Ultimate Edition")
        self.root.geometry("1100x750")
        self.root.configure(bg="#1e1e2e")

        style = ttk.Style()
        style.theme_use('clam')

        bg_color = "#1e1e2e"
        fg_color = "#cdd6f4"
        accent_color = "#89b4fa"
        button_bg = "#313244"

        style.configure("TLabel", background=bg_color, foreground=fg_color, font=("Segoe UI", 11))
        style.configure("Header.TLabel", background=bg_color, foreground=accent_color, font=("Segoe UI", 20, "bold"))
        style.configure("TButton", background=button_bg, foreground="#ffffff", borderwidth=0, font=("Segoe UI", 10))
        style.map("TButton", background=[('active', accent_color)])
        style.configure("TFrame", background=bg_color)
        style.configure("TLabelframe", background=bg_color, foreground=fg_color)
        style.configure("TLabelframe.Label", background=bg_color, foreground=accent_color)
        style.configure("TCheckbutton", background=bg_color, foreground=fg_color)

        self.selected_folder = tk.StringVar()
        self.default_prompt = "Create a clean, professional folder structure. Separate Work, Personal, and System files."
        self.preview_data = []
        self.backup_path = None

        # Checkbox Variablen
        self.should_backup = tk.BooleanVar(value=True)
        self.should_delete_empty = tk.BooleanVar(value=True)  # NEU: Leere Ordner löschen

        self.btn_restore = None
        self.entry_prompt = None
        self.progress_bar = None

        self.create_widgets()

    def create_widgets(self):
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill="x", padx=20, pady=20)
        lbl_title = ttk.Label(header_frame, text="Unordnung ➜ Ordnung (Ultimate)", style="Header.TLabel")
        lbl_title.pack(side="left")

        select_frame = ttk.Labelframe(self.root, text=" 1. Chaos-Quelle wählen ", padding=15)
        select_frame.pack(fill="x", padx=20, pady=10)
        self.entry_path = tk.Entry(select_frame, textvariable=self.selected_folder, bg="#313244", fg="#ffffff",
                                   insertbackground="white", relief="flat", font=("Consolas", 10))
        self.entry_path.pack(side="left", fill="x", expand=True, padx=(0, 10))
        btn_browse = ttk.Button(select_frame, text="Ordner öffnen...", command=self.browse_folder)
        btn_browse.pack(side="right")

        prompt_frame = ttk.Labelframe(self.root, text=" 2. KI-Befehl ", padding=15)
        prompt_frame.pack(fill="x", padx=20, pady=10)
        self.entry_prompt = tk.Text(prompt_frame, bg="#313244", fg="#ffffff", insertbackground="white", relief="flat",
                                    font=("Consolas", 10), height=3, wrap="word")
        self.entry_prompt.insert("1.0", self.default_prompt)
        self.entry_prompt.pack(fill="x", pady=5)

        action_frame = ttk.Labelframe(self.root, text=" 3. Aktionen ", padding=15)
        action_frame.pack(fill="x", padx=20, pady=10)

        options_frame = ttk.Frame(action_frame)
        options_frame.pack(side="left", padx=(0, 20))

        chk_backup = ttk.Checkbutton(options_frame, text="Backup erstellen", variable=self.should_backup,
                                     style="TCheckbutton")
        chk_backup.pack(anchor="w")

        # NEU: Checkbox für leere Ordner
        chk_empty = ttk.Checkbutton(options_frame, text="Leere Quellordner löschen", variable=self.should_delete_empty,
                                    style="TCheckbutton")
        chk_empty.pack(anchor="w")

        self.btn_restore = ttk.Button(options_frame, text="Wiederherstellen", command=self.run_restore,
                                      state="disabled")
        self.btn_restore.pack(anchor="w", pady=(5, 0))

        btn_analyze = ttk.Button(action_frame, text="🔍 KI-Analyse Starten", command=self.run_analysis)
        btn_analyze.pack(side="left", padx=(0, 10))
        self.btn_execute = ttk.Button(action_frame, text="🚀 AUFRÄUMEN", command=self.run_cleanup, state="disabled")
        self.btn_execute.pack(side="left")

        self.progress_bar = ttk.Progressbar(action_frame, orient="horizontal", mode="determinate")

        log_frame = ttk.Labelframe(self.root, text=" Protokoll ", padding=15)
        log_frame.pack(fill="both", expand=True, padx=20, pady=10)
        self.log_text = tk.Text(log_frame, bg="#181825", fg="#a6adc8", font=("Consolas", 10), relief="flat",
                                state="disabled")
        scroll = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.log_text.pack(side="left", fill="both", expand=True)
        self.log_text.tag_config("success", foreground="#a6e3a1")
        self.log_text.tag_config("warning", foreground="#f9e2af")
        self.log_text.tag_config("error", foreground="#f38ba8")
        self.log_text.tag_config("info", foreground="#89b4fa")
        self.log_text.tag_config("arch", foreground="#cba6f7", font=("Consolas", 10, "bold"))

    def log(self, message, tag="info"):
        self.log_text.config(state="normal")
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{ts}] {message}\n", tag)
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def browse_folder(self):
        f = filedialog.askdirectory()
        if f:
            self.selected_folder.set(f)
            self.log(f"Ordner: {f}", "info")
            bp = Path(f) / "ChaosManager_Backup"
            if bp.is_dir() and any(bp.iterdir()):
                self.btn_restore.config(state="normal")

    def run_analysis(self):
        path = self.selected_folder.get()
        if not path or not os.path.isdir(path):
            messagebox.showerror("Fehler", "Ungültiger Pfad!")
            return

        user_prompt = self.entry_prompt.get("1.0", "end-1c").strip()
        if not user_prompt: user_prompt = self.default_prompt

        self.log("--- Starte Analyse ---", "info")
        self.preview_data = []
        self.btn_execute.config(state="disabled")
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=(15, 0))

        threading.Thread(target=self._batch_analyze_thread, args=(path, user_prompt), daemon=True).start()

    def _batch_analyze_thread(self, path, user_prompt):
        base_path = Path(path)

        # 1. Alle Dateien erfassen
        all_files = get_all_files_list(path)
        total_files = len(all_files)

        if total_files == 0:
            self.root.after(0, lambda: self.log("Keine sortierbaren Dateien gefunden.", "warning"))
            self.root.after(0, self._stop_progress_bar)
            return

        self.root.after(0, lambda: self.log(f"Phase 1: Der Architekt analysiert {total_files} Dateien...", "arch"))
        self.root.after(0, lambda: self.progress_bar.configure(maximum=total_files + 10, value=0))

        master_categories = query_llama_for_categories(all_files, user_prompt)

        if not master_categories:
            self.root.after(0, lambda: self.log("Konnte keine Kategorien ermitteln. Nutze Standard.", "warning"))
            master_categories = ["Dokumente", "Bilder", "Musik", "Video", "Sonstiges"]

        cat_str = ", ".join(master_categories)
        self.root.after(0, lambda c=cat_str: self.log(f"Architekt Plan: [{c}]", "arch"))

        # 3. PHASE 2: Der Arbeiter
        BATCH_SIZE = 25
        chunks = [all_files[i:i + BATCH_SIZE] for i in range(0, total_files, BATCH_SIZE)]

        self.root.after(0, lambda: self.progress_bar.configure(maximum=len(chunks), value=0))
        proposed_moves = []

        # Tracking set für processed files (relative Pfade)
        processed_files_set = set()

        for i, chunk in enumerate(chunks):
            self.root.after(0, lambda idx=i + 1, t=len(chunks): self.log(f"Phase 2: Verarbeite Batch {idx}/{t}...",
                                                                         "info"))

            response = query_llama_for_chunk(chunk, user_prompt, master_categories)

            if response.startswith("ERROR"):
                self.root.after(0, lambda r=response: self.log(r, "error"))
                continue

            for line in response.splitlines():
                line = line.strip()
                if ' -> ' in line:
                    try:
                        parts = [p.strip() for p in line.split(' -> ', 1)]
                        if len(parts) == 2:
                            rel_source = parts[0].strip('[]"\'')
                            folder_name = parts[1].strip('[]"\'')

                            full_source = base_path / rel_source

                            if full_source.exists() and full_source.is_file():
                                dest_folder = base_path / folder_name
                                proposed_moves.append({
                                    "file": full_source.name,
                                    "source": str(full_source),
                                    "category": folder_name,
                                    "dest_folder": str(dest_folder)
                                })
                                # Zum Set hinzufügen für späteren Vergleich
                                processed_files_set.add(rel_source)

                                msg = f"{rel_source[:60].ljust(60)} -> {folder_name}"
                                self.root.after(0, lambda m=msg: self.log(m, "success"))
                    except Exception:
                        pass

            self.root.after(0, lambda val=i + 1: self.progress_bar.configure(value=val))

        # 4. Abschluss & Fehlende Dateien Bericht
        self.preview_data = proposed_moves
        self.root.after(0, lambda: self.log("-" * 30, "info"))

        # Vergleich: Alle Dateien vs. Sortierte Dateien
        # Wir müssen normalisieren (Strings), um sicher zu sein
        all_files_set = set(all_files)
        # processed_files_set ist schon gefüllt

        missing_files = all_files_set - processed_files_set

        if len(missing_files) == 0:
            self.root.after(0, lambda: self.log(f"✅ PERFEKT: Alle {total_files} Dateien wurden zugeordnet!", "success"))
        else:
            self.root.after(0, lambda: self.log(f"⚠️ {len(missing_files)} Dateien konnten nicht zugeordnet werden:",
                                                "warning"))
            for mf in missing_files:
                self.root.after(0, lambda m=mf: self.log(f"   - FEHLT: {m}", "warning"))

        if len(self.preview_data) > 0:
            self.root.after(0, lambda: self.btn_execute.config(state="normal"))

        self.root.after(0, self._stop_progress_bar)

    def _stop_progress_bar(self):
        self.progress_bar.stop()
        self.progress_bar.pack_forget()

    # --- Cleanup / Backup / Restore ---
    def run_cleanup(self):
        if not self.preview_data: return
        if not messagebox.askyesno("Starten?", f"{len(self.preview_data)} Dateien verschieben?"): return

        if self.should_backup.get():
            threading.Thread(target=self._run_backup_and_clean, daemon=True).start()
        else:
            self.log("--- Starte Verschiebung ---", "info")
            self.btn_execute.config(state="disabled")
            threading.Thread(target=self._cleanup_thread, daemon=True).start()

    def _run_backup_and_clean(self):
        self.btn_execute.config(state="disabled")
        self.log("Erstelle Backup...", "info")
        self.run_backup()
        self.root.after(0, lambda: self.btn_restore.config(state="normal"))
        self.log("--- Starte Verschiebung ---", "info")
        self._cleanup_thread()

    def run_backup(self):
        s_dir = Path(self.selected_folder.get())
        b_path = s_dir / "ChaosManager_Backup"
        if b_path.exists(): shutil.rmtree(b_path)
        b_path.mkdir()

        count = 0
        for item in self.preview_data:
            try:
                src = Path(item['source'])
                rel = src.relative_to(s_dir)
                dst = b_path / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                count += 1
            except:
                pass
        self.root.after(0, lambda: self.log(f"Backup: {count} Dateien kopiert.", "success"))

    def _cleanup_thread(self):
        moved = 0
        for item in self.preview_data:
            try:
                if not os.path.exists(item['dest_folder']): os.makedirs(item['dest_folder'])
                dest = Path(item['dest_folder']) / item['file']
                base, ext = os.path.splitext(item['file'])
                c = 1
                while dest.exists():
                    dest = Path(item['dest_folder']) / f"{base}_{c}{ext}"
                    c += 1
                shutil.move(item['source'], dest)
                moved += 1
            except Exception as e:
                self.root.after(0, lambda e=str(e): self.log(f"Error moving: {e}", "error"))

        self.root.after(0, lambda: self.log(f"FERTIG: {moved} verschoben.", "success"))

        # NEU: Leere Ordner löschen
        if self.should_delete_empty.get():
            self.remove_empty_folders(self.selected_folder.get())

        self.preview_data = []

    def remove_empty_folders(self, path):
        """Löscht rekursiv leere Ordner (von unten nach oben)."""
        deleted_count = 0
        self.root.after(0, lambda: self.log("Suche nach leeren Ordnern...", "info"))

        # topdown=False ist wichtig! Erst Kinder löschen, dann Eltern.
        for root, dirs, files in os.walk(path, topdown=False):
            for name in dirs:
                full_path = os.path.join(root, name)
                # Ignoriere den Backup-Ordner!
                if "ChaosManager_Backup" in full_path:
                    continue

                try:
                    # Versuche zu löschen. Wenn nicht leer, wirft OSError (das ist gut so)
                    os.rmdir(full_path)
                    deleted_count += 1
                    # self.root.after(0, lambda p=full_path: self.log(f"Gelöscht: {p}", "warning"))
                except OSError:
                    pass  # Ordner nicht leer

        self.root.after(0, lambda: self.log(f"Bereinigung: {deleted_count} leere Ordner entfernt.", "success"))

    def run_restore(self):
        s_dir = Path(self.selected_folder.get())
        b_path = s_dir / "ChaosManager_Backup"
        if not b_path.exists(): return
        if not messagebox.askyesno("Restore", "Alles zurücksetzen?"): return
        self.log("Stelle wieder her...", "info")
        threading.Thread(target=self._restore_thread, args=(b_path, s_dir), daemon=True).start()

    def _restore_thread(self, b_path, s_dir):
        count = 0
        for f in b_path.rglob('*'):
            if f.is_file():
                rel = f.relative_to(b_path)
                dst = s_dir / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(f, dst)
                count += 1
        shutil.rmtree(b_path)
        self.root.after(0, lambda: self.log(f"Restore fertig: {count} Dateien.", "success"))
        self.root.after(0, lambda: self.btn_restore.config(state="disabled"))


if __name__ == "__main__":
    root = tk.Tk()
    app = ChaosManagerApp(root)
    root.mainloop()