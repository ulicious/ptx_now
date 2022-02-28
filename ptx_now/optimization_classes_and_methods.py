import pyomo.environ
import pyomo.environ as pyo
from pyomo.core import *
import pandas as pd
from pyomo.core import Binary
from copy import deepcopy
from pyomo.opt import SolverStatus, TerminationCondition


class OptimizationProblem:

    def clone_components_which_use_parallelization(self):
        pm_object_copy = deepcopy(self.pm_object)

        # Copy components if number of components in system is higher than 1
        for component_object in pm_object_copy.get_final_conversion_components_objects():
            if component_object.get_number_parallel_units() > 1:
                # Simply rename first component
                component_name = component_object.get_name()
                component_nice_name = component_object.get_nice_name()
                component_object.set_name(component_name + '_0')
                component_object.set_nice_name(component_nice_name + ' Parallel Unit 0')
                pm_object_copy.remove_component_entirely(component_name)
                pm_object_copy.add_component(component_name + '_0', component_object)

                for i in range(1, int(component_object.get_number_parallel_units())):
                    # Add other components as copy
                    parallel_unit_component_name = component_name + '_' + str(i)
                    parallel_unit_component_nice_name = component_nice_name + ' Parallel Unit ' + str(i)
                    component_copy = component_object.__copy__()
                    component_copy.set_name(parallel_unit_component_name)
                    component_copy.set_nice_name(parallel_unit_component_nice_name)
                    pm_object_copy.add_component(parallel_unit_component_name, component_copy)

                for i in range(0, int(component_object.get_number_parallel_units())):
                    exclude = ['wacc', 'covered_period']
                    parallel_unit_component_name = component_name + '_' + str(i)
                    for p in self.pm_object.get_general_parameters():
                        if p in exclude:
                            continue
                        pm_object_copy.set_applied_parameter_for_component(p,
                                                                           parallel_unit_component_name,
                                                                           self.pm_object.get_applied_parameter_for_component(p, component_name))

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
        self.model.ME_STREAMS = Set(initialize=self.final_commodities)  # Mass energy commodity
        self.model.AVAILABLE_STREAMS = Set(initialize=self.available_commodities)
        self.model.EMITTED_STREAMS = Set(initialize=self.emittable_commodities)
        self.model.PURCHASABLE_STREAMS = Set(initialize=self.purchasable_commodities)
        self.model.SALEABLE_STREAMS = Set(initialize=self.saleable_commodities)
        self.model.DEMANDED_STREAMS = Set(initialize=self.demanded_commodities)
        self.model.TOTAL_DEMANDED_STREAMS = Set(initialize=self.total_demand_commodities)
        self.model.GENERATED_STREAMS = Set(initialize=self.generated_commodities)

    def attach_general_parameters_to_optimization_problem(self):
        general_parameters = self.pm_object.get_general_parameter_value_dictionary()

        self.model.wacc = Param(initialize=general_parameters['wacc'])
        self.model.taxes_and_insurance = Param(initialize=general_parameters['taxes_and_insurance'])
        self.model.overhead = Param(initialize=general_parameters['overhead'])
        self.model.working_capital = Param(initialize=general_parameters['working_capital'])
        self.model.personnel_cost = Param(initialize=general_parameters['personnel_costs'])

    def attach_annuity_to_optimization_problem(self):
        self.model.ANF = Param(self.model.COMPONENTS, initialize=self.annuity_factor_dict)

    def attach_component_parameters_to_optimization_problem(self):
        self.model.lifetime = Param(self.model.COMPONENTS, initialize=self.lifetime_dict)
        self.model.maintenance = Param(self.model.COMPONENTS, initialize=self.maintenance_dict)

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

        self.model.status_on = Var(self.model.CONVERSION_COMPONENTS, self.model.TIME, within=Binary)

        self.model.status_off = Var(self.model.CONVERSION_COMPONENTS, self.model.TIME, within=Binary)
        self.model.status_off_switch_on = Var(self.model.CONVERSION_COMPONENTS, self.model.TIME, within=Binary)
        self.model.status_off_switch_off = Var(self.model.CONVERSION_COMPONENTS, self.model.TIME, within=Binary)
        self.model.start_up_costs_component = Var(self.model.CONVERSION_COMPONENTS, self.model.TIME, bounds=(0, None))
        self.model.total_start_up_costs_component = Var(self.model.CONVERSION_COMPONENTS, bounds=(0, None))
        self.model.total_start_up_costs = Var(bounds=(0, None))

        self.model.status_standby = Var(self.model.CONVERSION_COMPONENTS, self.model.TIME, within=Binary)

        # STORAGE binaries (charging and discharging)
        self.model.storage_charge_binary = Var(self.model.STORAGES, self.model.TIME, within=Binary)
        self.model.storage_discharge_binary = Var(self.model.STORAGES, self.model.TIME, within=Binary)

        self.model.investment = Var(self.model.COMPONENTS, bounds=(0, None))
        self.model.annuity = Var(self.model.COMPONENTS, bounds=(0, None))
        self.model.total_annuity = Var(bounds=(0, None))
        self.model.maintenance_costs = Var(self.model.COMPONENTS, bounds=(0, None))
        self.model.total_maintenance_costs = Var(bounds=(0, None))
        self.model.taxes_and_insurance_costs = Var(self.model.COMPONENTS, bounds=(0, None))
        self.model.total_taxes_and_insurance_costs = Var(bounds=(0, None))
        self.model.overhead_costs = Var(self.model.COMPONENTS, bounds=(0, None))
        self.model.total_overhead_costs = Var(bounds=(0, None))
        self.model.personnel_costs = Var(self.model.COMPONENTS, bounds=(0, None))
        self.model.total_personnel_costs = Var(bounds=(0, None))
        self.model.working_capital_costs = Var(self.model.COMPONENTS, bounds=(0, None))
        self.model.total_working_capital_costs = Var(bounds=(0, None))
        self.model.purchase_costs = Var(self.model.PURCHASABLE_STREAMS, bounds=(0, None))
        self.model.total_purchase_costs = Var(bounds=(0, None))
        self.model.revenue = Var(self.model.SALEABLE_STREAMS, bounds=(None, None))
        self.model.total_revenue = Var(bounds=(None, None))

    def set_scalable_component_capacity_bound_rule(self, s, i):
        return 0, self.scaling_capex_upper_bound_dict[(s, i)]

    def attach_scalable_component_variables_to_optimization_problem(self):

        self.model.nominal_cap_pre = Var(self.model.SCALABLE_COMPONENTS, self.model.INTEGER_STEPS,
                                         bounds=self.set_scalable_component_capacity_bound_rule)
        self.model.capacity_binary = Var(self.model.SCALABLE_COMPONENTS, self.model.INTEGER_STEPS, within=Binary)

    def attach_commodity_variables_to_optimization_problem(self):

        # -------------------------------------
        # Commodity variables
        # Input and output commodity of component
        self.model.mass_energy_component_in_commodities = Var(self.model.CONVERSION_COMPONENTS, self.model.ME_STREAMS,
                                                     self.model.TIME, bounds=(0, None))
        self.model.mass_energy_component_out_commodities = Var(self.model.CONVERSION_COMPONENTS, self.model.ME_STREAMS,
                                                      self.model.TIME, bounds=(0, None))

        # Freely available commodities
        self.model.mass_energy_available = Var(self.model.ME_STREAMS, self.model.TIME, bounds=(0, None))
        self.model.mass_energy_emitted = Var(self.model.ME_STREAMS, self.model.TIME, bounds=(0, None))

        # Charged and discharged commodities
        self.model.mass_energy_storage_in_commodities = Var(self.model.ME_STREAMS, self.model.TIME, bounds=(0, None))
        self.model.mass_energy_storage_out_commodities = Var(self.model.ME_STREAMS, self.model.TIME, bounds=(0, None))
        self.model.soc = Var(self.model.ME_STREAMS, self.model.TIME, bounds=(0, None))

        # sold and purchased commodities
        self.model.mass_energy_sell_commodity = Var(self.model.ME_STREAMS, self.model.TIME, bounds=(0, None))
        self.model.mass_energy_purchase_commodity = Var(self.model.ME_STREAMS, self.model.TIME, bounds=(0, None))

        # generated commodities
        self.model.mass_energy_generation = Var(self.model.GENERATORS, self.model.ME_STREAMS, self.model.TIME,
                                                bounds=(0, None))
        self.model.mass_energy_total_generation = Var(self.model.ME_STREAMS, self.model.TIME, bounds=(0, None))

        # Demanded commodities
        self.model.mass_energy_demand = Var(self.model.ME_STREAMS, self.model.TIME, bounds=(0, None))

        # Hot standby demand
        self.model.mass_energy_hot_standby_demand = Var(self.model.CONVERSION_COMPONENTS, self.model.ME_STREAMS,
                                                        self.model.TIME, bounds=(0, None))

    def attach_purchase_price_time_series_to_optimization_problem(self):
        self.model.purchase_price = Param(self.model.PURCHASABLE_STREAMS, self.model.TIME,
                                          initialize=self.purchase_price_dict)

    def attach_sale_price_time_series_to_optimization_problem(self):
        self.model.selling_price = Param(self.model.SALEABLE_STREAMS, self.model.TIME, initialize=self.sell_price_dict)

    def attach_demand_time_series_to_optimization_problem(self):
        self.model.commodity_demand = Param(self.model.DEMANDED_STREAMS, self.model.TIME, initialize=self.demand_dict)

    def attach_generation_time_series_to_optimization_problem(self):
        self.model.generation_profiles = Param(self.model.GENERATORS, self.model.TIME,
                                               initialize=self.generation_profiles_dict)

    def attach_weightings_time_series_to_optimization_problem(self):
        self.model.weightings = Param(self.model.TIME, initialize=self.weightings_dict)

    def attach_constraints(self):
        """ Method attaches all constraints to optimization problem """

        pm_object = self.pm_object
        model = self.model

        def _mass_energy_balance_rule(m, me_out, t):
            # Sets mass energy balance for all components
            # produced (out), generated, discharged, available and purchased commodities
            #   = emitted, sold, demanded, charged and used (in) commodities
            commodity_object = pm_object.get_commodity(me_out)
            equation_lhs = []
            equation_rhs = []

            if commodity_object.is_available():
                equation_lhs.append(m.mass_energy_available[me_out, t])
            if commodity_object.is_emittable():
                equation_lhs.append(-m.mass_energy_emitted[me_out, t])
            if commodity_object.is_purchasable():
                equation_lhs.append(m.mass_energy_purchase_commodity[me_out, t])
            if commodity_object.is_saleable():
                equation_lhs.append(-m.mass_energy_sell_commodity[me_out, t])
            if commodity_object.is_demanded():
                equation_lhs.append(-m.mass_energy_demand[me_out, t])
            if me_out in m.STORAGES:
                equation_lhs.append(
                    m.mass_energy_storage_out_commodities[me_out, t] - m.mass_energy_storage_in_commodities[
                        me_out, t])
            if me_out in m.GENERATED_STREAMS:
                equation_lhs.append(m.mass_energy_total_generation[me_out, t])

            for c in m.CONVERSION_COMPONENTS:
                if (c, me_out) in self.output_tuples:
                    equation_lhs.append(m.mass_energy_component_out_commodities[c, me_out, t])

                if (c, me_out) in self.input_tuples:
                    equation_rhs.append(m.mass_energy_component_in_commodities[c, me_out, t])

                # hot standby demand
                if c in m.STANDBY_COMPONENTS:
                    hot_standby_commodity = [*pm_object.get_component(c).get_hot_standby_demand().keys()][0]
                    if me_out == hot_standby_commodity:
                        equation_rhs.append(m.mass_energy_hot_standby_demand[c, me_out, t])

            return sum(equation_lhs) == sum(equation_rhs)
        model._mass_energy_balance_con = Constraint(model.ME_STREAMS, model.TIME, rule=_mass_energy_balance_rule)

        def _set_available_commodities_rule(m, me, t):
            # Sets commodities, which are available without limit and price
            if me in m.AVAILABLE_STREAMS:
                return m.mass_energy_available[me, t] >= 0
            else:
                return m.mass_energy_available[me, t] == 0
        model.set_available_commodities_con = Constraint(model.ME_STREAMS, model.TIME, rule=_set_available_commodities_rule)

        def _set_emitted_commodities_rule(m, me, t):
            # Sets commodities, which are emitted without limit and price
            if me in m.EMITTED_STREAMS:
                return m.mass_energy_emitted[me, t] >= 0
            else:
                return m.mass_energy_emitted[me, t] == 0

        model.set_emitted_commodities_con = Constraint(model.ME_STREAMS, model.TIME, rule=_set_emitted_commodities_rule)

        def _set_saleable_commodities_rule(m, me, t):
            # Sets commodities, which are sold without limit but for a certain price
            if me in m.SALEABLE_STREAMS:
                return m.mass_energy_sell_commodity[me, t] >= 0
            else:
                return m.mass_energy_sell_commodity[me, t] == 0
        model.set_saleable_commodities_con = Constraint(model.ME_STREAMS, model.TIME, rule=_set_saleable_commodities_rule)

        def _set_purchasable_commodities_rule(m, me, t):
            # Sets commodities, which are purchased without limit but for a certain price
            if me in m.PURCHASABLE_STREAMS:
                return m.mass_energy_purchase_commodity[me, t] >= 0
            else:
                return m.mass_energy_purchase_commodity[me, t] == 0
        model.set_purchasable_commodities_con = Constraint(model.ME_STREAMS, model.TIME, rule=_set_purchasable_commodities_rule)

        def _demand_satisfaction_rule(m, me, t):
            # Sets commodities, which are demanded
            if me in m.DEMANDED_STREAMS:  # Case with demand
                if me not in m.TOTAL_DEMANDED_STREAMS:  # Case where demand needs to be satisfied in every t
                    return m.mass_energy_demand[me, t] >= m.commodity_demand[me, t]
                else:
                    return Constraint.Skip
            else:  # Case without demand
                return m.mass_energy_demand[me, t] == 0
        model.demand_satisfaction_con = Constraint(model.ME_STREAMS, model.TIME, rule=_demand_satisfaction_rule)

        def _total_demand_satisfaction_rule(m, me):
            return sum(m.mass_energy_demand[me, t] * m.weightings[t] for t in m.TIME) \
                       >= m.commodity_demand[me, 0]
        model.total_demand_satisfaction_con = Constraint(model.TOTAL_DEMANDED_STREAMS,
                                                         rule=_total_demand_satisfaction_rule)

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
            return m.nominal_cap_pre[c, i] >= self.lower_bound_dict[c, i] * m.capacity_binary[c, i]
        model.set_lower_bound_con = Constraint(model.SCALABLE_COMPONENTS, model.INTEGER_STEPS,
                                               rule=set_lower_bound_rule)

        def final_capacity_rule(m, c):
            # Final capacity of component is sum of capacity over all integer steps
            return m.nominal_cap[c] == sum(m.nominal_cap_pre[c, i] for i in m.INTEGER_STEPS)
        model.final_capacity_con = Constraint(model.SCALABLE_COMPONENTS, rule=final_capacity_rule)

        def _commodity_conversion_output_rule(m, c, me_out, t):
            # Define ratio between main input and output commodities for all conversion tuples
            main_input = pm_object.get_component(c).get_main_input()
            if (c, main_input, me_out) in self.output_conversion_tuples:
                return m.mass_energy_component_out_commodities[c, me_out, t] == \
                       m.mass_energy_component_in_commodities[c, main_input, t] \
                       * self.output_conversion_tuples_dict[c, main_input, me_out]
            else:
                return m.mass_energy_component_out_commodities[c, me_out, t] == 0
        model._commodity_conversion_output_con = Constraint(model.CONVERSION_COMPONENTS, model.ME_STREAMS, model.TIME,
                                                         rule=_commodity_conversion_output_rule)

        def _commodity_conversion_input_rule(m, c, me_in, t):
            # Define ratio between main input and other input commodities for all conversion tuples
            main_input = pm_object.get_component(c).get_main_input()
            if me_in == main_input:
                return Constraint.Skip
            else:
                if (c, main_input, me_in) in self.input_conversion_tuples:
                    return m.mass_energy_component_in_commodities[c, me_in, t] == \
                           m.mass_energy_component_in_commodities[c, main_input, t] \
                           * self.input_conversion_tuples_dict[c, main_input, me_in]
                else:
                    return m.mass_energy_component_in_commodities[c, me_in, t] == 0
        model._commodity_conversion_input_con = Constraint(model.CONVERSION_COMPONENTS, model.ME_STREAMS, model.TIME,
                                                        rule=_commodity_conversion_input_rule)

        def balance_component_status_rule(m, c, t):
            # The component is either on, off or in hot standby
            return m.status_on[c, t] + m.status_off[c, t] + m.status_standby[c, t] == 1
        model.balance_component_status_con = Constraint(model.CONVERSION_COMPONENTS, model.TIME,
                                                        rule=balance_component_status_rule)

        def component_no_shutdown_or_standby_rule(m, c, t):
            # If component can not be shut off or put in hot standby, the status is always on
            if (c not in m.SHUT_DOWN_COMPONENTS) & (c not in m.STANDBY_COMPONENTS):
                return m.status_on[c, t] == 1
            elif c not in m.SHUT_DOWN_COMPONENTS:
                return m.status_off[c, t] == 0
            elif c not in m.STANDBY_COMPONENTS:
                return m.status_standby[c, t] == 0
            else:
                return Constraint.Skip
        model.component_no_shutdown_or_standby_con = Constraint(model.CONVERSION_COMPONENTS, model.TIME,
                                                                rule=component_no_shutdown_or_standby_rule)

        def _active_component_rule(m, c, me_in, t):
            # Set binary to 1 if component is active
            main_input = pm_object.get_component(c).get_main_input()
            if me_in == main_input:
                return m.mass_energy_component_in_commodities[c, me_in, t] \
                       - m.status_on[c, t] * 1000000 <= 0
            else:
                return Constraint.Skip
        model._active_component_con = Constraint(model.CONVERSION_COMPONENTS, model.ME_STREAMS, model.TIME,
                                                 rule=_active_component_rule)

        def status_off_switch_rule(m, c, t):
            if t > 0:
                return m.status_off[c, t] == m.status_off[c, t - 1] + m.status_off_switch_on[c, t] \
                       - m.status_off_switch_off[c, t]
            else:
                return Constraint.Skip
        model.status_off_switch_con = Constraint(model.CONVERSION_COMPONENTS, model.TIME,
                                                 rule=status_off_switch_rule)

        def balance_status_off_switch_rule(m, c, t):
            return m.status_off_switch_on[c, t] + m.status_off_switch_off[c, t] <= 1
        model.balance_status_off_switch_con = Constraint(model.CONVERSION_COMPONENTS, model.TIME,
                                                         rule=balance_status_off_switch_rule)

        def _conversion_maximal_component_capacity_rule(m, c, me_in, t):
            # Limits conversion on capacity of conversion unit and defines conversions
            # Important: Capacity is always matched with input
            main_input = pm_object.get_component(c).get_main_input()
            if me_in == main_input:
                return m.mass_energy_component_in_commodities[c, me_in, t] <= m.nominal_cap[c] * m.max_p[c]
            else:
                return Constraint.Skip
        model._conversion_maximal_component_capacity_con = Constraint(model.CONVERSION_COMPONENTS, model.ME_STREAMS,
                                                                      model.TIME,
                                                                      rule=_conversion_maximal_component_capacity_rule)

        def _conversion_minimal_component_capacity_rule(m, c, me_in, t):
            main_input = pm_object.get_component(c).get_main_input()
            if me_in == main_input:
                return m.mass_energy_component_in_commodities[c, me_in, t] \
                       >= m.nominal_cap[c] * m.min_p[c] + (m.status_on[c, t] - 1) * 1000000
            else:
                return Constraint.Skip
        model._conversion_minimal_component_capacity_con = Constraint(model.CONVERSION_COMPONENTS, model.ME_STREAMS,
                                                                      model.TIME,
                                                                      rule=_conversion_minimal_component_capacity_rule)

        def _ramp_up_rule(m, c, me_in, t):
            main_input = pm_object.get_component(c).get_main_input()
            if me_in == main_input:
                if t > 0:
                    return (m.mass_energy_component_in_commodities[c, me_in, t]
                            - m.mass_energy_component_in_commodities[c, me_in, t - 1]) <= \
                           m.nominal_cap[c] * m.ramp_up[c] + (m.status_off[c, t] + m.status_standby[c, t]) * 1000000
                else:
                    return Constraint.Skip
            else:
                return Constraint.Skip
        model._ramp_up_con = Constraint(model.CONVERSION_COMPONENTS, model.ME_STREAMS, model.TIME, rule=_ramp_up_rule)

        def _ramp_down_rule(m, c, me_in, t):
            main_input = pm_object.get_component(c).get_main_input()
            if me_in == main_input:
                if t > 0:
                    return (m.mass_energy_component_in_commodities[c, me_in, t]
                            - m.mass_energy_component_in_commodities[c, me_in, t - 1]) >= \
                           - (m.nominal_cap[c] * m.ramp_down[c] +
                              (m.status_off[c, t] + m.status_standby[c, t]) * 1000000)
                else:
                    return Constraint.Skip
            else:
                return Constraint.Skip
        model._ramp_down_con = Constraint(model.CONVERSION_COMPONENTS, model.ME_STREAMS, model.TIME,
                                          rule=_ramp_down_rule)

        if not self.pm_object.get_uses_representative_periods():

            def shut_off_downtime_adherence_rule(m, c, t):
                if m.down_time[c] + t > max(m.TIME):
                    dt = max(m.TIME) - t + 1
                else:
                    dt = m.down_time[c]

                if t > 0:
                    return (m.status_off[c, t] - m.status_off[c, t - 1]) - sum(m.status_off[c, t + i]
                                                                               for i in range(dt)) / dt <= 0
                else:
                    return Constraint.Skip

            model.shut_off_downtime_adherence_con = Constraint(model.SHUT_DOWN_COMPONENTS, model.TIME,
                                                               rule=shut_off_downtime_adherence_rule)

            def hot_standby_downtime_adherence_rule(m, c, t):
                if m.standby_time[c] + t > max(m.TIME):
                    st = max(m.TIME) - t + 1
                else:
                    st = m.standby_time[c]

                if t > 0:
                    return (m.status_standby[c, t] - m.status_standby[c, t - 1]) - sum(m.status_stanby[c, t + i]
                                                                                       for i in range(st)) / st <= 0

            model.hot_standby_downtime_adherence_con = Constraint(model.STANDBY_COMPONENTS, model.TIME,
                                                                  rule=hot_standby_downtime_adherence_rule)

        else:

            def shut_off_downtime_adherence_with_representative_periods_rule(m, c, t):
                period_length = self.pm_object.get_representative_periods_length()
                past_periods = floor(t / period_length)
                if period_length - (t - past_periods * period_length) < m.down_time[c]:
                    dt = int(period_length - (t - past_periods * period_length))
                else:
                    dt = int(m.down_time[c])

                if t > 0:
                    return (m.status_off[c, t] - m.status_off[c, t - 1]) - sum(m.status_off[c, t + i]
                                                                               for i in range(dt)) / dt <= 0
                else:
                    return Constraint.Skip

            model.shut_off_downtime_adherence_with_representative_periods_con = Constraint(model.SHUT_DOWN_COMPONENTS,
                                                                                           model.TIME,
                                                                                           rule=shut_off_downtime_adherence_with_representative_periods_rule)

            def hot_standby_downtime_adherence_with_representative_periods_rule(m, c, t):
                # In case of representative periods, the component is in standby maximal until end of week
                period_length = self.pm_object.get_representative_periods_length()
                past_periods = floor(t / period_length)
                if period_length - (t - past_periods * period_length) < m.standby_time[c]:
                    st = int(period_length - (t - past_periods * period_length))
                else:
                    st = int(m.standby_time[c])

                return (st - m.status_standby_switch_on[c, t] * st) >= sum(m.status_on_switch_on[c, t + i]
                                                                           for i in range(0, st))
            model.hot_standby_downtime_adherence_with_representative_rule = Constraint(model.STANDBY_COMPONENTS,
                                                                                       model.TIME,
                                                                                       rule=hot_standby_downtime_adherence_with_representative_periods_rule)

        def lower_limit_hot_standby_demand_rule(m, c, me, t):
            # Defines demand for hot standby
            if c in m.STANDBY_COMPONENTS:
                hot_standby_commodity = [*pm_object.get_component(c).get_hot_standby_demand().keys()][0]
                hot_standby_demand = pm_object.get_component(c).get_hot_standby_demand()[hot_standby_commodity]
                if me == hot_standby_commodity:
                    return m.mass_energy_hot_standby_demand[c, me, t] \
                           >= m.nominal_cap[c] * hot_standby_demand + (m.status_standby[c, t] - 1) * 1000000
                else:
                    return m.mass_energy_hot_standby_demand[c, me, t] == 0
            else:
                return m.mass_energy_hot_standby_demand[c, me, t] == 0
        model.lower_limit_hot_standby_demand_con = Constraint(model.CONVERSION_COMPONENTS, model.ME_STREAMS, model.TIME,
                                                  rule=lower_limit_hot_standby_demand_rule)

        def upper_limit_hot_standby_demand_rule(m, c, me, t):
            # Define that the hot standby demand is not higher than the capacity * demand per capacity
            hot_standby_commodity = [*pm_object.get_component(c).get_hot_standby_demand().keys()][0]
            hot_standby_demand = pm_object.get_component(c).get_hot_standby_demand()[hot_standby_commodity]
            if me == hot_standby_commodity:
                return m.mass_energy_hot_standby_demand[c, me, t] <= m.nominal_cap[c] * hot_standby_demand
            else:
                return Constraint.Skip
        model.upper_limit_hot_standby_demand_con = Constraint(model.STANDBY_COMPONENTS, model.ME_STREAMS, model.TIME,
                                                              rule=upper_limit_hot_standby_demand_rule)

        def hot_standby_binary_activation_rule(m, c, me, t):
            # activates hot standby demand binary if component goes into hot standby
            hot_standby_commodity = [*pm_object.get_component(c).get_hot_standby_demand().keys()][0]
            if me == hot_standby_commodity:
                return m.mass_energy_hot_standby_demand[c, me, t] <= m.status_standby[c, t] * 1000000
            else:
                return Constraint.Skip
        model.hot_standby_binary_activation_con = Constraint(model.STANDBY_COMPONENTS, model.ME_STREAMS, model.TIME,
                                                             rule=hot_standby_binary_activation_rule)

        """ Generation constraints """
        def power_generation_rule(m, g, me, t):
            if me == pm_object.get_component(g).get_generated_commodity():
                if pm_object.get_component(g).get_curtailment_possible():
                    return m.mass_energy_generation[g, me, t] <= m.generation_profiles[g, t] * m.nominal_cap[g]
                else:
                    return m.mass_energy_generation[g, me, t] == m.generation_profiles[g, t] * m.nominal_cap[g]
            else:
                return m.mass_energy_generation[g, me, t] == 0
        model.power_generation_con = Constraint(model.GENERATORS, model.ME_STREAMS, model.TIME,
                                                rule=power_generation_rule)

        def total_power_generation_rule(m, me, t):
            return m.mass_energy_total_generation[me, t] == sum(m.mass_energy_generation[g, me, t]
                                                                for g in m.GENERATORS)
        model.total_power_generation_con = Constraint(model.ME_STREAMS, model.TIME, rule=total_power_generation_rule)

        if not self.pm_object.get_uses_representative_periods():

            def storage_balance_rule(m, me, t):
                if me in m.STORAGES:
                    if t == 0:
                        return Constraint.Skip
                    else:
                        return m.soc[me, t] == m.soc[me, t - 1] \
                               + m.mass_energy_storage_in_commodities[me, t - 1] * m.charging_efficiency[me] \
                               - m.mass_energy_storage_out_commodities[me, t - 1] / m.discharging_efficiency[me]
                else:
                    return m.soc[me, t] == 0

            model.storage_balance_con = Constraint(model.ME_STREAMS, model.TIME, rule=storage_balance_rule)

            def last_soc_rule(m, me, t):
                if t == max(m.TIME):
                    return m.soc[me, 0] == m.soc[me, t] \
                           + m.mass_energy_storage_in_commodities[me, t] * m.charging_efficiency[me] \
                           - m.mass_energy_storage_out_commodities[me, t] / m.discharging_efficiency[me]
                else:
                    return Constraint.Skip

            model.last_soc_con = Constraint(model.STORAGES, model.TIME, rule=last_soc_rule)

        else:
            def storage_balance_with_representative_periods_rule(m, me, t):
                # Defines the SOC of the storage unit
                if me in m.STORAGES:
                    period_length = self.pm_object.get_representative_periods_length()
                    if t % period_length == 0:  # First hours SOC are not defined
                        return Constraint.Skip
                    else:
                        return m.soc[me, t] == m.soc[me, t - 1] \
                               + m.mass_energy_storage_in_commodities[me, t - 1] * m.charging_efficiency[me] \
                               - m.mass_energy_storage_out_commodities[me, t - 1] / m.discharging_efficiency[me]
                else:
                    return m.soc[me, t] == 0

            model.storage_balance_with_representative_periods_con = Constraint(model.ME_STREAMS, model.TIME,
                                                                               rule=storage_balance_with_representative_periods_rule)

            def discharging_with_representative_periods_rule(m, me, t):
                # This constraint defines the discharging at time steps from the last hour in the previous repr. period
                # to the first hour of the following repr. period
                period_length = self.pm_object.get_representative_periods_length()
                if t > 0:
                    if t % period_length == 0:
                        return m.soc[me, t - 1] - m.minimal_soc[me] * m.nominal_cap[me] >= \
                               m.mass_energy_storage_out_commodities[me, t - 1] / m.discharging_efficiency[me]
                    else:
                        return Constraint.Skip
                else:
                    return Constraint.Skip

            model.discharging_with_representative_periods_con = Constraint(model.STORAGES, model.TIME,
                                                                           rule=discharging_with_representative_periods_rule)

            def charging_with_representative_periods_rule(m, me, t):
                # This constraint defines the charging at time steps from the last hour in the previous repr. period
                # to the first hour of the following repr. period
                period_length = self.pm_object.get_representative_periods_length()
                if t > 0:
                    if t % period_length == 0:
                        return m.maximal_soc[me] * m.nominal_cap[me] - m.soc[me, t - 1] >= \
                               m.mass_energy_storage_in_commodities[me, t - 1] * m.charging_efficiency[me]
                    else:
                        return Constraint.Skip
                else:
                    return Constraint.Skip

            model.charging_with_representative_periods_con = Constraint(model.STORAGES, model.TIME,
                                                                        rule=charging_with_representative_periods_rule)

            def last_soc_representative_periods_rule(m, me, t):
                period_length = self.pm_object.get_representative_periods_length()
                if t % period_length == 0:
                    return m.soc[me, t] == m.soc[me, t + period_length - 1] \
                           + m.mass_energy_storage_in_commodities[me, t + period_length - 1] * m.charging_efficiency[me] \
                           - m.mass_energy_storage_out_commodities[me, t + period_length - 1] / m.discharging_efficiency[me]
                else:
                    return Constraint.Skip

            model.last_soc_representative_periods_con = Constraint(model.STORAGES, model.TIME, rule=last_soc_representative_periods_rule)

        def soc_max_bound_rule(m, me, t):
            return m.soc[me, t] <= m.maximal_soc[me] * m.nominal_cap[me]

        model.soc_max = Constraint(model.STORAGES, model.TIME, rule=soc_max_bound_rule)

        def soc_min_bound_rule(m, me, t):
            return m.soc[me, t] >= m.minimal_soc[me] * m.nominal_cap[me]

        model.soc_min = Constraint(model.STORAGES, model.TIME, rule=soc_min_bound_rule)

        def storage_charge_upper_bound_rule(m, me, t):
            if me in m.STORAGES:
                return m.mass_energy_storage_in_commodities[me, t] <= m.nominal_cap[me] / \
                           m.ratio_capacity_p[me]
            else:
                return m.mass_energy_storage_in_commodities[me, t] == 0

        model.storage_charge_upper_bound_con = Constraint(model.ME_STREAMS, model.TIME,
                                                          rule=storage_charge_upper_bound_rule)

        def storage_discharge_upper_bound_rule(m, me, t):
            if me in m.STORAGES:
                return m.mass_energy_storage_out_commodities[me, t] / m.discharging_efficiency[me] \
                           <= m.nominal_cap[me] / m.ratio_capacity_p[me]
            else:
                return m.mass_energy_storage_out_commodities[me, t] == 0

        model.storage_discharge_upper_bound_con = Constraint(model.ME_STREAMS, model.TIME,
                                                             rule=storage_discharge_upper_bound_rule)

        def storage_binary_sum_rule(m, s, t):
            return m.storage_charge_binary[s, t] + m.storage_discharge_binary[s, t] <= 1
        model.storage_binary_sum_con = Constraint(model.STORAGES, model.TIME, rule=storage_binary_sum_rule)

        def charge_binary_activation_rule(m, s, t):
            return m.mass_energy_storage_in_commodities[s, t] - m.storage_charge_binary[s, t] * 1000000 <= 0
        model.charge_binary_activation_con = Constraint(model.STORAGES, model.TIME, rule=charge_binary_activation_rule)

        def discharge_binary_activation_rule(m, s, t):
            return m.mass_energy_storage_out_commodities[s, t] - m.storage_discharge_binary[s, t] * 1000000 <= 0

        model.discharge_binary_activation_con = Constraint(model.STORAGES, model.TIME,
                                                           rule=discharge_binary_activation_rule)

        """ Financial constraints """
        def calculate_investment_scalable_components_rule(m, c):
            return m.investment[c] == sum(m.nominal_cap_pre[c, i] * m.capex_pre_var[c, i]
                                          + m.capex_pre_fix[c, i] * m.capacity_binary[c, i]
                                          for i in m.INTEGER_STEPS)
        model.calculate_investment_scalable_components_con = Constraint(model.SCALABLE_COMPONENTS,
                                                                        rule=calculate_investment_scalable_components_rule)

        def calculate_investment_not_scalable_components_rule(m, c):
            if c not in m.SCALABLE_COMPONENTS:
                return m.investment[c] == m.nominal_cap[c] * m.capex_var[c] + m.capex_fix[c]
        model.calculate_investment_not_scalable_components_con = Constraint(model.COMPONENTS,
                                                                            rule=calculate_investment_not_scalable_components_rule)

        def calculate_annuity_of_component_rule(m, c):
            return m.annuity[c] == m.investment[c] * m.ANF[c]
        model.calculate_annuity_of_component_con = Constraint(model.COMPONENTS, rule=calculate_annuity_of_component_rule)

        def calculate_total_annuity_rule(m):
            return m.total_annuity == sum(m.annuity[c] for c in m.COMPONENTS)
        model.calculate_total_annuity_con = Constraint(rule=calculate_total_annuity_rule)

        def calculate_maintenance_costs_of_component_rule(m, c):
            return m.maintenance_costs[c] == m.investment[c] * m.maintenance[c]
        model.calculate_maintenance_costs_of_component_con = Constraint(model.COMPONENTS,
                                                                        rule=calculate_maintenance_costs_of_component_rule)

        def calculate_total_maintenance_cost_rule(m):
            return m.total_maintenance_costs == sum(m.maintenance_costs[c] for c in m.COMPONENTS)
        model.calculate_total_maintenance_cost_con = Constraint(rule=calculate_total_maintenance_cost_rule)

        def calculate_taxes_and_insurance_costs_of_component_rule(m, c):
            if pm_object.get_applied_parameter_for_component('taxes_and_insurance', c):
                return m.taxes_and_insurance_costs[c] == m.investment[c] * m.taxes_and_insurance
            else:
                return m.taxes_and_insurance_costs[c] == 0
        model.calculate_taxes_and_insurance_costs_of_component_con = Constraint(model.COMPONENTS,
                                                                                rule=calculate_taxes_and_insurance_costs_of_component_rule)

        def calculate_total_taxes_and_insurance_cost_rule(m):
            return m.total_taxes_and_insurance_costs == sum(m.taxes_and_insurance_costs[c] for c in m.COMPONENTS)
        model.calculate_total_taxes_and_insurance_cost_con = Constraint(rule=calculate_total_taxes_and_insurance_cost_rule)

        def calculate_overhead_costs_of_component_rule(m, c):
            if pm_object.get_applied_parameter_for_component('overhead', c):
                return m.overhead_costs[c] == m.investment[c] * m.overhead
            else:
                return m.overhead_costs[c] == 0
        model.calculate_overhead_costs_of_component_con = Constraint(model.COMPONENTS,
                                                                     rule=calculate_overhead_costs_of_component_rule)

        def calculate_total_overhead_costs_rule(m):
            return m.total_overhead_costs == sum(m.overhead_costs[c] for c in m.COMPONENTS)
        model.calculate_total_overhead_costs_con = Constraint(rule=calculate_total_overhead_costs_rule)

        def calculate_personnel_costs_of_component_rule(m, c):
            if pm_object.get_applied_parameter_for_component('personnel_costs', c):
                return m.personnel_costs[c] == m.investment[c] * m.personnel_cost
            else:
                return m.personnel_costs[c] == 0
        model.calculate_personnel_costs_of_component_con = Constraint(model.COMPONENTS,
                                                                      rule=calculate_personnel_costs_of_component_rule)

        def calculate_total_personnel_costs_rule(m):
            return m.total_personnel_costs == sum(m.personnel_costs[c] for c in m.COMPONENTS)
        model.calculate_total_personnel_costs_con = Constraint(rule=calculate_total_personnel_costs_rule)

        def calculate_working_capital_of_component_rule(m, c):
            if pm_object.get_applied_parameter_for_component('working_capital', c):
                return m.working_capital_costs[c] == (m.investment[c] / (1 - m.working_capital)
                                                      * m.working_capital) * m.wacc
            else:
                return m.working_capital_costs[c] == 0
        model.calculate_working_capital_of_component_con = Constraint(model.COMPONENTS,
                                                                      rule=calculate_working_capital_of_component_rule)

        def calculate_total_working_capital_rule(m):
            return m.total_working_capital_costs == sum(m.working_capital_costs[c] for c in m.COMPONENTS)
        model.calculate_total_working_capital_con = Constraint(rule=calculate_total_working_capital_rule)

        def calculate_purchase_costs_of_commodity_rule(m, me):
            return m.purchase_costs[me] == sum(m.mass_energy_purchase_commodity[me, t] * m.weightings[t]
                                               * m.purchase_price[me, t] for t in m.TIME)
        model.calculate_purchase_costs_of_commodity_con = Constraint(model.PURCHASABLE_STREAMS,
                                                                  rule=calculate_purchase_costs_of_commodity_rule)

        def calculate_total_purchase_costs_rule(m):
            return m.total_purchase_costs == sum(m.purchase_costs[me] for me in m.PURCHASABLE_STREAMS)
        model.calculate_total_purchase_costs_con = Constraint(rule=calculate_total_purchase_costs_rule)

        def calculate_revenue_of_commodity_rule(m, me):
            return m.revenue[me] == sum(m.mass_energy_sell_commodity[me, t] * m.weightings[t]
                                        * m.selling_price[me, t] for t in m.TIME)
        model.calculate_revenue_of_commodity_con = Constraint(model.SALEABLE_STREAMS,
                                                           rule=calculate_revenue_of_commodity_rule)

        def calculate_total_revenue_rule(m):
            return m.total_revenue == sum(m.revenue[me] for me in m.SALEABLE_STREAMS)
        model.calculate_total_revenue_con = Constraint(rule=calculate_total_revenue_rule)

        if not self.pm_object.get_uses_representative_periods():

            def set_start_up_costs_component_rule(m, c, t):
                return m.start_up_costs_component[c, t] >= m.start_up_costs[c] * m.nominal_cap[c] \
                       + (m.status_off_switch_off[c, t] - 1) * 1000000
            model.set_start_up_costs_component_con = Constraint(model.SHUT_DOWN_COMPONENTS, model.TIME,
                                                                rule=set_start_up_costs_component_rule)

        else:
            def set_start_up_costs_component_using_representative_periods_rule(m, c, t):
                period_length = self.pm_object.get_representative_periods_length()
                if t % period_length != 0:
                    return m.start_up_costs_component[c, t] >= m.start_up_costs[c] * m.nominal_cap[c] \
                           + (m.status_off_switch_off[c, t] - 1) * 1000000
                else:
                    return Constraint.Skip
            model.set_start_up_costs_component_using_representative_periods_con = Constraint(model.SHUT_DOWN_COMPONENTS,
                                                                                             model.TIME,
                                                                                             rule=set_start_up_costs_component_using_representative_periods_rule)

        def calculate_total_start_up_costs_of_component_rule(m, c):
            return m.total_start_up_costs_component[c] == sum(m.start_up_costs_component[c, t] for t in m.TIME)
        model.calculate_total_start_up_costs_of_component_con = Constraint(model.SHUT_DOWN_COMPONENTS,
                                                                           rule=calculate_total_start_up_costs_of_component_rule)

        def calculate_total_start_up_costs_rule(m):
            return m.total_start_up_costs == sum(m.total_start_up_costs_component[c] for c in m.SHUT_DOWN_COMPONENTS)
        model.calculate_total_start_up_costs_con = Constraint(rule=calculate_total_start_up_costs_rule)

        def objective_function(m):
            return (m.total_annuity
                    + m.total_maintenance_costs
                    + m.total_taxes_and_insurance_costs
                    + m.total_overhead_costs
                    + m.total_personnel_costs
                    + m.total_working_capital_costs
                    + m.total_purchase_costs
                    - m.total_revenue
                    + m.total_start_up_costs)
        model.obj = Objective(rule=objective_function, sense=minimize)

        return model

    def optimize(self, instance=None):
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

    def __init__(self, pm_object, path_data, solver, path_to_generation_folder=None):

        self.lower_bound_dict = {}

        # ----------------------------------
        # Set up problem
        self.path_data = path_data
        self.path_to_generation_folder = path_to_generation_folder
        self.solver = solver
        self.instance = None
        self.pm_object = pm_object

        self.pm_object = self.clone_components_which_use_parallelization()

        self.annuity_factor_dict = self.pm_object.get_annuity_factor()

        self.lifetime_dict, self.maintenance_dict, self.capex_var_dict, self.capex_fix_dict, self.minimal_power_dict,\
            self.maximal_power_dict,  self.ramp_up_dict, self.ramp_down_dict, self.scaling_capex_var_dict, \
            self.scaling_capex_fix_dict, self.scaling_capex_upper_bound_dict, self.shut_down_down_time_dict,\
            self.shut_down_start_up_costs, self.standby_down_time_dict, self.charging_efficiency_dict,\
            self.discharging_efficiency_dict, self.minimal_soc_dict, self.maximal_soc_dict, \
            self.ratio_capacity_power_dict = self.pm_object.get_all_component_parameters()

        self.scalable_components, self.not_scalable_components, self.shut_down_components,\
            self.no_shut_down_components, self.standby_components,\
            self.no_standby_components = self.pm_object.get_conversion_component_sub_sets()

        self.final_commodities, self.available_commodities, self.emittable_commodities, self.purchasable_commodities,\
            self.saleable_commodities, self.demanded_commodities, self.total_demand_commodities, self.generated_commodities\
            = self.pm_object.get_commodity_sets()

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
        self.model.TIME = RangeSet(0, self.pm_object.get_time_steps() - 1)
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
        self.attach_general_parameters_to_optimization_problem()
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
