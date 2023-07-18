import pandas as pd

from optimization_classes_and_methods import SuperOptimizationProblem, SubOptimizationProblem, FullDualModel, PrimalDispatch, DualDispatch
from SuperProblemRepresentative import SuperProblemRepresentative
from AlternatingDual import AlternatingDual
from mixed_int_dual_forecast import MixedIntDualForecast
# from TestSubProblem import MixedIntDualRepresentative
from SubProblemDualRepresentative import MixedIntDualRepresentative
from Test_Shortend_ygen import MixedIntDualRepresentative_v1
from Test_Shortend_ygen_2 import MixedIntDualRepresentative_v2
from with_extreme_case import ExtremeCaseBilinear
from max_output_fix_capacities import FixedCapacityMaximization
from with_extreme_case_no_bilinear import ExtremeCaseNoBilinear
# from SubProblemBilinear import MixedIntDualRepresentative
from ResultAnalysis import ResultAnalysis
from _helpers_gui import save_current_parameters_and_options
from joblib import Parallel, delayed
from tqdm import tqdm
import multiprocessing
from copy import deepcopy

import datetime

from os import walk

idx = pd.IndexSlice


def optimize(pm_object, path_data, path_results, solver):
    """ Optimization either with one single case or several cases
    depend on number of generation, purchase and sale data"""

    # read data
    # todo: read solar, wind and weighting data as normal data and implement new data request for all data
    all_data_folder = 'C:/Users/mt5285/Desktop/clustering_test/solar_and_turbine_2030/'

    nominal_data = pd.read_excel(path_data + pm_object.get_profile_data(), index_col=0) # todo:adjust to csv as well
    period_length = pm_object.get_covered_period()
    number_clusters = int(pm_object.get_number_clusters())

    # nominal implements the profiles used in the super problem
    nominal = {0: {}}
    for col in nominal_data.columns:
        if col != 'Weighting':
            nominal[0][col] = {}

    for i in range(number_clusters):
        for col in nominal_data.columns:
            if col != 'Weighting':
                profile = nominal_data.loc[i*period_length:(i+1)*period_length, col]
                profile.index = range(len(profile.index))
                nominal[0][col][i] = profile

    # Set initial worst case cluster
    nominal[0]['Wind'][number_clusters] = nominal[0]['Wind'][0]
    nominal[0]['Solar'][number_clusters] = nominal[0]['Solar'][0]

    weighting = {}
    for i in range(number_clusters):
        weighting[i] = nominal_data.loc[i*period_length, 'Weighting'] / 2 - pm_object.get_time_steps() / 8760

    weighting[number_clusters] = 1

    # all profile data
    all_profiles = pd.read_csv(path_data + 'all_profiles.csv', index_col=0, sep=';')
    number_profiles = int(len(all_profiles.columns) / len(nominal[0].keys()))

    # choose if only some profiles are used
    preselect_profiles = True  # todo: delete. Data set should be correct in the first place
    if preselect_profiles:
        preselection_profiles = [0, 1, 2, 3, 4]
        number_profiles = len(preselection_profiles)

        selected_profiles = []
        for k in [*nominal[0].keys()]:
            selected_profiles += [k + '_' + str(c) for c in preselection_profiles]

        all_profiles = all_profiles[selected_profiles]

    tolerance = 0.01
    UB = float('inf')
    iteration = 0

    kwargs = {}

    capacities = {}
    total_costs_dict = {'UB': {},
                        'LB': {}}

    _, total_demand = pm_object.get_demand_time_series()

    while True:
        if True:
            sup_problem = SuperProblemRepresentative(pm_object, solver, nominal, number_clusters, weighting, iteration)
            sup_problem.optimize()
            capacities_new = sup_problem.optimal_capacities
            capacities[iteration] = capacities_new
            print(capacities_new)
            LB = sup_problem.obj_value

            total_costs_LB = LB / total_demand['Ammonia']
            print('Production costs first stage: ' + str(total_costs_LB))

        else:
            capacities_new = {'Electricity': 6.196400419016634,
                              'H2': 72.31716678211828,
                              'HB Synthesis': 9.993288319972256,
                              'N2 Separation': 0.34113472620374263,
                              'PEM': 29.319579230130245,
                              'Solar': 59.616776674809785,
                              'Wind': 0.20415967566580978}

        sub_problem = ExtremeCaseBilinear(pm_object, solver, capacities_new, nominal, all_profiles, number_clusters,
                                          weighting, number_profiles, **kwargs)
        sub_problem.optimize()

        UB = min(UB, sup_problem.obj_value - sup_problem.auxiliary_variable + sub_problem.obj_value)

        total_costs_UB = UB / total_demand['Ammonia']
        total_costs_dict['UB'][iteration] = total_costs_UB

        total_costs_LB = LB / total_demand['Ammonia']
        total_costs_dict['LB'][iteration] = total_costs_LB

        print('Iteration number: ' + str(iteration))

        print('Total costs UB: ' + str(total_costs_UB))
        print('Total costs LB: ' + str(total_costs_LB))

        difference = (UB - LB) / LB
        print('Difference is: ' + str(difference))

        nominal[iteration]['Wind'][number_clusters] = sub_problem.chosen_profiles['Wind']
        nominal[iteration]['Solar'][number_clusters] = sub_problem.chosen_profiles['Solar']

        if -tolerance <= difference <= tolerance:

            first = True
            for k in [*capacities.keys()]:
                if first:
                    capacity_df = pd.DataFrame.from_dict(capacities[k], orient='index')
                    first = False
                else:
                    capacity_df[k] = pd.DataFrame.from_dict(capacities[k], orient='index')

            capacity_df.to_excel('C:/Users/mt5285/Desktop/clustering_test/results/RO_results/capacity.xlsx')

            profiles_df = pd.DataFrame()
            for i in [*nominal.keys()]:
                for g in [*nominal[i].keys()]:
                    for c in [*nominal[i][g].keys()]:
                        profiles_df[str(i) + '_' + g + '_' + str(c)] = nominal[i][g][c]

            profiles_df.to_excel('C:/Users/mt5285/Desktop/clustering_test/results/RO_results/profiles.xlsx')

            first = True
            total_costs_df = pd.DataFrame()
            for k in [*total_costs_dict.keys()]:
                if first:
                    total_costs_df[k] = pd.DataFrame.from_dict(total_costs_dict[k], orient='index')
                    first = False
                else:
                    total_costs_df[k] = pd.DataFrame.from_dict(total_costs_dict[k], orient='index')
            total_costs_df.to_excel('C:/Users/mt5285/Desktop/clustering_test/results/RO_results/total_costs.xlsx')

            print('optimization successful')

            break

        else:
            iteration += 1
            nominal[iteration] = {}

            nominal[iteration]['Wind'] = nominal[0]['Wind']
            nominal[iteration]['Solar'] = nominal[0]['Solar']

            nominal[iteration]['Wind'][number_clusters] = sub_problem.chosen_profiles['Wind']
            nominal[iteration]['Solar'][number_clusters] = sub_problem.chosen_profiles['Solar']
