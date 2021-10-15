import pandas as pd
from pyomo.core import *
import matplotlib.pyplot as plt
import numpy as np
import os

import plotly.graph_objects as go
from datetime import datetime


class Result:

    def extracting_data(self):

        for v in self.instance.component_objects(Var, active=True):

            variable_dict = v.extract_values()
            if not bool(variable_dict):
                continue

            list_value = []

            if len([*variable_dict]) == 0:
                number_keys = 0
            elif type([*variable_dict][0]) == str:
                number_keys = 1
            elif [*variable_dict][0] is None:
                number_keys = 0
            else:
                number_keys = len([*variable_dict][0])

            if number_keys == 0:
                value_list = list(variable_dict.values())
                for item in range(len(value_list)):
                    list_value = value_list[item]
                self.all_variables_dict.update({str(v): list_value})
                self.variable_zero_index.append(str(v))

                if str(v) == 'test_b':
                    print(list_value)

                if str(v) == 'power_penalty':
                    print(list_value)

            elif number_keys == 1:
                self.all_variables_dict.update({str(v): variable_dict})
                self.variable_one_index.append(str(v))
            elif number_keys == 2:

                variable_list = []
                stream_dict = {}
                stream = ''
                first = True
                for key in [*variable_dict]:

                    if first:
                        stream = key[0]
                        first = False

                    if stream != key[0]:

                        stream_dict.update({stream: variable_list})
                        stream = key[0]
                        variable_list = []

                    variable_list.append(variable_dict[key])

                stream_dict.update({stream: variable_list})

                self.all_variables_dict.update({str(v): stream_dict})
                self.variable_two_index.append(str(v))

            elif number_keys == 3:

                variable_list = []
                component_dict = {}
                stream_dict = {}
                stream = ''
                c = ''
                first = True
                for key in [*variable_dict]:

                    if first:
                        stream = key[1]
                        c = key[0]
                        first = False

                    if (stream != key[1]) & (c == key[0]):
                        stream_dict.update({stream: variable_list})
                        stream = key[1]
                        c = key[0]
                        variable_list = []
                    elif c != key[0]:
                        stream_dict.update({stream: variable_list})
                        component_dict.update({c: stream_dict})
                        stream_dict = {}
                        stream = key[1]
                        c = key[0]
                        variable_list = []

                    variable_list.append(variable_dict[key])

                stream_dict.update({stream: variable_list})
                component_dict.update({c: stream_dict})

                self.all_variables_dict.update({str(v): component_dict})
                self.variable_three_index.append(str(v))

    def process_variables(self):

        """ Allocates costs to streams """

        # Calculate the total availability of each stream (purchase, from conversion, available)
        variable_names = ['mass_energy_purchase_stream', 'mass_energy_available',
                          'mass_energy_component_out_streams', 'mass_energy_total_generation',
                          'mass_energy_storage_in_streams', 'mass_energy_sell_stream', 'mass_energy_emitted',
                          'nominal_cap', 'mass_energy_generation', 'mass_energy_hot_standby_demand']

        for stream in self.model.ME_STREAMS:
            self.purchased_stream.update({stream: 0})
            self.purchase_costs.update({stream: 0})
            self.sold_stream.update({stream: 0})
            self.selling_costs.update({stream: 0})
            self.generated_stream.update({stream: 0})
            self.available_stream.update({stream: 0})
            self.emitted_stream.update({stream: 0})
            self.stored_stream.update({stream: 0})
            self.conversed_stream.update({stream: 0})
            self.total_generated_stream.update({stream: 0})

        for variable_name in [*self.all_variables_dict]:

            if variable_name in self.variable_two_index:

                if variable_name in variable_names:
                    for stream in [*self.all_variables_dict[variable_name]]:

                        list_values = self.all_variables_dict[variable_name][stream]
                        sum_values = sum(self.all_variables_dict[variable_name][stream])

                        if not self.pm_object.get_uses_representative_weeks():

                            if variable_name == "mass_energy_available":
                                self.available_stream[stream] = (self.available_stream[stream] + sum_values)

                            if variable_name == 'mass_energy_emitted':
                                if stream in self.model.EMITTED_STREAMS:
                                    self.emitted_stream[stream] = (self.emitted_stream[stream] + sum_values)

                            if variable_name == 'mass_energy_purchase_stream':  # Calculate costs of purchase
                                if stream in self.model.PURCHASABLE_STREAMS:
                                    self.purchased_stream[stream] = (self.purchased_stream[stream] + sum_values)
                                    self.purchase_costs[stream] = (self.purchase_costs[stream] +
                                                                   sum(list_values[t]
                                                                       * self.model.purchase_price[stream, t]
                                                                       for t in self.model.TIME))

                            if variable_name == 'mass_energy_sell_stream':  # Calculate costs of purchase
                                if stream in self.model.SALEABLE_STREAMS:
                                    self.sold_stream[stream] = (self.sold_stream[stream] + sum_values)
                                    self.selling_costs[stream] = (self.selling_costs[stream]
                                                                  + sum(list_values[t]
                                                                        * self.model.selling_price[stream, t] * (-1)
                                                                        for t in self.model.TIME))

                            if variable_name == 'mass_energy_total_generation':
                                if stream in self.model.GENERATED_STREAMS:
                                    self.total_generated_stream[stream] = (self.total_generated_stream[stream]
                                                                           + sum_values)

                            if variable_name == 'mass_energy_storage_in_streams':
                                if stream in self.model.STORAGES:
                                    self.stored_stream[stream] = (self.stored_stream[stream] + sum_values)

                        else:

                            if variable_name == "mass_energy_available":
                                self.available_stream[stream] = (self.available_stream[stream]
                                                                 + sum(list_values[t] * self.model.weightings[t]
                                                                       for t in self.model.TIME))

                            if variable_name == 'mass_energy_emitted':
                                if stream in self.model.EMITTED_STREAMS:
                                    self.emitted_stream[stream] = (self.emitted_stream[stream] +
                                                                   sum(list_values[t] * self.model.weightings[t]
                                                                       for t in self.model.TIME))

                            if variable_name == 'mass_energy_purchase_stream':  # Calculate costs of purchase
                                if stream in self.model.PURCHASABLE_STREAMS:
                                    self.purchased_stream[stream] = (self.purchased_stream[stream]
                                                                     + sum(list_values[t] * self.model.weightings[t]
                                                                           for t in self.model.TIME))
                                    self.purchase_costs[stream] = (self.purchase_costs[stream]
                                                                   + sum(list_values[t] * self.model.weightings[t]
                                                                         * self.model.purchase_price[stream, t]
                                                                         for t in self.model.TIME))

                            if variable_name == 'mass_energy_sell_stream':  # Calculate costs of purchase
                                if stream in self.model.SALEABLE_STREAMS:
                                    self.sold_stream[stream] = (self.sold_stream[stream]
                                                                + sum(list_values[t] * self.model.weightings[t]
                                                                      for t in self.model.TIME))
                                    self.selling_costs[stream] = (self.selling_costs[stream]
                                                                  + sum(list_values[t] * self.model.weightings[t]
                                                                        * self.model.selling_price[stream, t] * (-1)
                                                                        for t in self.model.TIME))

                            if variable_name == 'mass_energy_total_generation':
                                if stream in self.model.GENERATED_STREAMS:
                                    self.total_generated_stream[stream] = (self.total_generated_stream[stream]
                                                                           + sum(list_values[t]
                                                                                 * self.model.weightings[t]
                                                                                 for t in self.model.TIME))

                            if variable_name == 'mass_energy_storage_in_streams':
                                if stream in self.model.STORAGES:
                                    self.stored_stream[stream] = (self.stored_stream[stream]
                                                                  + sum(list_values[t] * self.model.weightings[t]
                                                                        for t in self.model.TIME))

            elif variable_name in self.variable_three_index:

                if variable_name in variable_names:

                    for c in [*self.all_variables_dict[variable_name]]:
                        component_object = self.pm_object.get_component(c)

                        conversion = False
                        for i in self.pm_object.get_specific_components('final', 'conversion'):
                            if c == i.get_name():
                                conversion = True
                                if variable_name == 'mass_energy_component_out_streams':
                                    self.conversed_stream_per_component[c] = {}
                                elif variable_name == 'mass_energy_hot_standby_demand':
                                    self.hot_standby_demand[c] = {}

                        for stream in [*self.all_variables_dict[variable_name][c]]:

                            list_values = self.all_variables_dict[variable_name][c][stream]
                            sum_values = sum(self.all_variables_dict[variable_name][c][stream])

                            ratio = 1
                            if conversion:
                                inputs = component_object.get_inputs()
                                outputs = component_object.get_outputs()

                                # Case stream is conversed but not fully
                                if (stream in [*inputs.keys()]) & (stream in [*outputs.keys()]):
                                    sum_values = sum_values * outputs[stream] / inputs[stream]
                                    ratio = sum_values * outputs[stream] / inputs[stream]

                            if not self.pm_object.get_uses_representative_weeks():

                                if variable_name == 'mass_energy_component_out_streams':
                                    if stream == component_object.get_main_output():
                                        self.conversed_stream[stream] = self.conversed_stream[stream] + sum_values
                                        self.conversed_stream_per_component[c][stream] = sum_values
                                    else:
                                        self.conversed_stream[stream] = self.conversed_stream[stream] + 0
                                        self.conversed_stream_per_component[c][stream] = 0

                                if variable_name == 'mass_energy_hot_standby_demand':
                                    if stream in [*component_object.get_hot_standby_demand().keys()]:
                                        self.hot_standby_demand[c][stream] = sum_values

                                if variable_name == 'mass_energy_generation':
                                    if stream in self.model.GENERATED_STREAMS:
                                        self.generated_stream[c] = sum_values

                            else:
                                if variable_name == 'mass_energy_component_out_streams':
                                    if stream == component_object.get_main_output():
                                        self.conversed_stream[stream] = (self.conversed_stream[stream]
                                                                         + sum(list_values[t] * self.model.weightings[t]
                                                                               * ratio for t in self.model.TIME))
                                        self.conversed_stream_per_component[c][stream] = sum(list_values[t]
                                                                                             * self.model.weightings[t]
                                                                                             * ratio
                                                                                             for t in self.model.TIME)
                                    else:
                                        self.conversed_stream[stream] = self.conversed_stream[stream] + 0
                                        self.conversed_stream_per_component[c][stream] = 0

                                if variable_name == 'mass_energy_hot_standby_demand':
                                    if stream in [*component_object.get_hot_standby_demand().keys()]:
                                        self.hot_standby_demand[c][stream] = sum(list_values[t]
                                                                                 * self.model.weightings[t] * ratio
                                                                                 for t in self.model.TIME)

                                if variable_name == 'mass_energy_generation':
                                    if stream in self.model.GENERATED_STREAMS:
                                        self.generated_stream[c] = sum(list_values[t] * self.model.weightings[t] * ratio
                                                                       for t in self.model.TIME)

    def analyze_streams(self):

        # Calculate total stream availability
        for stream in self.model.ME_STREAMS:
            is_input = False
            for input_tuples in self.optimization_problem.input_tuples:
                if input_tuples[1] == stream:
                    is_input = True

            if is_input:
                self.total_availability[stream] = (self.purchased_stream[stream] + self.total_generated_stream[stream]
                                                   + self.conversed_stream[stream] - self.emitted_stream[stream]
                                                   - self.sold_stream[stream])
            else:
                self.total_availability[stream] = self.conversed_stream[stream]

        not_used_streams = []
        for key in [*self.total_availability]:
            if self.total_availability[key] == 0:
                not_used_streams.append(key)

        # Calculate the total cost of conversion. Important: conversion costs only occur for stream, where
        # output is main stream (E.g., electrolysis produces hydrogen and oxygen -> oxygen will not have conversion cost

        for stream in self.model.ME_STREAMS:
            self.storage_costs.update({stream: 0})
            self.storage_costs_per_unit.update({stream: 0})
            self.generation_costs.update({stream: 0})
            self.generation_costs_per_unit.update({stream: 0})
            self.maintenance.update({stream: 0})

            self.total_conversion_costs.update({stream: 0})
            self.total_generation_costs.update({stream: 0})

        self.conversion_costs_component = {}

        # Get fix costs for each stream
        for component in self.pm_object.get_specific_components('final', 'conversion'):
            c = component.get_name()
            out_stream = component.get_main_output()
            self.total_conversion_costs[out_stream] = (self.total_conversion_costs[out_stream]
                                                       + self.all_variables_dict['annuity'][c]
                                                       + self.all_variables_dict['maintenance_costs'][c]
                                                       + self.all_variables_dict['taxes_and_insurance_costs'][c]
                                                       + self.all_variables_dict['personnel_costs'][c]
                                                       + self.all_variables_dict['overhead_costs'][c]
                                                       + self.all_variables_dict['working_capital_costs'][c])
            self.conversion_costs_component[c] = (self.all_variables_dict['annuity'][c]
                                                  + self.all_variables_dict['maintenance_costs'][c]
                                                  + self.all_variables_dict['taxes_and_insurance_costs'][c]
                                                  + self.all_variables_dict['personnel_costs'][c]
                                                  + self.all_variables_dict['overhead_costs'][c]
                                                  + self.all_variables_dict['working_capital_costs'][c])

        # Get annuity of storage units
        for stream in self.model.STORAGES:
            self.storage_costs[stream] = (self.all_variables_dict['annuity'][stream]
                                          + self.all_variables_dict['maintenance_costs'][stream]
                                          + self.all_variables_dict['taxes_and_insurance_costs'][stream]
                                          + self.all_variables_dict['personnel_costs'][stream]
                                          + self.all_variables_dict['overhead_costs'][stream]
                                          + self.all_variables_dict['working_capital_costs'][stream])

        # Get annuity of generation units
        for generator in self.model.GENERATORS:
            generated_stream = self.pm_object.get_component(generator).get_generated_stream()
            self.total_generation_costs[generated_stream] = (self.total_generation_costs[generated_stream]
                                                       + self.all_variables_dict['annuity'][generator]
                                                       + self.all_variables_dict['maintenance_costs'][generator]
                                                       + self.all_variables_dict['taxes_and_insurance_costs'][generator]
                                                       + self.all_variables_dict['personnel_costs'][generator]
                                                       + self.all_variables_dict['overhead_costs'][generator]
                                                       + self.all_variables_dict['working_capital_costs'][generator])
            self.generation_costs[generator] = (self.all_variables_dict['annuity'][generator]
                                                + self.all_variables_dict['maintenance_costs'][generator]
                                                + self.all_variables_dict['taxes_and_insurance_costs'][generator]
                                                + self.all_variables_dict['personnel_costs'][generator]
                                                + self.all_variables_dict['overhead_costs'][generator]
                                                + self.all_variables_dict['working_capital_costs'][generator])

        # COST DISTRIBUTION: Distribute the costs to each stream
        # First: The intrinsic costs of each stream.
        # Intrinsic costs include generation, storage, purchase and selling costs
        intrinsic_costs = {}
        intrinsic_costs_per_available_unit = {}
        for stream in self.model.ME_STREAMS:
            intrinsic_costs[stream] = round(self.total_generation_costs[stream]
                                            + self.purchase_costs[stream]
                                            + self.storage_costs[stream]
                                            + self.selling_costs[stream], 5)

            # If intrinsic costs exist, distribute them on the total stream available
            # Available stream = Generated, Purchased, Conversed minus Sold, Emitted
            if intrinsic_costs[stream] >= 0:
                if self.total_availability[stream] == 0:
                    intrinsic_costs_per_available_unit[stream] = 0
                else:
                    intrinsic_costs_per_available_unit[stream] = (intrinsic_costs[stream]
                                                                  / self.total_availability[stream])
            elif intrinsic_costs[stream] < 0:
                # If intrinsic costs are negative (due to selling of side products),
                # the total costs are distributed to the total stream sold
                intrinsic_costs_per_available_unit[stream] = (-intrinsic_costs[stream]
                                                              / self.sold_stream[stream])

        pd.DataFrame.from_dict(intrinsic_costs, orient='index').to_excel(
            self.new_result_folder + '/intrinsic_costs.xlsx')
        pd.DataFrame.from_dict(intrinsic_costs_per_available_unit, orient='index').to_excel(
            self.new_result_folder + '/intrinsic_costs_per_available_unit.xlsx')

        # Second: Next to intrinsic costs, conversion costs exist.
        # Each stream, which is the main output of a conversion unit,
        # will be matched with the costs this conversion unit produces
        conversion_costs_per_conversed_unit = {}
        total_intrinsic_costs_per_available_unit = {}
        for component in self.pm_object.get_specific_components('final', 'conversion'):
            component_name = component.get_name()
            main_output = component.get_main_output()

            # Components without capacity are not considered, as they dont converse anything
            if self.all_variables_dict['nominal_cap'][component_name] == 0:
                continue

            # Calculate the conversion costs per conversed unit
            conversion_costs_per_conversed_unit[component_name] = (self.conversion_costs_component[component_name]
                                                              / self.conversed_stream_per_component[component_name][main_output])

            # To this conversion costs, the intrinsic costs of the stream are added
            total_intrinsic_costs_per_available_unit[component_name] = (intrinsic_costs_per_available_unit[main_output]
                                                                   + conversion_costs_per_conversed_unit[component_name])

        pd.DataFrame.from_dict(conversion_costs_per_conversed_unit, orient='index').to_excel(
            self.new_result_folder + '/conversion_costs_per_conversed_unit.xlsx')
        pd.DataFrame.from_dict(total_intrinsic_costs_per_available_unit, orient='index').to_excel(
            self.new_result_folder + '/total_intrinsic_costs_per_available_unit.xlsx')

        stream_equations_constant = {}
        columns_index = [*self.pm_object.get_all_streams().keys()]
        for s in self.pm_object.get_specific_components('final', 'conversion'):
            component_name = s.get_name()
            if self.all_variables_dict['nominal_cap'][component_name] > 0:
                columns_index.append(component_name)

        coefficients_df = pd.DataFrame(index=columns_index, columns=columns_index)
        coefficients_df.fillna(value=0, inplace=True)

        main_outputs = []
        main_output_coefficients = {}
        for component in self.pm_object.get_specific_components('final', 'conversion'):
            main_output = component.get_main_output()
            main_outputs.append(main_output)
            main_output_coefficients[component.get_main_output()] = component.get_outputs()[main_output]

        all_inputs = []
        final_stream = None
        for component in self.pm_object.get_specific_components('final', 'conversion'):
            component_name = component.get_name()
            inputs = component.get_inputs()
            outputs = component.get_outputs()
            main_output = component.get_main_output()

            if self.all_variables_dict['nominal_cap'][component_name] == 0:
                continue

            hot_standby_stream = ''
            hot_standby_demand = 0
            if component.get_hot_standby_ability():
                hot_standby_stream = [*component.get_hot_standby_demand().keys()][0]
                hot_standby_demand = (self.hot_standby_demand[component_name][hot_standby_stream]
                                      / self.conversed_stream_per_component[component_name][main_output])

            # First of all, associate inputs to components
            # If hot standby possible: input + hot standby demand -> hot standby demand prt conversed unit
            # If same stream in input and output: input - output
            # If neither: just input
            for i in [*inputs.keys()]:  # stream in input
                if i not in [*outputs.keys()]:  # stream not in output
                    if component.get_hot_standby_ability():  # component has hot standby ability
                        if i != hot_standby_stream:
                            coefficients_df.loc[i, component_name] = inputs[i]
                        else:
                            coefficients_df.loc[i, component_name] = inputs[i] + hot_standby_demand
                    else:  # component has no hot standby ability
                        coefficients_df.loc[i, component_name] = inputs[i]
                else:  # stream in output
                    if (i in main_outputs) | (intrinsic_costs_per_available_unit[i] != 0):
                        if component.get_hot_standby_ability():    # component has hot standby ability
                            if i != hot_standby_stream:  # hot standby stream is not stream
                                coefficients_df.loc[i, component_name] = inputs[i] - outputs[i]
                            else:
                                coefficients_df.loc[i, component_name] = inputs[i] + hot_standby_demand - outputs[i]
                        else:    # component has no hot standby ability
                            coefficients_df.loc[i, component_name] = inputs[i] - outputs[i]

                all_inputs.append(i)

            # If outputs have costs, then they are associated with component (not main output)
            for o in [*outputs.keys()]:
                if (o not in [*inputs.keys()]) & (o != main_output):
                    if intrinsic_costs_per_available_unit[o] != 0:
                        coefficients_df.loc[o, component_name] = -outputs[o]

                if self.pm_object.get_stream(o).is_demanded():
                    final_stream = o

            coefficients_df.loc[component_name, component_name] = -1

        # Matching of costs, which do not influence demanded stream directly (via inputs)
        # Costs of side streams with no demand (e.g., flares to burn excess gases)
        # will be added to final stream
        for component in self.pm_object.get_specific_components('final', 'conversion'):
            main_output = self.pm_object.get_stream(component.get_main_output())
            main_output_name = main_output.get_name()

            component_name = component.get_name()
            if self.all_variables_dict['nominal_cap'][component_name] == 0:
                continue

            if main_output_name not in all_inputs:  # Check if main output is input of other conversion
                if not main_output.is_demanded():  # Check if main output is demanded
                    coefficients_df.loc[component.get_name(), final_stream] = 1

        # Each stream, if main output, has its intrinsic costs and the costs of the conversion component
        for stream in self.model.ME_STREAMS:
            for component in self.pm_object.get_specific_components('final', 'conversion'):
                component_name = component.get_name()

                if self.all_variables_dict['nominal_cap'][component_name] == 0:
                    continue

                main_output = component.get_main_output()
                outputs = component.get_outputs()
                if stream == main_output:
                    # ratio is when several components have same output
                    ratio = (self.conversed_stream_per_component[component_name][stream]
                             / self.conversed_stream[stream])
                    coefficients_df.loc[component_name, stream] = 1 / outputs[stream] * ratio

                    coefficients_df.loc[stream, stream] = -1

            if stream not in main_outputs:
                coefficients_df.loc[stream, stream] = -1

        coefficients_df.to_excel(self.new_result_folder + '/equations.xlsx')

        # Right hand side (constants)
        coefficients_dict = {}
        for column in coefficients_df.columns:
            coefficients_dict.update({column: coefficients_df[column].tolist()})
            if column in self.model.ME_STREAMS:
                if column in [main_output_coefficients.keys()]:
                    if False:
                        stream_equations_constant.update({column: (-intrinsic_costs_per_available_unit[column]
                                                                   * main_output_coefficients[column])})
                    else:
                        stream_equations_constant.update({column: -intrinsic_costs_per_available_unit[column]})
                else:
                    stream_equations_constant.update({column: -intrinsic_costs_per_available_unit[column]})
            else:
                if self.all_variables_dict['nominal_cap'][column] == 0:
                    continue

                component = self.pm_object.get_component(column)
                main_output = component.get_main_output()
                stream_equations_constant.update({column: (-conversion_costs_per_conversed_unit[column]
                                                           * main_output_coefficients[main_output])})

        pd.DataFrame.from_dict(stream_equations_constant, orient='index').to_excel(
            self.new_result_folder + '/stream_equations_constant.xlsx')

        values_equations = coefficients_dict.values()
        A = np.array(list(values_equations))
        values_constant = stream_equations_constant.values()
        B = np.array(list(values_constant))
        X = np.linalg.solve(A, B)

        for i, c in enumerate(columns_index):
            self.production_cost_stream_per_unit.update({c: round(X[i], 3)})

        streams_and_costs = pd.DataFrame()
        dataframe_dict = {}

        for column in columns_index:

            if column in self.model.ME_STREAMS:
                stream = column
                stream_object = self.pm_object.get_stream(stream)
                nice_name = stream_object.get_nice_name()
                streams_and_costs.loc[nice_name, 'unit'] = stream_object.get_unit()

                streams_and_costs.loc[nice_name, 'Available Stream'] = self.available_stream[stream]
                streams_and_costs.loc[nice_name, 'Emitted Stream'] = self.emitted_stream[stream]
                streams_and_costs.loc[nice_name, 'Purchased Stream'] = self.purchased_stream[stream]
                streams_and_costs.loc[nice_name, 'Sold Stream'] = self.sold_stream[stream]
                streams_and_costs.loc[nice_name, 'Generated Stream'] = self.total_generated_stream[stream]
                streams_and_costs.loc[nice_name, 'Stored Stream'] = self.stored_stream[stream]
                streams_and_costs.loc[nice_name, 'Conversed Stream'] = self.conversed_stream[stream]
                streams_and_costs.loc[nice_name, 'Total Stream'] = self.total_availability[stream]

                streams_and_costs.loc[nice_name, 'Total Purchase Costs'] = self.purchase_costs[stream]
                if self.purchased_stream[stream] > 0:
                    purchase_costs = self.purchase_costs[stream] / self.purchased_stream[stream]
                    streams_and_costs.loc[nice_name, 'Average Purchase Costs per purchased Unit'] = purchase_costs
                else:
                    streams_and_costs.loc[nice_name, 'Average Purchase Costs per purchased Unit'] = 0

                streams_and_costs.loc[nice_name, 'Total Selling Revenue/Disposal Costs'] = self.selling_costs[stream]
                if self.sold_stream[stream] > 0:
                    revenue = self.selling_costs[stream] / self.sold_stream[stream]
                    streams_and_costs.loc[nice_name, 'Average Selling Revenue / Disposal Costs per sold/disposed Unit'] \
                        = revenue
                else:
                    streams_and_costs.loc[nice_name, 'Average Selling Revenue / Disposal Costs per sold/disposed Unit'] \
                        = 0

                self.total_variable_costs[stream] = self.purchase_costs[stream] + self.selling_costs[stream]
                streams_and_costs.loc[nice_name, 'Total Variable Costs'] = self.total_variable_costs[stream]

                streams_and_costs.loc[nice_name, 'Total Generation Fix Costs'] = self.total_generation_costs[stream]
                if self.total_generated_stream[stream] > 0:
                    streams_and_costs.loc[nice_name, 'Costs per used unit'] \
                        = self.total_generation_costs[stream] / (self.total_generated_stream[stream] - self.emitted_stream[stream])
                else:
                    streams_and_costs.loc[nice_name, 'Costs per used unit'] = 0

                streams_and_costs.loc[nice_name, 'Total Storage Fix Costs'] = self.storage_costs[stream]
                if self.stored_stream[stream] > 0:
                    stored_costs = self.storage_costs[stream] / self.stored_stream[stream]
                    streams_and_costs.loc[nice_name, 'Total Storage Fix Costs per stored Unit'] = stored_costs
                else:
                    streams_and_costs.loc[nice_name, 'Total Storage Fix Costs per stored Unit'] = 0

                streams_and_costs.loc[nice_name, 'Total Conversion Fix Costs'] = self.total_conversion_costs[stream]
                if self.conversed_stream[stream] > 0:
                    conversion_costs = self.total_conversion_costs[stream] / self.conversed_stream[stream]
                    streams_and_costs.loc[nice_name, 'Total Conversion Fix Costs per conversed Unit'] = conversion_costs
                else:
                    streams_and_costs.loc[nice_name, 'Total Conversion Fix Costs per conversed Unit'] = 0

                self.total_fix_costs[stream] \
                    = self.total_conversion_costs[stream] + self.storage_costs[stream] + self.total_generation_costs[stream]
                streams_and_costs.loc[nice_name, 'Total Fix Costs'] = self.total_fix_costs[stream]

                self.total_costs[stream] = self.total_variable_costs[stream] + self.total_fix_costs[stream]
                streams_and_costs.loc[nice_name, 'Total Costs'] = self.total_costs[stream]

                if self.total_availability[stream] > 0:
                    streams_and_costs.loc[nice_name, 'Total Costs per Unit'] \
                        = self.total_costs[stream] / self.total_availability[stream]
                else:
                    streams_and_costs.loc[nice_name, 'Total Costs per Unit'] = 0

                if intrinsic_costs[stream] >= 0:
                    streams_and_costs.loc[nice_name, 'Production Costs per Unit'] \
                        = self.production_cost_stream_per_unit[stream]
                else:
                    streams_and_costs.loc[nice_name, 'Production Costs per Unit'] \
                        = -self.production_cost_stream_per_unit[stream]

                streams_and_costs.to_excel(self.new_result_folder + '/streams.xlsx')

            else:
                component_name = column
                component_nice_name = self.pm_object.get_nice_name(component_name)
                component = self.pm_object.get_component(component_name)

                main_output = component.get_main_output()
                main_output_nice_name = self.pm_object.get_nice_name(component.get_main_output())

                stream_object = self.pm_object.get_stream(main_output)
                unit = stream_object.get_unit()

                index = component_nice_name + ' [' + unit + ' ' + main_output_nice_name + ']'

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
                    input_nice_name = self.pm_object.get_nice_name(i)

                    in_coeff = round(inputs[i] / main_output_coefficient, 3)
                    prod_costs = round(self.production_cost_stream_per_unit[i], 3)
                    input_costs = round(self.production_cost_stream_per_unit[i] * inputs[i]
                                        / main_output_coefficient, 3)

                    input_nice_name += ' (Input)'

                    components_and_costs.loc[(index, 'Coefficient'), input_nice_name] = in_coeff
                    components_and_costs.loc[(index, 'Cost per Unit'), input_nice_name] = prod_costs
                    components_and_costs.loc[(index, 'Total Costs'), input_nice_name] = input_costs

                    total_costs += input_costs

                    if i in [*outputs.keys()]:
                        # Handle output earlier s.t. its close to input of same stream in excel file
                        output_nice_name = self.pm_object.get_nice_name(i)
                        out_coeff = round(outputs[i] / main_output_coefficient, 3)

                        # Three cases occur
                        # 1: The output stream has a positive intrinsic value because it can be used again -> negative
                        # 2: The output can be sold with revenue -> negative
                        # 3: The output produces costs because the stream needs to be disposed, for example -> positive

                        if self.selling_costs[i] > 0: # Case 3
                            prod_costs = round(self.production_cost_stream_per_unit[i], 3)
                            output_costs = round(self.production_cost_stream_per_unit[i] * outputs[i]
                                                / main_output_coefficient, 3)
                        else: # Case 1 & 2
                            prod_costs = - round(self.production_cost_stream_per_unit[i], 3)
                            output_costs = - round(self.production_cost_stream_per_unit[i] * outputs[i]
                                                / main_output_coefficient, 3)

                        output_nice_name += ' (Output)'

                        components_and_costs.loc[(index, 'Coefficient'), output_nice_name] = out_coeff
                        components_and_costs.loc[(index, 'Cost per Unit'), output_nice_name] = prod_costs
                        components_and_costs.loc[(index, 'Total Costs'), output_nice_name] = output_costs

                        total_costs += output_costs

                        processed_outputs.append(i)

                for o in [*outputs.keys()]:
                    if o in processed_outputs:
                        continue

                    output_nice_name = self.pm_object.get_nice_name(o)

                    if o != component.get_main_output():
                        out_coeff = round(outputs[o] / main_output_coefficient, 3)

                        # Three cases occur
                        # 1: The output stream has a positive intrinsic value because it can be used again -> negative
                        # 2: The output can be sold with revenue -> negative
                        # 3: The output produces costs because the stream needs to be disposed, for example -> positive

                        if self.selling_costs[o] > 0:  # Case 3: Disposal costs exist
                            prod_costs = round(self.production_cost_stream_per_unit[o], 3)
                            output_costs = round(self.production_cost_stream_per_unit[o] * outputs[o]
                                                / main_output_coefficient, 3)
                        else:  # Case 1 & 2
                            prod_costs = - round(self.production_cost_stream_per_unit[o], 3)
                            output_costs = - round(self.production_cost_stream_per_unit[o] * outputs[o]
                                                  / main_output_coefficient, 3)

                        output_nice_name += ' (Output)'

                        components_and_costs.loc[(index, 'Coefficient'), output_nice_name] = out_coeff
                        components_and_costs.loc[(index, 'Cost per Unit'), output_nice_name] = prod_costs
                        components_and_costs.loc[(index, 'Total Costs'), output_nice_name] = output_costs

                        total_costs += output_costs

                # Further costs, which are not yet in stream, need to be associated
                # In case that several components have same main output, costs are matched regarding share of production
                ratio = (self.conversed_stream_per_component[component_name][main_output]
                         / self.conversed_stream[main_output])

                if main_output in self.model.STORAGES:
                    column_name = 'Storage Costs'
                    components_and_costs.loc[(index, 'Coefficient'), column_name] = ratio
                    prod_costs = (self.storage_costs[main_output] / self.conversed_stream[main_output])
                    components_and_costs.loc[(index, 'Cost per Unit'), column_name] = prod_costs
                    components_and_costs.loc[(index, 'Total Costs'), column_name] = prod_costs * ratio

                    total_costs += prod_costs * ratio

                if stream_object.is_demanded():
                    for stream in self.model.ME_STREAMS:
                        if (stream not in all_inputs) & (stream in main_outputs) & (stream != main_output):
                            stream_nice_name = self.pm_object.get_nice_name(stream)

                            column_name = stream_nice_name + ' (Associated Costs)'
                            components_and_costs.loc[(index, 'Coefficient'), column_name] = ratio
                            prod_costs = (self.production_cost_stream_per_unit[stream]
                                          * self.conversed_stream[stream]
                                          / self.conversed_stream[main_output])
                            components_and_costs.loc[(index, 'Cost per Unit'), column_name] = prod_costs
                            components_and_costs.loc[(index, 'Total Costs'), column_name] = prod_costs * ratio

                            total_costs += prod_costs * ratio

                prod_costs = round(total_costs, 3)
                components_and_costs.loc[(index, 'Coefficient'), 'Final'] = ''
                components_and_costs.loc[(index, 'Cost per Unit'), 'Final'] = ''
                components_and_costs.loc[(index, 'Total Costs'), 'Final'] = prod_costs

                dataframe_dict[component_nice_name] = components_and_costs

            # Save dataframes in multi-sheet excel file
            with pd.ExcelWriter(self.new_result_folder + '/main_output_costs.xlsx', engine="xlsxwriter") as writer:
                for df in [*dataframe_dict.keys()]:
                    sheet_name = df.replace("Parallel Unit", "PU")
                    dataframe_dict[df].to_excel(writer, sheet_name)
                writer.save()

    def analyze_components(self):

        columns = ['Capacity [input]', 'Capacity Unit [input]', 'Investment [per input]',
                   'Capacity [output]', 'Capacity Unit [output]', 'Investment [per output]',
                   'Total Investment', 'Annuity', 'Maintenance', 'Taxes and Insurance',
                   'Personnel', 'Overhead', 'Working Capital']

        capacity_df = pd.DataFrame(columns=columns)
        for key in self.all_variables_dict['nominal_cap']:
            component_object = self.pm_object.get_component(key)
            nice_name = component_object.get_nice_name()

            capacity = self.all_variables_dict['nominal_cap'][key]

            if capacity == 0:
                continue

            investment = self.all_variables_dict['investment'][key]
            annuity = self.all_variables_dict['annuity'][key]
            maintenance = self.all_variables_dict['maintenance_costs'][key]
            taxes_and_insurance = self.all_variables_dict['taxes_and_insurance_costs'][key]
            personnel = self.all_variables_dict['personnel_costs'][key]
            overhead = self.all_variables_dict['overhead_costs'][key]
            working_capital = self.all_variables_dict['working_capital_costs'][key]

            if component_object.get_component_type() == 'conversion':
                main_input = component_object.get_main_input()
                stream_object_input = self.pm_object.get_stream(main_input)
                nice_name_stream = stream_object_input.get_nice_name()
                unit_input = stream_object_input.get_unit()

                main_output = component_object.get_main_output()
                stream_object_output = self.pm_object.get_stream(main_output)
                nice_name_stream_output = stream_object_output.get_nice_name()
                unit_output = stream_object_output.get_unit()

                inputs = component_object.get_inputs()
                outputs = component_object.get_outputs()

                if unit_input == 'MWh':
                    unit_input = 'MW'
                elif unit_input == 'kWh':
                    unit_input = 'kW'
                else:
                    unit_input = unit_input + ' / h'

                if unit_output == 'MWh':
                    unit_output = 'MW'
                elif unit_output == 'kWh':
                    unit_output = 'kW'
                else:
                    unit_output = unit_output + ' / h'

                coefficient = outputs[main_output] / inputs[main_input]

                capacity_df.loc[nice_name, 'Capacity [input]'] = capacity
                capacity_df.loc[nice_name, 'Capacity Unit [input]'] = unit_input + ' ' + nice_name_stream
                capacity_df.loc[nice_name, 'Investment [per input]'] = investment / capacity

                capacity_df.loc[nice_name, 'Capacity [output]'] = capacity * coefficient
                capacity_df.loc[nice_name, 'Capacity Unit [output]'] = unit_output + ' ' + nice_name_stream_output
                capacity_df.loc[nice_name, 'Investment [per output]'] = investment / (capacity * coefficient)

            elif component_object.get_component_type() == 'generator':
                stream_object = self.pm_object.get_stream(component_object.get_generated_stream())
                nice_name_stream = stream_object.get_nice_name()
                unit = stream_object.get_unit()

                capacity_df.loc[nice_name, 'Capacity [output]'] = capacity
                if unit == 'MWh':
                    unit = 'MW'
                elif unit == 'kWh':
                    unit = 'kW'
                else:
                    unit = unit + ' / h'

                capacity_df.loc[nice_name, 'Capacity Unit [output]'] = unit + ' ' + nice_name_stream

                capacity_df.loc[nice_name, 'Investment [per output]'] = investment / capacity

            else:
                stream_object = self.pm_object.get_stream(key)
                nice_name_stream = stream_object.get_nice_name() + ' Storage'
                unit = stream_object.get_unit()

                capacity_df.loc[nice_name, 'Capacity [input]'] = capacity
                capacity_df.loc[nice_name, 'Capacity Unit [input]'] = unit + ' ' + nice_name_stream

                capacity_df.loc[nice_name, 'Investment [per input]'] = investment / capacity

            capacity_df.loc[nice_name, 'Total Investment'] = investment
            capacity_df.loc[nice_name, 'Annuity'] = annuity
            capacity_df.loc[nice_name, 'Maintenance'] = maintenance
            capacity_df.loc[nice_name, 'Taxes and Insurance'] = taxes_and_insurance
            capacity_df.loc[nice_name, 'Personnel'] = personnel
            capacity_df.loc[nice_name, 'Overhead'] = overhead
            capacity_df.loc[nice_name, 'Working Capital'] = working_capital

        capacity_df.to_excel(self.new_result_folder + '/components.xlsx')

    def analyze_generation(self):

        if len(self.model.GENERATORS) > 0:

            generation_df = pd.DataFrame(index=pd.Index([s for s in self.model.GENERATORS]))

            for generator in self.model.GENERATORS:
                generator_object = self.pm_object.get_component(generator)
                generated_stream = generator_object.get_generated_stream()

                investment = self.all_variables_dict['investment'][generator]
                capacity = self.all_variables_dict['nominal_cap'][generator]

                generation_df.loc[generator, 'Capacity'] = capacity
                generation_df.loc[generator, 'Investment'] = investment
                generation_df.loc[generator, 'Annuity'] = self.all_variables_dict['annuity'][generator]
                generation_df.loc[generator, 'Maintenance Cost'] = self.all_variables_dict['maintenance_costs'][generator]
                generation_df.loc[generator, 'Taxes and Insurance'] = self.all_variables_dict['taxes_and_insurance_costs'][generator]
                generation_df.loc[generator, 'Overhead'] = self.all_variables_dict['overhead_costs'][generator]
                generation_df.loc[generator, 'Personnel Cost'] = self.all_variables_dict['personnel_costs'][generator]

                generation_profile = pd.read_excel(self.path_data + generator_object.get_generation_data(), index_col=0)
                if max(self.model.TIME) > generation_profile.index[0]:
                    generation_profile = generation_profile.iloc[0:max(self.model.TIME) + 1]
                potential_generation = generation_profile.multiply(self.model.weightings, axis=0).sum().sum() * capacity
                generation_df.loc[generator, 'Potential Generation'] = potential_generation

                generation_df.loc[generator, 'LCOE before Curtailment'] = (generation_df.loc[generator, 'Annuity']
                                                                           + generation_df.loc[generator, 'Maintenance Cost']
                                                                           + generation_df.loc[generator, 'Taxes and Insurance']
                                                                           + generation_df.loc[generator, 'Overhead']
                                                                           + generation_df.loc[generator, 'Personnel Cost']) / potential_generation

                generation = self.generated_stream[generator]
                generation_df.loc[generator, ' Actual Generation'] = generation

                curtailment = potential_generation - generation
                generation_df.loc[generator, 'Curtailment'] = curtailment
                generation_df.loc[generator, 'LCOE after Curtailment'] = ((generation_df.loc[generator, 'Annuity']
                                                                           + generation_df.loc[generator, 'Maintenance Cost']
                                                                           + generation_df.loc[generator, 'Taxes and Insurance']
                                                                           + generation_df.loc[generator, 'Overhead']
                                                                           + generation_df.loc[generator, 'Personnel Cost'])
                                                                          / generation)

            generation_df.to_excel(self.new_result_folder + '/generation.xlsx')

    def analyze_total_costs(self):
        # Total costs: annuity, maintenance, buying and selling, taxes and insurance, etc.
        total_production = 0
        for stream in [*self.all_variables_dict['mass_energy_demand'].keys()]:
            total_production += sum(self.all_variables_dict['mass_energy_demand'][stream][t]
                                    * self.model.weightings[t] for t in self.model.TIME)

        cost_distribution = pd.DataFrame()

        total_costs = 0

        cost_distribution.loc['Annuity', 'Total'] = self.all_variables_dict['total_annuity']
        total_costs += self.all_variables_dict['total_annuity']

        cost_distribution.loc['Maintenance Costs', 'Total'] = self.all_variables_dict['total_maintenance_costs']
        total_costs += self.all_variables_dict['total_maintenance_costs']

        cost_distribution.loc['Personnel Costs', 'Total'] = self.all_variables_dict['total_personnel_costs']
        total_costs += self.all_variables_dict['total_personnel_costs']

        cost_distribution.loc['Taxes and Insurance Costs', 'Total'] = self.all_variables_dict[
            'total_taxes_and_insurance_costs']
        total_costs += self.all_variables_dict['total_taxes_and_insurance_costs']

        cost_distribution.loc['Overhead Costs', 'Total'] = self.all_variables_dict['total_overhead_costs']
        total_costs += self.all_variables_dict['total_overhead_costs']

        cost_distribution.loc['Working Capital Costs', 'Total'] = self.all_variables_dict['total_working_capital_costs']
        total_costs += self.all_variables_dict['total_working_capital_costs']

        for stream in self.model.ME_STREAMS:
            if self.purchase_costs[stream] != 0:
                cost_distribution.loc['Purchase Costs ' + self.pm_object.get_nice_name(stream), 'Total'] \
                    = self.purchase_costs[stream]
                total_costs += self.purchase_costs[stream]

        for stream in self.model.ME_STREAMS:
            if self.selling_costs[stream] < 0:
                cost_distribution.loc['Disposal ' + self.pm_object.get_nice_name(stream), 'Total'] \
                    = self.selling_costs[stream]
                total_costs += self.selling_costs[stream]

            if self.selling_costs[stream] > 0:
                cost_distribution.loc['Revenue ' + self.pm_object.get_nice_name(stream), 'Total'] \
                    = self.selling_costs[stream]
                total_costs += self.selling_costs[stream]

        cost_distribution.loc['Total', 'Total'] = total_costs

        cost_distribution.loc[:, 'Per Output'] = cost_distribution.loc[:, 'Total'] / total_production

        cost_distribution.loc[:, '%'] = cost_distribution.loc[:, 'Total'] / cost_distribution.loc['Total', 'Total']

        cost_distribution.to_excel(self.new_result_folder + '/cost_distribution.xlsx')

    def check_integer_variables(self, plots=False):

        integer_variables = ['capacity_binary',
                             'status_on', 'status_on_switch_on', 'status_on_switch_off',
                             'status_off', 'status_off_switch_on', 'status_off_switch_off',
                             'status_standby', 'status_standby_switch_on', 'status_standby_switch_off',
                             'storage_charge_binary', 'storage_discharge_binary']

        time_depending_variables = {}

        for variable_name in [*self.all_variables_dict]:

            if variable_name in integer_variables:

                for c in [*self.all_variables_dict[variable_name]]:

                    if self.all_variables_dict['nominal_cap'][c] == 0:
                        continue

                    list_values = self.all_variables_dict[variable_name][c]
                    if plots:

                        plt.figure()
                        plt.plot(list_values)
                        plt.xlabel('Hours')
                        plt.title(variable_name)

                        plt.savefig(self.new_result_folder + '/' + variable_name + " " + c + '.png')
                        plt.close()

                    if variable_name in integer_variables:
                        time_depending_variables[(variable_name, c)] = list_values

        ind = pd.MultiIndex.from_tuples([*time_depending_variables.keys()], names=('Variable', 'Component'))
        time_depending_variables_df = pd.DataFrame(index=ind)
        time_depending_variables_df = time_depending_variables_df.sort_index()

        for key in [*time_depending_variables.keys()]:
            for i, elem in enumerate(time_depending_variables[key]):
                time_depending_variables_df.loc[key, i] = elem

        if len(time_depending_variables_df.index) > 0:
            time_depending_variables_df.to_excel(self.new_result_folder + '/time_series_binaries.xlsx')

    def create_and_print_vector(self, plots=False):

        """ Uses the created dataframes to plot the stream vectors over time """

        variable_nice_names = {'mass_energy_purchase_stream': 'Purchase',
                               'mass_energy_available': 'Freely Available',
                               'mass_energy_component_in_streams': 'Input',
                               'mass_energy_component_out_streams': 'Output',
                               'mass_energy_generation': 'Generation',
                               'mass_energy_total_generation': 'Total Generation',
                               'mass_energy_storage_in_streams': 'Charging',
                               'mass_energy_storage_out_streams': 'Discharging',
                               'soc': 'State of Charge',
                               'mass_energy_sell_stream': 'Selling',
                               'mass_energy_emitted': 'Emitting',
                               'mass_energy_demand': 'Demand',
                               'storage_charge_binary': 'Charging Binary',
                               'storage_discharge_binary': 'Discharging Binary',
                               'mass_energy_hot_standby_demand': 'Hot Standby Demand'}

        time_depending_variables = {}

        # Two index vectors
        all_streams = []
        for stream in self.pm_object.get_specific_streams('final'):
            all_streams.append(stream.get_name())

        for variable_name in [*self.all_variables_dict]:

            if variable_name in self.variable_two_index:

                for stream in [*self.all_variables_dict[variable_name]]:

                    if stream not in all_streams:
                        continue

                    if (variable_name == 'storage_charge_binary') | (variable_name == 'storage_discharge_binary'):
                        if self.all_variables_dict['nominal_cap'][stream] == 0:
                            continue

                    list_values = self.all_variables_dict[variable_name][stream]
                    unit = self.pm_object.get_stream(stream).get_unit()
                    if unit == 'MWh':
                        unit = 'MW'
                    elif unit == 'kWh':
                        unit = 'kW'
                    else:
                        unit = unit + ' / h'

                    if list_values[0] is None:
                        continue

                    if sum(list_values) > 0:

                        if plots:

                            plt.figure()
                            plt.plot(list_values)
                            plt.xlabel('Hours')
                            plt.ylabel(unit)
                            plt.title(variable_nice_names[variable_name] + ' '
                                      + self.pm_object.get_nice_name(stream))

                            plt.savefig(self.new_result_folder + '/' + variable_nice_names[variable_name] + ' '
                                        + self.pm_object.get_nice_name(stream) + '.png')
                            plt.close()

                        if variable_name in [*variable_nice_names.keys()]:
                            time_depending_variables[(variable_nice_names[variable_name], '',
                                                      self.pm_object.get_nice_name(stream))] = list_values

            elif variable_name in self.variable_three_index:

                for c in [*self.all_variables_dict[variable_name]]:

                    if self.all_variables_dict['nominal_cap'][c] == 0:
                        continue

                    for stream in [*self.all_variables_dict[variable_name][c]]:

                        if stream not in all_streams:
                            continue

                        list_values = self.all_variables_dict[variable_name][c][stream]
                        unit = self.pm_object.get_stream(stream).get_unit()
                        if unit == 'MWh':
                            unit = 'MW'
                        elif unit == 'kWh':
                            unit = 'kW'
                        else:
                            unit = unit + ' / h'

                        if list_values[0] is None:
                            continue

                        if sum(list_values) > 0:

                            if plots:

                                plt.figure()
                                plt.plot(list_values)
                                plt.xlabel('Hours')
                                plt.ylabel(unit)
                                plt.title(variable_nice_names[variable_name] + ' '
                                          + self.pm_object.get_nice_name(stream) + ' '
                                          + self.pm_object.get_nice_name(c))

                                plt.savefig(self.new_result_folder + '/' + variable_nice_names[variable_name] + ' '
                                            + self.pm_object.get_nice_name(stream) + ' '
                                            + self.pm_object.get_nice_name(c) + '.png')
                                plt.close()

                            if variable_name in [*variable_nice_names.keys()]:
                                time_depending_variables[(variable_nice_names[variable_name],
                                                          self.pm_object.get_nice_name(c),
                                                          self.pm_object.get_nice_name(stream))] = list_values

        ind = pd.MultiIndex.from_tuples([*time_depending_variables.keys()], names=('Variable', 'Component', 'Stream'))
        time_depending_variables_df = pd.DataFrame(index=ind)
        time_depending_variables_df = time_depending_variables_df.sort_index()

        for key in [*time_depending_variables.keys()]:
            unit = self.pm_object.get_stream(self.pm_object.get_abbreviation(key[2])).get_unit()
            if unit == 'MWh':
                unit = 'MW'
            elif unit == 'kWh':
                unit = 'kW'
            else:
                unit = unit + ' / h'
            time_depending_variables_df.loc[key, 'unit'] = unit
            for i, elem in enumerate(time_depending_variables[key]):
                time_depending_variables_df.loc[key, i] = elem

        time_depending_variables_df.to_excel(self.new_result_folder + '/time_series_streams.xlsx')

    def build_sankey_diagram(self, only_energy=False, specific_stream='Hydrogen', average_streams=True,
                             specific_period=0):

        # todo: Add colors of stream and options of method

        all_streams = []
        for stream in self.pm_object.get_specific_streams('final'):
            all_streams.append(stream.get_name())

        # Sankey Diagram are structured as nodes and links
        # Nodes: Dictionary with pad, thickness, line, label and color
        # Links: Dictionary with source, target, value, label and color

        average = True

        # Nodes will be implemented as following: Each component will be one node as well as the "bus" for each stream
        labels = []
        label_indices = {}
        i = 0
        for component_object in self.pm_object.get_specific_components('final'):
            if component_object.get_component_type() == 'conversion':
                labels.append(component_object.get_nice_name())
                label_indices[component_object.get_nice_name()] = i
            elif component_object.get_component_type() == 'generator':
                generated_stream = component_object.get_generated_stream()
                generated_stream_nn = self.pm_object.get_stream(generated_stream).get_nice_name()
                labels.append(generated_stream_nn + ' Generation')
                label_indices[generated_stream_nn + ' Generation'] = i
            else:
                labels.append(component_object.get_nice_name() + ' Storage')
                label_indices[component_object.get_nice_name() + ' Storage'] = i
            i += 1

        for stream_object in self.pm_object.get_specific_streams('final'):
            labels.append(stream_object.get_nice_name() + ' Bus')
            label_indices[stream_object.get_nice_name() + ' Bus'] = i
            i += 1

            labels.append(stream_object.get_nice_name() + ' Freely Available')
            label_indices[stream_object.get_nice_name() + ' Freely Available'] = i
            i += 1

            labels.append(stream_object.get_nice_name() + ' Purchased')
            label_indices[stream_object.get_nice_name() + ' Purchased'] = i
            i += 1

            labels.append(stream_object.get_nice_name() + ' Generation')
            label_indices[stream_object.get_nice_name() + ' Generation'] = i
            i += 1

            labels.append(stream_object.get_nice_name() + ' Emitted')
            label_indices[stream_object.get_nice_name() + ' Emitted'] = i
            i += 1

            labels.append(stream_object.get_nice_name() + ' Sold')
            label_indices[stream_object.get_nice_name() + ' Sold'] = i
            i += 1

        # Links
        sources = []
        targets = []
        link_value = []

        to_bus_streams = ['mass_energy_purchase_stream', 'mass_energy_available', 'mass_energy_component_out_streams',
                          'mass_energy_generation', 'mass_energy_storage_out_streams']
        from_bus_stream = ['mass_energy_component_in_streams', 'mass_energy_storage_in_streams',
                           'mass_energy_sell_stream', 'mass_energy_emitted']

        for variable_name in [*self.all_variables_dict]:

            if variable_name in self.variable_two_index:

                for stream in [*self.all_variables_dict[variable_name]]:

                    if stream not in all_streams:
                        continue

                    stream_object = self.pm_object.get_stream(stream)
                    stream_name = stream_object.get_nice_name()
                    unit = stream_object.get_unit()

                    if only_energy:
                        if (unit != 'MWh') | (unit != 'kWh'):
                            continue

                    list_values = self.all_variables_dict[variable_name][stream]

                    average_list_value = 0
                    if not average:
                        if (list_values[specific_period] is None) | (list_values[specific_period] == 0):
                            continue
                    else:
                        average_list_value = sum(list_values) / len(list_values)
                        if (average_list_value is None) | (average_list_value == 0):
                            continue

                    inside = False
                    if variable_name in to_bus_streams:
                        if variable_name == 'mass_energy_available':
                            sources.append(label_indices[stream_name + ' Freely Available'])
                            targets.append(label_indices[stream_name + ' Bus'])
                        elif variable_name == 'mass_energy_purchase_stream':
                            sources.append(label_indices[stream_name + ' Purchased'])
                            targets.append(label_indices[stream_name + ' Bus'])
                        elif variable_name == 'mass_energy_generation':
                            sources.append(label_indices[stream_name + ' Generation'])
                            targets.append(label_indices[stream_name + ' Bus'])
                        elif variable_name == 'mass_energy_storage_out_streams':
                            sources.append(label_indices[stream_name + ' Storage'])
                            targets.append(label_indices[stream_name + ' Bus'])

                        inside = True

                    elif variable_name in from_bus_stream:
                        if variable_name == 'mass_energy_sell_stream':
                            sources.append(label_indices[stream_name + ' Bus'])
                            targets.append(label_indices[stream_name + ' Sold'])
                        elif variable_name == 'mass_energy_emitted':
                            sources.append(label_indices[stream_name + ' Bus'])
                            targets.append(label_indices[stream_name + ' Emitted'])
                        elif variable_name == 'mass_energy_storage_in_streams':
                            sources.append(label_indices[stream_name + ' Bus'])
                            targets.append(label_indices[stream_name + ' Storage'])

                        inside = True

                    if inside:
                        if not average:
                            link_value.append(list_values[specific_period])
                        else:
                            link_value.append(average_list_value)

            elif variable_name in self.variable_three_index:

                for c in [*self.all_variables_dict[variable_name]]:

                    for stream in [*self.all_variables_dict[variable_name][c]]:

                        if stream not in all_streams:
                            continue

                        component_object = self.pm_object.get_component(c)
                        component_name = component_object.get_nice_name()
                        stream_object = self.pm_object.get_stream(stream)
                        stream_name = stream_object.get_nice_name()
                        unit = stream_object.get_unit()

                        if only_energy:
                            if (unit != 'MWh') | (unit != 'kWh'):
                                continue

                        list_values = self.all_variables_dict[variable_name][c][stream]

                        average_list_value = 0
                        if not average:
                            if (list_values[specific_period] is None) | (list_values[specific_period] == 0):
                                continue
                        else:
                            average_list_value = sum(list_values) / len(list_values)
                            if (average_list_value is None) | (average_list_value == 0):
                                continue

                        inside = False
                        if variable_name in to_bus_streams:

                            if variable_name == 'mass_energy_component_out_streams':
                                sources.append(label_indices[component_name])
                                targets.append(label_indices[stream_name + ' Bus'])

                            inside = True

                        elif variable_name in from_bus_stream:

                            if variable_name == 'mass_energy_component_in_streams':
                                sources.append(label_indices[stream_name + ' Bus'])
                                targets.append(label_indices[component_name])

                            inside = True

                        if inside:
                            if not average:
                                link_value.append(list_values[specific_period])
                            else:
                                link_value.append(average_list_value)

        node = dict(
            pad=15,
            thickness=15,
            line=dict(color="black", width=0.5),
            label=labels,
            color='grey')

        link = dict(
            source=sources,
            target=targets,
            value=link_value,
            color='blue')

        fig = go.Figure(data=[go.Sankey(
            valueformat=".0f",
            valuesuffix="TWh",
            # Define nodes
            node=node,
            # Add links
            link=link)])

        if average:
            title_text = 'Average mass and energy flows'
        else:
            title_text = "Mass and energy flows during time step " + str(specific_period)

        fig.update_layout(
            title_text=title_text,
            font_size=10)
        fig.show()

    def __init__(self, optimization_problem, path_result, path_data, file_name=None):

        self.optimization_problem = optimization_problem
        self.model = optimization_problem.model
        self.instance = optimization_problem.instance
        self.pm_object = optimization_problem.pm_object
        self.file_name = file_name

        now = datetime.now()
        dt_string = now.strftime("%Y%m%d_%H%M%S")
        if self.file_name is None:
            self.new_result_folder = path_result + dt_string
        else:
            self.new_result_folder = path_result + dt_string + '_' + file_name
        os.makedirs(self.new_result_folder)

        self.path_data = path_data

        self.capacity_df = pd.DataFrame()
        self.financial_df = pd.DataFrame()
        self.annuity_df = pd.DataFrame()
        self.maintenance_df = pd.DataFrame()
        self.one_index_dict = {}
        self.two_index_dict = {}
        self.three_index_dict = {}
        self.available_stream = {}
        self.emitted_stream = {}
        self.conversed_stream = {}
        self.conversed_stream_per_component = {}
        self.purchased_stream = {}
        self.purchase_costs = {}
        self.sold_stream = {}
        self.selling_costs = {}
        self.stored_stream = {}
        self.storage_costs = {}
        self.storage_costs_per_unit = {}
        self.generated_stream = {}
        self.generation_costs = {}
        self.generation_costs_per_unit = {}
        self.conversion_component_costs = {}
        self.maintenance = {}
        self.total_fix_costs = {}
        self.total_variable_costs = {}
        self.total_costs = {}
        self.total_availability = {}
        self.production_cost_stream_per_unit = {}

        self.total_conversion_costs = {}
        self.total_generation_costs = {}
        self.total_generated_stream = {}

        self.hot_standby_demand = {}

        self.variable_zero_index = []
        self.variable_one_index = []
        self.variable_two_index = []
        self.variable_three_index = []
        self.all_variables_dict = {}

        self.extracting_data()
        self.process_variables()
        self.analyze_components()
        self.analyze_generation()
        self.analyze_total_costs()
        self.check_integer_variables()
        self.create_and_print_vector()
        self.analyze_streams()

        # self.build_sankey_diagram(only_energy=False)