import os
import time
import math
import itertools

import pandas as pd

from copy import deepcopy
from pyomo.core import *

from optimization_pyomo_model import OptimizationPyomoModel
from optimization_gurobi_model import OptimizationGurobiModel
from optimization_highs_model import OptimizationHighsModel
from _helper_optimization import multi_processing_optimization_country, clone_components_which_use_parallelization

from joblib import Parallel, delayed
from tqdm import tqdm
import multiprocessing

from os import walk
from datetime import datetime


def optimize_single_profile_not_multi_objective(optimization_type, pm_object_copy_pyomo, pm_object_copy_gurobi,
                                                solver, path_results):

    optimization_model_pyomo = OptimizationPyomoModel
    optimization_model_gurobi = OptimizationGurobiModel
    optimization_model_highs = OptimizationHighsModel

    if False:

        now = time.time()
        optimization_problem = optimization_model_pyomo(pm_object_copy_pyomo, solver)
        optimization_problem.prepare(optimization_type=optimization_type)
        optimization_problem.optimize()

        pyomo_time_optimization = time.time() - now
        now = time.time()

        pm_object_copy_pyomo.set_objective_function_value(optimization_problem.objective_function_value)
        pyomo_ofv = optimization_problem.objective_function_value
        pm_object_copy_pyomo.set_instance(optimization_problem.instance)
        pm_object_copy_pyomo.process_results(path_results, optimization_problem.model_type)

        pyomo_time_analysis = time.time() - now

    if True:

        now = time.time()
        optimization_problem = optimization_model_gurobi(pm_object_copy_gurobi, solver)
        optimization_problem.prepare(optimization_type=optimization_type)
        optimization_problem.optimize()

        gurobi_time_optimization = time.time() - now
        now = time.time()

        pm_object_copy_gurobi.set_objective_function_value(optimization_problem.objective_function_value)
        gurobi_ofv = optimization_problem.objective_function_value
        pm_object_copy_gurobi.set_instance(optimization_problem.instance)
        pm_object_copy_gurobi.process_results(optimization_problem.model_type, path_results)

        gurobi_time_analysis = time.time() - now

    if False:

        now = time.time()
        optimization_problem = optimization_model_highs(pm_object_copy_pyomo, solver)
        optimization_problem.prepare(optimization_type=optimization_type)
        optimization_problem.optimize()

        highs_time_optimization = time.time() - now
        now = time.time()

        pm_object_copy_pyomo.set_objective_function_value(optimization_problem.objective_function_value)
        highs_ofv = optimization_problem.objective_function_value
        pm_object_copy_pyomo.set_instance(optimization_problem.instance)
        pm_object_copy_pyomo.process_results(optimization_problem.model_type, path_results)
        highs_time_analysis = time.time() - now

        print('Comparison OFV: highs: ' + str(highs_ofv) + ' | Gurobi: ' + str(gurobi_ofv) + ' | Pyomo: ' + str(pyomo_ofv))
        print('Comparison Time Optimization: highs: ' + str(highs_time_optimization) + ' | Gurobi: ' + str(gurobi_time_optimization) + ' | Pyomo: ' + str(pyomo_time_optimization))
        print('Comparison Time Analysis: highs: ' + str(highs_time_analysis) + ' | Gurobi: ' + str(gurobi_time_analysis) + ' | Pyomo: ' + str(pyomo_time_analysis))


