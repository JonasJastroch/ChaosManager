import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import threading
import datetime
# Import des LLaMA-Sortierers
from llama_sorter import get_file_structure_string, query_llama_for_sort


class ChaosManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Chaos Manager - MiniHackathon 3.0 (LLaMA) - Backup Edition")
        self.root.geometry("1100x700")  # Etwas breiter für die neuen Buttons
        self.root.configure(bg="#1e1e2e")

        # --- Styles ---
        style = ttk.Style()
        style.theme_use('clam')

        bg_color = "#1e1e2e"
        fg_color = "#cdd6f4"
        accent_color = "#89b4fa"
        button_bg = "#313244"  # button_bg korrigiert

        style.configure("TLabel", background=bg_color, foreground=fg_color, font=("Segoe UI", 11))
        style.configure("Header.TLabel", background=bg_color, foreground=accent_color, font=("Segoe UI", 20, "bold"))
        # button_bg korrigiert
        style.configure("TButton", background=button_bg, foreground="#ffffff", borderwidth=0, font=("Segoe UI", 10))
        style.map("TButton", background=[('active', accent_color)])
        style.configure("TFrame", background=bg_color)
        style.configure("TLabelframe", background=bg_color, foreground=fg_color)
        style.configure("TLabelframe.Label", background=bg_color, foreground=accent_color)

        style.configure("TCheckbutton", background=bg_color, foreground=fg_color)

        # --- Variablen ---
        self.selected_folder = tk.StringVar()
        # NEU: Zwingender Standard-Prompt
        self.default_prompt = self.default_prompt = "DU MUSST JEDE EINZELNE DATEI im Ordner, ohne Ausnahme, in einen neuen, passenden TOP-LEVEL Ordner verschieben. Finde für jede Datei eine sinnvolle Kategorie. CRITICAL: Überprüfe am Ende, dass JEDE Datei, die in der Eingabe unter 'CURRENT FILES' gelistet ist, eine entsprechende Zeile in deinen Vorschlägen hat. Gib alle Vorschläge ausschließlich in der geforderten Listenform zurück."
        # self.llama_prompt wurde entfernt und durch die Text-Widget-Referenz ersetzt
        self.log_text = None
        self.preview_data = []

        # Variablen für Backup/Restore
        self.backup_path = None
        self.should_backup = tk.BooleanVar(value=True)  # Checkbox-Zustand: Standardmäßig an
        self.btn_restore = None
        self.entry_prompt = None  # Referenz zum Text-Widget

        # Progress Bar
        self.progress_bar = None

        # --- Layout ---
        self.create_widgets()

    def create_widgets(self):
        # Header
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill="x", padx=20, pady=20)

        lbl_title = ttk.Label(header_frame, text="Unordnung ➜ Ordnung", style="Header.TLabel")
        lbl_title.pack(side="left")

        lbl_subtitle = ttk.Label(header_frame, text="Entwickle etwas, um Chaos in Ordnung zu verwandeln.",
                                 font=("Segoe UI", 10, "italic"))
        lbl_subtitle.pack(side="left", padx=10, pady=(10, 0))

        # Folder Selection Area
        select_frame = ttk.Labelframe(self.root, text=" 1. Chaos-Quelle wählen ", padding=15)
        select_frame.pack(fill="x", padx=20, pady=10)

        self.entry_path = tk.Entry(select_frame, textvariable=self.selected_folder, bg="#313244", fg="#ffffff",
                                   insertbackground="white", relief="flat", font=("Consolas", 10))
        self.entry_path.pack(side="left", fill="x", expand=True, padx=(0, 10))

        btn_browse = ttk.Button(select_frame, text="Ordner öffnen...", command=self.browse_folder)
        btn_browse.pack(side="right")

        # NEU: LLaMA Prompt Area mit Text-Widget
        prompt_frame = ttk.Labelframe(self.root, text=" 2. KI-Befehl ", padding=15)
        prompt_frame.pack(fill="x", padx=20, pady=10)

        lbl_prompt = ttk.Label(prompt_frame, text="Sortier-Befehl für die KI:")
        lbl_prompt.pack(fill="x")

        # NEU: Text Widget für den Prompt
        self.entry_prompt = tk.Text(prompt_frame, bg="#313244", fg="#ffffff", insertbackground="white",
                                    relief="flat", font=("Consolas", 10), height=3, wrap="word")
        self.entry_prompt.insert("1.0", self.default_prompt)  # Default Prompt einfügen
        self.entry_prompt.pack(fill="x", pady=(5, 5))

        # Action Area
        action_frame = ttk.Labelframe(self.root, text=" 3. Aktionen ", padding=15)
        action_frame.pack(fill="x", padx=20, pady=10)

        # Unter-Frame für Backup-Optionen
        options_frame = ttk.Frame(action_frame)
        options_frame.pack(side="left", padx=(0, 20))

        # Checkbox für Backup
        chk_backup = ttk.Checkbutton(options_frame, text="Backup der Originaldateien erstellen",
                                     variable=self.should_backup, style="TCheckbutton")
        chk_backup.pack(anchor="w")

        # Restore-Button (anfangs deaktiviert)
        self.btn_restore = ttk.Button(options_frame, text="🔄 LETZTE ORDNUNG WIEDERHERSTELLEN",
                                      command=self.run_restore, state="disabled")
        self.btn_restore.pack(anchor="w", pady=(5, 0))

        # Buttons für Analyse und Ausführung
        btn_analyze = ttk.Button(action_frame, text="🔍 Analyse & Vorschau", command=self.run_analysis)
        btn_analyze.pack(side="left", padx=(0, 10))

        self.btn_execute = ttk.Button(action_frame, text="🚀 AUFRÄUMEN STARTEN", command=self.run_cleanup,
                                      state="disabled")
        self.btn_execute.pack(side="left")

        # Fortschrittsanzeige hinzufügen
        self.progress_bar = ttk.Progressbar(action_frame, orient="horizontal", mode="indeterminate")

        # Log / Preview Area
        log_frame = ttk.Labelframe(self.root, text=" Protokoll & Vorschau ", padding=15)
        log_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Text Widget mit Scrollbar
        self.log_text = tk.Text(log_frame, bg="#181825", fg="#a6adc8", font=("Consolas", 10), relief="flat",
                                state="disabled")
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.log_text.pack(side="left", fill="both", expand=True)

        # Tags für Farben im Log
        self.log_text.tag_config("info", foreground="#89b4fa")
        self.log_text.tag_config("success", foreground="#a6e3a1")
        self.log_text.tag_config("warning", foreground="#f9e2af")
        self.log_text.tag_config("error", foreground="#f38ba8")
        self.log_text.tag_config("header", foreground="#cba6f7", font=("Consolas", 10, "bold"))

        self.log("Willkommen beim Chaos Manager. Bitte wähle einen Ordner.", "info")

    def log(self, message, tag="info"):
        self.log_text.config(state="normal")
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{timestamp}] {message}\n", tag)
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.selected_folder.set(folder)
            self.log(f"Ordner ausgewählt: {folder}", "info")
            self.btn_execute.config(state="disabled")

            backup_path = Path(folder) / "ChaosManager_Backup"
            if backup_path.is_dir() and any(backup_path.iterdir()):
                self.btn_restore.config(state="normal")
                self.log("Backup-Ordner gefunden. Wiederherstellung möglich.", "info")
            else:
                self.btn_restore.config(state="disabled")
                self.log("Kein gültiger Backup-Ordner gefunden.", "info")

    def _stop_progress_bar(self):
        """Stoppt und versteckt die Fortschrittsanzeige."""
        self.progress_bar.stop()
        self.progress_bar.pack_forget()

    # Run Analysis startet IMMER die LLaMA-Analyse
    def run_analysis(self):
        path = self.selected_folder.get()
        if not path or not os.path.isdir(path):
            messagebox.showerror("Fehler", "Bitte wähle einen gültigen Ordner aus!")
            return

        # NEU: Auslesen des Text-Widgets
        user_prompt = self.entry_prompt.get("1.0", "end-1c").strip()

        # Fallback auf den intelligenten Default-Prompt
        if not user_prompt:
            user_prompt = self.default_prompt

        self.log("--- Starte Analyse ---", "header")
        self.preview_data = []
        self.btn_execute.config(state="disabled")

        # Progress Bar starten und anzeigen
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=(15, 0))
        self.progress_bar.start()

        # Starte IMMER den LLaMA-Thread
        self.log(f"KI-Analyse aktiv mit Befehl: '{user_prompt[:40]}...' ", "info")
        threading.Thread(target=self._llama_analyze_thread, args=(path, user_prompt), daemon=True).start()

    # LLaMA-gesteuerte Analyse (rekursiv)
    def _llama_analyze_thread(self, path, user_prompt):

        base_path = Path(path)
        proposed_moves = []

        # ÄUSSERER TRY-BLOCK
        try:
            # 1. Dateistruktur abrufen
            file_structure = get_file_structure_string(path)
            self.root.after(0, lambda: self.log(f"Sende Dateistruktur (rekursiv) an KI...", "info"))

            if file_structure.endswith("ignored file types like .lnk)."):
                self.root.after(0, lambda: self.log("Der Ordner enthält keine Dateien, die nicht ignoriert werden.",
                                                    "warning"))
                return

            # 2. LLaMA abfragen
            llama_response = query_llama_for_sort(file_structure, user_prompt)

            # 3. Fehlerbehandlung
            if llama_response.startswith("ERROR:"):
                self.root.after(0, lambda: self.log(llama_response, "error"))
                self.root.after(0, lambda: self.btn_execute.config(state="disabled"))

            else:  # KI hat eine Antwort geliefert
                # 4. KI-Vorschlag verarbeiten und anzeigen
                self.root.after(0, lambda: self.log_text.config(state="normal"))
                self.root.after(0, lambda: self.log_text.delete('1.0', tk.END))
                self.root.after(0, lambda: self.log("--- LLaMA's Sortier-Vorschlag ---", "header"))

                valid_lines_count = 0
                for line in llama_response.splitlines():
                    line = line.strip().strip('*').strip('-').strip()
                    if ' -> ' in line:
                        # INNERE TRY/EXCEPT FÜR DAS PARSING
                        try:
                            parts = [p.strip() for p in line.split(' -> ', 1)]
                            if len(parts) != 2:
                                continue

                                # KORRIGIERT: Entferne eckige Klammern von Quelle und Ziel
                            relative_source_path = parts[0].strip('[]')
                            dest_folder_name = parts[1].strip('[]')

                            # Strip Quotes
                            if relative_source_path.startswith('"') or relative_source_path.startswith("'"):
                                relative_source_path = relative_source_path.strip('"').strip("'")

                            full_source_path = base_path / relative_source_path

                            if full_source_path.exists() and full_source_path.is_file():

                                final_dest_folder = base_path / dest_folder_name

                                proposed_moves.append({
                                    "file": full_source_path.name,
                                    "source": str(full_source_path),
                                    "category": dest_folder_name,
                                    "dest_folder": str(final_dest_folder)
                                })

                                # --- NEUE FORMATIERTE AUSGABE ---
                                # Breite 65 für bessere Übersicht
                                source_display = relative_source_path[:65].ljust(65)
                                formatted_message = f"{source_display} -> {dest_folder_name}"

                                valid_lines_count += 1
                                self.root.after(0, lambda msg=formatted_message: self.log(msg, "success"))
                                # --- ENDE NEUE AUSGABE ---

                            else:
                                self.root.after(0, lambda l=line: self.log(
                                    f"IGNORIERT (Quelle nicht gefunden/keine Datei): {l}", "warning"))
                        except Exception as e:
                            self.root.after(0, lambda l=line, err=str(e): self.log(
                                f"IGNORIERT (Formatfehler/Pfadproblem {err}): {l}", "error"))

                self.preview_data = proposed_moves
                files_to_move = len(self.preview_data)

                self.root.after(0, lambda: self.log("-" * 30, "info"))
                if files_to_move > 0:
                    self.root.after(0, lambda: self.log(
                        f"KI schlägt {files_to_move} Verschiebungen vor. Überprüfe die Liste und drücke 'Aufräumen STARTEN'.",
                        "header"))
                    self.root.after(0, lambda: self.btn_execute.config(state="normal"))
                else:
                    # LOGIK FÜR DIE BEGRÜNDUNG
                    if valid_lines_count == 0:
                        if "-> " not in llama_response:
                            reason = "Die KI hat geantwortet, aber keine Vorschläge im korrekten Format ('Datei -> Ordner') gefunden."
                        elif len(self.preview_data) == 0 and len(llama_response.splitlines()) > 0:
                            reason = f"Die KI hat Vorschläge gemacht, aber alle {len(llama_response.splitlines())} Zeilen wurden aufgrund ungültiger Pfade oder Dateitypen ignoriert. (Dateien in Unterordnern, die nicht existieren, werden ignoriert)."
                        else:
                            reason = "Unbekannter Fehler. Die KI hat geantwortet, aber keine umsetzbare Aktion vorgeschlagen."

                        self.root.after(0, lambda: self.log("KI hat keine gültigen Verschiebungen vorgeschlagen.",
                                                            "warning"))
                        self.root.after(0, lambda: self.log(f"Begründung: {reason}", "info"))
                        self.root.after(0, lambda: self.btn_execute.config(state="disabled"))


        except Exception as general_error:
            self.root.after(0, lambda: self.log(f"Schwerwiegender Fehler in Analyse-Thread: {str(general_error)}",
                                                "error"))

        finally:
            self.root.after(0, self._stop_progress_bar)

    # run_cleanup Methode
    def run_cleanup(self):
        if not self.preview_data:
            return

        answer = messagebox.askyesno("Bestätigung",
                                     f"Möchtest du wirklich {len(self.preview_data)} Dateien verschieben?\n(Aktion kann nicht einfach rückgängig gemacht werden)")
        if not answer:
            return

        # Backup-Prüfung
        if self.should_backup.get():
            self.log("Backup wird erstellt...", "info")
            backup_thread = threading.Thread(target=self.run_backup, daemon=True)
            backup_thread.start()
            backup_thread.join()
            self.btn_restore.config(state="normal")

        self.btn_execute.config(state="disabled")
        self.log("--- Starte Aufräumvorgang ---", "header")

        threading.Thread(target=self._cleanup_thread, daemon=True).start()

    # _cleanup_thread Methode
    def _cleanup_thread(self):
        moved_count = 0
        errors = 0

        for item in self.preview_data:
            try:
                if not os.path.exists(item['dest_folder']):
                    os.makedirs(item['dest_folder'])

                dest_path = os.path.join(item['dest_folder'], item['file'])
                base, ext = os.path.splitext(item['file'])
                counter = 1
                while os.path.exists(dest_path):
                    new_name = f"{base}_{counter}{ext}"
                    dest_path = os.path.join(item['dest_folder'], new_name)
                    counter += 1

                shutil.move(item['source'], dest_path)
                moved_count += 1

            except Exception as e:
                errors += 1
                self.root.after(0, lambda m=item['file'], err=str(e): self.log(f"Fehler bei {m}: {err}", "error"))

        self.root.after(0, lambda: self.log("-" * 30, "info"))
        self.root.after(0, lambda: self.log(f"FERTIG! {moved_count} Dateien in Ordnung verwandelt.", "success"))
        if errors > 0:
            self.root.after(0, lambda: self.log(f"{errors} Fehler aufgetreten.", "warning"))

        self.preview_data = []

    # Methode zum Kopieren der Dateien (Backup)
    def run_backup(self):
        source_dir = self.selected_folder.get()
        if not source_dir:
            return 0

        # Erstelle den dedizierten Backup-Ordner
        backup_base_path = Path(source_dir) / "ChaosManager_Backup"

        # Leere den alten Backup-Ordner, falls er existiert
        if backup_base_path.exists():
            shutil.rmtree(backup_base_path)

        backup_base_path.mkdir(exist_ok=True)
        self.backup_path = str(backup_base_path)

        copied_count = 0

        # Kopiere jede Datei aus der Vorschau an den relativen Pfad im Backup-Ordner
        for item in self.preview_data:
            try:
                source_file_path = Path(item['source'])

                # Relativer Pfad von der Quelle (wichtig, um die Unterordnerstruktur zu erhalten)
                relative_path = source_file_path.relative_to(source_dir)

                # Zieldatei im Backup-Ordner
                dest_file_path = backup_base_path / relative_path

                # Stelle sicher, dass der Ziel-Unterordner im Backup existiert
                dest_file_path.parent.mkdir(parents=True, exist_ok=True)

                shutil.copy2(source_file_path, dest_file_path)  # copy2 behält Metadaten
                copied_count += 1

            except Exception as e:
                self.root.after(0, lambda m=item['file'], err=str(e): self.log(f"FEHLER beim Backup von {m}: {err}",
                                                                               "error"))

        self.root.after(0,
                        lambda: self.log(f"Backup erfolgreich! {copied_count} Dateien in {self.backup_path} gesichert.",
                                         "success"))
        return copied_count

    # Methode zum Wiederherstellen der Originalordnung
    def run_restore(self):
        source_dir = self.selected_folder.get()
        backup_path = Path(source_dir) / "ChaosManager_Backup"

        if not backup_path.is_dir():
            messagebox.showerror("Fehler", "Kein Backup-Ordner gefunden!")
            return

        answer = messagebox.askyesno("Bestätigung",
                                     "Möchtest du wirklich alle Dateien aus dem Backup in den Quellordner zurückverschieben? Bereits sortierte Dateien werden überschrieben.")
        if not answer:
            return

        self.btn_restore.config(state="disabled")
        self.log("--- Starte Wiederherstellung ---", "header")

        threading.Thread(target=self._restore_thread, args=(backup_path, Path(source_dir)), daemon=True).start()

    def _restore_thread(self, backup_path, source_dir):
        restored_count = 0
        errors = 0

        try:
            # Iteriere über alle Dateien im Backup-Ordner (rekursiv)
            for item in backup_path.rglob('*'):
                if item.is_file():
                    # Relativer Pfad zum Backup-Ordner
                    relative_path = item.relative_to(backup_path)

                    # Zielpfad im Quellordner
                    dest_path = source_dir / relative_path

                    # Stelle sicher, dass der Unterordner im Ziel existiert
                    dest_path.parent.mkdir(parents=True, exist_ok=True)

                    # Verschiebe die Datei zurück (überschreibt existierende Dateien!)
                    shutil.move(item, dest_path)
                    restored_count += 1

            # Lösche den leeren Backup-Ordner, nachdem alles verschoben wurde
            shutil.rmtree(backup_path)

            self.root.after(0, lambda: self.log(
                f"WIEDERHERSTELLUNG ERFOLGREICH! {restored_count} Dateien zurückverschoben.", "success"))
            self.root.after(0, lambda: self.btn_execute.config(state="disabled"))

        except Exception as e:
            errors += 1
            self.root.after(0, lambda err=str(e): self.log(f"FEHLER bei Wiederherstellung: {err}", "error"))

        self.root.after(0, lambda: self.btn_restore.config(state="disabled"))


if __name__ == "__main__":
    root = tk.Tk()
    app = ChaosManagerApp(root)
    root.mainloop()