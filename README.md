# 🌆 Cyberpunk 2077 API

A primeira e mais completa **API open-source** do jogo Cyberpunk 2077. Acesse dados de personagens, gangues, distritos e muito mais.

![Cyberpunk 2077](https://img.shields.io/badge/Cyberpunk-2077-fcee0a?style=for-the-badge&logo=steam&logoColor=white)
![GitHub](https://img.shields.io/github/license/jose-pires-neto/Cyberpunk-2077-API?style=for-the-badge)
![Status](https://img.shields.io/badge/status-active-00f0ff?style=for-the-badge)

## 📡 Endpoints

Base URL: `https://jose-pires-neto.github.io/Cyberpunk-2077-API/docs/api/v1/`

| Endpoint | Descrição |
|----------|-----------|
| `/characters.json` | Lista de todos os personagens |
| `/gangs.json` | Gangues de Night City |
| `/districts.json` | Distritos da cidade |
| `/affiliations.json` | Afiliações (gangues, corpos, profissões) |

---

## 🚀 Como Usar

### JavaScript (Fetch)
```javascript
// Buscar todos os personagens
fetch('https://jose-pires-neto.github.io/Cyberpunk-2077-API/docs/api/v1/characters.json')
  .then(response => response.json())
  .then(characters => {
    // Filtrar apenas personagens COM imagens
    const withImages = characters.filter(c => c.has_images !== false);
    console.log(withImages);
  });
```

### JavaScript (Async/Await)
```javascript
async function getCharacters() {
  const response = await fetch('https://jose-pires-neto.github.io/Cyberpunk-2077-API/docs/api/v1/characters.json');
  const characters = await response.json();
  
  // Apenas personagens com imagens
  return characters.filter(c => c.has_images !== false);
}
```

### Python
```python
import requests

url = "https://jose-pires-neto.github.io/Cyberpunk-2077-API/docs/api/v1/characters.json"
response = requests.get(url)
characters = response.json()

# Filtrar personagens com imagens
with_images = [c for c in characters if c.get('has_images', True)]

for char in with_images[:5]:
    print(f"{char['name']} - {char['affiliation']}")
```

---

## 📦 Estrutura de Dados

### Character
```json
{
  "id": 1,
  "name": "Adam Smasher",
  "gender": "Male",
  "affiliation": "Arasaka",
  "description": "Adam Smasher is a full borg mercenary...",
  "has_images": true,
  "images": [
    "https://.../adam_smasher_01.png",
    "https://.../adam_smasher_02.png"
  ],
  "occupation": "Solo",
  "status": "Alive",
  "wiki_url": "https://cyberpunk.fandom.com/wiki/Adam_Smasher"
}
```

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | number | Identificador único |
| `name` | string | Nome do personagem |
| `gender` | string | "Male", "Female" ou "Unknown" |
| `affiliation` | string | Gangue, corporação ou profissão |
| `description` | string | Descrição do personagem |
| `has_images` | boolean | Se possui imagens disponíveis |
| `images` | array | URLs das imagens |
| `occupation` | string | (opcional) Profissão |
| `status` | string | (opcional) Vivo, Morto, etc. |
| `wiki_url` | string | (opcional) Link para a Wiki |

---

## 📁 Estrutura do Projeto

```
Cyberpunk-2077-API/
├── docs/
│   └── api/v1/
│       ├── characters.json
│       ├── gangs.json
│       ├── districts.json
│       └── affiliations.json
├── images/
│   └── characters/
│       └── sex/
│           ├── male/
│           │   └── adam_smasher/
│           │       ├── adam_smasher_01.png
│           │       └── info.json
│           ├── female/
│           │   └── judy_alvarez/
│           └── unknown/
├── scraper/
│   └── scraper.py          # Extrator de dados da Wiki
├── gerador.py              # Gerador do characters.json
├── index.html              # Site showcase
├── docs.html               # Documentação
└── terms.html              # Termos de uso
```

---

## 🛠️ Desenvolvimento

### Requisitos
- Python 3.8+
- pip

### Instalação
```bash
pip install requests beautifulsoup4

# Opcional: para mais imagens via navegador
pip install playwright
playwright install chromium
```

### Adicionar Novos Personagens
```bash
# 1. Baixar personagens da Wiki (60 por vez)
python -m scraper.scraper --limit 60

# 2. Atualizar characters.json
python gerador.py

# 3. Commit e push
git add .
git commit -m "Adiciona novos personagens"
git push
```

### Opções do Scraper
```bash
# Baixar 100 personagens
python -m scraper.scraper --limit 100

# Usar navegador para mais imagens
python -m scraper.scraper --limit 60 --browser

# Desabilitar cache
python -m scraper.scraper --limit 60 --no-cache

# Reprocessar todos (incluindo existentes)
python -m scraper.scraper --limit 60 --all
```

---

## ⚠️ Notas Importantes

- **Imagens**: Alguns personagens podem não ter imagens disponíveis. Use o campo `has_images` para filtrar.
- **Rate Limiting**: A API é servida via GitHub Pages, sem limites de requisição.
- **Atribuição**: Os dados são extraídos da [Cyberpunk Wiki](https://cyberpunk.fandom.com/).

---

## 📄 Licença

Este projeto é open-source e disponibilizado sob a licença MIT.

---

## 👤 Créditos

Criado por **Netrunner José P.**

- GitHub: [@jose-pires-neto](https://github.com/jose-pires-neto)

---

*Night City Database © 2077*
