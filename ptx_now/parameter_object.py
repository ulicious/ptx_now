import pandas as pd
import copy

from components import ConversionComponent
from commodity import Commodity

import numpy as np
import matplotlib.pyplot as plt

from sklearn.linear_model import LinearRegression

import math

idx = pd.IndexSlice


class ParameterObject:

    def set_nice_name(self, abbreviation, nice_name):
        self.nice_names.update({abbreviation: nice_name})

    def get_nice_name(self, abbreviation):
        return self.nice_names[abbreviation]

    def set_abbreviation(self, nice_name, abbreviation):
        self.abbreviations_dict.update({nice_name: abbreviation})

    def get_abbreviation(self, nice_name):
        return self.abbreviations_dict[nice_name]

    def get_all_abbreviations(self):
        return [*self.nice_names.keys()]

    def set_general_parameter_value(self, parameter, value):
        self.general_parameter_values.update({parameter: float(value)})

    def get_general_parameter_value(self, parameter):
        return self.general_parameter_values[parameter]

    def get_general_parameter_value_dictionary(self):
        return self.general_parameter_values

    def set_general_parameter(self, parameter):
        if parameter not in self.general_parameters:
            self.general_parameters.append(parameter)

            if parameter not in ['wacc', 'covered_period', 'representative_weeks']:
                self.applied_parameter_for_component[parameter] = {}

    def get_general_parameters(self):
        return self.general_parameters

    def set_applied_parameter_for_component(self, general_parameter, component, status):
        if general_parameter not in ['wacc', 'covered_period', 'representative_weeks']:
            self.applied_parameter_for_component[general_parameter][component] = status

    def set_all_applied_parameters(self, applied_parameters):
        self.applied_parameter_for_component = applied_parameters

    def get_applied_parameter_for_component(self, general_parameter, component):
        return self.applied_parameter_for_component[general_parameter][component]

    def get_all_applied_parameters(self):
        return self.applied_parameter_for_component

    def get_annuity_factor(self):
        """ Setting time-dependent parameters"""

        # Calculate annuity factor of each component
        wacc = self.get_general_parameter_value_dictionary()['wacc']
        annuity_factor_dict = {}
        for c in self.get_final_components_objects():
            lifetime = c.get_lifetime()
            if lifetime != 0:
                anf_component = (1 + wacc) ** lifetime * wacc \
                                / ((1 + wacc) ** lifetime - 1)
                annuity_factor_dict.update({c.get_name(): anf_component})
            else:
                annuity_factor_dict.update({c.get_name(): 0})

        return annuity_factor_dict

    def add_component(self, abbreviation, component):
        self.components.update({abbreviation: component})
        self.set_nice_name(abbreviation, component.get_nice_name())
        self.set_abbreviation(component.get_nice_name(), abbreviation)

        self.applied_parameter_for_component[abbreviation] = {'taxes_and_insurance': True,
                                                              'personnel_costs': True,
                                                              'overhead': True,
                                                              'working_capital': True}

    def get_all_component_names(self):
        return [*self.components.keys()]

    def get_all_components(self):
        components = []
        for c in self.get_all_component_names():
            components.append(self.get_component(c))
        return components

    def get_component(self, name):
        return self.components[name]

    def remove_component_entirely(self, name):
        self.components.pop(name)

    def get_component_by_nice_name(self, nice_name):
        abbreviation = self.get_abbreviation(nice_name)
        return self.get_component(abbreviation)

    def get_final_components_names(self):
        final_components_names = []
        all_components = self.get_all_component_names()
        for c in all_components:
            if self.get_component(c).is_final():
                final_components_names.append(self.get_component(c).get_name())

        return final_components_names

    def get_final_components_objects(self):
        final_components = []
        all_components = self.get_all_component_names()
        for c in all_components:
            if self.get_component(c).is_final():
                final_components.append(self.get_component(c))

        return final_components

    def get_conversion_components_names(self):
        conversion_components_names = []
        for c in self.get_all_component_names():
            if self.get_component(c).get_component_type() == 'conversion':
                conversion_components_names.append(self.get_component(c).get_name())

        return conversion_components_names

    def get_conversion_components_objects(self):
        conversion_components_objects = []
        for c in self.get_all_component_names():
            if self.get_component(c).get_component_type() == 'conversion':
                conversion_components_objects.append(self.get_component(c))

        return conversion_components_objects

    def get_storage_components_names(self):
        storage_components_names = []
        all_components = self.get_all_component_names()
        for c in all_components:
            if self.get_component(c).get_component_type() == 'storage':
                storage_components_names.append(self.get_component(c).get_name())

        return storage_components_names

    def get_storage_components_objects(self):
        storage_components_objects = []
        all_components = self.get_all_component_names()
        for c in all_components:
            if self.get_component(c).get_component_type() == 'storage':
                storage_components_objects.append(self.get_component(c))

        return storage_components_objects

    def get_generator_components_names(self):
        generator_components_names = []
        all_components = self.get_all_component_names()
        for c in all_components:
            if self.get_component(c).get_component_type() == 'generator':
                generator_components_names.append(self.get_component(c).get_name())

        return generator_components_names

    def get_generator_components_objects(self):
        generator_components_objects = []
        all_components = self.get_all_component_names()
        for c in all_components:
            if self.get_component(c).get_component_type() == 'generator':
                generator_components_objects.append(self.get_component(c))

        return generator_components_objects

    def get_final_conversion_components_names(self):
        final_components = self.get_final_components_names()
        conversion_components = self.get_conversion_components_names()

        final_components_as_set = set(final_components)
        final_conversion_components = final_components_as_set.intersection(conversion_components)
        final_conversion_components = list(final_conversion_components)

        return final_conversion_components

    def get_final_conversion_components_objects(self):

        final_conversion_components_objects = []
        for c in self.get_final_conversion_components_names():
            final_conversion_components_objects.append(self.get_component(c))

        return final_conversion_components_objects

    def get_final_scalable_conversion_components_names(self):
        final_scalable_conversion_components_names = []
        for c in self.get_final_conversion_components_objects():
            if c.is_scalable():
                final_scalable_conversion_components_names.append(c.get_name())

        return final_scalable_conversion_components_names

    def get_final_scalable_conversion_components_objects(self):
        final_scalable_conversion_components_objects = []
        for c in self.get_final_conversion_components_objects():
            if c.is_scalable():
                final_scalable_conversion_components_objects.append(c)

        return final_scalable_conversion_components_objects

    def get_final_shut_down_conversion_components_names(self):
        final_shutdown_conversion_components_names = []
        for c in self.get_final_conversion_components_objects():
            if c.get_shut_down_ability():
                final_shutdown_conversion_components_names.append(c.get_name())

        return final_shutdown_conversion_components_names

    def get_final_shut_down_conversion_components_objects(self):
        final_shutdown_conversion_components_objects = []
        for c in self.get_final_conversion_components_objects():
            if c.get_shut_down_ability():
                final_shutdown_conversion_components_objects.append(c)

        return final_shutdown_conversion_components_objects

    def get_final_standby_conversion_components_names(self):
        final_standby_conversion_components_names = []
        for c in self.get_final_conversion_components_objects():
            if c.get_hot_standby_ability():
                final_standby_conversion_components_names.append(c.get_name())

        return final_standby_conversion_components_names

    def get_final_standby_conversion_components_objects(self):
        final_standby_conversion_components_objects = []
        for c in self.get_final_conversion_components_objects():
            if c.get_hot_standby_ability():
                final_standby_conversion_components_objects.append(c)

        return final_standby_conversion_components_objects

    def get_final_storage_components_names(self):
        final_components = self.get_final_components_names()
        storage_components = self.get_storage_components_names()

        final_components_as_set = set(final_components)
        final_storage_components = final_components_as_set.intersection(storage_components)
        final_storage_components = list(final_storage_components)

        return final_storage_components

    def get_final_storage_components_objects(self):

        final_storage_components_objects = []
        for c in self.get_final_storage_components_names():
            final_storage_components_objects.append(self.get_component(c))

        return final_storage_components_objects

    def get_final_generator_components_names(self):
        final_components = self.get_final_components_names()
        generator_components = self.get_generator_components_names()

        generator_components_as_set = set(final_components)
        final_generator_components = generator_components_as_set.intersection(generator_components)
        final_generator_components = list(final_generator_components)

        return final_generator_components

    def get_final_generator_components_objects(self):

        final_generator_components_objects = []
        for c in self.get_final_generator_components_names():
            final_generator_components_objects.append(self.get_component(c))

        return final_generator_components_objects

    def get_final_commodities_names(self):
        final_commodities = []
        for commodity in self.get_all_commodities():
            if self.get_commodity(commodity).is_final():
                final_commodities.append(self.get_commodity(commodity).get_nice_name())

        return final_commodities

    def get_final_commodities_objects(self):
        final_commodities = []
        for commodity in self.get_all_commodities():
            if self.get_commodity(commodity).is_final():
                final_commodities.append(self.get_commodity(commodity))

        return final_commodities

    def get_not_used_commodities_names(self):
        not_used_commodities = []
        for commodity in self.get_all_commodities():
            if not self.get_commodity(commodity).is_final():
                not_used_commodities.append(self.get_commodity(commodity).get_nice_name())

        return not_used_commodities

    def get_not_used_commodities_objects(self):
        not_used_commodities = []
        for commodity in self.get_all_commodities():
            if not self.get_commodity(commodity).is_final():
                not_used_commodities.append(self.get_commodity(commodity))

        return not_used_commodities

    def get_custom_commodities_names(self):
        custom_commodities = []
        for commodity in self.get_all_commodities():
            if self.get_commodity(commodity).is_custom():
                custom_commodities.append(self.get_commodity(commodity).get_nice_name())

        return custom_commodities

    def get_custom_commodities_objects(self):
        custom_commodities = []
        for commodity in self.get_all_commodities():
            if self.get_commodity(commodity).is_custom():
                custom_commodities.append(self.get_commodity(commodity))

        return custom_commodities

    def add_commodity(self, abbreviation, commodity):
        self.commodities.update({abbreviation: commodity})
        self.set_nice_name(abbreviation, commodity.get_nice_name())
        self.set_abbreviation(commodity.get_nice_name(), abbreviation)

    def remove_commodity_entirely(self, name):
        self.commodities.pop(name)

    def get_all_commodities(self):
        return self.commodities

    def get_all_commodity_names(self):  # checked
        all_commodities = []
        for s in [*self.get_all_commodities().keys()]:
            if s not in all_commodities:
                all_commodities.append(s)
        return all_commodities

    def get_commodity(self, name):  # checked
        return self.commodities[name]

    def get_commodity_by_nice_name(self, nice_name):
        abbreviation = self.get_abbreviation(nice_name)
        return self.get_commodity(abbreviation)

    def get_commodity_by_component(self, component):  # checked
        return self.components[component].get_commodities()

    def get_component_by_commodity(self, commodity):  # checked
        components = []

        for c in self.components:
            if commodity in self.get_commodity_by_component(c):
                components.append(c)

        return components

    def remove_commodity(self, commodity):
        self.get_commodity(commodity).set_final(False)

    def activate_commodity(self, commodity):
        self.get_commodity(commodity).set_final(True)

    def set_integer_steps(self, integer_steps):
        self.integer_steps = integer_steps

    def get_integer_steps(self):
        return self.integer_steps

    def set_uses_representative_periods(self, uses_representative_periods):
        self.uses_representative_periods = bool(uses_representative_periods)

    def get_uses_representative_periods(self):
        return self.uses_representative_periods

    def set_representative_periods_length(self, representative_periods_length):
        self.representative_periods_length = representative_periods_length

    def get_representative_periods_length(self):
        return self.representative_periods_length

    def set_path_weighting(self, path):
        self.path_weighting = str(path)

    def get_path_weighting(self):
        return self.path_weighting

    def set_covered_period(self, covered_period):
        self.covered_period = int(covered_period)

    def get_covered_period(self):
        return self.covered_period

    def get_time_steps(self):
        if self.get_uses_representative_periods():
            length_weighting = len(pd.read_excel(self.path_data + self.get_path_weighting(), index_col=0).index)
            return int(length_weighting * self.get_representative_periods_length())
        else:
            return int(self.covered_period)

    def set_single_or_multiple_generation_profiles(self, status):
        self.single_or_multiple_generation_profiles = status

    def get_single_or_multiple_generation_profiles(self):
        return self.single_or_multiple_generation_profiles

    def set_generation_data(self, generation_data):
        self.generation_data = generation_data

    def get_generation_data(self):
        return self.generation_data

    def set_single_or_multiple_commodity_profiles(self, status):
        self.single_or_multiple_commodity_profiles = status

    def get_single_or_multiple_commodity_profiles(self):
        return self.single_or_multiple_commodity_profiles

    def set_commodity_data(self, commodity_data):
        self.commodity_data = commodity_data

    def get_commodity_data(self):
        return self.commodity_data

    def check_commodity_data_needed(self):
        commodity_data_needed = False
        for s in self.get_all_commodities():
            if self.get_commodity(s).is_purchasable():
                if self.get_commodity(s).get_purchase_price_type() == 'variable':
                    commodity_data_needed = True
                    break

            elif self.get_commodity(s).is_saleable():
                if self.get_commodity(s).get_sale_price_type() == 'variable':
                    commodity_data_needed = True
                    break

            elif self.get_commodity(s).is_demanded():
                if self.get_commodity(s).get_demand_type() == 'variable':
                    commodity_data_needed = True
                    break

        self.commodity_data_needed = commodity_data_needed

    def get_commodity_data_needed(self):
        return self.commodity_data_needed

    def get_path_data(self):
        return self.path_data

    def get_project_name(self):
        return self.project_name

    def set_project_name(self, project_name):
        self.project_name = project_name

    def set_monetary_unit(self, monetary_unit):
        self.monetary_unit = monetary_unit

    def get_monetary_unit(self):
        return self.monetary_unit

    def get_component_lifetime_parameters(self):
        lifetime_dict = {}

        for component_object in self.get_final_components_objects():
            component_name = component_object.get_name()

            lifetime_dict[component_name] = component_object.get_lifetime()

        return lifetime_dict

    def get_component_maintenance_parameters(self):
        maintenance_dict = {}

        for component_object in self.get_final_components_objects():
            component_name = component_object.get_name()
            maintenance_dict[component_name] = component_object.get_maintenance()

        return maintenance_dict

    def get_component_variable_capex_parameters(self):
        capex_var_dict = {}

        for component_object in self.get_final_components_objects():
            component_name = component_object.get_name()
            capex_var_dict[component_name] = component_object.get_capex()

            if component_object.get_component_type() == 'conversion':

                if component_object.get_capex_basis() == 'output':
                    i = component_object.get_main_input()
                    i_coefficient = component_object.get_inputs()[i]
                    o = component_object.get_main_output()
                    o_coefficient = component_object.get_outputs()[o]
                    ratio = o_coefficient / i_coefficient
                else:
                    ratio = 1

                capex_var_dict[component_name] = capex_var_dict[component_name] * ratio

        return capex_var_dict

    def get_component_fixed_capex_parameters(self):
        capex_fix_dict = {}

        for component_object in self.get_final_components_objects():
            component_name = component_object.get_name()
            capex_fix_dict[component_name] = 0

        return capex_fix_dict

    def get_scaling_component_variable_capex_parameters(self):
        capex_var_pre_dict = {}

        for component_object in self.get_final_conversion_components_objects():
            if component_object.is_scalable():
                lower_bound, upper_bound, coefficient, intercept = \
                    self.calculate_economies_of_scale_steps(component_object)

                capex_var_pre_dict.update(coefficient)

        return capex_var_pre_dict

    def get_scaling_component_fixed_capex_parameters(self):
        capex_fix_pre_dict = {}

        for component_object in self.get_final_conversion_components_objects():
            if component_object.is_scalable():
                lower_bound, upper_bound, coefficient, intercept = \
                    self.calculate_economies_of_scale_steps(component_object)

                capex_fix_pre_dict.update(intercept)

        return capex_fix_pre_dict

    def get_scaling_component_capex_upper_bound_parameters(self):
        upper_bound_dict = {}

        for component_object in self.get_final_conversion_components_objects():

            if component_object.is_scalable():
                lower_bound, upper_bound, coefficient, intercept = \
                    self.calculate_economies_of_scale_steps(component_object)

                upper_bound_dict.update(upper_bound)

        return upper_bound_dict

    def get_scaling_component_capex_lower_bound_parameters(self):
        lower_bound_dict = {}

        for component_object in self.get_final_conversion_components_objects():

            if component_object.is_scalable():
                lower_bound, upper_bound, coefficient, intercept = \
                    self.calculate_economies_of_scale_steps(component_object)

                lower_bound_dict.update(lower_bound)

        return lower_bound_dict

    def get_component_minimal_power_parameters(self):
        min_p_dict = {}

        for component_object in self.get_final_conversion_components_objects():
            component_name = component_object.get_name()
            min_p_dict[component_name] = component_object.get_min_p()

        return min_p_dict

    def get_component_maximal_power_parameters(self):
        max_p_dict = {}

        for component_object in self.get_final_conversion_components_objects():
            component_name = component_object.get_name()
            max_p_dict[component_name] = component_object.get_max_p()

        return max_p_dict

    def get_component_ramp_up_parameters(self):
        ramp_up_dict = {}

        for component_object in self.get_final_conversion_components_objects():
            component_name = component_object.get_name()
            ramp_up_dict[component_name] = component_object.get_ramp_up()

        return ramp_up_dict

    def get_component_ramp_down_parameters(self):
        ramp_down_dict = {}

        for component_object in self.get_final_conversion_components_objects():
            component_name = component_object.get_name()
            ramp_down_dict[component_name] = component_object.get_ramp_down()

        return ramp_down_dict

    def get_shut_down_component_down_time_parameters(self):
        down_time_dict = {}

        for component_object in self.get_final_conversion_components_objects():
            component_name = component_object.get_name()
            if component_object.get_shut_down_ability():
                if int(component_object.get_start_up_time()) == 0:
                    # shut down time of 0 is not possible (division). Therefore, set it to 1
                    down_time_dict[component_name] = 1
                else:
                    down_time_dict[component_name] = int(component_object.get_start_up_time())

        return down_time_dict

    def get_shut_down_component_start_up_costs_parameters(self):
        start_up_costs_dict = {}

        for component_object in self.get_final_conversion_components_objects():
            component_name = component_object.get_name()

            if component_object.get_capex_basis() == 'output':
                i = component_object.get_main_input()
                i_coefficient = component_object.get_inputs()[i]
                o = component_object.get_main_output()
                o_coefficient = component_object.get_outputs()[o]
                ratio = o_coefficient / i_coefficient
            else:
                ratio = 1

            if component_object.get_shut_down_ability():
                start_up_costs_dict[component_name] = component_object.get_start_up_costs() * ratio

        return start_up_costs_dict

    def get_standby_component_down_time_parameters(self):
        standby_time_dict = {}

        for component_object in self.get_final_conversion_components_objects():
            component_name = component_object.get_name()

            if component_object.get_hot_standby_ability():
                if int(component_object.get_hot_standby_startup_time()) == 0:
                    # shut down time of 0 is not possible (division). Therefore, set it to 1
                    standby_time_dict[component_name] = 1
                else:
                    standby_time_dict[component_name] = int(component_object.get_hot_standby_startup_time())

        return standby_time_dict

    def get_storage_component_charging_efficiency(self):

        charging_efficiency_dict = {}
        for component_object in self.get_final_storage_components_objects():
            component_name = component_object.get_name()
            charging_efficiency_dict[component_name] = component_object.get_charging_efficiency()

        return charging_efficiency_dict

    def get_storage_component_discharging_efficiency(self):

        discharging_efficiency_dict = {}
        for component_object in self.get_final_storage_components_objects():
            component_name = component_object.get_name()
            discharging_efficiency_dict[component_name] = component_object.get_discharging_efficiency()

        return discharging_efficiency_dict

    def get_storage_component_minimal_soc(self):

        min_soc_dict = {}
        for component_object in self.get_final_storage_components_objects():
            component_name = component_object.get_name()
            min_soc_dict[component_name] = component_object.get_min_soc()

        return min_soc_dict

    def get_storage_component_maximal_soc(self):

        max_soc_dict = {}
        for component_object in self.get_final_storage_components_objects():
            component_name = component_object.get_name()
            max_soc_dict[component_name] = component_object.get_max_soc()

        return max_soc_dict

    def get_storage_component_ratio_capacity_power(self):

        ratio_capacity_power_dict = {}
        for component_object in self.get_final_storage_components_objects():
            component_name = component_object.get_name()
            ratio_capacity_power_dict[component_name] = component_object.get_ratio_capacity_p()

        return ratio_capacity_power_dict

    def get_fixed_capacities(self):
        fixed_capacities_dict = {}
        for component_object in self.get_final_generator_components_objects():
            component_name = component_object.get_name()
            fixed_capacities_dict[component_name] = component_object.get_fixed_capacity()

        return fixed_capacities_dict

    def calculate_economies_of_scale_steps(self, component_object, plot=False):

        component_name = component_object.get_name()

        base_capacity = component_object.get_base_capacity()
        economies_of_scale = component_object.get_economies_of_scale()
        max_capacity_economies_of_scale = component_object.get_max_capacity_economies_of_scale()
        base_investment = component_object.get_base_investment()

        if component_object.get_capex_basis() == 'output':
            # If the investment is based on the output, the investment curve has to be transformed

            i = component_object.get_main_input()
            i_coefficient = component_object.get_inputs()[i]
            o = component_object.get_main_output()
            o_coefficient = component_object.get_outputs()[o]
            ratio = o_coefficient / i_coefficient

            base_capacity = base_capacity / ratio
            max_capacity_economies_of_scale = max_capacity_economies_of_scale / ratio

        # First, calculate the investment curve based on the economies of scale

        # If max_capacity is higher than calculating every step would increase calculation time
        # Therefore, the approach uses 1000 capacities to calculate the investment

        integer_steps = self.get_integer_steps()

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

            upper_bound[(component_name, i + 1)] = capacities[i + 1]
            lower_bound[(component_name, i + 1)] = capacities[i]

            y_value = np.zeros([len(range(int(capacities[i]), int(capacities[i + 1])))])
            x_value = np.zeros([len(range(int(capacities[i]), int(capacities[i + 1])))]).reshape((-1, 1))

            k = 0
            for j in range(int(capacities[i]), int(capacities[i + 1])):
                x_value[k] = j
                if x_value[k] != 0:
                    y_value[k] = base_investment * (j / base_capacity) ** economies_of_scale
                else:
                    y_value[k] = 0
                k += 1

            model = LinearRegression().fit(x_value, y_value)
            coefficient[(component_name, i + 1)] = model.coef_[0]
            intercept[(component_name, i + 1)] = model.intercept_

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

    def get_all_component_parameters(self):

        lifetime_dict = self.get_component_lifetime_parameters()
        maintenance_dict = self.get_component_maintenance_parameters()
        capex_var_dict = self.get_component_variable_capex_parameters()
        capex_fix_dict = self.get_component_fixed_capex_parameters()

        minimal_power_dict = self.get_component_minimal_power_parameters()
        maximal_power_dict = self.get_component_maximal_power_parameters()
        ramp_up_dict = self.get_component_ramp_up_parameters()
        ramp_down_dict = self.get_component_ramp_down_parameters()

        scaling_capex_var_dict = self.get_scaling_component_variable_capex_parameters()
        scaling_capex_fix_dict = self.get_scaling_component_fixed_capex_parameters()
        scaling_capex_upper_bound_dict = self.get_scaling_component_capex_upper_bound_parameters()
        scaling_capex_lower_bound_dict = self.get_scaling_component_capex_lower_bound_parameters()

        shut_down_down_time_dict = self.get_shut_down_component_down_time_parameters()
        shut_down_start_up_costs = self.get_shut_down_component_start_up_costs_parameters()

        standby_down_time_dict = self.get_standby_component_down_time_parameters()

        charging_efficiency_dict = self.get_storage_component_charging_efficiency()
        discharging_efficiency_dict = self.get_storage_component_discharging_efficiency()

        minimal_soc_dict = self.get_storage_component_minimal_soc()
        maximal_soc_dict = self.get_storage_component_maximal_soc()

        ratio_capacity_power_dict = self.get_storage_component_ratio_capacity_power()

        fixed_capacity_dict = self.get_fixed_capacities()

        return lifetime_dict, maintenance_dict, capex_var_dict, capex_fix_dict, minimal_power_dict, maximal_power_dict,\
            ramp_up_dict, ramp_down_dict, scaling_capex_var_dict, scaling_capex_fix_dict,\
            scaling_capex_upper_bound_dict, scaling_capex_lower_bound_dict,\
            shut_down_down_time_dict, shut_down_start_up_costs, standby_down_time_dict,\
            charging_efficiency_dict, discharging_efficiency_dict, minimal_soc_dict, maximal_soc_dict, \
            ratio_capacity_power_dict, fixed_capacity_dict

    def get_conversion_component_sub_sets(self):

        scalable_components = []
        not_scalable_components = []

        shut_down_components = []
        no_shut_down_components = []

        standby_components = []
        no_standby_components = []

        for component_object in self.get_final_components_objects():
            component_name = component_object.get_name()

            if component_object.get_component_type() == 'conversion':

                if not component_object.is_scalable():
                    not_scalable_components.append(component_name)
                else:
                    scalable_components.append(component_name)

                if component_object.get_shut_down_ability():
                    shut_down_components.append(component_name)
                else:
                    no_shut_down_components.append(component_name)

                if component_object.get_hot_standby_ability():
                    standby_components.append(component_name)
                else:
                    no_standby_components.append(component_name)

        return scalable_components, not_scalable_components, shut_down_components, no_shut_down_components,\
            standby_components, no_standby_components

    def get_commodity_sets(self):
        final_commodities = []
        available_commodities = []
        emittable_commodities = []
        purchasable_commodities = []
        saleable_commodities = []
        demanded_commodities = []
        total_demand_commodities = []

        for commodity in self.get_final_commodities_objects():

            commodity_name = commodity.get_name()

            final_commodities.append(commodity_name)

            if commodity.is_available():
                available_commodities.append(commodity_name)
            if commodity.is_emittable():
                emittable_commodities.append(commodity_name)
            if commodity.is_purchasable():
                purchasable_commodities.append(commodity_name)
            if commodity.is_saleable():
                saleable_commodities.append(commodity_name)
            if commodity.is_demanded():
                demanded_commodities.append(commodity_name)
            if commodity.is_total_demand():
                total_demand_commodities.append(commodity_name)

        generated_commodities = []
        for generator in self.get_final_generator_components_objects():
            if generator.get_generated_commodity() not in generated_commodities:
                generated_commodities.append(generator.get_generated_commodity())

        return final_commodities, available_commodities, emittable_commodities, purchasable_commodities, saleable_commodities,\
            demanded_commodities, total_demand_commodities, generated_commodities

    def get_input_conversions(self):
        input_tuples = []
        input_conversion_tuples = []
        input_conversion_tuples_dict = {}

        for component in self.get_final_conversion_components_objects():
            name = component.get_name()
            inputs = component.get_inputs()
            main_input = component.get_main_input()

            for current_input in [*inputs.keys()]:
                input_tuples.append((name, current_input))
                if current_input != main_input:
                    input_conversion_tuples.append((name, main_input, current_input))
                    input_conversion_tuples_dict.update(
                        {(name, main_input, current_input): float(inputs[current_input]) / float(inputs[main_input])})

        return input_tuples, input_conversion_tuples, input_conversion_tuples_dict

    def get_output_conversions(self):
        output_tuples = []
        output_conversion_tuples = []
        output_conversion_tuples_dict = {}

        for component in self.get_final_conversion_components_objects():
            name = component.get_name()
            inputs = component.get_inputs()
            outputs = component.get_outputs()

            main_input = component.get_main_input()
            for current_output in [*outputs.keys()]:
                output_conversion_tuples.append((name, main_input, current_output))
                output_conversion_tuples_dict.update(
                    {(name, main_input, current_output): float(outputs[current_output]) / float(inputs[main_input])})

                output_tuples.append((name, current_output))

        return output_tuples, output_conversion_tuples, output_conversion_tuples_dict

    def get_all_conversions(self):

        input_tuples, input_conversion_tuples, input_conversion_tuples_dict = self.get_input_conversions()
        output_tuples, output_conversion_tuples, output_conversion_tuples_dict = self.get_output_conversions()

        return input_tuples, input_conversion_tuples, input_conversion_tuples_dict,\
            output_tuples, output_conversion_tuples, output_conversion_tuples_dict

    def get_generation_time_series(self):
        generation_profiles_dict = {}

        if self.get_generation_data() is not None:
            generation_profile = pd.read_excel(self.get_generation_data(), index_col=0)
            for generator in self.get_final_generator_components_objects():
                generator_name = generator.get_name()
                for t in range(self.get_time_steps()):
                    ind = generation_profile.index[t]
                    generation_profiles_dict.update({(generator_name, t):
                                                     float(generation_profile.loc[ind, generator.get_nice_name()])})

        return generation_profiles_dict

    def get_demand_time_series(self):
        demand_dict = {}

        for commodity in self.get_final_commodities_objects():
            commodity_name = commodity.get_name()
            commodity_nice_name = commodity.get_nice_name()

            if commodity.is_demanded():
                if commodity.get_demand_type() == 'fixed':
                    for t in range(self.get_time_steps()):
                        demand_dict.update({(commodity_name, t): float(commodity.get_demand())})

                else:
                    demand_curve_df = pd.read_excel(self.get_commodity_data(), index_col=0)
                    demand_curve = demand_curve_df.loc[:, commodity_nice_name + '_Demand']
                    for t in range(self.get_time_steps()):
                        demand_dict.update({(commodity_name, t): float(demand_curve.loc[t])})

        return demand_dict

    def get_purchase_price_time_series(self):
        purchase_price_dict = {}

        for commodity in self.get_final_commodities_objects():
            commodity_name = commodity.get_name()
            commodity_nice_name = commodity.get_nice_name()
            if commodity.is_purchasable():
                if commodity.get_purchase_price_type() == 'fixed':
                    for t in range(self.get_time_steps()):
                        purchase_price_dict.update({(commodity_name, t): float(commodity.get_purchase_price())})

                else:
                    sell_purchase_price_curve = pd.read_excel(self.get_commodity_data(),
                                                              index_col=0)
                    purchase_price_curve = sell_purchase_price_curve.loc[:, commodity_nice_name + '_Purchase_Price']
                    for t in range(self.get_time_steps()):
                        purchase_price_dict.update({(commodity_name, t): float(purchase_price_curve.loc[t])})

        return purchase_price_dict

    def get_sale_price_time_series(self):
        sell_price_dict = {}
        for commodity in self.get_final_commodities_objects():
            commodity_name = commodity.get_name()
            commodity_nice_name = commodity.get_nice_name()
            if commodity.is_saleable():
                if commodity.get_sale_price_type() == 'fixed':
                    for t in range(self.get_time_steps()):
                        sell_price_dict.update({(commodity_name, t): float(commodity.get_sale_price())})
                else:
                    sell_purchase_price_curve = pd.read_excel(self.get_commodity_data(),
                                                              index_col=0)
                    sale_price_curve = sell_purchase_price_curve.loc[:, commodity_nice_name + '_Selling_Price']
                    for t in range(self.get_time_steps()):
                        sell_price_dict.update({(commodity_name, t): float(sale_price_curve.loc[t])})

        return sell_price_dict

    def get_weightings_time_series(self):
        weightings_dict = {}
        if self.get_uses_representative_periods():
            weightings = pd.read_excel(self.path_data + self.get_path_weighting(), index_col=0)
            j = 0
            for i in weightings.index:
                for k in range(7 * 24):
                    weightings_dict[j] = weightings.at[i, 'weighting']
                    j += 1
        else:
            for t in range(self.get_time_steps()):
                weightings_dict[t] = 1

        return weightings_dict

    def create_new_project(self):
        """ Create new project """

        nice_names = {'WACC': 'wacc',
                      'Personnel Cost': 'personnel_costs',
                      'Taxes and insurance': 'taxes_and_insurance',
                      'Overhead': 'overhead',
                      'Working Capital': 'working_capital'}

        for c in [*nice_names.keys()]:
            self.set_nice_name(nice_names[c], c)
            self.set_abbreviation(c, nice_names[c])

        # Set general parameters
        self.set_general_parameter_value('wacc', 0.07)
        self.set_general_parameter('wacc')

        self.set_general_parameter_value('taxes_and_insurance', 0.015)
        self.set_general_parameter('taxes_and_insurance')

        self.set_general_parameter_value('personnel_costs', 0.01)
        self.set_general_parameter('personnel_costs')

        self.set_general_parameter_value('overhead', 0.015)
        self.set_general_parameter('overhead')

        self.set_general_parameter_value('working_capital', 0.1)
        self.set_general_parameter('working_capital')

        conversion_component = ConversionComponent(name='dummy', nice_name='Dummy', final_unit=True)
        self.add_component('dummy', conversion_component)

        for g in self.get_general_parameters():
            self.set_applied_parameter_for_component(g, 'dummy', True)

        c = 'dummy'
        input_commodity = 'electricity'
        output_commodity = 'electricity'

        self.get_component(c).add_input(input_commodity, 1)
        self.get_component(c).add_output(output_commodity, 1)

        self.get_component(c).set_main_input(input_commodity)
        self.get_component(c).set_main_output(output_commodity)

        s = Commodity('electricity', 'Electricity', 'MWh', final_commodity=True)
        self.add_commodity('electricity', s)

        self.set_nice_name('electricity', 'Electricity')
        self.set_abbreviation('Electricity', 'electricity')

    def __copy__(self):

        # deepcopy mutable objects
        general_parameters = copy.deepcopy(self.general_parameters)
        general_parameter_values = copy.deepcopy(self.general_parameter_values)
        nice_names = copy.deepcopy(self.nice_names)
        abbreviations_dict = copy.deepcopy(self.abbreviations_dict)
        commodities = copy.deepcopy(self.commodities)

        return ParameterObject(name=self.name,
                               integer_steps=self.integer_steps,
                               general_parameters=general_parameters,
                               general_parameter_values=general_parameter_values,
                               nice_names=nice_names,
                               abbreviations_dict=abbreviations_dict,
                               commodities=commodities,
                               components=self.components,
                               generation_data=self.generation_data,
                               single_or_multiple_generation_profiles=self.single_or_multiple_generation_profiles,
                               commodity_data=self.commodity_data,
                               single_or_multiple_commodity_profiles=self.single_or_multiple_commodity_profiles,
                               uses_representative_periods=self.uses_representative_periods,
                               representative_periods_length=self.representative_periods_length,
                               path_weighting=self.path_weighting,
                               covered_period=self.covered_period,
                               monetary_unit=self.monetary_unit,
                               copy_object=True)

    def __init__(self, name=None, integer_steps=5,
                 general_parameters=None, general_parameter_values=None,
                 nice_names=None, abbreviations_dict=None, commodities=None, components=None,
                 generation_data=None, single_or_multiple_generation_profiles='single',
                 commodity_data=None, single_or_multiple_commodity_profiles='single',
                 uses_representative_periods=False, representative_periods_length=0, path_weighting='',
                 covered_period=8760, monetary_unit='€',
                 project_name=None, path_data=None,
                 copy_object=False):

        """
        Object, which stores all components, commodities, settings etc.
        :param name: [string] - name of parameter object
        :param integer_steps: [int] - number of integer steps (used to split capacity)
        :param general_parameters: [list] - List of general parameters
        :param general_parameter_values: [dict] - Dictionary with general parameter values
        :param nice_names: [list] - List of nice names of components, commodities etc.
        :param abbreviations_dict: [dict] - List of abbreviations of components, commodities etc.
        :param commodities: [dict] - Dictionary with abbreviations as keys and commodity objects as values
        :param components: [dict] - Dictionary with abbreviations as keys and component objects as values
        :param copy_object: [boolean] - Boolean if object is copy
        """
        self.name = name

        if not copy_object:

            # Initiate as default values
            self.general_parameters = ['wacc', 'taxes_and_insurance', 'personnel_costs', 'overhead', 'working_capital']
            self.general_parameter_values = {'wacc': 0.07,
                                             'taxes_and_insurance': 0.015,
                                             'personnel_costs': 0.01,
                                             'overhead': 0.015,
                                             'working_capital': 0.1}
            self.applied_parameter_for_component = {'taxes_and_insurance': {},
                                                    'personnel_costs': {},
                                                    'overhead': {},
                                                    'working_capital': {}}

            self.nice_names = {}
            self.abbreviations_dict = {}

            self.commodities = {}
            self.components = {}

        else:
            # Object is copied if components have parallel units.
            # It is copied so that the original pm_object is not changed

            self.general_parameters = general_parameters
            self.general_parameter_values = general_parameter_values
            self.applied_parameter_for_component = {'taxes_and_insurance': {},
                                                    'personnel_costs': {},
                                                    'overhead': {},
                                                    'working_capital': {}}

            self.nice_names = nice_names
            self.abbreviations_dict = abbreviations_dict

            self.commodities = commodities
            self.components = components

        self.covered_period = covered_period
        self.uses_representative_periods = uses_representative_periods
        self.representative_periods_length = representative_periods_length
        self.path_weighting = path_weighting
        self.integer_steps = integer_steps
        self.monetary_unit = str(monetary_unit)

        self.generation_data = generation_data
        self.single_or_multiple_generation_profiles = single_or_multiple_generation_profiles

        self.commodity_data = commodity_data
        self.single_or_multiple_commodity_profiles = single_or_multiple_commodity_profiles

        self.path_data = path_data
        self.project_name = project_name

        self.commodity_data_needed = False
        self.check_commodity_data_needed()


ParameterObjectCopy = type('CopyOfB', ParameterObject.__bases__, dict(ParameterObject.__dict__))
