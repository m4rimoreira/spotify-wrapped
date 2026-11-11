import json
import glob
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# ============================================================
# 1. CARREGAMENTO DOS DADOS (Ajustado para Extended History)
# ============================================================

def carregar_dados(pasta="data"):
    """Lê todos os JSONs (áudio e vídeo) e retorna um DataFrame."""
    # Pega apenas arquivos que contém 'Audio' ou 'Video' no nome
    padrao_busca = os.path.join(pasta, "*Audio*.json")
    padrao_busca_video = os.path.join(pasta, "*Video*.json")
    arquivos = glob.glob(padrao_busca) + glob.glob(padrao_busca_video)
    
    if not arquivos:
        raise FileNotFoundError(f"Nenhum JSON de áudio ou vídeo encontrado em '{pasta}'")

    registros = []
    print("Lendo arquivos...")
    for arq in arquivos:
        with open(arq, encoding="utf-8") as f:
            try:
                dados = json.load(f)
                registros.extend(dados)
                print(f"  ✓ {os.path.basename(arq)} lido ({len(dados)} registros)")
            except Exception as e:
                print(f"  ✗ Erro ao ler {arq}: {e}")

    df = pd.DataFrame(registros)

    # O formato Extended já vem com esses nomes de colunas, mas vamos garantir
    colunas_necessarias = ["master_metadata_track_name", "master_metadata_album_artist_name", 
                           "master_metadata_album_album_name", "ms_played", "ts", "skipped"]
    
    for col in colunas_necessarias:
        if col not in df.columns:
            df[col] = None

    # Renomeando para facilitar o uso
    df = df.rename(columns={
        "master_metadata_track_name": "musica",
        "master_metadata_album_artist_name": "artista",
        "master_metadata_album_album_name": "album",
        "ms_played": "ms",
        "ts": "timestamp",
        "skipped": "skip"
    })

    # Limpeza: remove linhas onde não há música (ex: podcasts ou anúncios que não têm metadados)
    df = df.dropna(subset=["musica", "artista", "ms"])
    
    # Converte timestamp (que vem em UTC no padrão ISO) para o fuso de SP
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df["timestamp_local"] = df["timestamp"].dt.tz_convert("America/Sao_Paulo")
    
    # Criação de colunas úteis
    df["minutos"] = df["ms"] / 60000
    df["hora"] = df["timestamp_local"].dt.hour
    df["dia_semana"] = df["timestamp_local"].dt.day_name()
    df["mes"] = df["timestamp_local"].dt.to_period("M").astype(str)
    df["data"] = df["timestamp_local"].dt.date

    return df

# ============================================================
# 2. MÉTRICAS
# ============================================================

def tempo_total(df):
    total_min = df["minutos"].sum()
    dias = total_min / 60 / 24
    return total_min, dias

def top_artistas(df, n=10):
    return df.groupby("artista")["minutos"].sum().sort_values(ascending=False).head(n).round(1)

def top_musicas(df, n=10):
    return df.groupby(["musica", "artista"])["minutos"].sum().sort_values(ascending=False).head(n).round(1)

def top_albuns(df, n=10):
    if "album" not in df.columns:
        return None
    return df.groupby(["album", "artista"])["minutos"].sum().sort_values(ascending=False).head(n).round(1)

def artista_mais_fiel(df, n=10):
    """Artista ouvido em mais dias diferentes."""
    return df.groupby("artista")["data"].nunique().sort_values(ascending=False).head(n)

def musica_viciante(df, n=10):
    """Músicas com maior número de reproduções consecutivas (mesmo dia)."""
    df_sorted = df.sort_values("timestamp_local").copy()
    df_sorted["bloco"] = (
        (df_sorted["musica"] != df_sorted["musica"].shift()) |
        (df_sorted["data"] != df_sorted["data"].shift())
    ).cumsum()
    repetidas = (
        df_sorted.groupby("bloco")
        .agg(musica=("musica", "first"), artista=("artista", "first"),
             repeticoes=("musica", "size"), dia=("data", "first"))
        .sort_values("repeticoes", ascending=False)
        .head(n)
    )
    return repetidas