def optimize_single_profile_multi_objective(optimization_type, pm_object_copy_pyomo, pm_object_copy_gurobi,
                                            solver, path_results):
    # the multi objective optimization follows the epsilon constraint method. This means
    # that the payoff table is calculated, deriving the nadir and udir value
    # of the second objective function. Afterwards, the range between these two values is separated into
    # small segments and each segment is included in the multi objective optimization
    # For more details, see
    # Mavrotas (2009): Effective implementation of the ε-constraint method in
    # Multi-Objective Mathematical Programming problems
    # todo: check nadir udir correct



    def run_multi_objective_optimization_in_parallel(input_local):
        # input: 0: eps; 1: optimization_model; 2: pm_object
        multi_objective_optimization_problem = OptimizationGurobiModel(input_local[2], solver)

        # multi_objective_optimization_problem = input_local[1](input_local[2], solver)
        multi_objective_optimization_problem.prepare(optimization_type='multiobjective', eps_value_ecologic=input_local[0])
        multi_objective_optimization_problem.optimize()

        values = [multi_objective_optimization_problem.economic_objective_function_value,
                  multi_objective_optimization_problem.ecologic_objective_function_value]

        pm_object_copy_local = clone_components_which_use_parallelization(input_local[2])

        pm_object_copy_local.set_objective_function_value(multi_objective_optimization_problem.objective_function_value)
        pm_object_copy_local.set_instance(multi_objective_optimization_problem.instance)
        pm_object_copy_local.process_results(multi_objective_optimization_problem.model_type, path_results,
                                             create_results=False)

        for c in pm_object_copy_local.get_all_components():
            values.append(c.get_total_installation_co2_emissions())
            values.append(c.get_total_disposal_co2_emissions())
            values.append(c.get_total_fixed_co2_emissions())
            values.append(c.get_total_variable_co2_emissions())

        for c in pm_object_copy_local.get_all_components():
            values.append(c.get_annualized_investment())
            values.append(c.get_total_fixed_costs())
            values.append(c.get_total_variable_costs())

        values.append(input_local[0])

        return values

    number_intervalls = 100

    # first calculate economical nadir value # todo: here you get minima of economic and ecologic --> save somewhere
    economic_optimization_problem = OptimizationGurobiModel(pm_object_copy_gurobi, solver)
    economic_optimization_problem.prepare(optimization_type='economical')
    economic_optimization_problem.optimize()

    ecologic_optimization_problem = OptimizationGurobiModel(pm_object_copy_gurobi, solver)
    ecologic_optimization_problem.prepare(optimization_type='ecological')
    ecologic_optimization_problem.optimize()

    # economic_minimum = economic_optimization_problem.objective_function_value
    economic_minimum = math.ceil(economic_optimization_problem.objective_function_value * 100) / 100
    ecologic_minimum = ecologic_optimization_problem.objective_function_value

    ecologic_optimization_problem = OptimizationGurobiModel(pm_object_copy_gurobi, solver)
    ecologic_optimization_problem.prepare(optimization_type='ecological', eps_value_economic=economic_minimum)
    ecologic_optimization_problem.optimize()
    ecologic_supremum = ecologic_optimization_problem.objective_function_value

    # create intervalls of the ecological value and repeat multi objective optimization
    objective_function_value_combinations = {}
    intervall_objective_function = (ecologic_supremum - ecologic_minimum) / number_intervalls

    inputs = []
    for i in range(0, number_intervalls):
        eps = ecologic_minimum + i * intervall_objective_function
        inputs.append((eps, OptimizationGurobiModel, clone_components_which_use_parallelization(pm_object_copy_gurobi)))

    inputs = tqdm(inputs)
    results = Parallel(n_jobs=25)(delayed(run_multi_objective_optimization_in_parallel)(i) for i in inputs)

    columns = ['Economic', 'Ecologic']
    for c in pm_object_copy_gurobi.get_all_components():
        columns.append(c.get_name() + '_Installation_Emissions')
        columns.append(c.get_name() + '_Disposal_Emissions')
        columns.append(c.get_name() + '_Fixed_Emissions')
        columns.append(c.get_name() + '_Variable_Emissions')

    for c in pm_object_copy_gurobi.get_all_components():
        columns.append(c.get_name() + '_Annual_Costs')
        columns.append(c.get_name() + '_Fixed_Costs')
        columns.append(c.get_name() + '_Variable_Costs')

    distances = {}

    for i, r in enumerate(results):
        objective_function_value_combinations[i] = r[:-1]

        distances[i] = math.sqrt(r[0] ** 2 + r[1] ** 2)

    print(distances)

    distance = math.inf
    chosen_i = None
    for k in distances.keys():
        if distances[k] < distance:
            distance = distances[k]
            chosen_i = k

    print(distance)
    print(chosen_i)

    # optimize that value where minimal distance
    multi_objective_optimization_problem = OptimizationGurobiModel(pm_object_copy_gurobi, solver)
    multi_objective_optimization_problem.prepare(optimization_type='multiobjective',
                                                 eps_value_ecologic=results[chosen_i][-1])
    multi_objective_optimization_problem.optimize()

    pm_object_copy_local = clone_components_which_use_parallelization(pm_object_copy_gurobi)
    pm_object_copy_local.set_objective_function_value(multi_objective_optimization_problem.objective_function_value)
    pm_object_copy_local.set_instance(multi_objective_optimization_problem.instance)
    pm_object_copy_local.process_results(multi_objective_optimization_problem.model_type, path_results)

    result_df = pd.DataFrame(objective_function_value_combinations).transpose()
    result_df.columns = columns

    dt_string = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_df.to_excel(path_results + dt_string + '_'
                       + pm_object_copy_gurobi.get_project_name() + '_multi_objective.xlsx')


