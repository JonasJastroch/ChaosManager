import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import threading
import datetime
import time
import requests  # <--- ADDED
import webbrowser  # <--- ADDED

# Import from your second file
from backend import get_all_files_list, query_llama_for_categories, query_llama_for_chunk


class ChaosManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Chaos Manager - MiniHackathon 3.0")
        self.root.geometry("1100x750")
        self.root.configure(bg="#1e1e2e")

        # --- Translations / Übersetzungen ---
        self.translations = {
            "title_header": {"Deutsch": "Unordnung ➜ Ordnung", "English": "Chaos ➜ Order"},
            "lbl_lang": {"Deutsch": "Sprache:", "English": "Language:"},
            "frame_select": {"Deutsch": " 1. Chaos-Ordner wählen ", "English": " 1. Select Chaos Folder "},
            "btn_browse": {"Deutsch": "Ordner öffnen...", "English": "Open Folder..."},
            "frame_prompt": {"Deutsch": " 2. KI-Prompt (Anweisung) ", "English": " 2. AI Prompt (Instruction) "},
            "frame_action": {"Deutsch": " 3. Aktionen & Status ", "English": " 3. Actions & Status "},
            "btn_analyze": {"Deutsch": "🔍 Analyse Starten", "English": "🔍 Start Analysis"},
            "btn_execute": {"Deutsch": "🚀 AUFRÄUMEN STARTEN", "English": "🚀 START CLEANUP"},
            "frame_log": {"Deutsch": " Protokoll ", "English": " Log "},
            "status_ready": {"Deutsch": "Bereit für Analyse...", "English": "Ready for analysis..."},
            "status_calculating": {"Deutsch": "Berechne Zeit...", "English": "Calculating time..."},
            "status_init": {"Deutsch": "Initialisiere KI...", "English": "Initializing AI..."},
            "status_phase1": {"Deutsch": "Phase 1: Architekt plant Struktur...",
                              "English": "Phase 1: Architect planning structure..."},
            "status_phase2": {"Deutsch": "Phase 2: Verarbeite Batch", "English": "Phase 2: Processing batch"},
            "status_done": {"Deutsch": "Analyse abgeschlossen.", "English": "Analysis complete."},
            "status_moving": {"Deutsch": "Verschiebe Dateien...", "English": "Moving files..."},
            "status_cleaning": {"Deutsch": "Bereinige leere Ordner...", "English": "Cleaning empty folders..."},
            "status_finished": {"Deutsch": "Vorgang abgeschlossen!", "English": "Process complete!"},
            "prompt_default": {"Deutsch": "Erstelle eine saubere, professionelle Ordnerstruktur.",
                               "English": "Create a clean, professional folder structure. Separate Work, Personal, University, and System files logically."},
            "msg_error_path": {"Deutsch": "Ungültiger Pfad!", "English": "Invalid path!"},
            "msg_confirm_title": {"Deutsch": "Starten?", "English": "Start?"},
            "msg_confirm_body": {"Deutsch": "Dateien verschieben?", "English": "Move files?"}
        }

        # --- Styles & Design ---
        self.style = ttk.Style()
        self.style.theme_use('clam')

        self.bg_color = "#1e1e2e"
        self.fg_color = "#cdd6f4"
        self.accent_color = "#89b4fa"
        self.success_color = "#a6e3a1"
        self.button_bg = "#313244"
        self.progress_bg = "#45475a"

        self.style.configure("TLabel", background=self.bg_color, foreground=self.fg_color, font=("Segoe UI", 11))
        self.style.configure("Header.TLabel", background=self.bg_color, foreground=self.accent_color,
                             font=("Segoe UI", 20, "bold"))
        self.style.configure("TButton", background=self.button_bg, foreground="#ffffff", borderwidth=0,
                             font=("Segoe UI", 10))
        self.style.map("TButton", background=[('active', self.accent_color)])
        self.style.configure("TFrame", background=self.bg_color)
        self.style.configure("TLabelframe", background=self.bg_color, foreground=self.fg_color)
        self.style.configure("TLabelframe.Label", background=self.bg_color, foreground=self.accent_color)
        self.style.configure("TCombobox", fieldbackground=self.button_bg, background=self.button_bg, foreground="black")
        self.style.configure("Custom.Horizontal.TProgressbar", troughcolor=self.progress_bg,
                             background=self.accent_color, thickness=10, borderwidth=0)
        self.style.configure("Action.TButton", font=("Segoe UI", 11))
        self.style.configure("Execute.TButton", background=self.button_bg, foreground="#ffffff", borderwidth=0,
                             font=("Segoe UI", 11, "bold"))

        # --- Variablen ---
        self.selected_folder = tk.StringVar()
        self.current_lang = tk.StringVar(value="Deutsch")
        self.preview_data = []
        self.entry_prompt = None
        self.progress_bar = None
        self.lbl_progress_text = None
        self.pulsing = False

        self.create_widgets()
        self.update_ui_language()

        # --- STARTUP CHECK ---
        # Checks if Ollama is running 1 second after app launch
        self.root.after(1000, self.check_ollama_status)

    def check_ollama_status(self):
        """Checks if Ollama is running on localhost."""
        try:
            # Simple ping to localhost:11434
            requests.get("http://localhost:11434", timeout=0.5)
            self.log("System Check: Ollama found. Ready.", "success")
        except requests.exceptions.ConnectionError:
            self.show_ollama_missing_dialog()

    def show_ollama_missing_dialog(self):
        """Shows the popup instructions."""
        dialog = tk.Toplevel(self.root)
        dialog.title("⚠️ AI Engine Missing")
        dialog.geometry("500x380")
        dialog.configure(bg="#1e1e2e")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Ollama Required!", font=("Segoe UI", 16, "bold"),
                  background="#1e1e2e", foreground="#f38ba8").pack(pady=10)

        msg = ("This tool uses a local AI to sort your files.\n"
               "You need to install 'Ollama' to continue.")
        ttk.Label(dialog, text=msg, justify="center", background="#1e1e2e", foreground="#cdd6f4").pack(pady=5)

        # Step 1: Download
        step1_frame = ttk.Frame(dialog)
        step1_frame.pack(pady=10, fill="x", padx=20)
        ttk.Label(step1_frame, text="1. Download Ollama:", width=20, font=("Segoe UI", 10, "bold")).pack(side="left")

        btn_dl = ttk.Button(step1_frame, text="⬇ Open Download Page",
                            command=lambda: webbrowser.open("https://ollama.com/download"))
        btn_dl.pack(side="left", padx=10)

        # Step 2: Command
        step2_frame = ttk.Frame(dialog)
        step2_frame.pack(pady=10, fill="x", padx=20)
        ttk.Label(step2_frame, text="2. Run Command:", width=20, font=("Segoe UI", 10, "bold")).pack(side="left")

        cmd_entry = tk.Entry(step2_frame, bg="#313244", fg="#a6e3a1", font=("Consolas", 11))
        cmd_entry.insert(0, "ollama pull llama3:8b")
        cmd_entry.pack(side="left", fill="x", expand=True, padx=5)

        # Info text
        ttk.Label(dialog, text="(Copy the command and paste it into PowerShell/CMD)",
                  background="#1e1e2e", foreground="#6c7086", font=("Segoe UI", 9)).pack(pady=0)

        # Retry button
        ttk.Button(dialog, text="I have installed it! (Retry)",
                   command=lambda: [dialog.destroy(), self.check_ollama_status()]).pack(side="bottom", pady=20)

    def get_text(self, key):
        lang = self.current_lang.get()
        return self.translations.get(key, {}).get(lang, "MISSING_TEXT")

    def create_widgets(self):
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill="x", padx=20, pady=20)
        self.lbl_title = ttk.Label(header_frame, text="", style="Header.TLabel")
        self.lbl_title.pack(side="left")

        lang_frame = ttk.Frame(header_frame)
        lang_frame.pack(side="right")
        self.lbl_lang = ttk.Label(lang_frame, text="Sprache:")
        self.lbl_lang.pack(side="left", padx=(0, 5))

        combo_lang = ttk.Combobox(lang_frame, textvariable=self.current_lang, values=["Deutsch", "English"],
                                  state="readonly", width=10)
        combo_lang.pack(side="left")
        combo_lang.bind("<<ComboboxSelected>>", self.on_language_change)

        self.select_frame = ttk.Labelframe(self.root, text="", padding=15)
        self.select_frame.pack(fill="x", padx=20, pady=10)
        self.entry_path = tk.Entry(self.select_frame, textvariable=self.selected_folder, bg="#313244", fg="#ffffff",
                                   insertbackground="white", relief="flat", font=("Consolas", 10))
        self.entry_path.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.btn_browse = ttk.Button(self.select_frame, text="", command=self.browse_folder)
        self.btn_browse.pack(side="right")

        self.prompt_frame = ttk.Labelframe(self.root, text="", padding=15)
        self.prompt_frame.pack(fill="x", padx=20, pady=10)
        self.entry_prompt = tk.Text(self.prompt_frame, bg="#313244", fg="#ffffff", insertbackground="white",
                                    relief="flat", font=("Consolas", 10), height=3, wrap="word")
        self.entry_prompt.insert("1.0", self.get_text("prompt_default"))
        self.entry_prompt.pack(fill="x", pady=5)

        self.action_frame = ttk.Labelframe(self.root, text="", padding=15)
        self.action_frame.pack(fill="x", padx=20, pady=10)
        btn_box = ttk.Frame(self.action_frame)
        btn_box.pack(fill="x", pady=(0, 10))
        self.btn_analyze = ttk.Button(btn_box, text="", command=self.run_analysis, style="Action.TButton")
        self.btn_analyze.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.btn_execute = ttk.Button(btn_box, text="", command=self.run_cleanup, state="disabled",
                                      style="Execute.TButton")
        self.btn_execute.pack(side="left", fill="x", expand=True)

        progress_box = ttk.Frame(self.action_frame)
        progress_box.pack(fill="x")
        self.lbl_progress_text = ttk.Label(progress_box, text="", font=("Consolas", 9))
        self.lbl_progress_text.pack(anchor="w", pady=(0, 2))
        self.progress_bar = ttk.Progressbar(progress_box, orient="horizontal", mode="determinate",
                                            style="Custom.Horizontal.TProgressbar")
        self.progress_bar.pack(fill="x")

        self.log_frame = ttk.Labelframe(self.root, text="", padding=15)
        self.log_frame.pack(fill="both", expand=True, padx=20, pady=10)
        self.log_text = tk.Text(self.log_frame, bg="#181825", fg="#a6adc8", font=("Consolas", 10), relief="flat",
                                state="disabled")
        scroll = ttk.Scrollbar(self.log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.log_text.pack(side="left", fill="both", expand=True)

        self.log_text.tag_config("success", foreground="#a6e3a1")
        self.log_text.tag_config("warning", foreground="#f9e2af")
        self.log_text.tag_config("error", foreground="#f38ba8")
        self.log_text.tag_config("info", foreground="#89b4fa")
        self.log_text.tag_config("arch", foreground="#cba6f7", font=("Consolas", 10, "bold"))

    def start_pulse_effect(self):
        self.pulsing = True
        self._animate_pulse(0)

    def stop_pulse_effect(self):
        self.pulsing = False
        self.style.configure("Execute.TButton", background=self.button_bg)

    def _animate_pulse(self, step):
        if not self.pulsing: return
        current_color = self.success_color if step % 2 == 0 else self.accent_color
        self.style.configure("Execute.TButton", background=current_color)
        self.root.after(800, lambda: self._animate_pulse(step + 1))

    def on_language_change(self, event=None):
        self.update_ui_language()
        new_prompt = self.get_text("prompt_default")
        self.entry_prompt.delete("1.0", tk.END)
        self.entry_prompt.insert("1.0", new_prompt)
        lang = self.current_lang.get()
        self.log(f"Sprache geändert auf: {lang}" if lang == "Deutsch" else f"Language changed to: {lang}", "info")

    def update_ui_language(self):
        self.lbl_title.config(text=self.get_text("title_header"))
        self.lbl_lang.config(text=self.get_text("lbl_lang"))
        self.select_frame.config(text=self.get_text("frame_select"))
        self.btn_browse.config(text=self.get_text("btn_browse"))
        self.prompt_frame.config(text=self.get_text("frame_prompt"))
        self.action_frame.config(text=self.get_text("frame_action"))
        self.btn_analyze.config(text=self.get_text("btn_analyze"))
        self.btn_execute.config(text=self.get_text("btn_execute"))
        self.log_frame.config(text=self.get_text("frame_log"))
        if self.progress_bar['value'] == 0:
            self.lbl_progress_text.config(text=self.get_text("status_ready"))

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
            lang = self.current_lang.get()
            msg = f"Ordner ausgewählt: {f}" if lang == "Deutsch" else f"Folder selected: {f}"
            self.log(msg, "info")

    def update_progress_ui(self, current_step, total_steps, start_time):
        if total_steps == 0: return
        percent = (current_step / total_steps) * 100
        self.progress_bar['value'] = percent
        elapsed_time = time.time() - start_time
        if current_step > 0:
            avg_time_per_step = elapsed_time / current_step
            remaining_steps = total_steps - current_step
            eta_seconds = int(avg_time_per_step * remaining_steps)
            minutes, seconds = divmod(eta_seconds, 60)
            if minutes > 60:
                hours, minutes = divmod(minutes, 60)
                time_str = f"{hours}h {minutes}m {seconds}s"
            elif minutes > 0:
                time_str = f"{minutes}m {seconds}s"
            else:
                time_str = f"{seconds}s"
            lang = self.current_lang.get()
            if lang == "Deutsch":
                status_text = f"Fortschritt: {int(percent)}% | Verbleibend: ~{time_str}"
            else:
                status_text = f"Progress: {int(percent)}% | Remaining: ~{time_str}"
        else:
            status_text = self.get_text("status_calculating")
        self.lbl_progress_text.config(text=status_text)

    def reset_progress_ui(self):
        self.progress_bar['value'] = 0
        lang = self.current_lang.get()
        text = "Bereit..." if lang == "Deutsch" else "Ready..."
        self.lbl_progress_text.config(text=text)

    def run_analysis(self):
        path = self.selected_folder.get()
        if not path or not os.path.isdir(path):
            messagebox.showerror("Fehler", self.get_text("msg_error_path"))
            return
        self.stop_pulse_effect()
        user_prompt = self.entry_prompt.get("1.0", "end-1c").strip()
        lang = self.current_lang.get()
        msg_start = "--- Starte Analyse ---" if lang == "Deutsch" else "--- Starting Analysis ---"
        self.log(msg_start, "info")
        self.preview_data = []
        self.btn_execute.config(state="disabled")
        self.progress_bar['value'] = 0
        self.lbl_progress_text.config(text=self.get_text("status_init"))
        threading.Thread(target=self._batch_analyze_thread, args=(path, user_prompt, lang), daemon=True).start()

    def _batch_analyze_thread(self, path, user_prompt, language):
        base_path = Path(path)
        start_time = time.time()
        all_files = get_all_files_list(path)
        total_files = len(all_files)
        if total_files == 0:
            msg = "Keine sortierbaren Dateien gefunden." if language == "Deutsch" else "No sortable files found."
            self.root.after(0, lambda: self.log(msg, "warning"))
            self.root.after(0, self.reset_progress_ui)
            return
        msg_arch = f"Phase 1: Architekt analysiert {total_files} Dateien..." if language == "Deutsch" else f"Phase 1: Architect analyzing {total_files} files..."
        self.root.after(0, lambda: self.log(msg_arch, "arch"))
        phase1_text = self.get_text("status_phase1")
        self.root.after(0, lambda: self.lbl_progress_text.config(text=phase1_text))
        self.root.after(0, lambda: self.progress_bar.configure(maximum=total_files + 10, value=0))

        master_categories = query_llama_for_categories(all_files, user_prompt, language)
        if not master_categories:
            master_categories = ["Dokumente", "Bilder", "Medien"] if language == "Deutsch" else ["Documents", "Images",
                                                                                                 "Media"]

        cat_str = ", ".join(master_categories)
        msg_plan = f"Architekt Plan: [{cat_str}]" if language == "Deutsch" else f"Architect Plan: [{cat_str}]"
        self.root.after(0, lambda: self.log(msg_plan, "arch"))

        BATCH_SIZE = 25
        chunks = [all_files[i:i + BATCH_SIZE] for i in range(0, total_files, BATCH_SIZE)]
        total_chunks = len(chunks)
        proposed_moves = []
        processed_files_set = set()
        phase2_start_time = time.time()
        status_p2_base = self.get_text("status_phase2")

        for i, chunk in enumerate(chunks):
            self.root.after(0,
                            lambda curr=i, tot=total_chunks, start=phase2_start_time: self.update_progress_ui(curr, tot,
                                                                                                              start))
            current_batch_size = len(chunk)
            msg_batch = f"{status_p2_base} {i + 1}/{total_chunks} ({current_batch_size} files)..."
            self.root.after(0, lambda m=msg_batch: self.log(m, "info"))
            response = query_llama_for_chunk(chunk, user_prompt, master_categories, language)

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
                                proposed_moves.append(
                                    {"file": full_source.name, "source": str(full_source), "category": folder_name,
                                     "dest_folder": str(dest_folder)})
                                processed_files_set.add(rel_source)
                                msg = f"{rel_source[:60].ljust(60)} -> {folder_name}"
                                self.root.after(0, lambda m=msg: self.log(m, "success"))
                    except Exception:
                        pass

        self.root.after(0, lambda: self.update_progress_ui(total_chunks, total_chunks, phase2_start_time))
        done_text = self.get_text("status_done")
        self.root.after(0, lambda: self.lbl_progress_text.config(text=done_text))
        self.preview_data = proposed_moves
        self.root.after(0, lambda: self.log("-" * 30, "info"))

        all_files_set = set(all_files)
        missing_files = all_files_set - processed_files_set
        if len(missing_files) == 0:
            msg_perfect = f"✅ PERFEKT: Alle {total_files} Dateien wurden zugeordnet!" if language == "Deutsch" else f"✅ PERFECT: All {total_files} files assigned!"
            self.root.after(0, lambda: self.log(msg_perfect, "success"))
        else:
            msg_miss = f"⚠️ {len(missing_files)} Dateien konnten nicht zugeordnet werden:" if language == "Deutsch" else f"⚠️ {len(missing_files)} files could not be assigned:"
            self.root.after(0, lambda: self.log(msg_miss, "warning"))
            for mf in list(missing_files)[:5]:
                self.root.after(0, lambda m=mf: self.log(f"   - {m}", "warning"))

        if len(self.preview_data) > 0:
            self.root.after(0, lambda: self.btn_execute.config(state="normal"))
            self.root.after(0, self.start_pulse_effect)
        self.root.after(0, self._stop_progress_bar)

    def _stop_progress_bar(self):
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.progress_bar.pack(fill="x")

    def run_cleanup(self):
        if not self.preview_data: return
        lang = self.current_lang.get()
        msg_title = self.get_text("msg_confirm_title")
        msg_body_base = self.get_text("msg_confirm_body")
        msg_body = f"{len(self.preview_data)} {msg_body_base}"
        if not messagebox.askyesno(msg_title, msg_body): return

        self.stop_pulse_effect()
        log_start = "--- Starte Verschiebung ---" if lang == "Deutsch" else "--- Starting Move ---"
        self.log(log_start, "info")
        self.btn_execute.config(state="disabled")
        threading.Thread(target=self._cleanup_thread, daemon=True).start()

    def _cleanup_thread(self):
        moved = 0
        total = len(self.preview_data)
        start_time = time.time()
        lang = self.current_lang.get()
        self.root.after(0, lambda: self.lbl_progress_text.config(text=self.get_text("status_moving")))

        for i, item in enumerate(self.preview_data):
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
                if i % 2 == 0:
                    self.root.after(0, lambda curr=i, tot=total, start=start_time: self.update_progress_ui(curr, tot,
                                                                                                           start))
            except Exception as e:
                self.root.after(0, lambda e=str(e): self.log(f"Error moving: {e}", "error"))

        self.remove_empty_folders(self.selected_folder.get())
        self.root.after(0, lambda: self.log("-" * 30, "info"))
        msg_fin = f"FERTIG! {moved} Dateien verschoben." if lang == "Deutsch" else f"DONE! {moved} files moved."
        self.root.after(0, lambda: self.log(msg_fin, "success"))
        self.root.after(0, lambda: self.progress_bar.configure(value=100))
        self.root.after(0, lambda: self.lbl_progress_text.config(text=self.get_text("status_finished")))
        self.preview_data = []
        msg_open = "Öffne Ordner..." if lang == "Deutsch" else "Opening folder..."
        self.root.after(0, lambda: self.log(msg_open, "info"))
        self.root.after(0, self.open_file_explorer)

    def remove_empty_folders(self, path):
        lang = self.current_lang.get()
        text = self.get_text("status_cleaning")
        self.root.after(0, lambda: self.lbl_progress_text.config(text=text))
        deleted_count = 0
        self.root.after(0, lambda: self.log(text, "info"))
        for root, dirs, files in os.walk(path, topdown=False):
            for name in dirs:
                full_path = os.path.join(root, name)
                try:
                    os.rmdir(full_path)
                    deleted_count += 1
                except OSError:
                    pass
        msg_clean = f"Bereinigung: {deleted_count} leere Ordner entfernt." if lang == "Deutsch" else f"Cleanup: {deleted_count} empty folders removed."
        self.root.after(0, lambda: self.log(msg_clean, "success"))

    def open_file_explorer(self):
        path = self.selected_folder.get()
        try:
            os.startfile(path)
        except Exception:
            pass


if __name__ == "__main__":
    root = tk.Tk()
    app = ChaosManagerApp(root)
    root.mainloop()