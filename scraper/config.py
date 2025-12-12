"""
Configurações do Scraper - Cyberpunk Wiki Fandom
"""

# URLs Base
WIKI_BASE_URL = "https://cyberpunk.fandom.com"
WIKI_LANG = "pt-br"  # Pode ser "en" para inglês

# URLs de Categorias
CATEGORIES = {
    "characters": f"{WIKI_BASE_URL}/{WIKI_LANG}/wiki/Categoria:Personagens_de_Cyberpunk_2077",
    "gangs": f"{WIKI_BASE_URL}/{WIKI_LANG}/wiki/Categoria:Gangues",
    "districts": f"{WIKI_BASE_URL}/{WIKI_LANG}/wiki/Categoria:Locais",
    "corporations": f"{WIKI_BASE_URL}/{WIKI_LANG}/wiki/Categoria:Corporações",
}

# Fallback para inglês (mais completo)
CATEGORIES_EN = {
    "characters": f"{WIKI_BASE_URL}/wiki/Category:Cyberpunk_2077_characters",
    "gangs": f"{WIKI_BASE_URL}/wiki/Category:Gangs",
    "districts": f"{WIKI_BASE_URL}/wiki/Category:Locations",
    "corporations": f"{WIKI_BASE_URL}/wiki/Category:Corporations",
}

# Rate Limiting (segundos entre requisições)
REQUEST_DELAY = 1.5

# Diretórios de saída
OUTPUT_DIR = "images"
CACHE_DIR = "scraper/cache"
JSON_OUTPUT_DIR = "docs/api/v1"

# Headers para simular navegador
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
}

# Mapeamento de afiliações conhecidas
AFFILIATION_KEYWORDS = {
    "arasaka": "Arasaka",
    "militech": "Militech",
    "kang tao": "Kang Tao",
    "maelstrom": "Maelstrom",
    "tyger claws": "Tyger Claws",
    "valentinos": "Valentinos",
    "6th street": "6th Street",
    "animals": "Animals",
    "voodoo boys": "Voodoo Boys",
    "the mox": "The Mox",
    "mox": "The Mox",
    "scavengers": "Scavengers",
    "wraiths": "Wraiths",
    "aldecaldos": "Aldecaldos",
    "barghest": "Barghest",
    "ncpd": "NCPD",
    "max-tac": "MaxTac",
    "maxtac": "MaxTac",
    "trauma team": "Trauma Team",
    "netrunner": "Netrunner",
    "fixer": "Fixer",
    "mercenary": "Mercenário",
    "mercenário": "Mercenário",
    "solo": "Solo",
    "nomad": "Nômade",
    "nômade": "Nômade",
}
