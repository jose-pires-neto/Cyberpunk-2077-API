"""
Gerador de API - Cyberpunk 2077
Escaneia as pastas de imagens, lê os info.json e gera o characters.json final.
Preserva dados existentes e faz merge inteligente.
"""

import json
import os
import sys
from pathlib import Path

# Configurar saída para UTF-8 em terminais Windows
sys.stdout.reconfigure(encoding='utf-8')

# --- CONFIGURAÇÕES ---
SOURCE_DIR = "images"
OUTPUT_DIR = "docs/api/v1"

# URL base para as imagens no GitHub Pages
BASE_IMAGE_URL = "https://jose-pires-neto.github.io/Cyberpunk-2077-API/images"

VALID_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}


# --- FUNÇÕES UTILITÁRIAS ---

def get_image_list(folder_path):
    """Escaneia uma pasta e retorna lista de arquivos de imagem (sem info.json)."""
    images = []
    if not os.path.exists(folder_path):
        return images

    for filename in sorted(os.listdir(folder_path)):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
            ext = os.path.splitext(filename)[1].lower()
            if ext in VALID_EXTENSIONS:
                images.append(filename)
    return images


def get_image_urls(folder_path, images):
    """Gera URLs completas para as imagens."""
    relative_path = os.path.relpath(folder_path, SOURCE_DIR).replace("\\", "/")
    return [f"{BASE_IMAGE_URL}/{relative_path}/{img}" for img in images]


def format_name(folder_name):
    """Converte nome de pasta para nome legível."""
    return folder_name.replace("_", " ").title()


def load_existing_json(filepath):
    """Carrega JSON existente, retornando dict por nome."""
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {item['name']: item for item in data}
        except Exception as e:
            print(f"⚠️ Aviso: Erro ao ler {filepath}: {e}")
    return {}


def load_info_json(folder_path):
    """Carrega info.json de uma pasta, se existir."""
    info_path = os.path.join(folder_path, "info.json")
    if os.path.exists(info_path):
        try:
            with open(info_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"   ⚠️ Erro ao ler info.json: {e}")
    return {}


# --- SCANNER DE PERSONAGENS ---

def scan_characters():
    """Escaneia todas as pastas de personagens e gera a lista final."""
    print("🕵️  Escaneando Personagens...")
    
    # 1. Carrega dados existentes do characters.json
    existing_data = load_existing_json(f"{OUTPUT_DIR}/characters.json")
    if existing_data:
        print(f"   💾 {len(existing_data)} personagens existentes carregados")
    
    characters = []
    id_counter = 1
    
    base_path = os.path.join(SOURCE_DIR, "characters", "sex")
    
    if not os.path.exists(base_path):
        print(f"   ⚠️ Pasta {base_path} não existe!")
        return []

    # 2. Escaneia gêneros (male, female, unknown)
    for gender in ["male", "female", "unknown"]:
        gender_path = os.path.join(base_path, gender)
        
        if not os.path.exists(gender_path):
            continue
            
        for char_folder in sorted(os.listdir(gender_path)):
            char_full_path = os.path.join(gender_path, char_folder)
            
            if not os.path.isdir(char_full_path):
                continue
            
            # 3. Escaneia imagens na pasta
            images = get_image_list(char_full_path)
            image_urls = get_image_urls(char_full_path, images)
            
            # Nome formatado
            formatted_name = format_name(char_folder)
            
            # 4. Carrega info.json (dados do scraper)
            info_data = load_info_json(char_full_path)
            
            # 5. Recupera dados existentes do characters.json antigo
            old_data = existing_data.get(formatted_name, {})
            # Também tenta pelo nome do info.json
            if info_data.get('name') and info_data['name'] in existing_data:
                old_data = existing_data.get(info_data['name'], old_data)
            
            # 6. Monta o personagem com merge inteligente
            # Prioridade: info.json > dados antigos > valores default
            has_images = len(image_urls) > 0
            
            char_data = {
                "id": id_counter,
                "name": info_data.get('name') or old_data.get('name') or formatted_name,
                "gender": info_data.get('gender') or old_data.get('gender') or gender.title(),
                "directory": char_folder,
                "has_images": has_images,
                "images": image_urls,  # Sempre atualiza com scan atual
                "description": info_data.get('description') or old_data.get('description') or "Sem descrição disponível.",
                "affiliation": info_data.get('affiliation') or old_data.get('affiliation') or "Unknown",
            }
            
            # Campos opcionais
            for field in ['occupation', 'status', 'wiki_url']:
                value = info_data.get(field) or old_data.get(field)
                if value:
                    char_data[field] = value
            
            characters.append(char_data)
            id_counter += 1
    
    print(f"   ✓ {len(characters)} personagens encontrados")
    return characters


