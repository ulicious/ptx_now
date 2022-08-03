import pandas as pd

from optimization_classes_and_methods import OptimizationProblem
from ResultAnalysis import ResultAnalysis
from _helpers_gui import save_current_parameters_and_options

from os import walk

idx = pd.IndexSlice


def optimize(pm_object, path_data, path_results, solver):

    """ Optimization either with one single case or several cases
    depend on number of generation, purchase and sale data"""

    generation_data_before = pm_object.get_generation_data()
    commodity_data_before = pm_object.get_commodity_data()

    optimization_problem = None
    if len(pm_object.get_final_generator_components_names()) > 0:
        # Case generators are used

        if pm_object.get_commodity_data_needed():  # Case market data available

            if pm_object.get_single_or_multiple_generation_profiles() == 'single':  # Case single file generation

                path_to_generation_files = path_data + pm_object.get_generation_data()
                pm_object.set_generation_data(path_to_generation_files)

                path_to_sell_purchase_files = path_data + pm_object.get_commodity_data()

                if pm_object.get_single_or_multiple_commodity_profiles() == 'single':  # Case single market data file

                    pm_object.set_commodity_data(path_to_sell_purchase_files)

                    optimization_problem = OptimizationProblem(pm_object, path_data, solver)
                    analyze_results(pm_object, optimization_problem, path_results)

                else:  # Case with several market data files

                    _, _, filenames_sell_purchase = next(walk(path_to_sell_purchase_files))
                    for fsp in filenames_sell_purchase:
                        pm_object.set_commodity_data(path_to_sell_purchase_files + '/' + fsp)

                        optimization_problem = OptimizationProblem(pm_object, path_data, solver)
                        analyze_results(pm_object, optimization_problem, path_results)

            else:  # Case several generation files
                path_to_generation_files = path_data + pm_object.get_generation_data()
                path_to_sell_purchase_files = path_data + pm_object.get_commodity_data()

                if pm_object.get_single_or_multiple_commodity_profiles() == 'single':
                    # Case with several generation profiles but only one market profile

                    pm_object.set_commodity_data(path_to_sell_purchase_files)

                    _, _, filenames_generation = next(walk(path_to_generation_files))
                    for fg in filenames_generation:
                        pm_object.set_generation_data(path_to_generation_files + '/' + fg)

                        optimization_problem = OptimizationProblem(pm_object, path_data, solver)
                        analyze_results(pm_object, optimization_problem, path_results)
                else:
                    # Case with several generation and purchase/sale profiles

                    _, _, filenames_generation = next(walk(path_to_generation_files))
                    _, _, filenames_sell_purchase = next(walk(path_to_sell_purchase_files))
                    for fg in filenames_generation:
                        for fsp in filenames_sell_purchase:
                            pm_object.set_generation_data(path_to_generation_files + '/' + fg)

                            pm_object.set_commodity_data(path_to_sell_purchase_files + '/' + fsp)

                            optimization_problem = OptimizationProblem(pm_object, path_data,
                                                                       solver)
                            analyze_results(pm_object, optimization_problem, path_results)

        else:  # Case no market data
            if pm_object.get_single_or_multiple_generation_profiles() == 'single':
                # Case only generation with single file

                path_to_generation_files = path_data + pm_object.get_generation_data()
                pm_object.set_generation_data(path_to_generation_files)

                optimization_problem = OptimizationProblem(pm_object, path_data, solver)
                analyze_results(pm_object, optimization_problem, path_results)

            else:  # Case only generation with several files
                path_to_generation_files = path_data + pm_object.get_generation_data()

                _, _, filenames_generation = next(walk(path_to_generation_files))
                for fg in filenames_generation:
                    pm_object.set_generation_data(path_to_generation_files + '/' + fg)

                    optimization_problem = OptimizationProblem(pm_object, path_data, solver)
                    analyze_results(pm_object, optimization_problem, path_results)

    else:  # Case generators are not used

        if pm_object.get_commodity_data_needed():
            if pm_object.get_single_or_multiple_commodity_profiles() == 'single':
                #  one case
                path_to_market_file = path_data + pm_object.get_commodity_data()
                pm_object.set_commodity_data(path_to_market_file)
                optimization_problem = OptimizationProblem(pm_object, path_data, solver)
                analyze_results(pm_object, optimization_problem, path_results)
            else:
                # Case with several purchase and selling price data
                path_to_sell_purchase_files = path_data + pm_object.get_commodity_data()

                _, _, filenames_sell_purchase = next(walk(path_to_sell_purchase_files))
                for fsp in filenames_sell_purchase:
                    pm_object.set_commodity_data(path_to_sell_purchase_files + '/' + fsp)

                    optimization_problem = OptimizationProblem(pm_object, path_data, solver)
                    analyze_results(pm_object, optimization_problem, path_results)

        else:
            optimization_problem = OptimizationProblem(pm_object, path_data, solver)
            analyze_results(pm_object, optimization_problem, path_results)

    pm_object.set_generation_data(generation_data_before)
    pm_object.set_commodity_data(commodity_data_before)


def analyze_results(pm_object, optimization_problem, path_result):

    result = ResultAnalysis(optimization_problem, path_result)
    save_current_parameters_and_options(pm_object, result.new_result_folder + '/7_settings.yaml')