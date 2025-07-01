import os
import json
import shutil
from difflib import get_close_matches

WORKFLOWS_DIR = 'workflows'

# Get all subfolders (categories)
CATEGORIES = [
    name for name in os.listdir(WORKFLOWS_DIR)
    if os.path.isdir(os.path.join(WORKFLOWS_DIR, name))
]

# Build a keyword map for each category (can be expanded for better accuracy)
CATEGORY_KEYWORDS = {cat: cat.lower().replace('&', '').replace('_', ' ').replace('  ', ' ').split() for cat in CATEGORIES}

# List all JSON workflow files in the root workflows directory
workflow_files = [
    f for f in os.listdir(WORKFLOWS_DIR)
    if f.endswith('.json') and os.path.isfile(os.path.join(WORKFLOWS_DIR, f))
]

moves = []

for wf in workflow_files:
    wf_path = os.path.join(WORKFLOWS_DIR, wf)
    try:
        with open(wf_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Use name, tags, and any description fields for matching
        text = ''
        if 'name' in data:
            text += data['name'] + ' '
        if 'tags' in data and isinstance(data['tags'], list):
            text += ' '.join([t['name'] if isinstance(t, dict) and 'name' in t else str(t) for t in data['tags']]) + ' '
        # Search for description in sticky notes or nodes
        if 'nodes' in data and isinstance(data['nodes'], list):
            for node in data['nodes']:
                if node.get('type', '').lower().startswith('n8n-nodes-base.stickynote'):
                    content = node.get('parameters', {}).get('content', '')
                    text += content + ' '
        text = text.lower()
        # Fuzzy match to category
        best_cat = None
        best_score = 0
        for cat, keywords in CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > best_score:
                best_score = score
                best_cat = cat
        # Only move if a clear match
        if best_cat and best_score > 0:
            dest = os.path.join(WORKFLOWS_DIR, best_cat, wf)
            shutil.move(wf_path, dest)
            moves.append((wf, best_cat))
    except Exception as e:
        print(f"Error processing {wf}: {e}")

print("Workflow moves performed:")
for wf, cat in moves:
    print(f"- {wf} -> {cat}/")
if not moves:
    print("No workflows moved.") 