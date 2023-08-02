import itertools
from copy import deepcopy
import gurobipy as gp


class GurobiOptimizationProblem:

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

    def attach_constraints(self):
        """ Method attaches all constraints to optimization problem """

        pm_object = self.pm_object
        
        for combi in itertools.product(self.final_commodities, self.clusters, self.time):
            commodity_object = pm_object.get_commodity(combi[0])
            equation_lhs = []
            equation_rhs = []

            com = combi[0]
            cl = combi[1]
            t = combi[2]

            name_adding = com + '_' + str(cl) + '_' + str(t) + '_constraint'

            # mass energy balance constraint
            # Sets mass energy balance for all components
            # produced (out), generated, discharged, available and purchased commodities
            #   = emitted, sold, demanded, charged and used (in) commodities

            if commodity_object.is_available():
                equation_lhs.append(self.mass_energy_available[com, cl, t])
            if commodity_object.is_emittable():
                equation_lhs.append(-self.mass_energy_emitted[com, cl, t])
            if commodity_object.is_purchasable():
                equation_lhs.append(self.mass_energy_purchase_commodity[com, cl, t])
            if commodity_object.is_saleable():
                equation_lhs.append(-self.mass_energy_sell_commodity[com, cl, t])
            if commodity_object.is_demanded():
                equation_lhs.append(-self.mass_energy_demand[com, cl, t])
            if com in self.storage_components:
                equation_lhs.append(
                    self.mass_energy_storage_out_commodities[com, cl, t]
                    - self.mass_energy_storage_in_commodities[com, cl, t])
            if com in self.generated_commodities:
                equation_lhs.append(sum(self.mass_energy_generation[g, com, cl, t]
                                        for g in self.generator_components
                                        if pm_object.get_component(g).get_generated_commodity() == com))

            for c in self.conversion_components:
                if (c, com) in self.output_tuples:
                    equation_lhs.append(self.mass_energy_component_out_commodities[c, com, cl, t])

                if (c, com) in self.input_tuples:
                    equation_rhs.append(self.mass_energy_component_in_commodities[c, com, cl, t])

                # hot standby demand
                if c in self.standby_components:
                    hot_standby_commodity = [*pm_object.get_component(c).get_hot_standby_demand().keys()][0]
                    if com == hot_standby_commodity:
                        equation_rhs.append(self.mass_energy_hot_standby_demand[c, com, cl, t])

            self.model.addConstr(sum(equation_lhs) == sum(equation_rhs),
                                 name='balancing_' + name_adding)

            # Sets commodities, which are demanded
            if com in self.demanded_commodities:
                if com not in self.total_demand_commodities:  # Case where demand needs to be satisfied in every t
                    self.model.addConstr(self.mass_energy_demand[com, cl, t] >= self.hourly_demand_dict[com, cl, t],
                                         name='hourly_demand_satisfaction_' + name_adding)

        # commodities with total demand
        for com in self.demanded_commodities:
            if com in self.total_demand_commodities:
                self.model.addConstr(sum(self.mass_energy_demand[com, cl, t] * self.weightings_dict[cl]
                                         for cl in self.clusters
                                         for t in self.time)
                                     >= self.total_demand_dict[com],
                                     name='total_demand_satisfaction_' + com + '_constraint')

        # output commodities
        for combi in itertools.product(self.conversion_components, self.clusters, self.time):
            c = combi[0]
            cl = combi[1]
            t = combi[2]

            for oc in self.all_outputs:
                main_input = pm_object.get_component(c).get_main_input()
                outputs = self.pm_object.get_component(c).get_outputs()

                if oc in [*outputs.keys()]:
                    self.model.addConstr(self.mass_energy_component_out_commodities[c, oc, cl, t] ==
                                         self.mass_energy_component_in_commodities[c, main_input, cl, t]
                                         * self.output_conversion_tuples_dict[c, main_input, oc],
                                         name='commodity_conversion_output_' + str(cl) + '_' + str(t)
                                              + '_constraint')

            for ic in self.all_inputs:
                main_input = pm_object.get_component(c).get_main_input()
                inputs = pm_object.get_component(c).get_inputs()
                if ic in [*inputs.keys()]:
                    if ic != main_input:
                        self.model.addConstr(self.mass_energy_component_in_commodities[c, ic, cl, t] ==
                                             self.mass_energy_component_in_commodities[c, main_input, cl, t]
                                             * self.input_conversion_tuples_dict[c, main_input, ic],
                                             name='commodity_conversion_input_' + str(cl) + '_' + str(t)
                                                  + '_constraint')

        for sc in self.scalable_components:

            for i in self.integer_steps:

                self.model.addConstr(self.capacity_binary[sc, i] >= self.nominal_cap_pre[sc, i] / 1000000,
                                     name='binary_activation' + '_' + str(i) + '_constraint')

                self.model.addConstr(self.nominal_cap_pre[sc, i]
                                     >= self.scaling_capex_lower_bound_dict[sc, i] * self.capacity_binary[sc, i],
                                     name='capacity_lower_bound' + '_' + str(i) + '_constraint')

            self.model.addConstr(sum(self.capacity_binary[sc, i] for i in self.integer_steps) <= 1,
                                 name='capacity_binary_sum' + '_' + sc + '_constraint')

            self.model.addConstr(sum(self.nominal_cap_pre[sc, i] for i in self.integer_steps) == self.nominal_cap[sc],
                                 name='final_capacity' + '_' + sc + '_constraint')

        for combi in itertools.product(self.conversion_components, self.clusters, self.time):
            c = combi[0]
            cl = combi[1]
            t = combi[2]

            main_input = pm_object.get_component(c).get_main_input()

            name_adding = c + '_' + str(cl) + '_' + str(t) + '_constraint'

            self.model.addConstr(self.status_on[c, cl, t] + self.status_off[c, cl, t] + self.status_standby[c, cl, t] == 1,
                                 name='balance_component_status' + name_adding)

            # If component can not be shut off or put in hot standby, the status is always on
            if (c not in self.shut_down_components) & (c not in self.standby_components):
                self.model.addConstr(self.status_on[c, cl, t] == 1,
                                     name='no_shutdown_or_standby' + name_adding)
            elif c not in self.shut_down_components:
                self.model.addConstr(self.status_off[c, cl, t] == 0,
                                     name='no_shutdown' + name_adding)
            elif c not in self.standby_components:
                self.model.addConstr(self.status_standby[c, cl, t] == 0,
                                     name='no_standby' + name_adding)

            # Set binary to 1 if component is active
            self.model.addConstr(self.mass_energy_component_in_commodities[c, main_input, cl, t]
                                 - self.status_on[c, cl, t] * 1000000 <= 0,
                                 name='active_component' + name_adding)

            # Balance switch off
            self.model.addConstr(self.status_off_switch_on[c, cl, t]
                                 + self.status_off_switch_off[c, cl, t] <= 1,
                                 name='balance_status_off_switch' + name_adding)

            # Define switch on / off constraint
            if t > 0:
                self.model.addConstr(self.status_off[c, cl, t]
                                     == self.status_off[c, cl, t - 1]
                                     + self.status_off_switch_on[c, cl, t]
                                     - self.status_off_switch_off[c, cl, t],
                                     name='define_status_on_off_switch' + name_adding)

            # Balance switch standby
            self.model.addConstr(self.status_standby_switch_on[c, cl, t]
                                 + self.status_standby_switch_off[c, cl, t] <= 1,
                                 name='balance_status_standby_switch' + name_adding)

            # Define switch on / standby constraint
            if t > 0:
                self.model.addConstr(self.status_standby[c, cl, t]
                                     == self.status_standby[c, cl, t - 1]
                                     + self.status_standby_switch_on[c, cl, t]
                                     - self.status_standby_switch_off[c, cl, t],
                                     name='define_status_on_standby_switch' + name_adding)

            # Set upper bound conversion
            self.model.addConstr(self.mass_energy_component_in_commodities[c, main_input, cl, t]
                                 <= self.nominal_cap[c] * self.maximal_power_dict[c],
                                 name='set_upper_bound_conversion' + name_adding)

            # Set lower bound conversion
            self.model.addConstr(self.mass_energy_component_in_commodities[c, main_input, cl, t]
                                 >= self.nominal_cap[c] * self.minimal_power_dict[c]
                                 + (self.status_on[c, cl, t] - 1) * 1000000,
                                 name='set_lower_bound_conversion' + name_adding)

            if t > 0:
                # ramp up limitations
                self.model.addConstr(self.mass_energy_component_in_commodities[c, main_input, cl, t]
                                     - self.mass_energy_component_in_commodities[c, main_input, cl, t - 1]
                                     <= self.nominal_cap[c] * self.ramp_up_dict[c]
                                     + (self.status_off_switch_off[c, cl, t]
                                        + self.status_standby_switch_off[c, cl, t]) * 1000000,
                                     name='set_ramp_up_limitations' + name_adding)

                # ramp down limitations
                self.model.addConstr(self.mass_energy_component_in_commodities[c, main_input, cl, t]
                                     - self.mass_energy_component_in_commodities[c, main_input, cl, t - 1]
                                     >= - self.nominal_cap[c] * self.ramp_down_dict[c]
                                     + (self.status_off_switch_on[c, cl, t]
                                        + self.status_standby_switch_on[c, cl, t]) * 1000000,
                                     name='set_ramp_down_limitations' + name_adding)

            if c in self.shut_down_components:

                # set minimal down time after shut down
                if self.shut_down_down_time_dict[c] + t > max(self.time):
                    dt = max(self.time) - t + 1
                else:
                    dt = self.shut_down_down_time_dict[c]

                self.model.addConstr((self.status_off[c, cl, t] - self.status_off[c, cl, t - 1])
                                     - sum(self.status_off[c, cl, t + i]
                                           for i in range(dt)) / dt <= 0,
                                     name='set_down_time' + name_adding)

                # set minimal standby time after standby
                if self.standby_down_time_dict[c] + t > max(self.time):
                    st = max(self.time) - t + 1
                else:
                    st = self.standby_down_time_dict[c]

                self.model.addConstr((self.status_standby[c, cl, t] - self.status_standby[c, cl, t - 1])
                                     - sum(self.status_standby[c, cl, t + i]
                                           for i in range(st)) / st <= 0,
                                     name='set_standby_time' + name_adding)

            # lower limit hot standby (don't create energy / commodity
            if c in self.standby_components:

                hot_standby_commodity = [*pm_object.get_component(c).get_hot_standby_demand().keys()][0]
                hot_standby_demand = pm_object.get_component(c).get_hot_standby_demand()[hot_standby_commodity]

                for com in self.final_commodities:
                    if com == hot_standby_commodity:
                        self.model.addConstr(self.mass_energy_hot_standby_demand[c, hot_standby_commodity, cl, t]
                                             >= self.nominal_cap[c] * hot_standby_demand
                                             + (self.status_standby[c, t] - 1) * 1000000,
                                             name='define_lower_limit_hot_standby_demand' + name_adding)
                    else:
                        self.model.addConstr(self.mass_energy_hot_standby_demand[c, com, cl, t] == 0,
                                             name='define_lower_limit_hot_standby_demand' + name_adding)

                # upper limit got standby (don't destroy energy / commodity)
                self.model.addConstr(self.mass_energy_hot_standby_demand[c, hot_standby_commodity, cl, t]
                                     <= self.nominal_cap[c] * hot_standby_demand,
                                     name='define_upper_limit_hot_standby_demand' + name_adding)

                # activate if in hot standby
                self.model.addConstr(self.mass_energy_hot_standby_demand[c, hot_standby_commodity, cl, t]
                                     <= self.status_standby[c, cl, t] * 1000000,
                                     name='define_hot_standby_activation' + name_adding)

        for g in self.generator_components:

            for combi in itertools.product(self.generated_commodities, self.clusters, self.time):
                gc = combi[0]
                cl = combi[1]
                t = combi[2]

                name_adding = g + '_' + str(cl) + '_' + str(t) + '_constraint'

                generated_commodity = pm_object.get_component(g).get_generated_commodity()

                if gc == generated_commodity:
                    if pm_object.get_component(g).get_curtailment_possible():
                        # with curtailment
                        self.model.addConstr(self.mass_energy_generation[g, generated_commodity, cl, t]
                                             <= self.generation_profiles_dict[g, cl, t] * self.nominal_cap[g],
                                             name='define_generation' + name_adding)
                    else:
                        # without curtailment
                        self.model.addConstr(self.mass_energy_generation[g, generated_commodity, cl, t]
                                             == self.generation_profiles_dict[g, cl, t] * self.nominal_cap[g],
                                             name='define_generation' + name_adding)
                else:
                    # no generation
                    self.model.addConstr(self.mass_energy_generation[g, generated_commodity, cl, t] == 0,
                                         name='define_generation' + name_adding)

            name_adding = g + '_constraint'

            # Applied if generator capacity is fixed
            if pm_object.get_component(g).get_has_fixed_capacity():
                self.model.addConstr(self.nominal_cap[g] == self.fixed_capacity_dict[g],
                                     name='fixed_capacity_of_generation' + name_adding)

        for combi in itertools.product(self.storage_components, self.clusters, self.time):
            s = combi[0]
            cl = combi[1]
            t = combi[2]

            name_adding = s + '_' + str(cl) + '_' + str(t) + '_constraint'

            # storage balance
            if t != 0:
                self.model.addConstr(self.soc[s, cl, t] == self.soc[s, cl, t - 1]
                                     + self.mass_energy_storage_in_commodities[s, cl, t - 1]
                                     * self.charging_efficiency_dict[s]
                                     - self.mass_energy_storage_out_commodities[s, cl, t - 1]
                                     / self.discharging_efficiency_dict[s],
                                     name='storage_balance' + name_adding)

            if t == max(self.time):
                self.model.addConstr(self.soc[s, cl, 0] == self.soc[s, cl, t]
                                     + self.mass_energy_storage_in_commodities[s, cl, t]
                                     * self.charging_efficiency_dict[s]
                                     - self.mass_energy_storage_out_commodities[s, cl, t]
                                     / self.discharging_efficiency_dict[s],
                                     name='last_soc_equals_first_soc' + name_adding)

            # min max soc
            self.model.addConstr(self.soc[s, cl, t] <= self.maximal_soc_dict[s] * self.nominal_cap[s],
                                 name='max_soc' + name_adding)

            self.model.addConstr(self.soc[s, cl, t] >= self.minimal_soc_dict[s] * self.nominal_cap[s],
                                 name='min_soc' + name_adding)

            # upper and lower bounds charging
            self.model.addConstr(self.mass_energy_storage_in_commodities[s, cl, t]
                                 <= self.nominal_cap[s] / self.ratio_capacity_power_dict[s],
                                 name='max_soc' + name_adding)

            self.model.addConstr(self.mass_energy_storage_out_commodities[s, cl, t]
                                 / self.discharging_efficiency_dict[s]
                                 <= self.nominal_cap[s]
                                 / self.ratio_capacity_power_dict[s],
                                 name='min_soc' + name_adding)

            # storage binary --> don't allow charge and discharge at same time
            self.model.addConstr(self.storage_charge_binary[s, cl, t] + self.storage_discharge_binary[s, cl, t] <= 1,
                                 name='balance_storage_binaries' + name_adding)

            self.model.addConstr(self.mass_energy_storage_in_commodities[s, cl, t]
                                 - self.storage_charge_binary[s, cl, t] * 1000000 <= 0,
                                 name='activate_charging_binary' + name_adding)

            self.model.addConstr(self.mass_energy_storage_out_commodities[s, cl, t]
                                 - self.storage_discharge_binary[s, cl, t] * 1000000 <= 0,
                                 name='deactivate_charging_binary' + name_adding)

        # calculate investment (used to simplify constraint)
        for c in self.all_components:
            if c not in self.scalable_components:
                self.model.addConstr(self.investment[c]
                                     == self.nominal_cap[c] * self.capex_var_dict[c]
                                     + self.capex_fix_dict[c],
                                     name='calculate_investment' + c + '_constraint')
            else:
                self.model.addConstr(self.investment[c]
                                     == sum(self.nominal_cap_pre[c, i] * self.scaling_capex_var_dict[c, i]
                                            + self.scaling_capex_fix_dict[c, i] * self.capacity_binary[c, i]
                                            for i in self.integer_steps),
                                     name='calculate_investment' + c + '_constraint')

        # minimize total costs
        self.model.setObjective(sum(self.investment[c] * self.annuity_factor_dict[c] for c in self.all_components)
                                + sum(self.investment[c] * self.fixed_om_dict[c] for c in self.all_components)
                                + sum(self.mass_energy_storage_in_commodities[s, cl, t] * self.variable_om_dict[s] * self.weightings_dict[cl]
                                      for t in self.time for cl in self.clusters
                                      for s in self.storage_components)
                                + sum(self.mass_energy_component_out_commodities[c, pm_object.get_component(c).get_main_output(), cl, t]
                                      * self.variable_om_dict[c] * self.weightings_dict[cl]
                                      for t in self.time for cl in self.clusters
                                      for c in self.conversion_components)
                                + sum(self.mass_energy_generation[g, pm_object.get_component(g).get_generated_commodity(), cl, t]
                                      * self.variable_om_dict[g] * self.weightings_dict[cl]
                                      for t in self.time for cl in self.clusters for g in self.generator_components)
                                + sum(self.mass_energy_purchase_commodity[me, cl, t]
                                      * self.purchase_price_dict[me, cl, t] * self.weightings_dict[cl]
                                      for t in self.time for cl in self.clusters
                                      for me in self.purchasable_commodities if me in self.purchasable_commodities)
                                - sum(self.mass_energy_sell_commodity[me, cl, t] * self.sell_price_dict[me, cl, t]
                                      * self.weightings_dict[cl]
                                      for t in self.time for cl in self.clusters for me in self.saleable_commodities
                                      if me in self.saleable_commodities)
                                + sum(self.status_off_switch_off[c, cl, t] * self.weightings_dict[cl]
                                      * self.shut_down_start_up_costs[c]
                                      for t in self.time for cl in self.clusters for c in self.shut_down_components),
                                gp.GRB.MINIMIZE)

    def optimize(self):

        self.model.optimize()

        print(f"Optimal objective value: {self.model.objVal}")

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
        self.hourly_demand_dict, self.total_demand_dict = self.pm_object.get_demand_time_series()
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
        self.model = gp.Model()
        self.time = range(0, self.pm_object.get_covered_period())  # no -1 because of for
        self.clusters = range(0, self.pm_object.get_number_clusters())  # no -1 because of for
        self.integer_steps = range(0, self.pm_object.integer_steps)
        self.weightings_dict = self.pm_object.get_weightings_time_series()

        # self.model.pwconst = Piecewise(indexes, yvar, xvar, **Keywords) # todo: Implement with big m
        # https://pyomo.readthedocs.io/en/stable/pyomo_self.modeling_components/Expressions.html
        self.M = 1000000000

        # Attach Variables

        import itertools

        # Component variables
        self.nominal_cap = self.model.addVars(self.all_components, lb=0)

        self.status_on = self.model.addVars(list(itertools.product(self.conversion_components,
                                                                   self.clusters,
                                                                   self.time)),
                                            vtype='B')
        self.status_off = self.model.addVars(list(itertools.product(self.conversion_components,
                                                                    self.clusters,
                                                                    self.time)),
                                             vtype='B')
        self.status_off_switch_on = self.model.addVars(list(itertools.product(self.conversion_components,
                                                                              self.clusters,
                                                                              self.time)),
                                                       vtype='B')
        self.status_off_switch_off = self.model.addVars(list(itertools.product(self.conversion_components,
                                                                               self.clusters,
                                                                               self.time)),
                                                        vtype='B')
        self.status_standby_switch_on = self.model.addVars(list(itertools.product(self.conversion_components,
                                                                                  self.clusters,
                                                                                  self.time)),
                                                           vtype='B')
        self.status_standby_switch_off = self.model.addVars(list(itertools.product(self.conversion_components,
                                                                                   self.clusters,
                                                                                   self.time)),
                                                            vtype='B')
        self.status_standby = self.model.addVars(list(itertools.product(self.conversion_components,
                                                                        self.clusters,
                                                                        self.time)),
                                                 vtype='B')

        # STORAGE binaries (charging and discharging)
        self.storage_charge_binary = self.model.addVars(list(itertools.product(self.storage_components,
                                                                               self.clusters,
                                                                               self.time)),
                                                        vtype='B')
        self.storage_discharge_binary = self.model.addVars(list(itertools.product(self.storage_components,
                                                                                  self.clusters,
                                                                                  self.time)),
                                                           vtype='B')

        self.investment = self.model.addVars(self.all_components, lb=0)

        self.nominal_cap_pre = self.model.addVars(list(itertools.product(self.scalable_components,
                                                                         self.integer_steps)),
                                                  lb=0,
                                                  ub=[self.scaling_capex_upper_bound_dict[(s, i)]
                                                      for s in self.scalable_components
                                                      for i in self.integer_steps])
        self.capacity_binary = self.model.addVars(list(itertools.product(self.scalable_components,
                                                                         self.integer_steps)),
                                                  vtype='B')
        # -------------------------------------
        # Commodity variables
        # Input and output commodity of component

        self.mass_energy_component_in_commodities = self.model.addVars(list(itertools.product(self.conversion_components,
                                                                             self.all_inputs,
                                                                             self.clusters,
                                                                             self.time)),
                                                                       lb=0)
        self.mass_energy_component_out_commodities\
            = self.model.addVars(list(itertools.product(self.conversion_components, self.all_outputs, self.clusters,
                                                        self.time)),
                                 lb=0)

        # Freely available commodities
        self.mass_energy_available = self.model.addVars(list(itertools.product(self.available_commodities,
                                                                               self.clusters,
                                                                               self.time)),
                                                        lb=0)
        self.mass_energy_emitted = self.model.addVars(list(itertools.product(self.emittable_commodities,
                                                                             self.clusters,
                                                                             self.time)),
                                                      lb=0)

        # Charged and discharged commodities
        self.mass_energy_storage_in_commodities = self.model.addVars(list(itertools.product(self.storage_components,
                                                                                            self.clusters,
                                                                                            self.time)),
                                                                     lb=0)
        self.mass_energy_storage_out_commodities = self.model.addVars(list(itertools.product(self.storage_components,
                                                                                             self.clusters,
                                                                                             self.time)),
                                                                      lb=0)
        self.soc = self.model.addVars(list(itertools.product(self.storage_components,
                                                             self.clusters,
                                                             self.time)),
                                      lb=0)

        # sold and purchased commodities
        self.mass_energy_sell_commodity = self.model.addVars(list(itertools.product(self.saleable_commodities,
                                                                                    self.clusters,
                                                                                    self.time)),
                                                             lb=0)
        self.mass_energy_purchase_commodity = self.model.addVars(list(itertools.product(self.purchasable_commodities,
                                                                                        self.clusters,
                                                                                        self.time)), lb=0)

        # generated commodities
        self.mass_energy_generation = self.model.addVars(list(itertools.product(self.generator_components,
                                                                                self.generated_commodities,
                                                                                self.clusters,
                                                                                self.time)),
                                                         lb=0)

        # Demanded commodities
        self.mass_energy_demand = self.model.addVars(list(itertools.product(self.demanded_commodities,
                                                                            self.clusters,
                                                                            self.time)),
                                                     lb=0)

        # Hot standby demand
        self.mass_energy_hot_standby_demand = self.model.addVars(list(itertools.product(self.standby_components,
                                                                                        self.final_commodities,
                                                                                        self.clusters,
                                                                                        self.time)),
                                                                 lb=0)

        self.attach_constraints()

        self.optimize()

        # print(self.instance.pprint())
