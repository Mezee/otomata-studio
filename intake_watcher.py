import os
import json
import shutil
import time
from difflib import get_close_matches
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

INTAKE_DIR = 'Workflow Intake'
WORKFLOWS_DIR = 'workflows'

# Get all subfolders (categories)
def get_categories():
    return [
        name for name in os.listdir(WORKFLOWS_DIR)
        if os.path.isdir(os.path.join(WORKFLOWS_DIR, name))
    ]

def get_category_keywords(categories):
    return {cat: cat.lower().replace('&', '').replace('_', ' ').replace('  ', ' ').split() for cat in categories}

def categorize_and_move(file_path, filename):
    categories = get_categories()
    category_keywords = get_category_keywords(categories)
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        text = ''
        if 'name' in data:
            text += data['name'] + ' '
        if 'tags' in data and isinstance(data['tags'], list):
            text += ' '.join([t['name'] if isinstance(t, dict) and 'name' in t else str(t) for t in data['tags']]) + ' '
        if 'nodes' in data and isinstance(data['nodes'], list):
            for node in data['nodes']:
                if node.get('type', '').lower().startswith('n8n-nodes-base.stickynote'):
                    content = node.get('parameters', {}).get('content', '')
                    text += content + ' '
        text = text.lower()
        best_cat = None
        best_score = 0
        for cat, keywords in category_keywords.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > best_score:
                best_score = score
                best_cat = cat
        if best_cat and best_score > 0:
            dest = os.path.join(WORKFLOWS_DIR, best_cat, filename)
            shutil.move(file_path, dest)
            print(f"Moved: {filename} -> {best_cat}/")
        else:
            print(f"No clear category for {filename}, leaving in intake.")
    except Exception as e:
        print(f"Error processing {filename}: {e}")

class IntakeHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.json'):
            filename = os.path.basename(event.src_path)
            # Wait for file to finish writing
            time.sleep(1)
            categorize_and_move(event.src_path, filename)

if __name__ == "__main__":
    print(f"Watching '{INTAKE_DIR}' for new workflow files...")
    event_handler = IntakeHandler()
    observer = Observer()
    observer.schedule(event_handler, INTAKE_DIR, recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join() 