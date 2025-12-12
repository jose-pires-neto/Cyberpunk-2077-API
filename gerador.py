import json
import os
import shutil
import sys
from pathlib import Path

# Configurar saída para UTF-8 em terminais Windows
sys.stdout.reconfigure(encoding='utf-8')

# --- CONFIGURAÇÕES ---
SOURCE_DIR = "images"
OUTPUT_DIR = "docs/api/v1"

# URL base para as imagens (Mude para seu repo real)
BASE_IMAGE_URL = "https://jose-pires-neto.github.io/Cyberpunk-2077-API/images"

VALID_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}

# --- FUNÇÕES UTILITÁRIAS ---

def get_image_list(folder_path, relative_path_start):
    """Escaneia uma pasta e retorna URLs das imagens."""
    images = []
    if not os.path.exists(folder_path):
        return images

    for filename in sorted(os.listdir(folder_path)):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
            ext = os.path.splitext(filename)[1].lower()
            if ext in VALID_EXTENSIONS:
                relative_path = os.path.relpath(file_path, relative_path_start)
                web_path = relative_path.replace("\\", "/")
                full_url = f"{BASE_IMAGE_URL}/{web_path}"
                images.append(full_url)
    return images

def format_name(folder_name):
    return folder_name.replace("_", " ").title()

def load_existing_data(filepath):
    """
    Lê o JSON atual (se existir) para não perder suas edições manuais
    ao rodar o script novamente.
    """
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Cria um dicionário onde a chave é o nome para busca rápida
                # Ex: { "V": { ...dados... }, "Judy": { ...dados... } }
                return {item['name']: item for item in data}
        except Exception as e:
            print(f"⚠️ Aviso: Não foi possível ler dados antigos de {filepath}: {e}")
    return {}

# --- SCANNERS ---

def scan_characters(legacy_data):
    print("🕵️  Escaneando Personagens...")
    characters = []
    id_counter = 1
    
    base_path = os.path.join(SOURCE_DIR, "characters", "sex")
    
    if not os.path.exists(base_path):
        return []

    for gender in ["male", "female"]:
        gender_path = os.path.join(base_path, gender)
        
        if os.path.exists(gender_path):
            for char_folder in sorted(os.listdir(gender_path)):
                char_full_path = os.path.join(gender_path, char_folder)
                
                if os.path.isdir(char_full_path):
                    imgs = get_image_list(char_full_path, SOURCE_DIR)
                    name = format_name(char_folder)
                    
                    # 1. Cria dados básicos do scan
                    char_data = {
                        "id": id_counter,
                        "name": name,
                        "gender": gender.title(),
                        "directory": char_folder,
                        "images": imgs, # As imagens são sempre atualizadas pelo scan
                        "description": "Edite este campo no JSON ou use info.json", # Default
                        "affiliation": "Unknown"
                    }

                    # 2. RECUPERAÇÃO: Se já existia dados deste personagem, restaura os textos
                    if name in legacy_data:
                        old_item = legacy_data[name]
                        # Atualiza char_data com os campos antigos, exceto imagens e id
                        # Assim preservamos a descrição, status, role, etc.
                        for key, value in old_item.items():
                            if key not in ['images', 'directory', 'gender']: 
                                char_data[key] = value

                    # 3. OVERRIDE: Se tiver info.json na pasta, ele tem prioridade máxima
                    meta_file = os.path.join(char_full_path, "info.json")
                    if os.path.exists(meta_file):
                        try:
                            with open(meta_file, 'r', encoding='utf-8') as f:
                                meta_data = json.load(f)
                                char_data.update(meta_data)
                        except:
                            pass

                    characters.append(char_data)
                    id_counter += 1
    
    return characters

def scan_generic_category(category_name, folder_name, legacy_data):
    print(f"🕵️  Escaneando {category_name}...")
    items = []
    id_counter = 1
    
    base_path = os.path.join(SOURCE_DIR, folder_name)
    
    if not os.path.exists(base_path):
        return []

    for item_folder in sorted(os.listdir(base_path)):
        item_full_path = os.path.join(base_path, item_folder)
        
        if os.path.isdir(item_full_path):
            imgs = get_image_list(item_full_path, SOURCE_DIR)
            name = format_name(item_folder)
            
            item_data = {
                "id": id_counter,
                "name": name,
                "images": imgs
            }
            
            # Recupera dados antigos (descrições manuais)
            if name in legacy_data:
                old_item = legacy_data[name]
                for key, value in old_item.items():
                    if key not in ['images']:
                        item_data[key] = value

            # Checa info.json
            meta_file = os.path.join(item_full_path, "info.json")
            if os.path.exists(meta_file):
                try:
                    with open(meta_file, 'r', encoding='utf-8') as f:
                        meta_data = json.load(f)
                        item_data.update(meta_data)
                except:
                    pass

            items.append(item_data)
            id_counter += 1
            
    return items

# --- BUILDER PRINCIPAL ---

def main():
    print("--- INICIANDO SCAN DA NIGHT CITY (MODO SEGURO) ---")
    
    # 1. Carregar dados existentes ANTES de limpar a pasta
    # Isso garante que edições manuais nos JSONs antigos não sejam perdidas
    old_chars = load_existing_data(f"{OUTPUT_DIR}/characters.json")
    old_gangs = load_existing_data(f"{OUTPUT_DIR}/gangs.json")
    old_districts = load_existing_data(f"{OUTPUT_DIR}/districts.json")
    
    if old_chars: print(f"💾 Memória recuperada: {len(old_chars)} personagens antigos.")

    # 2. Limpar e recriar pasta de saída
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR)
    
    # 3. Rodar Scans passando os dados antigos para fusão
    chars = scan_characters(old_chars)
    save_json(f"{OUTPUT_DIR}/characters.json", chars)
    
    gangs = scan_generic_category("Gangues", "gangs", old_gangs)
    save_json(f"{OUTPUT_DIR}/gangs.json", gangs)
    
    districts = scan_generic_category("Distritos", "districts", old_districts)
    save_json(f"{OUTPUT_DIR}/districts.json", districts)
    
    print("\n✅ API ATUALIZADA! Suas descrições manuais foram preservadas.")

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"📄 Arquivo salvo: {path}")

if __name__ == "__main__":
    main()