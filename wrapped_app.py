import streamlit as st
import pandas as pd
import json
import glob
import os
import requests
import base64

st.set_page_config(page_title="Meu Spotify Wrapped | Portfólio", page_icon="", layout="wide")

css_personalizado = """
<style>
    
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background-color: #1A0B2E;
        color: #F3E8FF; /* Texto quase branco, com um toque de lilás */
    }
    
    [data-testid="stSidebar"] {
        background-color: #241042;
        border-right: 1px solid #3D2066;
    }
    
    h1, h2, h3 {
        color: #D8B4E2 !important; 
        font-weight: 600;
    }
    
    [data-testid="stMetricValue"] {
        color: #FF6B9E; /* Rosa para os números principais */
        font-weight: bold;
    }
    [data-testid="stMetricLabel"] {
        color: #C77DFF; /* Lilás para as legendas das métricas */
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        border-bottom: 1px solid #3D2066;
    }
    .stTabs [data-baseweb="tab"] {
        color: #A78BFA; /* Lilás acinzentado */
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        color: #FF6B9E !important; /* Rosa para a aba ativa */
        border-bottom-color: #FF6B9E !important;
    }
    
    .stCaption {
        color: #A78BFA !important; 
    }
    
   
    .stButton>button {
        background-color: #FF6B9E;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 8px 16px;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #C77DFF; /* Muda para lilás ao passar o mouse */
        color: white;
    }

    a {
        color: #FF6B9E !important;
        text-decoration: none;
    }
    a:hover {
        color: #C77DFF !important;
        text-decoration: underline;
    }
    
    .stTextInput>div>div>input {
        background-color: #241042;
        color: #F3E8FF;
        border: 1px solid #3D2066;
    }
</style>
"""
st.markdown(css_personalizado, unsafe_allow_html=True)


