"""Script de teste para identificar categorias corretas."""
import requests
import json

API_URL = "https://cyberpunk.fandom.com/api.php"

# Lista categorias que começam com "Cyberpunk 2077"
params = {
    'action': 'query',
    'list': 'allcategories',
    'acprefix': 'Cyberpunk 2077',
    'aclimit': 50,
    'format': 'json'
}

r = requests.get(API_URL, params=params)
data = r.json()

print("=== CATEGORIAS DISPONÍVEIS ===")
for cat in data.get('query', {}).get('allcategories', []):
    print(f"  - {cat['*']}")

# Testa categoria específica
print("\n=== TESTANDO CATEGORIAS ===")
test_cats = [
    "Cyberpunk 2077 Characters",
    "Cyberpunk 2077 characters",
    "Characters"
]

for cat in test_cats:
    params = {
        'action': 'query',
        'list': 'categorymembers',
        'cmtitle': f'Category:{cat}',
        'cmlimit': 10,
        'cmtype': 'page',
        'format': 'json'
    }
    r = requests.get(API_URL, params=params)
    data = r.json()
    members = data.get('query', {}).get('categorymembers', [])
    print(f"\n'{cat}': {len(members)} páginas")
    for m in members[:5]:
        print(f"    - {m['title']}")
