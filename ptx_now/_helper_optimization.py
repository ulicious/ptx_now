from pyomo.core import *

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sklearn.linear_model import LinearRegression

import math

idx = pd.IndexSlice


def calculate_economies_of_scale_steps(component_object, pm_object, plot=False):

    component_name = component_object.get_name()

    if component_object.get_capex_basis == 'output':
        i = component_object.get_main_input()
        i_coefficient = component_object.get_inputs()[i]
        o = component_object.get_main_output()
        o_coefficient = component_object.get_outputs()[o]
        ratio = o_coefficient / i_coefficient
    else:
        ratio = 1

    base_capacity = component_object.get_base_capacity()
    economies_of_scale = component_object.get_economies_of_scale()
    max_capacity_economies_of_scale = component_object.get_max_capacity_economies_of_scale()
    base_investment = component_object.get_base_investment() * ratio

    # First, calculate the investment curve based on the economies of scale

    # If max_capacity is high than calculating every step would increase calculation time
    # Therefore, the approach uses 1000 capacities to calculate the investment

    integer_steps = pm_object.get_integer_steps()

    max_invest = base_investment * (max_capacity_economies_of_scale / base_capacity) ** economies_of_scale
    delta_investment_per_step = max_invest / (integer_steps - 1)

    lower_bound = {(component_name, 0): 0}
    upper_bound = {(component_name, 0): 0}
    coefficient = {(component_name, 0): 0}
    intercept = {(component_name, 0): 0}

    # Find capacities at beginning/end of steps
    capacities = {}
    investments = {}
    for i in range(integer_steps):
        investment = i * delta_investment_per_step
        investments[i] = investment
        capacity = (investment / base_investment) ** (1 / economies_of_scale) * base_capacity
        capacities[i] = capacity

    for i in range(integer_steps):
        if i == integer_steps - 1:
            continue

        upper_bound[(component_name, i+1)] = capacities[i+1]
        lower_bound[(component_name, i+1)] = capacities[i]

        y_value = np.zeros([len(range(int(capacities[i]), int(capacities[i+1])))])
        x_value = np.zeros([len(range(int(capacities[i]), int(capacities[i+1])))]).reshape((-1, 1))

        k = 0
        for j in range(int(capacities[i]), int(capacities[i+1])):
            x_value[k] = j
            if x_value[k] != 0:
                y_value[k] = base_investment * (j / base_capacity) ** economies_of_scale
            else:
                y_value[k] = 0
            k += 1

        model = LinearRegression().fit(x_value, y_value)
        coefficient[(component_name, i+1)] = model.coef_[0]
        intercept[(component_name, i+1)] = model.intercept_

    # Calculate coefficient, intercept, lower bound and upper bound for step without upper bound
    investment = integer_steps * delta_investment_per_step
    capacity = (investment / base_investment) ** (1 / economies_of_scale) * base_capacity
    upper_bound[(component_name, integer_steps)] = math.inf
    lower_bound[(component_name, integer_steps)] = capacities[integer_steps - 1]

    y_value = np.zeros([len(range(int(capacities[integer_steps - 1]), int(capacity)))])
    x_value = np.zeros([len(range(int(capacities[integer_steps - 1]), int(capacity)))]).reshape((-1, 1))
    k = 0
    for j in range(int(capacities[integer_steps - 1]), int(capacity)):
        x_value[k] = j
        if x_value[k] != 0:
            y_value[k] = base_investment * (j / base_capacity) ** economies_of_scale
        else:
            y_value[k] = 0
        k += 1

        model = LinearRegression().fit(x_value, y_value)
        coefficient[(component_name, integer_steps)] = model.coef_[0]
        intercept[(component_name, integer_steps)] = model.intercept_

    if plot:
        plt.figure()
        y = []
        x = []

        x_value_absolut = np.zeros([len(range(0, int(max_capacity_economies_of_scale)))])
        y_value_absolut = np.zeros([len(range(0, int(max_capacity_economies_of_scale)))])
        for i in range(int(max_capacity_economies_of_scale)):
            if i == 0:
                y_value_absolut[i] = 0
            else:
                y_value_absolut[i] = base_investment * (i / base_capacity) ** economies_of_scale

            x_value_absolut[i] = i

        for i in [*intercept.keys()]:

            low = int(lower_bound[i])
            if upper_bound[i] == math.inf:
                up = int(lower_bound[i] * 1.2)
            else:
                up = int(upper_bound[i])

            for capacity in range(low, up):
                y.append(intercept[i] + capacity * coefficient[i])
                x.append(capacity)

        plt.plot(x, y, marker='', color='red', linewidth=2)
        plt.plot(x_value_absolut, y_value_absolut, marker='', color='olive', linewidth=2)

        plt.title(component_object.get_nice_name())
        plt.xlabel('Capacity')
        plt.ylabel('Total investment in €')

        plt.show()

    return lower_bound, upper_bound, coefficient, intercept


