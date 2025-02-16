import pandas as pd

from _helper_optimization import clone_components_which_use_parallelization
from optimization_types import optimize_single_profile_not_multi_objective, optimize_single_profile_multi_objective,\
    optimize_multi_profiles_no_multi_optimization, multi_profiles_multi_objective, optimize_no_profile

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

    # Adjust pm_object if parallel units are used
    pm_object_copy = clone_components_which_use_parallelization(pm_object)

    optimization_type = pm_object_copy.get_optimization_type()
    profile_needed = (len(pm_object_copy.get_final_generator_components_names()) > 0) | (pm_object_copy.get_commodity_data_needed())
    profile_type = pm_object_copy.get_single_or_multiple_profiles()

    if (optimization_type == 'economical') | (optimization_type == 'ecological'):

        if profile_needed:

            # todo: case where single profiles but multiple cases

            if profile_type == 'single':

                optimize_single_profile_not_multi_objective(optimization_type, pm_object_copy, solver, path_results)

            else:
                # multiple profiles are processed using multiprocessing
                optimize_multi_profiles_no_multi_optimization(optimization_type, pm_object_copy, solver, path_results)

        else:

            # todo: multiple cases like above

            optimize_no_profile(optimization_type, pm_object_copy, solver, path_results)

    else:
        if profile_needed:
            # Difference to economical / ecological: multi-objective approach uses parallelization therefore can't
            # process different profiles in parallelization

            if pm_object_copy.get_single_or_multiple_profiles() == 'single':

                optimize_single_profile_multi_objective(pm_object_copy, solver, path_results)

            else:
                # multiple profiles are processed using multiprocessing
                multi_profiles_multi_objective(pm_object_copy, solver, path_results)

        else:

            # todo: multiple cases

            optimize_no_profile(optimization_type, pm_object_copy, solver, path_results)

    print('Optimization completed.')


