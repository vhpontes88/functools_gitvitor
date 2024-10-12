'''
Funções que necessitam de modulos já instalados no python

'''
import os, re, sys,math

import numpy as np
import sympy as sp
import pandas as pd
import scipy as sc


def print_matriz(A):
    """
    Converte uma matriz numérica em uma representação mais legível, dependendo das bibliotecas disponíveis.

    Se o módulo `sympy` (importado como `sp`) estiver disponível, a função retorna uma matriz do Sympy
    com valores inteiros. Caso contrário, utiliza o `pandas.DataFrame` para retornar a matriz como um 
    DataFrame com os valores convertidos para inteiros.

    Parâmetros:
    ----------
    A : array-like
        A matriz que se deseja imprimir. Pode ser uma matriz NumPy ou estrutura similar.

    Retorno:
    -------
    sympy.Matrix ou pandas.DataFrame
        Retorna uma matriz Sympy se `sympy` estiver importado como `sp`. Caso contrário, 
        retorna um DataFrame `pandas` com valores inteiros.
    """
    if 'sp' in globals():
        return sp.Matrix(A.astype(int))
    else:
        return pd.DataFrame(A).astype(int)

def cramer(i, A):
    """
    Calcula a solução do sistema linear Ax = b usando a Regra de Cramer para a incógnita de índice `i`.

    A Regra de Cramer é uma fórmula explícita para a solução de sistemas lineares onde o determinante da matriz
    A não é zero. A solução para a variável `x_i` é obtida substituindo a coluna `i` de A pelo vetor de termos 
    constantes `b`, e dividindo o determinante desta nova matriz pelo determinante da matriz original.

    Parâmetros:
    ----------
    i : int
        O índice da incógnita que se deseja calcular usando a Regra de Cramer.
    A : array-like
        A matriz de coeficientes do sistema linear.

    Retorno:
    -------
    float
        O valor da incógnita `x_i` obtido pela Regra de Cramer.

    Exceções:
    --------
    LinAlgError:
        Se o determinante da matriz A for zero, a solução não pode ser determinada pela Regra de Cramer.
    """
    Ai = A.copy()        # Copia a matriz A
    Ai[:, i] = b         # Substitui a coluna `i` pela coluna de termos constantes `b`
    return np.linalg.det(Ai) / np.linalg.det(A)  # Retorna o valor da incógnita `x_i`
