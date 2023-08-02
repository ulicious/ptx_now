import pandas as pd

from optimization_classes_and_methods import OptimizationProblem
from gurobi_optimization_classes_and_methods import GurobiOptimizationProblem
from gurobi_matrix_optimization_classes_and_methods import GurobiMatrixOptimizationProblem
from ResultAnalysis import ResultAnalysis
from _helpers_gui import save_current_parameters_and_options
from joblib import Parallel, delayed
from tqdm import tqdm
import multiprocessing
from copy import deepcopy

from os import walk

import time

idx = pd.IndexSlice


def optimize(pm_object, path_data, path_results, solver):

    """ Optimization either with one single case or several cases
    depend on number of generation, purchase and sale data"""

    if (len(pm_object.get_final_generator_components_names()) > 0) | (pm_object.get_commodity_data_needed()):
        # Case generators are used and/or commodities purchasable/saleable

        if pm_object.get_single_or_multiple_profiles() == 'single':  # Case single file generation

            # now = time.time()
            optimization_problem = OptimizationProblem(pm_object, solver)
            # print('time needed pyomo: ' + str(time.time() - now))

            result = ResultAnalysis(optimization_problem, path_results)
            save_current_parameters_and_options(pm_object, result.new_result_folder + '/7_settings.yaml',
                                                    result_mp.all_variables_dict['nominal_cap'])

            # now = time.time()
            # optimization_problem = GurobiOptimizationProblem(pm_object, solver)
            # print('time needed gurobipy: ' + str(time.time() - now))

            if False:

                now = time.time()
                optimization_problem = GurobiMatrixOptimizationProblem(pm_object, solver)
                print('time needed gurobipy: ' + str(time.time() - now))

        else:  # Case with several profiles

            def multi_processing_optimization(input_data):  # 0: pm_object, 1: path to file
                input_data[0].set_profile_data(path_data_before + '/' + input_data[1])

                optimization_problem_mp = OptimizationProblem(input_data[0], solver)
                result_mp = ResultAnalysis(optimization_problem_mp, path_results)
                save_current_parameters_and_options(pm_object, result_mp.new_result_folder + '/7_settings.yaml',
                                                    result_mp.all_variables_dict['nominal_cap'])

                return [input_data[1], result_mp.exported_results]

            num_cores = min(32, multiprocessing.cpu_count()-1)

            path_data_before = pm_object.get_profile_data()
            path_to_profiles = path_data + pm_object.get_profile_data()
            _, _, filenames_sell_purchase = next(walk(path_to_profiles))

            new_input = []
            for f in filenames_sell_purchase:
                new_input.append((deepcopy(pm_object), f))

            inputs = tqdm(new_input)
            common_results = Parallel(n_jobs=num_cores)(delayed(multi_processing_optimization)(i) for i in inputs)

            pm_object.set_profile_data(path_data_before)

            first = True
            common_results_df = None
            for i in common_results:
                if first:
                    common_results_df = pd.DataFrame(i[1], index=[i[0]])
                    first = False
                else:
                    k_df = pd.DataFrame(i[1], index=[i[0]])
                    common_results_df = common_results_df.append(k_df)

            common_results_df.to_excel(path_results + pm_object.get_project_name() + '_common_results.xlsx')

    else:
        optimization_problem = OptimizationProblem(pm_object, solver)
        result = ResultAnalysis(optimization_problem, path_results)
        save_current_parameters_and_options(pm_object, result.new_result_folder + '/7_settings.yaml',
                                            result.all_variables_dict['nominal_cap'])

        # optimization_problem = GurobiOptimizationProblem(pm_object, solver)

    print('Optimization completed.')
