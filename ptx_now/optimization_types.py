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


def optimize_single_profile_not_multi_objective(optimization_type, pm_object_copy,
                                                solver, path_results):

    if solver == 'gurobi':
        optimization_model = OptimizationGurobiModel
    else:
        optimization_model = OptimizationPyomoModel

    optimization_problem = optimization_model(pm_object_copy, solver)
    optimization_problem.prepare(optimization_type=optimization_type)
    optimization_problem.optimize()

    pm_object_copy.set_objective_function_value(optimization_problem.objective_function_value)
    pm_object_copy.set_instance(optimization_problem.instance)
    pm_object_copy.process_results(solver, path_results=path_results)


def optimize_single_profile_multi_objective(pm_object_copy, solver, path_results):
    # the multi objective optimization follows the epsilon constraint method. This means
    # that the payoff table is calculated, deriving the nadir and udir value
    # of the second objective function. Afterwards, the range between these two values is separated into
    # small segments and each segment is included in the multi objective optimization
    # For more details, see
    # Mavrotas (2009): Effective implementation of the ε-constraint method in
    # Multi-Objective Mathematical Programming problems

    def run_multi_objective_optimization_in_parallel(input_local):
        # input: 0: eps; 1: optimization_model; 2: pm_object
        multi_objective_optimization_problem = optimization_model(input_local[2], solver)

        # multi_objective_optimization_problem = input_local[1](input_local[2], solver)
        multi_objective_optimization_problem.prepare(optimization_type='multiobjective',
                                                     eps_value_ecologic=input_local[0])
        multi_objective_optimization_problem.optimize()

        values = [multi_objective_optimization_problem.economic_objective_function_value,
                  multi_objective_optimization_problem.ecologic_objective_function_value]

        pm_object_copy_parallel = clone_components_which_use_parallelization(input_local[2])

        pm_object_copy_parallel.set_objective_function_value(multi_objective_optimization_problem.objective_function_value)
        pm_object_copy_parallel.set_instance(multi_objective_optimization_problem.instance)
        pm_object_copy_parallel.process_results(multi_objective_optimization_problem.model_type, path_results,
                                             create_results=False)

        for c_parallel in pm_object_copy_parallel.get_all_components():
            values.append(c_parallel.get_total_installation_co2_emissions())
            values.append(c_parallel.get_total_disposal_co2_emissions())
            values.append(c_parallel.get_total_fixed_co2_emissions())
            values.append(c_parallel.get_total_variable_co2_emissions())

        for c_parallel in pm_object_copy_parallel.get_all_components():
            values.append(c_parallel.get_annualized_investment())
            values.append(c_parallel.get_total_fixed_costs())
            values.append(c_parallel.get_total_variable_costs())

        values.append(input_local[0])

        return values

    if solver == 'gurobi':
        optimization_model = OptimizationGurobiModel
    else:
        optimization_model = OptimizationPyomoModel

    number_intervalls = 5

    # first calculate economical nadir value
    economic_optimization_problem = optimization_model(pm_object_copy, solver)
    economic_optimization_problem.prepare(optimization_type='economical')
    economic_optimization_problem.optimize()

    ecologic_optimization_problem = optimization_model(pm_object_copy, solver)
    ecologic_optimization_problem.prepare(optimization_type='ecological')
    ecologic_optimization_problem.optimize()

    # economic_minimum = economic_optimization_problem.objective_function_value
    economic_minimum = math.ceil(economic_optimization_problem.objective_function_value * 100) / 100
    ecologic_minimum = ecologic_optimization_problem.objective_function_value

    ecologic_optimization_problem = optimization_model(pm_object_copy, solver)
    ecologic_optimization_problem.prepare(optimization_type='ecological', eps_value_economic=economic_minimum)
    ecologic_optimization_problem.optimize()
    ecologic_supremum = ecologic_optimization_problem.objective_function_value

    # create intervalls of the ecological value and repeat multi objective optimization
    objective_function_value_combinations = {}
    intervall_objective_function = (ecologic_supremum - ecologic_minimum) / number_intervalls

    inputs = []
    for i in range(0, number_intervalls):
        eps = ecologic_minimum + i * intervall_objective_function
        inputs.append((eps, optimization_model, clone_components_which_use_parallelization(pm_object_copy)))

    inputs = tqdm(inputs)
    results = Parallel(n_jobs=25)(delayed(run_multi_objective_optimization_in_parallel)(i) for i in inputs)

    columns = ['Economic', 'Ecologic']
    for c in pm_object_copy.get_all_components():
        columns.append(c.get_name() + '_Installation_Emissions')
        columns.append(c.get_name() + '_Disposal_Emissions')
        columns.append(c.get_name() + '_Fixed_Emissions')
        columns.append(c.get_name() + '_Variable_Emissions')

    for c in pm_object_copy.get_all_components():
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
    multi_objective_optimization_problem = optimization_model(pm_object_copy, solver)
    multi_objective_optimization_problem.prepare(optimization_type='multiobjective',
                                                 eps_value_ecologic=results[chosen_i][-1])
    multi_objective_optimization_problem.optimize()

    pm_object_copy_local = clone_components_which_use_parallelization(pm_object_copy)
    pm_object_copy_local.set_objective_function_value(multi_objective_optimization_problem.objective_function_value)
    pm_object_copy_local.set_instance(multi_objective_optimization_problem.instance)
    pm_object_copy_local.process_results(multi_objective_optimization_problem.model_type, path_results)

    result_df = pd.DataFrame(objective_function_value_combinations).transpose()
    result_df.columns = columns

    dt_string = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_df.to_excel(path_results + dt_string + '_'
                       + pm_object_copy.get_project_name() + '_multi_objective.xlsx')


