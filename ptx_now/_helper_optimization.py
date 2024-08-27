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
    # anticipate big M, so the parameter not too high and not too low in the optimization model to cause trouble

    bigM_per_capacity = {}
    total_demand = 0
    hourly_demand = 0
    for commodity_object in pm_object.get_final_commodities_objects():
        if commodity_object.is_demanded():
            demand = commodity_object.get_demand()
            if commodity_object.is_total_demand():
                hourly_demand = demand / pm_object.get_covered_period()
                total_demand = demand
            else:
                hourly_demand = demand
                total_demand = demand * 8760

            break

    efficiency_chain = {}
    for component_object in pm_object.get_final_generator_components_objects():
        generated_commodity = component_object.get_generated_commodity()

        efficiency_chain[generated_commodity] = 1

    for commodity_object in pm_object.get_final_commodities_objects():
        if (commodity_object.is_available()) | (commodity_object.is_purchasable()):
            efficiency_chain[commodity_object.get_name()] = 1

    in_to_out_conversions = pm_object.get_main_input_to_output_conversions()[2]
    components_to_process = pm_object.get_final_conversion_components_names()
    while components_to_process:
        for component_name in components_to_process:
            component_object = pm_object.get_component(component_name)

            main_input = component_object.get_main_input()
            main_output = component_object.get_main_output()
            efficiency = in_to_out_conversions[component_name, main_input, main_output]

            if main_input in [*efficiency_chain.keys()]:
                if main_output in [*efficiency_chain.keys()]:
                    if efficiency_chain[main_input] * efficiency < efficiency_chain[main_output]:
                        # Always use the lowest efficiency of components if parallel processes exist.
                        # M will take the highest capacity value --> better than too low
                        efficiency_chain[main_output] = efficiency_chain[main_input] * efficiency
                else:
                    efficiency_chain[main_output] = efficiency_chain[main_input] * efficiency

                components_to_process.remove(component_name)

    for component_object in pm_object.get_final_components_objects():
        component_name = component_object.get_name()

        # anticipate final capacity based on hourly demand
        if component_object.get_component_type() == 'conversion':
            main_output = component_object.get_main_output()
            bigM_per_capacity[component_name] = hourly_demand * (1 / efficiency_chain[main_output]) * 10

        elif component_object.get_component_type() == 'storage':
            # set anticipated storage capacity to total demand
            bigM_per_capacity[component_name] = total_demand * (1 / efficiency_chain[component_name])

        elif component_object.get_component_type() == 'generator':
            generated_commodity = component_object.get_generated_commodity()
            bigM_per_capacity[component_name] = hourly_demand * (1 / efficiency_chain[generated_commodity]) * 10

    return bigM_per_capacity


def multi_processing_optimization_country(args):  # 0: pm_object, 1: path to file

    input_data, path_data_before, optimization_model_global, solver, optimization_type = args

    input_data[0].set_profile_data(path_data_before + '/' + input_data[1])

    optimization_problem = optimization_model_global(input_data[0], solver)
    optimization_problem.prepare(optimization_type=optimization_type)
    optimization_problem.optimize()

    return optimization_problem.economic_objective_function_value, optimization_problem.ecologic_objective_function_value

