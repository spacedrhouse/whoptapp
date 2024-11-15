import toolbox as tb
import warnings

if __name__ == "__main__":
    warnings.filterwarnings('ignore')
    [coords, x_coord, y_coord, x_node, y_node, Q, W, VOL, LC, cast, internal, Z, Z_, wp_list, MP, PF_MP] = tb.input_data()
    [Class, P, G, C, Stock_Zones, Cast_Zones, num_columns_per_zone, column_data, dis, L, A, apc, VOL, LC, cast, internal, MP] = tb.data_manipulation(coords, x_coord, y_coord, x_node, y_node, Q, W, VOL, LC, cast, internal, Z, Z_, wp_list, MP, PF_MP)
    [mdl, sol, x, y, L, P] = tb.solve(Class, P, G, C, Stock_Zones, Cast_Zones, num_columns_per_zone, column_data, dis, L, A, apc, VOL, LC, cast, internal, MP)
    tb.plotting(mdl, sol, x, y, L, P, MP, Stock_Zones, x_coord, y_coord, num_columns_per_zone, column_data, wp_list, Z_, PF_MP, apc)
 