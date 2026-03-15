#!/usr/bin/env python3
"""
Recipe Search Web App
Flask web interface for searching your recipe database.
Run: python app.py  then open http://127.0.0.1:5000
"""

from pathlib import Path

from flask import Flask, render_template, request

from recipe_processor import RecipeProcessor

app = Flask(__name__)

# Global processor used for read-only search (doesn't require API key)
search_processor = RecipeProcessor()


@app.route("/")
def index():
    """Home page with search form"""
    return render_template("index.html")


@app.route("/search", methods=["GET", "POST"])
def search():
    """Search recipes by ingredients and show results"""
    ingredients_str = request.form.get("ingredients", "") or request.args.get("ingredients", "")
    ingredients = [x.strip() for x in ingredients_str.split(",") if x.strip()]
    results = []
    if ingredients:
        results = search_processor.search_recipes(ingredients)
    return render_template(
        "results.html",
        ingredients=ingredients,
        results=results,
        query_string=ingredients_str,
    )


@app.route("/admin", methods=["GET", "POST"])
def admin():
    """
    Simple admin page to run the same loading options as setup_recipes.py:
    - Process HelloFresh URLs
    - Process PDFs
    - Process images
    - Process Word (.docx) recipes

    This is intended for local use only.
    """
    status = None
    error = None

    if request.method == "POST":
        action = request.form.get("action") or ""
        api_key = (request.form.get("api_key") or "").strip() or None
        path = (request.form.get("path") or "").strip()

        # Use a dedicated processor for admin actions, so the user can supply an API key
        admin_processor = RecipeProcessor(api_key=api_key)

        try:
            # URL-based options
            if action == "url_single":
                if not path:
                    raise ValueError("Please enter a HelloFresh URL.")
                admin_processor.process_url(path)
                status = f"Processed single HelloFresh URL: {path}"

            elif action == "url_file":
                if not path:
                    raise ValueError("Please enter a path to a text file with URLs.")
                if not Path(path).exists():
                    raise ValueError(f"File not found: {path}")
                admin_processor.process_urls_from_file(path)
                status = f"Processed URLs from file: {path}"

            # PDF options
            elif action == "pdf_single":
                if not path:
                    raise ValueError("Please enter a path to a PDF file.")
                if not Path(path).exists():
                    raise ValueError(f"File not found: {path}")
                admin_processor.process_pdf(path)
                status = f"Processed PDF file: {path}"

            elif action == "pdf_folder":
                if not path:
                    raise ValueError("Please enter a path to a folder with PDFs.")
                if not Path(path).exists():
                    raise ValueError(f"Folder not found: {path}")
                admin_processor.process_pdfs_from_folder(path)
                status = f"Processed all PDFs in folder: {path}"

            # Image options
            elif action == "image_single":
                if not path:
                    raise ValueError("Please enter a path to an image file.")
                if not Path(path).exists():
                    raise ValueError(f"File not found: {path}")
                admin_processor.process_image_file(path)
                status = f"Processed image file: {path}"

            elif action == "image_folder":
                if not path:
                    raise ValueError("Please enter a path to a folder with images.")
                if not Path(path).exists():
                    raise ValueError(f"Folder not found: {path}")
                admin_processor.process_images_from_folder(path)
                status = f"Processed all images in folder: {path}"

            # Word (.docx) options
            elif action == "docx_single":
                if not path:
                    raise ValueError("Please enter a path to a Word (.docx) file.")
                if not Path(path).exists():
                    raise ValueError(f"File not found: {path}")
                admin_processor.process_docx(path)
                status = f"Processed Word file: {path}"

            elif action == "docx_folder":
                if not path:
                    raise ValueError("Please enter a path to a folder with Word (.docx) files.")
                if not Path(path).exists():
                    raise ValueError(f"Folder not found: {path}")
                admin_processor.process_docx_from_folder(path)
                status = f"Processed all Word (.docx) files in folder: {path}"

            else:
                raise ValueError("Please choose an action.")

        except Exception as exc:  # noqa: BLE001
            error = str(exc)

    return render_template("admin.html", status=status, error=error)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
