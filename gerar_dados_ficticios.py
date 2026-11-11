import json
import random
import os
from datetime import datetime, timedelta

os.makedirs("data", exist_ok=True)

artistas_ficticios = ["Luna Vortex", "Os Cariocas", "Neon Tiger", "Beatriz Solar", "DJ Algoritmo", "The Data Miners", "Clara Luz", "Rock do Vale"]
musicas_ficticias = ["Eco do Amanhã", "Data Driven", "Noite de Código", "Amor em Python", "Loop Infinito", "Filtro Passa-Alta", "Sintaxe do Coração", "Na Nuvem"]

historico = []
data_inicial = datetime(2023, 1, 1)

# Vamos simular que o usuário ouviu 800 músicas no ano
for _ in range(800):
    artista = random.choice(artistas_ficticios)
    musica = random.choice(musicas_ficticias)
    # Sorteia uma data aleatória no ano
    dias_aleatorios = random.randint(0, 364)
    data_reproducao = data_inicial + timedelta(days=dias_aleatorios, hours=random.randint(0, 23), minutes=random.randint(0, 59))
    
    # Formata igual ao Spotify
    play = {
        "endTime": data_reproducao.strftime("%Y-%m-%d %H:%M"),
        "artistName": artista,
        "trackName": musica,
        "msPlayed": random.randint(45000, 300000) # Entre 45 seg e 5 min
    }
    historico.append(play)

# Salva o arquivo
with open("data/exemplo_dados.json", "w", encoding="utf-8") as f:
    json.dump(historico, f, indent=4, ensure_ascii=False)

print("✔ Arquivo 'data/exemplo_dados.json' gerado com sucesso! (Dados 100% fictícios)")