import tkinter as tk
from tkinter import filedialog
import pandas as pd
import os
import json
import openpyxl
import math
import numpy as np
import time
import datetime

def input_data():
    root = tk.Tk()
    root.withdraw()
    export_path = filedialog.askopenfilename()
    root.destroy()

    # --- PF_MP Dictionary ---
    file_path = './020_DATA/mp-pf.csv'  
    index_col = 'PF' 
    col1 = 'MP1'          
    col2 = 'MP2'         

    # --- Load the CSV file with error handling ---
    df = pd.read_csv(file_path)

    # --- Set the index and create the dictionary ---
    df.set_index(index_col, inplace=True)

    # --- Fill NaN values with 0 ---
    df.fillna(0, inplace=True)  
    PF_MP = {index: (row[col1], row[col2]) for index, row in df.iterrows()}

    # --- Write the dictionary on the JSON file ---
    with open('pf_mp.json', 'w') as pf_mp_file:
        json.dump(PF_MP, pf_mp_file, indent=4)

    # --- MP Dictionary ---
    index_col = 'Materiale' 
    material_col = 'Materiale'
    ctr_col = 'Ctr.'
    qta_aperta_col = 'Qtà Aperta'

    # --- Load the Excel file ---
    df_mp = pd.read_excel(export_path)

    # --- Convert Timestamp and time objects to strings ---
    for col in df_mp.columns:
        if pd.api.types.is_datetime64_any_dtype(df_mp[col]) or isinstance(df_mp[col].iloc[0], datetime.time):  # Use datetime.time
            df_mp[col] = df_mp[col].astype(str)


    # --- Convert DataFrame to a list of dictionaries ---
    df_mp_list = df_mp.to_dict('records')  

    # --- Write the list of dictionaries to the JSON file ---
    with open('df_mp.json', 'w') as df_mp_file:
        json.dump(df_mp_list, df_mp_file, indent=4)


    # --- Load the CSV file with explicit header ---
    df_lc = pd.read_csv('./020_DATA/MP_INDEX.csv', header=0)

    # --- Set the index to 'MP' ---
    df_lc.set_index('MP', inplace=True)  

    # --- Create the lc_data dictionary ---
    lc_data = {index: (row['L1'].item(), row['L2'].item(), row['H'].item(), row['AREA'].item(), row['VOL'].item(), row['#PER_LC'].item(), row['TC'].item(), row['CAST'].item(), row['INT'].item()) for index, row in df_lc.iterrows()} 

    with open('lc_data.json', 'w') as lc_data_file:
        json.dump(lc_data, lc_data_file, indent=4)

    # --- Create the new dictionary ---
    MP = {}
    for index in PF_MP.keys():
        matching_rows = df_mp[df_mp[material_col] == index]
        qta_aperta_sum = 0
        for _, row in matching_rows.iterrows():
            if row[ctr_col]=='ZPEM':
                qta_aperta_sum += row[qta_aperta_col]

        # --- Calculate TOT_MP ---
        qta_aperta_avg = math.ceil(qta_aperta_sum / 3)
        if PF_MP[index][1] != 0:
            tot_mp = qta_aperta_avg*2
            MP[index] = {
                'MP1': PF_MP[index][0],
                'MP2': PF_MP[index][1],
                'TOT_MP': tot_mp,
                'L1': lc_data[PF_MP[index][0]][0],
                'L2': lc_data[PF_MP[index][0]][1],
                'H': lc_data[PF_MP[index][0]][2],
                'AREA': lc_data[PF_MP[index][0]][3],
                'VOL': lc_data[PF_MP[index][0]][4],
                '#PER_LC': lc_data[PF_MP[index][0]][5],
                'TC': lc_data[PF_MP[index][0]][6],
                'CAST': lc_data[PF_MP[index][0]][7],
                'INT': lc_data[PF_MP[index][0]][8]
            }
        else:
            tot_mp = qta_aperta_avg
            MP[index] = {
                'MP1': PF_MP[index][0],
                'MP2': 0,
                'TOT_MP': tot_mp,
                'L1': lc_data[PF_MP[index][0]][0],
                'L2': lc_data[PF_MP[index][0]][1],
                'H': lc_data[PF_MP[index][0]][2],
                'AREA': lc_data[PF_MP[index][0]][3],
                'VOL': lc_data[PF_MP[index][0]][4],
                '#PER_LC': lc_data[PF_MP[index][0]][5],
                'TC': lc_data[PF_MP[index][0]][6],
                'CAST': lc_data[PF_MP[index][0]][7],
                'INT': lc_data[PF_MP[index][0]][8]
            }

        # --- Calculate #LC and TOT_VOL ---
        if lc_data[PF_MP[index][0]][5] is not None:
            num_lc = math.ceil(tot_mp / lc_data[PF_MP[index][0]][5])
            tot_vol = lc_data[PF_MP[index][0]][4] * num_lc
        else:
            num_lc = None
            tot_vol = None

        lc_cons = 1 / ((MP[index]['#PER_LC']) * (MP[index]['TC'] * 60 * 8 * 1.865))
        vol_dep = tot_vol/lc_cons
        # --- Add #LC and TOT_VOL to the dictionary ---
        MP[index]['#LC'] = num_lc
        MP[index]['TOT_VOL'] = tot_vol
        MP[index]['LC_CONSUMPTION'] = lc_cons
        MP[index]['VOL_DEPLETING'] = vol_dep

    # --- Write the dictionary on the JSON file ---
    with open('mp.json', 'w') as mp_file:
        json.dump(MP, mp_file, indent=4)


    coords = pd.read_csv("./020_DATA/coordinates.csv")
    x_coord = coords['x'].values
    y_coord = coords['y'].values
    x_node = coords['x_node'].values
    y_node = coords['y_node'].values

    # Accessing Q, W, VOL, LC, cast, internal
    Q = [MP[index]['TOT_MP'] for index in MP]  # Access 'TOT_MP' for each index
    W = [MP[index]['VOL_DEPLETING'] for index in MP]  # Access 'VOL_DEPLETING' for each index
    VOL = [MP[index]['VOL'] for index in MP]  # Access 'VOL' for each index
    LC = [MP[index]['#LC'] for index in MP]  # Access '#LC' for each index
    cast = [MP[index]['CAST'] for index in MP]  # Access 'CAST' with a default of None
    internal = [MP[index]['INT'] for index in MP]  # Access 'INT' with a default of None

    # --- Hardcoded input data ---
    Z = [(350, 65), (570, 65), (420, 65), (60, 65), (490, 340), (630, 225), (60, 165), (220, 165), (127, 165), (375, 340), (563, 390)]
    Z_ = [(350, 65), (570, 65), (300, 65), (60, 65), (490, 340), (630, 225), (60, 165), (220, 165), (127, 165), (375, 340), (563, 390)]
    wp_list = [(424, 65), (630, 100), (630, 340), (563, 340), (270, 340), (270, 165), (460, 165), (127, 65)]

    return(
        coords, x_coord, y_coord, x_node, y_node, 
        Q, W, VOL, LC, cast, internal,
        Z, Z_, wp_list, MP
    )