def scan_gangs():
    """Escaneia todas as gangues e gera a lista final com dados ricos."""
    print("🔫 Escaneando Gangues...")
    
    existing_data = load_existing_json(f"{OUTPUT_DIR}/gangs.json")
    
    gangs = []
    id_counter = 1
    
    base_path = os.path.join(SOURCE_DIR, "gangs")
    
    if not os.path.exists(base_path):
        print(f"   ⚠️ Pasta {base_path} não existe!")
        return []

    for gang_folder in sorted(os.listdir(base_path)):
        gang_path = os.path.join(base_path, gang_folder)
        
        if not os.path.isdir(gang_path):
            continue
        
        images = get_image_list(gang_path)
        image_urls = get_image_urls(gang_path, images)
        
        formatted_name = format_name(gang_folder)
        info_data = load_info_json(gang_path)
        old_data = existing_data.get(formatted_name, {})
        
        gang_data = {
            "id": id_counter,
            "name": info_data.get('name') or old_data.get('name') or formatted_name,
            "directory": gang_folder,
            "description": info_data.get('description') or old_data.get('description'),
            "founder": info_data.get('founder'),
            "leader": info_data.get('leader'),
            "hq": info_data.get('hq'),
            "territory": info_data.get('territory'),
            "members_count": info_data.get('members_count'),
            "affiliations": info_data.get('affiliations', []),
            "wiki_url": info_data.get('wiki_url'),
            "images": image_urls,
        }
        
        # Remove campos None
        gang_data = {k: v for k, v in gang_data.items() if v is not None}
        
        gangs.append(gang_data)
        id_counter += 1
    
    print(f"   ✓ {len(gangs)} gangues encontradas")
    return gangs


def scan_districts():
    """Escaneia todos os distritos e subdistritos."""
    print("🏙️  Escaneando Distritos...")
    
    existing_data = load_existing_json(f"{OUTPUT_DIR}/districts.json")
    
    districts = []
    id_counter = 1
    
    base_path = os.path.join(SOURCE_DIR, "districts")
    
    if not os.path.exists(base_path):
        print(f"   ⚠️ Pasta {base_path} não existe!")
        return []

    for district_folder in sorted(os.listdir(base_path)):
        district_path = os.path.join(base_path, district_folder)
        
        if not os.path.isdir(district_path):
            continue
        
        images = get_image_list(district_path)
        image_urls = get_image_urls(district_path, images)
        
        formatted_name = format_name(district_folder)
        info_data = load_info_json(district_path)
        old_data = existing_data.get(formatted_name, {})
        
        # Processa SUBDISTRITOS
        subdistricts_list = []
        subdistricts_path = os.path.join(district_path, "subdistricts")
        
        if os.path.exists(subdistricts_path):
            for sub_folder in sorted(os.listdir(subdistricts_path)):
                sub_path = os.path.join(subdistricts_path, sub_folder)
                
                if not os.path.isdir(sub_path):
                    continue
                
                sub_images = get_image_list(sub_path)
                sub_image_urls = get_image_urls(sub_path, sub_images)
                sub_info = load_info_json(sub_path)
                
                subdistrict_data = {
                    "name": sub_info.get('name') or format_name(sub_folder),
                    "description": sub_info.get('description'),
                    "wiki_url": sub_info.get('wiki_url'),
                    "images": sub_image_urls,
                }
                
                # Remove campos None
                subdistrict_data = {k: v for k, v in subdistrict_data.items() if v is not None}
                subdistricts_list.append(subdistrict_data)
        
        district_data = {
            "id": id_counter,
            "name": info_data.get('name') or old_data.get('name') or formatted_name,
            "directory": district_folder,
            "description": info_data.get('description') or old_data.get('description'),
            "danger_level": info_data.get('danger_level'),
            "wiki_url": info_data.get('wiki_url'),
            "images": image_urls,
            "subdistricts": subdistricts_list,
        }
        
        # Remove campos None (exceto subdistricts que pode ser vazio)
        district_data = {k: v for k, v in district_data.items() if v is not None or k == 'subdistricts'}
        
        districts.append(district_data)
        id_counter += 1
        
        if subdistricts_list:
            print(f"   📍 {formatted_name}: {len(subdistricts_list)} subdistrito(s)")
    
    print(f"   ✓ {len(districts)} distritos encontrados")
    return districts



# --- FUNÇÕES PRINCIPAIS ---

def save_json(path, data):
    """Salva dados em JSON formatado."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"📄 Salvo: {path} ({len(data)} itens)")


def main():
    print("\n" + "=" * 50)
    print("🌆 GERADOR DE API - CYBERPUNK 2077")
    print("=" * 50)
    
    # Garante que o diretório de saída existe (NÃO apaga!)
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    # Escaneia e salva personagens
    chars = scan_characters()
    if chars:
        save_json(f"{OUTPUT_DIR}/characters.json", chars)
    
    # Escaneia e salva gangues
    gangs = scan_gangs()
    if gangs:
        save_json(f"{OUTPUT_DIR}/gangs.json", gangs)
    
    # Escaneia e salva distritos (com subdistritos)
    districts = scan_districts()
    if districts:
        save_json(f"{OUTPUT_DIR}/districts.json", districts)
    
    print("\n✅ API atualizada com sucesso!")
    print("   Dados existentes foram preservados.")


if __name__ == "__main__":
    main()
