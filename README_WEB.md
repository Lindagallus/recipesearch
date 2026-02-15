# Recipe Search — Web & Word version

This branch adds:

- **Word document support**: Process `.docx` recipe files (single file or folder) from the setup wizard (options 7 and 8).
- **Web interface**: Search recipes in your browser.

## Run the web app

1. Install dependencies (including Flask and python-docx):
   ```bash
   pip install -r requirements.txt
   ```
2. Start the app:
   ```bash
   python app.py
   ```
3. Open **http://127.0.0.1:5000** in your browser.

Use **Add recipes** with `python setup_recipes.py` (PDF, Word, images, HelloFresh URLs), then search via the web UI or `python search_recipes.py`.
