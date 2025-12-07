import requests
import json
from pathlib import Path
import os
import time

# --- Configuration ---
OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3:8b"


def get_file_structure_string(base_path):
    """
    Generiert eine lesbare Repräsentation der Dateistruktur,
    rekursiv und filtert nicht benötigte Dateitypen.
    """
    base_path = Path(base_path)
    file_count = 0
    structure = []

    # Ignoriert: Verknüpfungen, Backup-Dateien, temporäre Dateien
    IGNORED_SUFFIXES = ['.lnk', '.url', '.vpp.bak', '.bak', '.tmp', '.ds_store']

    # Durchsuche den Basis-Pfad und alle Unterordner rekursiv
    for item in base_path.rglob('*'):

        is_ignored_type = item.suffix.lower() in IGNORED_SUFFIXES

        # Nur Dateien, keine versteckten Dateien und keine ignorierten Endungen
        if item.is_file() and not item.name.startswith('.') and not is_ignored_type:
            # Relativer Pfad zur Basis
            relative_path = str(item.relative_to(base_path))
            structure.append(relative_path)
            file_count += 1

    if file_count == 0:
        return "The folder and its subfolders are empty of files (or only contain ignored file types like .lnk)."

    structure_str = "\n".join(structure)

    return f"CURRENT FILES (TOTAL: {file_count}):\n{structure_str}"


def query_llama_for_sort(file_structure_str, user_prompt):
    """Sends the file structure and user prompt to the Ollama API."""

    system_prompt = (
        "You are an intelligent file sorter. Your task is to propose an ideal, new folder "
        "structure for the given files. NOTE: The files listed may include their full relative path "
        "(e.g., 'Subfolder/file.pdf'). "
        "Your proposed moves MUST use the FULL RELATIVE PATH as the source, "
        "and ONLY a NEW FOLDER NAME as the destination. "
        "The destination MUST be a top-level folder name within the root. "
        "Output ONLY a simple, markdown-formatted list of proposed moves. Each item must be formatted as: "
        "'[FULL_RELATIVE_PATH_TO_FILE] -> [PROPOSED_TOP_LEVEL_FOLDER_NAME]'. "
        "Do not include any explanation, intro, or extra text. Only list files that need to be moved."
    )

    prompt = (
        f"--- CURRENT FILES AND FOLDERS ---\n"
        f"{file_structure_str}\n\n"
        f"--- SORTING INSTRUCTION ---\n"
        f"{user_prompt}\n\n"
        f"Generate the proposed moves list:"
    )

    data = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "system": system_prompt,
        "stream": False,
        "options": {
            "temperature": 0.2
        }
    }

    try:
        response = requests.post(OLLAMA_API_URL, json=data, timeout=120)
        response.raise_for_status()

        result = response.json()
        return result.get('response', '').strip()

    except requests.exceptions.ConnectionError:
        return "ERROR: Could not connect to Ollama API. Is Ollama running and the port 11434 open?"
    except requests.exceptions.Timeout:
        return "ERROR: Ollama API request timed out."
    except requests.exceptions.RequestException as e:
        return f"ERROR: API request failed: {e}"