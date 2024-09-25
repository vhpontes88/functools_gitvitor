import os,re, requests, sys

import yfinance as yf
import numpy as np
import pandas as pd

import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio

from sklearn.linear_model import LinearRegression

###
class Perfil_bbce:
    def __init__(self, df_bbce,):
        self.df_bbce = df_bbce


def profile_bbce(df, produto, freq='5t'):
    df_out = df.groupby('nome').get_group(produto).loc[:,['createdAt','quantity','unitPrice','originOperationType_Match','tendency_Compra']].set_index('createdAt').resample(freq).agg({'quantity':['sum','size'],'unitPrice':'median','originOperationType_Match':'mean','tendency_Compra':'mean'})
    df_out.columns = [f'{col[0]}_{col[1]}' for col in df_out.columns]
    return df_out 

def gera_plot1_bbce(produto, profile):
    # Defina o título como uma variável
    titulo_grafico = f"Análise de Preço e Volume com Regressão Linear - {produto}"

    df = profile.copy()

    # Preparação da regressão linear (OLS) para o preço
    df_ols = df.ffill()
    X = np.array(range(len(df_ols))).reshape(-1, 1)  # Variável independente (índice de tempo)
    y = df_ols['unitPrice_median'].values.reshape(-1, 1)  # Variável dependente (preço)
    ols_model = LinearRegression()
    ols_model.fit(X, y)
    y_pred = ols_model.predict(X)

    # Criação do gráfico com dois eixos Y
    fig = go.Figure()

    # Gráfico de preços no eixo Y1 (esquerda)
    fig.add_trace(go.Scatter(x=df.index, y=df['unitPrice_median'], mode='lines+markers', 
                            name='Preço', yaxis='y1'))

    # Adicionando a linha de regressão OLS
    fig.add_trace(go.Scatter(x=df.index, y=y_pred.flatten(), mode='lines', 
                            name='OLS (Regressão Linear)', line=dict(dash='dash'), yaxis='y1'))

    # Gráfico de volume com coloração baseada em tendency_Compra_mean no eixo Y2 (direita)
    for i in range(len(df)):
        color = 'red' if df['tendency_Compra_mean'].iloc[i] > 0.5 else 'green'
        fig.add_trace(go.Bar(x=[df.index[i]], y=[df['quantity_sum'].iloc[i]], 
                            marker_color=color, name='Volume', yaxis='y2', showlegend=False))

    # Atualizando layout para adicionar dois eixos Y e posicionar a legenda fora do gráfico
    fig.update_layout(
        title=titulo_grafico,  # Título do gráfico como variável
        xaxis_title="Hora da Operação",
        yaxis=dict(title="Preço (R$)", side="left"),
        yaxis2=dict(title="Volume (MW)", overlaying='y', side='right'),
        height=600,  # Altura para 8 unidades
        width=1600,  # Largura para 16 unidades
        legend=dict(x=1.05, y=1),  # Posição da legenda fora do gráfico
        margin=dict(l=50, r=100, t=50, b=50)  # Ajustando margens para espaço da legenda
    )

    return fig


def foo_agg_bbce(s):
    res_nomes = ['qtde'         ,'abertura'         ,'fechamento'       ,'media','mediana','dp','min','max']
    res =       [len(s.dropna()),s.dropna().iloc[0] ,s.dropna().iloc[-1],s.mean(),s.median(),s.std(),s.min(),s.max()]

    res = dict(zip(res_nomes,res))
    res['gap_minmax'] = res['max'] - res['min']
    res['gap_periodo'] = res['fechamento'] - res['abertura']
    return res

def get_financial_data(start_date, end_date):
    # Definir os ativos
    tickers = {
        'BRL/USD': 'BRL=X',       # BRL/USD Cambio
        'Brent': 'BZ=F',          # Brent Crude Oil
        'NYMEX': 'CL=F',          # WTI Crude Oil (NYMEX)
        #'OCBI': '^DJUSCM',        # OCBI (DJ US Coal Mining, placeholder)
        #'CMI': '^CMI',            # Commodity Index
        'ODI': '^GSPC',           # ODI (S&P 500, como exemplo de placeholder)
        'JKM': 'NG=F',            # JKM Natural Gas (como exemplo de placeholder)
        'TTF': 'TTF=F'            # Dutch TTF Gas (como exemplo de placeholder)
    }
    
    # Baixar dados de todos os tickers no período desejado
    data = yf.download(list(tickers.values()), start=start_date, end=end_date)['Adj Close']
    
    # Renomear colunas de acordo com os nomes dos ativos
    data.columns = tickers.keys()
    
    return data
