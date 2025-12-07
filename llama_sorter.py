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
        "arch_sys": "Du bist ein erfahrener Informationsarchitekt. Deine Aufgabe ist es, eine Liste von Dateinamen zu analysieren und eine saubere Ordnerstruktur zu erstellen. Erstelle logische Kategorien in DEUTSCHER SPRACHE (z.B. 'Dokumente', 'Finanzen', 'Bilder'). Gib NUR die Liste der Ordnernamen aus, getrennt durch Kommas.",
        "arch_user": "Definiere basierend auf den Dateien die perfekte Ordnerstruktur in DEUTSCH.\nAusgabe NUR die Ordnernamen getrennt durch Kommas:",
        "worker_sys": "Du bist ein Datei-Sortier-Roboter. Du musst jede Datei einem der vorgegebenen Zielordner zuweisen.",
        "worker_constraint": "--- ERLAUBTE ZIELORDNER ---\nDu darfst NUR Ordner aus dieser Liste verwenden: [{cat_str}].\nErfinde keine neuen Namen.",
        "worker_user": "CRITICAL: Output a sorting line for EVERY file listed. Format: [File] -> [Folder]"
    },
    "EN": {
        "arch_sys": "You are an experienced information architect. Your task is to analyze a list of filenames and create a clean folder structure. Create logical categories in ENGLISH (e.g., 'Documents', 'Finance', 'Images'). Output ONLY the list of folder names, separated by commas.",
        "arch_user": "Define the perfect folder structure in ENGLISH based on the files.\nOutput ONLY the folder names separated by commas:",
        "worker_sys": "You are a file sorting robot. You must assign every single file to one of the provided destination folders.",
        "worker_constraint": "--- ALLOWED DESTINATION FOLDERS ---\nYou must ONLY use folders from this list: [{cat_str}].\nDo not invent new folder names.",
        "worker_user": "CRITICAL: Output a sorting line for EVERY file listed. Format: [File] -> [Folder]"
    }
}


def get_all_files_list(base_path):
    """Returns a list of all relative file paths (recursive)."""
    base_path = Path(base_path)
    file_list = []
    IGNORED_SUFFIXES = ['.vpp.bak', '.bak', '.tmp', '.ds_store', '.ini']

    for item in base_path.rglob('*'):
        if item.is_file() and not item.name.startswith('.'):
            is_ignored_type = item.suffix.lower() in IGNORED_SUFFIXES
            if not is_ignored_type:
                relative_path = str(item.relative_to(base_path))
                file_list.append(relative_path)
    return file_list


def query_llama_for_categories(all_files, user_prompt, language="DE"):
    """
    PHASE 1: THE ARCHITECT
    """
    sample_files = all_files[:500]
    files_str = "\n".join(sample_files)

    # Wähle die Prompts basierend auf der Sprache
    lang_key = "DE" if language == "Deutsch" else "EN"
    p = PROMPTS[lang_key]

    system_prompt = p["arch_sys"]

    prompt = (
        f"--- FILE LIST (SAMPLE) ---\n"
        f"{files_str}\n\n"
        f"--- USER GOAL ---\n"
        f"{user_prompt}\n\n"
        f"{p['arch_user']}"
    )

    print(f"DEBUG: Asking Architect ({lang_key}) for Global Folder Structure...")

    data = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "system": system_prompt,
        "stream": False,
        "options": {"temperature": 0.2, "num_predict": 256}
    }

    try:
        response = requests.post(OLLAMA_API_URL, json=data, timeout=120)
        response.raise_for_status()
        raw_text = response.json().get('response', '').strip()
        raw_text = raw_text.replace('[', '').replace(']', '').replace('\n', ',')
        categories = [cat.strip() for cat in raw_text.split(',') if cat.strip()]
        return categories
    except Exception as e:
        print(f"Architect Error: {e}")
        return []


def query_llama_for_chunk(file_chunk, user_prompt, defined_categories, language="DE"):
    """
    PHASE 2: THE WORKER
    """
    files_str = "\n".join(file_chunk)
    lang_key = "DE" if language == "Deutsch" else "EN"
    p = PROMPTS[lang_key]

    if defined_categories:
        cat_str = ", ".join(defined_categories)
        # Formatiere den Constraint-String mit den Kategorien
        constraint = p["worker_constraint"].format(cat_str=cat_str)
    else:
        constraint = ""

    system_prompt = p["worker_sys"]

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
        "system": system_prompt,
        "stream": False,
        "options": {"temperature": 0.1, "num_predict": 1024}
    }

    try:
        response = requests.post(OLLAMA_API_URL, json=data, timeout=120)
        response.raise_for_status()
        return response.json().get('response', '').strip()
    except Exception as e:
        return f"ERROR: {e}"