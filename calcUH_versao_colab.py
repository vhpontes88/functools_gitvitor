import numpy as np
import pandas as pd
import csv
import os 

excecoes = [45,46,62,63,153] 

def qqq(x):    
    return int(x[:x.index(" ")])

def cota_montante(usina):
    '''
        O que essa funcao faz?
    '''
    
    vol_min = float(usina['Vol.min.(hm3)'])
    
    if (usina['Reg'] == "D"):
        cota_montante = usina['Cota Máx.(m)']
        
    else:
        vol = usina['Vol_util'] + vol_min
        parc0 =  float(usina['PCV(0)'])/1  * (vol**1 - vol_min**1)
        parc1 = (float(usina['PCV(1)'])/2) * (vol**2 - vol_min**2)
        parc2 = (float(usina['PCV(2)'])/3) * (vol**3 - vol_min**3)
        parc3 = (float(usina['PCV(3)'])/4) * (vol**4 - vol_min**4)
        parc4 = (float(usina['PCV(4)'])/5) * (vol**5 - vol_min**5)        
        cota_montante = (1 / (vol - vol_min)) * (parc0 + parc1 + parc2 + parc3 + parc4)
    return cota_montante

def queda_liq(usina):

    if (int(usina['Tipo Perdas(1=%/2=M/3=K)']) == 1):
        queda_liq = (usina['Cota Montante'] - usina['Canal Fuga Médio(m)']) * (1 - usina['Valor Perdas']/100)
    
    else:
        queda_liq = usina['Cota Montante'] - usina['Canal Fuga Médio(m)'] - usina['Valor Perdas']
    
    return queda_liq
    
def outra_cota_montante(usina):
    
    if (usina['Reg'] == "D"):
        outra_cota_montante = usina['Cota Máx.(m)']
        
    else:
        vol_real = usina['Vol_util'] * usina['Vol_ini_por']/100
        if vol_real == 0:
            outra_cota_montante = usina['Cota min.(m)']
        else:
            vol_min = usina['Vol.min.(hm3)']
            vol = vol_real + vol_min
            parc0 =  float(usina['PCV(0)'])/1  * (vol**1 - vol_min**1)
            parc1 = (float(usina['PCV(1)'])/2) * (vol**2 - vol_min**2)
            parc2 = (float(usina['PCV(2)'])/3) * (vol**3 - vol_min**3)
            parc3 = (float(usina['PCV(3)'])/4) * (vol**4 - vol_min**4)
            parc4 = (float(usina['PCV(4)'])/5) * (vol**5 - vol_min**5)        
            outra_cota_montante = (1 / (vol - vol_min)) * (parc0 + parc1 + parc2 + parc3 + parc4)

            if(outra_cota_montante <= usina['Cota min.(m)']):
                outra_cota_montante = usina['Cota min.(m)']
            
    return outra_cota_montante

def outra_queda_liq(usina):

    if (int(usina['Tipo Perdas(1=%/2=M/3=K)']) == 1):
        outra_queda_liq = (usina['Cota Montante %'] - usina['Canal Fuga Médio(m)']) * (1 - usina['Valor Perdas']/100)

    
    else:
        outra_queda_liq = usina['Cota Montante %'] - usina['Canal Fuga Médio(m)'] - usina['Valor Perdas']
        
    return outra_queda_liq

## Precisamos re-escrever as funcoes soma e soma1

def soma(a,data):
    cod  = a['Cod Usina']
    jusante = a['Jus']
    soma = 0
    soma = a['Produtibilidade']
    recebe = a['Sist'] 
    
    while jusante in data.index:
        prod_ind = data.loc[jusante]['Produtibilidade']
        if data.loc[jusante]['Sist'] != recebe:
            break
        if jusante == 268: # não sei pq soma na cascata de 169 e nessa ñ
            prod_ind = 0
        if not np.isnan(data.loc[jusante]['Vol_ini_por_origin']) or data.loc[jusante]['Usina'].startswith('FICT.'):
            soma = soma + prod_ind   
        if jusante == 176:
            soma = soma + prod_ind
        jusante = data.loc[jusante]['Jus']
    if cod in excecoes:
        soma = soma - data['Produtibilidade'].loc[66]
        
    return soma

def soma1(a,data):
    cod  = a['Cod Usina']    
    jusante = a['Jus']
    soma1 = 0
    soma1 = a['Produtibilidade %']
    recebe = a['Sist'] 
    
    while jusante in data.index:
        prod_ind = data.loc[jusante]['Produtibilidade %']    
        if data.loc[jusante]['Sist'] != recebe:
            break
        if jusante == 268: # não sei pq soma na cascata de 169 e nessa ñ
            prod_ind = 0
        if not np.isnan(data.loc[jusante]['Vol_ini_por_origin']) or data.loc[jusante]['Usina'].startswith('FICT.'):
            soma1 = soma1 + prod_ind   
        if jusante == 176:
            soma1 = soma1 + prod_ind        
        jusante = data.loc[jusante]['Jus']
    if cod in excecoes:
        soma1 = soma1 - data['Produtibilidade %'].loc[66]
        
    return soma1


