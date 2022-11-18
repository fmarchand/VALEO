import streamlit as st
import pandas as pd
import numpy as np
import networkx as nx
import itertools 
import math
from math import factorial as f
from datetime import timedelta
from streamlit import session_state
import matplotlib.pyplot as plt
import json
import collections
import copy
from types import SimpleNamespace
import matplotlib.patches as mpatch

# @st.cache(allow_output_mutation=True)
# def load_data(Size, time):
#     return load_data_brut(Size)

def load_data_brut(file, select = None):
    
    DictLine, DictPos, A0,Comb = new_import()
    dfline = pd.DataFrame(DictLine).T
    dfline.index.name = 'ID'
    dfline.reset_index(inplace = True)

    CombAll = list(DictPos.keys())
    # if select is not None : 
    #     dfline = dfline[~dfline.ID.str.contains('|'.join(select))]
    #     dfslot = dfslot[~dfslot.ID.isin(select)]  
    #     dfslot = {k : v for k,v in DictPos}
    
    confs = pd.read_excel('test.xlsx')
    DataCategorie = {}
    mask = confs['Actif'].notnull()
    df = confs[mask].copy()
    for Categorie in df.Categorie.unique():        
        dfx = df[df.Categorie == Categorie]
        DataCategorie[Categorie] = {
            'Unique' : dfx.Name.unique().tolist(),
            'Values' : dfx.set_index('Name').dropna(axis = 1).to_dict('index')
                    }  
    
    Clist = Comb['C']
    Pompes  = [DataCategorie['Pompe']['Unique'][0]]* len(Comb['P'])
    Pvals   = [DataCategorie['Pompe']['Values'][Pompes[0]][i] for i in ['a','b','c']]
    Nozzles = [DataCategorie['Nozzle']['Unique'][0]] * len(Comb['C'])
    Nvals   = [DataCategorie['Nozzle']['Values'][n]['a'] for n in Nozzles]
    Nvals  = dict(zip(Clist, Nvals))
        
    algo = dict(
        Group = [],
        pop = 50,
        fitness = 'dist',
        crossover = 20,
        mutation = 20,
        Nlim = 2.0,          
        Pmax = 3,
        Plot = False,
        DictPos = DictPos,
        dfline = dfline,
        DictLine = DictLine,
        epoch = 0,
        Nindiv = 0,
        Nrepro = 0,
        indivs = [],
        df = [],
        DataCategorie =  DataCategorie,
        Tuyau = ['Ta'],
        Pompes = Pompes, 
        Pvals = Pvals,     
        EV = ['Ea'],    
        Nozzles  = Nozzles,  
        Nvals = Nvals,               
        confs = confs,
        Clist = Clist,
        Comb = Comb,
        CombAll = CombAll,
        dist = dfline.set_index('ID').dist.to_dict(),
        # height = data['height'],
        A0 = A0,
        )
    algo = SimpleNamespace(**algo)
    return algo

