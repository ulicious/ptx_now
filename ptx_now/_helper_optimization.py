import pandas as pd

from optimization_classes_and_methods import OptimizationProblem
from ResultAnalysis import ResultAnalysis
from _helpers_gui import save_current_parameters_and_options

from os import walk

idx = pd.IndexSlice


def optimize(pm_object, path_data, path_results, solver):

    """ Optimization either with one single case or several cases
    depend on number of generation, purchase and sale data"""

    path_data_before = pm_object.get_profile_data()
    if (len(pm_object.get_final_generator_components_names()) > 0) | (pm_object.get_commodity_data_needed()):
        # Case generators are used or commodities purchasable/saleable

        if pm_object.get_single_or_multiple_profiles() == 'single':  # Case single file generation

            optimization_problem = OptimizationProblem(pm_object, path_data, solver)
            analyze_results(pm_object, optimization_problem, path_results)

        else:  # Case with several profiles

            path_to_profiles = path_data + pm_object.get_profile_data()
            _, _, filenames_sell_purchase = next(walk(path_to_profiles))
            for fsp in filenames_sell_purchase:
                pm_object.set_profile_data(fsp)

                optimization_problem = OptimizationProblem(pm_object, path_data, solver)
                analyze_results(pm_object, optimization_problem, path_results)

            pm_object.set_path_data(path_data_before)


def analyze_results(pm_object, optimization_problem, path_result):

    result = ResultAnalysis(optimization_problem, path_result)
    save_current_parameters_and_options(pm_object, result.new_result_folder + '/7_settings.yaml')