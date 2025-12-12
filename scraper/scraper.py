"""
Cyberpunk Wiki Scraper v5 - Com melhorias
- Detecção de gênero melhorada (analisa pronomes)
- Personagens sem imagens são salvos com marcação
- Suporte opcional a Playwright para mais imagens
"""

import json
import os
import re
import sys
import time
import hashlib
from pathlib import Path
from urllib.parse import urljoin, quote, unquote

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("❌ Dependências não instaladas. Execute:")
    print("   pip install requests beautifulsoup4")
    sys.exit(1)

# Tenta importar Playwright (opcional)
PLAYWRIGHT_AVAILABLE = False
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    pass


class CyberpunkScraper:
    """Scraper para a Wiki Fandom do Cyberpunk 2077."""
    
    # URLs
    API_URL = "https://cyberpunk.fandom.com/api.php"
    WIKI_URL = "https://cyberpunk.fandom.com/wiki/"
    
    # Rate limiting
    REQUEST_DELAY = 0.5
    
    # Headers
    HEADERS = {
        "User-Agent": "CyberpunkAPIBot/1.0 (Educational Project)",
        "Accept": "application/json",
    }
    
    # Categorias de personagens do CP2077
    CHARACTER_CATEGORIES = [
        "Cyberpunk 2077 Characters",
        "Cyberpunk 2077 - Phantom Liberty Characters", 
        "Cyberpunk: Edgerunners Characters",
    ]
    
    # Páginas a ignorar
    SKIP_PATTERNS = [
        "members", "list of", "category:", "template:", 
        "file:", "user:", "talk:", "minor characters"
    ]
    
    # Mapeamento de afiliações
    AFFILIATIONS = {
        "arasaka": "Arasaka",
        "militech": "Militech",
        "kang tao": "Kang Tao",
        "biotechnica": "Biotechnica",
        "trauma team": "Trauma Team",
        "netwatch": "NetWatch",
        "maelstrom": "Maelstrom",
        "tyger claws": "Tyger Claws",
        "valentinos": "Valentinos",
        "6th street": "6th Street",
        "animals": "Animals",
        "voodoo boys": "Voodoo Boys",
        "the mox": "The Mox",
        "moxes": "The Mox",
        "scavengers": "Scavengers",
        "wraiths": "Wraiths",
        "aldecaldos": "Aldecaldos",
        "barghest": "Barghest",
        "ncpd": "NCPD",
        "maxtac": "MaxTac",
        "afterlife": "Afterlife",
        "netrunner": "Netrunner",
        "fixer": "Fixer",
        "mercenary": "Mercenário",
        "solo": "Solo",
        "nomad": "Nômade",
        "rockerboy": "Rockerboy",
        "media": "Mídia",
        "corpo": "Corporação",
    }
    
    # Personagens femininos conhecidos (fallback)
    KNOWN_FEMALES = {
        "judy alvarez", "panam palmer", "alt cunningham", "rogue amendiares",
        "evelyn parker", "misty olszewski", "claire russell", "hanako arasaka",
        "regina jones", "meredith stout", "blue moon", "lizzy wizzy",
        "songbird", "alex", "alena xenakis", "ana friedman", "rita wheeler",
        "sandra dorsett", "yorinobu", "michiko arasaka", "t-bug"
    }
    
    def __init__(self, use_cache=True, use_browser=False):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        self.use_cache = use_cache
        self.use_browser = use_browser and PLAYWRIGHT_AVAILABLE
        self.cache_dir = Path("scraper/cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.stats = {"processed": 0, "success": 0, "images": 0, "skipped": 0, "no_images": 0}
        self.existing_characters = self._get_existing_characters()
        
        if self.use_browser:
            print("🌐 Modo navegador ativado (Playwright)")
        else:
            print("📡 Modo API (sem navegador)")
    
    def _get_existing_characters(self):
        """Retorna set de nomes de personagens existentes."""
        existing = set()
        base_path = Path("images/characters/sex")
        
        if not base_path.exists():
            return existing
        
        for gender_dir in ["male", "female", "unknown"]:
            gender_path = base_path / gender_dir
            if gender_path.exists():
                for char_dir in gender_path.iterdir():
                    if char_dir.is_dir():
                        existing.add(char_dir.name.lower())
                        info_path = char_dir / "info.json"
                        if info_path.exists():
                            try:
                                info = json.loads(info_path.read_text(encoding='utf-8'))
                                if info.get('name'):
                                    existing.add(info['name'].lower())
                            except:
                                pass
        
        return existing
    
    def _character_exists(self, name):
        name_safe = re.sub(r'[^\w\s-]', '', name).strip().lower().replace(' ', '_')
        return name_safe in self.existing_characters or name.lower() in self.existing_characters
    
    def _cache_key(self, data):
        return hashlib.md5(str(data).encode()).hexdigest()
    
    def _api_request(self, params, use_cache=True):
        """Faz requisição à API MediaWiki."""
        params['format'] = 'json'
        
        cache_key = self._cache_key(params)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if use_cache and self.use_cache and cache_file.exists():
            try:
                return json.loads(cache_file.read_text(encoding='utf-8'))
            except:
                pass
        
        time.sleep(self.REQUEST_DELAY)
        
        try:
            response = self.session.get(self.API_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if use_cache and self.use_cache:
                cache_file.write_text(json.dumps(data), encoding='utf-8')
            
            return data
        except Exception as e:
            print(f"    ❌ Erro API: {e}")
            return None
    
    def _should_skip_page(self, title):
        lower = title.lower()
        return any(pattern in lower for pattern in self.SKIP_PATTERNS)
    
    def get_all_characters(self, limit=None):
        """Busca todos os personagens."""
        all_members = {}
        
        for category in self.CHARACTER_CATEGORIES:
            print(f"\n📂 Categoria: {category}")
            members = self._get_category_pages(category, limit=limit)
            
            for member in members:
                title = member['title']
                if title not in all_members and not self._should_skip_page(title):
                    all_members[title] = member
                    
                    if limit and len(all_members) >= limit:
                        return list(all_members.values())
        
        return list(all_members.values())
    
    def _get_category_pages(self, category, limit=500):
        members = []
        params = {
            'action': 'query',
            'list': 'categorymembers',
            'cmtitle': f'Category:{category}',
            'cmlimit': 50,
            'cmtype': 'page'
        }
        
        cmcontinue = None
        while len(members) < (limit or 9999):
            if cmcontinue:
                params['cmcontinue'] = cmcontinue
            
            data = self._api_request(params)
            if not data or 'query' not in data:
                break
            
            for member in data['query'].get('categorymembers', []):
                if not self._should_skip_page(member['title']):
                    members.append({
                        'pageid': member['pageid'],
                        'title': member['title']
                    })
            
            if 'continue' in data:
                cmcontinue = data['continue']['cmcontinue']
            else:
                break
        
        print(f"   → {len(members)} páginas")
        return members
    
    def scrape_character(self, title):
        """Extrai informações de um personagem."""
        self.stats['processed'] += 1
        
        params = {
            'action': 'parse',
            'page': title,
            'prop': 'text|images',
            'disablelimitreport': True,
        }
        
        data = self._api_request(params)
        if not data or 'parse' not in data:
            return None
        
        parse = data['parse']
        html = parse.get('text', {}).get('*', '')
        soup = BeautifulSoup(html, 'html.parser')
        
        result = {
            'name': title,
            'gender': None,
            'affiliation': None,
            'description': None,
            'occupation': None,
            'status': None,
            'wiki_url': f"{self.WIKI_URL}{quote(title.replace(' ', '_'))}"
        }
        
        # Extrai da infobox
        infobox = soup.select_one('.portable-infobox')
        if infobox:
            result.update(self._parse_infobox(infobox))
        
        # Extrai descrição
        result['description'] = self._extract_description(soup)
        
        # === DETECÇÃO DE GÊNERO MELHORADA ===
        result['gender'] = self._detect_gender(result, soup, title)
        
        # Extrai URLs de imagens
        result['image_urls'] = self._extract_images(parse, soup, title)
        
        # Marca se tem imagens
        result['has_images'] = len(result['image_urls']) > 0
        
        if result['name'] and (result['description'] or result['has_images']):
            self.stats['success'] += 1
            if not result['has_images']:
                self.stats['no_images'] += 1
            return result
        
        return None
    
    def _detect_gender(self, char_data, soup, title):
        """Detecta gênero com múltiplas estratégias."""
        
        # 1. Primeiro tenta da infobox (já extraído)
        if char_data.get('gender') and char_data['gender'] in ['Male', 'Female']:
            return char_data['gender']
        
        # 2. Verifica lista de personagens femininos conhecidos
        if title.lower() in self.KNOWN_FEMALES:
            return 'Female'
        
        # Nome parcial
        for known in self.KNOWN_FEMALES:
            if known in title.lower() or title.lower() in known:
                return 'Female'
        
        # 3. Busca na infobox com múltiplos seletores
        infobox = soup.select_one('.portable-infobox')
        if infobox:
            # Seletores variados
            selectors = [
                '[data-source="gender"] .pi-data-value',
                '[data-source="sex"] .pi-data-value',
                '[data-source="Gender"] .pi-data-value',
                '[data-source="Sex"] .pi-data-value',
            ]
            for selector in selectors:
                elem = infobox.select_one(selector)
                if elem:
                    text = elem.get_text(strip=True).lower()
                    if 'female' in text or 'woman' in text or 'feminino' in text:
                        return 'Female'
                    elif 'male' in text or 'man' in text and 'woman' not in text or 'masculino' in text:
                        return 'Male'
            
            # Busca por texto "Gender" em qualquer lugar da infobox
            for row in infobox.select('.pi-data'):
                label = row.select_one('.pi-data-label')
                value = row.select_one('.pi-data-value')
                if label and value:
                    label_text = label.get_text(strip=True).lower()
                    if 'gender' in label_text or 'sex' in label_text:
                        value_text = value.get_text(strip=True).lower()
                        if 'female' in value_text or 'woman' in value_text:
                            return 'Female'
                        elif 'male' in value_text or 'man' in value_text:
                            return 'Male'
        
        # 4. Analisa pronomes na descrição
        desc = char_data.get('description', '') or ''
        desc_lower = desc.lower()
        
        # Conta pronomes
        female_pronouns = desc_lower.count(' she ') + desc_lower.count(' her ') + desc_lower.count(' herself ')
        male_pronouns = desc_lower.count(' he ') + desc_lower.count(' him ') + desc_lower.count(' himself ') + desc_lower.count(' his ')
        
        if female_pronouns > male_pronouns and female_pronouns >= 2:
            return 'Female'
        elif male_pronouns > female_pronouns and male_pronouns >= 2:
            return 'Male'
        
        # 5. Verifica frases específicas
        if 'grandmother' in desc_lower or 'mother of' in desc_lower or 'wife of' in desc_lower:
            return 'Female'
        if 'grandfather' in desc_lower or 'father of' in desc_lower or 'husband of' in desc_lower:
            return 'Male'
        
        return 'Unknown'
    
    def _parse_infobox(self, infobox):
        data = {}
        
        fields = {
            'gender': ['gender', 'sex', 'Gender', 'Sex'],
            'affiliation': ['affiliation', 'faction', 'gang', 'employer', 'group', 'Affiliation'],
            'occupation': ['role', 'occupation', 'profession', 'job', 'class', 'Role'],
            'status': ['status', 'state', 'Status'],
        }
        
        for key, sources in fields.items():
            for source in sources:
                elem = infobox.select_one(f'[data-source="{source}"] .pi-data-value')
                if elem:
                    value = elem.get_text(strip=True)
                    if value:
                        if key == 'gender':
                            if 'female' in value.lower() or 'woman' in value.lower():
                                value = 'Female'
                            elif 'male' in value.lower():
                                value = 'Male'
                            else:
                                value = None  # Vai para detecção avançada
                        elif key == 'affiliation':
                            value = self._normalize_affiliation(value)
                        if value:
                            data[key] = value
                        break
        
        return data
    
    def _normalize_affiliation(self, raw):
        if not raw:
            return None
        lower = raw.lower()
        for keyword, normalized in self.AFFILIATIONS.items():
            if keyword in lower:
                return normalized
        if ',' in raw:
            return raw.split(',')[0].strip()
        return raw
    
    def _extract_description(self, soup):
        for tag in soup.select('.mw-editsection, .reference, .toc, script, style, .infobox, .portable-infobox, .navbox'):
            tag.decompose()
        
        content = soup.select_one('.mw-parser-output')
        if not content:
            return None
        
        paragraphs = []
        for p in content.find_all('p', recursive=False):
            text = p.get_text(strip=True)
            text = re.sub(r'\[\d+\]', '', text)
            text = re.sub(r'\s+', ' ', text).strip()
            
            if len(text) > 80 and not text.startswith(('This article', 'See also', 'For more')):
                paragraphs.append(text)
        
        if paragraphs:
            description = ' '.join(paragraphs)
            if len(description) > 600:
                description = description[:600].rsplit(' ', 1)[0] + '...'
            return description
        
        return None
    
    def _extract_images(self, parse_data, soup, title):
        """Extrai imagens via API."""
        images = []
        
        # Imagem da infobox
        infobox_img = soup.select_one('.pi-image-thumbnail, .pi-image img, .image img')
        if infobox_img:
            src = infobox_img.get('src') or infobox_img.get('data-src')
            if src:
                cleaned = self._clean_image_url(src)
                if cleaned:
                    images.append(cleaned)
        
        # Imagens via API
        image_titles = parse_data.get('images', [])
        for img_title in image_titles[:8]:
            if any(skip in img_title.lower() for skip in ['icon', 'logo', 'button', 'arrow', 'wiki', 'transparent']):
                continue
            
            img_url = self._get_image_info(f"File:{img_title}")
            if img_url and img_url not in images:
                images.append(img_url)
        
        # Galeria
        for img in soup.select('.wikia-gallery-item img, .gallery img, .thumbimage')[:5]:
            src = img.get('src') or img.get('data-src')
            if src:
                cleaned = self._clean_image_url(src)
                if cleaned and cleaned not in images:
                    images.append(cleaned)
        
        return images[:5]
    
    def _extract_images_with_browser(self, url):
        """Extrai imagens usando navegador headless (mais imagens)."""
        if not self.use_browser:
            return []
        
        images = []
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, wait_until='networkidle')
                
                # Espera carregamento
                time.sleep(2)
                
                # Busca todas as imagens
                img_elements = page.query_selector_all('img')
                for img in img_elements:
                    src = img.get_attribute('src') or img.get_attribute('data-src')
                    if src:
                        cleaned = self._clean_image_url(src)
                        if cleaned and cleaned not in images:
                            # Filtra imagens pequenas/irrelevantes
                            if 'static.wikia.nocookie.net' in cleaned and any(ext in cleaned.lower() for ext in ['.png', '.jpg', '.jpeg']):
                                images.append(cleaned)
                
                browser.close()
        except Exception as e:
            print(f"    ⚠️ Erro no navegador: {e}")
        
        return images[:8]
    
    def _clean_image_url(self, url):
        if not url:
            return None
        
        if url.startswith('//'):
            url = 'https:' + url
        
        url = re.sub(r'/revision/latest/scale-to-width-down/\d+', '/revision/latest', url)
        url = re.sub(r'/revision/latest\?.*$', '/revision/latest', url)
        url = re.sub(r'\?cb=\d+', '', url)
        
        if not any(ext in url.lower() for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']):
            return None
        
        return url
    
    def _get_image_info(self, file_title):
        params = {
            'action': 'query',
            'titles': file_title,
            'prop': 'imageinfo',
            'iiprop': 'url',
        }
        
        data = self._api_request(params, use_cache=True)
        if not data or 'query' not in data:
            return None
        
        pages = data['query'].get('pages', {})
        for page_id, page_data in pages.items():
            if page_id == '-1':
                continue
            imageinfo = page_data.get('imageinfo', [])
            if imageinfo:
                return imageinfo[0].get('url')
        
        return None
    
    def download_image(self, url, output_path):
        try:
            if Path(output_path).exists():
                return True
            
            time.sleep(0.3)
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            return True
        except Exception as e:
            print(f"    ❌ Erro download: {e}")
            return False
    
    def process_character(self, char_data):
        """Processa um personagem: baixa imagens e salva info.json."""
        name = char_data['name']
        gender = char_data.get('gender', 'Unknown')
        
        # Determina diretório de gênero
        if gender == 'Male':
            gender_dir = 'male'
        elif gender == 'Female':
            gender_dir = 'female'
        else:
            gender_dir = 'unknown'
        
        # Nome seguro
        name_safe = re.sub(r'[^\w\s-]', '', name).strip().lower().replace(' ', '_')
        
        # Diretório
        char_dir = Path(f"images/characters/sex/{gender_dir}/{name_safe}")
        char_dir.mkdir(parents=True, exist_ok=True)
        
        # Se tem imagens, baixa
        downloaded_images = []
        if char_data.get('has_images'):
            for i, url in enumerate(char_data.get('image_urls', []), 1):
                ext = '.png'
                if '.jpg' in url.lower() or '.jpeg' in url.lower():
                    ext = '.jpg'
                elif '.webp' in url.lower():
                    ext = '.webp'
                
                filename = f"{name_safe}_{i:02d}{ext}"
                filepath = char_dir / filename
                
                if filepath.exists():
                    print(f"      📦 {filename} (cache)")
                    downloaded_images.append(filename)
                elif self.download_image(url, filepath):
                    print(f"      📷 {filename}")
                    downloaded_images.append(filename)
                    self.stats['images'] += 1
        
        # Carrega info existente
        info_path = char_dir / "info.json"
        existing_info = {}
        if info_path.exists():
            try:
                existing_info = json.loads(info_path.read_text(encoding='utf-8'))
            except:
                pass
        
        # Monta info.json
        new_info = {
            "name": char_data['name'],
            "gender": gender,
            "affiliation": char_data.get('affiliation') or existing_info.get('affiliation') or "Unknown",
            "description": existing_info.get('description') or char_data.get('description') or "Sem descrição disponível.",
            "has_images": len(downloaded_images) > 0,
            "wiki_url": char_data.get('wiki_url', ""),
        }
        
        if char_data.get('occupation'):
            new_info['occupation'] = char_data['occupation']
        if char_data.get('status'):
            new_info['status'] = char_data['status']
        
        # Salva info.json
        info_path.write_text(json.dumps(new_info, indent=2, ensure_ascii=False), encoding='utf-8')
        
        return {
            'directory': name_safe,
            'gender_dir': gender_dir,
            'images_downloaded': len(downloaded_images),
            'has_images': len(downloaded_images) > 0,
            'info': new_info
        }
    
    def scrape_all(self, limit=None, skip_existing=True):
        """Raspa todos os personagens."""
        print("\n" + "=" * 60)
        print("🌆 CYBERPUNK WIKI SCRAPER v5")
        print("    Detecção de gênero melhorada + marcação sem imagem")
        print("=" * 60)
        
        if skip_existing:
            print(f"\n📦 {len(self.existing_characters)} personagens já existem")
        
        print("\n📋 Buscando personagens...")
        members = self.get_all_characters(limit=limit)
        print(f"\n   Total: {len(members)} personagens na Wiki")
        
        if skip_existing:
            new_members = [m for m in members if not self._character_exists(m['title'])]
            print(f"   📥 {len(new_members)} novos para baixar")
            print(f"   ⏭️  {len(members) - len(new_members)} já existem")
            members = new_members
        
        processed = []
        for i, member in enumerate(members, 1):
            title = member['title']
            print(f"\n[{i}/{len(members)}] {title}")
            
            char_data = self.scrape_character(title)
            if not char_data:
                print("   ⚠️ Sem dados, pulando...")
                self.stats['skipped'] += 1
                continue
            
            result = self.process_character(char_data)
            processed.append(result)
            
            gender = char_data.get('gender', '?')
            aff = char_data.get('affiliation', '-')
            imgs = result['images_downloaded']
            has_img = "✓" if result['has_images'] else "⚠️"
            print(f"   {has_img} {char_data['name']} | {gender} | {aff} | {imgs} img(s)")
        
        # Estatísticas
        print("\n" + "=" * 60)
        print("📊 ESTATÍSTICAS")
        print(f"   Processados: {self.stats['processed']}")
        print(f"   Sucesso: {self.stats['success']}")
        print(f"   Sem imagens: {self.stats['no_images']}")
        print(f"   Imagens baixadas: {self.stats['images']}")
        print("\n✅ Execute 'python gerador.py' para atualizar characters.json")
        
        return processed


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Scraper Wiki Cyberpunk 2077 v5')
    parser.add_argument('--limit', type=int, default=None, help='Limite de personagens (default: sem limite)')
    parser.add_argument('--no-cache', action='store_true', help='Desabilita cache')
    parser.add_argument('--browser', action='store_true', help='Usa navegador para mais imagens')
    parser.add_argument('--all', action='store_true', help='Baixa todos os personagens (inclui existentes)')
    
    args = parser.parse_args()
    
    if args.browser and not PLAYWRIGHT_AVAILABLE:
        print("⚠️ Playwright não instalado. Execute:")
        print("   pip install playwright")
        print("   playwright install chromium")
        print("\nContinuando sem navegador...\n")
    
    scraper = CyberpunkScraper(
        use_cache=not args.no_cache,
        use_browser=args.browser
    )
    scraper.scrape_all(limit=args.limit, skip_existing=not args.all)


if __name__ == '__main__':
    main()
