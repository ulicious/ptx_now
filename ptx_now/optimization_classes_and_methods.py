import pyomo.environ as pyo
from pyomo.core import *
from pyomo.core import Binary
from copy import deepcopy

import os

GLPK_FOLDER_PATH = "C:/Users/mt5285/glpk/w64"
os.environ["PATH"] += os.pathsep + str(GLPK_FOLDER_PATH)  # todo: Check if necessary

from pyutilib.services import register_executable
register_executable(name='glpsol')


class OptimizationProblem:

    def clone_components_which_use_parallelization(self):
        pm_object_copy = deepcopy(self.pm_object)

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
                    parallel_unit_component_name = component_name + '_' + str(i)
                    component_copy = component_object.__copy__()
                    component_copy.set_name(parallel_unit_component_name)
                    pm_object_copy.add_component(parallel_unit_component_name, component_copy)

        return pm_object_copy

    def attach_component_sets_to_optimization_problem(self):
        self.model.CONVERSION_COMPONENTS = Set(initialize=self.conversion_components)
        self.model.STORAGES = Set(initialize=self.storage_components)
        self.model.GENERATORS = Set(initialize=self.generator_components)
        self.model.COMPONENTS = Set(initialize=self.all_components)

    def attach_scalable_component_sets_to_optimization_problem(self):
        self.model.SCALABLE_COMPONENTS = Set(initialize=self.scalable_components)

    def attach_shut_down_component_sets_to_optimization_problem(self):
        self.model.SHUT_DOWN_COMPONENTS = Set(initialize=self.shut_down_components)

    def attach_standby_component_sets_to_optimization_problem(self):
        self.model.STANDBY_COMPONENTS = Set(initialize=self.standby_components)

    def attach_commodity_sets_to_optimization_problem(self):
        self.model.COMMODITIES = Set(initialize=self.final_commodities)  # Mass energy commodity
        self.model.AVAILABLE_COMMODITIES = Set(initialize=self.available_commodities)
        self.model.EMITTED_COMMODITIES = Set(initialize=self.emittable_commodities)
        self.model.PURCHASABLE_COMMODITIES = Set(initialize=self.purchasable_commodities)
        self.model.SALEABLE_COMMODITIES = Set(initialize=self.saleable_commodities)
        self.model.DEMANDED_COMMODITIES = Set(initialize=self.demanded_commodities)
        self.model.TOTAL_DEMANDED_COMMODITIES = Set(initialize=self.total_demand_commodities)
        self.model.GENERATED_COMMODITIES = Set(initialize=self.generated_commodities)
        self.model.INPUT_COMMODITIES = Set(initialize=self.all_inputs)
        self.model.OUTPUT_COMMODITIES = Set(initialize=self.all_outputs)

    def attach_annuity_to_optimization_problem(self):
        self.model.ANF = Param(self.model.COMPONENTS, initialize=self.annuity_factor_dict)

    def attach_component_parameters_to_optimization_problem(self):
        self.model.lifetime = Param(self.model.COMPONENTS, initialize=self.lifetime_dict)
        self.model.fixed_om = Param(self.model.COMPONENTS, initialize=self.fixed_om_dict)
        self.model.variable_om = Param(self.model.COMPONENTS, initialize=self.variable_om_dict)

        self.model.capex_var = Param(self.model.COMPONENTS, initialize=self.capex_var_dict)
        self.model.capex_fix = Param(self.model.COMPONENTS, initialize=self.capex_fix_dict)

        self.model.min_p = Param(self.model.CONVERSION_COMPONENTS, initialize=self.minimal_power_dict)
        self.model.max_p = Param(self.model.CONVERSION_COMPONENTS, initialize=self.maximal_power_dict)

        self.model.ramp_up = Param(self.model.CONVERSION_COMPONENTS, initialize=self.ramp_up_dict)
        self.model.ramp_down = Param(self.model.CONVERSION_COMPONENTS, initialize=self.ramp_down_dict)

        self.model.charging_efficiency = Param(self.model.STORAGES, initialize=self.charging_efficiency_dict)
        self.model.discharging_efficiency = Param(self.model.STORAGES, initialize=self.discharging_efficiency_dict)

        self.model.minimal_soc = Param(self.model.STORAGES, initialize=self.minimal_soc_dict)
        self.model.maximal_soc = Param(self.model.STORAGES, initialize=self.maximal_soc_dict)

        self.model.ratio_capacity_p = Param(self.model.STORAGES, initialize=self.ratio_capacity_power_dict)

        self.model.generator_fixed_capacity = Param(self.model.GENERATORS, initialize=self.fixed_capacity_dict)

    def attach_scalable_component_parameters_to_optimization_problem(self):
        # Investment linearized: Investment = capex var * capacity + capex fix
        # Variable part of investment -> capex var * capacity

        self.model.capex_pre_var = Param(self.model.SCALABLE_COMPONENTS, self.model.INTEGER_STEPS,
                                         initialize=self.scaling_capex_var_dict)
        # fix part of investment
        self.model.capex_pre_fix = Param(self.model.SCALABLE_COMPONENTS, self.model.INTEGER_STEPS,
                                         initialize=self.scaling_capex_fix_dict)

    def attach_shut_down_component_parameters_to_optimization_problem(self):
        self.model.down_time = Param(self.model.SHUT_DOWN_COMPONENTS, initialize=self.shut_down_down_time_dict)
        self.model.start_up_costs = Param(self.model.SHUT_DOWN_COMPONENTS, initialize=self.shut_down_start_up_costs)

    def attach_standby_component_parameters_to_optimization_problem(self):
        self.model.standby_time = Param(self.model.STANDBY_COMPONENTS, initialize=self.standby_down_time_dict)

    def attach_component_variables_to_optimization_problem(self):
        # Component variables
        self.model.nominal_cap = Var(self.model.COMPONENTS, bounds=(0, None))

        self.model.status_on = Var(self.model.CONVERSION_COMPONENTS, self.model.CLUSTERS, self.model.TIME, within=Binary)
        self.model.status_off = Var(self.model.CONVERSION_COMPONENTS, self.model.CLUSTERS, self.model.TIME, within=Binary)
        self.model.status_off_switch_on = Var(self.model.CONVERSION_COMPONENTS, self.model.CLUSTERS, self.model.TIME, within=Binary)
        self.model.status_off_switch_off = Var(self.model.CONVERSION_COMPONENTS, self.model.CLUSTERS, self.model.TIME, within=Binary)
        self.model.status_standby_switch_on = Var(self.model.CONVERSION_COMPONENTS, self.model.CLUSTERS, self.model.TIME, within=Binary)
        self.model.status_standby_switch_off = Var(self.model.CONVERSION_COMPONENTS, self.model.CLUSTERS, self.model.TIME, within=Binary)
        self.model.status_standby = Var(self.model.CONVERSION_COMPONENTS, self.model.CLUSTERS, self.model.TIME, within=Binary)

        # STORAGE binaries (charging and discharging)
        self.model.storage_charge_binary = Var(self.model.STORAGES, self.model.CLUSTERS, self.model.TIME, within=Binary)
        self.model.storage_discharge_binary = Var(self.model.STORAGES, self.model.CLUSTERS, self.model.TIME, within=Binary)

        self.model.investment = Var(self.model.COMPONENTS, bounds=(0, None))

    def attach_scalable_component_variables_to_optimization_problem(self):

        def set_scalable_component_capacity_bound_rule(model, s, i):
            return 0, self.scaling_capex_upper_bound_dict[(s, i)]

        self.model.nominal_cap_pre = Var(self.model.SCALABLE_COMPONENTS, self.model.INTEGER_STEPS,
                                         bounds=set_scalable_component_capacity_bound_rule)
        self.model.capacity_binary = Var(self.model.SCALABLE_COMPONENTS, self.model.INTEGER_STEPS, within=Binary)

    def attach_commodity_variables_to_optimization_problem(self):

        # -------------------------------------
        # Commodity variables
        # Input and output commodity of component

        self.model.mass_energy_component_in_commodities = Var(self.model.CONVERSION_COMPONENTS,
                                                              self.model.INPUT_COMMODITIES, self.model.CLUSTERS,
                                                              self.model.TIME,
                                                              bounds=(0, None))
        self.model.mass_energy_component_out_commodities = Var(self.model.CONVERSION_COMPONENTS,
                                                               self.model.OUTPUT_COMMODITIES, self.model.CLUSTERS,
                                                               self.model.TIME,
                                                               bounds=(0, None))

        # Freely available commodities
        self.model.mass_energy_available = Var(self.model.AVAILABLE_COMMODITIES, self.model.CLUSTERS, self.model.TIME,
                                               bounds=(0, None))
        self.model.mass_energy_emitted = Var(self.model.EMITTED_COMMODITIES, self.model.CLUSTERS, self.model.TIME,
                                             bounds=(0, None))

        # Charged and discharged commodities
        self.model.mass_energy_storage_in_commodities = Var(self.model.STORAGES, self.model.CLUSTERS,
                                                            self.model.TIME, bounds=(0, None))
        self.model.mass_energy_storage_out_commodities = Var(self.model.STORAGES, self.model.CLUSTERS,
                                                             self.model.TIME, bounds=(0, None))
        self.model.soc = Var(self.model.STORAGES, self.model.CLUSTERS, self.model.TIME, bounds=(0, None))

        # sold and purchased commodities
        self.model.mass_energy_sell_commodity = Var(self.model.SALEABLE_COMMODITIES, self.model.CLUSTERS,
                                                    self.model.TIME, bounds=(0, None))
        self.model.mass_energy_purchase_commodity = Var(self.model.PURCHASABLE_COMMODITIES, self.model.CLUSTERS,
                                                        self.model.TIME, bounds=(0, None))

        # generated commodities
        self.model.mass_energy_generation = Var(self.model.GENERATORS, self.model.GENERATED_COMMODITIES,
                                                self.model.CLUSTERS,  self.model.TIME,
                                                bounds=(0, None))

        # Demanded commodities
        self.model.mass_energy_demand = Var(self.model.DEMANDED_COMMODITIES, self.model.CLUSTERS,  self.model.TIME,
                                            bounds=(0, None))

        # Hot standby demand
        self.model.mass_energy_hot_standby_demand = Var(self.model.STANDBY_COMPONENTS, self.model.COMMODITIES,
                                                        self.model.CLUSTERS, self.model.TIME, bounds=(0, None))

    def attach_purchase_price_time_series_to_optimization_problem(self):
        self.model.purchase_price = Param(self.model.PURCHASABLE_COMMODITIES, self.model.CLUSTERS, self.model.TIME,
                                          initialize=self.purchase_price_dict)

    def attach_sale_price_time_series_to_optimization_problem(self):
        self.model.selling_price = Param(self.model.SALEABLE_COMMODITIES, self.model.CLUSTERS, self.model.TIME,
                                         initialize=self.sell_price_dict)

    def attach_demand_time_series_to_optimization_problem(self):

        if isinstance([*self.demand_dict.keys()][0], tuple):
            self.model.commodity_demand = Param(self.model.DEMANDED_COMMODITIES, self.model.CLUSTERS,
                                                self.model.TIME, initialize=self.demand_dict)
        else:
            self.model.commodity_demand = Param(self.model.TOTAL_DEMANDED_COMMODITIES, initialize=self.demand_dict)

    def attach_generation_time_series_to_optimization_problem(self):
        self.model.generation_profiles = Param(self.model.GENERATORS, self.model.CLUSTERS, self.model.TIME,
                                               initialize=self.generation_profiles_dict)

    def attach_weightings_time_series_to_optimization_problem(self):
        self.model.weightings = Param(self.model.CLUSTERS, initialize=self.weightings_dict)

    def attach_constraints(self):
        """ Method attaches all constraints to optimization problem """

        pm_object = self.pm_object
        model = self.model

        def _mass_energy_balance_rule(m, cl, com, t):
            # Sets mass energy balance for all components
            # produced (out), generated, discharged, available and purchased commodities
            #   = emitted, sold, demanded, charged and used (in) commodities
            commodity_object = pm_object.get_commodity(com)
            equation_lhs = []
            equation_rhs = []

            if commodity_object.is_available():
                equation_lhs.append(m.mass_energy_available[com, cl, t])
            if commodity_object.is_emittable():
                equation_lhs.append(-m.mass_energy_emitted[com, cl, t])
            if commodity_object.is_purchasable():
                equation_lhs.append(m.mass_energy_purchase_commodity[com, cl, t])
            if commodity_object.is_saleable():
                equation_lhs.append(-m.mass_energy_sell_commodity[com, cl, t])
            if commodity_object.is_demanded():
                equation_lhs.append(-m.mass_energy_demand[com, cl, t])
            if com in m.STORAGES:
                equation_lhs.append(
                    m.mass_energy_storage_out_commodities[com, cl, t] - m.mass_energy_storage_in_commodities[
                        com, cl, t])
            if com in m.GENERATED_COMMODITIES:
                equation_lhs.append(sum(m.mass_energy_generation[g, com, cl, t]
                                        for g in m.GENERATORS
                                        if pm_object.get_component(g).get_generated_commodity() == com))

            for c in m.CONVERSION_COMPONENTS:
                if (c, com) in self.output_tuples:
                    equation_lhs.append(m.mass_energy_component_out_commodities[c, com, cl, t])

                if (c, com) in self.input_tuples:
                    equation_rhs.append(m.mass_energy_component_in_commodities[c, com, cl, t])

                # hot standby demand
                if c in m.STANDBY_COMPONENTS:
                    hot_standby_commodity = [*pm_object.get_component(c).get_hot_standby_demand().keys()][0]
                    if com == hot_standby_commodity:
                        equation_rhs.append(m.mass_energy_hot_standby_demand[c, com, cl, t])

            return sum(equation_lhs) == sum(equation_rhs)
        model._mass_energy_balance_con = Constraint(model.CLUSTERS, model.COMMODITIES, model.TIME,
                                                    rule=_mass_energy_balance_rule)

        def demand_satisfaction_rule(m, me, cl, t):
            # Sets commodities, which are demanded
            if me not in m.TOTAL_DEMANDED_COMMODITIES:  # Case where demand needs to be satisfied in every t
                return m.mass_energy_demand[me, cl, t] >= m.commodity_demand[me, cl, t]
            else:  # case covering demand over all time steps
                return Constraint.Skip
        model.demand_satisfaction_con = Constraint(model.DEMANDED_COMMODITIES, model.CLUSTERS, model.TIME,
                                                   rule=demand_satisfaction_rule)

        def total_demand_satisfaction_rule(m, me):
            # Sets commodities, which are demanded
            if me not in m.TOTAL_DEMANDED_COMMODITIES:  # Case where demand needs to be satisfied in every t
                return Constraint.Skip
            else:  # case covering demand over all time steps
                return sum(m.mass_energy_demand[me, cl, t] * m.weightings[cl]
                           for cl in m.CLUSTERS for t in m.TIME) >= m.commodity_demand[me]
        model.total_demand_satisfaction_con = Constraint(model.DEMANDED_COMMODITIES,
                                                         rule=total_demand_satisfaction_rule)

        def capacity_binary_sum_rule(m, c):
            # For each component, only one capacity over all integer steps can be 1
            return sum(m.capacity_binary[c, i] for i in m.INTEGER_STEPS) <= 1  # todo: == 1?
        model.capacity_binary_sum_con = Constraint(model.SCALABLE_COMPONENTS, rule=capacity_binary_sum_rule)

        def capacity_binary_activation_rule(m, c, i):
            # Capacity binary will be 1 if the capacity of the integer step is higher than 0
            return m.capacity_binary[c, i] >= m.nominal_cap_pre[c, i] / 1000000  # big M
        model.capacity_binary_activation_con = Constraint(model.SCALABLE_COMPONENTS, model.INTEGER_STEPS,
                                                          rule=capacity_binary_activation_rule)

        def set_lower_bound_rule(m, c, i):
            # capacity binary sets lower bound. Lower bound is not predefined as each capacity step can be 0
            # if capacity binary = 0 -> nominal_cap_pre has no lower bound
            # if capacity binary = 1 -> nominal_cap_pre needs to be at least lower bound

            return m.nominal_cap_pre[c, i] >= self.scaling_capex_lower_bound_dict[c, i] * m.capacity_binary[c, i]
        model.set_lower_bound_con = Constraint(model.SCALABLE_COMPONENTS, model.INTEGER_STEPS,
                                               rule=set_lower_bound_rule)

        def final_capacity_rule(m, c):
            # Final capacity of component is sum of capacity over all integer steps
            return m.nominal_cap[c] == sum(m.nominal_cap_pre[c, i] for i in m.INTEGER_STEPS)
        model.final_capacity_con = Constraint(model.SCALABLE_COMPONENTS, rule=final_capacity_rule)

        def _commodity_conversion_output_rule(m, c, oc, cl, t):
            # Define ratio between main input and output commodities for all conversion tuples
            main_input = pm_object.get_component(c).get_main_input()
            outputs = self.pm_object.get_component(c).get_outputs()
            if oc in [*outputs.keys()]:
                return m.mass_energy_component_out_commodities[c, oc, cl, t] == \
                       m.mass_energy_component_in_commodities[c, main_input, cl, t] \
                       * self.output_conversion_tuples_dict[c, main_input, oc]
            else:
                return m.mass_energy_component_out_commodities[c, oc, cl, t] == 0
        model._commodity_conversion_output_con = Constraint(model.CONVERSION_COMPONENTS, model.OUTPUT_COMMODITIES,
                                                            model.CLUSTERS, model.TIME,
                                                         rule=_commodity_conversion_output_rule)

        def _commodity_conversion_input_rule(m, c, ic, cl, t):
            # Define ratio between main input and other input commodities for all conversion tuples
            main_input = pm_object.get_component(c).get_main_input()
            inputs = pm_object.get_component(c).get_inputs()
            if ic in [*inputs.keys()]:
                if ic != main_input:
                    return m.mass_energy_component_in_commodities[c, ic, cl, t] == \
                           m.mass_energy_component_in_commodities[c, main_input, cl, t] \
                           * self.input_conversion_tuples_dict[c, main_input, ic]
                else:
                    return Constraint.Skip
            else:
                return m.mass_energy_component_in_commodities[c, ic, cl, t] == 0
        model._commodity_conversion_input_con = Constraint(model.CONVERSION_COMPONENTS, model.INPUT_COMMODITIES,
                                                           model.CLUSTERS, model.TIME,
                                                        rule=_commodity_conversion_input_rule)

        def balance_component_status_rule(m, c, cl, t):
            # The component is either on, off or in hot standby
            return m.status_on[c, cl, t] + m.status_off[c, cl, t] + m.status_standby[c, cl, t] == 1
        model.balance_component_status_con = Constraint(model.CONVERSION_COMPONENTS, model.CLUSTERS, model.TIME,
                                                        rule=balance_component_status_rule)

        def component_no_shutdown_or_standby_rule(m, c, cl, t):
            # If component can not be shut off or put in hot standby, the status is always on
            if (c not in m.SHUT_DOWN_COMPONENTS) & (c not in m.STANDBY_COMPONENTS):
                return m.status_on[c, cl, t] == 1
            elif c not in m.SHUT_DOWN_COMPONENTS:
                return m.status_off[c, cl, t] == 0
            elif c not in m.STANDBY_COMPONENTS:
                return m.status_standby[c, cl, t] == 0
            else:
                return Constraint.Skip
        model.component_no_shutdown_or_standby_con = Constraint(model.CONVERSION_COMPONENTS, model.CLUSTERS, model.TIME,
                                                                rule=component_no_shutdown_or_standby_rule)

        def _active_component_rule(m, c, cl, t):
            # Set binary to 1 if component is active
            main_input = pm_object.get_component(c).get_main_input()
            return m.mass_energy_component_in_commodities[c, main_input, cl, t] \
                   - m.status_on[c, cl, t] * 1000000 <= 0
        model._active_component_con = Constraint(model.CONVERSION_COMPONENTS, model.CLUSTERS, model.TIME,
                                                 rule=_active_component_rule)

        def status_off_switch_rule(m, c, cl, t):
            if t > 0:
                return m.status_off[c, cl, t] == m.status_off[c, cl, t - 1] + m.status_off_switch_on[c, cl, t] \
                       - m.status_off_switch_off[c, cl, t]
            else:
                return Constraint.Skip
        model.status_off_switch_con = Constraint(model.CONVERSION_COMPONENTS, model.CLUSTERS, model.TIME,
                                                 rule=status_off_switch_rule)

        def balance_status_standby_switch_rule(m, c, cl, t):
            return m.status_standby_switch_on[c, cl, t] + m.status_standby_switch_off[c, cl, t] <= 1
        model.balance_status_standby_switch_con = Constraint(model.CONVERSION_COMPONENTS, model.CLUSTERS, model.TIME,
                                                             rule=balance_status_standby_switch_rule)

        def status_standby_switch_rule(m, c, cl, t):
            if t > 0:
                return m.status_standby[c, cl, t] == m.status_standby[c, cl, t - 1]\
                       + m.status_standby_switch_on[c, cl, t] \
                       - m.status_standby_switch_off[c, cl, t]
            else:
                return Constraint.Skip
        model.status_standby_switch_con = Constraint(model.CONVERSION_COMPONENTS, model.CLUSTERS, model.TIME,
                                                     rule=status_standby_switch_rule)

        def balance_status_off_switch_rule(m, c, cl, t):
            return m.status_off_switch_on[c, cl, t] + m.status_off_switch_off[c, cl, t] <= 1
        model.balance_status_off_switch_con = Constraint(model.CONVERSION_COMPONENTS, model.CLUSTERS, model.TIME,
                                                         rule=balance_status_off_switch_rule)

        def _conversion_maximal_component_capacity_rule(m, c, cl, t):
            # Limits conversion on capacity of conversion unit and defines conversions
            # Important: Capacity is always matched with input
            main_input = pm_object.get_component(c).get_main_input()
            return m.mass_energy_component_in_commodities[c, main_input, cl, t] <= m.nominal_cap[c] * m.max_p[c]
        model._conversion_maximal_component_capacity_con = Constraint(model.CONVERSION_COMPONENTS,
                                                                      model.CLUSTERS, model.TIME,
                                                                      rule=_conversion_maximal_component_capacity_rule)

        def _conversion_minimal_component_capacity_rule(m, c, cl, t):
            main_input = pm_object.get_component(c).get_main_input()
            return m.mass_energy_component_in_commodities[c, main_input, cl, t] \
                   >= m.nominal_cap[c] * m.min_p[c] + (m.status_on[c, cl, t] - 1) * 1000000
        model._conversion_minimal_component_capacity_con = Constraint(model.CONVERSION_COMPONENTS, model.CLUSTERS, model.TIME,
                                                                      rule=_conversion_minimal_component_capacity_rule)

        def _ramp_up_rule(m, c, cl, t):
            main_input = pm_object.get_component(c).get_main_input()
            if t > 0:
                return (m.mass_energy_component_in_commodities[c, main_input, cl, t]
                        - m.mass_energy_component_in_commodities[c, main_input, cl, t - 1]) <= \
                       m.nominal_cap[c] * m.ramp_up[c] + (m.status_off_switch_off[c, cl, t]
                                                          + m.status_standby_switch_off[c, cl, t]) * 1000000
            else:
                return Constraint.Skip
        model._ramp_up_con = Constraint(model.CONVERSION_COMPONENTS, model.CLUSTERS, model.TIME, rule=_ramp_up_rule)

        def _ramp_down_rule(m, c, cl, t):
            main_input = pm_object.get_component(c).get_main_input()
            if t > 0:
                return (m.mass_energy_component_in_commodities[c, main_input, cl, t]
                        - m.mass_energy_component_in_commodities[c, main_input, cl, t - 1]) >= \
                       - (m.nominal_cap[c] * m.ramp_down[c] +
                          (m.status_off_switch_on[c, cl, t] + m.status_standby_switch_on[c, cl, t]) * 1000000)
            else:
                return Constraint.Skip
        model._ramp_down_con = Constraint(model.CONVERSION_COMPONENTS, model.CLUSTERS, model.TIME,
                                          rule=_ramp_down_rule)

        def shut_off_downtime_adherence_rule(m, c, cl, t):
            if m.down_time[c] + t > max(m.TIME):
                dt = max(m.TIME) - t + 1
            else:
                dt = m.down_time[c]

            if t > 0:
                return (m.status_off[c, cl, t] - m.status_off[c, cl, t - 1]) - sum(m.status_off[c, cl, t + i]
                                                                           for i in range(dt)) / dt <= 0
            else:
                return Constraint.Skip
        model.shut_off_downtime_adherence_con = Constraint(model.SHUT_DOWN_COMPONENTS, model.CLUSTERS, model.TIME,
                                                           rule=shut_off_downtime_adherence_rule)

        def hot_standby_downtime_adherence_rule(m, c, cl, t):
            if m.standby_time[c] + t > max(m.TIME):
                st = max(m.TIME) - t + 1
            else:
                st = m.standby_time[c]

            if t > 0:
                return (m.status_standby[c, cl, t] - m.status_standby[c, cl, t - 1]) - sum(m.status_stanby[c, cl, t + i]
                                                                                           for i in range(st)) / st <= 0
            else:
                return Constraint.Skip
        model.hot_standby_downtime_adherence_con = Constraint(model.STANDBY_COMPONENTS, model.CLUSTERS, model.TIME,
                                                              rule=hot_standby_downtime_adherence_rule)

        def lower_limit_hot_standby_demand_rule(m, c, me, cl, t):
            # Defines demand for hot standby
            hot_standby_commodity = [*pm_object.get_component(c).get_hot_standby_demand().keys()][0]
            hot_standby_demand = pm_object.get_component(c).get_hot_standby_demand()[hot_standby_commodity]
            if me == hot_standby_commodity:
                return m.mass_energy_hot_standby_demand[c, hot_standby_commodity, cl, t] \
                       >= m.nominal_cap[c] * hot_standby_demand + (m.status_standby[c, t] - 1) * 1000000
            else:
                return m.mass_energy_hot_standby_demand[c, me, cl, t] == 0
        model.lower_limit_hot_standby_demand_con = Constraint(model.STANDBY_COMPONENTS, model.COMMODITIES,
                                                              model.CLUSTERS, model.TIME,
                                                              rule=lower_limit_hot_standby_demand_rule)

        def upper_limit_hot_standby_demand_rule(m, c, cl, t):
            # Define that the hot standby demand is not higher than the capacity * demand per capacity
            hot_standby_commodity = [*pm_object.get_component(c).get_hot_standby_demand().keys()][0]
            hot_standby_demand = pm_object.get_component(c).get_hot_standby_demand()[hot_standby_commodity]
            return m.mass_energy_hot_standby_demand[c, hot_standby_commodity, cl, t] \
                   <= m.nominal_cap[c] * hot_standby_demand
        model.upper_limit_hot_standby_demand_con = Constraint(model.STANDBY_COMPONENTS, model.CLUSTERS, model.TIME,
                                                              rule=upper_limit_hot_standby_demand_rule)

        def hot_standby_binary_activation_rule(m, c, cl, t):
            # activates hot standby demand binary if component goes into hot standby
            hot_standby_commodity = [*pm_object.get_component(c).get_hot_standby_demand().keys()][0]
            return m.mass_energy_hot_standby_demand[c, hot_standby_commodity, cl, t] \
                   <= m.status_standby[c, cl, t] * 1000000
        model.hot_standby_binary_activation_con = Constraint(model.STANDBY_COMPONENTS, model.CLUSTERS, model.TIME,
                                                             rule=hot_standby_binary_activation_rule)

        """ Generation constraints """
        def power_generation_rule(m, g, gc, cl, t):
            generated_commodity = pm_object.get_component(g).get_generated_commodity()
            if gc == generated_commodity:
                if pm_object.get_component(g).get_curtailment_possible():
                    return m.mass_energy_generation[g, generated_commodity, cl, t] \
                           <= m.generation_profiles[g, cl, t] * m.nominal_cap[g]
                else:
                    return m.mass_energy_generation[g, generated_commodity, cl, t] \
                           == m.generation_profiles[g, cl, t] * m.nominal_cap[g]
            else:
                return m.mass_energy_generation[g, generated_commodity, cl, t] == 0
        model.power_generation_con = Constraint(model.GENERATORS, model.GENERATED_COMMODITIES,
                                                model.CLUSTERS, model.TIME,
                                                rule=power_generation_rule)

        def attach_fixed_capacity_rule(m, g):
            if pm_object.get_component(g).get_has_fixed_capacity():
                return m.nominal_cap[g] == m.generator_fixed_capacity[g]
            else:
                return Constraint.Skip
        model.attach_fixed_capacity_con = Constraint(model.GENERATORS, rule=attach_fixed_capacity_rule)

        def storage_balance_rule(m, s, cl, t):
            if t == 0:
                return Constraint.Skip
            else:
                return m.soc[s, cl, t] == m.soc[s, cl, t - 1] \
                       + m.mass_energy_storage_in_commodities[s, cl, t - 1] * m.charging_efficiency[s] \
                       - m.mass_energy_storage_out_commodities[s, cl, t - 1] / m.discharging_efficiency[s]

        model.storage_balance_con = Constraint(model.STORAGES, model.CLUSTERS, model.TIME, rule=storage_balance_rule)

        def last_soc_rule(m, s, cl, t):
            if t == max(m.TIME):
                return m.soc[s, cl, 0] == m.soc[s, cl, t] \
                       + m.mass_energy_storage_in_commodities[s, cl, t] * m.charging_efficiency[s] \
                       - m.mass_energy_storage_out_commodities[s, cl, t] / m.discharging_efficiency[s]
            else:
                return Constraint.Skip

        model.last_soc_con = Constraint(model.STORAGES, model.CLUSTERS, model.TIME, rule=last_soc_rule)

        def soc_max_bound_rule(m, s, cl, t):
            return m.soc[s, cl, t] <= m.maximal_soc[s] * m.nominal_cap[s]

        model.soc_max = Constraint(model.STORAGES, model.CLUSTERS, model.TIME, rule=soc_max_bound_rule)

        def soc_min_bound_rule(m, s, cl, t):
            return m.soc[s, cl, t] >= m.minimal_soc[s] * m.nominal_cap[s]

        model.soc_min = Constraint(model.STORAGES, model.CLUSTERS, model.TIME, rule=soc_min_bound_rule)

        def storage_charge_upper_bound_rule(m, s, cl, t):
            return m.mass_energy_storage_in_commodities[s, cl, t] <= m.nominal_cap[s] / \
                       m.ratio_capacity_p[s]
        model.storage_charge_upper_bound_con = Constraint(model.STORAGES, model.CLUSTERS, model.TIME,
                                                          rule=storage_charge_upper_bound_rule)

        def storage_discharge_upper_bound_rule(m, s, cl, t):
            return m.mass_energy_storage_out_commodities[s, cl, t] / m.discharging_efficiency[s] \
                       <= m.nominal_cap[s] / m.ratio_capacity_p[s]

        model.storage_discharge_upper_bound_con = Constraint(model.STORAGES, model.CLUSTERS, model.TIME,
                                                             rule=storage_discharge_upper_bound_rule)

        def storage_binary_sum_rule(m, s, cl, t):
            return m.storage_charge_binary[s, cl, t] + m.storage_discharge_binary[s, cl, t] <= 1
        model.storage_binary_sum_con = Constraint(model.STORAGES, model.CLUSTERS, model.TIME, rule=storage_binary_sum_rule)

        def charge_binary_activation_rule(m, s, cl, t):
            return m.mass_energy_storage_in_commodities[s, cl, t] - m.storage_charge_binary[s, cl, t] * 1000000 <= 0
        model.charge_binary_activation_con = Constraint(model.STORAGES, model.CLUSTERS, model.TIME, rule=charge_binary_activation_rule)

        def discharge_binary_activation_rule(m, s, cl, t):
            return m.mass_energy_storage_out_commodities[s, cl, t] - m.storage_discharge_binary[s, cl, t] * 1000000 <= 0

        model.discharge_binary_activation_con = Constraint(model.STORAGES, model.CLUSTERS, model.TIME,
                                                           rule=discharge_binary_activation_rule)

        """ Financial constraints """
        def calculate_investment_components_rule(m, c):
            if c not in m.SCALABLE_COMPONENTS:
                return m.investment[c] == m.nominal_cap[c] * m.capex_var[c] + m.capex_fix[c]
            else:
                return m.investment[c] == sum(m.nominal_cap_pre[c, i] * m.capex_pre_var[c, i]
                                              + m.capex_pre_fix[c, i] * m.capacity_binary[c, i]
                                              for i in m.INTEGER_STEPS)
        model.calculate_investment_components_con = Constraint(model.COMPONENTS,
                                                               rule=calculate_investment_components_rule)

        def objective_function(m):
            return (sum(m.investment[c] * m.ANF[c] for c in m.COMPONENTS)
                    + sum(m.investment[c] * m.fixed_om[c] for c in m.COMPONENTS)
                    + sum(m.mass_energy_storage_in_commodities[s, cl, t] * m.variable_om[s] * m.weightings[cl]
                          for t in m.TIME for cl in m.CLUSTERS for s in m.STORAGES)
                    + sum(m.mass_energy_component_out_commodities[c, pm_object.get_component(c).get_main_output(), cl, t]
                          * m.variable_om[c] * m.weightings[cl] for t in m.TIME for cl in m.CLUSTERS for c in m.CONVERSION_COMPONENTS)
                    + sum(m.mass_energy_generation[g, pm_object.get_component(g).get_generated_commodity(), cl, t]
                          * m.variable_om[g] * m.weightings[cl]
                          for t in m.TIME for cl in m.CLUSTERS for g in m.GENERATORS)
                    + sum(m.mass_energy_purchase_commodity[me, cl, t] * m.purchase_price[me, cl, t] * m.weightings[cl]
                          for t in m.TIME for cl in m.CLUSTERS for me in m.PURCHASABLE_COMMODITIES if
                          me in self.purchasable_commodities)
                    - sum(m.mass_energy_sell_commodity[me, cl, t] * m.selling_price[me, cl, t] * m.weightings[cl]
                          for t in m.TIME for cl in m.CLUSTERS for me in m.SALEABLE_COMMODITIES if
                          me in self.saleable_commodities)
                    + sum(m.status_off_switch_off[c, cl, t] * m.weightings[cl] * m.start_up_costs[c]
                          for t in m.TIME for cl in m.CLUSTERS for c in m.SHUT_DOWN_COMPONENTS))
        model.obj = Objective(rule=objective_function, sense=minimize)

        return model

    def optimize(self, instance=None):

        if (self.solver == 'cbc') | (self.solver == 'glpk'):
            opt = pyo.SolverFactory(self.solver)
        else:
            opt = pyo.SolverFactory(self.solver, solver_io="python")

        opt.options["mipgap"] = 0.01
        if instance is None:
            instance = self.model.create_instance()
            results = opt.solve(instance, tee=True)
        else:
            results = opt.solve(instance, tee=True, warmstart=True)

        print(results)

        return instance, results

    def reset_information(self):
        self.input_tuples, self.input_conversion_tuples, self.input_conversion_tuples_dict, \
            self.output_tuples, self.output_conversion_tuples, self.output_conversion_tuples_dict \
            = self.pm_object.get_all_conversion()

    def __init__(self, pm_object, solver):

        # ----------------------------------
        # Set up problem
        self.solver = solver
        self.instance = None
        self.pm_object = pm_object

        self.pm_object = self.clone_components_which_use_parallelization()

        self.annuity_factor_dict = self.pm_object.get_annuity_factor()

        self.lifetime_dict, self.fixed_om_dict, self.variable_om_dict, self.capex_var_dict, self.capex_fix_dict,\
            self.minimal_power_dict, \
            self.maximal_power_dict, self.ramp_up_dict, self.ramp_down_dict, self.scaling_capex_var_dict, \
            self.scaling_capex_fix_dict, self.scaling_capex_upper_bound_dict, self.scaling_capex_lower_bound_dict, \
            self.shut_down_down_time_dict, self.shut_down_start_up_costs, self.standby_down_time_dict, \
            self.charging_efficiency_dict, self.discharging_efficiency_dict, \
            self.minimal_soc_dict, self.maximal_soc_dict, \
            self.ratio_capacity_power_dict, self.fixed_capacity_dict = self.pm_object.get_all_component_parameters()

        self.scalable_components, self.not_scalable_components, self.shut_down_components,\
            self.no_shut_down_components, self.standby_components,\
            self.no_standby_components = self.pm_object.get_conversion_component_sub_sets()

        self.final_commodities, self.available_commodities, self.emittable_commodities, self.purchasable_commodities,\
            self.saleable_commodities, self.demanded_commodities, self.total_demand_commodities, self.generated_commodities, \
            self.all_inputs, self.all_outputs = self.pm_object.get_commodity_sets()

        self.input_tuples, self.input_conversion_tuples, self.input_conversion_tuples_dict, \
            self.output_tuples, self.output_conversion_tuples, self.output_conversion_tuples_dict\
            = self.pm_object.get_all_conversions()

        self.generation_profiles_dict = self.pm_object.get_generation_time_series()
        self.demand_dict = self.pm_object.get_demand_time_series()
        self.purchase_price_dict = self.pm_object.get_purchase_price_time_series()
        self.sell_price_dict = self.pm_object.get_sale_price_time_series()
        self.weightings_dict = self.pm_object.get_weightings_time_series()

        self.all_components = self.pm_object.get_final_components_names()
        self.conversion_components = self.pm_object.get_final_conversion_components_names()
        self.generator_components = self.pm_object.get_final_generator_components_names()
        self.storage_components = self.pm_object.get_final_storage_components_names()

        self.scalable_components = self.pm_object.get_final_scalable_conversion_components_names()
        self.shut_down_components = self.pm_object.get_final_shut_down_conversion_components_names()
        self.standby_components = self.pm_object.get_final_standby_conversion_components_names()

        # Create optimization program
        self.model = ConcreteModel()
        self.model.TIME = RangeSet(0, self.pm_object.get_covered_period() - 1)
        self.model.CLUSTERS = RangeSet(0, self.pm_object.get_number_clusters() - 1)
        self.attach_weightings_time_series_to_optimization_problem()
        self.model.INTEGER_STEPS = RangeSet(0, self.pm_object.integer_steps)
        # self.model.pwconst = Piecewise(indexes, yvar, xvar, **Keywords) # todo: Implement with big m
        # https://pyomo.readthedocs.io/en/stable/pyomo_self.modeling_components/Expressions.html
        self.model.M = Param(initialize=1000000000)

        # Attach Sets
        self.attach_component_sets_to_optimization_problem()
        self.attach_commodity_sets_to_optimization_problem()

        self.attach_scalable_component_sets_to_optimization_problem()
        self.attach_shut_down_component_sets_to_optimization_problem()
        self.attach_standby_component_sets_to_optimization_problem()

        # Attach Parameters
        self.attach_component_parameters_to_optimization_problem()
        self.attach_annuity_to_optimization_problem()

        self.attach_scalable_component_parameters_to_optimization_problem()
        self.attach_shut_down_component_parameters_to_optimization_problem()
        self.attach_standby_component_parameters_to_optimization_problem()

        # Attach Variables
        self.attach_component_variables_to_optimization_problem()
        self.attach_scalable_component_variables_to_optimization_problem()

        self.attach_commodity_variables_to_optimization_problem()
        self.attach_purchase_price_time_series_to_optimization_problem()
        self.attach_sale_price_time_series_to_optimization_problem()
        self.attach_demand_time_series_to_optimization_problem()
        self.attach_generation_time_series_to_optimization_problem()

        self.model = self.attach_constraints()

        self.instance, self.results = self.optimize()

        # print(self.instance.pprint())
