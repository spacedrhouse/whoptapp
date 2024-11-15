import math
import numpy as np
import warnings
import os
import sys
import pandas as pd
import plotly.graph_objects as go

def plotting(
        mdl, sol, x, y, L, P, 
        MP, Stock_Zones,
        x_coord, y_coord, num_columns_per_zone,
        column_data, wp_list, Z_, PF_MP,
        apc
    ):

    def sort_by_product_id_and_slot_id(allocation):
        return (allocation[0], allocation[1])

    # --- Save the solution in a list ---
    x_list = []
    for l in range(L):
        tmp = False
        for p in range(P):
            if sol.get_value(x[l, p]) == 1:
                tmp = True
                x_list.append([l + 1, p + 1])
        if not tmp:
            x_list.append([l + 1, -1])

    # --- 1. Write slot IDs to MP ---
    for index in MP:
        MP[index]['Slot_IDs'] = [''] # Initialize an empty column for slot IDs
        for l in range(L):
            for p in range(P):
                if sol.get_value(x[l, p]) == 1:
                    MP[index]['Slot_IDs'] += f"{l+1}, "

    # --- 2. Create an array with product ID, slot ID, and #LC ---
    product_allocation = []
    for l in range(L):
        for p in range(P):
            if sol.get_value(x[l, p]) == 1:
                product_allocation.append([p, l, int(sol.get_value(y[l, p]))])

    # --- Sort and rearrange data for visualization ---
    a_class_products = [allocation for allocation in product_allocation if apc[[allocation[0]],0] == 1]
    a_class_products.sort(key=sort_by_product_id_and_slot_id)
    slot_ids = [allocation[1] for allocation in a_class_products]
    slot_ids.sort()
    slotA_mapping = dict(zip([allocation[1] for allocation in a_class_products], slot_ids))
    for i in range(len(a_class_products)):
        a_class_products[i][1] = slotA_mapping[a_class_products[i][1]]
    a_prod = [[allocation[1], allocation[0], allocation[2], 'A', 'blue'] for allocation in a_class_products]

    b_class_products = [allocation for allocation in product_allocation if apc[[allocation[0]],1] == 1]
    b_class_products.sort(key=sort_by_product_id_and_slot_id)
    slot_ids = [allocation[1] for allocation in b_class_products]
    slot_ids.sort()
    slotB_mapping = dict(zip([allocation[1] for allocation in b_class_products], slot_ids))
    for i in range(len(b_class_products)):
        b_class_products[i][1] = slotB_mapping[b_class_products[i][1]]
    b_prod = [[allocation[1], allocation[0], allocation[2], 'B', 'yellow'] for allocation in b_class_products]

    c_class_products = [allocation for allocation in product_allocation if apc[[allocation[0]],2] == 1]
    c_class_products.sort(key=sort_by_product_id_and_slot_id)
    slot_ids = [allocation[1] for allocation in c_class_products]
    slot_ids.sort()
    slotC_mapping = dict(zip([allocation[1] for allocation in c_class_products], slot_ids))
    for i in range(len(c_class_products)):
        c_class_products[i][1] = slotC_mapping[c_class_products[i][1]]
    c_prod = [[allocation[1], allocation[0], allocation[2], 'C', 'purple'] for allocation in c_class_products]

    # --- Visualization ---
    fig = go.Figure()

    # --- Label all slots before assignment ---
    all_slots = []
    all_x = x_coord
    all_y = y_coord
    all_text = []
    zone_letter = ord('A')

    for i, zone in enumerate(Stock_Zones):
        absolute_slot_number = 1
        zone_id = chr(zone_letter + i)
        num_columns = num_columns_per_zone[i]
        slots_in_column = len(zone) // num_columns
        remaining_slots = len(zone) % num_columns
        current_slot = 0
        column_counter = 0
        for col in range(num_columns):
            column_letter = chr(ord('A') + column_counter % 26)
            extra_letter = ''
            if column_counter // 26 > 0:
                extra_letter = chr(ord('A') + (column_counter // 26) - 1)
            column_label = f"{zone_id}{extra_letter}{column_letter}"
            for slot_number in column_data[column_label]:
                slot_id = list(column_data[column_label]).index(slot_number) + 1
                all_text.append(f"{column_label}{slot_id}")
            column_counter += 1

    # --- Add trace for all slots ---
    fig.add_trace(go.Scatter(
        x=all_x,
        y=all_y,
        mode='markers',
        marker=dict(color='grey', size=10),
        text=all_text,
        hoverinfo='text',
        name='Unallocated'
    ))

    # --- Add DEA_gate node ---
    fig.add_trace(go.Scatter(
        x=[424],
        y=[26.155],
        mode='markers',
        marker=dict(color='red', size=10),
        text='DEA_gate',
        hoverinfo='text',
        name='DEA_gate'
    ))

    # --- Add Waypoints ---
    wpx = [wp[0] for wp in wp_list]
    wpy = [wp[1] for wp in wp_list]
    wp_text = [f"WP: {i+1}" for i in range(len(wp_list))]
    fig.add_trace(go.Scatter(
        x=wpx,
        y=wpy,
        mode='markers',
        marker=dict(color='orange', size=10),
        text=wp_text,
        hoverinfo='text',
        name='Waypoints'
    ))

    # --- Add nodes in Z ---
    zx = [coord[0] for coord in Z_]
    zy = [coord[1] for coord in Z_]
    z_text = [f"Node: {i+1}" for i in range(len(Z_))]
    
    fig.add_trace(go.Scatter(
        x=zx,
        y=zy,
        mode='markers',
        marker=dict(color='green', size=10),
        text=z_text,
        hoverinfo='text',
        name='Pickup_Nodes'
        ))

    occupied_slots = []
    color_list = []
    ax_coord = []
    bx_coord = []
    cx_coord = []
    ay_coord = []
    by_coord = []
    cy_coord = []
    coccupied_text = []
    boccupied_text = []
    aoccupied_text = []
    index_list = list(MP.keys())
    # Add slots for each product class with corresponding colors
    for product_class, color in zip(['A', 'B', 'C'], ['blue', 'yellow', 'purple']):
        if product_class == 'A':  # Use a_class_products for class A
            occupied_slots = a_prod
        elif product_class == 'B':  # Use a_class_products for class A
            occupied_slots = b_prod
        elif product_class == 'C':  # Use a_class_products for class A
            occupied_slots = c_prod
        # Calculate occupied_x and occupied_y for the current product class
        for i in range(len(occupied_slots)):
            color_list.append(occupied_slots[i][4])
            if product_class == 'A':  # Use a_class_products for class A
                ax_coord.append(x_coord[int(occupied_slots[i][0])])
                ay_coord.append(y_coord[int(occupied_slots[i][0])])
            elif product_class == 'B':  # Use a_class_products for class A
                bx_coord.append(x_coord[int(occupied_slots[i][0])])
                by_coord.append(y_coord[int(occupied_slots[i][0])])
            elif product_class == 'C':  # Use a_class_products for class A
                cx_coord.append(x_coord[int(occupied_slots[i][0])])
                cy_coord.append(y_coord[int(occupied_slots[i][0])])

        for column_label, column_coords in column_data.items():  # Iterate using column labels
            for j in range(len(occupied_slots)):
                if occupied_slots[j][0] in column_coords:
                    slot_id = list(column_coords).index(occupied_slots[j][0]) + 1
                    slot_code = f"{column_label}{slot_id}"
                    if product_class == 'A':  # Use a_class_products for class A
                        aoccupied_text.append(f"Slot: {occupied_slots[j][0]}<br>Class: {occupied_slots[j][3]}<br>Product ID: {index_list[occupied_slots[j][1]]}<br>Product Index: {occupied_slots[j][1]+1}<br>Cast: {MP[index_list[occupied_slots[j][1]]]['CAST']}<br>Int/Ext: {MP[index_list[occupied_slots[j][1]]]['INT']}<br>#LC: {occupied_slots[j][2]}<br>Code: {slot_code}")
                    elif product_class == 'B':  # Use a_class_products for class A
                        boccupied_text.append(f"Slot: {occupied_slots[j][0]}<br>Class: {occupied_slots[j][3]}<br>Product ID: {index_list[occupied_slots[j][1]]}<br>Product Index: {occupied_slots[j][1]+1}<br>Cast: {MP[index_list[occupied_slots[j][1]]]['CAST']}<br>Int/Ext: {MP[index_list[occupied_slots[j][1]]]['INT']}<br>#LC: {occupied_slots[j][2]}<br>Code: {slot_code}")
                    elif product_class == 'C':  # Use a_class_products for class A
                        coccupied_text.append(f"Slot: {occupied_slots[j][0]}<br>Class: {occupied_slots[j][3]}<br>Product ID: {index_list[occupied_slots[j][1]]}<br>Product Index: {occupied_slots[j][1]+1}<br>Cast: {MP[index_list[occupied_slots[j][1]]]['CAST']}<br>Int/Ext: {MP[index_list[occupied_slots[j][1]]]['INT']}<br>#LC: {occupied_slots[j][2]}<br>Code: {slot_code}")


    fig.add_trace(
        go.Scatter(
        x=ax_coord,
        y=ay_coord,
        mode='markers',
        marker=dict(color='blue', size=10),  # Use color directly
        text=aoccupied_text,
        hoverinfo='text',
        name=f'A Class'
        )
    )

    fig.add_trace(
        go.Scatter(
        x=bx_coord,
        y=by_coord,
        mode='markers',
        marker=dict(color='yellow', size=10),  # Use color directly
        text=boccupied_text,
        hoverinfo='text',
        name=f'B Class'
        )
    )

    fig.add_trace(
        go.Scatter(
        x=cx_coord,
        y=cy_coord,
        mode='markers',
        marker=dict(color='purple', size=10),  # Use color directly
        text=coccupied_text,
        hoverinfo='text',
        name=f'C Class'
        )
    )
        
    # Update layout
    fig.update_layout(
        title='MCV WH OPTIMIZATION',
        xaxis_title='X',
        yaxis_title='Y',
        hovermode='closest',
        showlegend=True
    )

    fig.show()
