# Adding This Project to GitHub

Your project is already set up with Git and an initial commit. Follow these steps to put it on GitHub.

## 1. Create a new repository on GitHub

1. Go to [github.com](https://github.com) and sign in.
2. Click the **+** in the top-right → **New repository**.
3. Choose a **Repository name** (e.g. `recipefiles`).
4. Leave **Initialize with README** unchecked (you already have a repo with a README).
5. Click **Create repository**.

## 2. Connect and push from your project

GitHub will show you commands. Use these from your project folder (or run them in the terminal in Cursor):

```bash
cd "f:\Claude\recipefiles"

# Add GitHub as the remote (replace YOUR_USERNAME and YOUR_REPO with your GitHub username and repo name)
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git

# Push your code (use "main" if GitHub created the repo with main as default)
git push -u origin master
```

If your GitHub repo uses `main` as the default branch and you want to match:

```bash
git branch -M main
git push -u origin main
```

## 3. Verify

Refresh your new repository page on GitHub. You should see all your files there.

---

**Note:** `recipe_env/`, `recipes.db`, and `__pycache__/` are in `.gitignore` and will not be pushed (this is intentional).
