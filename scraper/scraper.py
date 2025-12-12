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


# =============================================================================
# GANGS SCRAPER
# =============================================================================

class GangsScraper:
    """Scraper para gangues do Cyberpunk 2077 - Dados Ricos."""
    
    API_URL = "https://cyberpunk.fandom.com/api.php"
    WIKI_URL = "https://cyberpunk.fandom.com/wiki/"
    REQUEST_DELAY = 0.5
    
    HEADERS = {
        "User-Agent": "CyberpunkAPIBot/1.0 (Educational Project)",
        "Accept": "text/html,application/xhtml+xml,application/xml",
    }
    
    # Lista de gangues conhecidas do CP2077
    GANGS = [
        "6th Street",
        "Animals",
        "Barghest",
        "Maelstrom",
        "Moxes",
        "Scavengers",
        "Tyger Claws",
        "Valentinos",
        "Voodoo Boys",
        "Wraiths",
        "Aldecaldos",
        "Raffens",
    ]
    
    def __init__(self, use_cache=True):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        self.use_cache = use_cache
        self.cache_dir = Path("scraper/cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.stats = {"processed": 0, "success": 0, "images": 0}
    
    def _fetch_page(self, url):
        """Busca página HTML diretamente."""
        cache_key = hashlib.md5(url.encode()).hexdigest()
        cache_file = self.cache_dir / f"gang_page_{cache_key}.html"
        
        if self.use_cache and cache_file.exists():
            try:
                return cache_file.read_text(encoding='utf-8')
            except:
                pass
        
        time.sleep(self.REQUEST_DELAY)
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            html = response.text
            if self.use_cache:
                cache_file.write_text(html, encoding='utf-8')
            return html
        except Exception as e:
            print(f"    ❌ Erro fetch: {e}")
            return None
    
    def scrape_gang(self, gang_name):
        """Extrai informações ricas de uma gangue."""
        self.stats['processed'] += 1
        
        # Monta URL
        page_url = f"{self.WIKI_URL}{quote(gang_name.replace(' ', '_'))}"
        
        html = self._fetch_page(page_url)
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        
        result = {
            'name': gang_name,
            'description': None,
            'territory': None,
            'hq': None,
            'founder': None,
            'leader': None,
            'members_count': None,
            'affiliations': [],
            'wiki_url': page_url
        }
        
        # 1. Descrição da meta tag OG (mais limpa)
        og_desc = soup.select_one('meta[property="og:description"]')
        if og_desc:
            desc = og_desc.get('content', '')
            if desc and len(desc) > 30:
                result['description'] = desc
        
        # 2. Extrai da infobox (dados ricos)
        infobox = soup.select_one('.portable-infobox')
        if infobox:
            # Founder
            founder_elem = infobox.select_one('[data-source="founder"] .pi-data-value, [data-source="founders"] .pi-data-value')
            if founder_elem:
                result['founder'] = self._clean_text(founder_elem.get_text())
            
            # Leadership / Leader
            leader_elem = infobox.select_one('[data-source="leadership"] .pi-data-value, [data-source="leader"] .pi-data-value')
            if leader_elem:
                result['leader'] = self._clean_text(leader_elem.get_text())
            
            # HQ
            hq_elem = infobox.select_one('[data-source="hq"] .pi-data-value, [data-source="headquarters"] .pi-data-value')
            if hq_elem:
                result['hq'] = self._clean_text(hq_elem.get_text())
            
            # Location/Territory
            loc_elem = infobox.select_one('[data-source="location"] .pi-data-value, [data-source="locations"] .pi-data-value, [data-source="territory"] .pi-data-value')
            if loc_elem:
                result['territory'] = self._clean_text(loc_elem.get_text())
            
            # Members count
            members_elem = infobox.select_one('[data-source="members"] .pi-data-value, [data-source="number"] .pi-data-value')
            if members_elem:
                members_text = members_elem.get_text(strip=True)
                # Extrai número
                match = re.search(r'[\d,\.]+', members_text.replace(',', ''))
                if match:
                    result['members_count'] = match.group()
            
            # Affiliations
            aff_elem = infobox.select_one('[data-source="affiliation"] .pi-data-value, [data-source="affiliations"] .pi-data-value')
            if aff_elem:
                affs = [self._clean_text(a.get_text()) for a in aff_elem.find_all('a')]
                result['affiliations'] = [a for a in affs if a and len(a) > 1]
        
        # 3. Fallback: descrição do primeiro parágrafo se OG não tiver
        if not result['description']:
            content = soup.select_one('.mw-parser-output')
            if content:
                for p in content.find_all('p', recursive=False)[:3]:
                    text = p.get_text(strip=True)
                    text = re.sub(r'\[\d+\]', '', text)
                    if len(text) > 80:
                        result['description'] = text[:600] + '...' if len(text) > 600 else text
                        break
        
        # 4. Busca imagens da galeria
        gallery_url = f"{page_url}/Gallery"
        result['image_urls'] = self._scrape_gallery(gallery_url)
        
        # Se não tem galeria, tenta infobox
        if not result['image_urls']:
            result['image_urls'] = self._extract_infobox_images(soup)
        
        result['has_images'] = len(result['image_urls']) > 0
        
        if result['description']:
            self.stats['success'] += 1
        
        return result
    
    def _clean_text(self, text):
        """Limpa texto removendo referências e espaços extras."""
        if not text:
            return None
        text = re.sub(r'\[\d+\]', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip() or None
    
    def _scrape_gallery(self, gallery_url):
        """Busca imagens da página de galeria, priorizando concept art e screenshots."""
        images = []
        
        html = self._fetch_page(gallery_url)
        if not html:
            return images
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Busca todas as imagens com data-image-key
        all_imgs = soup.select('img[data-image-key]')
        
        # Separa logos de outras imagens (concept art, screenshots, etc)
        other_images = []
        logo_images = []
        
        for img in all_imgs:
            img_name = (img.get('data-image-key') or img.get('alt') or '').lower()
            src = img.get('src') or img.get('data-src')
            
            if not src:
                continue
            
            cleaned = self._clean_image_url(src)
            if not cleaned or cleaned in images:
                continue
            
            # Logos vão por último
            if 'logo' in img_name or 'decal' in img_name:
                logo_images.append(cleaned)
            else:
                other_images.append(cleaned)
        
        # Prioriza imagens que NÃO são logos (concept art, screenshots)
        images = other_images[:6]  # Até 6 imagens de concept/screenshots
        
        # Adiciona logos se necessário para completar
        remaining = 8 - len(images)
        if remaining > 0:
            images.extend(logo_images[:remaining])
        
        return images

    
    def _extract_infobox_images(self, soup):
        """Extrai imagem da infobox como fallback."""
        images = []
        
        infobox_img = soup.select_one('.pi-image-thumbnail, .pi-image img')
        if infobox_img:
            src = infobox_img.get('src') or infobox_img.get('data-src')
            if src:
                cleaned = self._clean_image_url(src)
                if cleaned:
                    images.append(cleaned)
        
        return images
    
    def _clean_image_url(self, url):
        if not url:
            return None
        if url.startswith('//'):
            url = 'https:' + url
        # Remove resize params para pegar imagem full
        url = re.sub(r'/revision/latest/scale-to-width-down/\d+', '/revision/latest', url)
        url = re.sub(r'/revision/latest/smart/.*?\?', '/revision/latest?', url)
        url = re.sub(r'\?cb=\d+.*$', '', url)
        if not any(ext in url.lower() for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']):
            return None
        return url
    
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
    
    def process_gang(self, gang_data):
        """Processa uma gangue: baixa imagens e salva info.json."""
        name = gang_data['name']
        name_safe = re.sub(r'[^\w\s-]', '', name).strip().lower().replace(' ', '_')
        
        gang_dir = Path(f"images/gangs/{name_safe}")
        gang_dir.mkdir(parents=True, exist_ok=True)
        
        downloaded_images = []
        for i, url in enumerate(gang_data.get('image_urls', []), 1):
            ext = '.png' if '.png' in url.lower() else '.jpg'
            filename = f"{name_safe}_{i:02d}{ext}"
            filepath = gang_dir / filename
            
            if filepath.exists() or self.download_image(url, filepath):
                downloaded_images.append(filename)
                self.stats['images'] += 1
        
        # Salva info.json com TODOS os campos
        info = {
            "name": gang_data['name'],
            "description": gang_data.get('description') or "Sem descrição disponível.",
            "territory": gang_data.get('territory'),
            "hq": gang_data.get('hq'),
            "founder": gang_data.get('founder'),
            "leader": gang_data.get('leader'),
            "members_count": gang_data.get('members_count'),
            "affiliations": gang_data.get('affiliations', []),
            "wiki_url": gang_data.get('wiki_url'),
            "has_images": len(downloaded_images) > 0,
        }
        
        info_path = gang_dir / "info.json"
        info_path.write_text(json.dumps(info, indent=2, ensure_ascii=False), encoding='utf-8')
        
        return {'name': name, 'images': len(downloaded_images)}
    
    def scrape_all(self):
        """Raspa todas as gangues."""
        print("\n" + "=" * 60)
        print("🔫 GANGS SCRAPER - CYBERPUNK 2077")
        print("=" * 60)
        
        for i, gang_name in enumerate(self.GANGS, 1):
            print(f"\n[{i}/{len(self.GANGS)}] {gang_name}")
            
            gang_data = self.scrape_gang(gang_name)
            if not gang_data:
                print("   ⚠️ Sem dados")
                continue
            
            result = self.process_gang(gang_data)
            print(f"   ✓ {result['name']} | {result['images']} img(s)")
        
        print("\n" + "=" * 60)
        print("📊 ESTATÍSTICAS")
        print(f"   Processadas: {self.stats['processed']}")
        print(f"   Sucesso: {self.stats['success']}")
        print(f"   Imagens: {self.stats['images']}")
        print("\n✅ Execute 'python gerador.py' para atualizar gangs.json")


# =============================================================================
# DISTRICTS SCRAPER
# =============================================================================

class DistrictsScraper:
    """Scraper para distritos do Cyberpunk 2077 - Dados Ricos."""
    
    WIKI_URL = "https://cyberpunk.fandom.com/wiki/"
    REQUEST_DELAY = 0.5
    
    HEADERS = {
        "User-Agent": "CyberpunkAPIBot/1.0 (Educational Project)",
        "Accept": "text/html,application/xhtml+xml,application/xml",
    }
    
    # Distritos de Night City - NOMES CORRETOS DA WIKI
    DISTRICTS = [
        ("Watson (2077)", "Watson"),
        ("Westbrook (2077)", "Westbrook"),
        ("City Center (2077)", "City Center"),
        ("Heywood (2077)", "Heywood"),
        ("Pacifica (2077)", "Pacifica"),
        ("Santo Domingo (2077)", "Santo Domingo"),
        ("Badlands", "Badlands"),
        ("Dogtown", "Dogtown"),
    ]
    
    def __init__(self, use_cache=True):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        self.use_cache = use_cache
        self.cache_dir = Path("scraper/cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.stats = {"processed": 0, "success": 0, "images": 0}
    
    def _fetch_page(self, url):
        """Busca página HTML diretamente."""
        cache_key = hashlib.md5(url.encode()).hexdigest()
        cache_file = self.cache_dir / f"district_page_{cache_key}.html"
        
        if self.use_cache and cache_file.exists():
            try:
                return cache_file.read_text(encoding='utf-8')
            except:
                pass
        
        time.sleep(self.REQUEST_DELAY)
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            html = response.text
            if self.use_cache:
                cache_file.write_text(html, encoding='utf-8')
            return html
        except Exception as e:
            print(f"    ❌ Erro fetch: {e}")
            return None
    
    def scrape_district(self, wiki_name, display_name):
        """Extrai informações ricas de um distrito."""
        self.stats['processed'] += 1
        
        page_url = f"{self.WIKI_URL}{quote(wiki_name.replace(' ', '_'))}"
        
        html = self._fetch_page(page_url)
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        
        result = {
            'name': display_name,
            'wiki_name': wiki_name,
            'description': None,
            'subdistricts': [],
            'subdistrict_data': [],  # Dados detalhados dos subdistritos
            'danger_level': None,
            'wiki_url': page_url
        }
        
        # 1. Descrição da meta tag OG
        og_desc = soup.select_one('meta[property="og:description"]')
        if og_desc:
            desc = og_desc.get('content', '')
            if desc and len(desc) > 30:
                result['description'] = desc
        
        # 2. Extrai da infobox (danger level)
        infobox = soup.select_one('.portable-infobox')
        if infobox:
            # Danger level
            danger_elem = infobox.select_one('[data-source="danger"] .pi-data-value, [data-source="threat"] .pi-data-value')
            if danger_elem:
                result['danger_level'] = self._clean_text(danger_elem.get_text())
        
        # 3. Busca Subdistritos da SEÇÃO "Sub-districts" na página
        content = soup.select_one('.mw-parser-output')
        if content:
            # Encontra header h2 "Sub-districts" e pega os links que vêm depois
            for header in content.find_all(['h2', 'h3']):
                header_text = header.get_text(strip=True).lower()
                if 'sub-district' in header_text or 'subdistrict' in header_text:
                    # Busca próximo elemento ul ou div com links
                    next_sibling = header.find_next_sibling()
                    while next_sibling:
                        # Para quando chegar no próximo h2
                        if next_sibling.name in ['h2']:
                            break
                        
                        # Busca links de subdistritos
                        if next_sibling.name in ['ul', 'div', 'p']:
                            for a in next_sibling.find_all('a'):
                                href = a.get('href', '')
                                name = self._clean_text(a.get_text())
                                if name and '/wiki/' in href and name not in ['edit', 'Edit']:
                                    wiki_page = href.split('/wiki/')[-1]
                                    # Evita duplicatas
                                    if not any(s['name'] == name for s in result['subdistricts']):
                                        result['subdistricts'].append({
                                            'name': name,
                                            'wiki_page': wiki_page
                                        })
                        
                        next_sibling = next_sibling.find_next_sibling()
                    break  # Encontrou a seção, para de procurar
        
        # 4. Fallback: descrição do primeiro parágrafo
        if not result['description'] and content:
            for p in content.find_all('p', recursive=False)[:3]:
                text = p.get_text(strip=True)
                text = re.sub(r'\[\d+\]', '', text)
                if len(text) > 80:
                    result['description'] = text[:600] + '...' if len(text) > 600 else text
                    break
        
        # 5. Busca imagens da PRÓPRIA PÁGINA
        result['image_urls'] = self._extract_page_images(soup)
        result['has_images'] = len(result['image_urls']) > 0
        
        if result['description']:
            self.stats['success'] += 1
        
        return result

    
    def scrape_subdistrict(self, wiki_page, display_name):
        """Raspa informações de um subdistrito."""
        page_url = f"{self.WIKI_URL}{quote(wiki_page)}"
        
        html = self._fetch_page(page_url)
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        
        result = {
            'name': display_name,
            'wiki_page': wiki_page,
            'description': None,
            'wiki_url': page_url
        }
        
        # Descrição da meta tag OG
        og_desc = soup.select_one('meta[property="og:description"]')
        if og_desc:
            desc = og_desc.get('content', '')
            if desc and len(desc) > 30:
                result['description'] = desc
        
        # Fallback: primeiro parágrafo
        if not result['description']:
            content = soup.select_one('.mw-parser-output')
            if content:
                for p in content.find_all('p', recursive=False)[:3]:
                    text = p.get_text(strip=True)
                    text = re.sub(r'\[\d+\]', '', text)
                    if len(text) > 50:
                        result['description'] = text[:500] + '...' if len(text) > 500 else text
                        break
        
        # Imagens
        result['image_urls'] = self._extract_page_images(soup)
        result['has_images'] = len(result['image_urls']) > 0
        
        return result


    
    def _clean_text(self, text):
        if not text:
            return None
        text = re.sub(r'\[\d+\]', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip() or None
    
    def _extract_page_images(self, soup):
        """Extrai todas as imagens relevantes da página do distrito."""
        images = []
        
        # Busca todas as imagens com data-image-key na página
        all_imgs = soup.select('img[data-image-key]')
        
        for img in all_imgs:
            img_name = (img.get('data-image-key') or '').lower()
            src = img.get('src') or img.get('data-src')
            
            if not src:
                continue
            
            # Ignora ícones pequenos, logos de navegação, etc
            if any(skip in img_name for skip in ['icon', 'logo', 'button', 'nav', 'footer', 'header']):
                continue
            
            cleaned = self._clean_image_url(src)
            if cleaned and cleaned not in images:
                images.append(cleaned)
        
        return images[:10]  # Max 10 imagens por distrito



    
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
    
    def process_district(self, district_data):
        """Processa um distrito: baixa imagens e salva info.json."""
        name = district_data['name']
        name_safe = re.sub(r'[^\w\s-]', '', name).strip().lower().replace(' ', '_')
        
        district_dir = Path(f"images/districts/{name_safe}")
        district_dir.mkdir(parents=True, exist_ok=True)
        
        downloaded_images = []
        for i, url in enumerate(district_data.get('image_urls', []), 1):
            ext = '.png' if '.png' in url.lower() else '.jpg'
            filename = f"{name_safe}_{i:02d}{ext}"
            filepath = district_dir / filename
            
            if filepath.exists() or self.download_image(url, filepath):
                downloaded_images.append(filename)
                self.stats['images'] += 1
        
        # Prepara lista de nomes de subdistritos para o JSON
        subdistrict_names = [s['name'] for s in district_data.get('subdistricts', [])]
        
        # Salva info.json do DISTRITO
        info = {
            "name": district_data['name'],
            "description": district_data.get('description') or "Sem descrição disponível.",
            "subdistricts": subdistrict_names,
            "danger_level": district_data.get('danger_level'),
            "wiki_url": district_data.get('wiki_url'),
            "has_images": len(downloaded_images) > 0,
        }
        
        info_path = district_dir / "info.json"
        info_path.write_text(json.dumps(info, indent=2, ensure_ascii=False), encoding='utf-8')
        
        return {'name': name, 'images': len(downloaded_images), 'district_dir': district_dir}
    
    def process_subdistrict(self, subdistrict_data, district_dir):
        """Processa um subdistrito: baixa imagens e salva info.json."""
        name = subdistrict_data['name']
        name_safe = re.sub(r'[^\w\s-]', '', name).strip().lower().replace(' ', '_')
        
        # Cria pasta subdistricts/{nome}
        sub_dir = district_dir / "subdistricts" / name_safe
        sub_dir.mkdir(parents=True, exist_ok=True)
        
        downloaded_images = []
        for i, url in enumerate(subdistrict_data.get('image_urls', []), 1):
            ext = '.png' if '.png' in url.lower() else '.jpg'
            filename = f"{name_safe}_{i:02d}{ext}"
            filepath = sub_dir / filename
            
            if filepath.exists() or self.download_image(url, filepath):
                downloaded_images.append(filename)
                self.stats['images'] += 1
        
        # Salva info.json do SUBDISTRITO
        info = {
            "name": subdistrict_data['name'],
            "description": subdistrict_data.get('description') or "Sem descrição disponível.",
            "wiki_url": subdistrict_data.get('wiki_url'),
            "has_images": len(downloaded_images) > 0,
        }
        
        info_path = sub_dir / "info.json"
        info_path.write_text(json.dumps(info, indent=2, ensure_ascii=False), encoding='utf-8')
        
        return {'name': name, 'images': len(downloaded_images)}
    
    def scrape_all(self):
        """Raspa todos os distritos e seus subdistritos."""
        print("\n" + "=" * 60)
        print("🏙️  DISTRICTS SCRAPER - CYBERPUNK 2077")
        print("=" * 60)
        
        for i, (wiki_name, display_name) in enumerate(self.DISTRICTS, 1):
            print(f"\n[{i}/{len(self.DISTRICTS)}] {display_name}")
            
            district_data = self.scrape_district(wiki_name, display_name)
            if not district_data:
                print("   ⚠️ Sem dados")
                continue
            
            result = self.process_district(district_data)
            print(f"   ✓ {result['name']} | {result['images']} img(s)")
            
            # Raspa SUBDISTRITOS
            subdistricts = district_data.get('subdistricts', [])
            if subdistricts:
                print(f"   📍 {len(subdistricts)} subdistrito(s)")
                
                for j, sub_info in enumerate(subdistricts, 1):
                    sub_name = sub_info['name']
                    sub_wiki = sub_info['wiki_page']
                    
                    print(f"      [{j}/{len(subdistricts)}] {sub_name}...", end=" ")
                    
                    sub_data = self.scrape_subdistrict(sub_wiki, sub_name)
                    if sub_data:
                        sub_result = self.process_subdistrict(sub_data, result['district_dir'])
                        print(f"✓ {sub_result['images']} img(s)")
                    else:
                        print("⚠️ Sem dados")
        
        print("\n" + "=" * 60)
        print("📊 ESTATÍSTICAS")
        print(f"   Processados: {self.stats['processed']}")
        print(f"   Sucesso: {self.stats['success']}")
        print(f"   Imagens: {self.stats['images']}")
        print("\n✅ Execute 'python gerador.py' para atualizar districts.json")




# =============================================================================
# MENU INTERATIVO
# =============================================================================

def show_menu():
    """Exibe menu interativo no terminal."""
    print("\n" + "=" * 60)
    print("🌆 CYBERPUNK 2077 - SCRAPER v6")
    print("=" * 60)
    print("\nEscolha o que deseja raspar:\n")
    print("  [1] 👤 Personagens")
    print("  [2] 🔫 Gangues")
    print("  [3] 🏙️  Distritos")
    print("  [4] 📦 Todos (Personagens + Gangues + Distritos)")
    print("  [0] ❌ Sair")
    print()
    
    return input("Digite sua opção: ").strip()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Scraper Wiki Cyberpunk 2077 v6')
    parser.add_argument('--limit', type=int, default=None, help='Limite de itens (default: sem limite)')
    parser.add_argument('--no-cache', action='store_true', help='Desabilita cache')
    parser.add_argument('--browser', action='store_true', help='Usa navegador para mais imagens')
    parser.add_argument('--all', action='store_true', help='Baixa todos (inclui existentes)')
    parser.add_argument('--menu', action='store_true', help='Mostra menu interativo')
    parser.add_argument('--category', choices=['characters', 'gangs', 'districts', 'all'], 
                        help='Categoria para raspar (pula menu)')
    
    args = parser.parse_args()
    
    use_cache = not args.no_cache
    
    # Se passou categoria via argumento, executa direto
    if args.category:
        if args.category in ['characters', 'all']:
            scraper = CyberpunkScraper(use_cache=use_cache, use_browser=args.browser)
            scraper.scrape_all(limit=args.limit, skip_existing=not args.all)
        if args.category in ['gangs', 'all']:
            gangs = GangsScraper(use_cache=use_cache)
            gangs.scrape_all()
        if args.category in ['districts', 'all']:
            districts = DistrictsScraper(use_cache=use_cache)
            districts.scrape_all()
        return
    
    # Menu interativo
    while True:
        choice = show_menu()
        
        if choice == '0':
            print("\n👋 Até mais, Samurai!")
            break
        
        elif choice == '1':
            print("\n👤 Raspando PERSONAGENS...")
            scraper = CyberpunkScraper(use_cache=use_cache, use_browser=args.browser)
            scraper.scrape_all(limit=args.limit, skip_existing=not args.all)
        
        elif choice == '2':
            print("\n🔫 Raspando GANGUES...")
            gangs = GangsScraper(use_cache=use_cache)
            gangs.scrape_all()
        
        elif choice == '3':
            print("\n🏙️  Raspando DISTRITOS...")
            districts = DistrictsScraper(use_cache=use_cache)
            districts.scrape_all()
        
        elif choice == '4':
            print("\n📦 Raspando TODOS...")
            scraper = CyberpunkScraper(use_cache=use_cache, use_browser=args.browser)
            scraper.scrape_all(limit=args.limit, skip_existing=not args.all)
            gangs = GangsScraper(use_cache=use_cache)
            gangs.scrape_all()
            districts = DistrictsScraper(use_cache=use_cache)
            districts.scrape_all()
        
        else:
            print("\n⚠️ Opção inválida!")
        
        input("\n🔄 Pressione ENTER para voltar ao menu...")


if __name__ == '__main__':
    main()