def optimize_multi_profiles_no_multi_optimization(optimization_type, pm_object_copy, solver, path_results):

    def multi_processing_optimization(input_data):  # 0: pm_object, 1: path to file
        input_data[0].set_profile_data(path_data_before + '/' + input_data[1])

        optimization_problem = optimization_model(input_data[0], solver)
        optimization_problem.prepare(optimization_type=optimization_type)
        optimization_problem.optimize()

        input_data[0].set_objective_function_value(optimization_problem.objective_function_value)

        input_data[0].set_instance(optimization_problem.instance)
        input_data[0].process_results(optimization_problem.model_type, path_results)

        return optimization_problem.objective_function_value

    if solver == 'gurobi':
        optimization_model = OptimizationGurobiModel
    else:
        optimization_model = OptimizationPyomoModel

    num_cores = min(75, multiprocessing.cpu_count() - 1)

    path_data_before = pm_object_copy.get_profile_data()
    path_to_profiles = pm_object_copy.get_path_data() + pm_object_copy.get_profile_data()
    _, _, filenames = next(walk(path_to_profiles))

    new_input = []
    for f in filenames:
        new_input.append((deepcopy(pm_object_copy), f))

    inputs = tqdm(new_input)
    results_gurobi = Parallel(n_jobs=num_cores)(delayed(multi_processing_optimization)(i) for i in inputs)

    result_df = pd.DataFrame(results_gurobi, index=filenames)

    dt_string = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_df.to_excel(path_results + dt_string + '_' + pm_object_copy.get_project_name() + '.xlsx')

    pm_object_copy.set_profile_data(path_data_before)