def indiv_create(algo, row = None, NewCtoE = None, NewPtoE = None): 
     
    dfline = algo.dfline
    D = algo.Comb    
    Clist = D['C']
    Ccount = len(D['C'])
        
    # Elist = D['E']
    # ElistMax = D['E']
    # if ElistMax >  algo.Pmax : 
    ElistMax = np.random.choice(D['E'],algo.Pmax) if len(D['E']) >  algo.Pmax  else D['E']
    
    if NewCtoE is not None : CtoE = NewCtoE
    else : CtoE = np.random.choice(ElistMax,Ccount)
    # else : CtoE = np.random.choice(D['E'],Ccount)

    
    d = collections.defaultdict(list)
    for i in range(Ccount): 
        d[CtoE[i]].append(D['C'][i])
    Econnect = dict(sorted(d.items()))
    Edist = dict(sorted(d.items()))
    # Econnect = dict(collections.Counter(CtoE))
    Elist = sorted(Econnect)
    Ecount = len(Elist)      
        
    if row is not None :  
        if Ecount > row.Ecount:
            # print(D['P'],Ecount - row.Ecount)
            # NewEtoP = np.random.randint(0,len(D['P']),Ecount - row.Ecount)
            # NewEtoP = np.random.choice(D['P'],Ecount - row.Ecount)
            NewEtoP = np.random.choice(D['P'],Ecount - row.Ecount)
            EtoP = np.append(row.EtoP, NewEtoP)
        elif Ecount < row.Ecount : 
            EtoP = np.random.choice(row.EtoP,Ecount)
            # print("Ecount",EtoP)
        else :
            EtoP = row.EtoP
        # print(NewCtoE , 'avant',row.Elist,row.EtoP,'apres',Elist,EtoP,row.Ecount, Ecount)
    else : EtoP = np.random.choice(D['P'],Ecount)
    if NewPtoE is not None : EtoP = NewPtoE
    
    d = collections.defaultdict(list)
    for i in range(Ecount):      d[EtoP[i]].append(Elist[i]) 
    Pconnect = dict(sorted(d.items()))   
    # Pconnect = dict(collections.Counter(EtoP))
    Plist = sorted(Pconnect)
    Pcount = len(Plist)    
    
    List_EtoC = [['E{}-C{}'.format(start, end) for end in List] for start , List in Econnect.items()]
    List_PtoE = [['P{}-E{}'.format(start, end) for end in List] for start , List in Pconnect.items()]
        
    Name = list(itertools.chain.from_iterable(List_EtoC + List_PtoE))
    dist_Connect = (dfline.loc[dfline.ID.isin(Name), ['ID','dist']].set_index('ID').dist).to_dict()
    dist = dfline.loc[dfline.ID.isin(Name), 'dist'].sum()
    dist = round(dist,2)
    Name_txt = ','.join(Name)
    
    algo.Nindiv += 1
    col = ['Clist','CtoE','Econnect','Elist','Ecount', 'EtoP',
           'Pconnect','Plist','Pcount', 'List_EtoC','List_PtoE',
           'dist_Connect', 'dist', 'Name','ID', 'Name_txt','Epoch']
    l = [Clist, CtoE,Econnect,Elist,Ecount, EtoP,
         Pconnect,Plist,Pcount, List_EtoC,List_PtoE,
         dist_Connect, dist, Name,algo.Nindiv, Name_txt, algo.epoch]
    # indiv = SimpleNamespace(**dict(zip(col,l)))
    indiv = dict(zip(col,l))
    algo.indivs.append(indiv)
    algo.Nrepro +=1    
    # calcul debit
    d =  Calcul_Debit(algo ,indiv, False)
    # col  = ['PressionList', 'DebitList','Debit']
    # indiv.update({(c): d[c] for c in col})
    indiv.update(d)
    # d =  Calcul_Debit(algo ,indiv, True)
    # indiv.update({(c +'_g'): d[c] for c in col})
    
    info , d = calcul_Masse_cout(indiv, algo)
    indiv.update(d)
    
    # Cond = False
    # for i, (e,EClist) in enumerate(Econnect.items()):
    #     Cond+= np.isin(algo.Group,  EClist).all()
    # indiv['Vg'] = Cond    
    # indiv['Vp'] = False if  (np.array(indiv['Pression_s']) < algo.Nlim).any() else True
    # indiv['Vnp'] = False if indiv['Ecount'] > algo.Pmax  else True
    
    indiv['Alive'] = False if  (np.array(indiv['PressionList']) < algo.Nlim).any() else True 
    # indiv['Alive'] = indiv['Vg']*indiv['Vp']*indiv['Vnp']      
        
    return indiv

def Indiv_reverse(Name,algo):
    NameList = Name.split(',')
    Clist = algo.Clist
    CtoE = {}
    EtoP = {}
    for n in NameList:
        if n[0] == 'E':
            c = int(n[-1])
            e = int(n[1])
            CtoE[c] = e

        if n[0] == 'P':
            e = int(n[-1])
            p = int(n[1])
            EtoP[e] = p
            
    d = dict(sorted(CtoE.items()))
    Clist = list(d.keys())
    CtoE = list(d.values())
    d = dict(sorted(EtoP.items()))
    EtoP = list(d.values())
    indiv = indiv_create(algo, row = None, NewCtoE = CtoE, NewPtoE = EtoP)
    return indiv

