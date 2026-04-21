import os
import json
from supabase import create_client

# PUT YOUR KEYS DIRECTLY HERE (temporary for migration)
SUPABASE_URL = "https://nhcufwzsmszlsyjdcbha.supabase.co"
SUPABASE_KEY = "sb_publishable_OfbvsapvYIGpPvU-WbgLDA_xDR8rOkR"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def save_user_data(username, data):
    data_copy = data.copy()
    data_copy.pop('username', None)
    existing = supabase.table('users').select('username').eq('username', username).execute()
    if existing.data:
        supabase.table('users').update(data_copy).eq('username', username).execute()
    else:
        data_copy['username'] = username
        supabase.table('users').insert(data_copy).execute()

def save_progress(username, subject, unit_id, lesson_id, completed=True, score=5):
    supabase.table('progress').upsert({
        'username': username,
        'subject': subject,
        'unit_id': unit_id,
        'lesson_id': lesson_id,
        'completed': completed,
        'score': score
    }).execute()

def save_chest(username, unit_id):
    supabase.table('chests_claimed').insert({
        'username': username,
        'unit_id': unit_id
    }).execute()

# Run migration
for filename in os.listdir('user_data'):
    if filename.endswith('.json') and filename != 'custom_units.json':
        username = filename[:-5]
        with open(f'user_data/{filename}', 'r') as f:
            data = json.load(f)
        
        progress = data.pop('progress', {})
        chests = data.pop('chests_claimed', [])
        
        save_user_data(username, data)
        
        for key, value in progress.items():
            parts = key.split(':')
            if len(parts) == 3:
                s, u, l = parts
                save_progress(username, s, int(u), int(l), True, value.get('score', 5))
        
        for unit_id in chests:
            save_chest(username, unit_id)
        
        print(f"✅ Migrated {username}")

print("🎉 Migration complete!")