import pyomo.environ as pyo
from pyomo.core import *
import pandas as pd
from pyomo.core import Binary
from copy import deepcopy

from _helper_optimization import calculate_economies_of_scale_steps


class OptimizationProblem:

    def pre_adjustments(self, pm_object):

        """ Copies components in the case that multiple parallel components exist """

        # Create deepcopy so that the original pm_object is not influenced by copying single components
        # Otherwise, GUI would add the copied components
        pm_object_copy = deepcopy(pm_object)

        # Copy components if number of components in system is higher than 1
        for component_object in pm_object_copy.get_specific_components('final', 'conversion'):
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
                    for p in pm_object.get_general_parameters():
                        if p in exclude:
                            continue
                        pm_object_copy.set_applied_parameter_for_component(p,
                                                                           parallel_unit_component_name,
                                                                           pm_object.get_applied_parameter_for_component(p, component_name))

        return pm_object_copy

    def initialize_problem(self):

        """ Add variables, parameters etc. to the optimization problem """

        # -------------------------------------
        # General Parameters
        general_parameters = self.pm_object.get_general_parameter_value_dictionary()

        self.model.wacc = Param(initialize=general_parameters['wacc'])
        self.model.taxes_and_insurance = Param(initialize=general_parameters['taxes_and_insurance'])
        self.model.overhead = Param(initialize=general_parameters['overhead'])
        self.model.working_capital = Param(initialize=general_parameters['working_capital'])
        self.model.personnel_cost = Param(initialize=general_parameters['personnel_costs'])

        # Time range
        self.model.TIME = RangeSet(0, general_parameters['covered_period'] - 1)

        # -------------------------------------
        # Components
        all_components = []
        conversion_components = []
        storage_components = []
        generator_components = []

        for component_object in self.pm_object.get_specific_components('final'):
            all_components.append(component_object.get_name())
            if component_object.get_component_type() == 'conversion':
                conversion_components.append(component_object.get_name())
            elif component_object.get_component_type() == 'generator':
                generator_components.append(component_object.get_name())
            elif component_object.get_component_type() == 'storage':
                storage_components.append(component_object.get_name())

        self.model.CONVERSION_COMPONENTS = Set(initialize=conversion_components)
        self.model.STORAGES = Set(initialize=storage_components)
        self.model.GENERATORS = Set(initialize=generator_components)
        self.model.COMPONENTS = Set(initialize=all_components)

        # -------------------------------------
        # Streams (Mass & Energy)

        # Initialization
        final_streams = []
        available_streams = []
        emittable_streams = []
        purchasable_streams = []
        saleable_streams = []
        demanded_streams = []
        total_demand_streams = []

        # Add characteristics to streams if set
        for stream in self.pm_object.get_specific_streams('final'):

            stream_name = stream.get_name()

            final_streams.append(stream_name)

            if stream.is_available():
                available_streams.append(stream_name)
            if stream.is_emittable():
                emittable_streams.append(stream_name)
            if stream.is_purchasable():
                purchasable_streams.append(stream_name)
            if stream.is_saleable():
                saleable_streams.append(stream_name)
            if stream.is_demanded():
                demanded_streams.append(stream_name)
            if stream.is_total_demand():
                total_demand_streams.append(stream_name)

        self.model.ME_STREAMS = Set(initialize=final_streams)
        self.model.AVAILABLE_STREAMS = Set(initialize=available_streams)
        self.model.EMITTED_STREAMS = Set(initialize=emittable_streams)
        self.model.PURCHASABLE_STREAMS = Set(initialize=purchasable_streams)
        self.model.SALEABLE_STREAMS = Set(initialize=saleable_streams)
        self.model.DEMANDED_STREAMS = Set(initialize=demanded_streams)
        self.model.TOTAL_DEMANDED_STREAMS = Set(initialize=total_demand_streams)

        generated_streams = []
        for generator in self.pm_object.get_specific_components('final', 'generator'):
            generated_streams.append(generator.get_generated_stream())
        self.model.GENERATED_STREAMS = Set(initialize=generated_streams)

        # ------------------------------------
        """ Attach component parameters"""
        # Iterate through components and collect parameters
        lifetime_dict = {}
        maintenance_dict = {}

        charging_efficiency_dict = {}
        discharging_efficiency_dict = {}
        min_soc_dict = {}
        max_soc_dict = {}
        initial_soc_dict = {}
        ratio_capacity_p_dict = {}
        storage_limiting_component_dict = {}
        storage_limiting_component_ratio_dict = {}

        capex_var_dict = {}
        capex_fix_dict = {}
        capex_var_pre_dict = {}
        capex_fix_pre_dict = {}
        self.lower_bound_dict = {}
        upper_bound_dict = {}
        min_p_dict = {}
        max_p_dict = {}
        ramp_up_dict = {}
        ramp_down_dict = {}
        shut_down_time_dict = {}
        start_up_time_dict = {}

        scalable_components = []
        not_scalable_components = []
        limited_storages = []

        shut_down_components = []
        no_shut_down_components = []

        for component_object in self.pm_object.get_specific_components('final'):
            component_name = component_object.get_name()

            lifetime_dict[component_name] = component_object.get_lifetime()
            maintenance_dict[component_name] = component_object.get_maintenance()
            capex_var_dict[component_name] = component_object.get_capex()
            capex_fix_dict[component_name] = 0

            if component_object.get_component_type() == 'conversion':
                min_p_dict[component_name] = component_object.get_min_p()
                max_p_dict[component_name] = component_object.get_max_p()
                ramp_up_dict[component_name] = component_object.get_ramp_up()
                ramp_down_dict[component_name] = component_object.get_ramp_down()

                if not component_object.is_scalable():
                    not_scalable_components.append(component_name)

                else:
                    scalable_components.append(component_name)

                    lower_bound, upper_bound, coefficient, intercept = calculate_economies_of_scale_steps(
                        component_object, self.pm_object)
                    for key in [*lower_bound.keys()]:
                        self.lower_bound_dict[key] = lower_bound[key]

                    for key in [*upper_bound.keys()]:
                        upper_bound_dict[key] = upper_bound[key]

                    for key in [*intercept.keys()]:
                        capex_fix_pre_dict[key] = intercept[key]
                        if type(key) == tuple:
                            capex_fix_dict[key[0]] = 0

                    for key in [*coefficient.keys()]:
                        capex_var_pre_dict[key] = coefficient[key]
                        if type(key) == tuple:
                            capex_var_dict[key[0]] = 0

                if component_object.get_shut_down_ability():
                    shut_down_components.append(component_name)
                    shut_down_time_dict[component_name] = component_object.get_shut_down_time()
                    start_up_time_dict[component_name] = component_object.get_start_up_time()
                else:
                    no_shut_down_components.append(component_name)

            elif component_object.get_component_type() == 'storage':
                not_scalable_components.append(component_name)

                charging_efficiency_dict[component_name] = component_object.get_charging_efficiency()
                discharging_efficiency_dict[component_name] = component_object.get_discharging_efficiency()
                min_soc_dict[component_name] = component_object.get_min_soc()
                max_soc_dict[component_name] = component_object.get_max_soc()
                initial_soc_dict[component_name] = component_object.get_initial_soc()
                ratio_capacity_p_dict[component_name] = component_object.get_ratio_capacity_p()

                if component_object.is_limited():
                    limited_storages.append(component_name)
                    storage_limiting_component_dict[component_name] = component_object.get_storage_limiting_component()
                    storage_limiting_component_ratio_dict[
                        component_name] = component_object.get_storage_limiting_component_ratio()

            elif component_object.get_component_type() == 'generator':
                not_scalable_components.append(component_name)

        # Attach parameters to optimization problem

        self.model.SCALABLE_COMPONENTS = Set(initialize=scalable_components)
        self.model.SHUT_DOWN_COMPONENTS = Set(initialize=shut_down_components)
        self.model.LIMITED_STORAGES = Set(initialize=limited_storages)

        # Parameters of components
        self.model.lifetime = Param(self.model.COMPONENTS,
                                    initialize=lifetime_dict,
                                    mutable=True)
        self.model.maintenance = Param(self.model.COMPONENTS,
                                       initialize=maintenance_dict,
                                       mutable=True)

        # Financial parameters
        self.model.capex_var = Param(self.model.COMPONENTS,
                                     initialize=capex_var_dict,
                                     mutable=True)

        self.model.capex_fix = Param(self.model.COMPONENTS,
                                     initialize=capex_fix_dict,
                                     mutable=True)

        # Technical Parameters
        self.model.min_p = Param(self.model.CONVERSION_COMPONENTS, initialize=min_p_dict)

        self.model.max_p = Param(self.model.CONVERSION_COMPONENTS, initialize=max_p_dict)

        self.model.ramp_up = Param(self.model.CONVERSION_COMPONENTS, initialize=ramp_up_dict)

        self.model.ramp_down = Param(self.model.CONVERSION_COMPONENTS, initialize=ramp_down_dict)

        self.model.charging_efficiency = Param(self.model.STORAGES,
                                               initialize=charging_efficiency_dict)

        self.model.discharging_efficiency = Param(self.model.STORAGES,
                                                  initialize=discharging_efficiency_dict)

        self.model.minimal_soc = Param(self.model.STORAGES,
                                       initialize=min_soc_dict)

        self.model.maximal_soc = Param(self.model.STORAGES,
                                       initialize=max_soc_dict)

        self.model.initial_soc = Param(self.model.STORAGES,
                                       initialize=initial_soc_dict)

        self.model.ratio_capacity_p = Param(self.model.STORAGES,
                                            initialize=ratio_capacity_p_dict)

        self.model.storage_limiting_component = Param(self.model.LIMITED_STORAGES,
                                                      initialize=storage_limiting_component_dict)
        self.model.storage_limiting_component_ratio = Param(self.model.LIMITED_STORAGES,
                                                            initialize=storage_limiting_component_ratio_dict)

        # Component variables
        self.model.nominal_cap = Var(self.model.COMPONENTS, bounds=(0, None))
        self.model.soc = Var(self.model.ME_STREAMS, self.model.TIME, bounds=(0, None))

        """ Integer variables and parameters """
        self.model.INTEGER_STEPS = RangeSet(0, self.pm_object.integer_steps)
        # self.model.pwconst = Piecewise(indexes, yvar, xvar, **Keywords) # todo: Implement with big m
        # https://pyomo.readthedocs.io/en/stable/pyomo_modeling_components/Expressions.html
        self.model.M = Param(initialize=1000000000)

        # SCALABLE COMPONENTS
        # Set bounds
        def _bounds_rule(self, s, i):
            return 0, upper_bound_dict[(s, i)]

        # ... for scalable components
        # Parameters and variables for scalable components

        # Capacities per integer steps
        self.model.nominal_cap_pre = Var(self.model.SCALABLE_COMPONENTS, self.model.INTEGER_STEPS, bounds=_bounds_rule)

        # Investment linearized: Investment = capex var * capacity + capex fix
        # Variable part of investment -> capex var * capacity
        self.model.capex_pre_var = Param(self.model.SCALABLE_COMPONENTS, self.model.INTEGER_STEPS,
                                         initialize=capex_var_pre_dict)
        # fix part of investment
        self.model.capex_pre_fix = Param(self.model.SCALABLE_COMPONENTS, self.model.INTEGER_STEPS,
                                         initialize=capex_fix_pre_dict)

        # Defines which integer step sets capacity
        self.model.capacity_binary = Var(self.model.SCALABLE_COMPONENTS, self.model.INTEGER_STEPS,
                                         within=Binary)
        # Penalty if capacity lower than its lower bounds
        self.model.penalty_binary_lower_bound = Var(self.model.SCALABLE_COMPONENTS, self.model.INTEGER_STEPS,
                                                    within=Binary)

        # Shutdown parameters and variables
        self.model.shut_down_time = Param(self.model.SHUT_DOWN_COMPONENTS, initialize=shut_down_time_dict)
        self.model.start_up_time = Param(self.model.SHUT_DOWN_COMPONENTS, initialize=start_up_time_dict)

        self.model.component_correct_p = Var(self.model.SHUT_DOWN_COMPONENTS, self.model.TIME, within=Binary)
        self.model.component_status = Var(self.model.SHUT_DOWN_COMPONENTS, self.model.TIME, within=Binary)
        self.model.component_status_1 = Var(self.model.SHUT_DOWN_COMPONENTS, self.model.TIME, within=Binary)  # todo: delete
        self.model.component_status_2 = Var(self.model.SHUT_DOWN_COMPONENTS, self.model.TIME, within=Binary)  # todo: delete
        self.model.status_switch_on = Var(self.model.SHUT_DOWN_COMPONENTS, self.model.TIME, within=Binary)
        self.model.status_switch_off = Var(self.model.SHUT_DOWN_COMPONENTS, self.model.TIME, within=Binary)
        self.model.test = Var(self.model.SHUT_DOWN_COMPONENTS, self.model.TIME)
        self.model.test_2 = Var(self.model.SCALABLE_COMPONENTS, self.model.INTEGER_STEPS)
        self.model.test_3 = Var()
        self.model.test_b = Var(within=Binary)

        # STORAGE binaries (charging and discharging)
        self.model.storage_charge_binary = Var(self.model.STORAGES, self.model.TIME, within=Binary)
        self.model.storage_discharge_binary = Var(self.model.STORAGES, self.model.TIME, within=Binary)

        # -------------------------------------
        # Stream variables
        # Input and output stream
        self.model.mass_energy_component_in_streams = Var(self.model.COMPONENTS, self.model.ME_STREAMS,
                                                          self.model.TIME, bounds=(0, None))
        self.model.mass_energy_component_out_streams = Var(self.model.COMPONENTS, self.model.ME_STREAMS,
                                                           self.model.TIME, bounds=(0, None))

        # Freely available streams
        self.model.mass_energy_available = Var(self.model.ME_STREAMS, self.model.TIME, bounds=(0, None))
        self.model.mass_energy_emitted = Var(self.model.ME_STREAMS, self.model.TIME, bounds=(0, None))

        # Charged and discharged streams
        self.model.mass_energy_storage_in_streams = Var(self.model.ME_STREAMS, self.model.TIME, bounds=(0, None))
        self.model.mass_energy_storage_out_streams = Var(self.model.ME_STREAMS, self.model.TIME, bounds=(0, None))

        # sold and purchased streams
        self.model.mass_energy_sell_stream = Var(self.model.ME_STREAMS, self.model.TIME, bounds=(0, None))
        self.model.mass_energy_purchase_stream = Var(self.model.ME_STREAMS, self.model.TIME, bounds=(0, None))

        # generated streams
        self.model.mass_energy_generation = Var(self.model.GENERATORS, self.model.ME_STREAMS, self.model.TIME,
                                                bounds=(0, None))
        self.model.mass_energy_total_generation = Var(self.model.ME_STREAMS, self.model.TIME, bounds=(0, None))

        # Demanded streams
        self.model.mass_energy_demand = Var(self.model.ME_STREAMS, self.model.TIME, bounds=(0, None))

        # ----------------------------------
        # Financial variables
        self.model.investment = Var(self.model.COMPONENTS, bounds=(0, None))  # calculates investment
        self.model.annuity = Var(self.model.COMPONENTS, bounds=(0, None))  # calculates annuity
        self.model.total_annuity = Var(bounds=(0, None))  # sums annuity
        self.model.maintenance_costs = Var(self.model.COMPONENTS, bounds=(0, None))  # calculates maintenance
        self.model.total_maintenance_costs = Var(bounds=(0, None))  # sums maintenance
        self.model.taxes_and_insurance_costs = Var(self.model.COMPONENTS, bounds=(0, None))  # calculates taxes and insurance
        self.model.total_taxes_and_insurance_costs = Var(bounds=(0, None))  # calculates taxes and insurance
        self.model.overhead_costs = Var(self.model.COMPONENTS, bounds=(0, None))  # calculates total overhead costs
        self.model.total_overhead_costs = Var(bounds=(0, None))  # calculates total overhead costs
        self.model.personnel_costs = Var(self.model.COMPONENTS, bounds=(0, None))  # calculates total personal costs
        self.model.total_personnel_costs = Var(bounds=(0, None))  # calculates total personal costs
        self.model.working_capital_costs = Var(self.model.COMPONENTS, bounds=(0, None))  # calculates total personal costs
        self.model.total_working_capital_costs = Var(bounds=(0, None))  # calculates total personal costs
        self.model.purchase_costs = Var(self.model.PURCHASABLE_STREAMS, bounds=(0, None))  # calculates purchase costs of each stream
        self.model.total_purchase_costs = Var(bounds=(0, None))  # sum purchase costs
        self.model.revenue = Var(self.model.SALEABLE_STREAMS, bounds=(None, None))  # calculates revenue of each stream
        self.model.total_revenue = Var(bounds=(None, None))  # sums revenues
        self.model.capacity_penalty = Var(initialize=0, bounds=(0, None))  # calculates penalty if capacity is not in right range
        self.model.power_penalty = Var(initialize=0, bounds=(0, None))  # calculates penalty if power is not in right range

    def post_adjustments(self):
        """ Any necessary precalculations are conducted here"""

        # Calculate annuity factor of each component
        anf_dict = {}
        for c in self.model.COMPONENTS:
            anf_component = (1 + self.model.wacc) ** self.model.lifetime[c] * self.model.wacc \
                            / ((1 + self.model.wacc) ** self.model.lifetime[c] - 1)
            anf_dict.update({c: anf_component})
        self.model.ANF = Param(self.model.COMPONENTS, initialize=anf_dict)

        # Define conversion tuples which will be used to set main conversion and side conversion
        # All other conversions will be set to 0 if not in conversion tuples
        main_conversions = self.pm_object.get_all_main_conversion()
        for i in main_conversions.index:
            conversion_component = main_conversions.loc[i, 'component']
            input_stream = main_conversions.loc[i, 'input_me']
            output_stream = main_conversions.loc[i, 'output_me']
            coefficient = float(main_conversions.loc[i, 'coefficient'])

            if conversion_component in self.model.CONVERSION_COMPONENTS:
                self.conversion_tuples.append((conversion_component, input_stream, output_stream))
                self.conversion_tuples_dict.update({(conversion_component, input_stream, output_stream): coefficient})

                self.main_tuples.append((conversion_component, input_stream))
                self.main_out_streams.append(output_stream)
                self.input_tuples.append((conversion_component, input_stream))
                self.output_tuples.append((conversion_component, output_stream))

        side_conversions = self.pm_object.get_all_side_conversions()
        if not side_conversions.empty:
            for i in side_conversions.index:
                conversion_component = side_conversions.loc[i, 'component']
                input_stream = side_conversions.loc[i, 'input_me']
                output_stream = side_conversions.loc[i, 'output_me']
                coefficient = float(side_conversions.loc[i, 'coefficient'])

                if conversion_component in self.model.CONVERSION_COMPONENTS:
                    self.conversion_tuples.append((conversion_component, input_stream, output_stream))
                    self.conversion_tuples_dict.update(
                        {(conversion_component, input_stream, output_stream): coefficient})

                    self.side_tuples.append((conversion_component, input_stream))

                    self.input_tuples.append((conversion_component, input_stream))
                    self.output_tuples.append((conversion_component, output_stream))

        self.model.CONVERSION_FACTOR = Param(self.model.COMPONENTS, self.model.ME_STREAMS,
                                             self.model.ME_STREAMS, initialize=self.conversion_tuples_dict)

        # Attach data to vector parameters, e.g., purchase price
        purchase_price_dict = {}
        sell_price_dict = {}
        demand_dict = {}
        generation_profiles_dict = {}

        for stream in self.pm_object.get_specific_streams('final'):
            stream_name = stream.get_name()

            # Purchase price
            if stream.is_purchasable():
                if stream.get_purchase_price_type() == 'fixed':
                    for t in self.model.TIME:
                        purchase_price_dict.update({(stream_name, t): float(stream.get_purchase_price())})

                else:
                    purchase_price_curve = pd.read_excel(self.path_data + stream.get_purchase_price(), index_col=0)
                    for t in self.model.TIME:
                        purchase_price_dict.update({(stream_name, t): float(purchase_price_curve.loc[t, 'value'])})

            # Selling price
            if stream.is_saleable():
                if stream.get_sale_price_type() == 'fixed':
                    for t in self.model.TIME:
                        sell_price_dict.update({(stream_name, t): float(stream.get_sale_price())})
                else:
                    sale_price_curve = pd.read_excel(self.path_data + stream.get_sale_price(), index_col=0)
                    for t in self.model.TIME:
                        sell_price_dict.update({(stream_name, t): float(sale_price_curve.loc[t, 'value'])})

            # Demand
            if stream.is_demanded():
                for t in self.model.TIME:
                    demand_dict.update({(stream_name, t): float(stream.get_demand())})

        self.model.purchase_price = Param(self.model.PURCHASABLE_STREAMS, self.model.TIME,
                                          initialize=purchase_price_dict)
        self.model.selling_price = Param(self.model.SALEABLE_STREAMS, self.model.TIME,
                                         initialize=sell_price_dict)
        self.model.stream_demand = Param(self.model.DEMANDED_STREAMS, self.model.TIME,
                                         initialize=demand_dict)

        # Set normalized generation profiles
        for generator in self.pm_object.get_specific_components('final', 'generator'):
            generator_name = generator.get_name()
            generation_profile = pd.read_excel(self.path_data + generator.get_generation_data(), index_col=0)
            for t in self.model.TIME:
                generation_profiles_dict.update({(generator_name, t): float(generation_profile.loc[t, 'value'])})

        self.model.generation_profiles = Param(self.model.GENERATORS, self.model.TIME,
                                               initialize=generation_profiles_dict)

    def attach_constraints(self):
        """ Method attaches all constraints to optimization problem """

        def _set_available_streams_rule(model, me, t):
            # Sets streams, which are available without limit and price
            if me in model.AVAILABLE_STREAMS:
                return model.mass_energy_available[me, t] >= 0
            else:
                return model.mass_energy_available[me, t] == 0

        self.model.set_available_streams_con = Constraint(self.model.ME_STREAMS, self.model.TIME,
                                                          rule=_set_available_streams_rule)

        def _set_emitted_streams_rule(model, me, t):
            # Sets streams, which are emitted without limit and price
            if me in model.EMITTED_STREAMS:
                return model.mass_energy_emitted[me, t] >= 0
            else:
                return model.mass_energy_emitted[me, t] == 0

        self.model.set_emitted_streams_con = Constraint(self.model.ME_STREAMS, self.model.TIME,
                                                        rule=_set_emitted_streams_rule)

        def _set_saleable_streams_rule(model, me, t):
            # Sets streams, which are sold without limit but for a certain price
            if me in model.SALEABLE_STREAMS:
                return model.mass_energy_sell_stream[me, t] >= 0
            else:
                return model.mass_energy_sell_stream[me, t] == 0

        self.model.set_saleable_streams_con = Constraint(self.model.ME_STREAMS, self.model.TIME,
                                                         rule=_set_saleable_streams_rule)

        def _set_purchasable_streams_rule(model, me, t):
            # Sets streams, which are purchased without limit but for a certain price
            if me in model.PURCHASABLE_STREAMS:
                return model.mass_energy_purchase_stream[me, t] >= 0
            else:
                return model.mass_energy_purchase_stream[me, t] == 0

        self.model.set_purchasable_streams_con = Constraint(self.model.ME_STREAMS, self.model.TIME,
                                                            rule=_set_purchasable_streams_rule)

        def _demand_satisfaction_rule(model, me, t):
            # Sets streams, which are demanded
            if me in model.DEMANDED_STREAMS:  # Case with demand
                if me not in model.TOTAL_DEMANDED_STREAMS:  # Case where demand needs to be satisfied in every t
                    return model.mass_energy_demand[me, t] == model.stream_demand[me, t]
                else:
                    return Constraint.Skip
            else:  # Case without demand
                return model.mass_energy_demand[me, t] == 0

        self.model.demand_satisfaction_con = Constraint(self.model.ME_STREAMS, self.model.TIME,
                                                        rule=_demand_satisfaction_rule)

        def _total_demand_satisfaction_rule(model, me):
            # Sets streams, which are demanded
            if me in model.DEMANDED_STREAMS:  # Case with demand
                if me in model.TOTAL_DEMANDED_STREAMS:  # Case where demand needs to be satisfied over all t
                    return sum(model.mass_energy_demand[me, t] for t in model.TIME) \
                           == model.stream_demand[me, 0]
                else:
                    return Constraint.Skip
            else:
                return Constraint.Skip

        self.model.total_demand_satisfaction_con = Constraint(self.model.ME_STREAMS,
                                                              rule=_total_demand_satisfaction_rule)

        def _mass_energy_balance_rule(model, me_out, t):
            # Sets mass energy balance for all components
            # produced (out), generated, discharged, available and purchased streams
            #   = emitted, sold, demanded, charged and used (in) streams
            if False:
                return sum(model.mass_energy_component_out_streams[c, me_out, t] for c in model.CONVERSION_COMPONENTS) \
                       + model.mass_energy_purchase_stream[me_out, t] \
                       + model.mass_energy_available[me_out, t] \
                       + model.mass_energy_storage_out_streams[me_out, t] \
                       + model.mass_energy_total_generation[me_out, t] \
                       - model.mass_energy_emitted[me_out, t] \
                       - model.mass_energy_sell_stream[me_out, t] \
                       - model.mass_energy_storage_in_streams[me_out, t] \
                       - model.mass_energy_demand[me_out, t] \
                       == sum(model.mass_energy_component_in_streams[c, me_out, t] for c in model.CONVERSION_COMPONENTS)

            else:
                stream_object = self.pm_object.get_stream(me_out)
                equation_lhs = []
                equation_rhs = []

                if stream_object.is_available():
                    equation_lhs.append(model.mass_energy_available[me_out, t])
                if stream_object.is_emittable():
                    equation_lhs.append(-model.mass_energy_emitted[me_out, t])
                if stream_object.is_purchasable():
                    equation_lhs.append(model.mass_energy_purchase_stream[me_out, t])
                if stream_object.is_saleable():
                    equation_lhs.append(-model.mass_energy_sell_stream[me_out, t])
                if stream_object.is_demanded():
                    equation_lhs.append(-model.mass_energy_demand[me_out, t])
                if me_out in model.STORAGES:
                    equation_lhs.append(
                        model.mass_energy_storage_out_streams[me_out, t] - model.mass_energy_storage_in_streams[
                            me_out, t])
                if me_out in model.GENERATED_STREAMS:
                    equation_lhs.append(model.mass_energy_total_generation[me_out, t])

                for c in model.CONVERSION_COMPONENTS:
                    if (c, me_out) in self.output_tuples:
                        equation_lhs.append(model.mass_energy_component_out_streams[c, me_out, t])

                    if (c, me_out) in self.input_tuples:
                        equation_rhs.append(model.mass_energy_component_in_streams[c, me_out, t])

                return sum(equation_lhs) == sum(equation_rhs)

        self.model._mass_energy_balance_con = Constraint(self.model.ME_STREAMS, self.model.TIME,
                                                         rule=_mass_energy_balance_rule)

        def _stream_conversion_rule(model, c, me_in, me_out, t):
            # Define ratio between input and output streams for all conversion tuples
            if (c, me_in, me_out) in self.conversion_tuples:
                return model.mass_energy_component_out_streams[c, me_out, t] == \
                       model.mass_energy_component_in_streams[c, me_in, t] \
                       * model.CONVERSION_FACTOR[c, me_in, me_out]
            else:
                return Constraint.Skip

        self.model.stream_conversion_con = Constraint(self.model.COMPONENTS, self.model.ME_STREAMS,
                                                      self.model.ME_STREAMS, self.model.TIME,
                                                      rule=_stream_conversion_rule)

        def _stream_conversion_input_rule(model, c, me_in, t):
            # Sets all inputs to 0 if not in conversion tuples
            if (c, me_in) not in self.input_tuples:
                return model.mass_energy_component_in_streams[c, me_in, t] == 0
            else:
                return Constraint.Skip

        self.model._stream_conversion_input_con = Constraint(self.model.COMPONENTS, self.model.ME_STREAMS,
                                                             self.model.TIME, rule=_stream_conversion_input_rule)

        def _stream_conversion_output_rule(model, c, me_out, t):
            # Sets all outputs to 0 if not in conversion tuples
            if (c, me_out) not in self.output_tuples:
                return model.mass_energy_component_out_streams[c, me_out, t] == 0
            else:
                return Constraint.Skip
        self.model._stream_conversion_output_con = Constraint(self.model.COMPONENTS, self.model.ME_STREAMS,
                                                              self.model.TIME, rule=_stream_conversion_output_rule)

        def power_generation_rule(model, g, me, t):
            # Limits generation to capacity factor * generator capacity for each t
            # todo: adjustment: '<=' durch abregelung?

            if me in model.GENERATED_STREAMS:
                return model.mass_energy_generation[g, me, t] == sum(model.generation_profiles[g, t]
                                                                  * model.nominal_cap[g] for g in model.GENERATORS
                                                                  if me == self.pm_object.get_component(g).get_generated_stream())
            else:
                return model.mass_energy_generation[g, me, t] == 0
        self.model.power_generation_con = Constraint(self.model.GENERATORS, self.model.ME_STREAMS, self.model.TIME,
                                                     rule=power_generation_rule)

        def total_power_generation_rule(model, me, t):
            return model.mass_energy_total_generation[me, t] == sum(model.mass_energy_generation[g, me, t]
                                                                    for g in model.GENERATORS)
        self.model.total_power_generation_con = Constraint(self.model.ME_STREAMS, self.model.TIME,
                                                           rule=total_power_generation_rule)

        def _conversion_maximal_component_capacity_rule(model, c, me_in, t):
            # Limits conversion on capacity of conversion unit and defines conversions
            # Important: Capacity is always matched with input
            if (c, me_in) in self.main_tuples:
                return model.mass_energy_component_in_streams[c, me_in, t] <= model.nominal_cap[c] * model.max_p[c]
            else:
                return Constraint.Skip
        self.model._conversion_maximal_component_capacity_con = \
            Constraint(self.model.CONVERSION_COMPONENTS, self.model.ME_STREAMS, self.model.TIME,
                       rule=_conversion_maximal_component_capacity_rule)

        def _ramp_up_rule(model, c, me_in, t):
            # Sets limits of change based on ramp up
            if c in model.SHUT_DOWN_COMPONENTS:
                if (c, me_in) in self.main_tuples:
                    if t > 0:
                        return model.mass_energy_component_in_streams[c, me_in, t] <= \
                               (model.mass_energy_component_in_streams[c, me_in, t - 1]
                                + model.nominal_cap[c] * model.ramp_up[c]
                                + model.status_switch_on[c, t] * 10000)
                    else:
                        return Constraint.Skip
                else:
                    return Constraint.Skip
            else:
                if (c, me_in) in self.main_tuples:
                    if t > 0:
                        return model.mass_energy_component_in_streams[c, me_in, t] <= \
                               (model.mass_energy_component_in_streams[c, me_in, t - 1]
                                + model.nominal_cap[c] * model.ramp_up[c])
                    else:
                        return Constraint.Skip
                else:
                    return Constraint.Skip
        self.model._ramp_up_con = Constraint(self.model.CONVERSION_COMPONENTS, self.model.ME_STREAMS,
                                             self.model.TIME, rule=_ramp_up_rule)

        def _ramp_down_rule(model, c, me_in, t):
            # Sets limits of change based on ramp down
            if c in model.SHUT_DOWN_COMPONENTS:
                # If shut down is possible, the change is unlimited
                if (c, me_in) in self.main_tuples:
                    if t > 0:
                        return model.mass_energy_component_in_streams[c, me_in, t] >= \
                               (model.mass_energy_component_in_streams[c, me_in, t - 1]
                                - model.nominal_cap[c] * model.ramp_down[c]
                                - model.status_switch_on[c, t] * 10000)
                    else:
                        return Constraint.Skip
                else:
                    return Constraint.Skip
            else:
                if (c, me_in) in self.main_tuples:
                    if t > 0:
                        return model.mass_energy_component_in_streams[c, me_in, t] >= \
                               (model.mass_energy_component_in_streams[c, me_in, t - 1]
                                - model.nominal_cap[c] * model.ramp_down[c])
                    else:
                        return Constraint.Skip
                else:
                    return Constraint.Skip
        self.model._ramp_down_con = Constraint(self.model.CONVERSION_COMPONENTS, self.model.ME_STREAMS,
                                               self.model.TIME, rule=_ramp_down_rule)

        """ Component shut down and start up constraints """
        if True:
            def _correct_power_rule(model, c, me_in, t):
                # Sets status binary to 0 if in stream is higher than nominal capacity * min p
                if (c, me_in) in self.main_tuples:
                    return (model.nominal_cap[c] * model.min_p[c]
                            - model.mass_energy_component_in_streams[c, me_in, t]
                            - model.component_correct_p[c, t] * 10000) <= 0
                else:
                    return Constraint.Skip
            self.model._correct_power_con = Constraint(self.model.SHUT_DOWN_COMPONENTS,
                                                       self.model.ME_STREAMS, self.model.TIME,
                                                       rule=_correct_power_rule)

        def _active_component_rule(model, c, me_in, t):
            # Set binary to 1 if component is active
            if (c, me_in) in self.main_tuples:
                return model.mass_energy_component_in_streams[c, me_in, t] \
                       - model.component_status[c, t] * model.M <= 0
            else:
                return Constraint.Skip
        self.model._active_component_con = Constraint(self.model.SHUT_DOWN_COMPONENTS,
                                                      self.model.ME_STREAMS, self.model.TIME,
                                                      rule=_active_component_rule)

        def _balance_switch_rule(model, c, t):
            # forbids simultaneous switch on and off
            return model.status_switch_off[c, t] + model.status_switch_on[c, t] <= 1
        self.model._balance_switch_con = Constraint(self.model.SHUT_DOWN_COMPONENTS, self.model.TIME,
                                                    rule=_balance_switch_rule)

        def _define_status_rule(model, c, t):
            # status is either 1 or 0 and can be changed with switch on (0 -> 1) or switch off (1 -> 0)
            if t > 0:
                return model.component_status[c, t] == model.component_status[c, t - 1] + \
                       model.status_switch_on[c, t] - model.status_switch_off[c, t]
            else:
                return Constraint.Skip
        self.model._define_status_con = Constraint(self.model.SHUT_DOWN_COMPONENTS, self.model.TIME,
                                                   rule=_define_status_rule)

        if False:
            def _define_machine_rule(model, c, t):
                # todo: delete
                return model.component_status[c, t] - model.component_correct_p[c, t] == model.component_status_1[c, t]
            self.model._define_machine_con = Constraint(self.model.SHUT_DOWN_COMPONENTS, self.model.TIME,
                                                        rule=_define_machine_rule)

        def _deactivate_component_rule(model, c, t):
            # if component is shut off, it can not be turned on again
            # without waiting for time = shut down time + start up time
            range_time = int(min(max(model.TIME) - t, model.shut_down_time[c] + model.start_up_time[c]))
            if t < max(model.TIME):
                return model.status_switch_off[c, t] * range_time <= \
                       (range_time - sum(model.status_switch_on[c, t + i] for i in range(0, range_time)))
            else:
                return Constraint.Skip
        self.model._deactivate_component_con = Constraint(self.model.SHUT_DOWN_COMPONENTS, self.model.TIME,
                                                          rule=_deactivate_component_rule)

        """ Capacity of scalable units """
        def capacity_binary_sum_rule(model, c):
            # For each component, only one capacity over all integer steps can be 1
            return sum(model.capacity_binary[c, i] for i in model.INTEGER_STEPS) <= 1
        self.model.capacity_binary_sum_con = Constraint(self.model.SCALABLE_COMPONENTS,
                                                        rule=capacity_binary_sum_rule)

        def capacity_binary_activation_rule(model, c, i):
            # Capacity binary will be 1 if the capacity of the integer step is higher than 0
            return model.capacity_binary[c, i] >= model.nominal_cap_pre[c, i] / 10000
        self.model.capacity_binary_activation_con = Constraint(self.model.SCALABLE_COMPONENTS, self.model.INTEGER_STEPS,
                                                               rule=capacity_binary_activation_rule)

        def set_lower_bound_rule(model, c, i):
            # capacity binary sets lower bound. Lower bound is not predefined as each capacity step can be 0
            return model.nominal_cap_pre[c, i] >= self.lower_bound_dict[c, i] * model.capacity_binary[c, i]
        self.model.set_lower_bound_con = Constraint(self.model.SCALABLE_COMPONENTS, self.model.INTEGER_STEPS,
                                                    rule=set_lower_bound_rule)

        def final_capacity_rule(model, c):
            # Final capacity of component is sum of capacity over all integer steps
            return model.nominal_cap[c] == sum(model.nominal_cap_pre[c, i] for i in model.INTEGER_STEPS)
        self.model.final_capacity_con = Constraint(self.model.SCALABLE_COMPONENTS, rule=final_capacity_rule)

        if False:

            def lower_bound_adherence_rule(model, c, i):
                # To allow the capacity steps to be 0, they have no lower bound.
                # Therefore, it is ensured that the lower bound is adhered
                # Activates binary if the capacity is lower than the lower bound of the integer step
                # This binary is later used to penalize the objective function
                if i == 0:
                    return model.penalty_binary_lower_bound[c, i] == 1
                else:
                    return model.penalty_binary_lower_bound[c, i] >= (self.lower_bound_dict[c, i] - model.nominal_cap_pre[c, i]) / 1000
            self.model.lower_bound_adherence_con = Constraint(self.model.SCALABLE_COMPONENTS,
                                                              self.model.INTEGER_STEPS,
                                                              rule=lower_bound_adherence_rule)

        """ Storage constraints """
        def storage_balance_rule(model, me, t):
            # Defines the SOC of the storage unit
            if me in model.STORAGES:
                if t == 0:  # First SOC based on options
                    return model.soc[me, t] == model.initial_soc[me] * model.nominal_cap[me]
                else:
                    return model.soc[me, t] == model.soc[me, t - 1] \
                           + model.mass_energy_storage_in_streams[me, t - 1] * model.charging_efficiency[me] \
                           - model.mass_energy_storage_out_streams[me, t - 1] / model.discharging_efficiency[me]
            else:
                return model.soc[me, t] == 0

        self.model.storage_balance_con = Constraint(self.model.ME_STREAMS, self.model.TIME,
                                                    rule=storage_balance_rule)

        def last_soc_rule(model, me):
            # Defines SOC in last to as no charging and discharging is possible
            return model.soc[me, max(model.TIME)] == model.initial_soc[me] * model.nominal_cap[me]

        self.model.last_soc_con = Constraint(self.model.STORAGES, rule=last_soc_rule)

        def soc_max_bound_rule(model, me, t):
            # Sets upper bound of SOC
            return model.soc[me, t] <= model.maximal_soc[me] * model.nominal_cap[me]

        self.model.soc_max = Constraint(self.model.STORAGES, self.model.TIME, rule=soc_max_bound_rule)

        def soc_min_bound_rule(model, me, t):
            # Sets lower bound of SOC
            return model.soc[me, t] >= model.minimal_soc[me] * model.nominal_cap[me]

        self.model.soc_min = Constraint(self.model.STORAGES, self.model.TIME, rule=soc_min_bound_rule)

        def storage_charge_upper_bound_rule(model, me, t):
            # Sets maximal in stream into storage based on set ratio
            if me in model.STORAGES:
                if t == model.TIME[-1]:
                    return model.mass_energy_storage_in_streams[me, t] == 0
                else:
                    return model.mass_energy_storage_in_streams[me, t] <= model.nominal_cap[me] / \
                           model.ratio_capacity_p[me]
            else:
                return model.mass_energy_storage_in_streams[
                           me, t] == 0  # Defines all streams of non storable streams

        self.model.storage_charge_upper_bound_con = Constraint(self.model.ME_STREAMS, self.model.TIME,
                                                               rule=storage_charge_upper_bound_rule)

        def storage_discharge_upper_bound_rule(model, me, t):
            # Sets maximal out stream into storage based on set ratio
            if me in model.STORAGES:
                if t == model.TIME[-1]:
                    return model.mass_energy_storage_out_streams[me, t] == 0
                else:
                    return model.mass_energy_storage_out_streams[me, t] / model.discharging_efficiency[me] \
                           <= self.model.nominal_cap[me] / model.ratio_capacity_p[me]
            else:
                return model.mass_energy_storage_out_streams[
                           me, t] == 0  # Defines all streams of non storable streams

        self.model.storage_discharge_upper_bound_con = Constraint(self.model.ME_STREAMS, self.model.TIME,
                                                                  rule=storage_discharge_upper_bound_rule)

        def storage_limitation_to_component_rule(model, s):
            # todo: delete completely to avoid complex cases?
            # Sets storage limitation based on other component.
            # E.g., if battery should be able to store max a 24 hour supply for electrolysis
            c = model.storage_limiting_component[s]
            coefficient = 1
            for stream in model.ME_STREAMS:
                if (c, stream, s) in [*self.conversion_tuples_dict.keys()]:
                    # Case, the storage is based in input -> Adjust coefficient
                    coefficient = self.conversion_tuples_dict[(c, stream, s)]
                    if (c, stream) in self.main_tuples:
                        break
            return model.nominal_cap[s] == model.nominal_cap[model.storage_limiting_component[s]] \
                   * model.storage_limiting_component_ratio[s] * coefficient
            # todo: wenn input, dann muss die effizienz noch eingerechnet werden

        self.model.storage_limitation_to_component_con = Constraint(self.model.LIMITED_STORAGES,
                                                                    rule=storage_limitation_to_component_rule)

        """ STORAGE BINARY DECISIONS """

        def storage_binary_sum_rule(model, s, t):
            # Constraints simultaneous charging and discharging
            return model.storage_charge_binary[s, t] + model.storage_discharge_binary[s, t] <= 1

        self.model.storage_binary_sum_con = Constraint(self.model.STORAGES, self.model.TIME,
                                                       rule=storage_binary_sum_rule)

        def charge_binary_activation_rule(model, s, t):
            # Define charging binary -> if charged, binary = 1
            return model.mass_energy_storage_in_streams[s, t] - model.storage_charge_binary[s, t] * model.M <= 0

        self.model.charge_binary_activation_con = Constraint(self.model.STORAGES, self.model.TIME,
                                                             rule=charge_binary_activation_rule)

        def discharge_binary_activation_rule(model, s, t):
            # Define discharging binary -> if discharged, binary = 1
            return model.mass_energy_storage_out_streams[s, t] - model.storage_discharge_binary[
                s, t] * model.M <= 0

        self.model.discharge_binary_activation_con = Constraint(self.model.STORAGES, self.model.TIME,
                                                                rule=discharge_binary_activation_rule)

        """ Financial constraints """
        def _investment_rule(model, c):
            # Calculates investment for each component
            if c in model.SCALABLE_COMPONENTS:
                return model.investment[c] == sum(model.nominal_cap_pre[c, i] * model.capex_pre_var[c, i]
                                                  + model.capex_pre_fix[c, i] * model.capacity_binary[c, i]
                                                  for i in model.INTEGER_STEPS)
            else:
                return model.investment[c] == model.nominal_cap[c] * model.capex_var[c] + model.capex_fix[c]
        self.model.investment_con = Constraint(self.model.COMPONENTS, rule=_investment_rule)

        def _annuity_rule(model, c):
            # Calculates annuity for each component
            return model.annuity[c] == model.investment[c] * model.ANF[c]
        self.model.annuity_con = Constraint(self.model.COMPONENTS, rule=_annuity_rule)

        def _total_annuity_rule(model):
            # Sums total annuity over all components
            return model.total_annuity == sum(model.annuity[c] for c in model.COMPONENTS)
        self.model.total_annuity_con = Constraint(rule=_total_annuity_rule)

        def _maintenance_cost_rule(model, c):
            # Calculates maintenance cost for each component
            return model.maintenance_costs[c] == model.investment[c] * model.maintenance[c]
        self.model.maintenance_cost_con = Constraint(self.model.COMPONENTS, rule=_maintenance_cost_rule)

        def total_maintenance_cost_rule(model):
            # Sum maintenance costs over all components
            return model.total_maintenance_costs == sum(model.maintenance_costs[c] for c in model.COMPONENTS)
        self.model.total_maintenance_cost_con = Constraint(rule=total_maintenance_cost_rule)

        def taxes_and_insurance_cost_rule(model, c):
            # Calculate taxes and insurance
            if self.pm_object.get_applied_parameter_for_component('taxes_and_insurance', c):
                return model.taxes_and_insurance_costs[c] == model.investment[c] * model.taxes_and_insurance
            else:
                return model.taxes_and_insurance_costs[c] == 0
        self.model.taxes_and_insurance_cost_con = Constraint(self.model.COMPONENTS, rule=taxes_and_insurance_cost_rule)

        def total_taxes_and_insurance_cost_rule(model):
            # Calculate total taxes and insurance
            return model.total_taxes_and_insurance_costs == sum(model.taxes_and_insurance_costs[c] for c in model.COMPONENTS)
        self.model.total_taxes_and_insurance_cost_con = Constraint(rule=total_taxes_and_insurance_cost_rule)

        def overhead_costs_rule(model, c):
            # Calculate total overhead costs
            if self.pm_object.get_applied_parameter_for_component('overhead', c):
                return model.overhead_costs[c] == self.model.investment[c] * model.overhead
            else:
                return model.overhead_costs[c] == 0
        self.model.overhead_costs_con = Constraint(self.model.COMPONENTS, rule=overhead_costs_rule)

        def total_overhead_costs_rule(model):
            # Calculate total overhead costs
            return model.total_overhead_costs == sum(self.model.overhead_costs[c] for c in model.COMPONENTS)
        self.model.total_overhead_costs_con = Constraint(rule=total_overhead_costs_rule)

        def personnel_costs_rule(model, c):
            # Calculate total personal costs
            if self.pm_object.get_applied_parameter_for_component('personnel_costs', c):
                return model.personnel_costs[c] == self.model.investment[c] * model.personnel_cost
            else:
                return model.personnel_costs[c] == 0
        self.model.personnel_costs_con = Constraint(self.model.COMPONENTS, rule=personnel_costs_rule)

        def total_personnel_costs_rule(model):
            # Calculate total personal costs
            return model.total_personnel_costs == sum(self.model.personnel_costs[c] for c in self.model.COMPONENTS)
        self.model.total_personnel_costs_con = Constraint(rule=total_personnel_costs_rule)

        def working_capital_rule(model, c):
            # calculate total working capital
            if self.pm_object.get_applied_parameter_for_component('working_capital', c):
                return model.working_capital_costs[c] == (self.model.investment[c]
                                                          / (1 - model.working_capital)
                                                          * model.working_capital) * model.wacc
            else:
                return model.working_capital_costs[c] == 0
        self.model.working_capital_con = Constraint(self.model.COMPONENTS, rule=working_capital_rule)

        def total_working_capital_rule(model):
            # calculate total working capital
            return model.total_working_capital_costs == sum(model.working_capital_costs[c] for c in model.COMPONENTS)
        self.model.total_working_capital_con = Constraint(rule=total_working_capital_rule)

        def _purchase_costs_rule(model, me):
            # calculate purchase costs of each stream
            return model.purchase_costs[me] == sum(model.mass_energy_purchase_stream[me, t]
                                                   * model.purchase_price[me, t] for t in model.TIME)
        self.model._purchase_costs_con = Constraint(self.model.PURCHASABLE_STREAMS, rule=_purchase_costs_rule)

        def _total_purchase_costs_rule(model):
            # Sum purchase costs over all streams
            return model.total_purchase_costs == sum(model.purchase_costs[me] for me in model.PURCHASABLE_STREAMS)
        self.model.total_purchase_costs_rule = Constraint(rule=_total_purchase_costs_rule)

        def _revenue_rule(model, me):
            # Calculate revenue for each stream
            return model.revenue[me] == sum(model.mass_energy_sell_stream[me, t]
                                            * model.selling_price[me, t] for t in model.TIME)
        self.model.revenue_con = Constraint(self.model.SALEABLE_STREAMS, rule=_revenue_rule)

        def _total_revenue_rule(model):
            # sum revenue over all streams
            return model.total_revenue == sum(model.revenue[me] for me in model.SALEABLE_STREAMS)
        self.model._total_revenue_con = Constraint(rule=_total_revenue_rule)

        def power_lower_bound_ignoring_penalty_rule(model):
            # Penalize capacities lower than lower bound
            if False:
                return model.power_penalty == sum(-(model.component_status[c, t]
                                                   - model.component_correct_p[c, t] - 1) * model.M
                                                  for c in model.SHUT_DOWN_COMPONENTS
                                                  for t in model.TIME)
            else:
                return model.power_penalty == model.test_b * 1000000000
        self.model.capacity_lower_bound_ignoring_penalty_con = Constraint(
            rule=power_lower_bound_ignoring_penalty_rule)

        def test_rule(model):
            return model.test_b * 10000000000 >= sum((model.component_status[c, t]
                                        + model.component_correct_p[c, t] - 1)
                                       for c in model.SHUT_DOWN_COMPONENTS
                                       for t in model.TIME)
        self.model.test_con = Constraint(rule=test_rule)

        def objective_function(model):
            # Define objective function
            return (model.total_annuity
                    + model.total_maintenance_costs
                    + model.total_taxes_and_insurance_costs
                    + model.total_overhead_costs
                    + model.total_personnel_costs
                    + model.total_working_capital_costs
                    + model.total_purchase_costs
                    - model.total_revenue
                    + model.power_penalty)
        self.model.obj = Objective(rule=objective_function, sense=minimize)

    def optimize(self):

        opt = pyo.SolverFactory(self.solver, solver_io="python")
        self.instance = self.model.create_instance()
        opt.options["mipgap"] = 0.05
        results = opt.solve(self.instance, tee=True)
        print(results)

    def __init__(self, pm_object, path_data, solver):

        self.conversion_tuples = []
        self.conversion_tuples_dict = {}
        self.main_tuples = []
        self.side_tuples = []
        self.main_out_streams = []
        self.input_tuples = []
        self.output_tuples = []

        # Define model
        self.model = ConcreteModel()

        # ----------------------------------
        # Set up problem
        self.pm_object = self.pre_adjustments(pm_object)
        self.path_data = path_data
        self.solver = solver
        self.instance = None
        self.initialize_problem()
        self.post_adjustments()
        self.attach_constraints()
        self.optimize()
