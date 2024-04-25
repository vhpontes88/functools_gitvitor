import calendar,datetime,requests,sys,shutil,time,zipfile,glob,os,re
import pandas as pd
import numpy as np

DATA_INICIAL_EXCEL=datetime.date(1900,1,1)


def quicksort(arr, indice):
    '''
    Ordena uma lista de listas ou tuplas pelo valor em um índice específico.
    Assume que todos os sub-elementos têm o índice especificado.
    '''
    if len(arr) <= 1:
        return arr
    
    # Verifica se o índice é válido para todos os elementos
    if not all(len(sub) > indice for sub in arr):
        raise ValueError("Índice fora dos limites para alguns elementos da lista.")
    
    pivot = arr[0][indice]
    less = [x for x in arr if x[indice] < pivot]
    equal = [x for x in arr if x[indice] == pivot]
    greater = [x for x in arr if x[indice] > pivot]
    
    return quicksort(less, indice) + equal + quicksort(greater, indice)

def dia_pmo(mes, ano):
    """
    Calcula a data do primeiro sábado do mês especificado.
    
    Parâmetros:
    mes (int): O mês para o qual o PMO será calculado (1 para janeiro, 12 para dezembro).
    ano (int): O ano para o qual o PMO será calculado.

    Retorna:
    datetime.date: A data do primeiro sábado do mês especificado.

    Exceções:
    ValueError: Se o mês não estiver no intervalo de 1 a 12.
    """
    if not 1 <= mes <= 12:
        raise ValueError("Mês deve estar entre 1 e 12.")
    
    # Determina o primeiro dia do mês
    dia_inicial = datetime.date(ano,mes,1)
    # Calcula qual dia da semana cai o primeiro dia do mês (0=Segunda, 6=Domingo)
    dia_da_semana = dia_inicial.weekday()
    # Calcula quantos dias são necessários para alcançar o primeiro sábado
    # Se já é sábado, não precisa adicionar dias, caso contrário calcula a diferença
    delta=(dia_da_semana - 5) % 7
    
    dia_pmo = dia_inicial + datetime.timedelta(days=-1*delta)
    
    return dia_pmo
 
def feriados_nacionais(ano, list_mode=False):
    """
    Calcula os feriados nacionais do Brasil para um determinado ano.
    
    Utiliza a fórmula de Gauss para calcular a data da Páscoa. Esta função é válida até o ano de 2099.
    
    Parâmetros:
    ano (int): O ano para o qual os feriados serão calculados.
    
    Retorna:
    dict: Um dicionário com os nomes dos feriados como chaves e as datas como valores no formato datetime.date.
    
    Exceções:
    ValueError: Se o ano fornecido for superior a 2099.
    """
    if ano > 2099:
        raise ValueError('Ano limite: 2099')
    
    feriados = {
        'Confraternização Universal': datetime.date(ano, 1, 1),
        'Tiradentes': datetime.date(ano, 4, 21),
        'Dia do Trabalho': datetime.date(ano, 5, 1),
        'Independência do Brasil': datetime.date(ano, 9, 7),
        'Nossa Senhora Aparecida': datetime.date(ano, 10, 12),
        'Finados': datetime.date(ano, 11, 2),
        'Proclamação da República': datetime.date(ano, 11, 15),
        'Dia da Consciência Negra': datetime.date(ano, 11, 20),
        'Natal': datetime.date(ano, 12, 25)
    }
    
    # Cálculo da Páscoa baseado na fórmula de Gauss
    X, Y = 24, 5
    a = ano % 19
    b = ano % 4
    c = ano % 7
    d = (19 * a + X) % 30
    e = (2 * b + 4 * c + 6 * d + Y) % 7
    dia = (d + e - 9) if (d + e) > 9 else (d + e + 22)
    mes = 4 if (d + e) > 9 else 3
    if dia == 26 and mes == 4: dia = 19
    if dia == 25 and mes == 4 and d == 28 and a > 10: dia = 18
    
    pascoa = datetime.date(ano, mes, dia)
    
    feriados['Páscoa'] = pascoa
    feriados['Carnaval'] = pascoa - datetime.timedelta(days=47)
    feriados['Sexta-Feira Santa'] = pascoa - datetime.timedelta(days=2)
    feriados['Corpus Christi'] = pascoa + datetime.timedelta(days=60)
    
    if list_mode:
        return quicksort(list(feriados.items()),1)
    else:
        return feriados

def tabela_patamar_2024(is_feriado, weekday, month, hour):
    # 0: leve, 1: média, 2: pesada
    if is_feriado or weekday in [5, 6]:  # sábado e domingo são 5 e 6 em Python
        if 18 <= hour <= 21:
            return 1
        elif hour == 22 and month in [11, 12, 1, 2, 3]:
            return 1
        else:
            return 0
    else:
        if 0 <= hour <= 7:
            return 0
        elif (8 <= hour <= 13) or (22 <= hour <= 23):
            return 1
        elif (16 <= hour <= 21):
            return 2
        elif hour in [14, 15]:
            return 1 if month in [5, 6, 7, 8] else 2
        else:
            raise ValueError('Erro na tabela')

