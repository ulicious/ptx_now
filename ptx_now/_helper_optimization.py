from pyomo.core import *

import pandas as pd

idx = pd.IndexSlice


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

    return main_conversion_tuples, main_conversion_factor_dict, side_conversion_tuples, side_conversion_factor_dict,\
       main_inputs, unit_dict


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
