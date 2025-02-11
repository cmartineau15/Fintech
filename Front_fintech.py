import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from io import BytesIO
from reportlab.pdfgen import canvas

# Fonction pour récupérer les données
def get_data(symbol, start_date='2019-01-01'):
    df = yf.download(symbol, start=start_date)
    return df

# Calcul du RSI
def calculate_rsi(df, window=14):
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# Calcul du MACD
def calculate_macd(df, short_window=12, long_window=26, signal_window=9):
    short_ema = df['Close'].ewm(span=short_window, min_periods=1, adjust=False).mean()
    long_ema = df['Close'].ewm(span=long_window, min_periods=1, adjust=False).mean()
    macd = short_ema - long_ema
    signal = macd.ewm(span=signal_window, min_periods=1, adjust=False).mean()
    return macd, signal

# Calcul des moyennes mobiles
def calculate_sma(df, window=50):
    sma = df['Close'].rolling(window=window).mean()
    return sma

st.set_page_config(layout="wide")

# Mise en page du titre
st.markdown(
    """
    <h1 style='text-align: center; font-family: Arial, sans-serif; font-weight: bold;'>
        Dashboard financier 📈
    </h1>
    """, unsafe_allow_html=True
)

# Sélection de l'actif
assets = {
    "Bitcoin": "BTC-USD",
    "S&P 500": "^GSPC",
    "Or": "GC=F"
}

col1, col2 = st.columns([2, 1])
with col1:
    asset_choice = st.selectbox("Sélectionnez un actif :", list(assets.keys()))
with col2:
    currency_choice = st.selectbox("Sélectionnez la devise :", ["USD", "EUR", "GBP"])

# Récupération des données
df = get_data(assets[asset_choice])

# Options de filtres
filters = st.multiselect("Sélectionnez les filtres à appliquer :", ["RSI", "MACD", "Rendement", "SMA", "EMA"])

# Affichage du tableau des données
st.write(f"**Données pour {asset_choice} ({currency_choice})**")
st.dataframe(df, use_container_width=True)

# --- Section Overview ---
tab_overview, tab_comparison = st.tabs(["Overview", "Comparaison"])

with tab_overview:
    # Graphique avec Plotly
    def plot_performance(df):
        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=df.index,
                    open=df['Open'], high=df['High'],
                    low=df['Low'], close=df['Close'],
                    name='Performance historique'))
        fig.update_layout(title="Performance Historique",
                          xaxis_title="Date",
                          yaxis_title="Prix",
                          template="plotly_dark",
                          margin=dict(t=50, l=50, r=50, b=50))  # Réduire les marges pour plus d'espace
        st.plotly_chart(fig, use_container_width=True)

    plot_performance(df)

    # Calcul des rendements
    def plot_returns(df):
        plt.figure(figsize=(12, 6))
        plt.plot(df.index, df['Close'].pct_change(), label="Rendements", color='blue')
        plt.title("Rendements quotidiens")
        plt.xlabel("Date")
        plt.ylabel("Rendement")
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.6)
        st.pyplot(plt)

    plot_returns(df)

    # Application des filtres
    if "RSI" in filters:
        rsi = calculate_rsi(df)
        st.subheader("RSI")
        st.line_chart(rsi)

    if "MACD" in filters:
        macd, signal = calculate_macd(df)
        st.subheader("MACD")
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(df.index, macd, label="MACD", color='blue')
        ax.plot(df.index, signal, label="Signal", color='red')
        ax.legend()
        ax.grid(True, linestyle='--', alpha=0.6)
        st.pyplot(fig)

    if "SMA" in filters:
        sma = calculate_sma(df)
        st.subheader("SMA (50 jours)")
        st.line_chart(sma)

    if "EMA" in filters:
        ema = df['Close'].ewm(span=50, adjust=False).mean()
        st.subheader("EMA (50 jours)")
        st.line_chart(ema)

with tab_comparison:
    # Comparaison des trois actifs
    st.write("Comparaison des trois actifs (Bitcoin, S&P 500, Or) sur la même devise :")
    df_bitcoin = get_data("BTC-USD")
    df_sp500 = get_data("^GSPC")
    df_or = get_data("GC=F")

    # Affichage de la performance comparée des actifs
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df_bitcoin.index, open=df_bitcoin['Open'], high=df_bitcoin['High'],
                low=df_bitcoin['Low'], close=df_bitcoin['Close'], name='Bitcoin'))
    fig.add_trace(go.Candlestick(x=df_sp500.index, open=df_sp500['Open'], high=df_sp500['High'],
                low=df_sp500['Low'], close=df_sp500['Close'], name='S&P 500'))
    fig.add_trace(go.Candlestick(x=df_or.index, open=df_or['Open'], high=df_or['High'],
                low=df_or['Low'], close=df_or['Close'], name='Or'))
    fig.update_layout(title="Comparaison des Performances",
                      xaxis_title="Date",
                      yaxis_title="Prix",
                      template="plotly_dark",
                      margin=dict(t=50, l=50, r=50, b=50))  
    st.plotly_chart(fig, use_container_width=True)

# Fonction pour générer un rapport PDF
def generate_pdf(df, asset_name):
    buffer = BytesIO()
    c = canvas.Canvas(buffer)
    
    # Titre du rapport
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 800, f"Rapport d'Analyse Financière : {asset_name}")
    
    # Ajout des données
    c.setFont("Helvetica", 12)
    c.drawString(100, 750, f"Performance historique pour {asset_name}:")
    c.drawString(100, 730, str(df.tail()))
    
    # Sauvegarde et retour du PDF
    c.save()
    buffer.seek(0)
    return buffer

# Bouton pour générer le PDF
if st.button("📄 Générer le Rapport PDF"):
    pdf = generate_pdf(df, asset_choice)
    st.download_button(label="Télécharger le Rapport PDF", data=pdf, file_name="rapport_analyse_financiere.pdf", mime="application/pdf")
