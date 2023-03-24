import pandas as pd
import numpy as np


def create_linear_system_of_equations(data):
    # todo: currently, variable operation costs are included in the total costs of components and not indicated
    #  separately

    # Calculate total commodity availability
    for commodity in data.model.COMMODITIES:
        is_input = False
        for input_tuples in data.optimization_problem.input_tuples:
            if input_tuples[1] == commodity:
                is_input = True

        difference = 0
        if commodity in data.model.STORAGES:
            # Due to charging and discharging efficiency, some mass or energy gets 'lost'
            total_in = sum(data.all_variables_dict['mass_energy_storage_in_commodities'][(commodity, cl, t)]
                           * data.model.weightings[cl] for cl in data.model.CLUSTERS for t in data.model.TIME)
            total_out = sum(data.all_variables_dict['mass_energy_storage_out_commodities'][(commodity, cl, t)]
                            * data.model.weightings[cl] for cl in data.model.CLUSTERS for t in data.model.TIME)
            difference = total_in - total_out

        if is_input:
            data.total_availability[commodity] = (
                    data.purchased_commodity[commodity] + data.total_generated_commodity[commodity]
                    + data.conversed_commodity[commodity] - data.emitted_commodity[commodity]
                    - data.sold_commodity[commodity] - difference)
        else:
            data.total_availability[commodity] = data.conversed_commodity[commodity]

    not_used_commodities = []
    for key in [*data.total_availability]:
        if data.total_availability[key] == 0:
            not_used_commodities.append(key)

    # Calculate the total cost of conversion. Important: conversion costs only occur for commodity, where
    # output is main commodity (E.g., electrolysis produces hydrogen and oxygen -> oxygen will not have conversion cost

    for commodity in data.model.COMMODITIES:
        data.storage_costs.update({commodity: 0})
        data.storage_costs_per_unit.update({commodity: 0})
        data.generation_costs.update({commodity: 0})
        data.generation_costs_per_unit.update({commodity: 0})
        data.total_conversion_costs.update({commodity: 0})
        data.total_generation_costs.update({commodity: 0})

    # Get fix costs for each commodity
    for component in data.pm_object.get_final_conversion_components_objects():
        c = component.get_name()

        out_commodity = component.get_main_output()
        data.total_conversion_costs[out_commodity] = (data.total_conversion_costs[out_commodity]
                                                      + data.annualized_investment[c]
                                                      + data.fixed_costs[c]
                                                      + data.variable_costs[c]
                                                      + data.start_up_costs[c])
        data.conversion_component_costs[c] = (data.annualized_investment[c]
                                              + data.fixed_costs[c]
                                              + data.variable_costs[c]
                                              + data.start_up_costs[c])

    # Get annuity of storage units
    for commodity in data.model.STORAGES:

        data.storage_costs[commodity] = (data.annualized_investment[commodity]
                                         + data.fixed_costs[commodity]
                                         + data.variable_costs[commodity])

    # Get annuity of generation units
    for generator in data.model.GENERATORS:
        generated_commodity = data.pm_object.get_component(generator).get_generated_commodity()

        data.total_generation_costs[generated_commodity] = (data.total_generation_costs[generated_commodity]
                                                            + data.annualized_investment[generator]
                                                            + data.fixed_costs[generator]
                                                            + data.variable_costs[generator])
        data.generation_costs[generator] = (data.annualized_investment[generator]
                                            + data.fixed_costs[generator]
                                            + data.variable_costs[generator])

    data.total_generation_costs_per_available_unit = {}
    data.purchase_costs_per_available_unit = {}
    data.storage_costs_per_available_unit = {}
    data.selling_costs_per_available_unit = {}
    for commodity in data.model.COMMODITIES:

        if data.total_availability[commodity] == 0:
            data.total_generation_costs_per_available_unit[commodity] = 0
            data.purchase_costs_per_available_unit[commodity] = 0
            data.storage_costs_per_available_unit[commodity] = 0
            data.selling_costs_per_available_unit[commodity] = 0

        else:

            data.total_generation_costs_per_available_unit[commodity] = data.total_generation_costs[commodity] / data.total_availability[commodity]
            data.purchase_costs_per_available_unit[commodity] = data.purchase_costs[commodity] / data.total_availability[commodity]
            data.storage_costs_per_available_unit[commodity] = data.storage_costs[commodity] / data.total_availability[commodity]
            data.selling_costs_per_available_unit[commodity] = data.selling_costs[commodity] / data.total_availability[commodity]

    # Second: Next to intrinsic costs, conversion costs exist.
    # Each commodity, which is the main output of a conversion unit,
    # will be matched with the costs this conversion unit produces
    conversion_costs_per_conversed_unit = {}
    for component in data.pm_object.get_final_conversion_components_objects():
        component_name = component.get_name()
        main_output = component.get_main_output()

        # Components without capacity are not considered, as they don't converse anything
        if data.all_variables_dict['nominal_cap'][component_name] == 0:
            continue

        # Calculate the conversion costs per conversed unit
        conversion_costs_per_conversed_unit[component_name] = (data.conversion_component_costs[component_name]
                                                               / data.total_availability[main_output])

    columns_index = [*data.pm_object.get_all_commodities().keys()]
    for s in data.pm_object.get_final_conversion_components_objects():
        component_name = s.get_name()
        if data.all_variables_dict['nominal_cap'][component_name] > 0:
            columns_index.append(component_name)

    coefficients_df = pd.DataFrame(index=columns_index, columns=columns_index)
    coefficients_df.fillna(value=0, inplace=True)

    main_outputs = []
    main_output_coefficients = {}
    for component in data.pm_object.get_final_conversion_components_objects():
        main_output = component.get_main_output()
        main_outputs.append(main_output)
        main_output_coefficients[component.get_main_output()] = component.get_outputs()[main_output]

    all_inputs = []
    final_commodity = None
    for component in data.pm_object.get_final_conversion_components_objects():
        component_name = component.get_name()
        inputs = component.get_inputs()
        outputs = component.get_outputs()
        main_output = component.get_main_output()

        if data.all_variables_dict['nominal_cap'][component_name] == 0:
            continue

        hot_standby_commodity = ''
        hot_standby_demand = 0
        if component.get_hot_standby_ability():
            hot_standby_commodity = [*component.get_hot_standby_demand().keys()][0]
            hot_standby_demand = (data.hot_standby_demand[component_name][hot_standby_commodity]
                                  / data.conversed_commodity_per_component[component_name][main_output])

        # First of all, associate inputs to components
        # If hot standby possible: input + hot standby demand -> hot standby demand prt conversed unit
        # If same commodity in input and output: input - output
        # If neither: just input

        # important: component might only produce a share of the commodity (rest is bought, output of other components
        # Therefore, share has to be adjusted

        for i in [*inputs.keys()]:  # commodity in input

            if data.conversed_commodity_per_component[component_name][main_output] > 0:
                ratio_conversed_to_total = data.conversed_commodity_per_component[component_name][main_output] \
                    / data.total_availability[main_output]

            else:
                ratio_conversed_to_total = 1

            if i not in [*outputs.keys()]:  # commodity not in output
                if component.get_hot_standby_ability():  # component has hot standby ability
                    if i != hot_standby_commodity:
                        coefficients_df.loc[i, component_name] = inputs[i] * ratio_conversed_to_total
                    else:
                        coefficients_df.loc[i, component_name] = inputs[i] * ratio_conversed_to_total + hot_standby_demand
                else:  # component has no hot standby ability
                    coefficients_df.loc[i, component_name] = inputs[i] * ratio_conversed_to_total
            else:  # commodity in output
                if i in main_outputs:
                    if component.get_hot_standby_ability():  # component has hot standby ability
                        if i != hot_standby_commodity:  # hot standby commodity is not commodity
                            coefficients_df.loc[i, component_name] = (inputs[i] - outputs[i]) * ratio_conversed_to_total
                        else:
                            coefficients_df.loc[i, component_name] = (inputs[i] - outputs[i]) * ratio_conversed_to_total \
                                                                     + hot_standby_demand
                    else:  # component has no hot standby ability
                        coefficients_df.loc[i, component_name] = (inputs[i] - outputs[i]) * ratio_conversed_to_total

            all_inputs.append(i)

        for o in [*outputs.keys()]:
            if (o not in [*inputs.keys()]) & (o != main_output):
                coefficients_df.loc[o, component_name] = -outputs[o]

            if data.pm_object.get_commodity(o).is_demanded():
                final_commodity = o

        coefficients_df.loc[component_name, component_name] = -1

    if final_commodity is not None:
        # The commodity is produced by one of the conversion units.

        # Matching of costs, which do not influence demanded commodity directly (via inputs)
        # Costs of side commodities with no demand (e.g., flares to burn excess gases)
        # will be added to final commodity
        for component in data.pm_object.get_final_conversion_components_objects():
            main_output = data.pm_object.get_commodity(component.get_main_output())
            main_output_name = main_output.get_name()

            component_name = component.get_name()
            if data.all_variables_dict['nominal_cap'][component_name] == 0:
                continue

            if main_output_name not in all_inputs:  # Check if main output is input of other conversion
                if not main_output.is_demanded():  # Check if main output is demanded
                    coefficients_df.loc[component_name, final_commodity] = 1

        # Each commodity, if main output, has its intrinsic costs and the costs of the conversion component
        for commodity in data.model.COMMODITIES:
            for component in data.pm_object.get_final_conversion_components_objects():
                component_name = component.get_name()

                if data.all_variables_dict['nominal_cap'][component_name] == 0:
                    if commodity in main_outputs:
                        coefficients_df.loc[commodity, commodity] = -1
                    continue

                main_output = component.get_main_output()
                outputs = component.get_outputs()
                if commodity == main_output:
                    # ratio is when several components have same output
                    ratio_different_components = (data.conversed_commodity_per_component[component_name][commodity]
                             / data.conversed_commodity[commodity])
                    coefficients_df.loc[component_name, commodity] = 1 / outputs[commodity] * ratio_different_components

                    coefficients_df.loc[commodity, commodity] = -1

            if commodity not in main_outputs:
                coefficients_df.loc[commodity, commodity] = -1

        old_columns = coefficients_df.columns.tolist()
        new_columns = old_columns.copy()
        for commodity in data.model.COMMODITIES:
            new_columns.append(commodity + ' Generation')
            new_columns.append(commodity + ' Purchase')
            new_columns.append(commodity + ' Selling')
            new_columns.append(commodity + ' Storage')

        for i in new_columns:
            for o in new_columns:
                if (i in old_columns) & (o in old_columns):
                    continue

                elif i == o:
                    coefficients_df.loc[i, o] = -1

                elif (o in i) & (o != i):
                    coefficients_df.loc[i, o] = 1

                else:
                    coefficients_df.loc[i, o] = 0

        if False:
            coefficients_df.to_excel(data.new_result_folder + '/equations.xlsx')

        # Right hand side (constants)
        coefficients_dict = {}
        commodity_equations_constant = {}
        for column in coefficients_df.columns:
            coefficients_dict.update({column: coefficients_df[column].tolist()})
            if column in data.model.COMMODITIES:
                commodity_equations_constant.update({column: 0})

            if column in data.model.CONVERSION_COMPONENTS:
                if data.all_variables_dict['nominal_cap'][column] == 0:
                    continue

                component = data.pm_object.get_component(column)
                main_output = component.get_main_output()
                commodity_equations_constant.update({column: (-conversion_costs_per_conversed_unit[column]
                                                              * main_output_coefficients[main_output])})

            if 'Generation' in column: # todo: wird aktuell getestet - Das funktioniert so nicht, wenn eine Komponente z.B. FT Crude heißt (Leerzeichen)
                commodity_equations_constant.update({column: -data.total_generation_costs_per_available_unit[column.split(' Generation')[0]]})
            if 'Purchase' in column:
                commodity_equations_constant.update({column: -data.purchase_costs_per_available_unit[column.split(' Purchase')[0]]})
            if 'Selling' in column:
                commodity_equations_constant.update({column: -data.selling_costs_per_available_unit[column.split(' Selling')[0]]})
            if 'Storage' in column:
                commodity_equations_constant.update({column: -data.storage_costs_per_available_unit[column.split(' Storage')[0]]})

        if False:
            pd.DataFrame.from_dict(commodity_equations_constant, orient='index').to_excel(
                data.new_result_folder + '/commodity_equations_constant.xlsx')

        values_equations = coefficients_dict.values()
        A = np.array(list(values_equations))
        values_constant = commodity_equations_constant.values()
        B = np.array(list(values_constant))
        X = np.linalg.solve(A, B)

        for i, c in enumerate(columns_index):
            data.production_cost_commodity_per_unit.update({c: X[i]})

        commodities_and_costs = pd.DataFrame()
        dataframe_dict = {}

        for column in columns_index:

            if column in data.model.COMMODITIES:
                commodity = column
                commodity_object = data.pm_object.get_commodity(commodity)
                commodities_and_costs.loc[commodity, 'unit'] = commodity_object.get_unit()
                commodities_and_costs.loc[commodity, 'MWh per unit'] = commodity_object.get_energy_content()

                commodities_and_costs.loc[commodity, 'Available Commodity'] = data.available_commodity[commodity]
                commodities_and_costs.loc[commodity, 'Emitted Commodity'] = data.emitted_commodity[commodity]
                commodities_and_costs.loc[commodity, 'Purchased Commodity'] = data.purchased_commodity[commodity]
                commodities_and_costs.loc[commodity, 'Sold Commodity'] = data.sold_commodity[commodity]
                commodities_and_costs.loc[commodity, 'Generated Commodity'] = data.total_generated_commodity[commodity]
                commodities_and_costs.loc[commodity, 'Stored Commodity'] = data.stored_commodity[commodity]
                commodities_and_costs.loc[commodity, 'Conversed Commodity'] = data.conversed_commodity[commodity]
                commodities_and_costs.loc[commodity, 'Total Commodity'] = data.total_availability[commodity]

                commodities_and_costs.loc[commodity, 'Total Purchase Costs'] = data.purchase_costs[commodity]
                if data.purchased_commodity[commodity] > 0:
                    purchase_costs = data.purchase_costs[commodity] / data.purchased_commodity[commodity]
                    commodities_and_costs.loc[commodity, 'Average Purchase Costs per purchased Unit'] = purchase_costs
                else:
                    commodities_and_costs.loc[commodity, 'Average Purchase Costs per purchased Unit'] = 0

                commodities_and_costs.loc[commodity, 'Total Selling Revenue/Disposal Costs'] = data.selling_costs[
                    commodity]
                if data.sold_commodity[commodity] > 0:
                    revenue = data.selling_costs[commodity] / data.sold_commodity[commodity]
                    commodities_and_costs.loc[
                        commodity, 'Average Selling Revenue / Disposal Costs per sold/disposed Unit'] \
                        = revenue
                else:
                    commodities_and_costs.loc[
                        commodity, 'Average Selling Revenue / Disposal Costs per sold/disposed Unit'] \
                        = 0

                data.total_variable_costs[commodity] = data.purchase_costs[commodity] - data.selling_costs[commodity]  # todo: + oder -?
                commodities_and_costs.loc[commodity, 'Total Variable Costs'] = data.total_variable_costs[commodity]

                commodities_and_costs.loc[commodity, 'Total Generation Fix Costs'] = data.total_generation_costs[
                    commodity]
                if data.total_generated_commodity[commodity] > 0:
                    commodities_and_costs.loc[commodity, 'Costs per used unit'] \
                        = data.total_generation_costs[commodity] / (data.total_generated_commodity[commodity]
                                                                    - data.emitted_commodity[commodity])
                else:
                    commodities_and_costs.loc[commodity, 'Costs per used unit'] = 0

                commodities_and_costs.loc[commodity, 'Total Storage Fix Costs'] = data.storage_costs[commodity]
                if data.stored_commodity[commodity] > 0:
                    stored_costs = data.storage_costs[commodity] / data.stored_commodity[commodity]
                    commodities_and_costs.loc[commodity, 'Total Storage Fix Costs per stored Unit'] = stored_costs
                else:
                    commodities_and_costs.loc[commodity, 'Total Storage Fix Costs per stored Unit'] = 0

                commodities_and_costs.loc[commodity, 'Total Conversion Fix Costs'] = data.total_conversion_costs[
                    commodity]
                if data.conversed_commodity[commodity] > 0:
                    conversion_costs = data.total_conversion_costs[commodity] / data.conversed_commodity[commodity]
                    commodities_and_costs.loc[
                        commodity, 'Total Conversion Fix Costs per conversed Unit'] = conversion_costs
                else:
                    commodities_and_costs.loc[commodity, 'Total Conversion Fix Costs per conversed Unit'] = 0

                data.total_fix_costs[commodity] \
                    = (data.total_conversion_costs[commodity] + data.storage_costs[commodity]
                       + data.total_generation_costs[commodity])
                commodities_and_costs.loc[commodity, 'Total Fix Costs'] = data.total_fix_costs[commodity]

                data.total_costs[commodity] = data.total_variable_costs[commodity] + data.total_fix_costs[commodity]
                commodities_and_costs.loc[commodity, 'Total Costs'] = data.total_costs[commodity]

                if data.total_availability[commodity] > 0:
                    commodities_and_costs.loc[commodity, 'Total Costs per Unit'] \
                        = data.total_costs[commodity] / data.total_availability[commodity]
                else:
                    commodities_and_costs.loc[commodity, 'Total Costs per Unit'] = 0

                if (data.total_generation_costs_per_available_unit[commodity]
                    + data.storage_costs_per_available_unit[commodity]
                    + data.purchase_costs_per_available_unit[commodity]
                    + data.selling_costs_per_available_unit[commodity]) >= 0:
                    commodities_and_costs.loc[commodity, 'Production Costs per Unit'] \
                        = data.production_cost_commodity_per_unit[commodity]
                else:
                    commodities_and_costs.loc[commodity, 'Production Costs per Unit'] \
                        = - data.production_cost_commodity_per_unit[commodity]

                commodities_and_costs.to_excel(data.new_result_folder + '/4_commodities.xlsx')
                data.commodities_and_costs = commodities_and_costs

            else:
                component_name = column
                component = data.pm_object.get_component(component_name)

                main_output = component.get_main_output()

                commodity_object = data.pm_object.get_commodity(main_output)
                unit = commodity_object.get_unit()

                index = component_name + ' [' + unit + ' ' + main_output + ']'

                component_list = [index, index, index]
                kpis = ['Coefficient', 'Cost per Unit', 'Total Costs']

                arrays = [component_list, kpis]
                m_index = pd.MultiIndex.from_arrays(arrays, names=('Component', 'KPI'))
                components_and_costs = pd.DataFrame(index=m_index)

                conv_costs = round(conversion_costs_per_conversed_unit[component_name], 3)
                total_costs = conv_costs

                components_and_costs.loc[(index, 'Coefficient'), 'Intrinsic'] = 1
                components_and_costs.loc[(index, 'Cost per Unit'), 'Intrinsic'] = conv_costs
                components_and_costs.loc[(index, 'Total Costs'), 'Intrinsic'] = conv_costs

                inputs = component.get_inputs()
                outputs = component.get_outputs()
                main_output_coefficient = outputs[main_output]
                processed_outputs = []
                for i in [*inputs.keys()]:
                    input_name = i

                    in_coeff = round(inputs[i] / main_output_coefficient, 3)
                    prod_costs = round(data.production_cost_commodity_per_unit[i], 3)
                    input_costs = round(data.production_cost_commodity_per_unit[i] * inputs[i]
                                        / main_output_coefficient, 3)

                    input_name += ' (Input)'

                    components_and_costs.loc[(index, 'Coefficient'), input_name] = in_coeff
                    components_and_costs.loc[(index, 'Cost per Unit'), input_name] = prod_costs
                    components_and_costs.loc[(index, 'Total Costs'), input_name] = input_costs

                    total_costs += input_costs

                    if i in [*outputs.keys()]:
                        # Handle output earlier s.t. its close to input of same commodity in excel file
                        output_name = i
                        out_coeff = round(outputs[i] / main_output_coefficient, 3)

                        # Three cases occur
                        # 1: The output commodity has a positive intrinsic value because it can be used again -> negative
                        # 2: The output can be sold with revenue -> negative
                        # 3: The output produces costs because the commodity needs to be disposed, for example -> positive

                        if data.selling_costs[i] > 0:  # Case 3
                            prod_costs = round(data.production_cost_commodity_per_unit[i], 3)
                            output_costs = round(data.production_cost_commodity_per_unit[i] * outputs[i]
                                                 / main_output_coefficient, 3)
                        else:  # Case 1 & 2
                            prod_costs = - round(data.production_cost_commodity_per_unit[i], 3)
                            output_costs = - round(data.production_cost_commodity_per_unit[i] * outputs[i]
                                                   / main_output_coefficient, 3)

                        output_name += ' (Output)'

                        components_and_costs.loc[(index, 'Coefficient'), output_name] = out_coeff
                        components_and_costs.loc[(index, 'Cost per Unit'), output_name] = prod_costs
                        components_and_costs.loc[(index, 'Total Costs'), output_name] = output_costs

                        total_costs += output_costs

                        processed_outputs.append(i)

                for o in [*outputs.keys()]:
                    if o in processed_outputs:
                        continue

                    output_name = o

                    if o != component.get_main_output():
                        out_coeff = round(outputs[o] / main_output_coefficient, 3)

                        # Three cases occur
                        # 1: The output commodity has a positive intrinsic value because it can be used again -> negative
                        # 2: The output can be sold with revenue -> negative
                        # 3: The output produces costs because the commodity needs to be disposed, for example -> positive

                        if data.selling_costs[o] > 0:  # Case 3: Disposal costs exist
                            prod_costs = round(data.production_cost_commodity_per_unit[o], 3)
                            output_costs = round(data.production_cost_commodity_per_unit[o] * outputs[o]
                                                 / main_output_coefficient, 3)
                        else:  # Case 1 & 2
                            prod_costs = - round(data.production_cost_commodity_per_unit[o], 3)
                            output_costs = - round(data.production_cost_commodity_per_unit[o] * outputs[o]
                                                   / main_output_coefficient, 3)

                        output_name += ' (Output)'

                        components_and_costs.loc[(index, 'Coefficient'), output_name] = out_coeff
                        components_and_costs.loc[(index, 'Cost per Unit'), output_name] = prod_costs
                        components_and_costs.loc[(index, 'Total Costs'), output_name] = output_costs

                        total_costs += output_costs

                # Further costs, which are not yet in commodity, need to be associated
                # In case that several components have same main output, costs are matched regarding share of production
                ratio = (data.conversed_commodity_per_component[component_name][main_output]
                         / data.conversed_commodity[main_output])

                if main_output in data.model.STORAGES:
                    column_name = 'Storage Costs'
                    components_and_costs.loc[(index, 'Coefficient'), column_name] = ratio
                    prod_costs = (data.storage_costs[main_output] / data.conversed_commodity[main_output])
                    components_and_costs.loc[(index, 'Cost per Unit'), column_name] = prod_costs
                    components_and_costs.loc[(index, 'Total Costs'), column_name] = prod_costs * ratio

                    total_costs += prod_costs * ratio

                if commodity_object.is_demanded():
                    for commodity in data.model.COMMODITIES:
                        if (commodity not in all_inputs) & (commodity in main_outputs) & (commodity != main_output):

                            column_name = commodity + ' (Associated Costs)'
                            components_and_costs.loc[(index, 'Coefficient'), column_name] = ratio
                            prod_costs = (data.production_cost_commodity_per_unit[commodity]
                                          * data.conversed_commodity[commodity]
                                          / data.conversed_commodity[main_output])
                            components_and_costs.loc[(index, 'Cost per Unit'), column_name] = prod_costs
                            components_and_costs.loc[(index, 'Total Costs'), column_name] = prod_costs * ratio

                            total_costs += prod_costs * ratio

                prod_costs = round(total_costs, 3)
                components_and_costs.loc[(index, 'Coefficient'), 'Final'] = ''
                components_and_costs.loc[(index, 'Cost per Unit'), 'Final'] = ''
                components_and_costs.loc[(index, 'Total Costs'), 'Final'] = prod_costs

                dataframe_dict[component_name] = components_and_costs

            # Save dataframes in multi-sheet excel file
            if False:
                with pd.ExcelWriter(data.new_result_folder + '/main_output_costs.xlsx', engine="xlsxwriter") as writer:
                    for df in [*dataframe_dict.keys()]:
                        sheet_name = df.replace("Parallel Unit", "PU")
                        dataframe_dict[df].to_excel(writer, sheet_name)
                    writer.save()