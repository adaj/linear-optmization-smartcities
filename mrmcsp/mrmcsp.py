import pulp
import pandas as pd
from data3_mrmcsp import *
from scipy.spatial import distance


"""
This is a calculation of routes between origins and destinations
it append to a dictionary (keys are a origin-destination pair id)
Example:
    example = ['o0_s0_s1_s2_s9_d0', 'o0_s2_s3_s8_d0'] is a set of routes between o0 and d0
    routes = {'0':example, ...}
"""
routes = {}
r = []
def route(d,tree_top,path):
    global routes
    global r
    path+=tree_top #append to the path
    son = []
    if 'd{}'.format(d) in tree_top: # a path gets from origin to a destination
        routes["r-{}".format(d)].append(path) # it becomes a route
        r.append(path)
        return
    else: # keep drilling
        for i in streets:
            if tree_top==i.split('_')[0]:
                son.append(i.split('_')[1])
        if len(son)==0:
            return path
        for s in son:
            route(d, s, path+'_') # recursive call
for d in range(3):
    routes["r-{}".format(d)] = []
    route(d,'o{}'.format(d),'')
r = {"r{}".format(i):r_ for i,r_ in enumerate(r)}
print(len(r),'routes')

"""
dij is a dictionary with the manhattan distances between i and j
 - case 1 (d = 0.8*d):  if bus stops i and j are on the same route
 - case 2 (d = d):      if bus stops i and j are on different routes
 - case 3 (d = inf):    if bus stops i and j don't have a street between them

Example:
 dij = {'s0_s1':3, 's0_d0':inf, ...}
"""
dij = {}
flag = False
for i in stops.keys():
    for j in stops.keys():
        d =  distance.cityblock(stops[i],stops[j])
        s = "{}_{}".format(i,j)
        if s in streets: # if s is a street
            for od in routes.keys():
                for r_ in routes[od]: # if s is inside a route
                    if s in r_:
                        d = 0.5*d
                        flag=True
                        break
                if flag:
                    break
            flag = False
        else:
            d = 10000000
        dij[s]=d
dij

s_notallowed = []
for i in dij:
    if dij[i] > 1000:
        s_notallowed.append(i)

"""
Nm is a dictionary with a list of bus stops j that are closer to m as
values and key as the ridership service area id

Example:
Nm = {m0: ['s2','s7', 's8'], m1: ['s3','s7'], ...}
"""
# Nm = {j | Dmj<S}
S = 2.5
Nm = {M:[j for j in stops if distance.cityblock(m[M]['position'],stops[j])<S] for M in m} #TODO: just one m for each stop?
# Nm



"""
Decision Variables
"""
yrm = pulp.LpVariable.dict('y', ["{}_{}".format(r_,m_) for r_ in r for m_ in m], cat='Binary')
zodij = pulp.LpVariable.dict('z', ["{}_{}_{}_{}".format(o,d,i,j) for o in origins for d in destins for i in stops for j in stops], cat="Binary")
xj = pulp.LpVariable.dict('x', [j for j in stops], cat="Binary")


def problem(alfa, path):
    """Objective (bi)"""
    prob = pulp.LpProblem('1-MRMCSP', pulp.LpMaximize)
    Z1 = pulp.lpSum([m[m_]['weight']*yrm[r_+"_"+m_] for r_ in r for m_ in m])
    Z2 = pulp.lpSum([zodij["{}_{}_{}_{}".format(o,d,i,j)]*dij["{}_{}".format(i,j)] for o in origins for d in destins for i in stops for j in stops])
    # alfa = 0.001
    prob += alfa*Z1 - (1-alfa)*Z2

    """Constraints"""
    for r_ in r:
        for m_ in m:
            prob += pulp.lpSum([xj[j] for j in Nm[m_]]) >= yrm[r_+'_'+m_], "c2_{}-{}".format(r_,m_) # (2)
    for o in origins:
        for d in destins:
            prob += pulp.lpSum([zodij["{}_{}_{}_{}".format(o,d,o,j)] for j in stops]) == 1, "c3_{}-{}".format(o,d) # (3)
            prob += pulp.lpSum([zodij["{}_{}_{}_{}".format(o,d,j,o)] for j in stops]) == 0, "c3a_{}-{}".format(o,d) # (3a)
            prob += pulp.lpSum([zodij["{}_{}_{}_{}".format(o,d,i,d)] for i in stops]) == 1, "c4_{}-{}".format(o,d) # (4)
            prob += pulp.lpSum([zodij["{}_{}_{}_{}".format(o,d,d,i)] for i in stops]) == 0, "c4a_{}-{}".format(o,d) # (4a)
            prob += pulp.lpSum([zodij["{}_{}_{}_{}".format(o,d,i,i)] for i in stops]) == 0, "cii_{}-{}".format(o,d) # (4a)

            prob += pulp.lpSum([zodij["{}_{}_{}".format(o,d,s_)] for s_ in s_notallowed]) == 0, "ciii_{}-{}".format(o,d) # (4a)

            for j in stops:
                prob += pulp.lpSum([zodij["{}_{}_{}_{}".format(o,d,i,j)] for i in stops]) == xj[j], "c6_{}-{}-{}-{}".format(o,d,i,j) # (6)
                if j[0]!='o' and j[0]!='d':
                    prob += pulp.lpSum([zodij["{}_{}_{}_{}".format(o,d,i,j)] for i in stops]) - pulp.lpSum([zodij["{}_{}_{}_{}".format(o,d,j,k)] for k in stops]) == 0, "c5_{}-{}-{}-{}".format(o,d,i,j)
    print('Solving MRMCSP for alfa = {} \n...'.format(alfa))
    prob.solve(pulp.GUROBI(msg=0))
    print("Objective: ", pulp.value(prob.objective),'\n')
    # print(pulp.LpStatus[prob.status],'\n')
    # print([(z,zodij[z].varValue) for z in zodij if zodij[z].varValue==1])
    # print([(j,xj[j].varValue) for j in xj if xj[j].varValue==1])
    pd.Series([(z,zodij[z].varValue) for z in zodij if zodij[z].varValue==1]).to_csv(path)

problem(0.0, 'data2/3_0.txt')
problem(0.01, 'data2/3_0,01.txt')
problem(0.50, 'data2/3_0,50.txt')
problem(0.99, 'data2/3_0,99.txt')
problem(1, 'data2/3_1.txt')