def multi_profiles_multi_objective(pm_object_copy, solver, path_results):
    def run_multi_objective_optimization_in_parallel(input_local):
        # input: 0: eps; 1: optimization_model; 2: pm_object
        multi_objective_optimization_problem_parallel = optimization_model(input_local[2], solver)

        # multi_objective_optimization_problem = input_local[1](input_local[2], solver)
        multi_objective_optimization_problem_parallel.prepare(optimization_type='multiobjective',
                                                     eps_value_ecologic=input_local[0])
        multi_objective_optimization_problem_parallel.optimize()

        values = [multi_objective_optimization_problem_parallel.economic_objective_function_value,
                  multi_objective_optimization_problem_parallel.ecologic_objective_function_value]

        pm_object_copy_parallel = clone_components_which_use_parallelization(input_local[2])

        pm_object_copy_parallel.set_objective_function_value(multi_objective_optimization_problem_parallel.objective_function_value)
        pm_object_copy_parallel.set_instance(multi_objective_optimization_problem_parallel.instance)
        pm_object_copy_parallel.process_results(multi_objective_optimization_problem_parallel.model_type, path_results,
                                             create_results=False)

        for c_parallel in pm_object_copy_parallel.get_final_components_objects():
            values.append(c_parallel.get_fixed_capacity())

            values.append(c_parallel.get_total_installation_co2_emissions())
            values.append(c_parallel.get_total_disposal_co2_emissions())
            values.append(c_parallel.get_total_fixed_co2_emissions())
            values.append(c_parallel.get_total_variable_co2_emissions())

            values.append(c_parallel.get_annualized_investment())
            values.append(c_parallel.get_total_fixed_costs())
            values.append(c_parallel.get_total_variable_costs())

        for c_parallel in pm_object_copy_parallel.get_final_commodities_objects():
            values.append(c_parallel.get_total_co2_emissions_available())
            values.append(c_parallel.get_total_co2_emissions_emitted())
            values.append(c_parallel.get_total_co2_emissions_purchase())
            values.append(c_parallel.get_total_co2_emissions_sale())

        values.append(input_local[0])

        return values

    if solver == 'gurobi':
        optimization_model = OptimizationGurobiModel
    else:
        optimization_model = OptimizationPyomoModel

    num_cores = min(25, multiprocessing.cpu_count() - 1)
    number_intervals = 100

    path_data_before = pm_object_copy.get_profile_data()
    path_to_profiles = pm_object_copy.get_path_data() + pm_object_copy.get_profile_data()
    _, _, filenames = next(walk(path_to_profiles))

    # create new results folder for multi objective results
    dt_string = datetime.now().strftime("%Y%m%d_%H%M%S")
    path_mo_result = path_results + dt_string + '_' + pm_object_copy.get_project_name() + '/'
    os.mkdir(path_mo_result)

    for f in filenames:

        print(f)

        pm_object_copy.set_profile_data(path_data_before + '/' + f)

        economic_optimization_problem = optimization_model(pm_object_copy, solver)
        economic_optimization_problem.prepare(optimization_type='economical')
        economic_optimization_problem.optimize()

        ecologic_optimization_problem = optimization_model(pm_object_copy, solver)
        ecologic_optimization_problem.prepare(optimization_type='ecological')
        ecologic_optimization_problem.optimize()

        economic_minimum = math.ceil(economic_optimization_problem.economic_objective_function_value * 100) / 100
        # economic_minimum = economic_optimization_problem.economic_objective_function_value
        ecologic_minimum = ecologic_optimization_problem.ecologic_objective_function_value

        ecologic_optimization_problem = optimization_model(pm_object_copy, solver)
        ecologic_optimization_problem.prepare(optimization_type='ecological', eps_value_economic=economic_minimum)
        ecologic_optimization_problem.optimize()

        ecologic_nadir = ecologic_optimization_problem.ecologic_objective_function_value

        # create intervalls of the ecological value and repeat multi objective optimization
        objective_function_value_combinations = {}
        interval_objective_function = (ecologic_nadir - ecologic_minimum) / number_intervals

        inputs = []
        for i in range(0, number_intervals):
            eps = min(math.ceil(ecologic_minimum) + i * interval_objective_function, ecologic_nadir)  # todo: ceil über all machen
            inputs.append((eps, OptimizationGurobiModel, pm_object_copy))

        inputs = tqdm(inputs)
        results = Parallel(n_jobs=num_cores)(delayed(run_multi_objective_optimization_in_parallel)(i) for i in inputs)

        columns = ['Economic', 'Ecologic']
        for c in pm_object_copy.get_final_components_objects():
            columns.append(c.get_name() + '_Capacity')

            columns.append(c.get_name() + '_Installation_Emissions')
            columns.append(c.get_name() + '_Disposal_Emissions')
            columns.append(c.get_name() + '_Fixed_Emissions')
            columns.append(c.get_name() + '_Variable_Emissions')

            columns.append(c.get_name() + '_Annual_Costs')
            columns.append(c.get_name() + '_Fixed_Costs')
            columns.append(c.get_name() + '_Variable_Costs')

        for c in pm_object_copy.get_final_commodities_objects():
            columns.append(c.get_name() + '_Available_Emissions')
            columns.append(c.get_name() + '_Emitted_Emissions')
            columns.append(c.get_name() + '_Purchase_Emissions')
            columns.append(c.get_name() + '_Sale_Emissions')

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
        multi_objective_optimization_problem = optimization_model(pm_object_copy, solver)
        multi_objective_optimization_problem.prepare(optimization_type='multiobjective',
                                                     eps_value_ecologic=results[chosen_i][-1])
        multi_objective_optimization_problem.optimize()

        pm_object_copy_local = clone_components_which_use_parallelization(pm_object_copy)
        pm_object_copy_local.set_objective_function_value(multi_objective_optimization_problem.objective_function_value)
        pm_object_copy_local.set_instance(multi_objective_optimization_problem.instance)
        pm_object_copy_local.process_results(multi_objective_optimization_problem.model_type, path_results)

        result_df = pd.DataFrame(objective_function_value_combinations).transpose()
        result_df.columns = columns

        result_df.to_excel(path_mo_result + f.split('_')[0] + '_'
                           + pm_object_copy.get_project_name() + '_multi_objective.xlsx')

    pm_object_copy.set_profile_data(path_data_before)


def optimize_no_profile(optimization_type, pm_object_copy, solver, path_results):

    if solver == 'gurobi':
        optimization_model = OptimizationGurobiModel
    else:
        optimization_model = OptimizationPyomoModel

    optimization_problem = optimization_model(pm_object_copy, solver)
    optimization_problem.prepare(optimization_type=optimization_type)
    optimization_problem.optimize()

    pm_object_copy.set_objective_function_value(optimization_problem.objective_function_value)
    pm_object_copy.set_instance(optimization_problem.instance)
    pm_object_copy.process_results(optimization_problem.model_type, path_results)