def calcul_Masse_cout(indiv, algo): 
    dmasse = {}
    dcout = {}
    # confs = algo.confs

    for Categorie in ['Pompe', 'Tuyau','EV']:
        if Categorie == 'Pompe' : 
            Factor = indiv['Ecount']
            Name = [algo.Pompes[0]]
        if Categorie == 'Tuyau' :
            Factor = indiv['dist']
            Name = algo.Tuyau
        if Categorie == 'EV' :
            Ccount = len(algo.Comb['C'])
            Factor = Ccount
            Name = algo.EV  
        # print(Factor, Name)    
        v = algo.DataCategorie[Categorie]['Values']
        dmasse[Categorie] = int(sum([Factor *v[n]['Masse'] for n in Name]))
        dcout[Categorie]  = int(sum([Factor *v[n]['Cout']  for n in Name]))
        
    dmasse['Reservoir'] = 600
    dcout['Reservoir']  = 30  
    info = [dmasse, dcout]
    Masse = round(sum(dmasse.values()),2)
    Cout = round(sum(dcout.values()),2)
    
    return  info, { 'Masse' : Masse, 'Cout' : Cout}

def calcul_Masse_cout_S(indiv, algo): 
    dmasse = {}
    dcout = {}
    confs = algo.confs

    masse, cout = confs[confs.Name == algo.Pompe][['Masse','Cout']].values[0]
    masse, cout 
    dmasse['Pmasse'] = indiv['Ecount']*masse
    dcout['Pcout']   = indiv['Ecount']*cout

    masse, cout = confs[confs.Name == algo.Tuyau][['Masse','Cout']].values[0]
    masse, cout
    dmasse['Tmasse'] = indiv['dist']*masse
    dcout['Tcout']   = indiv['dist']*cout


    Ccount = len(algo.Comb['C'])
    masse, cout = confs[confs.Name == algo.EV][['Masse','Cout']].values[0]
    masse, cout
    dmasse['Emasse'] = Ccount*masse
    dcout['Ecout']   = Ccount*cout

    dmasse['Reservoir'] = 600
    dcout['Reservoir']  = 30    
    
    info = [dmasse, dcout]
    Masse = round(sum(dmasse.values()),2)
    Cout = round(sum(dcout.values()),2)
    
    return  info, { 'Masse' : Masse, 'Cout' : Cout}

def AG_CrossOver(dfx, algo):    
    c1, c2 = copy.deepcopy(dfx.CtoE.values)
    
    if (c1 != c2).any():        
        m = c1 != c2
        index = np.where(m)[0]
        
        # search for gen diff between indivs = index        
        if len(index) > 1:    
            idx = np.random.choice(index)
        elif len(index) == 1:
            idx = index  
            
        # print(c1, c2,'crossover',index, c1[idx] , c2[idx])           
        c1[idx] , c2[idx] = c2[idx] , c1[idx]
        NewCtoE = c1 , c2
        # print(NewCtoE)
        L = []
        parents = dfx.ID.tolist()
        for i in range(2):
            row = dfx.iloc[i]            
            indiv = indiv_create(algo, row,NewCtoE[i]) 
            indiv['parent'] =  parents
            L.append(indiv)
        return L 

def Mutation(row, algo): 
    NewCtoE = copy.deepcopy(row.CtoE)
    idx = np.random.randint(len(NewCtoE))
    D = algo.Comb
    l = [e for e in D['E'] if e != NewCtoE[idx]]
    e = np.random.choice(l,1)[0]
    NewCtoE[idx] = e
    indiv = indiv_create(algo, row,NewCtoE)
    indiv['parent'] =  [row.ID]
    return indiv

def indiv_init(algo, pop):
    algo.Nindiv = 0 
    algo.indivs = []
    algo.epoch = 0
    algo.Nrepro = 0
    L = []
    for i in range(pop):        
        indiv = indiv_create(algo)        
        L.append(indiv)
    df = pd.DataFrame(L)
    df = df.drop_duplicates(subset='Name_txt')
    df = df.reset_index(drop = True)
    
    return df

