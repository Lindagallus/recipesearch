# Image Recipe Processing - Quick Start Guide

## 📸 Processing Recipe Photos & Scanned Documents

Your recipe database tool now supports extracting recipes from images! This works with:
- **Photos of recipe cards**
- **Handwritten recipes**
- **Screenshots from websites**
- **Scanned documents**
- **Photos of cookbook pages**

## 🎯 Step-by-Step Guide

### 1. Organize Your Images

Put all your recipe photos in one folder:
```
my_recipes/
  ├── grandmas_lasagna.jpg
  ├── chicken_curry.png
  ├── handwritten_cake.jpg
  └── screenshot_pasta.png
```

### 2. Run Setup

```bash
python3 setup_recipes.py
```

Choose option **5** (Process image files from a folder)
Enter your folder path: `my_recipes/`

### 3. Watch the Magic

The tool will:
1. Read each image (even handwritten text!)
2. Extract recipe title, ingredients, and instructions
3. Classify ingredients by category
4. Store everything in your searchable database

### 4. Search Your Collection

```bash
python3 search_recipes.py
```

Enter ingredients: `chicken, coconut milk, ginger`

Get instant results from all your recipes!

## 📷 Tips for Best Results

### Good Photos:
- ✅ Well-lit, clear focus
- ✅ Text is readable
- ✅ Recipe fills most of the frame
- ✅ Straight-on angle (not too tilted)

### For Handwritten Recipes:
- ✅ Write clearly and legibly
- ✅ Use dark ink on light paper
- ✅ Good contrast
- ✅ No shadows blocking text

### Multiple Formats Work:
- JPG/JPEG
- PNG
- GIF
- WEBP

## 💡 Example Workflow

**Scenario:** You have a box of your grandmother's handwritten recipe cards

1. Take clear photos of each card with your phone
2. Transfer photos to your computer (e.g., in `~/grandmas_recipes/`)
3. Run: `python3 setup_recipes.py`
4. Choose option 5, enter folder path
5. Wait 30-60 seconds while AI processes them
6. Search by ingredients anytime!

**Cost:** ~$0.02 per image with Claude API (so 50 recipes ≈ $1)

## 🔧 Troubleshooting

**"Can't read the handwriting"**
- Claude is pretty good at handwriting, but if text is too messy, try typing it into a text file or cleaning up the image

**"Image too blurry"**
- Retake the photo with better lighting and focus
- Make sure camera lens is clean

**"Missing some ingredients"**
- Check the console output - the AI shows what it extracted
- You can manually edit the database if needed (it's just SQLite)

**"File format not supported"**
- Convert to JPG or PNG
- Most phones save as JPG by default

## 🎨 Advanced: Single Image Processing

For just one recipe:
```bash
python3 setup_recipes.py
```
Choose option **6** (Process a single image file)
Enter: `path/to/recipe_photo.jpg`

## 🔍 What Gets Extracted

From each image, the AI extracts:
- Recipe title
- Cook time and servings
- Full ingredients list with quantities
- Ingredient categories (protein, vegetable, grain, etc.)
- Step-by-step instructions
- Cuisine type
- Protein type

All of this becomes searchable!

## 🚀 Next Steps

Once you've processed your images:
1. Try searching different ingredient combinations
2. Discover recipes you forgot you had
3. Plan meals based on what's in your fridge
4. Share your database with family members

---

**Questions?** Check the main README.md for full documentation!