def optimize_multi_profiles_no_multi_optimization(optimization_type, pm_object_copy_pyomo, pm_object_copy_gurobi,
                                                  solver, path_results):

    def multi_processing_optimization(input_data):  # 0: pm_object, 1: path to file
        input_data[0].set_profile_data(path_data_before + '/' + input_data[1])

        optimization_problem = optimization_model_global(input_data[0], solver)
        optimization_problem.prepare(optimization_type=optimization_type)
        optimization_problem.optimize()

        input_data[0].set_objective_function_value(optimization_problem.objective_function_value)

        input_data[0].set_instance(optimization_problem.instance)
        input_data[0].process_results(optimization_problem.model_type, path_results)

        return optimization_problem.objective_function_value

    num_cores = min(75, multiprocessing.cpu_count() - 1)

    optimization_model_global = OptimizationGurobiModel

    path_data_before = pm_object_copy_gurobi.get_profile_data()
    path_to_profiles = pm_object_copy_gurobi.get_path_data() + pm_object_copy_gurobi.get_profile_data()
    _, _, filenames = next(walk(path_to_profiles))

    use_country_data = True
    if use_country_data:
        # path_data = '/run/user/1000/gvfs/smb-share:server=iipsrv-file3.iip.kit.edu,share=ssbackup/weatherOut/weatherOut_Uwe/'
        path_data = '/run/user/1000/gvfs/smb-share:server=iipsrv-ss1.iip.kit.edu,share=daten$/weatherOut/weatherOut_Uwe/'

        cluster_length = 168
        scenario = 2030

        country_specific_wacc = pd.read_excel('/home/localadmin/Dokumente/country_specific_wacc.xlsx', index_col=0)

        countries = ['Algeria', 'Armenia', 'Azerbaijan', 'Angola', 'Argentina', 'Australia',
                     'Austria',
                     'Belgium', 'Bhutan', 'Bolivia', 'Botswana', 'Brazil', 'Burundi', 'Bangladesh', 'Belarus', 'Belize',
                     'Benin', 'Bosnia and Herzegovina', 'Bulgaria', 'Burkina Faso', 'Brunei',
                     'Canada', 'Central African Republic', 'Chile', 'Colombia', 'Cambodia', 'Cameroon', 'Croatia',
                     'Czech Republic', 'Cyprus', 'Chad', 'Comoros', 'Costa Rica', 'Cuba',
                     'Denmark', 'Democratic Republic of the Congo', 'Djibouti', 'Dominican Republic',
                     'Ecuador', 'El Salvador', 'Egypt', 'Eswatini', 'Ethiopia', 'Equatorial Guinea', 'Eritrea',
                     'Estonia',
                     'Finland', 'France',
                     'Germany', 'Ghana', 'Guyana', 'Gabon', 'Gambia', 'Georgia', 'Greece', 'Guatemala', 'Guinea',
                     'Guinea-Bissau',
                     'Haiti', 'Honduras', 'Hungary',
                     'Iran', 'Iraq', 'Ireland', 'Israel', 'Italy', 'Iceland', 'India', 'Indonesia', 'Ivory Coast',
                     'Jordan', 'Jamaica', 'Japan',
                     'Kazakhstan', 'Kenya', 'Kuwait', 'Kyrgyzstan',
                     'Lebanon', 'Latvia', 'Lithuania', 'Lesotho', 'Libya', 'Laos', 'Luxembourg', 'Liberia',
                     'Madagascar', 'Malawi', 'Mali', 'Morocco', 'Mozambique', 'Malaysia', 'Mauritania',
                     'Mexico', 'Moldova', 'Mongolia', 'Montenegro', 'Myanmar',
                     'Netherlands', 'North Macedonia', 'Namibia', 'New Zealand', 'Nicaragua', 'Niger', 'Nigeria',
                     'Norway',
                     'Nepal', 'North Korea',
                     'Oman',
                     'Pakistan', 'Paraguay', 'Peru', 'Poland', 'Portugal', 'Panama', 'Papua New Guinea', 'Puerto Rico',
                     "People's Republic of China", 'Philippines',
                     'Qatar',
                     'Rwanda', 'Romania', 'Russia', 'Republic of the Congo',
                     'Saudi Arabia', 'Somalia', 'South Africa', 'South Sudan', 'Serbia', 'Slovakia', 'Slovenia',
                     'Spain', 'Suriname', 'Sweden', 'Switzerland', 'Syria', 'Senegal', 'Sierra Leone', 'South Korea',
                     'Sri Lanka', 'Sudan',
                     'Tajikistan', 'Tanzania', 'Tunisia', 'Turkmenistan', 'Turkey', 'Thailand', 'Togo',
                     'Uganda', 'United Arab Emirates', 'United Kingdom', 'Uruguay', 'Uzbekistan', 'Ukraine',
                     'United States of America',
                     'Venezuela', 'Vietnam',
                     'Western Sahara',
                     'Yemen',
                     'Zambia', 'Zimbabwe']

        for c in countries:
            if c not in country_specific_wacc.index:
                print(c)

        for c in sorted(countries):

            print(c)

            print('old: ' + str(pm_object_copy_gurobi.get_wacc()))
            print('new: ' + str(country_specific_wacc.at[c, 'WACC']))

            pm_object_copy_gurobi.set_wacc(country_specific_wacc.at[c, 'WACC'])

            path_data = path_data + c + '/Clustered_Profiles/' + str(scenario) + '/' + str(cluster_length) + '/'
            path_data_before = ''
            pm_object_copy_gurobi.set_path_data(path_data)
            pm_object_copy_gurobi.set_profile_data('')

            try:
                filenames = os.listdir(path_data)
            except KeyError:
                continue

            new_input = []
            for f in filenames:
                new_input.append((deepcopy(pm_object_copy_gurobi), f))

            task_args = zip(tqdm(new_input),
                            itertools.repeat(path_data_before),
                            itertools.repeat(optimization_model_global),
                            itertools.repeat(solver),
                            itertools.repeat(optimization_type))

            # Create a pool of worker processes
            pool = multiprocessing.Pool(processes=num_cores, maxtasksperchild=1)

            # Start processing tasks and ensure parallelism
            results_gurobi = list(pool.imap(multi_processing_optimization_country, task_args))

            # Close and join the worker pool
            pool.close()
            pool.join()

            result_df = pd.DataFrame(results_gurobi, index=filenames, columns=['economic', 'ecologic'])

            result_df.to_excel(path_results + c + '_' + pm_object_copy_gurobi.get_project_name() + '.xlsx')

            path_data = '/run/user/1000/gvfs/smb-share:server=iipsrv-ss1.iip.kit.edu,share=daten$/weatherOut/weatherOut_Uwe/'

    else:
        new_input = []
        for f in filenames:
            new_input.append((deepcopy(pm_object_copy_gurobi), f))

        inputs = tqdm(new_input)
        results_gurobi = Parallel(n_jobs=num_cores)(delayed(multi_processing_optimization)(i) for i in inputs)

        result_df = pd.DataFrame(results_gurobi, index=filenames)

        dt_string = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_df.to_excel(path_results + dt_string + '_' + pm_object_copy_gurobi.get_project_name() + '.xlsx')

    pm_object_copy_gurobi.set_profile_data(path_data_before)


