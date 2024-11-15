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
    file_path = './020_DATA/pf-mp.xlsx'  
    index_col = 'PF' 
    col1 = 'MP1'          
    col2 = 'MP2'         

    # --- Load the CSV file with error handling ---
    df = pd.read_excel(file_path)

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
    qta_aperta_col = 'Qta Aperta'

    # --- Load the Excel file ---
    df_budget = pd.read_excel(export_path)

    # Convert the "Data Fine" column to datetime objects
    df_budget['Data fine'] = pd.to_datetime(df_budget['Data fine'], format='%m/%d/%Y')

    # Extract the months
    months = df_budget['Data fine'].dt.month

    # Count the unique months
    # num_unique_months = months.nunique()
    num_unique_months = 3

    # --- Convert Timestamp and time objects to strings ---
    for col in df_budget.columns:
        if pd.api.types.is_datetime64_any_dtype(df_budget[col]) or isinstance(df_budget[col].iloc[0], datetime.time):  # Use datetime.time
            df_budget[col] = df_budget[col].astype(str)


    # --- Convert DataFrame to a list of dictionaries ---
    df_budget_list = df_budget.to_dict('records')  

    # --- Write the list of dictionaries to the JSON file ---
    with open('df_budget.json', 'w') as df_budget_file:
        json.dump(df_budget_list, df_budget_file, indent=4)


    # --- Load the CSV file with explicit header ---
    df_lc = pd.read_csv('./020_DATA/MP_INDEX.csv', header=0, index_col='MP')

    lc_data = {index: {
                'L1': row['L1'].item(), 
                'L2': row['L2'].item(), 
                'H': row['H'].item(), 
                'AREA': row['AREA'].item(), 
                'VOL': row['VOL'].item(), 
                '#PER_LC': row['#PER_LC'].item(), 
                'TC': row['TC'].item(), 
                'CAST': row['CAST'].item(), 
                'INT': row['INT'].item()
            } for index, row in df_lc.iterrows()}

    with open('lc_data.json', 'w') as lc_data_file:
        json.dump(lc_data, lc_data_file, indent=4)

    # Rename the column
    df_budget = df_budget.rename(columns={"Qtà Aperta": "Qta Aperta"})

    # Filter the DataFrame to include only rows where the `Ctr.` column is equal to 'ZPEM'
    df_budget_F = df_budget[df_budget['Ctr.'] == 'ZPEM']

    # Select the desired columns from df_budget_F
    df_budget_F = df_budget_F[["Ctr.", "Materiale", "Qta Aperta"]]

    # Group the filtered DataFrame by `Materiale` and `Ctr.`,
    # and calculate the sum of `Qta Aperta` for each group
    grouped_df = (
        df_budget_F.groupby(["Materiale", "Ctr."])["Qta Aperta"].sum().reset_index()
    )

    grouped_df.to_csv("./PF_budget.csv", index=True, header=True)

    # Convert the aggregated DataFrame to a dictionary with `Materiale` as the index
    PF_budget = grouped_df.set_index('Materiale').to_dict(orient='index')

    for index in PF_budget:
        PF_budget[index]['Qta Aperta'] = math.floor(PF_budget[index]['Qta Aperta']/num_unique_months)

    # Export this dictionary to a JSON file named "PF_budget.json"
    with open('PF_budget.json', 'w') as f:
        json.dump(PF_budget, f, indent=4)

    MP_buff = {}
    for index in PF_budget:
        MP_buff[index] = {
            "MP1" : PF_MP[index][0],
            "TOT_MP1" : PF_budget[index]["Qta Aperta"],
            "MP2" : PF_MP[index][1],
            "TOT_MP2" : PF_budget[index]["Qta Aperta"]
            }
        if MP_buff[index]["MP2"] == 0:
            MP_buff[index]["TOT_MP2"] = 0
    
    # --- Calculate MP ---
    MP = {}
    for index in MP_buff:
        mp1 = MP_buff[index]['MP1']
        mp2 = MP_buff[index]['MP2']

        if mp1 not in MP:
            MP[mp1] = {}  # Create the inner dictionary first
            MP[mp1]['MP'] = mp1
            MP[mp1]['TOT_MP'] = MP_buff[index]['TOT_MP1']
        else:
            MP[mp1]['TOT_MP'] += MP_buff[index]['TOT_MP1']

        if mp2 != 0 and mp2 not in MP:
            MP[mp2] = {}  # Create the inner dictionary first
            MP[mp2]['MP'] = mp2
            MP[mp2]['TOT_MP'] = MP_buff[index]['TOT_MP2']
        elif mp2 != 0:
            MP[mp2]['TOT_MP'] += MP_buff[index]['TOT_MP2']

    for index in MP:
        MP[index]['L1'] = lc_data[index]['L1']
        MP[index]['L2'] = lc_data[index]['L2']
        MP[index]['H'] = lc_data[index]['H']
        MP[index]['AREA'] = lc_data[index]['AREA']
        MP[index]['VOL'] = lc_data[index]['VOL']
        MP[index]['#PER_LC'] = lc_data[index]['#PER_LC']
        MP[index]['TC'] = lc_data[index]['TC']
        MP[index]['CAST'] = lc_data[index]['CAST']
        MP[index]['INT'] = lc_data[index]['INT']
    
        # --- Calculate #LC and TOT_VOL ---
        if lc_data[index]['#PER_LC'] is not None:
            num_lc = math.ceil(MP[index]['TOT_MP'] / MP[index]['#PER_LC'])
            tot_vol = lc_data[index]['VOL'] * num_lc
        else:
            num_lc = None
            tot_vol = None

        lc_cons = 1/((MP[index]['#PER_LC']) / (MP[index]['TC'] * 60 * 8 * 1.865))
        vol_dep = tot_vol / lc_cons

        # --- Add #LC and TOT_VOL to the dictionary ---
        MP[index]['#LC'] = num_lc
        MP[index]['TOT_VOL'] = tot_vol
        MP[index]['LC_CONSUMPTION'] = lc_cons
        MP[index]['VOL_DEPLETING'] = vol_dep

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

    PARAMS = {}
    for index in MP:
        PARAMS[index] = {
            'Q': MP[index]['TOT_MP'],
            'W': MP[index]['VOL_DEPLETING'],
            'VOL': MP[index]['VOL'],
            'LC': MP[index]['#LC'],
            'cast': MP[index]['CAST'],
            'internal': MP[index]['INT']
        }

    # --- Write the dictionary on the JSON file ---
    with open('PARAMS.json', 'w') as mp_buff_file:
        json.dump(PARAMS, mp_buff_file, indent=4)

        # Export this dictionary to a JSON file named "mp.json"
    with open('mp.json', 'w') as f:
        json.dump(MP, f, indent=4)

    for index in MP:
        del MP[index]['MP']

    df_mp = pd.DataFrame(MP) 

    df_mp.to_csv("mp.csv", index=False)

    # --- Hardcoded input data ---
    Z = [(350, 65), (570, 65), (420, 65), (60, 65), (490, 340), (630, 225), (60, 165), (220, 165), (127, 165), (375, 340), (563, 390)]
    Z_ = [(350, 65), (570, 65), (300, 65), (60, 65), (490, 340), (630, 225), (60, 165), (220, 165), (127, 165), (375, 340), (563, 390)]
    wp_list = [(424, 65), (630, 100), (630, 340), (563, 340), (270, 340), (270, 165), (460, 165), (127, 65)]

    return (
        coords, x_coord, y_coord, x_node, y_node, Q, W, VOL, LC, cast, internal, Z, Z_, wp_list, MP, PF_MP
        )