def main(path_dadger, path_cad_usih='CadUsH.csv', med=730.5, MES = '', UH_ALTERA=None ):

    if UH_ALTERA==None:UH_ALTERA={}

    nomes_meses = ['JAN','FEV','MAR','ABR','MAI','JUN','JUL','AGO','SET','OUT','NOV','DEZ']
    
    meses =np.array([(i,j) for (j,i) in enumerate(nomes_meses,start=1)])
    meses = pd.DataFrame(meses, columns=['Mes', 'Numero'])
    meses = meses.set_index("Mes")

    with open( path_dadger , 'r',encoding='latin-1') as arquivo:
        linhas = arquivo.readlines()

    for i in range(len(linhas)-1,0,-1):
        if linhas[i][:24].startswith("& MES INICIAL DO ESTUDO"):
            mes = int(linhas[i][39:41])            
            break
    
    if MES=='':MES = nomes_meses[mes-1]
    
    UH = []
    AC = []
    
    for l in linhas:     
        if (l[:3] == 'UH '):
            UH.append(l)           
        elif (l[:3] == 'AC '):
            AC.append(l)
    
    usinas = []
    for k in range(len(UH)):
        usinas.append({'CodUsina': float(UH[k][3:7]),'REE': int(UH[k][8:11]), 'Vol_ini_por': float(UH[k][12:24])}) # esse valor esta em porcentagem %
    UH_usinas = pd.DataFrame.from_dict(usinas)
    
    UH_usinas['CodUsina'] = UH_usinas['CodUsina'].astype('int32')
    
    cadastro_usinas1 = pd.read_csv(path_cad_usih,encoding='latin-1',sep = ";")
    
    df = cadastro_usinas1[['CodUsina','Usina','Sistema','Posto','Jusante','Vol.Máx.(hm3)','Vol.min.(hm3)','Cota Máx.(m)','Cota min.(m)','PCV(0)','PCV(1)','PCV(2)','PCV(3)','PCV(4)','Prod.Esp.(MW/m3/s/m)','Canal Fuga Médio(m)','Num.Unid.Base','Tipo Perdas(1=%/2=M/3=K)','Valor Perdas','Reg']]
    df = df.dropna()
    
    df['Jus']=df['Jusante'].map(qqq)
    df['Sist']=df['Sistema'].map(qqq)
    df['Num. de maq. Oper.']=df['Num.Unid.Base']
    
    df['CodUsina'] = df['CodUsina'].astype('int32')
    
    df =df.set_index('CodUsina')
    
    UH_usinas = UH_usinas.set_index('CodUsina')
    
    for cod,val in UH_ALTERA.items():
        if cod in UH_usinas.index:
            UH_usinas.loc[cod,'Vol_ini_por'] = val
    
    data1 = df.join(UH_usinas).drop_duplicates() # join pelo index que sao os codigos
    
    data1.loc[data1['Reg'] == 'D', 'Vol.min.(hm3)'] = data1.loc[data1['Reg'] == 'D', 'Vol.Máx.(hm3)']  # usinas fio dagua no csv do ons
    
    usinas_fict=pd.DataFrame({'CodUsina':[291,292,294,295,298,299,301,302,303,306,307,308,317,318,319], #'Usina': ['FICT.SERRA M','FICT.CANA BR','FICT.QUEIMAD','FICT.TRES MA','FICT.IRAPE','FICT.COUTO M','FICT.SAO JER','FICT.LAJEADO','FICT.PEIXE A', 'FICT.SAO SAL','FICT.MURTA','FICT.RETIRO', 'FICT.TIBAGI','FICT.STA BRA','FICT.MAUA'],           
                                  'REE': [4,4,3,3,3,0,0,4,4,4,0,3,0,0,12]}) # matriz de usinas FICT.
    
    usinas_fict = usinas_fict.set_index('CodUsina')
       
    for k in usinas_fict.index:        
        if k in data1.index:        
            data1.loc[k,'REE'] = usinas_fict.loc[k,'REE']
            
    usina_NOTNAN = data1[~np.isnan(data1['Vol_ini_por'])].copy(deep=True)
    usina_NAN = data1[np.isnan(data1['Vol_ini_por'])].copy(deep=True)
    
    for i in usina_NAN.index:
        if  usina_NAN['Usina'].loc[i][:5] == 'FICT.':
            for p in range(len(usina_NOTNAN['Posto'])):
                if (usina_NOTNAN['Posto'].iloc[p] == usina_NAN['Posto'].loc[i]):
                    usina_NAN.loc[i,'Vol_ini_por'] = usina_NOTNAN['Vol_ini_por'].iloc[p]
                    if i == 291:
                        if usina_NOTNAN['Vol_ini_por'].iloc[p] <= 55:
                            usina_NAN.loc[i,'Vol_ini_por'] = (usina_NOTNAN['Vol_ini_por'].iloc[p]/55)*100
                        elif usina_NOTNAN['Vol_ini_por'].iloc[p] >= 55:
                            usina_NAN.loc[i,'Vol_ini_por'] = 100
                   
    data=pd.concat([usina_NOTNAN,usina_NAN])
        
    h=data['Usina'].dtypes
    
    FLO_AT = ['Vol.Máx.(hm3)', 'Vol.min.(hm3)', 'Cota Máx.(m)', 'Cota min.(m)' ,'PCV(0)', 'PCV(1)', 'PCV(2)', 'PCV(3)',
              'PCV(4)', 'Prod.Esp.(MW/m3/s/m)', 'Canal Fuga Médio(m)', 'Num.Conj.Máq.', 'Tipo Perdas(1=%/2=M/3=K)', 
              'Valor Perdas', 'Num. de maq. Oper.', 'Vol_ini_por']#, 'Vol_util', 'Cota Montante']
    
    for c in data.columns:        
        if data[c].dtypes.name == 'object':            
            data[c] = [x.replace(',', '.') for x in data[c]]
        if c in FLO_AT:
            data[c] = data[c].astype(float)      
    
    for k in AC:
        l = [] # criando lista
        k=k[:-1] # tirando o \n    
        for i in k.split(" "):
            if len(i) > 0:
                l.append(i)
                
        #JUSMED
            
        if len(l) >= 6 and l[2] == 'JUSMED' and  l[5] == '1' and l[4] == MES:
            #print(l)
            data.loc[int(l[1]),'Canal Fuga Médio(m)'] = float(l[3])
            
        elif len(l) <= 4 and l[2] == 'JUSMED':
            data.loc[int(l[1]),'Canal Fuga Médio(m)'] = float(l[3])        
        
        #JUSENA    
        if len(l) >= 4 and l[2] == 'JUSENA':
            data.loc[int(l[1]),'Jus'] = int(l[3])
        
        #VOLMIN        
        if len(l) >= 5 and l[2] == 'VOLMIN' and l[4] == MES and  l[5] == '1':
            data.loc[int(l[1]),'Vol.min.(hm3)'] = float(l[3])
            if data.loc[int(l[1]),'Reg'] == 'D': 
                data.loc[int(l[1]),'Vol.Máx.(hm3)'] = float(l[3])
        elif len(l) <= 4 and l[2] == 'VOLMIN':
            data.loc[int(l[1]),'Vol.min.(hm3)'] = float(l[3])
            if data.loc[int(l[1]),'Reg'] == 'D': 
                data.loc[int(l[1]),'Vol.Máx.(hm3)'] = float(l[3])

        #VOLMAX
        if len(l) >= 5 and l[2] == 'VOLMAX'and l[4] == MES and  l[5] == '1':
            data.loc[int(l[1]),'Vol.Máx.(hm3)'] = float(l[3])
            if data.loc[int(l[1]),'Reg'] == 'D': 
                data.loc[int(l[1]),'Vol.min.(hm3)'] = float(l[3])  
        elif len(l) >= 4 and l[2] == 'VOLMAX':
            data.loc[int(l[1]),'Vol.Máx.(hm3)'] = float(l[3])
            if data.loc[int(l[1]),'Reg'] == 'D': 
                data.loc[int(l[1]),'Vol.min.(hm3)'] = float(l[3])  

        #NUMMAQ
        if len(l) >= 7 and l[2] == 'NUMMAQ' and  l[6] == '1' and l[5] == MES:
            #['AC', '227', 'NUMMAQ', '1', '1', 'OUT', '1']
            # a casa 3 é refernet ao conjunto e a casa 4 referente ao nº de máquinas nele
            #print(l)
            if data.loc[int(l[1]),'Num. de maq. Oper.'] > float(l[4]):
                data.loc[int(l[1]),'Num. de maq. Oper.'] = 0        
            #data.loc[int(l[1]),'Num. de maq. Oper.'] = float(l[4])
        elif len(l) <= 5 and l[2] == 'NUMMAQ':
            if data.loc[int(l[1]),'Num. de maq. Oper.'] > float(l[4]):
                data.loc[int(l[1]),'Num. de maq. Oper.'] = 0        
            #data.loc[int(l[1]),'Num. de maq. Oper.'] = float(l[3])

        #PROESP
        if len(l) >= 5 and l[2] == 'PROESP':
            # acho q é igual a esse aqui
            # ['AC', '181', 'NUMJUS', '129']
            data.loc[int(l[1]),'Prod.Esp.(MW/m3/s/m)'] = int(l[3])
        
        #TIPERH
        if len(l) >= 4 and l[2] == 'TIPERH':
            # acho q é igual a esse aqui
            # ['AC', '181', 'NUMJUS', '129']
            #print(l)
            data.loc[int(l[1]),'Tipo Perdas(1=%/2=M/3=K)'] = int(l[3])
        
    data['Vol_util'] = data['Vol.Máx.(hm3)'].astype(float) - data['Vol.min.(hm3)'].astype(float)
        
    # Trecho alterado vitor
    # for i in range(len(data['Usina'])):
        # if data['Usina'].iloc[i] == 'FICT.SERRA M':
            # data['Vol_util'].iloc[i] = data['Vol_util'].iloc[i] * 0.55
            # break
    data.loc[data['Usina']=='FICT.SERRA M','Vol_util'] = data.loc[data['Usina']=='FICT.SERRA M','Vol_util'] * 0.55
            
    data['Vol_ini_por_origin'] = data['Vol_ini_por'].copy(deep=True)
    data['Vol_ini_por'] = data['Vol_ini_por'].fillna(0)
            
    data['Cod Usina'] = data.index
    data['Cota Montante'] = data.apply(cota_montante,axis=1)
    
    #print(data['Cota Montante'].dtypes)
    data['Queda Líquida'] = data.apply(queda_liq,axis=1)
    
    data['Cota Montante %'] = data.apply(outra_cota_montante,axis=1)
    #print(data['Cota Montante'].dtypes)
    data['Queda Líquida %'] = data.apply(outra_queda_liq,axis=1)
    
    
    data['Produtibilidade1'] =data['Prod.Esp.(MW/m3/s/m)']*data['Queda Líquida']
    data['Produtibilidade'] = data['Produtibilidade1']
    
    data['Produtibilidade1 %'] =data['Prod.Esp.(MW/m3/s/m)']*data['Queda Líquida %']
    data['Produtibilidade %'] = data['Produtibilidade1 %']        
    
    
    
    # for i in range(len(data['Num. de maq. Oper.'])):
        # if data['Num.Unid.Base'].iloc[i] != data['Num. de maq. Oper.'].iloc[i]:
            # data['Produtibilidade'].iloc[i] = data['Produtibilidade'].iloc[i] * data['Num. de maq. Oper.'].iloc[i]/data['Num.Unid.Base'].iloc[i]
            # data['Produtibilidade %'].iloc[i] = data['Produtibilidade %'].iloc[i] * data['Num. de maq. Oper.'].iloc[i]/data['Num.Unid.Base'].iloc[i]
            
    # Alterado Vitor
    for idx in data.loc[(data['Num.Unid.Base'] != data['Num. de maq. Oper.'])].index:
        for col in ['Produtibilidade','Produtibilidade %']:
            data.loc[idx,col] = data.loc[idx,col] * data.loc[idx,'Num. de maq. Oper.']/data.loc[idx,'Num.Unid.Base']
    
    
    # Essa e a parte demorada do codigo pois calcula a prodt acumulada de cada usina por vez repetindo o loop o(n2) (vitor)
    # Trecho passivel de melhoria
    
    data['Soma Produtibilidade'] = data.apply(soma,axis=1,args=[data])
    data['Soma Produtibilidade %'] = data.apply(soma1,axis=1,args=[data])    
        
    data['Earm'] = ((10 ** 6) / (60 * 60)) * data['Soma Produtibilidade'] * data['Vol_util']
    data['Earm %'] = ((10 ** 6) / (60 * 60)) * data['Soma Produtibilidade %'] * data['Vol_util'] * data['Vol_ini_por']/100
    
    abc = data.copy(deep=True)
    abc['REE'] = data['REE'].replace(0, np.nan)
    
    abc=abc.dropna(subset=['REE'])
    
    AGG = {'Earm %':'sum','Earm':'sum'}
    #REE = abc.groupby(by='REE').sum()/med
    REE = abc.groupby(by='REE').agg(AGG)/med
    
    #sistema = abc.groupby(by='Sist').sum()/med
    sistema = abc.groupby(by='Sist').agg(AGG)/med
    
    arr = []
    
    for i in sistema['Earm %']:arr.append(i)
    
    for i in sistema['Earm']:arr.append(i)
    
    total = []
    
    count = 4
    
    for i in range(0, len(sistema['Earm %'])):        
        total.append(arr[i] / arr[count])
        count = count + 1
    
    # return total, sistema, REE, data1 # data1 tem tudo
    # return data1
    return 100*np.array(total).round(4)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    