# 🎧 Meu Spotify Wrapped Personalizado

![Status](https://img.shields.io/badge/status-conclu%C3%ADdo-brightgreen)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-red)

Uma análise interativa e visual dos meus dados de audição do Spotify, transformando o arquivo *Extended Streaming History* em um dashboard personalizado.

## 🚀 Funcionalidades
- **Top Artistas, Músicas e Álbuns:** com integração à API do Spotify para carregar as capas.
- **Análise de Hábitos:** gráficos de audição por hora do dia e dia da semana.
- **Evolução Mensal:** acompanhe como seu gosto musical mudou ao longo dos meses.
- **Métricas Avançadas:** cálculo de taxa de *skip* por artista, artista mais fiel (dias diferentes) e músicas "viciantes" (repetições seguidas).
- **Design Customizado:** Interface com tema dark roxo, construída com Streamlit e CSS personalizado.

## 🛠️ Tecnologias Utilizadas
- **Python** (Pandas para manipulação de dados)
- **Streamlit** (Dashboard interativo)
- **Spotify Web API** (Busca de capas de álbuns)
- **Altair** (Gráficos interativos)
- **Pillow (PIL)** (Geração de poster para redes sociais)

## ⚙️ Como rodar o projeto localmente
1. Clone o repositório.
2. Instale as dependências: `pip install -r requirements.txt`
3. Crie uma pasta `data` e coloque seus arquivos `.json` do Spotify (Extended Streaming History) dentro dela.
4. Crie um app no [Spotify Developer](https://developer.spotify.com/dashboard) e pegue seu *Client ID* e *Client Secret*.
5. Rode o app: `streamlit run wrapped_app.py`
6. Insira suas credenciais na barra lateral do app.
