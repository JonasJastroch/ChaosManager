import requests
import json
from pathlib import Path
import os

# --- Configuration ---
OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3:8b"

# --- PROMPT TEMPLATES ---
PROMPTS = {
    "DE": {
        "arch_sys": (
            "Du bist ein strikter Informationsarchitekt. Dein Ziel: Reduziere Chaos durch wenige, große Ordner.\n"
            "REGELN:\n"
            "1. Fasse Verknüpfungen (.lnk, .url) und ausführbare Dateien (.exe) IMMER in einem Ordner namens 'Anwendungen' oder 'System' zusammen.\n"
            "2. Erstelle NIEMALS einen Ordner für nur 1-2 Dateien.\n"
            "3. Nutze breite Kategorien: Statt 'Rechnungen', 'Verträge', 'Briefe' nutze einfach 'Dokumente'.\n"
            "4. Nutze 'Bilder' für alle Fotos, Screenshots und Grafiken.\n"
            "5. Erstelle maximal 8 Kategorien.\n"
            "Gib NUR die Liste der Ordnernamen aus, getrennt durch Kommas."
        ),
        "arch_user": "Analysiere diese Dateien und definiere max. 8 breite Kategorien in DEUTSCH.\nAusgabe NUR die Ordnernamen (Kommagetrennt):",

        "worker_sys": "Du bist ein Sortier-Roboter. Ordne Dateien den vorgegebenen Kategorien zu.",
        "worker_constraint": (
            "--- ERLAUBTE KATEGORIEN ---\n"
            "Du darfst NUR in diese Ordner sortieren: [{cat_str}].\n"
            "REGEL: Alle .lnk, .url und .exe Dateien gehören in den Ordner 'Anwendungen' oder 'System' (je nachdem was in der Liste ist).\n"
            "Erfinde KEINE neuen Namen."
        ),
        "worker_user": "CRITICAL: Output a sorting line for EVERY file listed. Format: [File] -> [Folder]"
    },
    "EN": {
        "arch_sys": (
            "You are a strict information architect. Your goal: Reduce chaos using few, broad folders.\n"
            "RULES:\n"
            "1. ALWAYS group shortcuts (.lnk, .url) and executables (.exe) into a folder named 'Apps' or 'System'.\n"
            "2. NEVER create a folder for just 1-2 files.\n"
            "3. Use broad categories: Instead of 'Invoices', 'Letters', use just 'Documents'.\n"
            "4. Use 'Images' for all photos, screenshots, and graphics.\n"
            "5. Create a maximum of 8 categories.\n"
            "Output ONLY the list of folder names, separated by commas."
        ),
        "arch_user": "Analyze these files and define max 8 broad categories in ENGLISH.\nOutput ONLY folder names (comma separated):",

        "worker_sys": "You are a sorting robot. Assign files to the provided categories.",
        "worker_constraint": (
            "--- ALLOWED CATEGORIES ---\n"
            "You must ONLY sort into these folders: [{cat_str}].\n"
            "RULE: All .lnk, .url, and .exe files go into 'Apps' or 'System' (whichever exists in the list).\n"
            "Do NOT invent new names."
        ),
        "worker_user": "CRITICAL: Output a sorting line for EVERY file listed. Format: [File] -> [Folder]"
    }
}


def get_all_files_list(base_path):
    """Returns a list of all relative file paths (recursive), ignoring specific system folders."""
    base_path = Path(base_path)
    file_list = []

    # Dateiendungen, die ignoriert werden sollen (temp files etc.)
    # WICHTIG: .lnk und .url sind HIER NICHT enthalten, sie werden also sortiert!
    IGNORED_SUFFIXES = ['.vpp.bak', '.bak', '.tmp', '.ds_store', '.ini']

    # Ordner, die komplett ignoriert werden
    IGNORED_FOLDERS = ['$RECYCLE.BIN', 'System Volume Information', '.git', '.idea']

    for item in base_path.rglob('*'):
        # Check ob der Pfad einen ignorierten Ordner enthält
        if any(ignored in str(item) for ignored in IGNORED_FOLDERS):
            continue

        if item.is_file() and not item.name.startswith('.'):
            is_ignored_type = item.suffix.lower() in IGNORED_SUFFIXES
            if not is_ignored_type:
                relative_path = str(item.relative_to(base_path))
                file_list.append(relative_path)
    return file_list


def query_llama_for_categories(all_files, user_prompt, language="DE"):
    """PHASE 1: THE ARCHITECT"""
    # Wir geben dem Architekten mehr Dateien (bis zu 800), damit er Muster besser erkennt
    sample_files = all_files[:800]
    files_str = "\n".join(sample_files)

    lang_key = "DE" if language == "Deutsch" else "EN"
    p = PROMPTS[lang_key]

    prompt = (
        f"--- FILE LIST (SAMPLE) ---\n"
        f"{files_str}\n\n"
        f"--- USER GOAL ---\n"
        f"{user_prompt}\n\n"
        f"{p['arch_user']}"
    )

    data = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "system": p["arch_sys"],
        "stream": False,
        "options": {"temperature": 0.1, "num_predict": 256}
    }

    try:
        response = requests.post(OLLAMA_API_URL, json=data, timeout=120)
        response.raise_for_status()
        raw_text = response.json().get('response', '').strip()
        # Bereinigung der KI-Antwort
        raw_text = raw_text.replace('[', '').replace(']', '').replace('\n', ',').replace('.', '')
        categories = [cat.strip() for cat in raw_text.split(',') if cat.strip()]

        # Fallback: Sicherstellen, dass es einen Ordner für "Restmüll" und "System" gibt
        fallback_cat = "Sonstiges" if language == "Deutsch" else "Misc"
        system_cat = "System"

        if fallback_cat not in categories:
            categories.append(fallback_cat)
        # Wenn kein passender System-Ordner da ist, fügen wir ihn hinzu
        if system_cat not in categories and "Anwendungen" not in categories and "Apps" not in categories:
            categories.append(system_cat)

        return categories
    except Exception as e:
        print(f"Architect Error: {e}")
        return []


def query_llama_for_chunk(file_chunk, user_prompt, defined_categories, language="DE"):
    """PHASE 2: THE WORKER"""
    files_str = "\n".join(file_chunk)
    lang_key = "DE" if language == "Deutsch" else "EN"
    p = PROMPTS[lang_key]

    if defined_categories:
        cat_str = ", ".join(defined_categories)
        constraint = p["worker_constraint"].format(cat_str=cat_str)
    else:
        constraint = ""

    prompt = (
        f"--- FILES TO SORT ---\n"
        f"{files_str}\n\n"
        f"{constraint}\n"
        f"--- INSTRUCTION ---\n"
        f"{user_prompt}\n"
        f"{p['worker_user']}\n"
    )

    data = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "system": p["worker_sys"],
        "stream": False,
        # Temp 0.0 zwingt die KI, exakt den Anweisungen zu folgen ohne Kreativität
        "options": {"temperature": 0.0, "num_predict": 1024}
    }

    try:
        response = requests.post(OLLAMA_API_URL, json=data, timeout=120)
        response.raise_for_status()
        return response.json().get('response', '').strip()
    except Exception as e:
        return f"ERROR: {e}"