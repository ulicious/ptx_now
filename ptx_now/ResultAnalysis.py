import pandas as pd
from pyomo.core import *
import matplotlib.pyplot as plt
import numpy as np
import os

import plotly.graph_objects as go
from datetime import datetime


class ResultAnalysis:

    def extracting_data(self):

        for v in self.instance.component_objects(Var, active=True):

            variable_dict = v.extract_values()
            if not bool(variable_dict):
                continue

            list_value = []

            if [*variable_dict.keys()][0] is None:
                number_keys = 0
            elif isinstance([*variable_dict.keys()][0], tuple):
                number_keys = len([*variable_dict.keys()][0])
            else:
                number_keys = 1

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
                commodity_dict = {}
                commodity = ''
                first = True
                for key in [*variable_dict]:

                    if first:
                        commodity = key[0]
                        first = False

                    if commodity != key[0]:

                        commodity_dict.update({commodity: variable_list})
                        commodity = key[0]
                        variable_list = []

                    variable_list.append(variable_dict[key])

                commodity_dict.update({commodity: variable_list})

                self.all_variables_dict.update({str(v): commodity_dict})
                self.variable_two_index.append(str(v))

            elif number_keys == 3:

                variable_list = []
                component_dict = {}
                commodity_dict = {}
                commodity = ''
                c = ''
                first = True
                for key in [*variable_dict]:

                    if first:
                        commodity = key[1]
                        c = key[0]
                        first = False

                    if (commodity != key[1]) & (c == key[0]):
                        commodity_dict.update({commodity: variable_list})
                        commodity = key[1]
                        c = key[0]
                        variable_list = []
                    elif c != key[0]:
                        commodity_dict.update({commodity: variable_list})
                        component_dict.update({c: commodity_dict})
                        commodity_dict = {}
                        commodity = key[1]
                        c = key[0]
                        variable_list = []

                    variable_list.append(variable_dict[key])

                commodity_dict.update({commodity: variable_list})
                component_dict.update({c: commodity_dict})

                self.all_variables_dict.update({str(v): component_dict})
                self.variable_three_index.append(str(v))

    def process_variables(self):

        """ Allocates costs to commodities """

        # Calculate the total availability of each commodity (purchase, from conversion, available)
        variable_names = ['mass_energy_purchase_commodity', 'mass_energy_available',
                          'mass_energy_component_out_commodities', 'mass_energy_total_generation',
                          'mass_energy_storage_in_commodities', 'mass_energy_sell_commodity', 'mass_energy_emitted',
                          'nominal_cap', 'mass_energy_generation', 'mass_energy_hot_standby_demand']

        for commodity in self.model.ME_STREAMS:
            self.purchased_commodity.update({commodity: 0})
            self.purchase_costs.update({commodity: 0})
            self.sold_commodity.update({commodity: 0})
            self.selling_costs.update({commodity: 0})
            self.generated_commodity.update({commodity: 0})
            self.available_commodity.update({commodity: 0})
            self.emitted_commodity.update({commodity: 0})
            self.stored_commodity.update({commodity: 0})
            self.conversed_commodity.update({commodity: 0})
            self.total_generated_commodity.update({commodity: 0})

        for variable_name in [*self.all_variables_dict]:

            if variable_name in self.variable_two_index:

                if variable_name in variable_names:
                    for commodity in [*self.all_variables_dict[variable_name]]:

                        list_values = self.all_variables_dict[variable_name][commodity]
                        sum_values = sum(self.all_variables_dict[variable_name][commodity])

                        if not self.pm_object.get_uses_representative_periods():

                            if variable_name == "mass_energy_available":
                                self.available_commodity[commodity] = (self.available_commodity[commodity] + sum_values)

                            if variable_name == 'mass_energy_emitted':
                                if commodity in self.model.EMITTED_STREAMS:
                                    self.emitted_commodity[commodity] = (self.emitted_commodity[commodity] + sum_values)

                            if variable_name == 'mass_energy_purchase_commodity':  # Calculate costs of purchase
                                if commodity in self.model.PURCHASABLE_STREAMS:
                                    self.purchased_commodity[commodity] = (self.purchased_commodity[commodity] + sum_values)
                                    self.purchase_costs[commodity] = (self.purchase_costs[commodity] +
                                                                   sum(list_values[t]
                                                                       * self.model.purchase_price[commodity, t]
                                                                       for t in self.model.TIME))

                            if variable_name == 'mass_energy_sell_commodity':  # Calculate costs of purchase
                                if commodity in self.model.SALEABLE_STREAMS:
                                    self.sold_commodity[commodity] = (self.sold_commodity[commodity] + sum_values)
                                    self.selling_costs[commodity] = (self.selling_costs[commodity]
                                                                  + sum(list_values[t]
                                                                        * self.model.selling_price[commodity, t] * (-1)
                                                                        for t in self.model.TIME))

                            if variable_name == 'mass_energy_total_generation':
                                if commodity in self.model.GENERATED_STREAMS:
                                    self.total_generated_commodity[commodity] = (self.total_generated_commodity[commodity]
                                                                           + sum_values)

                            if variable_name == 'mass_energy_storage_in_commodities':
                                if commodity in self.model.STORAGES:
                                    self.stored_commodity[commodity] = (self.stored_commodity[commodity] + sum_values)

                        else:

                            if variable_name == "mass_energy_available":
                                self.available_commodity[commodity] = (self.available_commodity[commodity]
                                                                 + sum(list_values[t] * self.model.weightings[t]
                                                                       for t in self.model.TIME))

                            if variable_name == 'mass_energy_emitted':
                                if commodity in self.model.EMITTED_STREAMS:
                                    self.emitted_commodity[commodity] = (self.emitted_commodity[commodity] +
                                                                   sum(list_values[t] * self.model.weightings[t]
                                                                       for t in self.model.TIME))

                            if variable_name == 'mass_energy_purchase_commodity':  # Calculate costs of purchase
                                if commodity in self.model.PURCHASABLE_STREAMS:
                                    self.purchased_commodity[commodity] = (self.purchased_commodity[commodity]
                                                                     + sum(list_values[t] * self.model.weightings[t]
                                                                           for t in self.model.TIME))
                                    self.purchase_costs[commodity] = (self.purchase_costs[commodity]
                                                                   + sum(list_values[t] * self.model.weightings[t]
                                                                         * self.model.purchase_price[commodity, t]
                                                                         for t in self.model.TIME))

                            if variable_name == 'mass_energy_sell_commodity':  # Calculate costs of purchase
                                if commodity in self.model.SALEABLE_STREAMS:
                                    self.sold_commodity[commodity] = (self.sold_commodity[commodity]
                                                                + sum(list_values[t] * self.model.weightings[t]
                                                                      for t in self.model.TIME))
                                    self.selling_costs[commodity] = (self.selling_costs[commodity]
                                                                  + sum(list_values[t] * self.model.weightings[t]
                                                                        * self.model.selling_price[commodity, t] * (-1)
                                                                        for t in self.model.TIME))

                            if variable_name == 'mass_energy_total_generation':
                                if commodity in self.model.GENERATED_STREAMS:
                                    self.total_generated_commodity[commodity] = (self.total_generated_commodity[commodity]
                                                                           + sum(list_values[t]
                                                                                 * self.model.weightings[t]
                                                                                 for t in self.model.TIME))

                            if variable_name == 'mass_energy_storage_in_commodities':
                                if commodity in self.model.STORAGES:
                                    self.stored_commodity[commodity] = (self.stored_commodity[commodity]
                                                                  + sum(list_values[t] * self.model.weightings[t]
                                                                        for t in self.model.TIME))

            elif variable_name in self.variable_three_index:

                if variable_name in variable_names:

                    for c in [*self.all_variables_dict[variable_name]]:
                        component_object = self.pm_object.get_component(c)

                        conversion = False
                        for i in self.pm_object.get_final_conversion_components_objects():
                            if c == i.get_name():
                                conversion = True
                                if variable_name == 'mass_energy_component_out_commodities':
                                    self.conversed_commodity_per_component[c] = {}
                                elif variable_name == 'mass_energy_hot_standby_demand':
                                    self.hot_standby_demand[c] = {}

                        for commodity in [*self.all_variables_dict[variable_name][c]]:

                            list_values = self.all_variables_dict[variable_name][c][commodity]
                            sum_values = sum(self.all_variables_dict[variable_name][c][commodity])

                            ratio = 1
                            if conversion:
                                inputs = component_object.get_inputs()
                                outputs = component_object.get_outputs()

                                # Case commodity is conversed but not fully
                                if (commodity in [*inputs.keys()]) & (commodity in [*outputs.keys()]):
                                    sum_values = sum_values * outputs[commodity] / inputs[commodity]
                                    ratio = sum_values * outputs[commodity] / inputs[commodity]

                            if not self.pm_object.get_uses_representative_periods():

                                if variable_name == 'mass_energy_component_out_commodities':
                                    if commodity == component_object.get_main_output():
                                        self.conversed_commodity[commodity] = self.conversed_commodity[commodity] + sum_values
                                        self.conversed_commodity_per_component[c][commodity] = sum_values
                                    else:
                                        self.conversed_commodity[commodity] = self.conversed_commodity[commodity] + 0
                                        self.conversed_commodity_per_component[c][commodity] = 0

                                if variable_name == 'mass_energy_hot_standby_demand':
                                    if commodity in [*component_object.get_hot_standby_demand().keys()]:
                                        self.hot_standby_demand[c][commodity] = sum_values

                                if variable_name == 'mass_energy_generation':
                                    if commodity in self.model.GENERATED_STREAMS:
                                        self.generated_commodity[c] = sum_values

                            else:
                                if variable_name == 'mass_energy_component_out_commodities':
                                    if commodity == component_object.get_main_output():
                                        self.conversed_commodity[commodity] = (self.conversed_commodity[commodity]
                                                                         + sum(list_values[t] * self.model.weightings[t]
                                                                               * ratio for t in self.model.TIME))
                                        self.conversed_commodity_per_component[c][commodity] = sum(list_values[t]
                                                                                             * self.model.weightings[t]
                                                                                             * ratio
                                                                                             for t in self.model.TIME)
                                    else:
                                        self.conversed_commodity[commodity] = self.conversed_commodity[commodity] + 0
                                        self.conversed_commodity_per_component[c][commodity] = 0

                                if variable_name == 'mass_energy_hot_standby_demand':
                                    if commodity in [*component_object.get_hot_standby_demand().keys()]:
                                        self.hot_standby_demand[c][commodity] = sum(list_values[t]
                                                                                 * self.model.weightings[t] * ratio
                                                                                 for t in self.model.TIME)

                                if variable_name == 'mass_energy_generation':
                                    if commodity in self.model.GENERATED_STREAMS:
                                        self.generated_commodity[c] = sum(list_values[t] * self.model.weightings[t] * ratio
                                                                       for t in self.model.TIME)

    def create_assumptions_file(self):

        index_df = []
        base_investment = []
        base_capacity = []
        scaling_factor = []
        capex = []
        capex_unit = []
        maintenance = []
        taxes_and_insurance = []
        personnel = []
        overhead = []
        working_capital = []
        lifetime = []
        start_up_costs = []

        for c in self.pm_object.get_final_components_objects():

            if c.component_type == 'storage':
                index_df.append(c.get_nice_name() + ' Storage')
            else:
                index_df.append(c.get_nice_name())

            if c.component_type == 'conversion':

                if c.is_scalable():
                    base_investment.append(c.get_base_investment())
                    base_capacity.append(c.get_base_capacity())
                    scaling_factor.append(c.get_economies_of_scale())
                else:
                    base_investment.append('')
                    base_capacity.append('')
                    scaling_factor.append('')

                capex_basis = c.get_capex_basis()

                main_input = c.get_main_input()
                main_output = c.get_main_output()

                inputs = c.get_inputs()
                outputs = c.get_outputs()

                coefficient = outputs[main_output] / inputs[main_input]

                if capex_basis == 'input':
                    capex.append(self.all_variables_dict['investment'][c.get_name()] /
                                 self.all_variables_dict['nominal_cap'][c.get_name()])
                    commodity_name = self.pm_object.get_commodity(main_input).get_nice_name()
                    unit = self.pm_object.get_commodity(main_input).get_unit()
                else:
                    capex.append(self.all_variables_dict['investment'][c.get_name()] / (
                            self.all_variables_dict['nominal_cap'][c.get_name()] * coefficient))
                    commodity_name = self.pm_object.get_commodity(main_output).get_nice_name()
                    unit = self.pm_object.get_commodity(main_output).get_unit()

                if unit == 'MWh':
                    text_capex_unit = self.monetary_unit + ' / MW ' + commodity_name
                elif unit == 'kWh':
                    text_capex_unit = self.monetary_unit + ' / kW ' + commodity_name
                else:
                    text_capex_unit = self.monetary_unit + ' / ' + unit + ' ' + commodity_name + ' * h'

                capex_unit.append(text_capex_unit)

                if c.get_shut_down_ability():
                    start_up_costs.append(c.get_start_up_costs())
                else:
                    start_up_costs.append(0)

            elif c.component_type == 'storage':

                base_investment.append('')
                base_capacity.append('')
                scaling_factor.append('')

                capex.append(c.get_capex())
                commodity_name = self.pm_object.get_commodity(c.get_name()).get_nice_name()
                unit = self.pm_object.get_commodity(c.get_name()).get_unit()
                capex_unit.append(self.monetary_unit + ' / ' + unit + ' ' + commodity_name)

                start_up_costs.append(0)

            else:
                base_investment.append('')
                base_capacity.append('')
                scaling_factor.append('')

                capex.append(c.get_capex())
                unit = self.pm_object.get_commodity(c.get_generated_commodity()).get_unit()
                generated_commodity = self.pm_object.get_commodity(c.get_generated_commodity()).get_nice_name()

                if unit == 'MWh':
                    text_capex_unit = self.monetary_unit + ' / MW ' + generated_commodity
                elif unit == 'kWh':
                    text_capex_unit = self.monetary_unit + ' / kW ' + generated_commodity
                else:
                    text_capex_unit = self.monetary_unit + ' / ' + unit + ' ' + generated_commodity + ' * h'

                capex_unit.append(text_capex_unit)

                start_up_costs.append(0)

            maintenance.append(c.get_maintenance())

            applied_parameters = self.pm_object.get_all_applied_parameters()
            for ga in [*applied_parameters[c.get_name()].keys()]:
                if applied_parameters[c.get_name()][ga]:
                    if ga == 'taxes_and_insurance':
                        taxes_and_insurance.append(self.pm_object.get_general_parameter_value(ga))
                    elif ga == 'personnel_costs':
                        personnel.append(self.pm_object.get_general_parameter_value(ga))
                    elif ga == 'overhead':
                        overhead.append(self.pm_object.get_general_parameter_value(ga))
                    elif ga == 'working_capital':
                        working_capital.append(self.pm_object.get_general_parameter_value(ga))
                else:
                    if ga == 'taxes_and_insurance':
                        taxes_and_insurance.append(0)
                    elif ga == 'personnel_costs':
                        personnel.append(0)
                    elif ga == 'overhead':
                        overhead.append(0)
                    elif ga == 'working_capital':
                        working_capital.append(0)

            lifetime.append(c.get_lifetime())

        assumptions_df = pd.DataFrame(index=index_df)
        assumptions_df['Capex'] = capex
        assumptions_df['Capex Unit'] = capex_unit
        assumptions_df['Maintenance'] = maintenance
        assumptions_df['Taxes and Insurance'] = taxes_and_insurance
        assumptions_df['Personnel'] = personnel
        assumptions_df['Overhead'] = overhead
        assumptions_df['Working Capital'] = working_capital
        assumptions_df['Lifetime'] = lifetime
        assumptions_df['Start-Up Costs'] = start_up_costs

        assumptions_df.to_excel(self.new_result_folder + '/0_assumptions.xlsx')

    def create_and_print_vector(self, plots=False):

        """ Uses the created dataframes to plot the commodity vectors over time """

        variable_nice_names = {'mass_energy_purchase_commodity': 'Purchase',
                               'mass_energy_available': 'Freely Available',
                               'mass_energy_component_in_commodities': 'Input',
                               'mass_energy_component_out_commodities': 'Output',
                               'mass_energy_generation': 'Generation',
                               'mass_energy_total_generation': 'Total Generation',
                               'mass_energy_storage_in_commodities': 'Charging',
                               'mass_energy_storage_out_commodities': 'Discharging',
                               'soc': 'State of Charge',
                               'mass_energy_sell_commodity': 'Selling',
                               'mass_energy_emitted': 'Emitting',
                               'mass_energy_demand': 'Demand',
                               'mass_energy_hot_standby_demand': 'Hot Standby Demand'}

        time_depending_variables = {}

        # Two index vectors
        all_commodities = []
        for commodity in self.pm_object.get_final_commodities_objects():
            all_commodities.append(commodity.get_name())

        for variable_name in [*self.all_variables_dict]:

            if variable_name in self.variable_two_index:

                for commodity in [*self.all_variables_dict[variable_name]]:

                    if commodity not in all_commodities:
                        continue

                    if (variable_name == 'storage_charge_binary') | (variable_name == 'storage_discharge_binary'):
                        if self.all_variables_dict['nominal_cap'][commodity] == 0:
                            continue

                    list_values = self.all_variables_dict[variable_name][commodity]
                    unit = self.pm_object.get_commodity(commodity).get_unit()
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
                                      + self.pm_object.get_nice_name(commodity))

                            plt.savefig(self.new_result_folder + '/' + variable_nice_names[variable_name] + ' '
                                        + self.pm_object.get_nice_name(commodity) + '.png')
                            plt.close()

                        if variable_name in [*variable_nice_names.keys()]:
                            time_depending_variables[(variable_nice_names[variable_name], '',
                                                      self.pm_object.get_nice_name(commodity))] = list_values

            elif variable_name in self.variable_three_index:

                for c in [*self.all_variables_dict[variable_name]]:

                    if self.all_variables_dict['nominal_cap'][c] == 0:
                        continue

                    for commodity in [*self.all_variables_dict[variable_name][c]]:

                        if commodity not in all_commodities:
                            continue

                        list_values = self.all_variables_dict[variable_name][c][commodity]
                        unit = self.pm_object.get_commodity(commodity).get_unit()
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
                                          + self.pm_object.get_nice_name(commodity) + ' '
                                          + self.pm_object.get_nice_name(c))

                                plt.savefig(self.new_result_folder + '/' + variable_nice_names[variable_name] + ' '
                                            + self.pm_object.get_nice_name(commodity) + ' '
                                            + self.pm_object.get_nice_name(c) + '.png')
                                plt.close()

                            if variable_name in [*variable_nice_names.keys()]:
                                time_depending_variables[(variable_nice_names[variable_name],
                                                          self.pm_object.get_nice_name(c),
                                                          self.pm_object.get_nice_name(commodity))] = list_values

        # Create potential generation time series
        path = self.pm_object.get_path_data() + self.pm_object.get_profile_data()
        if path.split('.')[-1] == 'xlsx':
            generation_profile = pd.read_excel(path, index_col=0)
        else:
            generation_profile = pd.read_csv(path, index_col=0)

        for commodity in self.pm_object.get_final_commodities_objects():
            total_profile = []

            for generator in self.model.GENERATORS:
                generator_object = self.pm_object.get_component(generator)
                generated_commodity = self.pm_object.get_commodity(
                    generator_object.get_generated_commodity()).get_nice_name()

                if commodity.get_nice_name() == generated_commodity:
                    capacity = self.all_variables_dict['nominal_cap'][generator_object.get_name()]

                    if capacity > 0:
                        profile = capacity * generation_profile.loc[:, generator_object.get_nice_name()]
                        total_profile.append(profile)
                        time_depending_variables[
                            'Potential Generation', generator_object.get_nice_name(), commodity.get_nice_name()] \
                            = profile.loc[0:self.pm_object.get_covered_period()]

            if total_profile:

                first = True
                potential_profile = None
                for pr in total_profile:
                    if first:
                        potential_profile = pr
                        first = False
                    else:
                        potential_profile += pr

                time_depending_variables['Total Potential Generation', '', commodity.get_nice_name()] = potential_profile.tolist()[0:self.pm_object.get_covered_period()]

        ind = pd.MultiIndex.from_tuples([*time_depending_variables.keys()], names=('Variable', 'Component', 'Commodity'))
        self.time_depending_variables_df = pd.DataFrame(index=ind)
        self.time_depending_variables_df = self.time_depending_variables_df.sort_index()

        for key in [*time_depending_variables.keys()]:
            unit = self.pm_object.get_commodity(self.pm_object.get_abbreviation(key[2])).get_unit()
            if unit == 'MWh':
                unit = 'MW'
            elif unit == 'kWh':
                unit = 'kW'
            else:
                unit = unit + ' / h'
            self.time_depending_variables_df.loc[key, 'unit'] = unit
            for i, elem in enumerate(time_depending_variables[key]):
                self.time_depending_variables_df.loc[key, i] = elem

        for t in self.model.TIME:
            self.time_depending_variables_df.loc[('Weighting', '', ''), t] = self.model.weightings[t]

        # Sort index for better readability
        ordered_list = ['Weighting', 'Freely Available', 'Purchase', 'Emitting', 'Selling', 'Demand', 'Charging',
                        'Discharging', 'State of Charge', 'Total Potential Generation', 'Total Generation',
                        'Potential Generation', 'Generation', 'Input', 'Output', 'Hot Standby Demand']

        index_order = []
        for o in ordered_list:
            index = self.time_depending_variables_df[self.time_depending_variables_df.index.get_level_values(0) == o].index.tolist()
            if index:
                index_order += self.time_depending_variables_df[self.time_depending_variables_df.index.get_level_values(0) == o].index.tolist()

        self.time_depending_variables_df = self.time_depending_variables_df.reindex(index_order).round(3)
        self.time_depending_variables_df.to_excel(self.new_result_folder + '/5_time_series_commodities.xlsx')

    def analyze_commodities(self):

        # Calculate total commodity availability
        for commodity in self.model.ME_STREAMS:
            is_input = False
            for input_tuples in self.optimization_problem.input_tuples:
                if input_tuples[1] == commodity:
                    is_input = True

            difference = 0
            if commodity in self.model.STORAGES:
                # Due to charging and discharging efficiency, some mass or energy gets 'lost'. This has to be considered
                total_in = sum(self.all_variables_dict['mass_energy_storage_in_commodities'][commodity][t]
                               * self.model.weightings[t] for t in self.model.TIME)
                total_out = sum(self.all_variables_dict['mass_energy_storage_out_commodities'][commodity][t]
                                * self.model.weightings[t] for t in self.model.TIME)
                difference = total_in - total_out

            if is_input:
                self.total_availability[commodity] = (self.purchased_commodity[commodity] + self.total_generated_commodity[commodity]
                                                   + self.conversed_commodity[commodity] - self.emitted_commodity[commodity]
                                                   - self.sold_commodity[commodity] - difference)
            else:
                self.total_availability[commodity] = self.conversed_commodity[commodity]

        not_used_commodities = []
        for key in [*self.total_availability]:
            if self.total_availability[key] == 0:
                not_used_commodities.append(key)

        # Calculate the total cost of conversion. Important: conversion costs only occur for commodity, where
        # output is main commodity (E.g., electrolysis produces hydrogen and oxygen -> oxygen will not have conversion cost

        for commodity in self.model.ME_STREAMS:
            self.storage_costs.update({commodity: 0})
            self.storage_costs_per_unit.update({commodity: 0})
            self.generation_costs.update({commodity: 0})
            self.generation_costs_per_unit.update({commodity: 0})
            self.maintenance.update({commodity: 0})

            self.total_conversion_costs.update({commodity: 0})
            self.total_generation_costs.update({commodity: 0})

        # Get fix costs for each commodity
        for component in self.pm_object.get_final_conversion_components_objects():
            c = component.get_name()

            if component.get_shut_down_ability():
                start_up_costs = self.all_variables_dict['total_start_up_costs_component'][c]
            else:
                start_up_costs = 0

            out_commodity = component.get_main_output()
            self.total_conversion_costs[out_commodity] = (self.total_conversion_costs[out_commodity]
                                                       + self.all_variables_dict['annuity'][c]
                                                       + self.all_variables_dict['maintenance_costs'][c]
                                                       + self.all_variables_dict['taxes_and_insurance_costs'][c]
                                                       + self.all_variables_dict['personnel_costs'][c]
                                                       + self.all_variables_dict['overhead_costs'][c]
                                                       + self.all_variables_dict['working_capital_costs'][c]
                                                       + start_up_costs)
            self.conversion_component_costs[c] = (self.all_variables_dict['annuity'][c]
                                                  + self.all_variables_dict['maintenance_costs'][c]
                                                  + self.all_variables_dict['taxes_and_insurance_costs'][c]
                                                  + self.all_variables_dict['personnel_costs'][c]
                                                  + self.all_variables_dict['overhead_costs'][c]
                                                  + self.all_variables_dict['working_capital_costs'][c]
                                                  + start_up_costs)

        # Get annuity of storage units
        for commodity in self.model.STORAGES:
            self.storage_costs[commodity] = (self.all_variables_dict['annuity'][commodity]
                                          + self.all_variables_dict['maintenance_costs'][commodity]
                                          + self.all_variables_dict['taxes_and_insurance_costs'][commodity]
                                          + self.all_variables_dict['personnel_costs'][commodity]
                                          + self.all_variables_dict['overhead_costs'][commodity]
                                          + self.all_variables_dict['working_capital_costs'][commodity])

        # Get annuity of generation units
        for generator in self.model.GENERATORS:
            generated_commodity = self.pm_object.get_component(generator).get_generated_commodity()
            self.total_generation_costs[generated_commodity] = (self.total_generation_costs[generated_commodity]
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

        # COST DISTRIBUTION: Distribute the costs to each commodity
        # First: The intrinsic costs of each commodity.
        # Intrinsic costs include generation, storage, purchase and selling costs
        intrinsic_costs = {}
        intrinsic_costs_per_available_unit = {}
        for commodity in self.model.ME_STREAMS:
            intrinsic_costs[commodity] = round((self.total_generation_costs[commodity]
                                       + self.purchase_costs[commodity]
                                       + self.storage_costs[commodity]
                                       + self.selling_costs[commodity]), 4)

            # If intrinsic costs exist, distribute them on the total commodity available
            # Available commodity = Generated, Purchased, Conversed minus Sold, Emitted
            if intrinsic_costs[commodity] >= 0:
                if self.total_availability[commodity] == 0:
                    intrinsic_costs_per_available_unit[commodity] = 0
                else:
                    intrinsic_costs_per_available_unit[commodity] = (intrinsic_costs[commodity]
                                                                  / self.total_availability[commodity])
            elif intrinsic_costs[commodity] < 0:
                # If intrinsic costs are negative (due to selling of side products),
                # the total costs are distributed to the total commodity sold
                intrinsic_costs_per_available_unit[commodity] = (-intrinsic_costs[commodity]
                                                              / self.sold_commodity[commodity])

        if False:
            pd.DataFrame.from_dict(intrinsic_costs, orient='index').to_excel(
                self.new_result_folder + '/intrinsic_costs.xlsx')
            pd.DataFrame.from_dict(intrinsic_costs_per_available_unit, orient='index').to_excel(
                self.new_result_folder + '/intrinsic_costs_per_available_unit.xlsx')

        # Second: Next to intrinsic costs, conversion costs exist.
        # Each commodity, which is the main output of a conversion unit,
        # will be matched with the costs this conversion unit produces
        conversion_costs_per_conversed_unit = {}
        total_intrinsic_costs_per_available_unit = {}
        for component in self.pm_object.get_final_conversion_components_objects():
            component_name = component.get_name()
            main_output = component.get_main_output()

            # Components without capacity are not considered, as they don't converse anything
            if self.all_variables_dict['nominal_cap'][component_name] == 0:
                continue

            # Calculate the conversion costs per conversed unit
            conversion_costs_per_conversed_unit[component_name] = (self.conversion_component_costs[component_name]
                                                              / self.conversed_commodity_per_component[component_name][main_output])

            # To this conversion costs, the intrinsic costs of the commodity are added
            total_intrinsic_costs_per_available_unit[component_name] = (intrinsic_costs_per_available_unit[main_output]
                                                                   + conversion_costs_per_conversed_unit[component_name])

        if False:
            pd.DataFrame.from_dict(conversion_costs_per_conversed_unit, orient='index').to_excel(
                self.new_result_folder + '/conversion_costs_per_conversed_unit.xlsx')
            pd.DataFrame.from_dict(total_intrinsic_costs_per_available_unit, orient='index').to_excel(
                self.new_result_folder + '/total_intrinsic_costs_per_available_unit.xlsx')

        commodity_equations_constant = {}
        columns_index = [*self.pm_object.get_all_commodities().keys()]
        for s in self.pm_object.get_final_conversion_components_objects():
            component_name = s.get_name()
            if self.all_variables_dict['nominal_cap'][component_name] > 0:
                columns_index.append(component_name)

        coefficients_df = pd.DataFrame(index=columns_index, columns=columns_index)
        coefficients_df.fillna(value=0, inplace=True)

        main_outputs = []
        main_output_coefficients = {}
        for component in self.pm_object.get_final_conversion_components_objects():
            main_output = component.get_main_output()
            main_outputs.append(main_output)
            main_output_coefficients[component.get_main_output()] = component.get_outputs()[main_output]

        all_inputs = []
        final_commodity = None
        for component in self.pm_object.get_final_conversion_components_objects():
            component_name = component.get_name()
            inputs = component.get_inputs()
            outputs = component.get_outputs()
            main_output = component.get_main_output()

            if self.all_variables_dict['nominal_cap'][component_name] == 0:
                continue

            hot_standby_commodity = ''
            hot_standby_demand = 0
            if component.get_hot_standby_ability():
                hot_standby_commodity = [*component.get_hot_standby_demand().keys()][0]
                hot_standby_demand = (self.hot_standby_demand[component_name][hot_standby_commodity]
                                      / self.conversed_commodity_per_component[component_name][main_output])

            # First of all, associate inputs to components
            # If hot standby possible: input + hot standby demand -> hot standby demand prt conversed unit
            # If same commodity in input and output: input - output
            # If neither: just input
            for i in [*inputs.keys()]:  # commodity in input
                if i not in [*outputs.keys()]:  # commodity not in output
                    if component.get_hot_standby_ability():  # component has hot standby ability
                        if i != hot_standby_commodity:
                            coefficients_df.loc[i, component_name] = inputs[i]
                        else:
                            coefficients_df.loc[i, component_name] = inputs[i] + hot_standby_demand
                    else:  # component has no hot standby ability
                        coefficients_df.loc[i, component_name] = inputs[i]
                else:  # commodity in output
                    if (i in main_outputs) | (intrinsic_costs_per_available_unit[i] != 0):
                        if component.get_hot_standby_ability():    # component has hot standby ability
                            if i != hot_standby_commodity:  # hot standby commodity is not commodity
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

                if self.pm_object.get_commodity(o).is_demanded():
                    final_commodity = o

            coefficients_df.loc[component_name, component_name] = -1

        # Matching of costs, which do not influence demanded commodity directly (via inputs)
        # Costs of side commodities with no demand (e.g., flares to burn excess gases)
        # will be added to final commodity
        for component in self.pm_object.get_final_conversion_components_objects():
            main_output = self.pm_object.get_commodity(component.get_main_output())
            main_output_name = main_output.get_name()

            component_name = component.get_name()
            if self.all_variables_dict['nominal_cap'][component_name] == 0:
                continue

            if main_output_name not in all_inputs:  # Check if main output is input of other conversion
                if not main_output.is_demanded():  # Check if main output is demanded
                    coefficients_df.loc[component.get_name(), final_commodity] = 1

        # Each commodity, if main output, has its intrinsic costs and the costs of the conversion component
        for commodity in self.model.ME_STREAMS:
            for component in self.pm_object.get_final_conversion_components_objects():
                component_name = component.get_name()

                if self.all_variables_dict['nominal_cap'][component_name] == 0:
                    if commodity in main_outputs:
                        coefficients_df.loc[commodity, commodity] = -1
                    continue

                main_output = component.get_main_output()
                outputs = component.get_outputs()
                if commodity == main_output:
                    # ratio is when several components have same output
                    ratio = (self.conversed_commodity_per_component[component_name][commodity]
                             / self.conversed_commodity[commodity])
                    coefficients_df.loc[component_name, commodity] = 1 / outputs[commodity] * ratio

                    coefficients_df.loc[commodity, commodity] = -1

            if commodity not in main_outputs:
                coefficients_df.loc[commodity, commodity] = -1

        if False:
            coefficients_df.to_excel(self.new_result_folder + '/equations.xlsx')

        # Right hand side (constants)
        coefficients_dict = {}
        for column in coefficients_df.columns:
            coefficients_dict.update({column: coefficients_df[column].tolist()})
            if column in self.model.ME_STREAMS:
                if column in [main_output_coefficients.keys()]:
                    if False:
                        commodity_equations_constant.update({column: (-intrinsic_costs_per_available_unit[column]
                                                                   * main_output_coefficients[column])})
                    else:
                        commodity_equations_constant.update({column: -intrinsic_costs_per_available_unit[column]})
                else:
                    commodity_equations_constant.update({column: -intrinsic_costs_per_available_unit[column]})
            else:
                if self.all_variables_dict['nominal_cap'][column] == 0:
                    continue

                component = self.pm_object.get_component(column)
                main_output = component.get_main_output()
                commodity_equations_constant.update({column: (-conversion_costs_per_conversed_unit[column]
                                                           * main_output_coefficients[main_output])})

        if False:
            pd.DataFrame.from_dict(commodity_equations_constant, orient='index').to_excel(
                self.new_result_folder + '/commodity_equations_constant.xlsx')

        values_equations = coefficients_dict.values()
        A = np.array(list(values_equations))
        values_constant = commodity_equations_constant.values()
        B = np.array(list(values_constant))
        X = np.linalg.solve(A, B)

        for i, c in enumerate(columns_index):
            self.production_cost_commodity_per_unit.update({c: X[i]})

        commodities_and_costs = pd.DataFrame()
        dataframe_dict = {}

        for column in columns_index:

            if column in self.model.ME_STREAMS:
                commodity = column
                commodity_object = self.pm_object.get_commodity(commodity)
                nice_name = commodity_object.get_nice_name()
                commodities_and_costs.loc[nice_name, 'unit'] = commodity_object.get_unit()
                commodities_and_costs.loc[nice_name, 'MWh per unit'] = commodity_object.get_energy_content()

                commodities_and_costs.loc[nice_name, 'Available Commodity'] = self.available_commodity[commodity]
                commodities_and_costs.loc[nice_name, 'Emitted Commodity'] = self.emitted_commodity[commodity]
                commodities_and_costs.loc[nice_name, 'Purchased Commodity'] = self.purchased_commodity[commodity]
                commodities_and_costs.loc[nice_name, 'Sold Commodity'] = self.sold_commodity[commodity]
                commodities_and_costs.loc[nice_name, 'Generated Commodity'] = self.total_generated_commodity[commodity]
                commodities_and_costs.loc[nice_name, 'Stored Commodity'] = self.stored_commodity[commodity]
                commodities_and_costs.loc[nice_name, 'Conversed Commodity'] = self.conversed_commodity[commodity]
                commodities_and_costs.loc[nice_name, 'Total Commodity'] = self.total_availability[commodity]

                commodities_and_costs.loc[nice_name, 'Total Purchase Costs'] = self.purchase_costs[commodity]
                if self.purchased_commodity[commodity] > 0:
                    purchase_costs = self.purchase_costs[commodity] / self.purchased_commodity[commodity]
                    commodities_and_costs.loc[nice_name, 'Average Purchase Costs per purchased Unit'] = purchase_costs
                else:
                    commodities_and_costs.loc[nice_name, 'Average Purchase Costs per purchased Unit'] = 0

                commodities_and_costs.loc[nice_name, 'Total Selling Revenue/Disposal Costs'] = self.selling_costs[commodity]
                if self.sold_commodity[commodity] > 0:
                    revenue = self.selling_costs[commodity] / self.sold_commodity[commodity]
                    commodities_and_costs.loc[nice_name, 'Average Selling Revenue / Disposal Costs per sold/disposed Unit']\
                        = revenue
                else:
                    commodities_and_costs.loc[nice_name, 'Average Selling Revenue / Disposal Costs per sold/disposed Unit']\
                        = 0

                self.total_variable_costs[commodity] = self.purchase_costs[commodity] + self.selling_costs[commodity]
                commodities_and_costs.loc[nice_name, 'Total Variable Costs'] = self.total_variable_costs[commodity]

                commodities_and_costs.loc[nice_name, 'Total Generation Fix Costs'] = self.total_generation_costs[commodity]
                if self.total_generated_commodity[commodity] > 0:
                    commodities_and_costs.loc[nice_name, 'Costs per used unit'] \
                        = self.total_generation_costs[commodity] / (self.total_generated_commodity[commodity]
                                                                 - self.emitted_commodity[commodity])
                else:
                    commodities_and_costs.loc[nice_name, 'Costs per used unit'] = 0

                commodities_and_costs.loc[nice_name, 'Total Storage Fix Costs'] = self.storage_costs[commodity]
                if self.stored_commodity[commodity] > 0:
                    stored_costs = self.storage_costs[commodity] / self.stored_commodity[commodity]
                    commodities_and_costs.loc[nice_name, 'Total Storage Fix Costs per stored Unit'] = stored_costs
                else:
                    commodities_and_costs.loc[nice_name, 'Total Storage Fix Costs per stored Unit'] = 0

                commodities_and_costs.loc[nice_name, 'Total Conversion Fix Costs'] = self.total_conversion_costs[commodity]
                if self.conversed_commodity[commodity] > 0:
                    conversion_costs = self.total_conversion_costs[commodity] / self.conversed_commodity[commodity]
                    commodities_and_costs.loc[nice_name, 'Total Conversion Fix Costs per conversed Unit'] = conversion_costs
                else:
                    commodities_and_costs.loc[nice_name, 'Total Conversion Fix Costs per conversed Unit'] = 0

                self.total_fix_costs[commodity] \
                    = (self.total_conversion_costs[commodity] + self.storage_costs[commodity]
                       + self.total_generation_costs[commodity])
                commodities_and_costs.loc[nice_name, 'Total Fix Costs'] = self.total_fix_costs[commodity]

                self.total_costs[commodity] = self.total_variable_costs[commodity] + self.total_fix_costs[commodity]
                commodities_and_costs.loc[nice_name, 'Total Costs'] = self.total_costs[commodity]

                if self.total_availability[commodity] > 0:
                    commodities_and_costs.loc[nice_name, 'Total Costs per Unit'] \
                        = self.total_costs[commodity] / self.total_availability[commodity]
                else:
                    commodities_and_costs.loc[nice_name, 'Total Costs per Unit'] = 0

                if intrinsic_costs[commodity] >= 0:
                    commodities_and_costs.loc[nice_name, 'Production Costs per Unit'] \
                        = self.production_cost_commodity_per_unit[commodity]
                else:
                    commodities_and_costs.loc[nice_name, 'Production Costs per Unit'] \
                        = -self.production_cost_commodity_per_unit[commodity]

                commodities_and_costs.to_excel(self.new_result_folder + '/4_commodities.xlsx')
                self.commodities_and_costs = commodities_and_costs

            else:
                component_name = column
                component_nice_name = self.pm_object.get_nice_name(component_name)
                component = self.pm_object.get_component(component_name)

                main_output = component.get_main_output()
                main_output_nice_name = self.pm_object.get_nice_name(component.get_main_output())

                commodity_object = self.pm_object.get_commodity(main_output)
                unit = commodity_object.get_unit()

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
                    prod_costs = round(self.production_cost_commodity_per_unit[i], 3)
                    input_costs = round(self.production_cost_commodity_per_unit[i] * inputs[i]
                                        / main_output_coefficient, 3)

                    input_nice_name += ' (Input)'

                    components_and_costs.loc[(index, 'Coefficient'), input_nice_name] = in_coeff
                    components_and_costs.loc[(index, 'Cost per Unit'), input_nice_name] = prod_costs
                    components_and_costs.loc[(index, 'Total Costs'), input_nice_name] = input_costs

                    total_costs += input_costs

                    if i in [*outputs.keys()]:
                        # Handle output earlier s.t. its close to input of same commodity in excel file
                        output_nice_name = self.pm_object.get_nice_name(i)
                        out_coeff = round(outputs[i] / main_output_coefficient, 3)

                        # Three cases occur
                        # 1: The output commodity has a positive intrinsic value because it can be used again -> negative
                        # 2: The output can be sold with revenue -> negative
                        # 3: The output produces costs because the commodity needs to be disposed, for example -> positive

                        if self.selling_costs[i] > 0:  # Case 3
                            prod_costs = round(self.production_cost_commodity_per_unit[i], 3)
                            output_costs = round(self.production_cost_commodity_per_unit[i] * outputs[i]
                                                / main_output_coefficient, 3)
                        else:  # Case 1 & 2
                            prod_costs = - round(self.production_cost_commodity_per_unit[i], 3)
                            output_costs = - round(self.production_cost_commodity_per_unit[i] * outputs[i]
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
                        # 1: The output commodity has a positive intrinsic value because it can be used again -> negative
                        # 2: The output can be sold with revenue -> negative
                        # 3: The output produces costs because the commodity needs to be disposed, for example -> positive

                        if self.selling_costs[o] > 0:  # Case 3: Disposal costs exist
                            prod_costs = round(self.production_cost_commodity_per_unit[o], 3)
                            output_costs = round(self.production_cost_commodity_per_unit[o] * outputs[o]
                                                / main_output_coefficient, 3)
                        else:  # Case 1 & 2
                            prod_costs = - round(self.production_cost_commodity_per_unit[o], 3)
                            output_costs = - round(self.production_cost_commodity_per_unit[o] * outputs[o]
                                                  / main_output_coefficient, 3)

                        output_nice_name += ' (Output)'

                        components_and_costs.loc[(index, 'Coefficient'), output_nice_name] = out_coeff
                        components_and_costs.loc[(index, 'Cost per Unit'), output_nice_name] = prod_costs
                        components_and_costs.loc[(index, 'Total Costs'), output_nice_name] = output_costs

                        total_costs += output_costs

                # Further costs, which are not yet in commodity, need to be associated
                # In case that several components have same main output, costs are matched regarding share of production
                ratio = (self.conversed_commodity_per_component[component_name][main_output]
                         / self.conversed_commodity[main_output])

                if main_output in self.model.STORAGES:
                    column_name = 'Storage Costs'
                    components_and_costs.loc[(index, 'Coefficient'), column_name] = ratio
                    prod_costs = (self.storage_costs[main_output] / self.conversed_commodity[main_output])
                    components_and_costs.loc[(index, 'Cost per Unit'), column_name] = prod_costs
                    components_and_costs.loc[(index, 'Total Costs'), column_name] = prod_costs * ratio

                    total_costs += prod_costs * ratio

                if commodity_object.is_demanded():
                    for commodity in self.model.ME_STREAMS:
                        if (commodity not in all_inputs) & (commodity in main_outputs) & (commodity != main_output):
                            commodity_nice_name = self.pm_object.get_nice_name(commodity)

                            column_name = commodity_nice_name + ' (Associated Costs)'
                            components_and_costs.loc[(index, 'Coefficient'), column_name] = ratio
                            prod_costs = (self.production_cost_commodity_per_unit[commodity]
                                          * self.conversed_commodity[commodity]
                                          / self.conversed_commodity[main_output])
                            components_and_costs.loc[(index, 'Cost per Unit'), column_name] = prod_costs
                            components_and_costs.loc[(index, 'Total Costs'), column_name] = prod_costs * ratio

                            total_costs += prod_costs * ratio

                prod_costs = round(total_costs, 3)
                components_and_costs.loc[(index, 'Coefficient'), 'Final'] = ''
                components_and_costs.loc[(index, 'Cost per Unit'), 'Final'] = ''
                components_and_costs.loc[(index, 'Total Costs'), 'Final'] = prod_costs

                dataframe_dict[component_nice_name] = components_and_costs

            # Save dataframes in multi-sheet excel file
            if False:
                with pd.ExcelWriter(self.new_result_folder + '/main_output_costs.xlsx', engine="xlsxwriter") as writer:
                    for df in [*dataframe_dict.keys()]:
                        sheet_name = df.replace("Parallel Unit", "PU")
                        dataframe_dict[df].to_excel(writer, sheet_name)
                    writer.save()

    def analyze_components(self):

        columns = ['Capacity [input]', 'Capacity Unit [input]', 'Investment [per input]',
                   'Capacity [output]', 'Capacity Unit [output]', 'Investment [per output]', 'Full-load Hours',
                   'Total Investment', 'Annuity', 'Maintenance', 'Taxes and Insurance',
                   'Personnel', 'Overhead', 'Working Capital', 'Start-up Costs']

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
                capex_basis = component_object.get_capex_basis()

                main_input = component_object.get_main_input()
                commodity_object_input = self.pm_object.get_commodity(main_input)
                nice_name_commodity = commodity_object_input.get_nice_name()
                unit_input = commodity_object_input.get_unit()

                main_output = component_object.get_main_output()
                commodity_object_output = self.pm_object.get_commodity(main_output)
                nice_name_commodity_output = commodity_object_output.get_nice_name()
                unit_output = commodity_object_output.get_unit()

                inputs = component_object.get_inputs()
                outputs = component_object.get_outputs()

                if unit_input == 'MWh':
                    unit_input = 'MW ' + nice_name_commodity
                elif unit_input == 'kWh':
                    unit_input = 'kW ' + nice_name_commodity
                else:
                    unit_input = unit_input + ' ' + nice_name_commodity + ' / h'

                if unit_output == 'MWh':
                    unit_output = 'MW ' + nice_name_commodity_output
                elif unit_output == 'kWh':
                    unit_output = 'kW ' + nice_name_commodity_output
                else:
                    unit_output = unit_output + ' ' + nice_name_commodity_output + ' / h'

                coefficient = outputs[main_output] / inputs[main_input]

                capacity_df.loc[nice_name, 'Capacity Basis'] = capex_basis
                capacity_df.loc[nice_name, 'Capacity [input]'] = capacity
                capacity_df.loc[nice_name, 'Capacity Unit [input]'] = unit_input
                capacity_df.loc[nice_name, 'Investment [per input]'] = investment / capacity

                capacity_df.loc[nice_name, 'Capacity [output]'] = capacity * coefficient
                capacity_df.loc[nice_name, 'Capacity Unit [output]'] = unit_output
                capacity_df.loc[nice_name, 'Investment [per output]'] = investment / (capacity * coefficient)

                total_input_component = sum(self.time_depending_variables_df.loc[('Input',
                                                                                  nice_name,
                                                                                  nice_name_commodity), t]
                                       * self.model.weightings[t] for t in self.model.TIME)
                full_load_hours = total_input_component / (capacity * 8760) * 8760

                capacity_df.loc[nice_name, 'Full-load Hours'] = full_load_hours

                if component_object.get_shut_down_ability():
                    start_up_costs = self.all_variables_dict['total_start_up_costs_component'][key]
                else:
                    start_up_costs = 0

                capacity_df.loc[nice_name, 'Start-Up Costs'] = start_up_costs

            elif component_object.get_component_type() == 'generator':
                commodity_object = self.pm_object.get_commodity(component_object.get_generated_commodity())
                nice_name_commodity = commodity_object.get_nice_name()
                unit = commodity_object.get_unit()

                capacity_df.loc[nice_name, 'Capacity [output]'] = capacity
                if unit == 'MWh':
                    unit = 'MW ' + nice_name_commodity
                elif unit == 'kWh':
                    unit = 'kW ' + nice_name_commodity
                else:
                    unit = unit + ' ' + nice_name_commodity + ' / h'

                capacity_df.loc[nice_name, 'Capacity Unit [output]'] = unit

                capacity_df.loc[nice_name, 'Investment [per output]'] = investment / capacity

            else:
                nice_name += ' Storage'

                commodity_object = self.pm_object.get_commodity(key)
                nice_name_commodity = commodity_object.get_nice_name()
                unit = commodity_object.get_unit()

                capacity_df.loc[nice_name, 'Capacity [input]'] = capacity
                capacity_df.loc[nice_name, 'Capacity Unit [input]'] = unit + ' ' + nice_name_commodity

                capacity_df.loc[nice_name, 'Investment [per input]'] = investment / capacity

            capacity_df.loc[nice_name, 'Total Investment'] = investment
            capacity_df.loc[nice_name, 'Annuity'] = annuity
            capacity_df.loc[nice_name, 'Maintenance'] = maintenance
            capacity_df.loc[nice_name, 'Taxes and Insurance'] = taxes_and_insurance
            capacity_df.loc[nice_name, 'Personnel'] = personnel
            capacity_df.loc[nice_name, 'Overhead'] = overhead
            capacity_df.loc[nice_name, 'Working Capital'] = working_capital

        capacity_df.to_excel(self.new_result_folder + '/2_components.xlsx')

        # Calculate efficiency
        input_possibilities = ['Freely Available', 'Purchase', 'Generation']
        energy_input = 0  # in MWh
        for ip in input_possibilities:

            input_time_series = self.time_depending_variables_df.iloc[
                self.time_depending_variables_df.index.get_level_values('Variable') == ip]

            input_commodities = input_time_series.index.get_level_values(2)
            for i in input_commodities:
                energy_content = float(self.commodities_and_costs.loc[i, 'MWh per unit'])
                input_per_commodity = float(input_time_series.iloc[
                                       input_time_series.index.get_level_values('Commodity') == i].loc[
                                   :, 1:].sum().sum())

                energy_input_per_commodity = input_per_commodity * energy_content
                energy_input += energy_input_per_commodity

        if energy_input != 0:
            energy_output = 0
            output_time_series = self.time_depending_variables_df.iloc[
                self.time_depending_variables_df.index.get_level_values('Variable') == 'Demand']
            output_commodities = output_time_series.index.get_level_values(2)
            for o in output_commodities:
                energy_content = self.commodities_and_costs.loc[o, 'MWh per unit']
                output_per_commodity = output_time_series.iloc[
                                        output_time_series.index.get_level_values('Commodity') == o].loc[:,
                                    1:].sum().sum()

                energy_output_per_commodity = float(output_per_commodity) * float(energy_content)
                energy_output += energy_output_per_commodity

            efficiency = str(round(energy_output / energy_input, 4))
        else:
            efficiency = 0

        index_overview = ['Annual Production', 'Total Investment', 'Total Fix Costs', 'Total Variable Costs',
                          'Annual Costs', 'Production Costs per Unit', 'Efficiency']

        total_production = 0
        for commodity in [*self.all_variables_dict['mass_energy_demand'].keys()]:
            total_production += sum(self.all_variables_dict['mass_energy_demand'][commodity][t]
                                    * self.model.weightings[t] for t in self.model.TIME)

        total_investment = capacity_df['Total Investment'].sum()
        fix_costs = (capacity_df['Annuity'].sum() + capacity_df['Maintenance'].sum()
                     + capacity_df['Taxes and Insurance'].sum() + capacity_df['Personnel'].sum()
                     + capacity_df['Overhead'].sum() + capacity_df['Working Capital'].sum())

        variable_costs = 0
        for commodity in self.model.ME_STREAMS:
            if self.purchase_costs[commodity] != 0:
                variable_costs += self.purchase_costs[commodity]
            if self.selling_costs[commodity] != 0:
                variable_costs += self.selling_costs[commodity]

        variable_costs += self.all_variables_dict['total_start_up_costs']

        annual_costs = fix_costs + variable_costs
        production_costs_per_unit = annual_costs / total_production
        efficiency = efficiency

        results_overview = pd.Series([total_production, total_investment,
                                      fix_costs, variable_costs, annual_costs, production_costs_per_unit, efficiency])
        results_overview.index = index_overview

        results_overview.to_excel(self.new_result_folder + '/1_results_overview.xlsx')

    def analyze_generation(self):

        if len(self.model.GENERATORS) > 0:

            generation_df = pd.DataFrame(index=pd.Index([self.pm_object.get_component(s).get_nice_name()
                                                         for s in self.model.GENERATORS]))

            path = self.pm_object.get_path_data() + self.pm_object.get_profile_data()

            if path.split('.')[-1] == 'xlsx':
                generation_profile = pd.read_excel(path, index_col=0)
            else:
                generation_profile = pd.read_csv(path, index_col=0)

            covered_period = self.pm_object.get_covered_period()-1

            for generator in self.model.GENERATORS:

                generator_object = self.pm_object.get_component(generator)
                generator_nice_name = generator_object.get_nice_name()
                generated_commodity = self.pm_object.get_commodity(generator_object.get_generated_commodity()).get_nice_name()

                generator_profile = generation_profile.iloc[0:covered_period+1][generator_nice_name]

                investment = self.all_variables_dict['investment'][generator]
                capacity = self.all_variables_dict['nominal_cap'][generator]

                generation_df.loc[generator_nice_name, 'Generated Commodity'] = generated_commodity
                generation_df.loc[generator_nice_name, 'Capacity'] = capacity
                generation_df.loc[generator_nice_name, 'Investment'] = investment
                generation_df.loc[generator_nice_name, 'Annuity'] = self.all_variables_dict['annuity'][generator]
                generation_df.loc[generator_nice_name, 'Maintenance'] = self.all_variables_dict['maintenance_costs'][generator]
                generation_df.loc[generator_nice_name, 'Taxes and Insurance'] = self.all_variables_dict['taxes_and_insurance_costs'][generator]
                generation_df.loc[generator_nice_name, 'Overhead'] = self.all_variables_dict['overhead_costs'][generator]
                generation_df.loc[generator_nice_name, 'Personnel'] = self.all_variables_dict['personnel_costs'][generator]

                if capacity != 0:
                    potential_generation = sum(generator_profile.loc[generator_profile.index[t]] * self.model.weightings[t] for t in self.model.TIME) * capacity
                    generation_df.loc[generator_nice_name, 'Potential Generation'] = potential_generation
                    generation_df.loc[generator_nice_name, 'Potential Full-load Hours'] = potential_generation / (capacity * 8760) * 8760

                    generation_df.loc[generator_nice_name, 'LCOE before Curtailment'] = (generation_df.loc[generator_nice_name, 'Annuity']
                                                                               + generation_df.loc[generator_nice_name, 'Maintenance']
                                                                               + generation_df.loc[generator_nice_name, 'Taxes and Insurance']
                                                                               + generation_df.loc[generator_nice_name, 'Overhead']
                                                                               + generation_df.loc[generator_nice_name, 'Personnel']) / potential_generation

                    generation = self.generated_commodity[generator]
                    generation_df.loc[generator_nice_name, 'Actual Generation'] = generation
                    generation_df.loc[generator_nice_name, 'Actual Full-load Hours'] = generation / (capacity * 8760) * 8760

                    curtailment = potential_generation - generation
                    generation_df.loc[generator_nice_name, 'Curtailment'] = curtailment
                    generation_df.loc[generator_nice_name, 'LCOE after Curtailment'] = ((generation_df.loc[generator_nice_name, 'Annuity']
                                                                               + generation_df.loc[generator_nice_name, 'Maintenance']
                                                                               + generation_df.loc[generator_nice_name, 'Taxes and Insurance']
                                                                               + generation_df.loc[generator_nice_name, 'Overhead']
                                                                               + generation_df.loc[generator_nice_name, 'Personnel'])
                                                                              / generation)

                else:
                    potential_generation = sum(generator_profile.loc[generator_profile.index[t]] * self.model.weightings[t] for t in self.model.TIME)
                    generation_df.loc[generator_nice_name, 'Potential Generation'] = 0
                    generation_df.loc[generator_nice_name, 'Potential Full-load Hours'] = potential_generation

                    # Calculate potential LCOE
                    wacc = self.pm_object.get_general_parameter_value_dictionary()['wacc']
                    generator_object = self.pm_object.get_component(generator)
                    lifetime = generator_object.get_lifetime()
                    if lifetime != 0:
                        anf_component = (1 + wacc) ** lifetime * wacc \
                                        / ((1 + wacc) ** lifetime - 1)
                    else:
                        anf_component = 0

                    capex = generator_object.get_capex()
                    maintenance = generator_object.get_maintenance()
                    other_fix_costs = 0
                    for param in self.pm_object.get_general_parameters():
                        if param not in ['wacc', 'covered_period', 'representative_weeks']:
                            if self.pm_object.check_parameter_applied_for_component(param, generator_object.get_name()):
                                other_fix_costs += self.pm_object.get_general_parameter_value(param)

                    total_costs_1_capacity = capex * (anf_component + other_fix_costs + maintenance)

                    generation_df.loc[generator_nice_name, 'LCOE before Curtailment'] = total_costs_1_capacity / potential_generation

                    generation_df.loc[generator_nice_name, 'Actual Generation'] = 0
                    generation_df.loc[generator_nice_name, 'Actual Full-load Hours'] = 0

                    generation_df.loc[generator_nice_name, 'Curtailment'] = 0
                    generation_df.loc[generator_nice_name, 'LCOE after Curtailment'] = '-'

            generation_df.to_excel(self.new_result_folder + '/6_generation.xlsx')

    def analyze_total_costs(self):
        # Total costs: annuity, maintenance, buying and selling, taxes and insurance, etc.
        total_production = 0
        for commodity in [*self.all_variables_dict['mass_energy_demand'].keys()]:
            total_production += sum(self.all_variables_dict['mass_energy_demand'][commodity][t]
                                    * self.model.weightings[t] for t in self.model.TIME)

        cost_distribution = pd.DataFrame()
        total_costs = 0

        for key in self.all_variables_dict['nominal_cap']:
            component_object = self.pm_object.get_component(key)
            if component_object.get_component_type() != 'storage':
                nice_name = component_object.get_nice_name()
            else:
                nice_name = component_object.get_nice_name() + ' Storage'

            capacity = self.all_variables_dict['nominal_cap'][key]

            if capacity == 0:
                continue

            annuity = self.all_variables_dict['annuity'][key]
            cost_distribution.loc[nice_name + ' Annuity', 'Total'] = annuity
            total_costs += annuity

            maintenance = self.all_variables_dict['maintenance_costs'][key]
            if maintenance != 0:
                cost_distribution.loc[nice_name + ' Maintenance Costs', 'Total'] = self.all_variables_dict['maintenance_costs'][key]
                total_costs += maintenance

            taxes_and_insurance = self.all_variables_dict['taxes_and_insurance_costs'][key]
            if taxes_and_insurance != 0:
                cost_distribution.loc[nice_name + ' Taxes and Insurance Costs', 'Total'] = taxes_and_insurance
                total_costs += taxes_and_insurance

            personnel = self.all_variables_dict['personnel_costs'][key]
            if personnel != 0:
                cost_distribution.loc[nice_name + ' Personnel Costs', 'Total'] = personnel
                total_costs += personnel

            overhead = self.all_variables_dict['overhead_costs'][key]
            if overhead != 0:
                cost_distribution.loc[nice_name + ' Overhead Costs', 'Total'] = overhead
                total_costs += overhead

            working_capital = self.all_variables_dict['working_capital_costs'][key]
            if working_capital != 0:
                cost_distribution.loc[nice_name + ' Working Capital Costs', 'Total'] = working_capital
                total_costs += working_capital

            if component_object.get_component_type() == 'conversion':
                if component_object.get_shut_down_ability():
                    start_up_costs = self.all_variables_dict['total_start_up_costs_component'][key]
                    if start_up_costs != 0:
                        cost_distribution.loc[nice_name + ' Start-Up Costs', 'Total'] = start_up_costs
                        total_costs += working_capital

        for commodity in self.model.ME_STREAMS:
            if self.purchase_costs[commodity] != 0:
                cost_distribution.loc['Purchase Costs ' + self.pm_object.get_nice_name(commodity), 'Total'] \
                    = self.purchase_costs[commodity]
                total_costs += self.purchase_costs[commodity]

        for commodity in self.model.ME_STREAMS:
            if self.selling_costs[commodity] < 0:
                cost_distribution.loc['Disposal ' + self.pm_object.get_nice_name(commodity), 'Total'] \
                    = self.selling_costs[commodity]
                total_costs += self.selling_costs[commodity]

            if self.selling_costs[commodity] > 0:
                cost_distribution.loc['Revenue ' + self.pm_object.get_nice_name(commodity), 'Total'] \
                    = self.selling_costs[commodity]
                total_costs += self.selling_costs[commodity]

        cost_distribution.loc['Total', 'Total'] = total_costs

        cost_distribution.loc[:, 'Per Output'] = cost_distribution.loc[:, 'Total'] / total_production

        cost_distribution.loc[:, '%'] = cost_distribution.loc[:, 'Total'] / cost_distribution.loc['Total', 'Total']

        cost_distribution.to_excel(self.new_result_folder + '/3_cost_distribution.xlsx')

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

        if True:
            # Only for maintenance
            if len(time_depending_variables_df.index) > 0:
                time_depending_variables_df.to_excel(self.new_result_folder + '/time_series_binaries.xlsx')

    def build_sankey_diagram(self, only_energy=False, specific_commodity='Hydrogen', average_commodities=True,
                             specific_period=0):

        # todo: Add colors of commodity and options of method

        all_commodities = []
        for commodity in self.pm_object.get_final_commodities_objects():
            all_commodities.append(commodity.get_name())

        # Sankey Diagram are structured as nodes and links
        # Nodes: Dictionary with pad, thickness, line, label and color
        # Links: Dictionary with source, target, value, label and color

        average = True

        # Nodes will be implemented as following: Each component will be one node as well as the "bus" for each commodity
        labels = []
        label_indices = {}
        i = 0
        for component_object in self.pm_object.get_final_components_objects():
            if component_object.get_component_type() == 'conversion':
                labels.append(component_object.get_nice_name())
                label_indices[component_object.get_nice_name()] = i
            elif component_object.get_component_type() == 'generator':
                generated_commodity = component_object.get_generated_commodity()
                generated_commodity_nn = self.pm_object.get_commodity(generated_commodity).get_nice_name()
                labels.append(generated_commodity_nn + ' Generation')
                label_indices[generated_commodity_nn + ' Generation'] = i
            else:
                labels.append(component_object.get_nice_name() + ' Storage')
                label_indices[component_object.get_nice_name() + ' Storage'] = i
            i += 1

        for commodity_object in self.pm_object.get_final_commodities_objects():
            labels.append(commodity_object.get_nice_name() + ' Bus')
            label_indices[commodity_object.get_nice_name() + ' Bus'] = i
            i += 1

            labels.append(commodity_object.get_nice_name() + ' Freely Available')
            label_indices[commodity_object.get_nice_name() + ' Freely Available'] = i
            i += 1

            labels.append(commodity_object.get_nice_name() + ' Purchased')
            label_indices[commodity_object.get_nice_name() + ' Purchased'] = i
            i += 1

            labels.append(commodity_object.get_nice_name() + ' Generation')
            label_indices[commodity_object.get_nice_name() + ' Generation'] = i
            i += 1

            labels.append(commodity_object.get_nice_name() + ' Emitted')
            label_indices[commodity_object.get_nice_name() + ' Emitted'] = i
            i += 1

            labels.append(commodity_object.get_nice_name() + ' Sold')
            label_indices[commodity_object.get_nice_name() + ' Sold'] = i
            i += 1

        # Links
        sources = []
        targets = []
        link_value = []

        to_bus_commodities = ['mass_energy_purchase_commodity', 'mass_energy_available', 'mass_energy_component_out_commodities',
                          'mass_energy_generation', 'mass_energy_storage_out_commodities']
        from_bus_commodity = ['mass_energy_component_in_commodities', 'mass_energy_storage_in_commodities',
                           'mass_energy_sell_commodity', 'mass_energy_emitted']

        for variable_name in [*self.all_variables_dict]:

            if variable_name in self.variable_two_index:

                for commodity in [*self.all_variables_dict[variable_name]]:

                    if commodity not in all_commodities:
                        continue

                    commodity_object = self.pm_object.get_commodity(commodity)
                    commodity_name = commodity_object.get_nice_name()
                    unit = commodity_object.get_unit()

                    if only_energy:
                        if (unit != 'MWh') | (unit != 'kWh'):
                            continue

                    list_values = self.all_variables_dict[variable_name][commodity]

                    average_list_value = 0
                    if not average:
                        if (list_values[specific_period] is None) | (list_values[specific_period] == 0):
                            continue
                    else:
                        average_list_value = sum(list_values) / len(list_values)
                        if (average_list_value is None) | (average_list_value == 0):
                            continue

                    inside = False
                    if variable_name in to_bus_commodities:
                        if variable_name == 'mass_energy_available':
                            sources.append(label_indices[commodity_name + ' Freely Available'])
                            targets.append(label_indices[commodity_name + ' Bus'])
                        elif variable_name == 'mass_energy_purchase_commodity':
                            sources.append(label_indices[commodity_name + ' Purchased'])
                            targets.append(label_indices[commodity_name + ' Bus'])
                        elif variable_name == 'mass_energy_generation':
                            sources.append(label_indices[commodity_name + ' Generation'])
                            targets.append(label_indices[commodity_name + ' Bus'])
                        elif variable_name == 'mass_energy_storage_out_commodities':
                            sources.append(label_indices[commodity_name + ' Storage'])
                            targets.append(label_indices[commodity_name + ' Bus'])

                        inside = True

                    elif variable_name in from_bus_commodity:
                        if variable_name == 'mass_energy_sell_commodity':
                            sources.append(label_indices[commodity_name + ' Bus'])
                            targets.append(label_indices[commodity_name + ' Sold'])
                        elif variable_name == 'mass_energy_emitted':
                            sources.append(label_indices[commodity_name + ' Bus'])
                            targets.append(label_indices[commodity_name + ' Emitted'])
                        elif variable_name == 'mass_energy_storage_in_commodities':
                            sources.append(label_indices[commodity_name + ' Bus'])
                            targets.append(label_indices[commodity_name + ' Storage'])

                        inside = True

                    if inside:
                        if not average:
                            link_value.append(list_values[specific_period])
                        else:
                            link_value.append(average_list_value)

            elif variable_name in self.variable_three_index:

                for c in [*self.all_variables_dict[variable_name]]:

                    for commodity in [*self.all_variables_dict[variable_name][c]]:

                        if commodity not in all_commodities:
                            continue

                        component_object = self.pm_object.get_component(c)
                        component_name = component_object.get_nice_name()
                        commodity_object = self.pm_object.get_commodity(commodity)
                        commodity_name = commodity_object.get_nice_name()
                        unit = commodity_object.get_unit()

                        if only_energy:
                            if (unit != 'MWh') | (unit != 'kWh'):
                                continue

                        list_values = self.all_variables_dict[variable_name][c][commodity]

                        average_list_value = 0
                        if not average:
                            if (list_values[specific_period] is None) | (list_values[specific_period] == 0):
                                continue
                        else:
                            average_list_value = sum(list_values) / len(list_values)
                            if (average_list_value is None) | (average_list_value == 0):
                                continue

                        inside = False
                        if variable_name in to_bus_commodities:

                            if variable_name == 'mass_energy_component_out_commodities':
                                sources.append(label_indices[component_name])
                                targets.append(label_indices[commodity_name + ' Bus'])

                            inside = True

                        elif variable_name in from_bus_commodity:

                            if variable_name == 'mass_energy_component_in_commodities':
                                sources.append(label_indices[commodity_name + ' Bus'])
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

    def copy_input_data(self):
        import shutil
        if self.model.GENERATORS:

            path = self.pm_object.get_path_data() + self.pm_object.get_profile_data()

            if path.split('.')[-1] == 'xlsx':
                shutil.copy(path,
                            self.new_result_folder + '/8_profile_data.xlsx')
            else:
                shutil.copy(path,
                            self.new_result_folder + '/8_profile_data.csv')

    def __init__(self, optimization_problem, path_result):

        self.optimization_problem = optimization_problem
        self.model = optimization_problem.model
        self.instance = optimization_problem.instance
        self.pm_object = optimization_problem.pm_object
        self.file_name = self.pm_object.get_project_name()
        self.monetary_unit = self.pm_object.get_monetary_unit()

        now = datetime.now()
        dt_string = now.strftime("%Y%m%d_%H%M%S")
        if self.file_name is None:
            self.new_result_folder = path_result + dt_string
        else:
            self.new_result_folder = path_result + dt_string + '_' + self.file_name
        os.makedirs(self.new_result_folder)

        self.capacity_df = pd.DataFrame()
        self.financial_df = pd.DataFrame()
        self.annuity_df = pd.DataFrame()
        self.maintenance_df = pd.DataFrame()
        self.one_index_dict = {}
        self.two_index_dict = {}
        self.three_index_dict = {}
        self.available_commodity = {}
        self.emitted_commodity = {}
        self.conversed_commodity = {}
        self.conversed_commodity_per_component = {}
        self.purchased_commodity = {}
        self.purchase_costs = {}
        self.sold_commodity = {}
        self.selling_costs = {}
        self.stored_commodity = {}
        self.storage_costs = {}
        self.storage_costs_per_unit = {}
        self.generated_commodity = {}
        self.generation_costs = {}
        self.generation_costs_per_unit = {}
        self.conversion_component_costs = {}
        self.maintenance = {}
        self.total_fix_costs = {}
        self.total_variable_costs = {}
        self.total_costs = {}
        self.total_availability = {}
        self.production_cost_commodity_per_unit = {}

        self.total_conversion_costs = {}
        self.total_generation_costs = {}
        self.total_generated_commodity = {}

        self.hot_standby_demand = {}

        self.variable_zero_index = []
        self.variable_one_index = []
        self.variable_two_index = []
        self.variable_three_index = []
        self.all_variables_dict = {}

        self.time_depending_variables_df = None
        self.commodities_and_costs = None

        self.extracting_data()
        self.process_variables()
        self.create_assumptions_file()
        self.create_and_print_vector()
        self.analyze_commodities()
        self.analyze_components()
        self.analyze_generation()
        self.analyze_total_costs()
        self.check_integer_variables()
        self.copy_input_data()

        # self.build_sankey_diagram(only_energy=False)
