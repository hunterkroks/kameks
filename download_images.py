import requests
from bs4 import BeautifulSoup
import os
import urllib.parse

urls = [
    "https://www.kameks.ru/catalogue/cardan/",
    "https://www.kameks.ru/catalogue/generator/",
    "https://www.kameks.ru/catalogue/starter/",
    "https://www.kameks.ru/catalogue/rti/",
    "https://www.kameks.ru/catalogue/gur/",
    "https://www.kameks.ru/catalogue/tormoz/",
]

os.makedirs("downloaded_images", exist_ok=True)

headers = {"User-Agent": "Mozilla/5.0"}

for url in urls:
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    images = soup.find_all("img")
    
    for img in images:
        src = img.get("src")
        if not src:
            continue
        full_url = urllib.parse.urljoin(url, src)
        filename = os.path.basename(full_url)
        
        try:
            img_data = requests.get(full_url, headers=headers).content
            with open(f"downloaded_images/{filename}", "wb") as f:
                f.write(img_data)
            print(f"Скачано: {filename}")
        except:
            print(f"Ошибка: {filename}")

print("Готово!")