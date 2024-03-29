
def load_data_brut_S(file, select = None):
    
    with open(file, 'r') as f:
      data = json.load(f)

    dfslot = pd.DataFrame(data['layers'][1]['objects']).drop(columns= ['rotation','width','height','visible','gid']).rename(columns = {'class' : 'Class', 'name' : 'Name'})
    dfslot.x = (dfslot.x/16).astype(int)
    dfslot.y = (dfslot.y/16).astype(int) - 1
    dfslot.Name = pd.to_numeric(dfslot.Name)
    dfslot['ID'] = dfslot.Class + dfslot.Name.astype(str)
    dfslot['Color'] = dfslot['Class'].map({'C':10,'E':20,'P':30})

    dfline  = pd.DataFrame(data['layers'][2]['objects']).drop(columns=['rotation','width','name','height','visible','id']).rename(columns = {'class' : 'Class'})
    for idx, row in dfline.iterrows():
        properties = row.properties
        # properties = properties[:0] + properties[-2:]
        dfline.loc[idx, ['end','long','start']] = [d['value'] for d in properties]    
        polyline = row.polyline
        x,y = row.x,row.y
        polyline = [(p['x'] + x, p['y'] + y) for p in polyline]
        p = np.array(polyline)
        dfline.at[idx , 'polyline'] = p   
        dfline.loc[idx ,'dist'] = np.abs(np.diff(p.T)).sum()
    dfline.start = pd.to_numeric(dfline.start)
    dfline.end = pd.to_numeric(dfline.end)
    dfline.dist = (dfline.dist.astype(int)*2/100).round(2)
    dfline = dfline.drop(columns= ['properties','x','y'])
    t = dfline.Class.str.split('-')
    dfline['ID'] = t.str[1] + dfline.end.astype(str) + '-' + t.str[0] + dfline.start.astype(str)
    dfline = dfline.sort_values('ID').reset_index(drop = True)
    
    CombAll = dfslot.ID.tolist()

    # DropList = ['C0','E2']
    # DropList = []
    # if len(DropList) > 0 : 
    # if select is not None : 
    #     dfline = dfline[~dfline.ID.str.contains('|'.join(DropList))]
    #     dfslot = dfslot[~dfslot.ID.isin(DropList)]
    if select is not None : 
        dfline = dfline[~dfline.ID.str.contains('|'.join(select))]
        dfslot = dfslot[~dfslot.ID.isin(select)]  
    A0 = data['layers'][0]['data']
    height = data['height']
    A0 = np.array(A0).reshape(10,7)
    pas = 16
    unique = np.unique(A0)
    A0[A0 == unique[0]] = 0
    A0[A0 == unique[1]] = 1
    
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
        
    Comb = dfslot.groupby('Class').Name.unique().apply(list).apply(sorted).to_dict()
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
        crossover = 0.4,
        mutation = 0.4,
        Nlim = 2.0,          
        Pmax = 3,
        Plot = False,
        dfslot = dfslot,
        dfline = dfline,
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
        height = data['height'],
        A0 = A0,
        )
    algo = SimpleNamespace(**algo)
    return algo


def plot_(algo,dflineSelect, dfsSelect, name): 
    A0 = algo.A0.copy()
    
    for idx, row in dfsSelect.iterrows():
        A0[row.y, row.x] = row.Color + int(row.Name)   
        
    A = np.kron(A0, np.ones((16,16), dtype=int))
    fig, ax = plt.subplots(figsize = (8,8))
    ax.set_title(name)
    plt.xticks([])
    plt.yticks([])
    ax.imshow(A)
    for idx, row in dflineSelect.iterrows():
        p = row.polyline
        f = ax.plot(p[:,0],p[:,1],'k', linewidth=4)

    style = dict(size=15, color='black') 
    for idx, row in dfsSelect.iterrows():
        x = row.x*16
        y = row.y*16
        text = row.Class + str(row.Name)
        f = ax.text(row.x*16+8, row.y*16+8,text , **style,  ha='center', weight='bold') 
    return fig



    # with st.form("Select"): 
    #     select = st.multiselect('Pattern',algo.CombAll, algo.CombAll)
    #     select = [s for s in algo.CombAll if s not in select]
    #     if select == [] : select = None
    #     submitted = st.form_submit_button("Submit & Reset")      

    #     if submitted:
    #         # file = {'SheetMapName' : algo.SheetMapName, 'uploaded_file' : algo.uploaded_file} 
    #         print('submitted Select')
    #         algo = load_data_brut(file, select)
    #         algo.df = indiv_init(algo, pop)
    #         session_state['algo'] = algo
    
'''col select'''
   # ColdropTest = ColAlgo + ColSysteme + ColResults + ColBus
    # dfCol = df1.columns
    # print([c for c in dfCol if c not in ColdropTest])
    # ColBase ['Ptype0', 'Ptype', 'PtypeCo', 'PompeCountFinal', 'ID', 'Epoch', 'dist', 'Esplit', 'Debit', 'Masse', 'Cout', 'fitness', 'Alive']
    # print(df1)
    # ColSelect = []
    # ColSt = st.columns(5)
    # ColCatList = [ColAlgo, ColSysteme, ColResults,ColBus]
    # ColCatName= ['ColAlgo', 'ColSysteme', 'ColResults','ColBus']
    # for i in range(len(ColCatList)):
    #     ColSelect += ColSt[i].multiselect(label = ColCatName[i],options = ColCatList[i],default=ColCatList[i], help = str(ColCatName[i]))
    # ColSelect = st.multiselect(label = 'Columns',options = df1.columns,default=ColBase, help = 'Columns')    


    # if not c2.checkbox('Algo'   , value = False, help = str(ColAlgo)) : Col_drop += ColAlgo
    # if not c3.checkbox('System' , value = False, help = str(ColSysteme)) : Col_drop += ColSysteme
    # if not c4.checkbox('Results', value = False, help = str(ColResults)) : Col_drop += ColResults 
    # if not c5.checkbox('BUS'    , value = False, help = str(ColBus)) : Col_drop += ColBus       
    # if not c6.checkbox('Pompe'  , value = False, help = str(ColPompe)) : Col_drop += ColPompe  
    # print(len(algo.indivs))       
    
def Calcul_Debit(algo ,indiv, split):
    D = algo.Comb  
    Group = algo.Group  
    Clist = D['C']
    Econnect = indiv['Econnect']
    Pconnect = indiv['Pconnect']
    EtoP = indiv['EtoP']
    Ptype = indiv['Ptype']
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
        pt = Ptype[i]
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
                res = debit(algo, d_EtoC_list,d_PtoE, EClist,pt, grouped, split = split)

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