import itertools
from copy import deepcopy


def clone_components_which_use_parallelization(pm_object):
    pm_object_copy = deepcopy(pm_object)

    # Copy components if number of components in system is higher than 1
    for component_object in pm_object_copy.get_final_conversion_components_objects():
        if component_object.get_number_parallel_units() > 1:
            # Simply rename first component
            component_name = component_object.get_name()

            component_object.set_name(component_name + '_0')
            pm_object_copy.remove_component_entirely(component_name)
            pm_object_copy.add_component(component_name + '_0', component_object)

            for i in range(1, int(component_object.get_number_parallel_units())):
                # Add other components as copy
                parallel_unit_component_name = component_name + '_parallel_' + str(i)
                component_copy = component_object.__copy__()
                component_copy.set_name(parallel_unit_component_name)
                pm_object_copy.add_component(parallel_unit_component_name, component_copy)

    return pm_object_copy


def anticipate_bigM(pm_object):
    from collections import defaultdict
    # anticipate big M, so the parameter not too high and not too low in the optimization model to cause trouble

    bigM_per_capacity = {}
    commodity_max_demand = defaultdict(float)
    total_demand = 0
    hourly_demand = 0
    paths = {}
    path_quantities = {}
    path_conversions = {}
    processed_commodities = []
    for commodity_object in pm_object.get_final_commodities_objects():
        if commodity_object.is_demanded():
            demand = commodity_object.get_demand()
            if commodity_object.is_total_demand():
                hourly_demand = demand / 8760
                total_demand = demand
            else:
                hourly_demand = demand
                total_demand = demand * 8760

            commodity_max_demand[commodity_object.get_name()] = hourly_demand  # could be increased to make sure sufficient
            paths[0] = [commodity_object.get_name()]
            path_quantities[0] = [hourly_demand]
            path_conversions[0] = []

            processed_commodities.append(commodity_object.get_name())

            break

    conversion_objects = pm_object.get_final_conversion_components_objects()
    processed_conversions = []
    in_to_out_conversions = pm_object.get_main_input_to_output_conversions()[2]
    in_to_in_conversions = pm_object.get_main_input_to_input_conversions()[2]

    n_paths = 1
    while len(processed_conversions) != len(conversion_objects):
        for conversion in conversion_objects:

            if conversion in processed_conversions:
                continue

            main_output = conversion.get_main_output()
            main_input = conversion.get_main_input()

            input_demand = 1 / in_to_out_conversions[conversion.get_name(), main_input, main_output]

            if main_output in processed_commodities:
                inputs = conversion.get_inputs()

                for i in inputs:
                    for p in [*paths.keys()]:

                        if main_output != paths[p][-1]:
                            continue

                        if i in paths[p]:
                            continue

                        paths[n_paths] = paths[p] + [i]
                        path_conversions[n_paths] = path_conversions[p] + [conversion.get_name()]

                        input_demand_path = input_demand * path_quantities[p][-1]
                        if i == main_input:
                            path_quantities[n_paths] = path_quantities[p] + [input_demand_path]
                        else:
                            i_demand_path = input_demand_path * in_to_in_conversions[conversion.get_name(), main_input, i]
                            path_quantities[n_paths] = path_quantities[p] + [i_demand_path]

                        n_paths += 1

                        processed_commodities.append(i)

                processed_conversions.append(conversion)

    paths_to_remove = []

    # removes all paths where scaling would be based on other input than main
    for p in [*path_conversions.keys()]:

        if len(path_conversions[p]) == 0:
            continue

        c = path_conversions[p][-1]
        c_object = pm_object.get_component(c)
        main_input = c_object.get_main_input()
        last_input = paths[p][-1]
        if last_input != main_input:
            paths_to_remove.append(p)

    # sort paths by length of conversion path --> most efficient paths are probably such which are the shortest
    path_conversions = dict(sorted(path_conversions.items(), key=lambda item: len(item[1]), reverse=True))
    paths = {k: paths[k] for k in path_conversions.keys()}
    path_quantities = {k: path_quantities[k] for k in path_conversions.keys()}

    bigM_per_capacity = {}
    for p in [*path_conversions.keys()]:
        if p in paths_to_remove:
            continue

        for i, c in enumerate(path_conversions[p]):

            c_object = pm_object.get_component(c)
            main_input = c_object.get_main_input()

            if paths[p][i+1] != main_input:
                continue

            bigM_per_capacity[c] = path_quantities[p][i+1] * 100

    for p in [*paths.keys()]:
        if p in paths_to_remove:
            continue

        for i, c in enumerate(paths[p]):
            bigM_per_capacity[c] = path_quantities[p][i] * 2000

    return bigM_per_capacity


def multi_processing_optimization_country(args):  # 0: pm_object, 1: path to file

    pm_object, path_data_before, f, optimization_model_global, solver, optimization_type, solar_cap, wind_cap = args

    pm_object.set_profile_data(path_data_before + '/' + f)

    max_cap = {'Solar': solar_cap, 'Wind': wind_cap}

    optimization_problem = optimization_model_global(pm_object, solver, max_cap)
    optimization_problem.prepare(optimization_type=optimization_type)
    optimization_problem.optimize()

    # print(optimization_problem.total_production.X)

    return optimization_problem.economic_objective_function_value, optimization_problem.ecologic_objective_function_value, \
        optimization_problem.nominal_cap['Solar'].X, optimization_problem.nominal_cap['Wind'].X

