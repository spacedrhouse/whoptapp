import math
import numpy as np
import warnings
import os
import sys
import pandas as pd
import plotly.graph_objects as go
import docplex
from docplex.mp.model import Model

def solve(Class, P, G, C, Stock_Zones, Cast_Zones,
        num_columns_per_zone, column_data, dis, L, A, apc, VOL, LC, cast, internal,
        MP
    ):

    mdl = Model(name='WH_REVAMP')

    # --- Decision Variables ---
    x = mdl.binary_var_matrix(L, P, name='X')
    y = mdl.integer_var_matrix(L, P, name='Y')

    # --- CONSTRAINTS ---
    # 1. At most one product type per location
    for l in range(L):
        mdl.add_constraint(mdl.sum(x[l, p] for p in range(P)) <= 1)

    # 2. Slot capacity
    for p in range(P):
        for l in range(L):
            mdl.add_constraint(
                VOL[p]*y[l,p]<=C*x[l,p]
            )

    # 3. Total LCs allocation
    for p in range(P):
        mdl.add_constraint(
            mdl.sum(y[l,p] for l in range(L)) == LC[p]
        )

    # 4. Cast constraint to allocate only in Zone_10
    for p in range(P):
        if cast[p] == 0:
            for zone in Cast_Zones:
                mdl.add_constraint(
                    mdl.sum(x[l-1, p] for l in zone) == 0
                )

    # 5. Int/Ext constraint
    for p in range(P):
        if internal[p] == 1:
            # Prevent allocation outside Zone_7, Zone_8, and Zone_9
            for zone in Stock_Zones:
                if zone not in (Stock_Zones[6], Stock_Zones[7], Stock_Zones[8]):
                    mdl.add_constraint(
                        mdl.sum(x[l-1, p] for l in zone) == 0  # No need for l-1
                    )
            # Ensure allocation in Zone_7, Zone_8, or Zone_9
            mdl.add_constraint(
                mdl.sum(y[l-1, p] for l in Stock_Zones[6]) + 
                mdl.sum(y[l-1, p] for l in Stock_Zones[7]) + 
                mdl.sum(y[l-1, p] for l in Stock_Zones[8]) == LC[p] 
            )

    # 6. Force slots 11 and 12 to be occupied by A class products
    for l in [10, 11]:  # Adjust for 0-based indexing
        mdl.add_constraint(
            mdl.sum(x[l, p] for p in range(P) if MP['Class'][p] == 'A') == 1
        )


    # --- OBJ FUNCTION ---
    mdl.minimize(
        mdl.sum(dis[l] * x[l, p] * (3 * apc[p, 0] + 2 * apc[p, 1] + 1 * apc[p, 2]) for p in range(P) for l in range(L))
    )

    # --- Solve the model ---
    print(mdl.export_to_string())

    # Set CPLEX parameters for detailed logging
    mdl.parameters.mip.display = 2  # Display every node and integer solution
    mdl.parameters.parallel = -1 # opportunistic
    mdl.parameters.workmem = 16000 # 16 GB 
    # Set CPLEX parameters for increased exploration
    mdl.parameters.mip.strategy.search = 2  # Dynamic search
    mdl.parameters.mip.limits.solutions = 56  # Explore more solutions
    mdl.parameters.mip.strategy.nodeselect = 3  # Alternative best-estimate search
    mdl.parameters.mip.strategy.variableselect = 1  # Strong branching
    mdl.parameters.mip.strategy.backtrack = 0.1  # More exploration
    mdl.parameters.mip.strategy.dive = 1  # Guided diving
    mdl.parameters.randomseed = 42  # Set random seed

    # warmstart=mdl.new_solution()
    # warmstart.add_var_value(x,1)
    # mdl.add_mip_start(warmstart)
    mdl.parameters.timelimit = 1000
    sol=mdl.solve(log_output=True)
    sol.display()

    return (
        mdl, sol, x, y, L, P
    )