def multi_profiles_multi_objective(pm_object_copy_gurobi, solver, path_results):
    def run_multi_objective_optimization_in_parallel(input_local):
        # input: 0: eps; 1: optimization_model; 2: pm_object
        multi_objective_optimization_problem = OptimizationGurobiModel(input_local[2], solver)

        # multi_objective_optimization_problem = input_local[1](input_local[2], solver)
        multi_objective_optimization_problem.prepare(optimization_type='multiobjective',
                                                     eps_value_ecologic=input_local[0])
        multi_objective_optimization_problem.optimize()

        values = [multi_objective_optimization_problem.economic_objective_function_value,
                  multi_objective_optimization_problem.ecologic_objective_function_value]

        pm_object_copy_local = clone_components_which_use_parallelization(input_local[2])

        pm_object_copy_local.set_objective_function_value(multi_objective_optimization_problem.objective_function_value)
        pm_object_copy_local.set_instance(multi_objective_optimization_problem.instance)
        pm_object_copy_local.process_results(multi_objective_optimization_problem.model_type, path_results,
                                             create_results=False)

        for c in pm_object_copy_local.get_final_components_objects():
            values.append(c.get_fixed_capacity())

            values.append(c.get_total_installation_co2_emissions())
            values.append(c.get_total_disposal_co2_emissions())
            values.append(c.get_total_fixed_co2_emissions())
            values.append(c.get_total_variable_co2_emissions())

            values.append(c.get_annualized_investment())
            values.append(c.get_total_fixed_costs())
            values.append(c.get_total_variable_costs())

        for c in pm_object_copy_local.get_final_commodities_objects():
            values.append(c.get_total_co2_emissions_available())
            values.append(c.get_total_co2_emissions_emitted())
            values.append(c.get_total_co2_emissions_purchase())
            values.append(c.get_total_co2_emissions_sale())

        values.append(input_local[0])

        return values

    num_cores = min(25, multiprocessing.cpu_count() - 1)
    number_intervals = 100

    path_data_before = pm_object_copy_gurobi.get_profile_data()
    path_to_profiles = pm_object_copy_gurobi.get_path_data() + pm_object_copy_gurobi.get_profile_data()
    _, _, filenames = next(walk(path_to_profiles))

    # create new results folder for multi objective results
    dt_string = datetime.now().strftime("%Y%m%d_%H%M%S")
    path_mo_result = path_results + dt_string + '_' + pm_object_copy_gurobi.get_project_name() + '/'
    os.mkdir(path_mo_result)

    for f in filenames:

        print(f)

        pm_object_copy_gurobi.set_profile_data(path_data_before + '/' + f)

        economic_optimization_problem = OptimizationGurobiModel(pm_object_copy_gurobi, solver)
        economic_optimization_problem.prepare(optimization_type='economical')
        economic_optimization_problem.optimize()

        ecologic_optimization_problem = OptimizationGurobiModel(pm_object_copy_gurobi, solver)
        ecologic_optimization_problem.prepare(optimization_type='ecological')
        ecologic_optimization_problem.optimize()

        economic_minimum = math.ceil(economic_optimization_problem.economic_objective_function_value * 100) / 100
        # economic_minimum = economic_optimization_problem.economic_objective_function_value
        ecologic_minimum = ecologic_optimization_problem.ecologic_objective_function_value

        ecologic_optimization_problem = OptimizationGurobiModel(pm_object_copy_gurobi, solver)
        ecologic_optimization_problem.prepare(optimization_type='ecological', eps_value_economic=economic_minimum)
        ecologic_optimization_problem.optimize()

        ecologic_nadir = ecologic_optimization_problem.ecologic_objective_function_value

        # create intervalls of the ecological value and repeat multi objective optimization
        objective_function_value_combinations = {}
        interval_objective_function = (ecologic_nadir - ecologic_minimum) / number_intervals

        inputs = []
        for i in range(0, number_intervals):
            eps = min(math.ceil(ecologic_minimum) + i * interval_objective_function, ecologic_nadir)  # todo: ceil über all machen
            inputs.append((eps, OptimizationGurobiModel, pm_object_copy_gurobi))

        inputs = tqdm(inputs)
        results = Parallel(n_jobs=num_cores)(delayed(run_multi_objective_optimization_in_parallel)(i) for i in inputs)

        columns = ['Economic', 'Ecologic']
        for c in pm_object_copy_gurobi.get_final_components_objects():
            columns.append(c.get_name() + '_Capacity')

            columns.append(c.get_name() + '_Installation_Emissions')
            columns.append(c.get_name() + '_Disposal_Emissions')
            columns.append(c.get_name() + '_Fixed_Emissions')
            columns.append(c.get_name() + '_Variable_Emissions')

            columns.append(c.get_name() + '_Annual_Costs')
            columns.append(c.get_name() + '_Fixed_Costs')
            columns.append(c.get_name() + '_Variable_Costs')

        for c in pm_object_copy_gurobi.get_final_commodities_objects():
            columns.append(c.get_name() + '_Available_Emissions')
            columns.append(c.get_name() + '_Emitted_Emissions')
            columns.append(c.get_name() + '_Purchase_Emissions')
            columns.append(c.get_name() + '_Sale_Emissions')

        for i, r in enumerate(results):
            objective_function_value_combinations[i] = r[:-1]

        if True:

            distances = {}

            distances[i] = math.sqrt(r[0] ** 2 + r[1] ** 2)

            print(distances)

            distance = math.inf
            chosen_i = None
            for k in distances.keys():
                if distances[k] < distance:
                    distance = distances[k]
                    chosen_i = k

            print(distance)
            print(chosen_i)

            # optimize that value where minimal distance
            multi_objective_optimization_problem = OptimizationGurobiModel(pm_object_copy_gurobi, solver)
            multi_objective_optimization_problem.prepare(optimization_type='multiobjective',
                                                         eps_value_ecologic=results[chosen_i][-1])
            multi_objective_optimization_problem.optimize()

            pm_object_copy_local = clone_components_which_use_parallelization(pm_object_copy_gurobi)
            pm_object_copy_local.set_objective_function_value(multi_objective_optimization_problem.objective_function_value)
            pm_object_copy_local.set_instance(multi_objective_optimization_problem.instance)
            pm_object_copy_local.process_results(multi_objective_optimization_problem.model_type, path_results)

        result_df = pd.DataFrame(objective_function_value_combinations).transpose()
        result_df.columns = columns

        result_df.to_excel(path_mo_result + f.split('_')[0] + '_'
                           + pm_object_copy_gurobi.get_project_name() + '_multi_objective.xlsx')

    pm_object_copy_gurobi.set_profile_data(path_data_before)


def optimize_no_profile(optimization_type, pm_object_copy_pyomo, pm_object_copy_gurobi,
                        solver, path_results):

    optimization_problem = OptimizationGurobiModel(pm_object_copy_gurobi, solver)
    optimization_problem.prepare(optimization_type=optimization_type)
    optimization_problem.optimize()

    # pm_object_copy_gurobi.set_objective_function_value(optimization_problem.objective_function_value)
    # pm_object_copy_gurobi.set_instance(optimization_problem.instance)
    # pm_object_copy_gurobi.process_results(path_results, optimization_problem.model_type)

    # optimization_problem = OptimizationHighsModel(pm_object_copy_gurobi, solver)
    # optimization_problem.prepare(optimization_type=optimization_type)
    # optimization_problem.optimize()

    pm_object_copy_gurobi.set_objective_function_value(optimization_problem.objective_function_value)
    pm_object_copy_gurobi.set_instance(optimization_problem.instance)
    pm_object_copy_gurobi.process_results(optimization_problem.model_type, path_results)