def taxa_skip_por_artista(df, n=10):
    """Artistas com maior taxa de skip (%)."""
    agrup = df.groupby("artista").agg(
        total=("skip", "size"),
        skips=("skip", "sum"),
    )
    agrup["taxa_skip_%"] = (agrup["skips"] / agrup["total"] * 100).round(1)
    return agrup.sort_values("taxa_skip_%", ascending=False).head(n)

def ouvintes_por_hora(df):
    return df.groupby("hora")["minutos"].sum().reindex(range(24), fill_value=0).round(1)

def ouvintes_por_dia_semana(df):
    ordem = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    return df.groupby("dia_semana")["minutos"].sum().reindex(ordem, fill_value=0).round(1)

def evolucao_mensal(df):
    return df.groupby("mes")["minutos"].sum().round(1)

def artistas_novos_por_mes(df, n=20):
    """Detecta artistas que apareceram pela primeira vez em cada mês."""
    primeira_vez = df.groupby("artista")["mes"].min().reset_index()
    primeira_vez.columns = ["artista", "mes_estreia"]
    return primeira_vez.sort_values("mes_estreia").head(n)

# ============================================================
# 3. VISUALIZAÇÕES
# ============================================================

def salvar_grafico(fig, nome, pasta="output"):
    os.makedirs(pasta, exist_ok=True)
    caminho = os.path.join(pasta, nome)
    fig.savefig(caminho, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"  ✓ Gráfico salvo: {caminho}")

def gerar_graficos(df):
    sns.set_theme(style="whitegrid")

    # Top artistas
    fig, ax = plt.subplots(figsize=(10, 6))
    top_artistas(df).plot(kind="barh", ax=ax, color="mediumseagreen")
    ax.invert_yaxis()
    ax.set_title("Top 10 Artistas (minutos ouvidos)")
    ax.set_xlabel("Minutos")
    salvar_grafico(fig, "top_artistas.png")

    # Top músicas
    fig, ax = plt.subplots(figsize=(10, 6))
    tm = top_musicas(df)
    tm.index = [f"{m} — {a}" for m, a in tm.index]
    tm.plot(kind="barh", ax=ax, color="steelblue")
    ax.invert_yaxis()
    ax.set_title("Top 10 Músicas (minutos ouvidos)")
    ax.set_xlabel("Minutos")
    salvar_grafico(fig, "top_musicas.png")

    # Top álbuns
    albuns = top_albuns(df)
    if albuns is not None:
        fig, ax = plt.subplots(figsize=(10, 6))
        albuns.index = [f"{al} — {ar}" for al, ar in albuns.index]
        albuns.plot(kind="barh", ax=ax, color="darkorange")
        ax.invert_yaxis()
        ax.set_title("Top 10 Álbuns (minutos ouvidos)")
        ax.set_xlabel("Minutos")
        salvar_grafico(fig, "top_albuns.png")

    # Horário de pico
    fig, ax = plt.subplots(figsize=(12, 5))
    ouvintes_por_hora(df).plot(kind="bar", ax=ax, color="mediumpurple")
    ax.set_title("Minutos ouvidos por hora do dia")
    ax.set_xlabel("Hora do dia (Fuso: São Paulo)")
    ax.set_ylabel("Minutos")
    salvar_grafico(fig, "por_hora.png")

    # Dia da semana
    fig, ax = plt.subplots(figsize=(10, 5))
    ouvintes_por_dia_semana(df).plot(kind="bar", ax=ax, color="coral")
    ax.set_title("Minutos ouvidos por dia da semana")
    ax.set_ylabel("Minutos")
    salvar_grafico(fig, "por_dia_semana.png")

    # Evolução mensal
    fig, ax = plt.subplots(figsize=(14, 5))
    evolucao_mensal(df).plot(kind="line", marker="o", ax=ax, color="teal")
    ax.set_title("Minutos ouvidos por mês")
    ax.set_ylabel("Minutos")
    ax.tick_params(axis="x", rotation=45)
    salvar_grafico(fig, "evolucao_mensal.png")

# ============================================================
# 4. RELATÓRIO TEXTO
# ============================================================

