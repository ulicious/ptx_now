import time

import pandas as pd

from primal_model import SuperProblemRepresentative
from primal_model_gurobi import GurobiPrimalProblem
from dual_model import ExtremeCaseBilinear
# from dual_model_gurobi import GurobiDualProblem
from old_dual import GurobiDualProblem
from dual_model_gurobi_no_uncertainty import GurobiDualProblem as dual_no_uncertainty
from primal_model_fixed_cluster_gurobi import GurobiPrimalProblemFixedCluster

import parameters


def run_decomposition(pm_object, solver, input_profiles, number_cluster, worst_case_cluster, weighting,
                      all_profiles, number_profiles, path_results, costs_missing_product,
                      input_profiles_clusters, input_profiles_iteration, weightings_cluster, weighting_iteration):

    tolerance = 0.01
    UB = float('inf')
    iteration = 0

    kwargs = {}

    capacities = {}
    total_costs_dict = {'UB': {},
                        'LB': {}}

    capacity_df = None

    _, total_demand = pm_object.get_demand_time_series()
    time_start = time.time()

    times = pd.DataFrame(columns=['first', 'second', 'total'])

    first = True
    while True:
        if False:
            time_old = time.time()

            print('old approach')
            sup_problem = SuperProblemRepresentative(pm_object, solver, input_profiles, worst_case_cluster, weighting, iteration)
            sup_problem.optimize()

            capacities_new = sup_problem.optimal_capacities
            capacities[iteration] = capacities_new

            print(sup_problem.obj_value)
            print(capacities_new)
            LB = sup_problem.obj_value

            total_costs_LB = LB / total_demand[parameters.energy_carrier]
            print('Production costs first stage: ' + str(total_costs_LB))

            # sub_problem = ExtremeCaseBilinear(pm_object, solver, capacities_new, input_profiles, all_profiles,
            #                                   worst_case_cluster,
            #                                   weighting, number_profiles, costs_missing_product, **kwargs)
            # sub_problem.optimize()
            # UB = min(UB, sup_problem.obj_value - sup_problem.auxiliary_variable + sub_problem.obj_value)
            # print(UB)

            print(time.time() - time_old)
            print('___________________________')

        if True:
            time_first = time.time()
            sup_problem = GurobiPrimalProblem(pm_object, solver, input_profiles, number_cluster, weighting,
                                              iteration, costs_missing_product, parameters.demand_type)
            sup_problem.prepare()
            sup_problem.optimize()
            objective_function_value = sup_problem.objective_function_value
            capacities_new = sup_problem.get_results()

            print(capacities_new)
            print(objective_function_value)

            # capacities_new = {'CO2 Kompressor': 3.134161860499101, 'CO2 compressed': 15602.782744204125, 'DAC': 25.547455661062124, 'Electricity': 977.9138269588296, 'H2 Dekompressor': 373.44098900350417, 'H2 Kompressor': 2.342820523119248, 'Hydrogen': 0.0, 'Hydrogen compressed': 7128.717595882437, 'Solar': 1209.4290051812418, 'Synthesis Island': 255.49163060992328, 'Wind': 712.6491659286404, 'electrolyzer': 485.0818491690336}

            times.at[iteration, 'first'] = (time.time() - time_first) / 60
            time_second = time.time()

            if first:
                not_robust_capacities = capacities_new
                first = False

            capacities[iteration] = capacities_new

            LB = objective_function_value

            total_costs_LB = LB / total_demand[parameters.energy_carrier]
            print('Production costs first stage: ' + str(total_costs_LB))

            sub_problem = GurobiDualProblem(pm_object, solver, capacities_new, input_profiles[iteration], all_profiles,
                                            worst_case_cluster, weighting, number_profiles, costs_missing_product,
                                            parameters.demand_type, **kwargs)
            sub_problem.optimize()

            times.at[iteration, 'second'] = (time.time() - time_second) / 60
            times.at[iteration, 'total'] = (time.time() - time_first) / 60

            times.at[iteration, 'primal_cont_vars'] = sup_problem.num_cont_vars
            times.at[iteration, 'dual_cont_vars'] = sub_problem.num_cont_vars
            times.at[iteration, 'dual_bin_vars'] = sub_problem.num_bin_vars

            UB = min(UB, sup_problem.objective_function_value - sup_problem.auxiliary_variable_value + sub_problem.objective_function_value)
            print('Time Iteration [m]: ' + str((time.time() - time_first) / 60))

        total_costs_UB = UB / total_demand[parameters.energy_carrier]
        total_costs_dict['UB'][iteration] = total_costs_UB

        total_costs_LB = LB / total_demand[parameters.energy_carrier]
        total_costs_dict['LB'][iteration] = total_costs_LB

        print('Iteration number: ' + str(iteration))

        print(sup_problem.auxiliary_variable_value)
        print(sub_problem.objective_function_value)

        print('Specific costs UB: ' + str(total_costs_UB))
        print('Specific costs LB: ' + str(total_costs_LB))

        # difference = (UB - LB) / LB
        difference = UB - LB
        print('Difference is: ' + str(difference))

        # if -tolerance <= difference <= tolerance:
        if difference <= tolerance:

            first = True
            for k in [*capacities.keys()]:
                if first:
                    capacity_df = pd.DataFrame.from_dict(capacities[k], orient='index')
                    first = False
                else:
                    capacity_df[k] = pd.DataFrame.from_dict(capacities[k], orient='index')

            capacity_df.to_excel(path_results + 'capacity.xlsx')

            profiles_df = pd.DataFrame()
            for i in [*input_profiles.keys()]:
                for g in [*input_profiles[i].keys()]:
                    for c in [*input_profiles[i][g].keys()]:
                        profiles_df[str(i) + '_' + g + '_' + str(c)] = input_profiles[i][g][c]

            profiles_df.to_excel(path_results + 'profiles.xlsx')

            if True:

                first = True
                total_costs_df = pd.DataFrame()
                for k in [*total_costs_dict.keys()]:
                    if first:
                        total_costs_df = pd.DataFrame.from_dict(total_costs_dict[k], orient='index')
                        first = False
                    else:
                        total_costs_df[k] = pd.DataFrame.from_dict(total_costs_dict[k], orient='index')
                total_costs_df.to_excel(path_results + 'total_costs.xlsx')

            times.at['final', 'total'] = (time.time() - time_start) / 60
            times.to_excel(path_results + 'times.xlsx')

            print('optimization successful')
            print('time needed: ' + str((time.time() - time_start) / 60) + ' minutes')

            break

        else:

            iteration += 1
            input_profiles[iteration] = {}

            input_profiles[iteration]['Wind'] = input_profiles[0]['Wind'].copy()
            input_profiles[iteration]['Solar'] = input_profiles[0]['Solar'].copy()

            input_profiles[iteration]['Wind'][worst_case_cluster] = sub_problem.chosen_profiles['Wind']
            input_profiles[iteration]['Solar'][worst_case_cluster] = sub_problem.chosen_profiles['Solar']

            # input_profiles_iteration['Wind'][iteration] = sub_problem.chosen_profiles['Wind']
            # input_profiles_iteration['Solar'][iteration] = sub_problem.chosen_profiles['Solar']

            # chosen_profile = None
            # for p in range(number_profiles):
            #     if sub_problem.weighting_profiles_binary[p].X == 1:
            #         chosen_profile = p
            #
            # adjusted_columns = [c for c in all_profiles.columns
            #                     if '_' + str(chosen_profile) not in c]
            # all_profiles = all_profiles[adjusted_columns]
            # number_profiles -= 1

    return capacities_new, not_robust_capacities
