import pandas as pd

from optimization_classes_and_methods import OptimizationProblem
from gurobi_optimization_classes_and_methods import GurobiOptimizationProblem
from gurobi_matrix_optimization_classes_and_methods import GurobiMatrixOptimizationProblem
from _helper_optimization import clone_components_which_use_parallelization

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

    def optimize_single_profile():

        now = time.time()
        optimization_problem = OptimizationProblem(pm_object_copy_pyomo, solver)

        pyomo_time_optimization = time.time() - now
        now = time.time()

        pm_object_copy_pyomo.set_objective_function_value(optimization_problem.instance.obj())
        pyomo_ofv = optimization_problem.instance.obj()
        pm_object_copy_pyomo.set_instance(optimization_problem.instance)
        pm_object_copy_pyomo.process_results(path_results, 'pyomo')
        pyomo_time_analysis = time.time() - now

        # now = time.time()
        # optimization_problem = GurobiOptimizationProblem(pm_object, solver)
        # print('time needed gurobipy: ' + str(time.time() - now))

        if True:
            now = time.time()
            optimization_problem = GurobiOptimizationProblem(pm_object_copy_gurobi, solver)

            gurobi_time_optimization = time.time() - now
            now = time.time()

            pm_object_copy_gurobi.set_objective_function_value(optimization_problem.model.objVal)
            gurobi_ofv = optimization_problem.model.objVal
            pm_object_copy_gurobi.set_instance(optimization_problem.instance)
            pm_object_copy_gurobi.process_results(path_results, solver)

            gurobi_time_analysis = time.time() - now

        print('Comparison OFV: Pyomo: ' + str(pyomo_ofv) + ' | Gurobi: ' + str(gurobi_ofv))
        print('Comparison Time Optimization: Pyomo: ' + str(pyomo_time_optimization) + ' | Gurobi: ' + str(gurobi_time_optimization))
        print('Comparison Time Analysis: Pyomo: ' + str(pyomo_time_analysis) + ' | Gurobi: ' + str(gurobi_time_analysis))

    def optimize_multiple_profiles():

        def multi_processing_optimization(input_data):  # 0: pm_object, 1: path to file
            input_data[0].set_profile_data(path_data_before + '/' + input_data[1])
            optimization_problem_mp = OptimizationProblem(input_data[0], solver)
            pm_object_copy.set_instance(optimization_problem_mp.instance)

            pm_object_copy.process_results(path_results)

            return [input_data[1], 'Dummy']  # todo: remove

        num_cores = min(32, multiprocessing.cpu_count() - 1)

        path_data_before = pm_object_copy.get_profile_data()
        path_to_profiles = path_data + pm_object_copy.get_profile_data()
        _, _, filenames_sell_purchase = next(walk(path_to_profiles))

        new_input = []
        for f in filenames_sell_purchase:
            new_input.append((deepcopy(pm_object_copy), f))

        inputs = tqdm(new_input)
        common_results = Parallel(n_jobs=num_cores)(delayed(multi_processing_optimization)(i) for i in inputs)

        pm_object_copy.set_profile_data(path_data_before)

        first = True
        common_results_df = None
        for i in common_results:
            if first:
                common_results_df = pd.DataFrame(i[1], index=[i[0]])
                first = False
            else:
                k_df = pd.DataFrame(i[1], index=[i[0]])
                common_results_df = common_results_df.append(k_df)

        common_results_df.to_excel(path_results + pm_object_copy.get_project_name() + '_common_results.xlsx')

    def optimize_no_profile():
        now = time.time()
        optimization_problem = OptimizationProblem(pm_object_copy, solver)
        pyomo_ofv = optimization_problem.instance.obj()
        pyomo_time = time.time() - now

        pm_object_copy.set_instance(optimization_problem.instance)
        pm_object_copy.process_results(path_results, solver)

        # now = time.time()
        # optimization_problem = GurobiOptimizationProblem(pm_object, solver)
        # print('time needed gurobipy: ' + str(time.time() - now))

        if True:
            now = time.time()
            optimization_problem = GurobiOptimizationProblem(pm_object_copy, solver)
            gurobi_ofv = optimization_problem.model.objVal
            pm_object_copy.set_instance(optimization_problem.instance)
            pm_object_copy.process_results(path_results, solver)
            gurobi_time = time.time() - now

        print('Comparison OFV: Pyomo: ' + str(pyomo_ofv) + ' | Gurobi: ' + str(gurobi_ofv))
        print('Comparison Time: Pyomo: ' + str(pyomo_time) + ' | Gurobi: ' + str(gurobi_time))

        # optimization_problem = GurobiOptimizationProblem(pm_object, solver)

    # Adjust pm_object if parallel units are used
    pm_object_copy_pyomo = clone_components_which_use_parallelization(pm_object) # todo: remove as soon as decided
    pm_object_copy_gurobi = clone_components_which_use_parallelization(pm_object)
    pm_object_copy = clone_components_which_use_parallelization(pm_object)

    if (len(pm_object_copy.get_final_generator_components_names()) > 0) | (pm_object_copy.get_commodity_data_needed()):

        # todo: case where single profiles but multiple cases

        if pm_object_copy.get_single_or_multiple_profiles() == 'single':

            optimize_single_profile()

        else:
            # multiple profiles are processed using multiprocessing
            optimize_multiple_profiles()

    else:

        # todo: multiple cases

        optimize_no_profile()

    print('Optimization completed.')