def create_conversion_factor_matrix(conversion_factor, year):
    """ Creates the matrix, which contents the ratio from one material to another """
    """ Important: All units are converted to tons """

    # Create dictionary with conversion factors
    main_conversion_df = conversion_factor[conversion_factor['main']]
    side_conversion_df = conversion_factor[~conversion_factor['main']]

    main_conversion_factor_dict = {}
    side_conversion_factor_dict = {}

    main_conversion_tuples = []
    side_conversion_tuples = []

    main_inputs = []
    unit_dict = {}

    components = conversion_factor['component'].unique()
    inputs = conversion_factor['input'].unique()
    outputs = conversion_factor['output'].unique()

    for i in inputs:
        input_df = conversion_factor[conversion_factor['input'] == i]
        for ind in input_df.index:
            unit_dict.update({i: input_df.loc[ind, 'unit_input']})
            break

    for o in outputs:
        output_df = conversion_factor[conversion_factor['output'] == o]
        for ind in output_df.index:
            unit_dict.update({o: output_df.loc[ind, 'unit_output']})
            break

    for c in components:
        component_main_conversion_df = main_conversion_df[main_conversion_df['component'] == c]
        component_side_conversion_df = side_conversion_df[side_conversion_df['component'] == c]

        for i in inputs:
            component_main_conversion_input_df = component_main_conversion_df[component_main_conversion_df['input'] == i]
            component_side_conversion_input_df = component_side_conversion_df[component_side_conversion_df['input'] == i]
            for o in outputs:
                tuples = (c, i, o)
                if i == o:
                    main_conversion_factor_dict.update({tuples: 0})
                    main_conversion_factor_dict.update({tuples: 0})
                else:
                    # Conversion
                    conversion_df_output = component_main_conversion_input_df[component_main_conversion_input_df['output'] == o]
                    if not conversion_df_output.empty:
                        main_conversion_factor_dict.update({tuples: conversion_df_output[year].values[0]})
                        main_conversion_tuples.append(tuples)
                    else:
                        main_conversion_factor_dict.update({tuples: 0})

                    # Joint products
                    joint_product_df_output = component_side_conversion_input_df[component_side_conversion_input_df['output'] == o]
                    if not joint_product_df_output.empty:
                        side_conversion_factor_dict.update({tuples: joint_product_df_output[year].values[0]})
                        side_conversion_tuples.append(tuples)
                    else:
                        side_conversion_factor_dict.update({tuples: 0})

    return main_conversion_tuples, main_conversion_factor_dict, side_conversion_tuples, side_conversion_factor_dict, main_inputs, unit_dict


def create_demand_matrix(model, conversion_factor):
    """ Creates the matrix, which contents the demand of different components """
    """ Important: All units are converted to tons """

    # Create dictionary with conversion factors

    demand_dict = {}
    demand_df = conversion_factor.loc[conversion_factor.index.get_level_values('type').str.contains('demand')]
    for c in model.COMPONENTS:
        component_conversion_df = demand_df.loc[demand_df.index.get_level_values('component').str.contains(c)]
        for i in model.INPUT:
            df_input = component_conversion_df.loc[
                component_conversion_df.index.get_level_values('input').str.contains(i)]
            for o in model.OUTPUT:
                tuples = (c, i, o)
                if i == o:
                    demand_dict.update({tuples: 1})
                else:
                    df_output = df_input.loc[df_input.index.get_level_values('output').str.contains(o)]

                    if not df_output.empty:
                        demand_dict.update({tuples: df_output.values[0]})
                    else:
                        demand_dict.update({tuples: 0})

    model.DEMAND = Param(model.COMPONENTS, model.INPUT, model.OUTPUT, initialize=demand_dict)

    return model