def debit(algo, d_EtoC_list,d_PtoE,Clist, group = True, split = True):
    if not group : split = False

    p = [-5.16e-04, -1.54e-02, 4.87]
    p = algo.Pvals

    cE0 = 7.64e-04
    coef_E = 0 if split else cE0
    
    coef_C  = 0.036
    coef_C  = [algo.Nvals[i] for i in Clist]
    coef_C  = np.array(coef_C)
    coef_d  = 2.35e-04    
    
    A = coef_E + d_EtoC_list * coef_d + coef_C 
    Z = ( A**-0.5).sum() if group else A**-0.5
    coef_E = cE0 if split else 0
    As = p[0] - (coef_d * d_PtoE) - 1/(Z**2) - coef_E
    Bs = p[1]
    Cs = p[2]
    delta = (Bs**2) - (4 * As * Cs)
    Qt  = np.array((- Bs - delta**0.5)/(2*As))
    Pt = np.array(Qt**2 / Z**2)
    a0 = p[0] * (Qt**2) + p[1] * Qt + p[2] - Pt
    Qi = (Pt / A)**0.5
    Pi = coef_C * (Qi**2)
    key = ['Qt','Pt','Qi','Pi']
    val = [Qt, Pt, Qi, Pi]
    val = [v.round(2) for v in val]
    return dict(zip(key,val))

def Calcul_Debit(algo ,indiv, group):
    D = algo.Comb  
    Group = algo.Group  
    Clist = D['C']
    Econnect = indiv['Econnect']
    Pconnect = indiv['Pconnect']
    EtoP = indiv['EtoP']
    Pression = []
    Debit = []
    # Data = {}
    # Pression_C = []
    # on loop sur chaque EV pour connect to C et faire calcul Pt Qt coté pompe et Pi Qi coté Capteur
    Cpression = {}
    Cdebit = {}
    grouped = False
    for i, (e,EClist) in enumerate(Econnect.items()):
        p = EtoP[i]
        name = 'P{}-E{}'.format(p,e)
        VerifGroup = np.isin(Group,  EClist)
        # EClistTotal = [EClist]
        # if VerifGroup.all() & (len(Group) > 0):
        EClistTotal = [[i for i in EClist if i in Group], [i for i in EClist if i not in Group]]          
        grouped = True
        for j,  EClist in enumerate(EClistTotal):
            if j >0 : grouped = False # bascule a No group apres le passage group 
            if len(EClist)>0: # bug avec calcul array
                d_EtoC_list = np.array([algo.dist['E{}-C{}'.format(e,c)] for c in EClist])
                d_PtoE = algo.dist['P{}-E{}'.format(p,e)]
                res = debit(algo, d_EtoC_list,d_PtoE, EClist, grouped)

                Debit = Debit + list(res['Qi'])
                Pi = list(res['Pi'])
                PressionConnect = dict(zip(EClist, Pi))
                Cpression.update(PressionConnect)
                
                Qi = list(res['Qi'])
                Cdebit.update(dict(zip(EClist, Qi)))
                
                # Data[name] = res        
                # Pression = Pression + list(res['Pi'])          
                # print(dc,dp,Clist,list(res['Pi']))
                # Pression_C = Pression_C + [PressionConnect]
                # print(i, j ,Group,grouped, EClistTotal ,EClist, PressionConnect)
    PressionList = [Cpression[i] for i in D['C']]
    DebitList    = [Cdebit[i] for i in D['C']]
    # print(Cpression)
    SumDebit = round(sum(Debit),1)
    # keys = ['info','Data','Pression','Debit','SumDebit']
    # vals = [info, Data,Pression, Debit, SumDebit]     
    keys = ['PressionList','DebitList','Debit']
    vals = [PressionList, DebitList, SumDebit] 
    return dict(zip(keys,vals))

