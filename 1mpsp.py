import pulp
from scipy.spatial import distance

"""Data"""
nodeData = {# NODE        Demand, Latitude, Longitude
         "START":         [0, -3, -2],
         "Youngstown":    [10, -2, -2],
         "Pittsburgh":    [15, -4, 2],
         "Cincinatti":    [14, 0, -2],
         "Kansas City":   [12, -1, 2],
         "Chicago":       [11, 0, 1],
         "Albany":        [7, 2, 1],
         "Houston":       [12, 1, 1],
         "Tempe":         [20, -1, 1],
         "Gary":          [12, -2, 1],
         "END":           [0, 3, 2]}
(demand, lat, lon) = pulp.splitDict(nodeData)
nodes = list(nodeData.keys())

arcData = {}
for i in nodes:
    for j in nodes:
        d = distance.cityblock([lat[i],lon[i]],[lat[j],lon[j]])
        if d < 5 and d > 0:
            arcData['{}_{}'.format(i,j)] = d
arcs = list(arcData.keys())
"""_____"""


"""Decision Variables"""
xij = pulp.LpVariable.dict('x', arcs, cat='Binary')
yi = pulp.LpVariable.dict('y', nodes, cat='Binary')
dij = arcData
aj = demand
"""__________________"""


"""Objective (mono)"""
prob = pulp.LpProblem('1-MPSP', pulp.LpMaximize)

alfa = 1
prob += pulp.lpSum([alfa*aj[a.split('_')[1]]*xij[a] - (1-alfa)*dij[a]*xij[a] for a in arcs]), 'aZ1 - (1-a)Z2'

"""_______________"""


"""Constraints"""
prob += pulp.lpSum([xij[a] for a in arcs if a.split('_')[0]=='START']) == 1, "constraint_one_visit_for_start"
prob += pulp.lpSum([xij[a] for a in arcs if a.split('_')[1]=='START']) == 0, "constraint_no_visit_for_start"
prob += pulp.lpSum([xij[a] for a in arcs if a.split('_')[1]=='END']) == 1, "constraint_one_visit_for_end"
prob += pulp.lpSum([xij[a] for a in arcs if a.split('_')[0]=='END']) == 0, "constraint_no_start_for_end"

for j in nodes:# j = 'Gary'
    if j!='START' and j!='END':
        nj = [a for a in arcs if a.split('_')[1]==j]
        a = pulp.lpSum([xij['{}_{}'.format(i.split('_')[0],j)] for i in nj])
        b = pulp.lpSum([xij['{}_{}'.format(j,i.split('_')[0])] for i in nj])
        prob +=  a-b == 0, "constraint_enter_and_leave_for_{}".format(j)
    
for j in nodes:
    if j!='START':
        nj = [a for a in arcs if a.split('_')[1]==j]
        d = pulp.lpSum([xij['{}_{}'.format(i.split('_')[0],j)] for i in nj])
        prob +=  d <= 1, "constraint_one_visit_for_{}".format(j)

for i in nodes:
    if i!='END':
        ni = [a for a in arcs if a.split('_')[0]==i]
        c = pulp.lpSum([xij['{}_{}'.format(i,j.split('_')[1])] for j in ni])
        prob += c-yi[i] >= 0, "constrain_node_covered_for_{}".format(i)
"""___________"""

prob.solve()
print(pulp.LpStatus[prob.status],'\n')

print('Arcs = 1: {')
for a in arcs:
    varvalue = pulp.value(xij[a].varValue)
    if varvalue > 0:
        print('  ',a)
print('}')

