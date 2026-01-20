
import os
import sys
from google import genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    print("Error: GOOGLE_API_KEY not set.")
    sys.exit(1)

client = genai.Client(api_key=api_key)

def list_and_delete_files():
    print("Listing files on Google GenAI...")
    files_to_delete = []
    
    try:
        # Paging through files
        for f in client.files.list():
            print(f"Found: {f.name} (Display Name: {f.display_name if hasattr(f, 'display_name') else 'N/A'}, Size: {f.size_bytes if hasattr(f, 'size_bytes') else 'Unknown'})")
            files_to_delete.append(f)
            
        print(f"\nTotal files found: {len(files_to_delete)}")
        
        if not files_to_delete:
            print("No files to delete.")
            return

        confirm = input("Do you want to DELETE ALL these files? (yes/no): ")
        if confirm.lower() == "yes":
            for f in files_to_delete:
                print(f"Deleting {f.name}...")
                try:
                    client.files.delete(name=f.name)
                except Exception as e:
                    print(f"Failed to delete {f.name}: {e}")
            print("Deletion complete.")
        else:
            print("Operation cancelled.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_and_delete_files()
