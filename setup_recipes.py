#!/usr/bin/env python3
"""
Recipe Database Setup Script
Run this to populate your database with recipes
"""

from recipe_processor import RecipeProcessor
import os
from pathlib import Path


def setup_wizard():
    """Interactive setup wizard"""
    print("🍽️  HelloFresh Recipe Database Setup")
    print("=" * 60)
    print("\nThis tool will help you build a searchable database of your recipes.")
    print("\nFirst, let's check your API key...")
    
    # Check API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("\n⚠️  No ANTHROPIC_API_KEY found!")
        print("\nTo use this tool, you need a Claude API key from:")
        print("https://console.anthropic.com/")
        print("\nOnce you have your key, set it as an environment variable:")
        print("  Mac/Linux: export ANTHROPIC_API_KEY='your-key-here'")
        print("  Windows:   set ANTHROPIC_API_KEY=your-key-here")
        print("\nOr enter it now (it won't be saved):")
        api_key = input("API Key: ").strip()
        if not api_key:
            print("\n❌ Cannot proceed without API key. Exiting.")
            return
    else:
        print("✅ API key found!")
    
    # Initialize processor
    processor = RecipeProcessor(api_key=api_key)
    
    print("\n" + "=" * 60)
    print("What would you like to add?")
    print("=" * 60)
    print("1. Process HelloFresh URLs from a file")
    print("2. Process a single HelloFresh URL")
    print("3. Process PDF files from a folder")
    print("4. Process a single PDF file")
    print("5. Process image files from a folder (photos/scanned recipes)")
    print("6. Process a single image file")
    print("7. Exit")
    
    choice = input("\nEnter choice (1-7): ").strip()
    
    if choice == "1":
        file_path = input("\nEnter path to text file with URLs (one per line): ").strip()
        if Path(file_path).exists():
            processor.process_urls_from_file(file_path)
            print("\n✅ Done! Use search_recipes.py to search your database.")
        else:
            print(f"❌ File not found: {file_path}")
    
    elif choice == "2":
        url = input("\nEnter HelloFresh URL: ").strip()
        processor.process_url(url)
        print("\n✅ Done! Use search_recipes.py to search your database.")
    
    elif choice == "3":
        folder_path = input("\nEnter path to folder containing PDFs: ").strip()
        if Path(folder_path).exists():
            processor.process_pdfs_from_folder(folder_path)
            print("\n✅ Done! Use search_recipes.py to search your database.")
        else:
            print(f"❌ Folder not found: {folder_path}")
    
    elif choice == "4":
        pdf_path = input("\nEnter path to PDF file: ").strip()
        if Path(pdf_path).exists():
            processor.process_pdf(pdf_path)
            print("\n✅ Done! Use search_recipes.py to search your database.")
        else:
            print(f"❌ File not found: {pdf_path}")
    
    elif choice == "5":
        folder_path = input("\nEnter path to folder containing images (JPG, PNG, etc.): ").strip()
        if Path(folder_path).exists():
            processor.process_images_from_folder(folder_path)
            print("\n✅ Done! Use search_recipes.py to search your database.")
        else:
            print(f"❌ Folder not found: {folder_path}")
    
    elif choice == "6":
        image_path = input("\nEnter path to image file: ").strip()
        if Path(image_path).exists():
            processor.process_image_file(image_path)
            print("\n✅ Done! Use search_recipes.py to search your database.")
        else:
            print(f"❌ File not found: {image_path}")
    
    elif choice == "7":
        print("\n👋 Goodbye!")
    
    else:
        print("\n❌ Invalid choice")


if __name__ == "__main__":
    setup_wizard()
