#!/usr/bin/env python3
"""
Recipe Search Tool - Simple command-line interface for searching your recipe database
"""

from recipe_processor import RecipeProcessor
import sys


def print_recipe(recipe, index):
    """Pretty print a recipe result"""
    print(f"\n{'='*60}")
    print(f"#{index}. {recipe['title']}")
    print(f"{'='*60}")
    print(f"🍳 Cuisine: {recipe['cuisine']}")
    print(f"🥩 Protein: {recipe['protein_type']}")
    print(f"⏱️  Cook Time: {recipe['cook_time']}")
    print(f"👥 Servings: {recipe['servings']}")
    print(f"🔗 Source: {recipe['source_url']}")
    print(f"\n📝 Ingredients:")
    for ing in recipe['ingredients']:
        qty = ing['quantity'] if ing['quantity'] else ''
        print(f"   • {ing['name']} {qty}")


def search_interface():
    """Interactive search interface"""
    processor = RecipeProcessor()
    
    print("🍽️  Recipe Search Tool")
    print("=" * 60)
    print("\nEnter ingredients separated by commas")
    print("Example: chicken, rice noodles, coconut milk")
    print("(Press Ctrl+C to exit)\n")
    
    while True:
        try:
            user_input = input("Search ingredients: ").strip()
            if not user_input:
                continue
            
            # Parse ingredients
            ingredients = [ing.strip() for ing in user_input.split(',') if ing.strip()]
            
            if not ingredients:
                print("Please enter at least one ingredient")
                continue
            
            # Search
            print(f"\n🔍 Searching for recipes with: {', '.join(ingredients)}")
            results = processor.search_recipes(ingredients)
            
            if not results:
                print("❌ No recipes found with all those ingredients")
            else:
                print(f"\n✅ Found {len(results)} recipe(s):\n")
                for idx, recipe in enumerate(results, 1):
                    print_recipe(recipe, idx)
            
            print("\n" + "-" * 60)
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        # Command-line mode
        ingredients = sys.argv[1:]
        processor = RecipeProcessor()
        print(f"🔍 Searching for: {', '.join(ingredients)}\n")
        results = processor.search_recipes(ingredients)
        
        if not results:
            print("❌ No recipes found")
        else:
            print(f"✅ Found {len(results)} recipe(s):")
            for idx, recipe in enumerate(results, 1):
                print_recipe(recipe, idx)
    else:
        # Interactive mode
        search_interface()


if __name__ == "__main__":
    main()