def gerar_relatorio(df, pasta="output"):
    os.makedirs(pasta, exist_ok=True)
    total_min, dias = tempo_total(df)

    linhas = []
    linhas.append("=" * 60)
    linhas.append("           MEU SPOTIFY WRAPPED — RELATÓRIO")
    linhas.append("=" * 60)
    linhas.append(f"\nPeríodo analisado: {df['timestamp_local'].min().date()} → {df['timestamp_local'].max().date()}")
    linhas.append(f"Total de reproduções: {len(df):,}")
    linhas.append(f"Tempo total: {total_min:,.0f} minutos ({total_min/60:,.1f} horas / {dias:.1f} dias)\n")

    linhas.append("-" * 60)
    linhas.append("TOP 10 ARTISTAS")
    linhas.append("-" * 60)
    for i, (art, min_) in enumerate(top_artistas(df).items(), 1):
        linhas.append(f"{i:2d}. {art:<40} {min_:>8.1f} min")

    linhas.append("\n" + "-" * 60)
    linhas.append("TOP 10 MÚSICAS")
    linhas.append("-" * 60)
    for i, ((m, a), min_) in enumerate(top_musicas(df).items(), 1):
        linhas.append(f"{i:2d}. {m} — {a} ({min_:.1f} min)")

    linhas.append("\n" + "-" * 60)
    linhas.append("TOP 10 ÁLBUNS")
    linhas.append("-" * 60)
    albuns = top_albuns(df)
    if albuns is not None:
        for i, ((al, ar), min_) in enumerate(albuns.items(), 1):
            linhas.append(f"{i:2d}. {al} — {ar} ({min_:.1f} min)")

    linhas.append("\n" + "-" * 60)
    linhas.append("ARTISTAS MAIS FIEIS (dias diferentes ouvidos)")
    linhas.append("-" * 60)
    for i, (art, d) in enumerate(artista_mais_fiel(df).items(), 1):
        linhas.append(f"{i:2d}. {art:<40} {d:>4} dias")

    linhas.append("\n" + "-" * 60)
    linhas.append("MÚSICAS VICIANTES (reproduções seguidas no mesmo dia)")
    linhas.append("-" * 60)
    viciantes = musica_viciante(df)
    for _, row in viciantes.iterrows():
        linhas.append(f"  • {row['musica']} — {row['artista']}: {row['repeticoes']}x em {row['dia']}")

    linhas.append("\n" + "-" * 60)
    linhas.append("TAXA DE SKIP POR ARTISTA (Top 10 - os mais pulados)")
    linhas.append("-" * 60)
    skips = taxa_skip_por_artista(df)
    for art, row in skips.iterrows():
        linhas.append(f"  {art:<40} {row['taxa_skip_%']:>5.1f}%  ({int(row['skips'])}/{int(row['total'])})")

    linhas.append("\n" + "-" * 60)
    linhas.append("ARTISTAS QUE VOCÊ DESCOBRIU (Primeiros 20 por mês)")
    linhas.append("-" * 60)
    novos = artistas_novos_por_mes(df)
    for _, row in novos.iterrows():
        linhas.append(f"  {row['mes_estreia']}  →  {row['artista']}")

    linhas.append("\n" + "=" * 60)

    texto = "\n".join(linhas)
    caminho = os.path.join(pasta, "relatorio.txt")
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(texto)

    print(texto)
    print(f"\n✓ Relatório completo salvo em {caminho}")

# ============================================================
# 5. MAIN
# ============================================================

if __name__ == "__main__":
    print("Iniciando processamento do Spotify Wrapped...\n")
    df = carregar_dados("data")
    
    if df.empty:
        print("Nenhum dado válido foi encontrado nos arquivos. Verifique a pasta 'data'.")
    else:
        print(f"\nTotal de {len(df):,} músicas processadas com sucesso!\n")
        
        print("Gerando gráficos...")
        gerar_graficos(df)

        print("\nGerando relatório em texto...")
        gerar_relatorio(df)

        print("\n🎉 Pronto! Confira seus resultados na pasta 'output/'.")