def new_import():
    print('new_import')
    dfmap = pd.read_excel('test.xlsx', sheet_name= 'map (4)', header=None)
    
    SlotColor = {'C' : 10, 'E': 20, 'P' : 30}
    slots = ['C','P','E']
    
    
    A0 = dfmap.values
    Size = max(A0.shape)
    DistFactor = 3 * Size / 3
    
    Comb = collections.defaultdict(list)
    DictPos = {}    
    ListBegin = []
    ListEnd = []
    for iy, ix in np.ndindex(A0.shape):
        v = A0[iy, ix]
        if type(v) == str: 
            slot = v[0]
            A0[iy,ix] = SlotColor[slot]*20
            Comb[v[0]].append(int(v[1:]))
            DictPos[v] = (iy,ix)   
            if slot == "E" : ListBegin.append(v)
            else : ListEnd.append(v)
            
    A0 = A0.astype(float)      
    Ax = np.ones((Size,Size))
    Ax[:A0.shape[0],:A0.shape[1]] = A0
    ListBegin, ListEnd = sorted(ListBegin), sorted(ListEnd)
        
    Path = {}
    DictLine = {}
    
    for begin in ListBegin:
        start = DictPos[begin]
        A = Ax.copy()
        A1 = Path1(A,start)
        for end in ListEnd: 
            goal = DictPos[end]        
            path = Path2(A1.copy() ,start,  goal)
            path = np.array(path)       
            dist = (np.abs(np.diff(path.T)).sum() / DistFactor).round(2)
            
            if end[0] == 'C' : ID = begin + '-' + end
            else : ID = end + '-' + begin

            DictLine[ID] = {'path' : path, 'dist' : dist}        

    return DictLine, DictPos, A0,dict(Comb)
      
def new_plot(algo,SelectLine, SelectSlot):
    DictLine = {k:v for k,v in algo.DictLine.items() if k in SelectLine}
    DictPos  = {k:v for k,v in algo.DictPos.items()  if k in SelectSlot}
    LenPath = len(DictLine)
    A0 = algo.A0
    Ymax , Xmax = A0.shape
    PlotColor = {'C' : "#93c9ee", 'E': '#a2ee93', 'P' : "#c593ee"}
    fig, ax = plt.subplots(figsize = (8,8))

    f = ax.add_patch(mpatch.Rectangle((0,0), Xmax-1, Ymax-1, color='#d8d8d8'))
    # masked = np.ma.masked_where(A0 <= 1, A0)
    MinOffset = LenPath*0.03
    MinOffset = MinOffset if MinOffset < 0.4 else 0.4
    offset = np.linspace(-MinOffset,MinOffset,LenPath)
    for i, (slot,data) in enumerate(DictLine.items()):
        n = offset[i]  
        p = data['path']
        if slot[0] == 'E' : 
            f = ax.plot(p[:,1]+n,p[:,0]+n,"#32cdff", linewidth=2, zorder=1, linestyle ='-')
        else : 
            f = ax.plot(p[:,1]+n,p[:,0]+n,"#3286ff", linewidth=3, zorder=1, linestyle ='-')

    style = dict(size= 15 * 9 / Ymax, color='black')
    for slot, pos in DictPos.items(): 
        x , y = pos
        Type = slot[0]
        color = PlotColor[Type]
        f = ax.add_patch(mpatch.Rectangle((y-0.45,x-0.45), 0.9, 0.9, color=color))
        f = ax.add_patch(mpatch.Rectangle((y-0.45,x-0.45), 0.9, 0.9, color='black', fill = None))
        f = ax.text(y, x+0.1,slot[1:] , **style,  ha='center', weight='bold') 
    f = ax.imshow(np.zeros(A0.shape), cmap='gray',vmin=0,vmax=1)  
    return  fig

def Path1(A,start): 
    N = len(A)
    v0 = np.array([-1,1,-N,N])
    #     v0 = np.array([-1,1,-N,N, -N-1, -N+1,N+1,N-1])
    Dim = len(v0)
    e = 2
    A[start] = e
    a = A.reshape(-1)
    v = np.where(a == e)  

    while len(v) > 0 :
        v = np.tile(v, (Dim, 1)).T + v0
        v = v[np.where(a[v]==0)]
        v = np.unique(v)        
        e+=1
        a[v]=e
    return a.reshape((N,N))

def Path2(A,start,goal):
    N = len(A)
    v0 = np.array([-1,1,-N,N])
    #     v0 = np.array([-1,1,-N,N, -N-1, -N+1,N+1,N-1])
    Dim = len(v0)
    e1,e2  = A[start] , A[goal]
    a = A.reshape(-1)
    v = goal[1] + goal[0]*N
    L  = [goal]
    while e2 > 2:
        v = v + v0
        v[v > len(a)] = len(a)-1
        v = v[np.where((a[v] < e2) & (a[v] >= 2))]
        idx = a[v].argmin()
        v = v[idx]
        e2 = a[v]
        pos = (int(np.ceil(v/N)-1),  v%N)
        L.insert(0,pos)
    return L  


  