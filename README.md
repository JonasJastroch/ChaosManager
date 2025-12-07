# Chaos Manager 📂🧠

### AI-Powered File Sorting for Windows

The **Chaos Manager** is an innovative tool that uses local Large Language Models (LLaMA/Llama 3) to automatically analyze your cluttered Downloads, Desktop, or other directories and organize them into a clean, professional, and logical folder structure.

---

There are two ways to start the Chaos Manager: [Jump directly to Installation & Start](#-installation--start).

---

## 💻 System Requirements

* **Operating System:** Windows 10/11 (The .exe is compiled for Windows only.)
* **AI Backend:** [Ollama](https://ollama.com/download/windows) (You must install and run Ollama to provide the AI models.)

---

## ⚠️ Important Security Notice (Windows Defender)

Since the **Chaos Manager** is a newly built, unsigned `.exe` file that accesses your file system, **Windows Defender SmartScreen** might show a warning when you first run it.

> 🔒 **Message:** "Windows protected your PC"

This is **normal behavior** for new programs that modify the file system. The project is open source, and the code is secure.

### How to Bypass the Warning:

1.  In the blue warning window, click **"More info"**.
2.  Then, click **"Run anyway"**.

---

## 🚀 Installation & Start

**Choose ONE of the following methods to start the Chaos Manager.**

### 1. Using Source Code (For Developers & Full Control)

To run the project directly from the source code and maintain full control, follow these steps:

#### Step 1: Prepare the AI Backend (Ollama)

Before you can run the script, you need to install Ollama and download the required language model (`llama3:8b`):

1.  Make sure **[Ollama for Windows](https://ollama.com/download/windows)** is installed and running.
2.  Open **PowerShell** and run the following command to pull the Llama 3 model:

    ```powershell
    ollama pull llama3:8b
    ```

#### Step 2: Clone and Run the Project

1.  Clone the repository locally:

    ```bash
    git clone [https://github.com/JonasJastroch/ChaosManager.git](https://github.com/JonasJastroch/ChaosManager.git)
    cd ChaosManager
    ```

2.  Make sure you have all Python dependencies installed (if necessary, via `pip install -r requirements.txt`).
3.  Run the main file:

    ```bash
    python main.py
    ```

### 2. Simple Use (.exe Binary)

For the quickest setup, download the pre-compiled executable:

1.  Go to the **[GitHub Releases](https://github.com/JonasJastroch/ChaosManager/releases/tag/v1.0)** of the project.
2.  Download the `.exe` file under **Assets**.
3.  Run the file (you may need to confirm the Windows Defender warning as described above).

---

## 📺 Demo Video

See the Chaos Manager in action:

[https://www.youtube.com/watch?v=40O2LQ0ObOE](https://www.youtube.com/watch?v=40O2LQ0ObOE)
