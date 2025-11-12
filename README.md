# 📦 SmartUtilityHub (v1.0)

SmartUtilityHub is a lightweight desktop toolkit for Windows that helps you find files quickly, clean up duplicates, and stay focused with a minimal UI. Everything runs locally—no background indexers or cloud jobs.

[![GitHub release](https://img.shields.io/github/v/release/anjumyaseen/SmartUtilityHub?style=for-the-badge)](https://github.com/anjumyaseen/SmartUtilityHub/releases/latest)
[![GitHub all releases](https://img.shields.io/github/downloads/anjumyaseen/SmartUtilityHub/total?style=for-the-badge)](https://github.com/anjumyaseen/SmartUtilityHub/releases)
[![License](https://img.shields.io/github/license/anjumyaseen/SmartUtilityHub?style=for-the-badge)](LICENSE.txt)

---

## 📂 Project Structure

```
SmartUtilityHub/
│
├── assets/
│   └── icons/                       # SU icon assets (ICO + PNG)
├── docs/                            # Future docs (roadmap, changelog, etc.)
├── modules/
│   ├── search_tool.py               # File search UI + logic
│   └── duplicate_tool.py            # Duplicate finder UI + logic
├── release/                         # Release-ready binaries + checksums
│
├── .gitignore
├── README.md
├── SmartUtilityHub.spec             # PyInstaller spec (reproducible build)
├── app.py                           # Entry point / main window
├── requirements.txt
└── build.ps1                        # Optional helper script
```

---

## 🚀 Features

* 🔍 **Smart File Search** with wildcard queries (`report*.pdf`), include-only file types, depth limits, and exclusion rules.
* 🧩 **Duplicate Finder** that hashes files, groups matches, and lets you open/delete items directly.
* 🌓 **Auto Light/Dark Theme** via `darkdetect`—matches your OS theme on launch.
* 📁 **Folder Tree + Result Chips** for quick filtering and status visibility.
* 🪟 **Custom SU Icon** baked into the EXE plus runtime window icon for a polished look.
* ⚡ **Local-first**: scans run locally with no background indexing or network traffic.

---

## 🚀 Download

[![GitHub release](https://img.shields.io/github/v/release/anjumyaseen/SmartUtilityHub?style=for-the-badge)](https://github.com/anjumyaseen/SmartUtilityHub/releases/latest)
[![GitHub all releases](https://img.shields.io/github/downloads/anjumyaseen/SmartUtilityHub/total?style=for-the-badge)](https://github.com/anjumyaseen/SmartUtilityHub/releases)

👍 **[Latest Release](https://github.com/anjumyaseen/SmartUtilityHub/releases/latest)**

⬇️ **`SmartUtilityHub.exe`** – standalone Windows binary  
⬇️ **`SmartUtilityHub-v1.0-win64.zip`** – zipped binary if you prefer archives  
🔑 **`checksums.txt`** – SHA256 hashes for both artifacts

---

## 🛠️ Installation (Development)

1. Clone the repo:

   ```bash
   git clone https://github.com/anjumyaseen/SmartUtilityHub.git
   cd SmartUtilityHub
   ```

2. Create & activate a virtual environment:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate      # Windows
   source .venv/bin/activate   # macOS/Linux
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Run the app:

   ```bash
   python app.py
   ```

---

## 📦 Build `.exe` (Windows)

Using [PyInstaller](https://pyinstaller.org/):

```powershell
pyinstaller --onefile --windowed `
  --name SmartUtilityHub `
  --icon assets/icons/smartutilityhub.ico `
  --add-data "assets/icons/smartutilityhub.ico;assets/icons" `
  --add-data "assets/icons/smartutilityhub.png;assets/icons" `
  app.py
```

* Output: `dist\SmartUtilityHub.exe`
* For reproducible builds: `pyinstaller SmartUtilityHub.spec`

After building, package + hash files (already scripted in `release/`) for GitHub releases.

---

## 📘 Usage Notes

* Select one or more folders, type a query or wildcard (`smart*`), then hit **Search**.
* Use the filter chips to include file types (e.g., `.pdf`, `.ico`) and remove them with the **x**.
* Duplicate Finder scans selected folders, groups identical hashes, and exposes **Open** / **Delete** actions.
* Filters remain active for the current session; click **Clear** to reset folders and chips.

---

## 🧭 Roadmap (Planned)

* Menu bar (File / Edit / View / Tools)
* Export search & duplicate results (CSV / text)
* Preferences dialog with recent-folder history and advanced filter defaults

---

## 🧪 Known Limitations

* Unsigned binary (SmartScreen will warn on first launch)
* No cross-machine sync or background indexing yet — both planned for future releases.

---

## 🛡️ Security & Privacy

* No telemetry, analytics, or network calls—everything runs locally.
* Searches only touch directories you explicitly choose.
* Hashes for duplicate detection stay in-memory per session.

---

## ✅ Verify Downloads

Until the binary is code-signed, validate the SHA256 after download:

```powershell
Get-FileHash .\SmartUtilityHub.exe -Algorithm SHA256
```

Compare with the hash published in `checksums.txt` on the release page. Optional verification files (`*.sha256`) are also attached per artifact.

---

## 🧑‍💻 Contributing

* Fork the repo and create a feature branch (`git checkout -b feat/xyz`).
* Keep pull requests focused with clear descriptions/screenshots.
* Follow semantic versioning (`1.0.1` fixes, `1.1.0` features).

---

## 📄 License & Governance

* License: MIT (see `LICENSE.txt`)
* Security Policy / Contributing / Code of Conduct: will live under `docs/` as the project grows.

---

## 🙌 Feedback / Issues

Open an issue or email **anjumy.ai@gmail.com** with steps to reproduce, logs, and screenshots where helpful. Ideas and feature requests are welcome!
