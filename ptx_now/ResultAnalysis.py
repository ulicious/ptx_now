import pandas as pd
from pyomo.core import *
import matplotlib.pyplot as plt
import numpy as np
import os

from _helpers_analysis import create_linear_system_of_equations

import plotly.graph_objects as go
from datetime import datetime


class ResultAnalysis:

    def extracting_data(self):

        for v in self.instance.component_objects(Var, active=True):

            variable_dict = v.extract_values()
            if not bool(variable_dict):
                continue

            self.all_variables_dict.update({str(v): variable_dict})

    def process_variables(self):

        """ Allocates costs to commodities """

        # Calculate the total availability of each commodity (purchase, from conversion, available)
        for commodity in self.model.COMMODITIES:
            self.purchased_commodity.update({commodity: 0})
            self.purchase_costs.update({commodity: 0})
            self.sold_commodity.update({commodity: 0})
            self.selling_costs.update({commodity: 0})
            self.available_commodity.update({commodity: 0})
            self.emitted_commodity.update({commodity: 0})
            self.stored_commodity.update({commodity: 0})
            self.conversed_commodity.update({commodity: 0})
            self.used_commodity.update({commodity: 0})
            self.total_generated_commodity.update({commodity: 0})

        for variable in self.commodity_three_index:
            if variable not in [*self.all_variables_dict.keys()]:
                continue

            variable_dict = self.all_variables_dict[variable]

            for k in [*variable_dict.keys()]:
                commodity = k[0]
                cluster = k[1]

                if variable_dict[k] is None:
                    continue

                if variable == 'mass_energy_available':
                    self.available_commodity[commodity] += variable_dict[k] * self.model.weightings[cluster]

                if variable == 'mass_energy_emitted':
                    self.emitted_commodity[commodity] += variable_dict[k] * self.model.weightings[cluster]

                if variable == 'mass_energy_purchase_commodity':
                    self.purchased_commodity[commodity] += variable_dict[k] * self.model.weightings[cluster]
                    self.purchase_costs[commodity] += variable_dict[k] * self.model.weightings[cluster] * self.model.purchase_price[k]

                if variable == 'mass_energy_sell_commodity':
                    self.sold_commodity[commodity] += variable_dict[k] * self.model.weightings[cluster]
                    self.selling_costs[commodity] += variable_dict[k] * self.model.weightings[cluster] * self.model.selling_price[k]

                if variable == 'mass_energy_storage_in_commodities':
                    self.stored_commodity[commodity] += variable_dict[k] * self.model.weightings[cluster]

                if variable == 'mass_energy_hot_standby_demand':
                    self.hot_standby_demand[commodity] += variable_dict[k] * self.model.weightings[cluster]

        self.conversed_commodity_per_component = {}
        self.generated_commodity_per_component = {}
        for variable in self.commodity_four_index:
            if variable not in [*self.all_variables_dict.keys()]:
                continue

            variable_dict = self.all_variables_dict[variable]

            for k in [*variable_dict.keys()]:
                component = k[0]
                commodity = k[1]
                cluster = k[2]

                if variable_dict[k] is None:
                    continue

                ratio = 1
                if component in self.model.CONVERSION_COMPONENTS:
                    if component not in [*self.conversed_commodity_per_component.keys()]:
                        self.conversed_commodity_per_component[component] = {}
                        self.used_commodity_per_component[component] = {}
                    if commodity not in [*self.conversed_commodity_per_component[component].keys()]:
                        self.conversed_commodity_per_component[component][commodity] = 0
                        self.used_commodity_per_component[component][commodity] = 0

                    # Check if commodity is fully conversed or parts of it remain
                    inputs = self.pm_object.get_component(component).get_inputs()
                    outputs = self.pm_object.get_component(component).get_outputs()
                    if (commodity in [*inputs.keys()]) & (commodity in [*outputs.keys()]):
                        ratio = outputs[commodity] / inputs[commodity]

                if component in self.model.GENERATORS:
                    if component not in [*self.generated_commodity_per_component.keys()]:
                        self.generated_commodity_per_component[component] = 0

                if variable == 'mass_energy_component_out_commodities':
                    self.conversed_commodity[commodity] += variable_dict[k] * self.model.weightings[cluster] * ratio
                    self.conversed_commodity_per_component[component][commodity] += variable_dict[k] * self.model.weightings[cluster] * ratio

                if variable == 'mass_energy_component_in_commodities':
                    self.used_commodity[commodity] += variable_dict[k] * self.model.weightings[cluster] * ratio
                    self.used_commodity_per_component[component][commodity] += variable_dict[k] * self.model.weightings[cluster] * ratio

                if variable == 'mass_energy_generation':
                    self.generated_commodity_per_component[component] += variable_dict[k] * self.model.weightings[cluster]
                    self.total_generated_commodity[commodity] += variable_dict[k] * self.model.weightings[cluster]

        for component in self.pm_object.get_final_components_objects():
            c = component.get_name()

            self.annualized_investment[c] = self.all_variables_dict['investment'][c] * self.model.ANF[c]
            self.fixed_costs[c] = self.all_variables_dict['investment'][c] * self.model.fixed_om[c]

            if component.get_component_type() == 'conversion':

                main_output = self.pm_object.get_component(c).get_main_output()
                self.variable_costs[c] = sum(self.all_variables_dict['mass_energy_component_out_commodities'][(c, main_output, cl, t)]
                                             * self.model.variable_om[c] * self.model.weightings[cl]
                                             for cl in self.model.CLUSTERS for t in self.model.TIME)

                if component.get_shut_down_ability():
                    self.start_up_costs[c] = sum(self.all_variables_dict['status_off_switch_off'][(c, cl, t)]
                                                 * self.model.weightings[cl] * self.model.start_up_costs[c]
                                                 for cl in self.model.CLUSTERS for t in self.model.TIME)
                else:
                    self.start_up_costs[c] = 0

            elif component.get_component_type() == 'storage':
                self.variable_costs[c] = sum(self.all_variables_dict['mass_energy_storage_in_commodities'][(c, cl, t)]
                                             * self.model.variable_om[c] * self.model.weightings[cl]
                                             for cl in self.model.CLUSTERS for t in self.model.TIME)

            else:

                generated_commodity = self.pm_object.get_component(c).get_generated_commodity()
                self.variable_costs[c] = sum(self.all_variables_dict['mass_energy_generation'][(c, generated_commodity, cl, t)]
                                     * self.model.variable_om[c] * self.model.weightings[cl]
                                     for cl in self.model.CLUSTERS for t in self.model.TIME)

    def create_assumptions_file(self):

        index_df = []
        base_investment = []
        base_capacity = []
        scaling_factor = []
        capex = []
        capex_unit = []
        fixed_om = []
        variable_om = []
        lifetime = []
        start_up_costs = []

        for c in self.pm_object.get_final_components_objects():

            if c.component_type == 'storage':
                index_df.append(c.get_name() + ' Storage')
            else:
                index_df.append(c.get_name())

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

                if self.all_variables_dict['nominal_cap'][c.get_name()] > 0:

                    if capex_basis == 'input':
                        capex.append(self.all_variables_dict['investment'][c.get_name()] /
                                     self.all_variables_dict['nominal_cap'][c.get_name()])
                        commodity_name = main_input
                        unit = self.pm_object.get_commodity(main_input).get_unit()
                    else:
                        capex.append(self.all_variables_dict['investment'][c.get_name()] / (
                                self.all_variables_dict['nominal_cap'][c.get_name()] * coefficient))
                        commodity_name = main_output
                        unit = self.pm_object.get_commodity(main_output).get_unit()

                else:
                    capex.append(0)
                    commodity_name = main_output
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
                commodity_name = c.get_name()
                unit = self.pm_object.get_commodity(c.get_name()).get_unit()
                capex_unit.append(self.monetary_unit + ' / ' + unit + ' ' + commodity_name)

                start_up_costs.append(0)

            else:
                base_investment.append('')
                base_capacity.append('')
                scaling_factor.append('')

                capex.append(c.get_capex())
                unit = self.pm_object.get_commodity(c.get_generated_commodity()).get_unit()
                generated_commodity = c.get_generated_commodity()

                if unit == 'MWh':
                    text_capex_unit = self.monetary_unit + ' / MW ' + generated_commodity
                elif unit == 'kWh':
                    text_capex_unit = self.monetary_unit + ' / kW ' + generated_commodity
                else:
                    text_capex_unit = self.monetary_unit + ' / ' + unit + ' ' + generated_commodity + ' * h'

                capex_unit.append(text_capex_unit)

                start_up_costs.append(0)

            fixed_om.append(c.get_fixed_OM())
            variable_om.append(c.get_variable_OM())
            lifetime.append(c.get_lifetime())

        assumptions_df = pd.DataFrame(index=index_df)
        assumptions_df['Capex'] = capex
        assumptions_df['Capex Unit'] = capex_unit
        assumptions_df['Fixed Operation and Maintenance'] = fixed_om
        assumptions_df['Variable Operation and Maintenance'] = variable_om
        assumptions_df['Lifetime'] = lifetime
        assumptions_df['Start-Up Costs'] = start_up_costs

        assumptions_df.to_excel(self.new_result_folder + '/0_assumptions.xlsx')

    def create_and_print_vector(self):

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

        list_values = {}
        for variable_name in [*self.all_variables_dict]:
            if variable_name in self.commodity_three_index:

                variable_dict = self.all_variables_dict[variable_name]

                for k in [*variable_dict.keys()]:
                    commodity = k[0]

                    if commodity not in all_commodities:
                        continue

                    if variable_dict[k] is None:
                        continue

                    # create vector from data
                    if variable_name not in [*list_values.keys()]:
                        list_values[variable_name] = {}

                    if commodity not in [*list_values[variable_name].keys()]:
                        list_values[variable_name][commodity] = []

                    list_values[variable_name][commodity].append(variable_dict[k])

        for variable_name in [*list_values.keys()]:
            for commodity in [*list_values[variable_name].keys()]:
                if sum(list_values[variable_name][commodity]) > 0:
                    if variable_name in [*variable_nice_names.keys()]:
                        time_depending_variables[(variable_nice_names[variable_name], '', commodity)] = list_values[variable_name][commodity]

        list_values = {}
        for variable_name in [*self.all_variables_dict]:
            if variable_name in self.commodity_four_index:
                variable_dict = self.all_variables_dict[variable_name]
                for k in [*variable_dict.keys()]:
                    component = k[0]
                    commodity = k[1]

                    if commodity not in all_commodities:
                        continue

                    if variable_dict[k] is None:
                        continue

                    # create vector from data
                    if variable_name not in [*list_values.keys()]:
                        list_values[variable_name] = {}

                    if component not in [*list_values[variable_name].keys()]:
                        list_values[variable_name][component] = {}

                    if commodity not in [*list_values[variable_name][component].keys()]:
                        list_values[variable_name][component][commodity] = []

                    list_values[variable_name][component][commodity].append(variable_dict[k])

        for variable_name in [*list_values.keys()]:
            for component in [*list_values[variable_name].keys()]:
                for commodity in [*list_values[variable_name][component].keys()]:
                    if sum(list_values[variable_name][component][commodity]) > 0:
                        if variable_name in [*variable_nice_names.keys()]:
                            time_depending_variables[(variable_nice_names[variable_name], component, commodity)] = list_values[variable_name][component][commodity]

        # Create potential generation time series
        if len(self.model.GENERATORS) > 0:
            path = self.pm_object.get_path_data() + self.pm_object.get_profile_data()
            if path.split('.')[-1] == 'xlsx':
                generation_profile = pd.read_excel(path, index_col=0)
            else:
                generation_profile = pd.read_csv(path, index_col=0)

            for commodity in self.pm_object.get_final_commodities_names():
                total_profile = []

                for generator in self.model.GENERATORS:
                    generator_object = self.pm_object.get_component(generator)
                    generated_commodity = generator_object.get_generated_commodity()

                    if commodity == generated_commodity:
                        capacity = self.all_variables_dict['nominal_cap'][generator_object.get_name()]

                        if capacity > 0:
                            profile = capacity * generation_profile.loc[:, generator_object.get_name()]
                            covered_index = profile.index[0:self.pm_object.get_covered_period()*self.pm_object.get_number_clusters()]
                            time_depending_variables[
                                'Potential Generation', generator_object.get_name(), commodity] \
                                = profile.loc[covered_index].tolist()

                            total_profile.append(profile)

                if total_profile:

                    first = True
                    potential_profile = None
                    for pr in total_profile:
                        if first:
                            potential_profile = pr.iloc[0:self.pm_object.get_covered_period() * self.pm_object.get_number_clusters()]
                            first = False
                        else:
                            potential_profile += pr.iloc[0:self.pm_object.get_covered_period() * self.pm_object.get_number_clusters()]

                    time_depending_variables[
                        'Total Potential Generation', '', commodity] = potential_profile.tolist()

        ind = pd.MultiIndex.from_tuples([*time_depending_variables.keys()],
                                        names=('Variable', 'Component', 'Commodity'))
        self.time_depending_variables_df = pd.DataFrame(index=ind)
        self.time_depending_variables_df = self.time_depending_variables_df.sort_index()

        for key in [*time_depending_variables.keys()]:
            unit = self.pm_object.get_commodity(key[2]).get_unit()
            if unit == 'MWh':
                unit = 'MW'
            elif unit == 'kWh':
                unit = 'kW'
            else:
                unit = unit + ' / h'
            self.time_depending_variables_df.loc[key, 'unit'] = unit
            t_range = range(self.pm_object.get_covered_period() * self.pm_object.get_number_clusters())
            self.time_depending_variables_df.loc[key, t_range] = time_depending_variables[key]

        i = 0
        weighting_list = []
        t_list = []
        for cl in self.model.CLUSTERS:
            for t in self.model.TIME:
                weighting_list.append(self.model.weightings[cl])
                t_list.append(i)
                i += 1
        self.time_depending_variables_df.loc[('Weighting', '', ''), t_list] = weighting_list

        # Sort index for better readability
        ordered_list = ['Weighting', 'Freely Available', 'Purchase', 'Emitting', 'Selling', 'Demand', 'Charging',
                        'Discharging', 'State of Charge', 'Total Potential Generation', 'Total Generation',
                        'Potential Generation', 'Generation', 'Input', 'Output', 'Hot Standby Demand']

        index_order = []
        for o in ordered_list:
            index = self.time_depending_variables_df[
                self.time_depending_variables_df.index.get_level_values(0) == o].index.tolist()
            if index:
                index_order += self.time_depending_variables_df[
                    self.time_depending_variables_df.index.get_level_values(0) == o].index.tolist()

        self.time_depending_variables_df = self.time_depending_variables_df.reindex(index_order).round(3)
        self.time_depending_variables_df.to_excel(self.new_result_folder + '/5_time_series_commodities.xlsx')

    def analyze_components(self):

        columns = ['Capacity [input]', 'Capacity Unit [input]', 'Investment [per input]',
                   'Capacity [output]', 'Capacity Unit [output]', 'Investment [per output]', 'Full-load Hours',
                   'Total Investment', 'Annuity', 'Fixed Operation and Maintenance', 'Variable Operation and Maintenance',
                   'Start-Up Costs']

        capacity_df = pd.DataFrame(columns=columns)
        for key in self.all_variables_dict['nominal_cap']:
            component_object = self.pm_object.get_component(key)
            component_name = key

            capacity = self.all_variables_dict['nominal_cap'][component_name]

            if capacity == 0:
                investment = 0
                annuity = 0
                fixed_om = 0
                variable_om = 0
            else:
                investment = self.all_variables_dict['investment'][key]
                annuity = self.annualized_investment[component_name]
                fixed_om = self.fixed_costs[component_name]
                variable_om = self.variable_costs[component_name]

            if component_object.get_component_type() == 'conversion':
                capex_basis = component_object.get_capex_basis()

                main_input = component_object.get_main_input()
                commodity_object_input = self.pm_object.get_commodity(main_input)
                name_commodity = main_input
                unit_input = commodity_object_input.get_unit()

                main_output = component_object.get_main_output()
                commodity_object_output = self.pm_object.get_commodity(main_output)
                name_commodity_output = main_output
                unit_output = commodity_object_output.get_unit()

                inputs = component_object.get_inputs()
                outputs = component_object.get_outputs()

                if unit_input == 'MWh':
                    unit_input = 'MW ' + name_commodity
                elif unit_input == 'kWh':
                    unit_input = 'kW ' + name_commodity
                else:
                    unit_input = unit_input + ' ' + name_commodity + ' / h'

                if unit_output == 'MWh':
                    unit_output = 'MW ' + name_commodity_output
                elif unit_output == 'kWh':
                    unit_output = 'kW ' + name_commodity_output
                else:
                    unit_output = unit_output + ' ' + name_commodity_output + ' / h'

                coefficient = outputs[main_output] / inputs[main_input]

                capacity_df.loc[component_name, 'Capacity Basis'] = capex_basis
                capacity_df.loc[component_name, 'Capacity [input]'] = capacity
                capacity_df.loc[component_name, 'Capacity Unit [input]'] = unit_input

                if capacity == 0:
                    capacity_df.loc[component_name, 'Investment [per input]'] = 0
                else:
                    capacity_df.loc[component_name, 'Investment [per input]'] = investment / capacity

                capacity_df.loc[component_name, 'Capacity [output]'] = capacity * coefficient
                capacity_df.loc[component_name, 'Capacity Unit [output]'] = unit_output

                if capacity == 0:
                    capacity_df.loc[component_name, 'Investment [per output]'] = 0
                else:
                    capacity_df.loc[component_name, 'Investment [per output]'] = investment / (capacity * coefficient)

                if capacity > 0:
                    total_input_component\
                        = sum(self.time_depending_variables_df.loc[('Input', component_name, name_commodity),
                                                                   t + cl*self.pm_object.get_covered_period()]
                              * self.model.weightings[cl] for cl in self.model.CLUSTERS for t in self.model.TIME)
                    full_load_hours = total_input_component / (capacity * 8760) * 8760

                else:
                    full_load_hours = 0

                capacity_df.loc[component_name, 'Full-load Hours'] = full_load_hours

                capacity_df.loc[component_name, 'Start-Up Costs'] = self.start_up_costs[key]

            elif component_object.get_component_type() == 'generator':
                commodity_object = self.pm_object.get_commodity(component_object.get_generated_commodity())
                name_commodity = commodity_object.get_name()
                unit = commodity_object.get_unit()

                capacity_df.loc[component_name, 'Capacity [output]'] = capacity
                if unit == 'MWh':
                    unit = 'MW ' + name_commodity
                elif unit == 'kWh':
                    unit = 'kW ' + name_commodity
                else:
                    unit = unit + ' ' + name_commodity + ' / h'

                capacity_df.loc[component_name, 'Capacity Unit [output]'] = unit

                if capacity == 0:
                    capacity_df.loc[component_name, 'Investment [per output]'] = 0
                else:
                    capacity_df.loc[component_name, 'Investment [per output]'] = investment / capacity

            else:
                component_name += ' Storage'

                commodity_object = self.pm_object.get_commodity(key)
                name_commodity = commodity_object.get_name()
                unit = commodity_object.get_unit()

                capacity_df.loc[component_name, 'Capacity [input]'] = capacity
                capacity_df.loc[component_name, 'Capacity Unit [input]'] = unit + ' ' + name_commodity

                if capacity == 0:
                    capacity_df.loc[component_name, 'Investment [per input]'] = 0
                else:
                    capacity_df.loc[component_name, 'Investment [per input]'] = investment / capacity

            capacity_df.loc[component_name, 'Total Investment'] = investment
            capacity_df.loc[component_name, 'Annuity'] = annuity
            capacity_df.loc[component_name, 'Fixed Operation and Maintenance'] = fixed_om
            capacity_df.loc[component_name, 'Variable Operation and Maintenance'] = variable_om

        capacity_df.to_excel(self.new_result_folder + '/2_components.xlsx')

        # Calculate efficiency
        total_energy_input = 0
        total_energy_output = 0
        for commodity in self.model.COMMODITIES:
            energy_content = float(self.commodities_and_costs.loc[commodity, 'MWh per unit'])

            if commodity in self.model.PURCHASABLE_COMMODITIES:
                purchased = self.purchased_commodity[commodity]
            else:
                purchased = 0

            if commodity in self.model.AVAILABLE_COMMODITIES:
                available = self.available_commodity[commodity]
            else:
                available = 0

            if commodity in self.model.GENERATED_COMMODITIES:
                generated = self.total_generated_commodity[commodity]
            else:
                generated = 0

            total_commodity_in = purchased + available + generated

            total_energy_input += total_commodity_in * energy_content

            if commodity in self.model.DEMANDED_COMMODITIES:
                conversed_commodity = self.conversed_commodity[commodity]
            else:
                conversed_commodity = 0

            if commodity in self.model.SALEABLE_COMMODITIES:
                sold = self.sold_commodity[commodity]
            else:
                sold = 0

            total_commodity_out = sold + conversed_commodity

            total_energy_output += total_commodity_out * energy_content

        efficiency = str(round(total_energy_output / total_energy_input, 4))

        index_overview = ['Annual Production', 'Total Investment', 'Total Fix Costs', 'Total Variable Costs',
                          'Annual Costs', 'Production Costs per Unit', 'Efficiency']

        total_production = 0
        total_production += sum(self.all_variables_dict['mass_energy_demand'][key]
                                * self.model.weightings[key[1]]
                                for key in [*self.all_variables_dict['mass_energy_demand'].keys()])

        total_investment = capacity_df['Total Investment'].sum()
        fix_costs = capacity_df['Annuity'].sum() + capacity_df['Fixed Operation and Maintenance'].sum()

        variable_costs = 0
        for commodity in self.model.COMMODITIES:
            if self.purchase_costs[commodity] != 0:
                variable_costs += self.purchase_costs[commodity]
            if self.selling_costs[commodity] != 0:
                variable_costs += self.selling_costs[commodity]

        variable_costs += (sum(self.start_up_costs[c] for c in self.model.SHUT_DOWN_COMPONENTS)
                           + sum(self.variable_costs[c] for c in self.model.COMPONENTS))

        annual_costs = fix_costs + variable_costs
        production_costs_per_unit = annual_costs / total_production
        efficiency = efficiency

        results_overview = pd.Series([total_production, total_investment,
                                      fix_costs, variable_costs, annual_costs, production_costs_per_unit, efficiency])
        results_overview.index = index_overview

        results_overview.to_excel(self.new_result_folder + '/1_results_overview.xlsx')

        self.exported_results['Production Costs'] = production_costs_per_unit

    def analyze_generation(self):

        if len(self.model.GENERATORS) > 0:

            generation_df = pd.DataFrame(index=pd.Index([s for s in self.model.GENERATORS]))

            path = self.pm_object.get_path_data() + self.pm_object.get_profile_data()

            if path.split('.')[-1] == 'xlsx':
                generation_profile = pd.read_excel(path, index_col=0)
            else:
                generation_profile = pd.read_csv(path, index_col=0)

            for generator in self.model.GENERATORS:

                generator_object = self.pm_object.get_component(generator)
                generator_name = generator
                generated_commodity = generator_object.get_generated_commodity()

                t_range = range(self.pm_object.get_covered_period() * self.pm_object.get_number_clusters())
                generator_profile = generation_profile.iloc[t_range][generator_name]

                investment = self.all_variables_dict['investment'][generator]
                capacity = self.all_variables_dict['nominal_cap'][generator]

                generation_df.loc[generator_name, 'Generated Commodity'] = generated_commodity
                generation_df.loc[generator_name, 'Capacity'] = capacity
                generation_df.loc[generator_name, 'Investment'] = investment
                generation_df.loc[generator_name, 'Annuity'] = self.annualized_investment[generator]
                generation_df.loc[generator_name, 'Fixed Operation and Maintenance'] = \
                    self.fixed_costs[generator]
                generation_df.loc[generator_name, 'Variable Operation and Maintenance'] = \
                    self.variable_costs[generator]

                if capacity != 0:
                    potential_generation = sum(
                        generator_profile.loc[generator_profile.index[t + cl*self.pm_object.get_covered_period()]] * self.model.weightings[cl]
                        for cl in self.model.CLUSTERS
                        for t in self.model.TIME) * capacity
                    generation_df.loc[generator_name, 'Potential Generation'] = potential_generation
                    generation_df.loc[generator_name, 'Potential Full-load Hours'] = potential_generation / (
                            capacity * 8760) * 8760

                    generation_df.loc[generator_name, 'LCOE before Curtailment'] = \
                        (generation_df.loc[generator_name, 'Annuity']
                         + generation_df.loc[generator_name, 'Fixed Operation and Maintenance']
                         + generation_df.loc[generator_name, 'Variable Operation and Maintenance']) \
                        / potential_generation

                    generation = self.generated_commodity_per_component[generator]
                    generation_df.loc[generator_name, 'Actual Generation'] = generation
                    generation_df.loc[generator_name, 'Actual Full-load Hours'] = generation / (
                            capacity * 8760) * 8760

                    curtailment = potential_generation - generation
                    generation_df.loc[generator_name, 'Curtailment'] = curtailment
                    generation_df.loc[generator_name, 'LCOE after Curtailment'] = \
                        (generation_df.loc[generator_name, 'Annuity']
                         + generation_df.loc[generator_name, 'Fixed Operation and Maintenance']
                         + generation_df.loc[generator_name, 'Variable Operation and Maintenance']) \
                        / generation

                else:

                    potential_generation = sum(
                        generator_profile.loc[generator_profile.index[t + cl*self.pm_object.get_covered_period()]] * self.model.weightings[cl]
                        for cl in self.model.CLUSTERS for t in self.model.TIME)
                    generation_df.loc[generator_name, 'Potential Generation'] = 0
                    generation_df.loc[generator_name, 'Potential Full-load Hours'] = potential_generation

                    # Calculate potential LCOE
                    wacc = self.pm_object.get_wacc()
                    generator_object = self.pm_object.get_component(generator)
                    lifetime = generator_object.get_lifetime()
                    if lifetime != 0:
                        anf_component = (1 + wacc) ** lifetime * wacc \
                                        / ((1 + wacc) ** lifetime - 1)
                    else:
                        anf_component = 0

                    capex = generator_object.get_capex()
                    fixed_om = generator_object.get_fixed_OM()
                    variable_om = generator_object.get_variable_OM()

                    total_costs_1_capacity = capex * (anf_component + fixed_om)

                    generation_df.loc[
                        generator_name, 'LCOE before Curtailment'] = total_costs_1_capacity / potential_generation + variable_om

                    generation_df.loc[generator_name, 'Actual Generation'] = 0
                    generation_df.loc[generator_name, 'Actual Full-load Hours'] = 0

                    generation_df.loc[generator_name, 'Curtailment'] = 0
                    generation_df.loc[generator_name, 'LCOE after Curtailment'] = '-'

            generation_df.to_excel(self.new_result_folder + '/6_generation.xlsx')

    def analyze_total_costs(self):
        # Total costs: annuity, maintenance, buying and selling, taxes and insurance, etc.
        total_production = 0
        for key in [*self.all_variables_dict['mass_energy_demand'].keys()]: # todo: demand stimmt nicht
            total_production += self.all_variables_dict['mass_energy_demand'][key] * self.model.weightings[key[1]]

        cost_distribution = pd.DataFrame()
        total_costs = 0

        for key in self.all_variables_dict['nominal_cap']:
            component_object = self.pm_object.get_component(key)
            if component_object.get_component_type() != 'storage':
                component_name = key
            else:
                component_name = key + ' Storage'

            capacity = self.all_variables_dict['nominal_cap'][key]

            if capacity == 0:
                continue

            annuity = self.annualized_investment[key]
            cost_distribution.loc[component_name + ' Annuity', 'Total'] = annuity
            total_costs += annuity

            fixed_om_costs = self.fixed_costs[key]
            if fixed_om_costs != 0:
                cost_distribution.loc[component_name + ' Fixed Operation and Maintenance Costs', 'Total'] = \
                    fixed_om_costs
                total_costs += fixed_om_costs

            variable_om_costs = self.variable_costs[key]
            if fixed_om_costs != 0:
                cost_distribution.loc[component_name + ' Variable Operation and Maintenance Costs', 'Total'] = \
                    variable_om_costs
                total_costs += variable_om_costs

            if component_object.get_component_type() == 'conversion':
                if component_object.get_shut_down_ability():
                    start_up_costs = self.start_up_costs[key]
                    if start_up_costs != 0:
                        cost_distribution.loc[component_name + ' Start-Up Costs', 'Total'] = start_up_costs
                        total_costs += start_up_costs

        for commodity in self.model.COMMODITIES:
            if self.purchase_costs[commodity] != 0:
                cost_distribution.loc['Purchase Costs ' + commodity, 'Total'] \
                    = self.purchase_costs[commodity]
                total_costs += self.purchase_costs[commodity]

        for commodity in self.model.COMMODITIES:
            if self.selling_costs[commodity] < 0:
                cost_distribution.loc['Disposal ' + commodity, 'Total'] \
                    = self.selling_costs[commodity]
                total_costs += self.selling_costs[commodity]

            if self.selling_costs[commodity] > 0:
                cost_distribution.loc['Revenue ' + commodity, 'Total'] \
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
        list_values = {}
        for variable_name in self.status_variables:

            if variable_name not in [*self.all_variables_dict.keys()]:
                continue

            for key in [*self.all_variables_dict[variable_name].keys()]:

                c = key[0]

                if self.all_variables_dict['nominal_cap'][c] == 0:
                    continue

                if variable_name not in [*list_values.keys()]:
                    list_values[variable_name] = {}

                if c not in [*list_values[variable_name].keys()]:
                    list_values[variable_name][c] = []

                list_values[variable_name][c].append(self.all_variables_dict[variable_name][key])

        for variable_name in [*list_values.keys()]:
            for component in [*list_values[variable_name].keys()]:
                time_depending_variables[(variable_name, component)] = list_values

        ind = pd.MultiIndex.from_tuples([*time_depending_variables.keys()], names=('Variable', 'Component'))
        time_depending_variables_df = pd.DataFrame(index=ind)
        time_depending_variables_df = time_depending_variables_df.sort_index()

        for key in [*time_depending_variables.keys()]:
            for i, elem in enumerate(time_depending_variables[key]):
                time_depending_variables_df.loc[key, i] = elem

        if False:
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
                labels.append(component_object.get_name())
                label_indices[component_object.get_name()] = i
            elif component_object.get_component_type() == 'generator':
                generated_commodity = component_object.get_generated_commodity()
                generated_commodity_nn = self.pm_object.get_commodity(generated_commodity).get_name()
                labels.append(generated_commodity_nn + ' Generation')
                label_indices[generated_commodity_nn + ' Generation'] = i
            else:
                labels.append(component_object.get_name() + ' Storage')
                label_indices[component_object.get_name() + ' Storage'] = i
            i += 1

        for commodity_object in self.pm_object.get_final_commodities_objects():
            labels.append(commodity_object.get_name() + ' Bus')
            label_indices[commodity_object.get_name() + ' Bus'] = i
            i += 1

            labels.append(commodity_object.get_name() + ' Freely Available')
            label_indices[commodity_object.get_name() + ' Freely Available'] = i
            i += 1

            labels.append(commodity_object.get_name() + ' Purchased')
            label_indices[commodity_object.get_name() + ' Purchased'] = i
            i += 1

            labels.append(commodity_object.get_name() + ' Generation')
            label_indices[commodity_object.get_name() + ' Generation'] = i
            i += 1

            labels.append(commodity_object.get_name() + ' Emitted')
            label_indices[commodity_object.get_name() + ' Emitted'] = i
            i += 1

            labels.append(commodity_object.get_name() + ' Sold')
            label_indices[commodity_object.get_name() + ' Sold'] = i
            i += 1

        # Links
        sources = []
        targets = []
        link_value = []

        to_bus_commodities = ['mass_energy_purchase_commodity', 'mass_energy_available',
                              'mass_energy_component_out_commodities',
                              'mass_energy_generation', 'mass_energy_storage_out_commodities']
        from_bus_commodity = ['mass_energy_component_in_commodities', 'mass_energy_storage_in_commodities',
                              'mass_energy_sell_commodity', 'mass_energy_emitted']

        for variable_name in [*self.all_variables_dict]:

            if variable_name in self.variable_two_index:

                for commodity in [*self.all_variables_dict[variable_name]]:

                    if commodity not in all_commodities:
                        continue

                    commodity_object = self.pm_object.get_commodity(commodity)
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
                            sources.append(label_indices[commodity + ' Freely Available'])
                            targets.append(label_indices[commodity + ' Bus'])
                        elif variable_name == 'mass_energy_purchase_commodity':
                            sources.append(label_indices[commodity + ' Purchased'])
                            targets.append(label_indices[commodity + ' Bus'])
                        elif variable_name == 'mass_energy_generation':
                            sources.append(label_indices[commodity + ' Generation'])
                            targets.append(label_indices[commodity + ' Bus'])
                        elif variable_name == 'mass_energy_storage_out_commodities':
                            sources.append(label_indices[commodity + ' Storage'])
                            targets.append(label_indices[commodity + ' Bus'])

                        inside = True

                    elif variable_name in from_bus_commodity:
                        if variable_name == 'mass_energy_sell_commodity':
                            sources.append(label_indices[commodity + ' Bus'])
                            targets.append(label_indices[commodity + ' Sold'])
                        elif variable_name == 'mass_energy_emitted':
                            sources.append(label_indices[commodity + ' Bus'])
                            targets.append(label_indices[commodity + ' Emitted'])
                        elif variable_name == 'mass_energy_storage_in_commodities':
                            sources.append(label_indices[commodity + ' Bus'])
                            targets.append(label_indices[commodity + ' Storage'])

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

                        commodity_object = self.pm_object.get_commodity(commodity)
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
                                sources.append(label_indices[c])
                                targets.append(label_indices[commodity + ' Bus'])

                            inside = True

                        elif variable_name in from_bus_commodity:

                            if variable_name == 'mass_energy_component_in_commodities':
                                sources.append(label_indices[commodity + ' Bus'])
                                targets.append(label_indices[c])

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

        self.status_variables = ['status_on', 'status_off', 'status_off_switch_on', 'status_off_switch_off',
                            'status_standby_switch_on', 'status_standby_switch_off', 'status_standby',
                            'storage_charge_binary', 'storage_discharge_binary']

        self.component_financial_one_index = ['nominal_cap', 'investment']

        self.commodity_four_index = ['mass_energy_component_in_commodities', 'mass_energy_component_out_commodities',
                                'mass_energy_generation']

        self.commodity_three_index = ['mass_energy_available', 'mass_energy_emitted',
                                 'mass_energy_storage_in_commodities',
                                 'mass_energy_storage_out_commodities', 'soc', 'mass_energy_sell_commodity',
                                 'mass_energy_purchase_commodity', 'mass_energy_demand',
                                 'mass_energy_hot_standby_demand']

        self.exported_results = {}

        now = datetime.now()
        dt_string = now.strftime("%Y%m%d_%H%M%S")

        profile_name = ''
        if self.pm_object.get_profile_data():
            if self.pm_object.get_single_or_multiple_profiles() == 'multiple':
                profile_name = self.pm_object.get_profile_data().split('/')[1].split('.')[0]
            else:
                profile_name = self.pm_object.get_profile_data().split('.')[0]

        if self.file_name is None:
            self.new_result_folder = path_result + dt_string + profile_name
        else:
            self.new_result_folder = path_result + dt_string + '_' + self.file_name + '_' + profile_name
        os.makedirs(self.new_result_folder)

        self.capacity_df = pd.DataFrame()
        self.financial_df = pd.DataFrame()
        self.annuity_df = pd.DataFrame()
        self.maintenance_df = pd.DataFrame()
        self.available_commodity = {}
        self.emitted_commodity = {}
        self.conversed_commodity = {}
        self.conversed_commodity_per_component = {}
        self.used_commodity = {}
        self.used_commodity_per_component = {}
        self.purchased_commodity = {}
        self.purchase_costs = {}
        self.sold_commodity = {}
        self.selling_costs = {}
        self.stored_commodity = {}
        self.storage_costs = {}
        self.storage_costs_per_unit = {}
        self.generated_commodity_per_component = {}
        self.generation_costs = {}
        self.generation_costs_per_unit = {}
        self.conversion_component_costs = {}

        self.annualized_investment = {}
        self.fixed_costs = {}
        self.variable_costs = {}
        self.start_up_costs = {}

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
        create_linear_system_of_equations(self)
        self.analyze_components()
        self.analyze_generation()
        self.analyze_total_costs()
        # self.check_integer_variables()
        self.copy_input_data()

        # self.build_sankey_diagram(only_energy=False)
