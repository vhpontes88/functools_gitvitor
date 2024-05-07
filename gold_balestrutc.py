import os, re, datetime, sys, time, json, requests
import pandas as pd
import numpy as np



class CCEE:
    def __init__(self):
        
        
        return None


    self.URLS_individuais = {
                    2024:'https://www.ccee.org.br/documents/80415/27035879/InfoMercado_Dados_Individuais-fev2024.xlsx/2a233377-c006-5535-816b-700a9ef706cd',
                    2023:'https://www.ccee.org.br/documents/80415/25552621/InfoMercado_Dados_Individuais-nov2023.xlsx/5cc2ba8f-a612-0bcf-eaea-3fe82335fa98',
                    2022:'https://www.ccee.org.br/documents/80415/919444/InfoMercado_Dados_Individuais-Dez2022.xlsx/01bdd7c7-9a3a-5c46-ef6b-bcb8c48e7daa',
                    2021:'https://www.ccee.org.br/documents/80415/919444/InfoMercado_Dados_Individuais-Dez2021.xlsx/f7d30b67-a650-cd6c-d363-862c73e826aa',
                    2020:'https://www.ccee.org.br/documents/80415/919444/InfoMercado%20Dados%20Individuais%20Dez2020.xlsx/33eda21e-2c07-df3b-7793-4ab6305a8fdb',
                    2019:'https://www.ccee.org.br/documents/80415/919444/InfoMercado%20Dados%20Individuais%202019.xlsx/b6c6feb5-ecc3-607f-020f-3dbdbfec1ab8',
                    2018:'https://www.ccee.org.br/documents/80415/919444/InfoMercado%20Dados%20Individuais%202018.xlsx/b2f5c7f8-209c-d880-ccd7-1e3bc9064ca7',
                    2017:'https://www.ccee.org.br/documents/80415/919444/InfoMercado%20Dados%20Individuais%202017_Rev1.xlsx/b77abaa1-17f7-16be-0a1a-95eff10694a5',
                    2016:'https://www.ccee.org.br/documents/80415/919444/InfoMercado%20Dados%20Individuais%202016_Rev1.xlsx/42a344fe-2b7a-bb87-9528-3272e8eae8be'
                    }
                    


