"""
Debug script para testar scraping da galeria
"""
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
import re

HEADERS = {
    "User-Agent": "CyberpunkAPIBot/1.0 (Educational Project)",
    "Accept": "text/html,application/xhtml+xml,application/xml",
}

def clean_image_url(url):
    if not url:
        return None
    if url.startswith('//'):
        url = 'https:' + url
    # Remove resize params para pegar imagem maior
    url = re.sub(r'/scale-to-width-down/\d+', '', url)
    url = re.sub(r'/smart/width/\d+/height/\d+', '', url)
    url = re.sub(r'\?cb=\d+.*$', '', url)
    if not any(ext in url.lower() for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']):
        return None
    return url

def test_gallery(gang_name):
    print(f"\n{'='*60}")
    print(f"Testando galeria: {gang_name}")
    print(f"{'='*60}")
    
    # URL da galeria
    gallery_url = f"https://cyberpunk.fandom.com/wiki/{quote(gang_name.replace(' ', '_'))}/Gallery"
    print(f"URL: {gallery_url}")
    
    # Fetch
    session = requests.Session()
    session.headers.update(HEADERS)
    
    try:
        response = session.get(gallery_url, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code != 200:
            print("❌ Página não encontrada!")
            return
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Debug: quantos elementos encontramos?
        print(f"\n📊 Elementos encontrados:")
        print(f"  .thumbimage: {len(soup.select('.thumbimage'))}")
        print(f"  .wikia-gallery-item img: {len(soup.select('.wikia-gallery-item img'))}")
        print(f"  .gallery img: {len(soup.select('.gallery img'))}")
        print(f"  img[data-image-key]: {len(soup.select('img[data-image-key]'))}")
        print(f"  .gallerybox img: {len(soup.select('.gallerybox img'))}")
        
        # Tenta diferentes seletores
        images = []
        
        # Seletor 1: todas as imgs com data-image-key
        for img in soup.select('img[data-image-key]')[:10]:
            src = img.get('src') or img.get('data-src')
            name = img.get('data-image-key') or img.get('alt') or 'unknown'
            if src:
                cleaned = clean_image_url(src)
                if cleaned and cleaned not in images:
                    images.append(cleaned)
                    print(f"  ✓ {name[:40]}...")
        
        print(f"\n📸 Total imagens encontradas: {len(images)}")
        
        if images:
            print("\nPrimeiras 3 URLs:")
            for url in images[:3]:
                print(f"  {url[:80]}...")
        
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == '__main__':
    test_gallery("6th Street")
    test_gallery("Maelstrom")
