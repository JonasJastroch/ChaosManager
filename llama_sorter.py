import requests
import json
from pathlib import Path
import os

# --- Configuration ---
OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3:8b"


def get_all_files_list(base_path):
    """
    Returns a list of all relative file paths (recursive),
    filtering out ignored types.
    """
    base_path = Path(base_path)
    file_list = []

    # ÄNDERUNG: .lnk und .url entfernt! Sie werden jetzt mit sortiert.
    IGNORED_SUFFIXES = ['.vpp.bak', '.bak', '.tmp', '.ds_store', '.ini']

    for item in base_path.rglob('*'):
        # Sicherheitscheck: Manchmal haben Ordner Endungen, wir wollen nur Dateien
        if item.is_file() and not item.name.startswith('.'):
            is_ignored_type = item.suffix.lower() in IGNORED_SUFFIXES
            if not is_ignored_type:
                # Relative path
                relative_path = str(item.relative_to(base_path))
                file_list.append(relative_path)

    return file_list


def query_llama_for_categories(all_files, user_prompt):
    """
    PHASE 1: THE ARCHITECT
    """
    sample_files = all_files[:500]
    files_str = "\n".join(sample_files)

    system_prompt = (
        "You are a senior information architect. Your goal is to analyze a list of filenames "
        "and create a clean, consistent set of top-level folders that covers ALL file types listed. "
        "Create broad but logical categories (e.g. 'Documentation', 'Finance', 'Images', 'Code', 'System'). "
        "Avoid creating too many folders (keep it between 5 and 15). "
        "Output ONLY the list of folder names, separated by commas. Nothing else."
    )

    prompt = (
        f"--- FILE LIST SAMPLE ---\n"
        f"{files_str}\n\n"
        f"--- USER GOAL ---\n"
        f"{user_prompt}\n\n"
        f"Based on the files above, define the perfect folder structure.\n"
        f"Output ONLY the folder names separated by commas (e.g. Folder A, Folder B, Folder C):"
    )

    print("DEBUG: Asking Architect for Global Folder Structure...")

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


def query_llama_for_chunk(file_chunk, user_prompt, defined_categories):
    """
    PHASE 2: THE WORKER
    """
    files_str = "\n".join(file_chunk)

    if defined_categories:
        cat_str = ", ".join(defined_categories)
        constraint = (
            f"--- ALLOWED DESTINATION FOLDERS ---\n"
            f"You must ONLY use folders from this list: [{cat_str}].\n"
            f"Do not invent new folder names. Pick the best fit from the list for each file.\n"
        )
    else:
        constraint = ""

    system_prompt = (
        "You are a file sorting robot. You must assign every single file to one of the provided destination folders. "
        "Strictly follow the format: '[FILE_PATH] -> [FOLDER_NAME]'. "
        "Do not include any intro or outro text."
    )

    prompt = (
        f"--- FILES TO SORT ---\n"
        f"{files_str}\n\n"
        f"{constraint}\n"
        f"--- INSTRUCTION ---\n"
        f"{user_prompt}\n"
        f"CRITICAL: Output a sorting line for EVERY file listed. Format: [File] -> [Folder]\n"
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