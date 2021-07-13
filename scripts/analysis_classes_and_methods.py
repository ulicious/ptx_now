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

    def analyze_streams(self):

        """ Allocates costs to streams """

        # Calculate the total availability of each stream (purchase, from conversion, available)
        variable_names = ['mass_energy_purchase_stream', 'mass_energy_available',
                          'mass_energy_component_out_streams', 'mass_energy_total_generation',
                          'mass_energy_storage_in_streams', 'mass_energy_sell_stream', 'mass_energy_emitted',
                          'nominal_cap', 'mass_energy_generation']

        if True:

            for stream in self.model.ME_STREAMS:
                self.purchased_stream.update({stream: 0})
                self.purchase_costs.update({stream: 0})
                self.sold_stream.update({stream: 0})
                self.selling_revenue.update({stream: 0})
                self.generated_stream.update({stream: 0})
                self.available_stream.update({stream: 0})
                self.emitted_stream.update({stream: 0})
                self.stored_stream.update({stream: 0})
                self.conversed_stream.update({stream: 0})

            for variable_name in [*self.all_variables_dict]:

                if variable_name in self.variable_two_index:

                    if variable_name in variable_names:
                        for stream in [*self.all_variables_dict[variable_name]]:

                            list_values = self.all_variables_dict[variable_name][stream]
                            sum_values = sum(self.all_variables_dict[variable_name][stream])

                            if variable_name == "mass_energy_available":
                                self.available_stream[stream] = self.available_stream[stream] + sum_values

                            if variable_name == 'mass_energy_emitted':
                                if stream in self.model.EMITTED_STREAMS:
                                    self.emitted_stream[stream] = self.emitted_stream[stream] + sum_values

                            if variable_name == 'mass_energy_purchase_stream':  # Calculate costs of purchase
                                if stream in self.model.PURCHASABLE_STREAMS:
                                    self.purchased_stream[stream] = self.purchased_stream[stream] + sum_values
                                    self.purchase_costs[stream] = self.purchase_costs[stream] + \
                                                                  sum(list_values[t] * self.model.purchase_price[stream, t]
                                                                      for t in self.model.TIME)

                            if variable_name == 'mass_energy_sell_stream':  # Calculate costs of purchase
                                if stream in self.model.SALEABLE_STREAMS:
                                    self.sold_stream[stream] = self.sold_stream[stream] + sum_values
                                    self.selling_revenue[stream] = self.selling_revenue[stream] + \
                                                                   sum(list_values[t] * self.model.selling_price[stream, t]
                                                                       for t in self.model.TIME)

                            if variable_name == 'mass_energy_total_generation':
                                if stream in self.model.GENERATED_STREAMS:
                                    self.generated_stream[stream] = self.generated_stream[stream] + sum_values

                            if variable_name == 'mass_energy_storage_in_streams':
                                if stream in self.model.STORAGES:
                                    self.stored_stream[stream] = self.stored_stream[stream] + sum_values

                elif variable_name in self.variable_three_index:

                    if variable_name in variable_names:

                        for c in [*self.all_variables_dict[variable_name]]:

                            self.conversed_stream_per_component[c] = {}

                            for stream in [*self.all_variables_dict[variable_name][c]]:

                                sum_values = sum(self.all_variables_dict[variable_name][c][stream])

                                if variable_name == 'mass_energy_component_out_streams':
                                    self.conversed_stream[stream] = self.conversed_stream[stream] + sum_values
                                    self.conversed_stream_per_component[c][stream] = sum_values

            # Calculate total stream availability
            for stream in self.model.ME_STREAMS:
                self.total_availability[stream] = (self.purchased_stream[stream] + self.generated_stream[stream]
                                                   + self.conversed_stream[stream])

            not_used_streams = []
            for key in [*self.total_availability]:
                if self.total_availability[key] == 0:
                    not_used_streams.append(key)

            # Calculate the total cost of conversion. Important: conversion costs only occur for stream, where
            # output is main stream (E.g., electrolysis produces hydrogen and oxygen -> oxygen will not have conversion cost

            for stream in self.model.ME_STREAMS:
                self.conversion_component_costs.update({stream: 0})
                self.storage_costs.update({stream: 0})
                self.storage_costs_per_unit.update({stream: 0})
                self.generation_costs.update({stream: 0})
                self.generation_costs_per_unit.update({stream: 0})
                self.maintenance.update({stream: 0})

            # Get fix costs for each stream
            main_conversions = self.pm_object.get_all_main_conversion()
            for i in main_conversions.index:
                out_stream = main_conversions.loc[i, 'output_me']
                c = main_conversions.loc[i, 'component']
                self.conversion_component_costs[out_stream] = (self.conversion_component_costs[out_stream]
                                                               + self.all_variables_dict['annuity'][c]
                                                               + self.all_variables_dict['maintenance_costs'][c]
                                                               + self.all_variables_dict['taxes_and_insurance_costs'][c]
                                                               + self.all_variables_dict['personnel_costs'][c]
                                                               + self.all_variables_dict['overhead_costs'][c]
                                                               + self.all_variables_dict['working_capital_costs'][c])

            # Get annuity of storage units
            for stream in self.model.STORAGES:
                self.storage_costs[stream] = (self.storage_costs[stream]
                                                + self.all_variables_dict['annuity'][stream]
                                                + self.all_variables_dict['maintenance_costs'][stream]
                                                + self.all_variables_dict['taxes_and_insurance_costs'][stream]
                                                + self.all_variables_dict['personnel_costs'][stream]
                                                + self.all_variables_dict['overhead_costs'][stream]
                                                + self.all_variables_dict['working_capital_costs'][stream])

            # Get annuity of generation units
            for generator in self.model.GENERATORS:
                generated_stream = self.pm_object.get_component(generator).get_generated_stream()
                self.generation_costs[generated_stream] = (self.generation_costs[generated_stream]
                                                           + self.all_variables_dict['annuity'][generator]
                                                           + self.all_variables_dict['maintenance_costs'][generator]
                                                           + self.all_variables_dict['taxes_and_insurance_costs'][generator]
                                                           + self.all_variables_dict['personnel_costs'][generator]
                                                           + self.all_variables_dict['overhead_costs'][generator]
                                                           + self.all_variables_dict['working_capital_costs'][generator])

            # Calculate total cost from purchase, storing, generation and conversion
            for stream in self.model.ME_STREAMS:
                self.total_fix_costs.update({stream: (self.conversion_component_costs[stream] + self.storage_costs[stream]
                                                      + self.generation_costs[stream])})

            for stream in self.model.ME_STREAMS:
                self.total_market_costs.update({stream: self.purchase_costs[stream] - self.selling_revenue[stream]})

            for stream in self.model.ME_STREAMS:
                self.total_costs.update({stream: self.total_fix_costs[stream] + self.total_market_costs[stream]})

            # Calculation of costs per stream
            costs_per_unit = {}
            for key in [*self.total_costs]:
                if key not in not_used_streams:
                    costs_per_unit.update({key: self.total_costs[key] / self.total_availability[key]})
                else:
                    costs_per_unit.update({key: 0})

            # Calculate final costs per unit based on input of other streams. Important: These has to be done upstream
            stream_position = {}
            stream_equations = {}
            stream_equations_constant = {}
            i = 0
            for stream in self.model.ME_STREAMS:  # Give each stream index
                stream_position.update({stream: i})
                i += 1

            # Calculate how much input one outstream got from instream
            # Important: The coefficients have to be weighted regarding the amount of stream which is actually produced
            # by the component
            for out_stream in self.model.ME_STREAMS:
                outstream_instream_coefficient_dict = {}
                stream_equation_list = []

                # First, main conversion from main input to main output
                main_conversions = self.pm_object.get_all_main_conversion()
                index_stream_main_conversions = main_conversions[main_conversions['output_me'] == out_stream].index
                components_for_outstream_production = main_conversions.loc[index_stream_main_conversions, 'component'].tolist()
                if len(index_stream_main_conversions) > 0:
                    for i in index_stream_main_conversions:
                        c = main_conversions.loc[i, 'component']
                        in_stream = main_conversions.loc[i, 'input_me']
                        coefficient = main_conversions.loc[i, 'coefficient'] * self.conversed_stream_per_component[c][out_stream]
                        outstream_instream_coefficient_dict.update({in_stream: coefficient / self.conversed_stream[out_stream]})

                    # Second, side conversions from side input to main output
                    side_conversions = self.pm_object.get_all_side_conversions()
                    index_stream_side_conversions = side_conversions[side_conversions['output_me'] == out_stream].index
                    if len(index_stream_side_conversions) > 0:
                        for i in index_stream_side_conversions:
                            c = side_conversions.loc[i, 'component']
                            in_stream = side_conversions.loc[i, 'input_me']
                            coefficient = side_conversions.loc[i, 'coefficient']
                            outstream_instream_coefficient_dict.update(
                                {in_stream: coefficient
                                            * self.conversed_stream_per_component[c][out_stream]
                                            / self.conversed_stream[out_stream]})

                    # Third, side conversions from side output to main output
                    # From side output to main input to main output
                    index_stream_side_conversions = side_conversions[(side_conversions['output_me'] != out_stream)
                                                                     & side_conversions['component'].isin(components_for_outstream_production)].index
                    if len(index_stream_side_conversions) > 0:
                        for i in index_stream_side_conversions:
                            c = side_conversions.loc[i, 'component']
                            output = side_conversions.loc[i, 'output_me']
                            coefficient_1 = side_conversions.loc[i, 'coefficient']
                            input_me = side_conversions.loc[i, 'input_me']
                            ind = main_conversions[(main_conversions['output_me'] == out_stream)
                                                   & (main_conversions['input_me'] == input_me)].index
                            coefficient_2 = main_conversions.loc[ind, 'coefficient'].values[0]
                            coefficient = (1 / coefficient_1 / coefficient_2
                                           * self.conversed_stream_per_component[c][output]
                                           / self.conversed_stream[output])

                            outstream_instream_coefficient_dict.update({output: coefficient})

                i = 0
                for stream in self.model.ME_STREAMS:
                    if stream_position[stream] == i:
                        if costs_per_unit[out_stream] == 0:
                            if stream != out_stream:
                                stream_equation_list.append(0)
                            else:
                                stream_equation_list.append(-1)
                        else:
                            if stream in [*outstream_instream_coefficient_dict]:
                                if outstream_instream_coefficient_dict[stream] != 0:
                                    stream_equation_list.append(1 / outstream_instream_coefficient_dict[stream])
                                else:
                                    stream_equation_list.append(0)
                            else:
                                if stream != out_stream:
                                    stream_equation_list.append(0)
                                else:
                                    stream_equation_list.append(-1)
                        i += 1

                stream_equations.update({out_stream: stream_equation_list})
                stream_equations_constant.update({out_stream: -costs_per_unit[out_stream]})

            pd.DataFrame().from_dict(stream_equations).to_excel(self.new_result_folder + '/equations.xlsx')

            values_equations = stream_equations.values()
            A = np.array(list(values_equations))
            values_constant = stream_equations_constant.values()
            B = np.array(list(values_constant))
            X = np.linalg.solve(A, B)

            for stream in [*stream_position]:
                self.production_cost_stream_per_unit.update({stream: X[stream_position[stream]]})

            streams_and_costs = pd.DataFrame()

            for stream in self.model.ME_STREAMS:
                stream_object = self.pm_object.get_stream(stream)
                nice_name = stream_object.get_nice_name()
                streams_and_costs.loc[nice_name, 'unit'] = stream_object.get_unit()

                streams_and_costs.loc[nice_name, 'Available Stream'] = self.available_stream[stream]
                streams_and_costs.loc[nice_name, 'Emitted Stream'] = self.emitted_stream[stream]
                streams_and_costs.loc[nice_name, 'Purchased Stream'] = self.purchased_stream[stream]
                streams_and_costs.loc[nice_name, 'Sold Stream'] = self.sold_stream[stream]
                streams_and_costs.loc[nice_name, 'Generated Stream'] = self.generated_stream[stream]
                streams_and_costs.loc[nice_name, 'Stored Stream'] = self.stored_stream[stream]
                streams_and_costs.loc[nice_name, 'Conversed Stream'] = self.conversed_stream[stream]
                streams_and_costs.loc[nice_name, 'Total Stream'] = self.total_availability[stream]

                streams_and_costs.loc[nice_name, 'Total Purchase Costs'] = self.purchase_costs[stream]
                if self.purchased_stream[stream] > 0:
                    streams_and_costs.loc[nice_name, 'Average Purchase Costs per purchased Unit'] = self.purchase_costs[stream] \
                                                                               / self.purchased_stream[stream]
                else:
                    streams_and_costs.loc[nice_name, 'Average Purchase Costs per purchased Unit'] = 0

                streams_and_costs.loc[nice_name, 'Total Selling Revenue/Disposal Costs'] = self.selling_revenue[stream]
                if self.sold_stream[stream] > 0:
                    streams_and_costs.loc[nice_name, 'Average Selling Revenue / Disposal Costs per sold/disposed Unit'] = self.selling_revenue[stream] \
                                                                                / self.sold_stream[stream]
                else:
                    streams_and_costs.loc[nice_name, 'Average Selling Revenue / Disposal Costs per sold/disposed Unit'] = 0

                streams_and_costs.loc[nice_name, 'Total Market Costs'] = self.total_market_costs[stream]

                streams_and_costs.loc[nice_name, 'Total Generation Fix Costs'] = self.generation_costs[stream]
                if self.generated_stream[stream] > 0:
                    streams_and_costs.loc[nice_name, 'Total Generation Fix Costs per generated Unit'] = self.generation_costs[stream] \
                                                                                 / self.generated_stream[stream]
                else:
                    streams_and_costs.loc[nice_name, 'Total Generation Fix Costs per generated Unit'] = 0

                streams_and_costs.loc[nice_name, 'Total Storage Fix Costs'] = self.storage_costs[stream]
                if self.stored_stream[stream] > 0:
                    streams_and_costs.loc[nice_name, 'Total Storage Fix Costs per stored Unit'] = self.storage_costs[stream] \
                                                                              / self.stored_stream[stream]
                else:
                    streams_and_costs.loc[nice_name, 'Total Storage Fix Costs per stored Unit'] = 0

                streams_and_costs.loc[nice_name, 'Total Conversion Fix Costs'] = self.conversion_component_costs[stream]
                if self.conversed_stream[stream] > 0:
                    streams_and_costs.loc[nice_name, 'Total Conversion Fix Costs per conversed Unit'] = (self.conversion_component_costs[stream]
                                                                                     / self.conversed_stream[stream])
                else:
                    streams_and_costs.loc[nice_name, 'Total Conversion Fix Costs per conversed Unit'] = 0

                streams_and_costs.loc[nice_name, 'Total Fix Costs'] = self.total_fix_costs[stream]
                streams_and_costs.loc[nice_name, 'Total Costs'] = self.total_costs[stream]
                streams_and_costs.loc[nice_name, 'Total Costs per Unit'] = costs_per_unit[stream]

                if self.total_availability[stream] != 0:
                    streams_and_costs.loc[nice_name, 'Total Variable Costs per Unit'] = \
                        (self.total_costs[stream] - self.total_fix_costs[stream]) / self.total_availability[stream]
                else:
                    streams_and_costs.loc[nice_name, 'Total Variable Costs per Unit'] = 0

                streams_and_costs.loc[nice_name, 'Production Costs per Unit'] = \
                    self.production_cost_stream_per_unit[stream]

            streams_and_costs.to_excel(self.new_result_folder + '/streams.xlsx')

    def analyze_components(self):

        capacity_df = pd.DataFrame()
        for key in self.all_variables_dict['nominal_cap']:
            component_object = self.pm_object.get_component(key)
            nice_name = component_object.get_nice_name()

            capacity = self.all_variables_dict['nominal_cap'][key]
            investment = self.all_variables_dict['investment'][key]
            annuity = self.all_variables_dict['annuity'][key]
            maintenance = self.all_variables_dict['maintenance_costs'][key]
            taxes_and_insurance = self.all_variables_dict['taxes_and_insurance_costs'][key]
            personnel = self.all_variables_dict['personnel_costs'][key]
            overhead = self.all_variables_dict['overhead_costs'][key]
            working_capital = self.all_variables_dict['working_capital_costs'][key]

            storage = False

            if component_object.get_component_type() == 'conversion':
                main_conversions = self.pm_object.get_main_conversion_streams_by_component(key)
                stream_object = self.pm_object.get_stream(main_conversions[0])
                nice_name_stream = stream_object.get_nice_name()
                unit = stream_object.get_unit()
            elif component_object.get_component_type() == 'generator':
                stream_object = self.pm_object.get_stream(component_object.get_generated_stream())
                nice_name_stream = stream_object.get_nice_name()
                unit = stream_object.get_unit()
            else:
                stream_object = self.pm_object.get_stream(key)
                nice_name_stream = stream_object.get_nice_name() + ' Storage'
                unit = stream_object.get_unit()
                storage = True

            capacity_df.loc[nice_name, 'Capacity'] = capacity

            if (not storage) & (unit == 'MWh'):
                unit = 'MW'
                capacity_df.loc[nice_name, 'Capacity Unit'] = unit + ' ' + nice_name_stream
            elif storage:
                capacity_df.loc[nice_name, 'Capacity Unit'] = unit + ' ' + nice_name_stream
            else:
                capacity_df.loc[nice_name, 'Capacity Unit'] = unit + ' ' + nice_name_stream + ' / h'

            capacity_df.loc[nice_name, 'Investment'] = investment
            capacity_df.loc[nice_name, 'Annuity'] = annuity
            capacity_df.loc[nice_name, 'Maintenance'] = maintenance
            capacity_df.loc[nice_name, 'Taxes and Insurance'] = taxes_and_insurance
            capacity_df.loc[nice_name, 'Personnel'] = personnel
            capacity_df.loc[nice_name, 'Overhead'] = overhead
            capacity_df.loc[nice_name, 'Working Capital'] = working_capital

        capacity_df.to_excel(self.new_result_folder + '/components.xlsx')

    def analyze_generation(self):

        generation_df = pd.DataFrame(index=pd.Index([s for s in self.model.GENERATORS]))

        for generator in self.model.GENERATORS:
            generated_stream = self.pm_object.get_component(generator).get_generated_stream()

            investment = self.all_variables_dict['investment'][generator]
            generation_df.loc[generator, 'investment'] = investment
            generation_df.loc[generator, 'annuity'] = self.all_variables_dict['annuity'][generator]
            generation_df.loc[generator, 'maintenance_cost'] = self.all_variables_dict['maintenance_costs'][generator]
            generation_df.loc[generator, 'taxes_and_insurance'] = self.all_variables_dict['taxes_and_insurance_costs'][generator]
            generation_df.loc[generator, 'overhead'] = self.all_variables_dict['overhead_costs'][generator]
            generation_df.loc[generator, 'personnel_cost'] = self.all_variables_dict['personnel_costs'][generator]

            generation = sum(self.all_variables_dict['mass_energy_generation'][generator][generated_stream])

            generation_df.loc[generator, 'LCOE'] = (generation_df.loc[generator, 'annuity']
                                                    + generation_df.loc[generator, 'maintenance_cost']
                                                    + generation_df.loc[generator, 'taxes_and_insurance']
                                                    + generation_df.loc[generator, 'overhead']
                                                    + generation_df.loc[generator, 'personnel_cost']) / generation

        generation_df.to_excel(self.new_result_folder + '/generation.xlsx')

    def analyze_total_costs(self):
        # Total costs: annuity, maintenance, buying and selling, taxes and insurance, etc.
        total_production = 0
        for stream in [*self.all_variables_dict['mass_energy_demand'].keys()]:
            total_production += sum(self.all_variables_dict['mass_energy_demand'][stream])

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
            if self.selling_revenue[stream] < 0:
                cost_distribution.loc['Disposal ' + self.pm_object.get_nice_name(stream), 'Total'] \
                    = self.selling_revenue[stream] * (-1)
                total_costs += self.selling_revenue[stream] * (-1)  # todo: Turn around caluclation of disposal etc?

            if self.selling_revenue[stream] > 0:
                cost_distribution.loc['Revenue ' + self.pm_object.get_nice_name(stream), 'Total'] \
                    = self.selling_revenue[stream] * (-1)
                total_costs += self.selling_revenue[stream] * (-1)  # todo: Turn around caluclation of disposal etc?

        cost_distribution.loc['Total', 'Total'] = total_costs

        cost_distribution.loc[:, 'Per Output'] = cost_distribution.loc[:, 'Total'] / total_production

        cost_distribution.loc[:, '%'] = cost_distribution.loc[:, 'Total'] / cost_distribution.loc['Total', 'Total']

        cost_distribution.to_excel(self.new_result_folder + '/cost_distribution.xlsx')

    def check_integer_variables(self):

        integer_variables = ['capacity_binary', 'penalty_binary_lower_bound', 'component_correct_p', 'component_status',
                             'component_status_1', 'component_status_2', 'status_switch_on', 'status_switch_off',
                             'storage_charge_binary',
                             'storage_discharge_binary']

        for variable_name in [*self.all_variables_dict]:

            if variable_name in integer_variables:

                for c in [*self.all_variables_dict[variable_name]]:

                    list_values = self.all_variables_dict[variable_name][c]

                    plt.figure()
                    plt.plot(list_values)
                    plt.xlabel('Hours')
                    plt.title(variable_name)

                    plt.savefig(self.new_result_folder + '/' + variable_name + " " + c + '.png')
                    plt.close()

    def create_and_print_vector(self):

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
                               'storage_discharge_binary': 'Discharging Binary'}

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

                    list_values = self.all_variables_dict[variable_name][stream]
                    unit = self.pm_object.get_stream(stream).get_unit()
                    if unit == 'MWh':
                        unit = 'MW'

                    if list_values[0] is None:
                        continue

                    if sum(list_values) > 0:

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

                    for stream in [*self.all_variables_dict[variable_name][c]]:

                        if stream not in all_streams:
                            continue

                        list_values = self.all_variables_dict[variable_name][c][stream]
                        unit = self.pm_object.get_stream(stream).get_unit()
                        if unit == 'MWh':
                            unit = 'MW'

                        if list_values[0] is None:
                            continue

                        if sum(list_values) > 0:

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
        for key in [*time_depending_variables.keys()]:
            unit = self.pm_object.get_stream(self.pm_object.get_abbreviation(key[2])).get_unit()
            if unit == 'MWh':
                entry = 'MW'
            else:
                entry = unit + ' / h'
            time_depending_variables_df.loc[key, 'unit'] = entry
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
                        if unit != 'MWh':
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
                            if unit != 'MWh':
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

    def __init__(self, optimization_problem, path_result, file_name=None):

        self.optimization_problem = optimization_problem
        self.model = optimization_problem.model
        self.results = optimization_problem.results
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
        self.selling_revenue = {}
        self.stored_stream = {}
        self.storage_costs = {}
        self.storage_costs_per_unit = {}
        self.generated_stream = {}
        self.generation_costs = {}
        self.generation_costs_per_unit = {}
        self.conversion_component_costs = {}
        self.maintenance = {}
        self.total_fix_costs = {}
        self.total_market_costs = {}
        self.total_costs = {}
        self.total_availability = {}
        self.production_cost_stream_per_unit = {}

        self.variable_zero_index = []
        self.variable_one_index = []
        self.variable_two_index = []
        self.variable_three_index = []
        self.all_variables_dict = {}

        #self.create_dataframe()
        #self.create_and_print_vector()
        #self.create_and_print_financial()

        self.extracting_data()
        self.analyze_components()
        self.analyze_streams()
        self.analyze_generation()
        self.analyze_total_costs()
        # self.check_integer_variables()

        #self.build_sankey_diagram(only_energy=True)
