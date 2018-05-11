"""
Implementation of "Optimizing public transit quality and system access:
the multiple-route, maximal covering/shortest-path problem"
by Changshan Wu and Alan T Murray (2005) DOI:10.1068/b31104

(under developing)
Author: Adelson Araujo Jr
"""

import numpy as np
import pulp
from scipy.spatial import distance

"""
stops is a dictionary with bus stop name (or id) as key
and their position (latitude and longitude, for instance) as values
"""
nstops = 10
stops = {'s{}'.format(i): np.random.rand(1,2) for i in range(nstops) }
stops

"""
streets is a list with stop i and stop j
Example: streets = ['s0_s1', 's1_s2', ...]
"""
streets = []
# artificial streets (forming routes)
#route 1
streets.append('s0_s1')
streets.append('s1_s5')
streets.append('s5_s9')
#route 2
streets.append('s0_s3')
streets.append('s3_s6')
streets.append('s6_s9')
# random streets (by closer points on manhattan distance)
for i in stops.keys():
    for j in stops.keys():
        d =  distance.cityblock(stops[i],stops[j])
        s = "{}_{}".format(i,j)
        if i!=j and "{}_{}".format(j,i) not in streets and s not in streets:
            if d<0.3: streets.append(s)
# adding origins and destionations (just one yet)
origins, destins = {}, {}
origins['o0'] = np.random.rand(1,2)
destins['d0'] = np.random.rand(1,2)
streets.append('o0_s0')
streets.append('s9_d0')
streets

"""
This is a calculation of routes between origins and destinations
it append to a dictionary (keys are a origin-destination pair id)
Example:
    example = ['o0_s0_s1_s2_s9_d0', 'o0_s2_s3_s8_d0'] is a set of routes between o0 and d0
    routes = {'0':example, ...}
"""
n_o = 1
n_d = 1
n_OD = 1
routes = {}
def route(o,d,tree_top,path):
    global routes
    path+=tree_top #append to the path
    son = []
    if 'd{}'.format(d) in tree_top: # a path gets from origin to a destination
        routes["r-{}-{}".format(o,d)].append(path) # it becomes a route
        return
    else: # keep drilling
        for i in streets:
            if tree_top==i.split('_')[0]:
                son.append(i.split('_')[1])
        if len(son)==0:
            return path
        for s in son:
            route(o,d, s, path+'_') # recursive call
for o in range(n_o):
    for d in range(n_d):
        routes["r-{}-{}".format(o,d)] = []
        route(o,d,'o{}'.format(o,d),'')
routes

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
                for r in routes[od]: # if s is inside a route
                    if s in r:
                        flag = True # this flags is to not recalculate d if s is in another route
                        d = 0.8*d
                        break
                if flag:
                    break
            dij[s] = d
        else:
            dij[s] = np.inf
dij

"""
m is a dictionary with ridership service areas weight and position as values

Example:
m = {'m0':{weight:3, 'position':[3,2]}, ...}
"""
nm = 15
m = {"m{}".format(i):{'weight':np.random.rand(),'position':np.random.rand(1,2)} for i in range(nm)}
m

"""
Nm is a dictionary with a list of bus stops j that are closer to m as
values and key as the ridership service area id

Example:
Nm = {m0: ['s2','s7', 's8'], m1: ['s3','s7'], ...}
"""
# Nm = {j | Dmj<S}
S = 0.5
Nm = {M:[j for j in stops if distance.cityblock(m[M]['position'],stops[j])<S] for M in m}
Nm


# yrm ?
# yrm = pulp.LpVariable()
arcIJ_includedinODpath = ["{}_{}_{}_{}".format(o,d,i,j) for o in origins for d in destins for i in stops for j in stops]
zodij = pulp.LpVariable('z', arcIJ_includedinODpath, cat="Binary")
stopj_selected = [j for j in stops]
xj = pulp.LpVariable('x', stopj_selected, cat="Binary")


# objective 1:
# sum_(o) sum_(d) sum_(i) sum_(j) of t_(ij)*z_(odij)

# objective 2:
# sum_(m) sum(r) of a_(m)*y_(rm)

# constraints ...
