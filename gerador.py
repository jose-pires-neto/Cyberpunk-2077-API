import json
import os
import shutil
from pathlib import Path

# --- CONFIGURAÇÕES ---
# Onde estão suas imagens (a pasta raiz das fotos)
SOURCE_DIR = "images"

# Onde os JSONs serão salvos (para o GitHub Pages ler)
OUTPUT_DIR = "docs/api/v1"

# URL base para as imagens (IMPORTANTE: Mude isso para seu repo real)
# Se você estiver usando GitHub Pages, será algo como:
# "https://seu-usuario.github.io/seu-repositorio/images"
BASE_IMAGE_URL = "https://jose-pires-neto.github.io/Cyberpunk-2077-API//images"

# Extensões de imagem aceitas
VALID_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}

# --- FUNÇÕES UTILITÁRIAS ---

def get_image_list(folder_path, relative_path_start):
    """
    Escaneia uma pasta e retorna a lista de URLs de todas as imagens encontradas.
    """
    images = []
    if not os.path.exists(folder_path):
        return images

    # Lista arquivos e ordena para manter consistência (v01, v02...)
    for filename in sorted(os.listdir(folder_path)):
        file_path = os.path.join(folder_path, filename)
        
        # Verifica se é arquivo e se é imagem
        if os.path.isfile(file_path):
            ext = os.path.splitext(filename)[1].lower()
            if ext in VALID_EXTENSIONS:
                # Cria a URL pública baseada no caminho relativo
                # Ex: characters/sex/female/v/v01.png
                relative_path = os.path.relpath(file_path, relative_path_start)
                # Converte barras invertidas (Windows) para barras normais (Web)
                web_path = relative_path.replace("\\", "/")
                
                full_url = f"{BASE_IMAGE_URL}/{web_path}"
                images.append(full_url)
    return images

def format_name(folder_name):
    """Transforma 'johnny_silverhand' em 'Johnny Silverhand'"""
    return folder_name.replace("_", " ").title()

# --- SCANNERS DE CATEGORIA ---

def scan_characters():
    print("🕵️  Escaneando Personagens...")
    characters = []
    id_counter = 1
    
    # Caminho base: images/characters/sex
    base_path = os.path.join(SOURCE_DIR, "characters", "sex")
    
    if not os.path.exists(base_path):
        print(f"⚠️  Pasta não encontrada: {base_path}")
        return []

    # Itera sobre 'male' e 'female'
    for gender in ["male", "female"]:
        gender_path = os.path.join(base_path, gender)
        
        if os.path.exists(gender_path):
            # Itera sobre cada pasta de personagem (ex: 'v', 'judy')
            for char_folder in sorted(os.listdir(gender_path)):
                char_full_path = os.path.join(gender_path, char_folder)
                
                if os.path.isdir(char_full_path):
                    # Pega todas as imagens dentro da pasta do personagem
                    imgs = get_image_list(char_full_path, SOURCE_DIR)
                    
                    # Cria o objeto do personagem
                    char_data = {
                        "id": id_counter,
                        "name": format_name(char_folder),
                        "gender": gender.title(),
                        "directory": char_folder, # Útil para referência
                        "images": imgs,
                        # Campos extras vazios para você preencher manualmente se quiser depois,
                        # ou criar um arquivo 'meta.json' dentro da pasta de cada um.
                        "description": f"Personagem identificado em {gender}/{char_folder}",
                        "affiliation": "Unknown" 
                    }
                    
                    # Tenta ler um arquivo 'info.json' se existir dentro da pasta do personagem
                    # para pegar dados extras como descrição, role, etc.
                    meta_file = os.path.join(char_full_path, "info.json")
                    if os.path.exists(meta_file):
                        try:
                            with open(meta_file, 'r', encoding='utf-8') as f:
                                meta_data = json.load(f)
                                char_data.update(meta_data) # Mescla os dados manuais
                        except Exception as e:
                            print(f"Erro ao ler info.json de {char_folder}: {e}")

                    characters.append(char_data)
                    id_counter += 1
    
    return characters

def scan_generic_category(category_name, folder_name):
    """
    Função genérica para Gangues e Distritos (já que a estrutura é mais simples)
    Estrutura: images/{categoria}/{item_nome}/*.png
    """
    print(f"🕵️  Escaneando {category_name}...")
    items = []
    id_counter = 1
    
    base_path = os.path.join(SOURCE_DIR, folder_name)
    
    if not os.path.exists(base_path):
        print(f"⚠️  Pasta não encontrada: {base_path}")
        return []

    for item_folder in sorted(os.listdir(base_path)):
        item_full_path = os.path.join(base_path, item_folder)
        
        if os.path.isdir(item_full_path):
            imgs = get_image_list(item_full_path, SOURCE_DIR)
            
            item_data = {
                "id": id_counter,
                "name": format_name(item_folder),
                "images": imgs
            }
            
            # Checa por info.json para dados extras
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

def clean_and_create_dir(path):
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"💾 JSON Gerado: {path} ({len(data)} itens)")

def main():
    print("--- INICIANDO SCAN DA NIGHT CITY ---")
    
    # 1. Prepara pasta de saída
    clean_and_create_dir(OUTPUT_DIR)
    
    # 2. Escaneia Personagens (Estrutura Complexa: Sex/Male/Char)
    chars = scan_characters()
    save_json(f"{OUTPUT_DIR}/characters.json", chars)
    
    # 3. Escaneia Gangues (Estrutura Simples: Gangs/GangName)
    gangs = scan_generic_category("Gangues", "gangs")
    save_json(f"{OUTPUT_DIR}/gangs.json", gangs)
    
    # 4. Escaneia Distritos (Estrutura Simples: Districts/DistrictName)
    districts = scan_generic_category("Distritos", "districts")
    save_json(f"{OUTPUT_DIR}/districts.json", districts)
    
    print("\n✅ API ATUALIZADA COM SUCESSO!")
    print("Lembre-se de fazer 'git push' para atualizar as imagens e os JSONs.")

if __name__ == "__main__":
    main()