#!/usr/bin/env python3
"""
Recipe Search Web App
Flask web interface for searching your recipe database.
Run: python app.py  then open http://127.0.0.1:5000
"""

from flask import Flask, render_template, request
from recipe_processor import RecipeProcessor

app = Flask(__name__)
processor = RecipeProcessor()


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
        results = processor.search_recipes(ingredients)
    return render_template(
        "results.html",
        ingredients=ingredients,
        results=results,
        query_string=ingredients_str,
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
