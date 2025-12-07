import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import threading
import datetime
import time
# Import des LLaMA-Sortierers
from llama_sorter import get_all_files_list, query_llama_for_categories, query_llama_for_chunk


class ChaosManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Chaos Manager - MiniHackathon 3.0 (LLaMA) - Clean Edition")
        self.root.geometry("1100x750")
        self.root.configure(bg="#1e1e2e")

        # --- Styles & Design ---
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # Farben (Catppuccin Mocha Palette)
        self.bg_color = "#1e1e2e"
        self.fg_color = "#cdd6f4"
        self.accent_color = "#89b4fa"  # Blau
        self.success_color = "#a6e3a1"  # Grün
        self.button_bg = "#313244"
        self.progress_bg = "#45475a"

        # Standard Widgets
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

        # Custom Progress Bar Style
        self.style.configure("Custom.Horizontal.TProgressbar",
                             troughcolor=self.progress_bg,
                             background=self.accent_color,
                             thickness=10,
                             borderwidth=0)

        # Styles für spezielle Buttons
        self.style.configure("Action.TButton", font=("Segoe UI", 11))
        self.style.configure("Execute.TButton", background=self.button_bg, foreground="#ffffff", borderwidth=0,
                             font=("Segoe UI", 11, "bold"))

        # --- Variablen ---
        self.selected_folder = tk.StringVar()
        self.default_prompt = "Erstelle eine saubere, professionelle Ordnerstruktur. Trenne Arbeit, Privates, Studium und Systemdateien logisch voneinander."
        self.current_lang = tk.StringVar(value="Deutsch")

        self.prompts = {
            "Deutsch": self.default_prompt,
            "English": "Create a clean, professional folder structure. Separate Work, Personal, University, and System files logically."
        }

        self.preview_data = []
        self.entry_prompt = None

        self.progress_bar = None
        self.lbl_progress_text = None

        # Variable für die Animation
        self.pulsing = False

        self.create_widgets()

    def create_widgets(self):
        # Header
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill="x", padx=20, pady=20)

        lbl_title = ttk.Label(header_frame, text="Unordnung ➜ Ordnung", style="Header.TLabel")
        lbl_title.pack(side="left")

        # Sprachauswahl
        lang_frame = ttk.Frame(header_frame)
        lang_frame.pack(side="right")
        ttk.Label(lang_frame, text="Sprache:").pack(side="left", padx=(0, 5))
        combo_lang = ttk.Combobox(lang_frame, textvariable=self.current_lang, values=["Deutsch", "English"],
                                  state="readonly", width=10)
        combo_lang.pack(side="left")
        combo_lang.bind("<<ComboboxSelected>>", self.update_prompt_language)

        # Auswahlbereich
        select_frame = ttk.Labelframe(self.root, text=" 1. Chaos-Quelle wählen ", padding=15)
        select_frame.pack(fill="x", padx=20, pady=10)
        self.entry_path = tk.Entry(select_frame, textvariable=self.selected_folder, bg="#313244", fg="#ffffff",
                                   insertbackground="white", relief="flat", font=("Consolas", 10))
        self.entry_path.pack(side="left", fill="x", expand=True, padx=(0, 10))
        btn_browse = ttk.Button(select_frame, text="Ordner öffnen...", command=self.browse_folder)
        btn_browse.pack(side="right")

        # KI-Befehl
        prompt_frame = ttk.Labelframe(self.root, text=" 2. KI-Befehl ", padding=15)
        prompt_frame.pack(fill="x", padx=20, pady=10)
        self.entry_prompt = tk.Text(prompt_frame, bg="#313244", fg="#ffffff", insertbackground="white", relief="flat",
                                    font=("Consolas", 10), height=3, wrap="word")
        self.entry_prompt.insert("1.0", self.prompts["Deutsch"])
        self.entry_prompt.pack(fill="x", pady=5)

        # --- AKTIONEN BEREICH (Vereinfacht) ---
        action_frame = ttk.Labelframe(self.root, text=" 3. Aktionen & Status ", padding=15)
        action_frame.pack(fill="x", padx=20, pady=10)

        # Buttons Reihe
        btn_box = ttk.Frame(action_frame)
        btn_box.pack(fill="x", pady=(0, 10))

        # Analyse Button
        btn_analyze = ttk.Button(btn_box, text="🔍 Analyse Starten", command=self.run_analysis, style="Action.TButton")
        btn_analyze.pack(side="left", fill="x", expand=True, padx=(0, 10))

        # Execute Button (Pulsierend)
        self.btn_execute = ttk.Button(btn_box, text="🚀 AUFRÄUMEN STARTEN", command=self.run_cleanup, state="disabled",
                                      style="Execute.TButton")
        self.btn_execute.pack(side="left", fill="x", expand=True)

        # Progress Info
        progress_box = ttk.Frame(action_frame)
        progress_box.pack(fill="x")

        self.lbl_progress_text = ttk.Label(progress_box, text="Bereit für Analyse...", font=("Consolas", 9))
        self.lbl_progress_text.pack(anchor="w", pady=(0, 2))

        self.progress_bar = ttk.Progressbar(progress_box, orient="horizontal", mode="determinate",
                                            style="Custom.Horizontal.TProgressbar")
        self.progress_bar.pack(fill="x")

        # --- LOG BEREICH ---
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

    # --- Animations-Logik ---
    def start_pulse_effect(self):
        self.pulsing = True
        self._animate_pulse(0)

    def stop_pulse_effect(self):
        self.pulsing = False
        self.style.configure("Execute.TButton", background=self.button_bg)

    def _animate_pulse(self, step):
        if not self.pulsing: return
        # Wechsel zwischen Akzentfarbe (Blau) und Erfolg (Grün)
        current_color = self.success_color if step % 2 == 0 else self.accent_color
        self.style.configure("Execute.TButton", background=current_color)
        self.root.after(800, lambda: self._animate_pulse(step + 1))

    # --- Standard Funktionen ---
    def update_prompt_language(self, event=None):
        lang = self.current_lang.get()
        new_prompt = self.prompts.get(lang, self.prompts["Deutsch"])
        self.entry_prompt.delete("1.0", tk.END)
        self.entry_prompt.insert("1.0", new_prompt)
        self.log(f"Sprache geändert auf: {lang}", "info")

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
            self.log(f"Ordner ausgewählt: {f}", "info")

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
            lang = self.current_lang.get()
            status_text = "Berechne Zeit..." if lang == "Deutsch" else "Calculating time..."

        self.lbl_progress_text.config(text=status_text)

    def reset_progress_ui(self):
        self.progress_bar['value'] = 0
        lang = self.current_lang.get()
        text = "Bereit..." if lang == "Deutsch" else "Ready..."
        self.lbl_progress_text.config(text=text)

    # --- Analyse ---
    def run_analysis(self):
        path = self.selected_folder.get()
        if not path or not os.path.isdir(path):
            messagebox.showerror("Fehler", "Ungültiger Pfad!")
            return

        self.stop_pulse_effect()
        user_prompt = self.entry_prompt.get("1.0", "end-1c").strip()
        lang = self.current_lang.get()

        self.log(f"--- Starte Analyse ({lang}) ---", "info")
        self.preview_data = []
        self.btn_execute.config(state="disabled")
        self.progress_bar['value'] = 0

        loading_text = "Initialisiere KI..." if lang == "Deutsch" else "Initializing AI..."
        self.lbl_progress_text.config(text=loading_text)

        threading.Thread(target=self._batch_analyze_thread, args=(path, user_prompt, lang), daemon=True).start()

    def _batch_analyze_thread(self, path, user_prompt, language):
        base_path = Path(path)
        start_time = time.time()

        all_files = get_all_files_list(path)
        total_files = len(all_files)

        if total_files == 0:
            self.root.after(0, lambda: self.log("Keine sortierbaren Dateien gefunden.", "warning"))
            self.root.after(0, self.reset_progress_ui)
            return

        self.root.after(0, lambda: self.log(f"Phase 1: Architekt analysiert {total_files} Dateien...", "arch"))

        phase1_text = "Phase 1: Architekt plant Struktur..." if language == "Deutsch" else "Phase 1: Architect planning structure..."
        self.root.after(0, lambda: self.lbl_progress_text.config(text=phase1_text))
        self.root.after(0, lambda: self.progress_bar.configure(maximum=total_files + 10, value=0))

        master_categories = query_llama_for_categories(all_files, user_prompt, language)
        if not master_categories:
            master_categories = ["Dokumente", "Bilder", "Medien"]

        cat_str = ", ".join(master_categories)
        self.root.after(0, lambda c=cat_str: self.log(f"Architekt Plan: [{c}]", "arch"))

        BATCH_SIZE = 25
        chunks = [all_files[i:i + BATCH_SIZE] for i in range(0, total_files, BATCH_SIZE)]
        total_chunks = len(chunks)

        proposed_moves = []
        processed_files_set = set()
        phase2_start_time = time.time()

        for i, chunk in enumerate(chunks):
            self.root.after(0,
                            lambda curr=i, tot=total_chunks, start=phase2_start_time: self.update_progress_ui(curr, tot,
                                                                                                              start))
            current_batch_size = len(chunk)
            self.root.after(0, lambda idx=i + 1, t=total_chunks, s=current_batch_size: self.log(
                f"Phase 2: Verarbeite Batch {idx}/{t} ({s} Dateien)...", "info"))

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
                                proposed_moves.append({
                                    "file": full_source.name,
                                    "source": str(full_source),
                                    "category": folder_name,
                                    "dest_folder": str(dest_folder)
                                })
                                processed_files_set.add(rel_source)
                                msg = f"{rel_source[:60].ljust(60)} -> {folder_name}"
                                self.root.after(0, lambda m=msg: self.log(m, "success"))
                    except Exception:
                        pass

        self.root.after(0, lambda: self.update_progress_ui(total_chunks, total_chunks, phase2_start_time))
        done_text = "Analyse abgeschlossen." if language == "Deutsch" else "Analysis complete."
        self.root.after(0, lambda: self.lbl_progress_text.config(text=done_text))

        self.preview_data = proposed_moves
        self.root.after(0, lambda: self.log("-" * 30, "info"))

        all_files_set = set(all_files)
        missing_files = all_files_set - processed_files_set

        if len(missing_files) == 0:
            self.root.after(0, lambda: self.log(f"✅ PERFEKT: Alle {total_files} Dateien wurden zugeordnet!", "success"))
        else:
            self.root.after(0, lambda: self.log(f"⚠️ {len(missing_files)} Dateien konnten nicht zugeordnet werden:",
                                                "warning"))
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

        # --- Cleanup ---

    def run_cleanup(self):
        if not self.preview_data: return
        lang = self.current_lang.get()
        msg = f"{len(self.preview_data)} Dateien verschieben?" if lang == "Deutsch" else f"Move {len(self.preview_data)} files?"
        if not messagebox.askyesno("Starten?", msg): return

        self.stop_pulse_effect()

        self.log("--- Starte Verschiebung ---", "info")
        self.btn_execute.config(state="disabled")
        threading.Thread(target=self._cleanup_thread, daemon=True).start()

    def _cleanup_thread(self):
        moved = 0
        total = len(self.preview_data)
        start_time = time.time()

        lang = self.current_lang.get()
        text = "Verschiebe Dateien..." if lang == "Deutsch" else "Moving files..."
        self.root.after(0, lambda: self.lbl_progress_text.config(text=text))

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
        self.root.after(0, lambda: self.log(f"FERTIG! {moved} Dateien verschoben.", "success"))
        self.root.after(0, lambda: self.progress_bar.configure(value=100))

        done = "Vorgang abgeschlossen!" if lang == "Deutsch" else "Process complete!"
        self.root.after(0, lambda: self.lbl_progress_text.config(text=done))
        self.preview_data = []

    def remove_empty_folders(self, path):
        lang = self.current_lang.get()
        text = "Bereinige leere Ordner..." if lang == "Deutsch" else "Cleaning empty folders..."
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
        self.root.after(0, lambda: self.log(f"Bereinigung: {deleted_count} leere Ordner entfernt.", "success"))


if __name__ == "__main__":
    root = tk.Tk()
    app = ChaosManagerApp(root)
    root.mainloop()