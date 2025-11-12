# Smart Utility Hub v1.0
A lightweight desktop suite focused on quickly locating files and cleaning up duplicates.

## Features
- **File Search** – Search one or more folders, limit depth, include-only file types, and add exclusion rules.
- **Duplicate Finder** – Hash-based duplicate detection with quick exclusion presets and in-app file management.

## Run Locally
```bash
pip install -r requirements.txt
python app.py
```

## Build Executable
```bash
pyinstaller --onefile --windowed --name SmartUtilityHub --icon assets/icons/smartutilityhub.ico app.py
```
The packaged binary will be placed in `dist\SmartUtilityHub.exe`.