@st.cache_data
def carregar_dados(pasta="data"):
    padrao_audio = os.path.join(pasta, "*Audio*.json")
    padrao_video = os.path.join(pasta, "*Video*.json")
    arquivos = glob.glob(padrao_audio) + glob.glob(padrao_video)
    
    registros = []
    for arq in arquivos:
        with open(arq, encoding="utf-8") as f:
            try:
                dados = json.load(f)
                registros.extend(dados)
            except:
                pass
                
    df = pd.DataFrame(registros)
    colunas = ["master_metadata_track_name", "master_metadata_album_artist_name", 
               "master_metadata_album_album_name", "ms_played", "ts", "skipped"]
    for col in colunas:
        if col not in df.columns:
            df[col] = None
            
    df = df.rename(columns={
        "master_metadata_track_name": "musica",
        "master_metadata_album_artist_name": "artista",
        "master_metadata_album_album_name": "album",
        "ms_played": "ms",
        "ts": "timestamp",
        "skipped": "skip"
    })
    
    df = df.dropna(subset=["musica", "artista", "ms"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df["timestamp_local"] = df["timestamp"].dt.tz_convert("America/Sao_Paulo")
    df["minutos"] = df["ms"] / 60000
    df["hora"] = df["timestamp_local"].dt.hour
    df["dia_semana"] = df["timestamp_local"].dt.day_name()
    df["mes"] = df["timestamp_local"].dt.to_period("M").astype(str)
    return df

@st.cache_data(ttl=3600)
def obter_token_spotify(client_id, client_secret):
    auth_string = f"{client_id}:{client_secret}"
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")
    
    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": f"Basic {auth_base64}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}
    
    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        st.error(f"Erro ao autenticar no Spotify: {response.status_code}")
        return None

@st.cache_data(ttl=3600)
def buscar_capa_album(album_nome, artista_nome, token):
    if not token or not album_nome or not artista_nome:
        return None
        
    url = "https://api.spotify.com/v1/search"
    headers = {"Authorization": f"Bearer {token}"}
    query = f"album:{album_nome} artist:{artista_nome}"
    params = {"q": query, "type": "album", "limit": 1}
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        albums = data.get("albums", {}).get("items", [])
        if albums:
            images = albums[0].get("images", [])
            if images:
                return images[0]["url"]
    return None

st.markdown("<h1 style='text-align: center;'> Meu Spotify Wrapped</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #A78BFA;'>Análise de dados do meu histórico musical • <a href='https://seuportfolio.com'>Voltar ao Portfólio</a></p>", unsafe_allow_html=True)
st.divider()

with st.sidebar:
    st.header("🔑 Configuração")
    st.markdown("Insira suas credenciais do [Spotify Developer](https://developer.spotify.com/dashboard).")
    client_id = st.text_input("Client ID", type="password")
    client_secret = st.text_input("Client Secret", type="password")
    
    if st.button("Limpar Cache"):
        st.cache_data.clear()
        st.rerun()

with st.spinner("Carregando seus dados do Spotify..."):
    df = carregar_dados("data")

if df.empty:
    st.error("Nenhum dado encontrado na pasta 'data'.")
    st.stop()

token = None
if client_id and client_secret:
    token = obter_token_spotify(client_id, client_secret)
    if token:
        st.sidebar.success("✅ Autenticado no Spotify!")
    else:
        st.sidebar.error("❌ Falha na autenticação.")

col1, col2, col3 = st.columns(3)
col1.metric("Total de Músicas", f"{len(df):,}")
col2.metric("Horas Ouvidas", f"{df['minutos'].sum() / 60:,.0f}")
col3.metric("Artistas Diferentes", f"{df['artista'].nunique():,}")

st.divider()

st.header("💿 Top Álbuns")

top_albuns = df.groupby(["album", "artista"])["minutos"].sum().sort_values(ascending=False).head(6)

if token:
    cols = st.columns(3)
    for idx, ((album, artista), minutos) in enumerate(top_albuns.items()):
        with cols[idx % 3]:
            capa_url = buscar_capa_album(album, artista, token)
            if capa_url:
                st.image(capa_url, use_container_width=True)
            else:
                st.info("Capa não encontrada")
            st.markdown(f"<p style='color: #D8B4E2; font-weight: bold; margin-bottom: 0;'>{album}</p>", unsafe_allow_html=True)
            st.caption(f"{artista} • {minutos:.0f} min")
else:
    st.info("Insira suas credenciais na barra lateral para ver as capas dos álbuns.")

st.divider()

tab1, tab2, tab3 = st.tabs(["🎤 Top Artistas", "📈 Evolução", "⏰ Hábitos"])

import altair as alt

with tab1:
    top_art = df.groupby("artista")["minutos"].sum().sort_values(ascending=False).head(10).reset_index()
    chart = alt.Chart(top_art).mark_bar(color="#FF6B9E").encode(
        x=alt.X('minutos:Q', title='Minutos'),
        y=alt.Y('artista:N', sort='-x', title='Artista'),
        tooltip=['artista', 'minutos']
    ).properties(height=400)
    st.altair_chart(chart, use_container_width=True)

with tab2:
    evolucao = df.groupby("mes")["minutos"].sum().reset_index()
    chart = alt.Chart(evolucao).mark_line(point=True, color="#C77DFF").encode(
        x=alt.X('mes:N', title='Mês', axis=alt.Axis(labelAngle=-45)),
        y=alt.Y('minutos:Q', title='Minutos'),
        tooltip=['mes', 'minutos']
    ).properties(height=400)
    st.altair_chart(chart, use_container_width=True)

with tab3:
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("Por Hora")
        hora_df = df.groupby("hora")["minutos"].sum().reset_index()
        chart_hora = alt.Chart(hora_df).mark_bar(color="#FF6B9E").encode(
            x=alt.X('hora:O', title='Hora do dia'),
            y=alt.Y('minutos:Q', title='Minutos'),
            tooltip=['hora', 'minutos']
        ).properties(height=300)
        st.altair_chart(chart_hora, use_container_width=True)
        
    with col_b:
        st.subheader("Por Dia da Semana")
        ordem = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        dia_df = df.groupby("dia_semana")["minutos"].sum().reindex(ordem, fill_value=0).reset_index()
        chart_dia = alt.Chart(dia_df).mark_bar(color="#C77DFF").encode(
            x=alt.X('dia_semana:N', title='Dia', sort=ordem),
            y=alt.Y('minutos:Q', title='Minutos'),
            tooltip=['dia_semana', 'minutos']
        ).properties(height=300)
        st.altair_chart(chart_dia, use_container_width=True)
