import os
import pandas as pd


def compare_results(path_results):

    total_overview = pd.DataFrame()

    for folder_name in os.listdir(path_results):
        sub_folder = path_results + '\\' + folder_name

        scenario_name = ''
        for i in range(2, len(folder_name.split('_'))):
            if i != len(folder_name.split('_')):
                scenario_name += folder_name.split('_')[i] + '_'
            else:
                scenario_name += folder_name.split('_')[i]

        name_list = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R']
        if scenario_name == '':
            scenario_name = name_list[0]
            name_list.pop(0)

        # Get data from case
        case_overview = pd.read_excel(sub_folder + '\\0_overview.xlsx')




