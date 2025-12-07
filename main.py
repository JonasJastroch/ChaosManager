import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import threading
import datetime

class ChaosManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Chaos Manager - MiniHackathon 3.0")
        self.root.geometry("900x650")
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

        self.selected_folder = tk.StringVar()
        self.log_text = None
        self.preview_data = []

        self.create_widgets()

    def create_widgets(self):
        # Header
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill="x", padx=20, pady=20)

        lbl_title = ttk.Label(header_frame, text="Unordnung ➜ Ordnung", style="Header.TLabel")
        lbl_title.pack(side="left")

        lbl_subtitle = ttk.Label(header_frame, text="Entwickle etwas, um Chaos in Ordnung zu verwandeln.", font=("Segoe UI", 10, "italic"))
        lbl_subtitle.pack(side="left", padx=10, pady=(10, 0))

        select_frame = ttk.Labelframe(self.root, text=" 1. Chaos-Quelle wählen ", padding=15)
        select_frame.pack(fill="x", padx=20, pady=10)

        self.entry_path = tk.Entry(select_frame, textvariable=self.selected_folder, bg="#313244", fg="#ffffff", insertbackground="white", relief="flat", font=("Consolas", 10))
        self.entry_path.pack(side="left", fill="x", expand=True, padx=(0, 10))

        btn_browse = ttk.Button(select_frame, text="Ordner öffnen...", command=self.browse_folder)
        btn_browse.pack(side="right")

        action_frame = ttk.Labelframe(self.root, text=" 2. Aktionen ", padding=15)
        action_frame.pack(fill="x", padx=20, pady=10)

        btn_analyze = ttk.Button(action_frame, text="🔍 Analyse & Vorschau", command=self.run_analysis)
        btn_analyze.pack(side="left", padx=(0, 10))

        self.btn_execute = ttk.Button(action_frame, text="🚀 AUFRÄUMEN STARTEN", command=self.run_cleanup, state="disabled")
        self.btn_execute.pack(side="left")

        log_frame = ttk.Labelframe(self.root, text=" Protokoll & Vorschau ", padding=15)
        log_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.log_text = tk.Text(log_frame, bg="#181825", fg="#a6adc8", font=("Consolas", 10), relief="flat", state="disabled")
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.log_text.pack(side="left", fill="both", expand=True)

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

    def get_category(self, filename):
        name_lower = filename.lower()
        ext = os.path.splitext(filename)[1].lower()

        if "rechnung" in name_lower or "invoice" in name_lower or "beleg" in name_lower:
            return "Finanzen & Rechnungen"
        if "bewerbung" in name_lower or "cv" in name_lower or "lebenslauf" in name_lower:
            return "Karriere"
        if "screenshot" in name_lower:
            return "Screenshots"
        if "setup" in name_lower or "install" in name_lower:
            return "Installer"

        categories = {
            "Bilder": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".raw", ".tiff"],
            "Dokumente": [".pdf", ".docx", ".doc", ".txt", ".odt", ".rtf", ".pages"],
            "Tabellen & Daten": [".xlsx", ".xls", ".csv", ".numbers", ".json", ".xml"],
            "Präsentationen": [".pptx", ".ppt", ".key"],
            "Archive": [".zip", ".rar", ".7z", ".tar", ".gz"],
            "Audio": [".mp3", ".wav", ".aac", ".flac", ".ogg"],
            "Video": [".mp4", ".mov", ".avi", ".mkv", ".wmv"],
            "Programme": [".exe", ".msi", ".dmg", ".pkg", ".app", ".bat", ".sh"],
            "Code": [".py", ".js", ".html", ".css", ".java", ".cpp", ".php"]
        }

        for cat, extensions in categories.items():
            if ext in extensions:
                return cat

        return "Sonstiges"

    def run_analysis(self):
        path = self.selected_folder.get()
        if not path or not os.path.isdir(path):
            messagebox.showerror("Fehler", "Bitte wähle einen gültigen Ordner aus!")
            return

        self.log("--- Starte Analyse ---", "header")
        self.preview_data = [] # Reset

        threading.Thread(target=self._analyze_thread, args=(path,), daemon=True).start()

    def _analyze_thread(self, path):
        files_found = 0
        categories_found = {}

        try:
            self.root.after(0, lambda: self.log("Durchsuche auch Unterordner...", "info"))

            for root_dir, dirs, files in os.walk(path):
                dirs[:] = [d for d in dirs if not d.startswith('.')]

                for item in files:
                    if item.startswith('.'):
                        continue

                    full_path = os.path.join(root_dir, item)
                    category = self.get_category(item)
                    dest_folder = os.path.join(path, category)

                    if os.path.abspath(root_dir) == os.path.abspath(dest_folder):
                        continue

                    self.preview_data.append({
                        "file": item,
                        "source": full_path,
                        "category": category,
                        "dest_folder": dest_folder
                    })

                    categories_found[category] = categories_found.get(category, 0) + 1
                    files_found += 1

            if files_found == 0:
                self.root.after(0, lambda: self.log("Nichts zu tun! Alles sauber (oder leer).", "warning"))
                return

            self.root.after(0, lambda: self.log(f"{files_found} Dateien gefunden.", "success"))
            for cat, count in categories_found.items():
                self.root.after(0, lambda c=cat, co=count: self.log(f"  ➜ {co}x {c}", "info"))

            self.root.after(0, lambda: self.log("Analyse abgeschlossen. Drücke 'Aufräumen Starten' um fortzufahren.", "header"))
            self.root.after(0, lambda: self.btn_execute.config(state="normal"))

        except Exception as e:
            self.root.after(0, lambda: self.log(f"Fehler bei Analyse: {str(e)}", "error"))

    def run_cleanup(self):
        if not self.preview_data:
            return

        answer = messagebox.askyesno("Bestätigung", f"Möchtest du wirklich {len(self.preview_data)} Dateien verschieben?\n(Aktion kann nicht einfach rückgängig gemacht werden)")
        if not answer:
            return

        self.btn_execute.config(state="disabled")
        self.log("--- Starte Aufräumvorgang ---", "header")

        threading.Thread(target=self._cleanup_thread, daemon=True).start()

    def _cleanup_thread(self):
        moved_count = 0
        errors = 0
        base_path = self.selected_folder.get()

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

        self.root.after(0, lambda: self.log(f"{moved_count} Dateien verschoben. Starte Reinigung...", "success"))

        try:
            for root, dirs , files in os.walk(base_path, topdown=False):
                for name in dirs:
                    dir_to_check = os.path.join(root, name)
                    try:
                        os.rmdir(dir_to_check)
                    except OSError:
                        pass
        except Exception as e:
            self.root.after(0, lambda: self.log(f"Warnung bei Ordner-Bereinigung: {e}", "warning"))

        self.root.after(0, lambda: self.log("-" * 30, "info"))
        self.root.after(0, lambda: self.log(f"FERTIG! {moved_count} Dateien in Ordnung verwandelt.", "success"))
        if errors > 0:
            self.root.after(0, lambda: self.log(f"{errors} Fehler aufgetreten.", "warning"))

        # Reset
        self.preview_data = []

if __name__ == "__main__":
    root = tk.Tk()
    app = ChaosManagerApp(root)
    root.mainloop()