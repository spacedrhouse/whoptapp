import math
import numpy as np
import pandas as pd
import json

def data_manipulation(
    coords, 
    x_coord, y_coord,
    x_node, y_node, 
    Q, W, VOL, LC, cast, internal,
    Z, Z_, wp_list, 
    MP, PF_MP
    ):

    def euclid_dist(x1, y1, x2, y2):
        return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

    def calculate_distance(node1_id, node2_id):
        x1, y1 = nodes[node1_id]
        x2, y2 = nodes[node2_id]
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

    # --- Node and distances ---
    nodes = {row['node_id']: (row['x_node'], row['y_node']) for _, row in coords.iterrows()}
    A = [
        (0, 13, 1), (0, 13, 21, 2), (0, 13, 1), (0, 13, 1, 3, 20, 4), (0, 13, 21, 2, 14, 6, 15, 16, 5),
        (0, 13, 21, 2, 14, 6), (0, 13, 1, 3, 20, 9, 7), (0, 13, 1, 3, 20, 9, 8), (0, 13, 1, 3, 20, 9),
        (0, 13, 21, 19, 18, 17, 10), (0, 13, 21, 2, 14, 6, 15, 16, 11)
    ]

    # Calculate the total distance for each sub-array in A
    dis_buffer1 = []
    for sub_array in A:
        total_distance = 0
        for i in range(len(sub_array) - 1):
            total_distance += calculate_distance(sub_array[i], sub_array[i + 1])
        dis_buffer1.append(total_distance)

    # --- Input data from context ---

    MP_list = list(MP.values()) 
    Class = 3
    P = len(MP)
    G = len(cast)
    C = 1.2*0.8*9  # Slot max capacity
    Zone_1 = range(1, 13)  # Esterno impianto 1
    Zone_2 = range(13, 50)  # Esterno impianto 2
    Zone_3 = range(50, 173)  # Esterno impianto 3
    Zone_4 = range(173, 209)  # Esterno impianto 4
    Zone_5 = range(209, 308)  # Esterno SEP 1
    Zone_6 = range(308, 348)  # Esterno SEP 2
    Zone_7 = range(348, 360)  # Interno SEP 1
    Zone_8 = range(360, 401)  # Interno SEP 2
    Zone_9 = range(401, 680)  # Interno SEP 3
    Zone_10 = range(680, 778)  # Esterno magazzino nuovo 1
    Zone_11 = range(778, 828)  # Esterno magazzino nuovo 2
    Stock_Zones = [Zone_1, Zone_2, Zone_3, Zone_4, Zone_5, Zone_6, Zone_7, Zone_8, Zone_9, Zone_10, Zone_11]
    Cast_Zones = [Zone_1, Zone_2, Zone_3, Zone_4, Zone_7, Zone_8, Zone_9]

    # --- Calculate the number of columns in each zone ---
    num_columns_per_zone = []
    for zone in Stock_Zones:
        unique_x_coords = set(x_coord[i - 1] for i in zone)
        num_columns = len(unique_x_coords)
        num_columns_per_zone.append(num_columns)

    # Calculate the number of columns for zone_6
    for i, zone in enumerate(Stock_Zones):
        if i == 5:  # Check if it's Zone_6 (index 5)
            # Find the unique y-coordinates in the zone
            unique_y_coords = set(y_coord[i - 1] for i in zone)

            # The number of columns is equal to the number of unique y-coordinates
            num_columns = len(unique_y_coords)
    num_columns_per_zone[5]=num_columns


    # Create a dictionary to store column labels and corresponding coordinates
    column_data = {}
    zone_letter = ord('A')  # Start with letter A for zones
    for i, zone in enumerate(Stock_Zones):
        zone_id = chr(zone_letter + i)  # Assign a letter to the zone
        num_columns = num_columns_per_zone[i]  # Get the number of columns for the current zone
        slots_in_column = len(zone) // num_columns
        remaining_slots = len(zone) % num_columns
        current_slot = 0
        for col in range(num_columns):
            column_letter = chr(ord('A') + col % 26)  # Get the column letter, loop through A-Z
            extra_letter = ''
            if col // 26 > 0:  # If we need an extra letter
                extra_letter = chr(ord('A') + (col // 26) - 1)  # Add the extra letter
            column_label = f"{zone_id}{extra_letter}{column_letter}"
            column_coords = set()
            # Correct the loop to iterate over the correct range of slots
            for l in range(zone.start + col * slots_in_column, zone.start + (col + 1) * slots_in_column + (1 if col < remaining_slots else 0)):
                column_coords.add(l)
                current_slot += 1
            column_data[column_label] = column_coords

    dis_buffer2 = []
    for i, (zx, zy) in enumerate(Z):  # Iterate over Z with index i
        for k in Stock_Zones[i]:  # Access the corresponding Stock_Zone using index i
            dist = euclid_dist(zx, zy, x_coord[k-1], y_coord[k-1])  # Calculate Euclidean distance
            if x_coord[k-1] > x_coord[0] and x_coord[k-1] < zx:  # Check x-coordinate condition
                dist *= -1  # Multiply distance by -1
            if x_coord[k-1] < x_coord[0] and x_coord[k-1] > zx:  # Check x-coordinate condition
                dist *= -1  # Multiply distance by -1
            dis_buffer2.append(dist)  # Append the adjusted distance

    dis = []
    counter = 0
    for i in range(11):  # Iterate over zones in Z
        for j in Stock_Zones[i]:  # Iterate over slots in the current zone
            dis.append(dis_buffer1[i] + dis_buffer2[j-1])
    L=len(dis)

    # --- Write the dictionary on the JSON file ---
    with open('mp.json', 'w') as mp_file:
        json.dump(MP, mp_file, indent=4)

    print(len(MP))

    #Apc Matrix
    apc=np.zeros((P,Class),int) 

    for i in range(P):
        if W[i]>=15:
            apc[[i],0] = 1
        elif W[i]>=5 and W[i]<15:
            apc[[i],1] = 1
        else:
            apc[[i],2] = 1

    for index in MP:
        MP[index]['CLASS'] = 0
    for i in range(P):
            if W[i]>=15: 
                MP[index]['CLASS'] = 2 
            elif W[i]>=5 and W[i]<15:
                MP[index]['CLASS']= 1
            else:
                MP[index]['CLASS']= 0

    # Convert ndarray to list
    apc_list = apc.tolist()

    # --- Write the dictionary on the JSON file ---
    with open('apc.json', 'w') as mp_file:
        json.dump(apc_list, mp_file, indent=4)

    restricted = []
    for i in range(P):
        if MP[index]['CLASS'] == 2: 
            restricted.append(i)

    # --- Write the dictionary on the JSON file ---
    with open('mp.json', 'w') as mp_file:
        json.dump(MP, mp_file, indent=4)

    return (
        Class, P, G, C, Stock_Zones, Cast_Zones,
        num_columns_per_zone, column_data, dis, L, A, apc, VOL, LC, cast, internal,
        MP
    )