def create_joint_products_matrix(model, conversion_factor):
    """ Creates the matrix, which contents the demand of different components """
    """ Important: All units are converted to tons """

    # Create dictionary with conversion factors

    joint_product_dict = {}
    joint_product_df = conversion_factor.loc[conversion_factor.index.get_level_values('type').str.contains('joint_product')]
    for c in model.COMPONENTS:
        component_conversion_df = joint_product_df.loc[joint_product_df.index.get_level_values('component').str.contains(c)]
        for i in model.INPUT:
            df_input = component_conversion_df.loc[
                component_conversion_df.index.get_level_values('input').str.contains(i)]
            for o in model.OUTPUT:
                tuples = (c, i, o)
                if i == o:
                    joint_product_dict.update({tuples: 1})
                else:
                    df_output = df_input.loc[df_input.index.get_level_values('output').str.contains(o)]

                    if not df_output.empty:
                        joint_product_dict.update({tuples: df_output.values[0]})
                    else:
                        joint_product_dict.update({tuples: 0})

    model.JOINT_PRODUCTS = Param(model.COMPONENTS, model.INPUT, model.OUTPUT, initialize=joint_product_dict)

    return model


def not_used():

    if False:
        # co2 intensity
        model.total_co2_intensity = Var(bounds=(0, None))

        def calculate_total_intensity_rule(model):
            return model.total_co2_intensity == (sum(model.p_grid[t] for t in model.TIME) * co2_intensity_electricity \
                                                 + sum(
                        sum(model.p_generation[generator, t] for generator in model.GENERATOR) for t in model.TIME) \
                                                 * co2_intensity_generation) \
                   / (sum(model.demand[t] for t in model.TIME) * 1000 * energy_density_fuel)

        model.calculate_total_intensity_con = Constraint(rule=calculate_total_intensity_rule)

        model.total_linked_co2_per_kWh = Var(bounds=(0, None))

        def calculate_total_linked_co2_per_kWh_rule(model):
            return model.total_linked_co2_per_kWh == (sum(model.co2[t] * 1000 for t in model.TIME)
                                                      / (sum(
                        model.demand[t] for t in model.TIME) * energy_per_t / 1000))

        model.calculate_total_linked_co2_per_kWh_con = Constraint(rule=calculate_total_linked_co2_per_kWh_rule)

        if co2_limit:
            def co2_limit_per_kWH_rule(model):
                return model.total_co2_intensity <= co2_limit_per_kWH

            model.co2_limit_per_kWH__con = Constraint(rule=co2_limit_per_kWH_rule)
        else:
            print('stuff')

    if False:

        # Constraints for analysis
        model.total_investment_pem = Var(bounds=(0, None))

        def total_investment_pem_rule(model):
            return model.total_investment_pem == \
                   (model.nominal_cap_pem * capex_electrolysis * supplementory_factor_electrolysis)

        model.total_investment_pem_con = Constraint(rule=total_investment_pem_rule)

        model.total_investment_synthesis = Var(bounds=(0, None))

        def total_investment_synthesis_rule(model):
            if integer_problem:
                return model.total_investment_synthesis == \
                       (model.nominal_cap_co2_scrubbing * model.capex_co2_scrubbing_variable * exchange_pcd_rate_2010 \
                        + sum(model.nominal_cap_rwgs[i] * model.capex_rwgs_variable[i] * exchange_pcd_rate_2010 \
                              + model.nominal_cap_hydrocracker[i] * model.capex_hydrocracke_variabler[
                                  i] * exchange_pcd_rate_2010 \
                              + model.nominal_cap_ftr[i] * model.capex_FTR_variable[i] * exchange_pcd_rate_2003 \
                              for i in model.INTEGER_STEPS)) \
                       * supplementory_factor_synthesis
            else:

                if True:
                    return model.total_investment_synthesis == \
                           (model.nominal_cap_co2_scrubbing * model.capex_co2_scrubbing_variable \
                            * exchange_pcd_rate_2010 \
 \
                            + (model.nominal_cap_rwgs * model.capex_rwgs_variable + model.capex_rwgs_fix) \
                            * exchange_pcd_rate_2010 \
 \
                            + (model.nominal_cap_hydrocracker * model.capex_hydrocracker_variable \
                               + model.capex_hydrocracker_fix) * exchange_pcd_rate_2010 \
 \
                            + (model.nominal_cap_ftr * model.capex_FTR_variable + model.capex_FTR_fix) \
                            * exchange_pcd_rate_2003) \
 \
                           * supplementory_factor_synthesis
                else:
                    return model.total_investment_synthesis == \
                           (model.nominal_cap_rwgs * model.capex_co2_scrubbing_variable \
                            * exchange_pcd_rate_2010) * supplementory_factor_synthesis

        model.total_investment_synthesis_con = Constraint(rule=total_investment_synthesis_rule)

        model.total_investment_storage = Var(bounds=(0, None))

        def total_investment_storage_rule(model):
            return model.total_investment_storage == sum(
                model.nominal_cap_storage[storage] * dict_capex_storage[storage] \
                for storage in model.STORAGE)

        model.total_investment_storage_con = Constraint(rule=total_investment_storage_rule)

        model.total_investment_compressor = Var(bounds=(0, None))

        def total_investment_compressor_rule(model):
            return model.total_investment_compressor == sum(model.nominal_cap_compressor[compressor] \
                                                            * dict_capex_compressor[compressor] \
                                                            for compressor in model.COMPRESSORS)

        model.total_investment_compressor_con = Constraint(rule=total_investment_compressor_rule)

        model.total_investment_pump = Var(bounds=(0, None))

        def total_investment_pump_rule(model):
            return model.total_investment_pump == sum(model.nominal_cap_pump[pump] * dict_capex_pump[pump] \
                                                      for pump in model.PUMPS)

        model.total_investment_pump_con = Constraint(rule=total_investment_pump_rule)

        model.total_investment_generation = Var(bounds=(0, None))

        def total_investment_generation_rule(model):
            return model.total_investment_generation == sum(model.nominal_cap_generation[generator] \
                                                            * dict_capex_generation[generator] \
                                                            for generator in model.GENERATOR)

        model.total_investment_generation_con = Constraint(rule=total_investment_generation_rule)

        model.total_annuity = Var(bounds=(0, None))

        def total_annuity_rule(model):
            return model.total_annuity == (model.total_investment_pem \
                                           + model.total_investment_synthesis \
                                           + model.total_investment_storage \
                                           + model.total_investment_compressor \
                                           + model.total_investment_pump \
                                           + model.total_investment_generation) \
                   * ANF

        model.total_annuity_con = Constraint(rule=total_annuity_rule)

        model.total_maintenance_cost = Var(bounds=(0, None))

        def total_maintenance_cost_rule(model):
            return model.total_maintenance_cost == \
                   model.total_investment_synthesis * maintenance_base_components \
                   + model.total_investment_storage * maintenance_base_components \
                   + (model.total_investment_pem * maintenance_pem
                      + capex_electrolysis * share_stacks * (vlh_pem / lifetime_stacks)) \
                   + model.total_investment_generation * maintenance_base_components

        model.total_maintenance_cost_con = Constraint(rule=total_maintenance_cost_rule)

        model.total_taxes_and_insurance_cost = Var(bounds=(0, None))

        def total_taxes_and_insurance_cost_rule(model):
            return model.total_taxes_and_insurance_cost == (model.total_investment_pem
                                                            + model.total_investment_synthesis
                                                            + model.total_investment_storage
                                                            + model.total_investment_generation) \
                   * taxes_and_insurance

        model.total_taxes_and_insurance_cost_con = Constraint(rule=total_taxes_and_insurance_cost_rule)

        model.total_overhead_costs = Var(bounds=(0, None))

        def total_overhead_costs_rule(model):
            return model.total_overhead_costs == model.total_investment_synthesis * overhead

        model.total_overhead_costs_con = Constraint(rule=total_overhead_costs_rule)

        model.total_working_capital = Var(bounds=(0, None))

        def total_working_capital_rule(model):
            return model.total_working_capital == (model.total_investment_synthesis * working_capital * WACC) \
                   / (1 - working_capital)

        model.total_working_capital_con = Constraint(rule=total_working_capital_rule)

        model.total_electricity_costs = Var(bounds=(0, None))

        def total_electricity_costs_rule(model):
            return model.total_electricity_costs == sum(model.p_grid_pos[t] * model.electricity_price[t]
                                                        / 1000 for t in model.TIME)

        model.total_electricity_costs_con = Constraint(rule=total_electricity_costs_rule)

        model.total_electricity_revenue = Var(bounds=(0, None))

        def total_electricity_revenue_rule(model):
            return model.total_electricity_revenue == sum(model.p_grid_neg[t] * electricity_feedin_tariff
                                                          / 1000 for t in model.TIME)

        model.total_electricity_revenue_con = Constraint(rule=total_electricity_revenue_rule)

        model.total_material_costs = Var(bounds=(0, None))

        def total_material_costs_rule(model):
            return model.total_material_costs == sum(model.water[t] * water_price \
                                                     + model.cooling_water[t] * cooling_water_price \
                                                     + model.waste_water[t] * waste_water_price for t in model.TIME) \
                   + model.total_investment_synthesis * material_costs

        model.total_material_costs_con = Constraint(rule=total_material_costs_rule)

        #####ADDDDJJJJJUUUUUSSSSSSSSSSSST -> Currently depending on demand per hour and not on capacity
        model.total_personal_costs = Var(bounds=(0, None))

        def total_personal_costs_rule(model):
            return model.total_personal_costs == demand_h * personal_cost_per_capacity \
                   + personal_cost_intercept

        model.total_personal_costs_con = Constraint(rule=total_personal_costs_rule)

        model.total_initial_storage_filling_cost = Var(bounds=(0, None))

        def total_initial_storage_filling_cost_rule(model):
            return model.total_initial_storage_filling_cost == sum((dict_soc_initial[storage] - dict_soc_min[storage]) \
                                                                   * model.nominal_cap_storage[storage] \
                                                                   * dict_initial_filling_cost[storage] \
                                                                   for storage in model.STORAGE)

        model.total_initial_storage_filling_con = Constraint(rule=total_initial_storage_filling_cost_rule)

        model.total_annual_costs = Var(bounds=(0, None))

        def total_annual_costs_rule(model):
            return model.total_annual_costs == (model.total_annuity \
                                                + model.total_maintenance_cost \
                                                + model.total_taxes_and_insurance_cost \
                                                + model.total_overhead_costs \
                                                + model.total_working_capital \
                                                + model.total_electricity_costs \
                                                + model.total_material_costs \
                                                + model.total_personal_costs \
                                                + model.total_initial_storage_filling_cost)

        model.total_annual_costs_con = Constraint(rule=total_annual_costs_rule)

        model.total_production_costs_per_liter = Var(bounds=(0, None))

        def total_production_costs_per_liter_rule(model):
            return model.total_production_costs_per_liter == model.total_annual_costs * density_diesel \
                   / (sum(model.demand[t] for t in model.TIME) * 1000)

        model.total_production_costs_per_liter_con = Constraint(rule=total_production_costs_per_liter_rule)

        if integer_problem:
            model.total_penality_cost = Var(bounds=(0, None))

            def total_penality_cost_rule(model):
                return model.total_penality_cost == sum(
                    (model.penality_binary_lower_bound_hydrocracker[i] + model.binary_capacity_higher_0_hydrocracker[
                        i] - 1) * M \
                    + (model.penality_binary_lower_bound_ftr[i] + model.binary_capacity_higher_0_ftr[i] - 1) * M \
                    + (model.penality_binary_lower_bound_rwgs[i] + model.binary_capacity_higher_0_rwgs[i] - 1) * M \
                    for i in model.INTEGER_STEPS if i > 0)

            model.total_penality_cost_con = Constraint(rule=total_penality_cost_rule)

        # ---------------------#
        # Objective function

        def objective_function(model):
            if integer_problem:
                return (model.total_annuity + model.total_maintenance_cost + model.total_taxes_and_insurance_cost
                        + model.total_overhead_costs + model.total_working_capital + model.total_elecitrcity_costs
                        + model.total_material_costs + model.total_initial_storage_filling_cost + model.total_personal_costs
                        + model.total_penality_cost)
            else:
                return (model.total_annuity + model.total_maintenance_cost + model.total_taxes_and_insurance_cost
                        + model.total_overhead_costs + model.total_working_capital + model.total_electricity_costs
                        + model.total_material_costs + model.total_initial_storage_filling_cost + model.total_personal_costs)

        # model.pprint()