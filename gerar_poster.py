import json
import glob
import os
import pandas as pd
import requests
import base64
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

# ============================================================
# 1. CONFIGURAÇÕES DO POSTER
# ============================================================
LARGURA = 1080
ALTURA = 1080
COR_FUNDO = (26, 11, 46)      # Roxo escuro
COR_TEXTO = (243, 232, 255)   # Quase branco
COR_DESTAQUE = (255, 107, 158) # Rosa
COR_SECUNDARIA = (199, 125, 255) # Lilás

# ============================================================
# 2. CARREGAR DADOS E API
# ============================================================
def carregar_dados():
    arquivos = glob.glob(os.path.join("data", "*Audio*.json")) + glob.glob(os.path.join("data", "*Video*.json"))
    registros = []
    for arq in arquivos:
        with open(arq, encoding="utf-8") as f:
            registros.extend(json.load(f))
    
    df = pd.DataFrame(registros)
    df = df.rename(columns={
        "master_metadata_track_name": "musica",
        "master_metadata_album_artist_name": "artista",
        "master_metadata_album_album_name": "album",
        "ms_played": "ms"
    })
    df = df.dropna(subset=["musica", "artista", "ms"])
    df["minutos"] = df["ms"] / 60000
    return df

def obter_token(client_id, client_secret):
    auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    response = requests.post("https://accounts.spotify.com/api/token", 
        headers={"Authorization": f"Basic {auth}"}, 
        data={"grant_type": "client_credentials"})
    return response.json().get("access_token") if response.status_code == 200 else None

def buscar_capa(album, artista, token):
    if not token: return None
    query = f"album:{album} artist:{artista}"
    res = requests.get("https://api.spotify.com/v1/search", 
        headers={"Authorization": f"Bearer {token}"}, 
        params={"q": query, "type": "album", "limit": 1})
    if res.status_code == 200:
        items = res.json().get("albums", {}).get("items", [])
        if items and items[0].get("images"):
            img_url = items[0]["images"][0]["url"]
            img_data = requests.get(img_url).content
            return Image.open(BytesIO(img_data)).resize((250, 250))
    return None

# ============================================================
# 3. DESENHAR O POSTER
# ============================================================
def gerar_poster(df, token):
    img = Image.new("RGB", (LARGURA, ALTURA), COR_FUNDO)
    draw = ImageDraw.Draw(img)
    
    # Tenta carregar fontes do sistema (Windows)
    try:
        fonte_titulo = ImageFont.truetype("arialbd.ttf", 60)
        fonte_subtitulo = ImageFont.truetype("arial.ttf", 30)
        fonte_destaque = ImageFont.truetype("arialbd.ttf", 80)
        fonte_pequena = ImageFont.truetype("arial.ttf", 20)
    except:
        # Fallback se não achar as fontes
        fonte_titulo = ImageFont.load_default()
        fonte_subtitulo = ImageFont.load_default()
        fonte_destaque = ImageFont.load_default()
        fonte_pequena = ImageFont.load_default()

    # Cabeçalho
    draw.text((60, 50), "MEU SPOTIFY WRAPPED", font=fonte_titulo, fill=COR_TEXTO)
    draw.text((60, 120), "Uma análise dos meus últimos meses de música", font=fonte_subtitulo, fill=COR_SECUNDARIA)
    
    # Linha divisória
    draw.line([(60, 170), (LARGURA - 60, 170)], fill=COR_DESTAQUE, width=3)
    
    # Métricas Gerais
    total_horas = df["minutos"].sum() / 60
    total_musicas = len(df)
    total_artistas = df["artista"].nunique()
    
    draw.text((60, 220), f"{total_horas:,.0f}", font=fonte_destaque, fill=COR_DESTAQUE)
    draw.text((60, 310), "Horas ouvidas", font=fonte_pequena, fill=COR_SECUNDARIA)
    
    draw.text((350, 220), f"{total_musicas:,}", font=fonte_destaque, fill=COR_DESTAQUE)
    draw.text((350, 310), "Músicas tocadas", font=fonte_pequena, fill=COR_SECUNDARIA)
    
    draw.text((650, 220), f"{total_artistas:,}", font=fonte_destaque, fill=COR_DESTAQUE)
    draw.text((650, 310), "Artistas diferentes", font=fonte_pequena, fill=COR_SECUNDARIA)
    
    draw.line([(60, 370), (LARGURA - 60, 370)], fill=(61, 32, 102), width=1)
    
    # Top 3 Álbuns
    draw.text((60, 400), "TOP ÁLBUNS", font=fonte_subtitulo, fill=COR_TEXTO)
    
    top_albuns = df.groupby(["album", "artista"])["minutos"].sum().sort_values(ascending=False).head(3)
    
    y_offset = 450
    for i, ((album, artista), minutos) in enumerate(top_albuns.items()):
        if token:
            capa = buscar_capa(album, artista, token)
            if capa:
                img.paste(capa, (60, y_offset))
        
        draw.text((330, y_offset + 20), album[:30], font=fonte_subtitulo, fill=COR_TEXTO)
        draw.text((330, y_offset + 60), artista[:30], font=fonte_pequena, fill=COR_SECUNDARIA)
        draw.text((330, y_offset + 100), f"{minutos:.0f} minutos ouvidos", font=fonte_pequena, fill=COR_DESTAQUE)
        
        y_offset += 190 # Pula para o próximo álbum
    
    # Rodapé
    draw.line([(60, ALTURA - 80), (LARGURA - 60, ALTURA - 80)], fill=COR_DESTAQUE, width=3)
    draw.text((60, ALTURA - 60), "Gerado por mim com Python & Streamlit 🎧", font=fonte_pequena, fill=COR_SECUNDARIA)
    
    img.save("poster_linkedin.png")
    print("✅ Poster salvo como 'poster_linkedin.png'!")

# ============================================================
# 4. EXECUÇÃO
# ============================================================
if __name__ == "__main__":
    print("Carregando dados...")
    df = carregar_dados()
    
    print("\nInsira suas credenciais do Spotify Developer:")
    cid = input("Client ID: ")
    csecret = input("Client Secret: ")
    
    token = obter_token(cid, csecret)
    
    print("\nGerando poster (isso pode levar alguns segundos)...")
    gerar_poster(df, token)