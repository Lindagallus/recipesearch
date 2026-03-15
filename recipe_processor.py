#!/usr/bin/env python3
"""
HelloFresh Recipe Database Builder
Scrapes HelloFresh URLs and processes PDF recipes to build a searchable database
"""

import sqlite3
import json
import re
from pathlib import Path
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
import anthropic
import PyPDF2
from docx import Document as DocxDocument
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph as DocxParagraph
from docx.table import Table as DocxTable
import os
import base64
import zipfile
from PIL import Image
import io

class RecipeProcessor:
    def __init__(self, db_path: str = "recipes.db", api_key: Optional[str] = None):
        """Initialize the recipe processor with database and API connections"""
        self.db_path = db_path
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if self.api_key:
            self.client = anthropic.Anthropic(api_key=self.api_key)
        else:
            self.client = None
            print("Warning: No API key provided. Set ANTHROPIC_API_KEY environment variable or pass api_key parameter.")
        self._init_database()
    
    def _init_database(self):
        """Create the SQLite database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create recipes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                source_type TEXT,
                source_url TEXT,
                cook_time TEXT,
                servings TEXT,
                cuisine TEXT,
                protein_type TEXT,
                full_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create ingredients table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ingredients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER,
                ingredient_name TEXT NOT NULL,
                quantity TEXT,
                category TEXT,
                FOREIGN KEY (recipe_id) REFERENCES recipes (id)
            )
        ''')
        
        # Create instructions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS instructions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER,
                step_number INTEGER,
                instruction TEXT,
                FOREIGN KEY (recipe_id) REFERENCES recipes (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        print(f"Database initialized at {self.db_path}")
    
    def scrape_hellofresh_url(self, url: str) -> Dict:
        """Scrape a HelloFresh recipe URL"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract raw text content
            # HelloFresh uses various layouts, so we grab all text
            text_content = soup.get_text(separator='\n', strip=True)
            
            return {
                'source_type': 'hellofresh_url',
                'source_url': url,
                'raw_content': text_content[:5000]  # Limit to 5000 chars
            }
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return None
    
    def extract_pdf_text(self, pdf_path: str) -> Dict:
        """Extract text from a PDF file"""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                
                return {
                    'source_type': 'pdf',
                    'source_url': pdf_path,
                    'raw_content': text[:5000]  # Limit to 5000 chars
                }
        except Exception as e:
            print(f"Error reading PDF {pdf_path}: {e}")
            return None
    
    def _iter_docx_blocks(self, doc):
        """Yield paragraphs and tables in document order (so ingredients before instructions are preserved)."""
        body = doc.element.body
        for child in body.iterchildren():
            if child.tag == qn('w:p'):
                yield DocxParagraph(child, doc)
            elif child.tag == qn('w:tbl'):
                yield DocxTable(child, doc)

    def _extract_docx_images(self, docx_path: str) -> List[Dict]:
        """Extract embedded images from a Word (.docx) file. Returns list of {image_data: base64, image_format: media_type}."""
        result = []
        ext_to_media = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
        }
        try:
            with zipfile.ZipFile(docx_path, 'r') as z:
                for name in z.namelist():
                    if not name.startswith('word/media/'):
                        continue
                    ext = os.path.splitext(name)[1].lower()
                    media_type = ext_to_media.get(ext, 'image/jpeg')
                    data = z.read(name)
                    if len(data) < 100:  # skip tiny/placeholder images
                        continue
                    result.append({
                        'image_data': base64.standard_b64encode(data).decode('utf-8'),
                        'image_format': media_type,
                    })
        except Exception as e:
            print(f"Note: could not extract images from Word doc: {e}")
        return result

    def extract_docx_text(self, docx_path: str) -> Optional[Dict]:
        """Extract text and embedded images from a Word (.docx) file in document order."""
        try:
            doc = DocxDocument(docx_path)
            parts = []
            for block in self._iter_docx_blocks(doc):
                if isinstance(block, DocxParagraph):
                    if block.text.strip():
                        parts.append(block.text.strip())
                else:
                    for row in block.rows:
                        row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                        if row_text:
                            parts.append(row_text)
            text = "\n".join(parts)
            images = self._extract_docx_images(docx_path)
            return {
                'source_type': 'docx',
                'source_url': docx_path,
                'raw_content': text[:8000] if text else "",
                'images': images,
            }
        except Exception as e:
            print(f"Error reading Word doc {docx_path}: {e}")
            return None
    
    def process_image(self, image_path: str) -> Dict:
        """Process an image file (photo or scanned recipe)"""
        try:
            # Read and encode image
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # Detect image format
            image_format = None
            if image_path.lower().endswith(('.jpg', '.jpeg')):
                image_format = 'image/jpeg'
            elif image_path.lower().endswith('.png'):
                image_format = 'image/png'
            elif image_path.lower().endswith('.gif'):
                image_format = 'image/gif'
            elif image_path.lower().endswith('.webp'):
                image_format = 'image/webp'
            else:
                # Try to detect format using PIL
                try:
                    img = Image.open(io.BytesIO(image_data))
                    format_map = {'JPEG': 'image/jpeg', 'PNG': 'image/png', 'GIF': 'image/gif', 'WEBP': 'image/webp'}
                    image_format = format_map.get(img.format, 'image/jpeg')
                except:
                    image_format = 'image/jpeg'  # Default fallback
            
            # Encode to base64
            image_base64 = base64.standard_b64encode(image_data).decode('utf-8')
            
            return {
                'source_type': 'image',
                'source_url': image_path,
                'image_data': image_base64,
                'image_format': image_format
            }
        except Exception as e:
            print(f"Error reading image {image_path}: {e}")
            return None
    
    def classify_with_ai(self, raw_content: str = None, image_data: Dict = None, image_list: List[Dict] = None) -> Optional[Dict]:
        """Use Claude API to extract and classify recipe information from text and/or images (e.g. Word doc with embedded image)."""
        if not self.client:
            print("Error: No API client available. Please set ANTHROPIC_API_KEY.")
            return None
        
        prompt_text = """Extract recipe information from this content and return it as a JSON object.

Return a JSON object with this exact structure:
{
  "title": "Recipe name",
  "cook_time": "e.g., 30 min",
  "servings": "e.g., 2 servings",
  "cuisine": "e.g., Asian, Italian, Mexican, American, etc.",
  "protein_type": "chicken, beef, pork, fish, seafood, vegetarian, vegan, or none",
  "ingredients": [
    {"name": "ingredient name", "quantity": "amount", "category": "protein/vegetable/grain/dairy/spice/other"}
  ],
  "instructions": [
    "Step 1 text",
    "Step 2 text"
  ]
}

Be thorough in extracting ALL ingredients from the recipe. List every ingredient with its quantity if given.
If the content includes both text and images (e.g. a Word doc with an inserted recipe photo), use BOTH: extract from the text and from any recipe image.
If information is missing, use "unknown" or leave empty array.
Return ONLY the JSON object, no other text."""

        try:
            # Build message content: text and/or images (single image, or text + embedded docx images)
            if image_list:
                # Word doc with embedded images: send text (if any) then all images, then prompt
                message_content = []
                if raw_content:
                    message_content.append({
                        "type": "text",
                        "text": f"""Recipe content from document (text below; images follow):

{raw_content}

---
Images from the same document follow. Use the text above and the images to extract the full recipe."""
                    })
                else:
                    message_content.append({
                        "type": "text",
                        "text": "The following image(s) were extracted from a Word document. Extract the recipe from the image(s)."
                    })
                for img in image_list:
                    message_content.append({
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": img['image_format'],
                            "data": img['image_data']
                        }
                    })
                message_content.append({"type": "text", "text": prompt_text})
            elif image_data:
                # Single standalone image (no image_list)
                message_content = [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": image_data['image_format'],
                            "data": image_data['image_data']
                        }
                    },
                    {"type": "text", "text": prompt_text}
                ]
            else:
                # Text only
                message_content = f"""Recipe text:
{raw_content or '(no text)'}

{prompt_text}"""
            
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[{"role": "user", "content": message_content}]
            )
            
            response_text = message.content[0].text
            # Extract JSON from response (in case there's extra text)
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                recipe_data = json.loads(json_match.group())
                return recipe_data
            else:
                print("Could not extract JSON from API response")
                return None
                
        except Exception as e:
            print(f"Error calling Claude API: {e}")
            return None
    
    def save_recipe(self, recipe_data: Dict, source_info: Dict):
        """Save a recipe to the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Insert recipe
            cursor.execute('''
                INSERT INTO recipes (title, source_type, source_url, cook_time, servings, cuisine, protein_type, full_text)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                recipe_data.get('title', 'Unknown Recipe'),
                source_info['source_type'],
                source_info['source_url'],
                recipe_data.get('cook_time', ''),
                recipe_data.get('servings', ''),
                recipe_data.get('cuisine', ''),
                recipe_data.get('protein_type', ''),
                source_info['raw_content']
            ))
            
            recipe_id = cursor.lastrowid
            
            # Insert ingredients (normalize: AI may return list of dicts or list of strings)
            raw_ingredients = recipe_data.get('ingredients', [])
            if isinstance(raw_ingredients, str):
                raw_ingredients = [s.strip() for s in raw_ingredients.replace(',', '\n').splitlines() if s.strip()]
            for ing in raw_ingredients:
                if isinstance(ing, dict):
                    name = (ing.get('name') or '').strip()
                    quantity = (ing.get('quantity') or '').strip()
                    category = ing.get('category') or 'other'
                else:
                    name = str(ing).strip()
                    quantity = ''
                    category = 'other'
                if not name:
                    continue
                cursor.execute('''
                    INSERT INTO ingredients (recipe_id, ingredient_name, quantity, category)
                    VALUES (?, ?, ?, ?)
                ''', (recipe_id, name, quantity, category))
            
            # Insert instructions
            for idx, instruction in enumerate(recipe_data.get('instructions', []), 1):
                cursor.execute('''
                    INSERT INTO instructions (recipe_id, step_number, instruction)
                    VALUES (?, ?, ?)
                ''', (recipe_id, idx, instruction))
            
            conn.commit()
            print(f"✓ Saved recipe: {recipe_data.get('title', 'Unknown')}")
            
        except Exception as e:
            print(f"Error saving recipe: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def process_url(self, url: str):
        """Process a single HelloFresh URL"""
        print(f"\nProcessing URL: {url}")
        source_info = self.scrape_hellofresh_url(url)
        if source_info:
            recipe_data = self.classify_with_ai(raw_content=source_info['raw_content'])
            if recipe_data:
                self.save_recipe(recipe_data, source_info)
    
    def process_pdf(self, pdf_path: str):
        """Process a single PDF file"""
        print(f"\nProcessing PDF: {pdf_path}")
        source_info = self.extract_pdf_text(pdf_path)
        if source_info:
            recipe_data = self.classify_with_ai(raw_content=source_info['raw_content'])
            if recipe_data:
                self.save_recipe(recipe_data, source_info)
    
    def process_docx(self, docx_path: str):
        """Process a single Word (.docx) file (text and any embedded recipe images)."""
        print(f"\nProcessing Word doc: {docx_path}")
        source_info = self.extract_docx_text(docx_path)
        if not source_info:
            return
        raw_content = source_info.get('raw_content') or ''
        images = source_info.get('images') or []
        if not raw_content and not images:
            print(f"  (No text or images found in {docx_path}; skipping)")
            return
        recipe_data = self.classify_with_ai(
            raw_content=raw_content if raw_content else None,
            image_list=images if images else None,
        )
        if recipe_data:
            self.save_recipe(recipe_data, source_info)
    
    def process_docx_from_folder(self, folder_path: str):
        """Process all Word (.docx) files in a folder"""
        docx_files = list(Path(folder_path).glob("*.docx"))
        print(f"Found {len(docx_files)} Word (.docx) files to process")
        for docx_file in docx_files:
            self.process_docx(str(docx_file))
    
    def process_image_file(self, image_path: str):
        """Process a single image file (photo or scanned recipe)"""
        print(f"\nProcessing image: {image_path}")
        source_info = self.process_image(image_path)
        if source_info:
            recipe_data = self.classify_with_ai(image_data=source_info)
            if recipe_data:
                # Store image info but remove base64 data before saving
                save_info = {
                    'source_type': source_info['source_type'],
                    'source_url': source_info['source_url'],
                    'raw_content': f"[Image file: {image_path}]"
                }
                self.save_recipe(recipe_data, save_info)
    
    def process_urls_from_file(self, file_path: str):
        """Process multiple URLs from a text file (one per line)"""
        with open(file_path, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
        
        print(f"Found {len(urls)} URLs to process")
        for url in urls:
            self.process_url(url)
    
    def process_pdfs_from_folder(self, folder_path: str):
        """Process all PDFs in a folder"""
        pdf_files = list(Path(folder_path).glob("*.pdf"))
        print(f"Found {len(pdf_files)} PDF files to process")
        
        for pdf_file in pdf_files:
            self.process_pdf(str(pdf_file))
    
    def process_images_from_folder(self, folder_path: str):
        """Process all image files in a folder"""
        image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.webp', '*.JPG', '*.JPEG', '*.PNG']
        image_files = []
        for ext in image_extensions:
            image_files.extend(list(Path(folder_path).glob(ext)))
        
        print(f"Found {len(image_files)} image files to process")
        
        for image_file in image_files:
            self.process_image_file(str(image_file))
    
    def search_recipes(self, ingredients: List[str]) -> List[Dict]:
        """Search for recipes where each term appears in ingredients, title, or full text.

        Returned recipe dicts include:
        - basic metadata (title, cook time, cuisine, etc.)
        - full ingredient list
        - full instructions list (step_number + text)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Each term can match in ingredient name, recipe title, or full_text (so "kodiak" finds a recipe even if only in title)
        term_clause = """(
            LOWER(r.title) LIKE ? OR
            LOWER(COALESCE(r.full_text, '')) LIKE ? OR
            EXISTS (SELECT 1 FROM ingredients i WHERE i.recipe_id = r.id AND LOWER(i.ingredient_name) LIKE ?)
        )"""
        # For each search term we need 3 placeholders: title, full_text, ingredient
        clauses = [term_clause for _ in ingredients]
        query = f'''
            SELECT DISTINCT r.id, r.title, r.cook_time, r.servings, r.cuisine, r.protein_type, r.source_url
            FROM recipes r
            WHERE {' AND '.join(clauses)}
            ORDER BY r.title
        '''
        params = []
        for ing in ingredients:
            pattern = f'%{ing.lower()}%'
            params.extend([pattern, pattern, pattern])
        cursor.execute(query, params)
        
        results = []
        for row in cursor.fetchall():
            recipe = {
                'id': row[0],
                'title': row[1],
                'cook_time': row[2],
                'servings': row[3],
                'cuisine': row[4],
                'protein_type': row[5],
                'source_url': row[6],
            }
            
            # Get all ingredients for this recipe
            cursor.execute('''
                SELECT ingredient_name, quantity
                FROM ingredients
                WHERE recipe_id = ?
                ORDER BY id
            ''', (recipe['id'],))
            recipe['ingredients'] = [
                {'name': ing[0], 'quantity': ing[1]}
                for ing in cursor.fetchall()
            ]

            # Get all instructions (ordered steps) for this recipe
            cursor.execute('''
                SELECT step_number, instruction
                FROM instructions
                WHERE recipe_id = ?
                ORDER BY step_number
            ''', (recipe['id'],))
            recipe['instructions'] = [
                {'step': row_i[0], 'text': row_i[1]}
                for row_i in cursor.fetchall()
            ]

            results.append(recipe)
        
        conn.close()
        return results


def main():
    """Example usage"""
    print("HelloFresh Recipe Database Builder")
    print("=" * 50)
    
    # Initialize processor
    processor = RecipeProcessor()
    
    print("\nUsage examples:")
    print("1. Process a single URL:")
    print('   processor.process_url("https://www.hellofresh.ca/recipes/...")')
    print("\n2. Process URLs from a file:")
    print('   processor.process_urls_from_file("my_urls.txt")')
    print("\n3. Process PDFs from a folder:")
    print('   processor.process_pdfs_from_folder("recipe_pdfs/")')
    print("\n4. Process images from a folder:")
    print('   processor.process_images_from_folder("recipe_photos/")')
    print("\n5. Process a single image:")
    print('   processor.process_image_file("recipe_photo.jpg")')
    print("\n6. Search for recipes:")
    print('   results = processor.search_recipes(["chicken", "rice noodles", "coconut milk"])')
    print("\nIMPORTANT: Set your ANTHROPIC_API_KEY environment variable first!")
    print("   export ANTHROPIC_API_KEY='your-api-key-here'")
    print("\nSupported image formats: JPG, PNG, GIF, WEBP")
    print("Works with photos, screenshots, and scanned documents!")


if __name__ == "__main__":
    main()
