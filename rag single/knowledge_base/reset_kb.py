import shutil
import tempfile
from pathlib import Path
import os

def reset_knowledge_base():
    temp_dir = Path(tempfile.gettempdir())
    
    # Directories to delete
    dirs_to_delete = [
        temp_dir / "faiss_db",
        temp_dir / "faiss_db_en"
    ]
    
    print(f"Targeting directories in: {temp_dir}")
    
    for d in dirs_to_delete:
        if d.exists():
            try:
                shutil.rmtree(d)
                print(f"✅ Successfully deleted: {d}")
            except Exception as e:
                print(f"❌ Failed to delete {d}: {e}")
        else:
            print(f"ℹ️ Directory not found (already clean): {d}")

    print("\nKnowledge base has been reset. Please rebuild the index using build_index_en.py or upload documents again.")

if __name__ == "__main__":
    reset_knowledge_base()
