import pandas as pd

from optimization_classes_and_methods import OptimizationProblem
from ResultAnalysis import ResultAnalysis
from _helpers_gui import save_current_parameters_and_options
from joblib import Parallel, delayed
from tqdm import tqdm
import multiprocessing
from copy import deepcopy

from os import walk

idx = pd.IndexSlice


def optimize(pm_object, path_data, path_results, solver):

    """ Optimization either with one single case or several cases
    depend on number of generation, purchase and sale data"""

    if (len(pm_object.get_final_generator_components_names()) > 0) | (pm_object.get_commodity_data_needed()):
        # Case generators are used and/or commodities purchasable/saleable

        if pm_object.get_single_or_multiple_profiles() == 'single':  # Case single file generation

            optimization_problem = OptimizationProblem(pm_object, solver)
            analyze_results(pm_object, optimization_problem, path_results)

        else:  # Case with several profiles

            def multi_processing_optimization(input_data):
                input_data[0].set_profile_data(path_data_before + '/' + input_data[1])

                optimization_problem_mp = OptimizationProblem(input_data[0], solver)
                analyze_results(input_data[0], optimization_problem_mp, path_results)

            num_cores = min(32, multiprocessing.cpu_count()-1)

            path_data_before = pm_object.get_profile_data()
            path_to_profiles = path_data + pm_object.get_profile_data()
            _, _, filenames_sell_purchase = next(walk(path_to_profiles))

            while len(filenames_sell_purchase) > 0:

                if len(filenames_sell_purchase) > num_cores:

                    i = 0
                    new_input = []
                    for f in filenames_sell_purchase:
                        new_input.append((deepcopy(pm_object), f))

                        i += 1
                        if i == num_cores:
                            break

                    filenames_sell_purchase = filenames_sell_purchase[num_cores:]

                else:
                    new_input = []
                    for f in filenames_sell_purchase:
                        new_input.append((deepcopy(pm_object), f))

                    filenames_sell_purchase = []

                inputs = tqdm(new_input)
                Parallel(n_jobs=num_cores)(delayed(multi_processing_optimization)(i) for i in inputs)

            pm_object.set_path_data(path_data_before)

    else:
        optimization_problem = OptimizationProblem(pm_object, solver)
        analyze_results(pm_object, optimization_problem, path_results)


def analyze_results(pm_object, optimization_problem, path_result):

    result = ResultAnalysis(optimization_problem, path_result)
    save_current_parameters_and_options(pm_object, result.new_result_folder + '/7_settings.yaml')
