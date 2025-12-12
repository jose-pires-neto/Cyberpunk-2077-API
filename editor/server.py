"""
Cyberpunk API JSON Editor - Backend
Servidor Flask para editar os arquivos JSON da API.
"""

import json
import os
import webbrowser
import threading
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

# Caminho absoluto para a pasta static
EDITOR_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(EDITOR_DIR, 'static')

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path='/static')
CORS(app)

# Caminhos dos arquivos JSON
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_DIR = os.path.join(BASE_DIR, 'docs', 'api', 'v1')

CATEGORIES = {
    'characters': 'characters.json',
    'gangs': 'gangs.json',
    'districts': 'districts.json'
}


def load_json(category):
    """Carrega um arquivo JSON da categoria especificada."""
    filepath = os.path.join(API_DIR, CATEGORIES[category])
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []


def save_json(category, data):
    """Salva dados no arquivo JSON da categoria especificada."""
    filepath = os.path.join(API_DIR, CATEGORIES[category])
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# --- ROTAS DA API ---

@app.route('/')
def index():
    """Serve a página principal do editor."""
    return send_from_directory(STATIC_DIR, 'index.html')


@app.route('/api/categories')
def get_categories():
    """Lista todas as categorias disponíveis."""
    return jsonify(list(CATEGORIES.keys()))


@app.route('/api/affiliations')
def get_affiliations():
    """Lista todas as afiliações disponíveis."""
    filepath = os.path.join(API_DIR, 'affiliations.json')
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return jsonify(json.load(f))
    except FileNotFoundError:
        return jsonify([])


@app.route('/api/<category>')
def get_all(category):
    """Lista todos os itens de uma categoria."""
    if category not in CATEGORIES:
        return jsonify({'error': 'Categoria não encontrada'}), 404
    
    data = load_json(category)
    return jsonify(data)


@app.route('/api/<category>/<int:item_id>')
def get_one(category, item_id):
    """Busca um item específico por ID."""
    if category not in CATEGORIES:
        return jsonify({'error': 'Categoria não encontrada'}), 404
    
    data = load_json(category)
    item = next((x for x in data if x.get('id') == item_id), None)
    
    if item is None:
        return jsonify({'error': 'Item não encontrado'}), 404
    
    return jsonify(item)


@app.route('/api/<category>/<int:item_id>', methods=['PUT'])
def update_one(category, item_id):
    """Atualiza um item específico."""
    if category not in CATEGORIES:
        return jsonify({'error': 'Categoria não encontrada'}), 404
    
    data = load_json(category)
    item_index = next((i for i, x in enumerate(data) if x.get('id') == item_id), None)
    
    if item_index is None:
        return jsonify({'error': 'Item não encontrado'}), 404
    
    # Atualiza apenas os campos enviados (não sobrescreve imagens, id, etc.)
    updates = request.json
    protected_fields = ['id', 'images', 'directory']
    
    for key, value in updates.items():
        if key not in protected_fields:
            data[item_index][key] = value
    
    save_json(category, data)
    
    return jsonify({
        'success': True,
        'message': 'Item atualizado com sucesso!',
        'item': data[item_index]
    })


def open_browser():
    """Abre o navegador após o servidor iniciar."""
    webbrowser.open('http://localhost:5000')


if __name__ == '__main__':
    print("\n🌆 CYBERPUNK API EDITOR")
    print("=" * 40)
    print(f"📁 Pasta da API: {API_DIR}")
    print("🌐 Abrindo navegador...")
    print("=" * 40)
    print("\n⚡ Pressione CTRL+C para parar o servidor\n")
    
    # Abre o navegador em uma thread separada após 1.5s
    threading.Timer(1.5, open_browser).start()
    
    # Inicia o servidor Flask
    app.run(debug=False, port=5000)
