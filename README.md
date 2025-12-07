# Chaos Manager 📂🧠

### KI-gestützte Dateisortierung für Windows

Der **Chaos Manager** ist ein innovatives Tool, das mithilfe von lokalen Large Language Models (LLaMA/Llama 3) Ihre ungeordneten Downloads, Desktops oder andere Verzeichnisse vollautomatisch in eine saubere, professionelle und logische Ordnerstruktur überführt.

---

## 💻 Systemanforderungen

* **Betriebssystem:** Windows 10/11 (Die .exe ist nur für Windows kompiliert.)
* **KI-Backend:** [Ollama](https://ollama.com/download/windows) (Muss installiert und ausgeführt werden, um die KI-Modelle bereitzustellen.)

---

## ⚠️ Wichtige Sicherheitshinweise (Windows Defender)

Da der **Chaos Manager** eine neu erstellte, unsignierte `.exe`-Datei ist, die auf Ihr Dateisystem zugreift, kann der **Windows Defender SmartScreen** beim ersten Start eine Warnung auslösen.

> 🔒 **Meldung:** „Windows hat Ihren PC geschützt“

Dies ist ein **Normalverhalten** für neue Programme, die das Dateisystem bearbeiten. Das Projekt ist Open Source (Quellcode einsehbar) und sicher.

### Wie Sie die Warnung umgehen:

1.  Klicken Sie im blauen Warnfenster auf **"Weitere Informationen"**.
2.  Klicken Sie anschließend auf **"Trotzdem ausführen"**.

---

## 🚀 Installation & Start

Sie haben zwei Möglichkeiten, den Chaos Manager zu verwenden:

### 1. Einfache Nutzung (.exe Binary) – Empfohlen

Laden Sie die vorkompilierte ausführbare Datei herunter:

1.  Gehen Sie zu den **[GitHub Releases](https://github.com/JonasJastroch/ChaosManager/releases/tag/v1.0)** des Projekts.
2.  Laden Sie die `.exe`-Datei unter **Assets** herunter.
3.  Führen Sie die Datei aus (bestätigen Sie ggf. die Windows Defender Warnung wie oben beschrieben).

### 2. Nutzung über Quellcode (Für Entwickler)

Wenn Sie die `.exe` vermeiden möchten oder den Quellcode selbst ausführen wollen:

#### Schritt 1: Das KI-Backend vorbereiten (Ollama)

Bevor Sie das Skript ausführen, müssen Sie Ollama installieren und das notwendige Sprachmodell (`llama3:8b`) herunterladen:

1.  Stellen Sie sicher, dass **[Ollama für Windows](https://ollama.com/download/windows)** installiert ist und läuft.
2.  Öffnen Sie **PowerShell** und führen Sie folgenden Befehl aus, um das Llama 3 Modell zu laden:

    ```powershell
    ollama pull llama3:8b
    ```

#### Schritt 2: Projekt klonen und ausführen

1.  Klonen Sie das Repository lokal:

    ```bash
    git clone [https://github.com/JonasJastroch/ChaosManager.git](https://github.com/JonasJastroch/ChaosManager.git)
    cd ChaosManager
    ```

2.  Stellen Sie sicher, dass Sie alle Python-Abhängigkeiten installiert haben (falls erforderlich, mittels `pip install -r requirements.txt`).
3.  Führen Sie die Hauptdatei aus:

    ```bash
    python main.py
    ```

---

## 📺 Demo Video

Sehen Sie den Chaos Manager in Aktion:

[https://www.youtube.com/watch?v=40O2LQ0ObOE](https://www.youtube.com/watch?v=40O2LQ0ObOE)