def Patamares(ano, tabela_patamar):
    # Criar um DataFrame com um range de data e hora para o ano inteiro
    rng = pd.date_range(start=f'{ano}-01-01 00:00', end=f'{ano}-12-31 23:00', freq='h')
    df = pd.DataFrame(rng, columns=['data_hora'])
    df['feriado'] = False
    df['dia_da_semana'] = df['data_hora'].apply(lambda x: x.weekday())

    # Marcando os feriados
    for nome, dia in feriados_nacionais(ano).items():
        df.loc[df['data_hora'].dt.date == dia, 'feriado'] = True

    # Extração de hora e mês
    df['hora'] = df['data_hora'].dt.hour
    df['mes'] = df['data_hora'].dt.month

    # Aplicação da função tabela_patamar para definir o patamar
    df['patamar'] = df.apply(lambda s: tabela_patamar(s['feriado'], s['dia_da_semana'], s['mes'], s['hora']), axis=1)
    df = df.set_index('data_hora')
    return df
    
def AcumulaPatamares(data_inicial, ano, tabela_patamar, dias=None):
    """
    Calcula os patamares acumulados em um período específico.
    Se dias for None, calcula até o final do mês da data_inicial.

    Parâmetros:
    - data_inicial (datetime.date): Data inicial para o cálculo dos patamares.
    - ano (int): Ano de referência para o cálculo dos patamares.
    - tabela_patamar (function): Função de referência para cálculo de patamares.
    - dias (int): Número de dias para o cálculo dos patamares a partir da data_inicial.

    Retorna:
    Tuple (leve, media, pesada) com o acumulado de cada patamar para o período em dias solicitado.
    """
    # Determinar o número de dias até o final do mês
    if dias is None:
        proximo_mes = data_inicial.replace(day=28) + datetime.timedelta(days=4)  # Isso garante que estaremos no próximo mês
        ultimo_dia_do_mes = proximo_mes - datetime.timedelta(days=proximo_mes.day)
        dias = (ultimo_dia_do_mes - data_inicial).days + 1
    
    # Cria um DataFrame para o ano especificado
    df = Patamares(ano, tabela_patamar)

    # Cálculo da soma dos patamares no período especificado
    fim_periodo = data_inicial + datetime.timedelta(days=dias - 1)
    df_periodo = df.loc[f'{data_inicial.year}-{data_inicial.month:02d}-{data_inicial.day:02d}':fim_periodo.strftime('%Y-%m-%d')]['patamar']
    soma = df_periodo.value_counts().reindex([0, 1, 2], fill_value=0).tolist()

    return tuple(soma) 


class DadosPMO:
    def __init__(self, mes, ano):
        self.mes = mes
        self.ano = ano
        self.dia_pmo = self.calcular_dia_pmo()
        self.arvore_gevazp = self.definir_arvore_gevazp()
        self.pesos = self.calcular_pesos()
        self.revisoes = self.calcular_revisoes()
        self.estagios = self.calcular_estagios()
        self.semana_inicial_previvaz = self.calcular_semana_inicial_previvaz()
        self.dias_mes_2 = self.calcular_dias_mes_2()

    def calcular_dia_pmo(self):
        # Lógica para calcular o dia do PMO
        return dia_pmo(self.mes, self.ano)

    def definir_arvore_gevazp(self):
        # Definir o valor da árvore de acordo com o mês
        return (0, 116, 143, 143, 193, 267, 513, 353, 303, 259, 228, 153, 136)[self.mes]

    def calcular_pesos(self):
        # Cálculo dos pesos para cada semana
        pesos = [self.dia_pmo + datetime.timedelta(days=6)]
        pesos[0] = pesos[0].day
        num_dias = calendar.monthrange(self.ano, self.mes)[1] - pesos[0]
        
        while num_dias > 0:
            pesos.append(min(num_dias, 7))
            num_dias -= 7
        
        while len(pesos) < 6:
            pesos.append(0)
        
        return pesos

    def calcular_revisoes(self):
        # Calcular a quantidade de revisões baseado nos pesos
        return self.pesos[1:].count(7) + 1

    def calcular_estagios(self):
        # Calcular a quantidade de estágios baseado nos pesos
        return 7 - self.pesos.count(0)

    def calcular_semana_inicial_previvaz(self):
        # Calcular a semana inicial do Previvaz
        dia_inicial = dia_pmo(1, self.ano)
        return (self.dia_pmo - dia_inicial).days // 7 + 1

    def calcular_dias_mes_2(self):
        # Calcular a quantidade de dias do próximo mês
        proximo_mes = 1 if self.mes == 12 else self.mes + 1
        proximo_ano = self.ano + 1 if self.mes == 12 else self.ano
        dia_inicial = dia_pmo(proximo_mes, proximo_ano) + datetime.timedelta(days=6*0)
        return calendar.monthrange(proximo_ano, proximo_mes)[1] - dia_inicial.day + 1

    def get_dados(self):
        # Retornar um dicionário com todos os dados calculados
        return {
            'DT': self.dia_pmo,
            'pesos': self.pesos,
            'revisoes': self.revisoes,
            'estagios': self.estagios,
            'arvore_gevazp': self.arvore_gevazp,
            'semana_inicial_previvaz': self.semana_inicial_previvaz,
            'dias_mes_2': self.dias_mes_2
        }


pass