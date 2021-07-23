import pyomo.environ as pyo
from pyomo.core import *
import pandas as pd
from pyomo.core import Binary
from copy import deepcopy
from pyomo.opt import SolverStatus, TerminationCondition

from _helper_optimization import calculate_economies_of_scale_steps


class OptimizationProblem:

    def create_initial_solution(self, pm_object):
        """ Especially the shutdown ability and parallel units
        create a large problem due to the large amount of binaries.
        Therefore, the problem is solved without these two options to create
        an initial solution """

        # Create simpler model and optimize to get warm start solution
        pm_object_warm_start = deepcopy(pm_object)

        conv_components = pm_object_warm_start.get_specific_components('final', 'conversion')
        for c in conv_components:
            c.set_shut_down_ability(False)
            c.set_number_parallel_units(1)

        pm_object_warm_start = self.pre_adjustments(pm_object_warm_start)
        model = self.initialize_problem(pm_object_warm_start)
        model = self.post_adjustments(pm_object_warm_start, model)
        model = self.attach_constraints(pm_object_warm_start, model)
        instance, results = self.optimize(model)

        solved_feasible = False
        if (results.solver.status == SolverStatus.ok) & (results.solver.termination_condition == TerminationCondition.optimal):
            solved_feasible = True

        self.reset_information()

        if solved_feasible:

            # Implement complex model and retrieve instance
            pm_object_adjusted = self.pre_adjustments(pm_object)
            model_adjusted = self.initialize_problem(pm_object_adjusted)
            model_adjusted = self.post_adjustments(pm_object_adjusted, model_adjusted)
            model_adjusted = self.attach_constraints(pm_object_adjusted, model_adjusted)
            instance_adjusted = model_adjusted.create_instance()

            # Parallel units will have no capacity
            # Respective variables are capacity_binary, nominal_cap and nominal_cap_pre
            for component_object in pm_object.get_specific_components('final', 'conversion'):
                component_name = component_object.get_name()
                capacity = instance.nominal_cap[component_name].value

                lower_bound_dict = {}
                upper_bound_dict = {}
                if component_object.is_scalable():
                    lower_bound, upper_bound, coefficient, intercept = calculate_economies_of_scale_steps(
                        component_object, pm_object_adjusted)

                    for key in [*lower_bound.keys()]:
                        lower_bound_dict[key] = lower_bound[key]

                    for key in [*upper_bound.keys()]:
                        upper_bound_dict[key] = upper_bound[key]

                if component_object.get_number_parallel_units() > 1:
                    # Several parallel units exist
                    for i in range(0, int(component_object.get_number_parallel_units())):
                        parallel_unit_component_name = component_name + '_' + str(i)
                        if i == 0:
                            # As initial solution, the component_0 will have the values of the single component of
                            # the simple problem
                            instance_adjusted.nominal_cap[parallel_unit_component_name] = capacity
                            if component_object.is_scalable():
                                for j in range(pm_object_adjusted.get_integer_steps()):
                                    lower_bound = lower_bound_dict[(component_name, j)]
                                    upper_bound = upper_bound_dict[(component_name, j)]
                                    if (capacity >= lower_bound) & (capacity <= upper_bound):
                                        # if capacity of simple solution is between lb and ub of component
                                        # This integer step will be chosen
                                        instance_adjusted.nominal_cap_pre[(parallel_unit_component_name, j)] = capacity
                                        instance_adjusted.capacity_binary[(parallel_unit_component_name, j)] = 1
                                    else:
                                        instance_adjusted.nominal_cap_pre[(parallel_unit_component_name, j)] = 0
                                        instance_adjusted.capacity_binary[(parallel_unit_component_name, j)] = 0

                            if component_object.get_shut_down_ability():
                                # if component is able for shutdown, it will set the binaries s.t. no shutdown is initiated
                                for t in model.TIME:

                                    # Time depending variables
                                    instance_adjusted.component_correct_p[(parallel_unit_component_name, t)] = 0
                                    instance_adjusted.component_status[(parallel_unit_component_name, t)] = 1
                                    instance_adjusted.status_switch_on[(parallel_unit_component_name, t)] = 0
                                    instance_adjusted.status_switch_off[(parallel_unit_component_name, t)] = 0
                        else:
                            # component_x will have no capacity
                            instance_adjusted.nominal_cap[parallel_unit_component_name] = 0
                            for j in range(pm_object_adjusted.get_integer_steps()):
                                if j == 0:
                                    instance_adjusted.nominal_cap_pre[(parallel_unit_component_name, j)] = 0
                                    instance_adjusted.capacity_binary[(parallel_unit_component_name, j)] = 1
                                else:
                                    instance_adjusted.nominal_cap_pre[(parallel_unit_component_name, j)] = 0
                                    instance_adjusted.capacity_binary[(parallel_unit_component_name, j)] = 0

                            if component_object.get_shut_down_ability():
                                for t in model.TIME:

                                    # Time depending variables
                                    instance_adjusted.component_correct_p[(parallel_unit_component_name, t)] = 1
                                    instance_adjusted.component_status[(parallel_unit_component_name, t)] = 0
                                    instance_adjusted.status_switch_on[(parallel_unit_component_name, t)] = 0
                                    instance_adjusted.status_switch_off[(parallel_unit_component_name, t)] = 0

                else:
                    # No parallel units
                    instance_adjusted.nominal_cap[component_name] = capacity
                    # integer depending binaries: capacity binary and nominal cap pre
                    if component_object.is_scalable():
                        for j in range(pm_object_adjusted.get_integer_steps()):
                            lower_bound = lower_bound_dict[(component_name, j)]
                            upper_bound = upper_bound_dict[(component_name, j)]
                            if (capacity >= lower_bound) & (capacity <= upper_bound):
                                instance_adjusted.nominal_cap_pre[(component_name, j)] = capacity
                                instance_adjusted.capacity_binary[(component_name, j)] = 1
                            else:
                                instance_adjusted.nominal_cap_pre[(component_name, j)] = 0
                                instance_adjusted.capacity_binary[(component_name, j)] = 0

                    if component_object.get_shut_down_ability():
                        # Time depending binaries
                        for t in model.TIME:

                            instance_adjusted.component_correct_p[(component_name, t)] = 0
                            instance_adjusted.component_status[(component_name, t)] = 1
                            instance_adjusted.status_switch_on[(component_name, t)] = 0
                            instance_adjusted.status_switch_off[(component_name, t)] = 0

            # Create variables, which are not in instance as shutdown was forbidden
            # Respective variables are component_correct_p, component_status
            # switch_on and switch_off

                return solved_feasible, model_adjusted, instance_adjusted, pm_object_adjusted

            else:

                return solved_feasible

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

    def initialize_problem(self, pm_object):

        """ Add variables, parameters etc. to the optimization problem """
        model = ConcreteModel()

        # -------------------------------------
        # General Parameters
        general_parameters = pm_object.get_general_parameter_value_dictionary()

        model.wacc = Param(initialize=general_parameters['wacc'])
        model.taxes_and_insurance = Param(initialize=general_parameters['taxes_and_insurance'])
        model.overhead = Param(initialize=general_parameters['overhead'])
        model.working_capital = Param(initialize=general_parameters['working_capital'])
        model.personnel_cost = Param(initialize=general_parameters['personnel_costs'])

        # Time range
        model.TIME = RangeSet(0, general_parameters['covered_period'] - 1)

        # -------------------------------------
        # Components
        all_components = []
        conversion_components = []
        storage_components = []
        generator_components = []

        for component_object in pm_object.get_specific_components('final'):
            all_components.append(component_object.get_name())
            if component_object.get_component_type() == 'conversion':
                conversion_components.append(component_object.get_name())
            elif component_object.get_component_type() == 'generator':
                generator_components.append(component_object.get_name())
            elif component_object.get_component_type() == 'storage':
                storage_components.append(component_object.get_name())

        model.CONVERSION_COMPONENTS = Set(initialize=conversion_components)
        model.STORAGES = Set(initialize=storage_components)
        model.GENERATORS = Set(initialize=generator_components)
        model.COMPONENTS = Set(initialize=all_components)

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
        for stream in pm_object.get_specific_streams('final'):

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

        model.ME_STREAMS = Set(initialize=final_streams)
        model.AVAILABLE_STREAMS = Set(initialize=available_streams)
        model.EMITTED_STREAMS = Set(initialize=emittable_streams)
        model.PURCHASABLE_STREAMS = Set(initialize=purchasable_streams)
        model.SALEABLE_STREAMS = Set(initialize=saleable_streams)
        model.DEMANDED_STREAMS = Set(initialize=demanded_streams)
        model.TOTAL_DEMANDED_STREAMS = Set(initialize=total_demand_streams)

        generated_streams = []
        for generator in pm_object.get_specific_components('final', 'generator'):
            generated_streams.append(generator.get_generated_stream())
        model.GENERATED_STREAMS = Set(initialize=generated_streams)

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

        for component_object in pm_object.get_specific_components('final'):
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
                        component_object, pm_object)
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

        model.SCALABLE_COMPONENTS = Set(initialize=scalable_components)
        model.SHUT_DOWN_COMPONENTS = Set(initialize=shut_down_components)
        model.LIMITED_STORAGES = Set(initialize=limited_storages)

        # Parameters of components
        model.lifetime = Param(model.COMPONENTS,
                                    initialize=lifetime_dict,
                                    mutable=True)
        model.maintenance = Param(model.COMPONENTS,
                                       initialize=maintenance_dict,
                                       mutable=True)

        # Financial parameters
        model.capex_var = Param(model.COMPONENTS,
                                     initialize=capex_var_dict,
                                     mutable=True)

        model.capex_fix = Param(model.COMPONENTS,
                                     initialize=capex_fix_dict,
                                     mutable=True)

        # Technical Parameters
        model.min_p = Param(model.CONVERSION_COMPONENTS, initialize=min_p_dict)

        model.max_p = Param(model.CONVERSION_COMPONENTS, initialize=max_p_dict)

        model.ramp_up = Param(model.CONVERSION_COMPONENTS, initialize=ramp_up_dict)

        model.ramp_down = Param(model.CONVERSION_COMPONENTS, initialize=ramp_down_dict)

        model.charging_efficiency = Param(model.STORAGES,
                                               initialize=charging_efficiency_dict)

        model.discharging_efficiency = Param(model.STORAGES,
                                                  initialize=discharging_efficiency_dict)

        model.minimal_soc = Param(model.STORAGES,
                                       initialize=min_soc_dict)

        model.maximal_soc = Param(model.STORAGES,
                                       initialize=max_soc_dict)

        model.initial_soc = Param(model.STORAGES,
                                       initialize=initial_soc_dict)

        model.ratio_capacity_p = Param(model.STORAGES,
                                            initialize=ratio_capacity_p_dict)

        model.storage_limiting_component = Param(model.LIMITED_STORAGES,
                                                      initialize=storage_limiting_component_dict)
        model.storage_limiting_component_ratio = Param(model.LIMITED_STORAGES,
                                                            initialize=storage_limiting_component_ratio_dict)

        # Component variables
        model.nominal_cap = Var(model.COMPONENTS, bounds=(0, None))
        model.soc = Var(model.ME_STREAMS, model.TIME, bounds=(0, None))

        """ Integer variables and parameters """
        model.INTEGER_STEPS = RangeSet(0, pm_object.integer_steps)
        # model.pwconst = Piecewise(indexes, yvar, xvar, **Keywords) # todo: Implement with big m
        # https://pyomo.readthedocs.io/en/stable/pyomo_modeling_components/Expressions.html
        model.M = Param(initialize=1000000000)

        # SCALABLE COMPONENTS
        # Set bounds
        def _bounds_rule(self, s, i):
            return 0, upper_bound_dict[(s, i)]

        # ... for scalable components
        # Parameters and variables for scalable components

        # Capacities per integer steps
        model.nominal_cap_pre = Var(model.SCALABLE_COMPONENTS, model.INTEGER_STEPS, bounds=_bounds_rule)

        # Investment linearized: Investment = capex var * capacity + capex fix
        # Variable part of investment -> capex var * capacity
        model.capex_pre_var = Param(model.SCALABLE_COMPONENTS, model.INTEGER_STEPS,
                                         initialize=capex_var_pre_dict)
        # fix part of investment
        model.capex_pre_fix = Param(model.SCALABLE_COMPONENTS, model.INTEGER_STEPS,
                                         initialize=capex_fix_pre_dict)

        # Defines which integer step sets capacity
        model.capacity_binary = Var(model.SCALABLE_COMPONENTS, model.INTEGER_STEPS,
                                         within=Binary)
        # Penalty if capacity lower than its lower bounds
        model.penalty_binary_lower_bound = Var(model.SCALABLE_COMPONENTS, model.INTEGER_STEPS,
                                                    within=Binary)

        # Shutdown parameters and variables
        model.shut_down_time = Param(model.SHUT_DOWN_COMPONENTS, initialize=shut_down_time_dict)
        model.start_up_time = Param(model.SHUT_DOWN_COMPONENTS, initialize=start_up_time_dict)

        model.component_correct_p = Var(model.SHUT_DOWN_COMPONENTS, model.TIME, within=Binary)
        model.component_status = Var(model.SHUT_DOWN_COMPONENTS, model.TIME, within=Binary)
        # model.component_status_1 = Var(model.SHUT_DOWN_COMPONENTS, model.TIME, within=Binary)  # todo: delete
        # model.component_status_2 = Var(model.SHUT_DOWN_COMPONENTS, model.TIME, within=Binary)  # todo: delete
        model.status_switch_on = Var(model.SHUT_DOWN_COMPONENTS, model.TIME, within=Binary)
        model.status_switch_off = Var(model.SHUT_DOWN_COMPONENTS, model.TIME, within=Binary)
        # model.test = Var(model.SHUT_DOWN_COMPONENTS, model.TIME)
        # model.test_2 = Var(model.SCALABLE_COMPONENTS, model.INTEGER_STEPS)
        # model.test_3 = Var()
        model.wrong_power = Var(model.SHUT_DOWN_COMPONENTS, within=Binary)

        # STORAGE binaries (charging and discharging)
        model.storage_charge_binary = Var(model.STORAGES, model.TIME, within=Binary)
        model.storage_discharge_binary = Var(model.STORAGES, model.TIME, within=Binary)

        # -------------------------------------
        # Stream variables
        # Input and output stream
        model.mass_energy_component_in_streams = Var(model.COMPONENTS, model.ME_STREAMS,
                                                          model.TIME, bounds=(0, None))
        model.mass_energy_component_out_streams = Var(model.COMPONENTS, model.ME_STREAMS,
                                                           model.TIME, bounds=(0, None))

        # Freely available streams
        model.mass_energy_available = Var(model.ME_STREAMS, model.TIME, bounds=(0, None))
        model.mass_energy_emitted = Var(model.ME_STREAMS, model.TIME, bounds=(0, None))

        # Charged and discharged streams
        model.mass_energy_storage_in_streams = Var(model.ME_STREAMS, model.TIME, bounds=(0, None))
        model.mass_energy_storage_out_streams = Var(model.ME_STREAMS, model.TIME, bounds=(0, None))

        # sold and purchased streams
        model.mass_energy_sell_stream = Var(model.ME_STREAMS, model.TIME, bounds=(0, None))
        model.mass_energy_purchase_stream = Var(model.ME_STREAMS, model.TIME, bounds=(0, None))

        # generated streams
        model.mass_energy_generation = Var(model.GENERATORS, model.ME_STREAMS, model.TIME,
                                                bounds=(0, None))
        model.mass_energy_total_generation = Var(model.ME_STREAMS, model.TIME, bounds=(0, None))

        # Demanded streams
        model.mass_energy_demand = Var(model.ME_STREAMS, model.TIME, bounds=(0, None))

        # ----------------------------------
        # Financial variables
        model.investment = Var(model.COMPONENTS, bounds=(0, None))  # calculates investment
        model.annuity = Var(model.COMPONENTS, bounds=(0, None))  # calculates annuity
        model.total_annuity = Var(bounds=(0, None))  # sums annuity
        model.maintenance_costs = Var(model.COMPONENTS, bounds=(0, None))  # calculates maintenance
        model.total_maintenance_costs = Var(bounds=(0, None))  # sums maintenance
        model.taxes_and_insurance_costs = Var(model.COMPONENTS, bounds=(0, None))  # calculates taxes and insurance
        model.total_taxes_and_insurance_costs = Var(bounds=(0, None))  # calculates taxes and insurance
        model.overhead_costs = Var(model.COMPONENTS, bounds=(0, None))  # calculates total overhead costs
        model.total_overhead_costs = Var(bounds=(0, None))  # calculates total overhead costs
        model.personnel_costs = Var(model.COMPONENTS, bounds=(0, None))  # calculates total personal costs
        model.total_personnel_costs = Var(bounds=(0, None))  # calculates total personal costs
        model.working_capital_costs = Var(model.COMPONENTS, bounds=(0, None))  # calculates total personal costs
        model.total_working_capital_costs = Var(bounds=(0, None))  # calculates total personal costs
        model.purchase_costs = Var(model.PURCHASABLE_STREAMS, bounds=(0, None))  # calculates purchase costs of each stream
        model.total_purchase_costs = Var(bounds=(0, None))  # sum purchase costs
        model.revenue = Var(model.SALEABLE_STREAMS, bounds=(None, None))  # calculates revenue of each stream
        model.total_revenue = Var(bounds=(None, None))  # sums revenues
        model.capacity_penalty = Var(initialize=0, bounds=(0, None))  # calculates penalty if capacity is not in right range
        model.power_penalty = Var(initialize=0, bounds=(0, None))  # calculates penalty if power is not in right range

        return model

    def post_adjustments(self, pm_object, model):
        """ Any necessary precalculations are conducted here"""

        # Calculate annuity factor of each component
        anf_dict = {}
        for c in model.COMPONENTS:
            anf_component = (1 + model.wacc) ** model.lifetime[c] * model.wacc \
                            / ((1 + model.wacc) ** model.lifetime[c] - 1)
            anf_dict.update({c: anf_component})
        model.ANF = Param(model.COMPONENTS, initialize=anf_dict)

        # Define conversion tuples which will be used to set main conversion and side conversion
        # All other conversions will be set to 0 if not in conversion tuples
        main_conversions = pm_object.get_all_main_conversion()
        for i in main_conversions.index:
            conversion_component = main_conversions.loc[i, 'component']
            input_stream = main_conversions.loc[i, 'input_me']
            output_stream = main_conversions.loc[i, 'output_me']
            coefficient = float(main_conversions.loc[i, 'coefficient'])

            if conversion_component in model.CONVERSION_COMPONENTS:
                self.conversion_tuples.append((conversion_component, input_stream, output_stream))
                self.conversion_tuples_dict.update({(conversion_component, input_stream, output_stream): coefficient})

                self.main_tuples.append((conversion_component, input_stream))
                self.main_out_streams.append(output_stream)
                self.input_tuples.append((conversion_component, input_stream))
                self.output_tuples.append((conversion_component, output_stream))

        side_conversions = pm_object.get_all_side_conversions()
        if not side_conversions.empty:
            for i in side_conversions.index:
                conversion_component = side_conversions.loc[i, 'component']
                input_stream = side_conversions.loc[i, 'input_me']
                output_stream = side_conversions.loc[i, 'output_me']
                coefficient = float(side_conversions.loc[i, 'coefficient'])

                if conversion_component in model.CONVERSION_COMPONENTS:
                    self.conversion_tuples.append((conversion_component, input_stream, output_stream))
                    self.conversion_tuples_dict.update(
                        {(conversion_component, input_stream, output_stream): coefficient})

                    self.side_tuples.append((conversion_component, input_stream))

                    self.input_tuples.append((conversion_component, input_stream))
                    self.output_tuples.append((conversion_component, output_stream))

        model.CONVERSION_FACTOR = Param(model.COMPONENTS, model.ME_STREAMS,
                                             model.ME_STREAMS, initialize=self.conversion_tuples_dict)

        # Attach data to vector parameters, e.g., purchase price
        purchase_price_dict = {}
        sell_price_dict = {}
        demand_dict = {}
        generation_profiles_dict = {}

        for stream in pm_object.get_specific_streams('final'):
            stream_name = stream.get_name()

            # Purchase price
            if stream.is_purchasable():
                if stream.get_purchase_price_type() == 'fixed':
                    for t in model.TIME:
                        purchase_price_dict.update({(stream_name, t): float(stream.get_purchase_price())})

                else:
                    purchase_price_curve = pd.read_excel(self.path_data + stream.get_purchase_price(), index_col=0)
                    for t in model.TIME:
                        purchase_price_dict.update({(stream_name, t): float(purchase_price_curve.loc[t, 'value'])})

            # Selling price
            if stream.is_saleable():
                if stream.get_sale_price_type() == 'fixed':
                    for t in model.TIME:
                        sell_price_dict.update({(stream_name, t): float(stream.get_sale_price())})
                else:
                    sale_price_curve = pd.read_excel(self.path_data + stream.get_sale_price(), index_col=0)
                    for t in model.TIME:
                        sell_price_dict.update({(stream_name, t): float(sale_price_curve.loc[t, 'value'])})

            # Demand
            if stream.is_demanded():
                for t in model.TIME:
                    demand_dict.update({(stream_name, t): float(stream.get_demand())})

        model.purchase_price = Param(model.PURCHASABLE_STREAMS, model.TIME,
                                          initialize=purchase_price_dict)
        model.selling_price = Param(model.SALEABLE_STREAMS, model.TIME,
                                         initialize=sell_price_dict)
        model.stream_demand = Param(model.DEMANDED_STREAMS, model.TIME,
                                         initialize=demand_dict)

        # Set normalized generation profiles
        for generator in pm_object.get_specific_components('final', 'generator'):
            generator_name = generator.get_name()
            generation_profile = pd.read_excel(self.path_data + generator.get_generation_data(), index_col=0)
            for t in model.TIME:
                generation_profiles_dict.update({(generator_name, t): float(generation_profile.loc[t, 'value'])})

        model.generation_profiles = Param(model.GENERATORS, model.TIME,
                                               initialize=generation_profiles_dict)

        return model

    def attach_constraints(self, pm_object, model):
        """ Method attaches all constraints to optimization problem """

        def _set_available_streams_rule(model, me, t):
            # Sets streams, which are available without limit and price
            if me in model.AVAILABLE_STREAMS:
                return model.mass_energy_available[me, t] >= 0
            else:
                return model.mass_energy_available[me, t] == 0

        model.set_available_streams_con = Constraint(model.ME_STREAMS, model.TIME,
                                                          rule=_set_available_streams_rule)

        def _set_emitted_streams_rule(model, me, t):
            # Sets streams, which are emitted without limit and price
            if me in model.EMITTED_STREAMS:
                return model.mass_energy_emitted[me, t] >= 0
            else:
                return model.mass_energy_emitted[me, t] == 0

        model.set_emitted_streams_con = Constraint(model.ME_STREAMS, model.TIME,
                                                   rule=_set_emitted_streams_rule)

        def _set_saleable_streams_rule(model, me, t):
            # Sets streams, which are sold without limit but for a certain price
            if me in model.SALEABLE_STREAMS:
                return model.mass_energy_sell_stream[me, t] >= 0
            else:
                return model.mass_energy_sell_stream[me, t] == 0

        model.set_saleable_streams_con = Constraint(model.ME_STREAMS, model.TIME,
                                                         rule=_set_saleable_streams_rule)

        def _set_purchasable_streams_rule(model, me, t):
            # Sets streams, which are purchased without limit but for a certain price
            if me in model.PURCHASABLE_STREAMS:
                return model.mass_energy_purchase_stream[me, t] >= 0
            else:
                return model.mass_energy_purchase_stream[me, t] == 0

        model.set_purchasable_streams_con = Constraint(model.ME_STREAMS, model.TIME,
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

        model.demand_satisfaction_con = Constraint(model.ME_STREAMS, model.TIME,
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

        model.total_demand_satisfaction_con = Constraint(model.ME_STREAMS,
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
                stream_object = pm_object.get_stream(me_out)
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

        model._mass_energy_balance_con = Constraint(model.ME_STREAMS, model.TIME,
                                                         rule=_mass_energy_balance_rule)

        def _stream_conversion_rule(model, c, me_in, me_out, t):
            # Define ratio between input and output streams for all conversion tuples
            if (c, me_in, me_out) in self.conversion_tuples:
                return model.mass_energy_component_out_streams[c, me_out, t] == \
                       model.mass_energy_component_in_streams[c, me_in, t] \
                       * model.CONVERSION_FACTOR[c, me_in, me_out]
            else:
                return Constraint.Skip

        model.stream_conversion_con = Constraint(model.COMPONENTS, model.ME_STREAMS,
                                                      model.ME_STREAMS, model.TIME,
                                                      rule=_stream_conversion_rule)

        def _stream_conversion_input_rule(model, c, me_in, t):
            # Sets all inputs to 0 if not in conversion tuples
            if (c, me_in) not in self.input_tuples:
                return model.mass_energy_component_in_streams[c, me_in, t] == 0
            else:
                return Constraint.Skip

        model._stream_conversion_input_con = Constraint(model.COMPONENTS, model.ME_STREAMS,
                                                             model.TIME, rule=_stream_conversion_input_rule)

        def _stream_conversion_output_rule(model, c, me_out, t):
            # Sets all outputs to 0 if not in conversion tuples
            if (c, me_out) not in self.output_tuples:
                return model.mass_energy_component_out_streams[c, me_out, t] == 0
            else:
                return Constraint.Skip
        model._stream_conversion_output_con = Constraint(model.COMPONENTS, model.ME_STREAMS,
                                                              model.TIME, rule=_stream_conversion_output_rule)

        def power_generation_rule(model, g, me, t):
            # Limits generation to capacity factor * generator capacity for each t
            # todo: adjustment: '<=' durch abregelung?

            if me in model.GENERATED_STREAMS:
                return model.mass_energy_generation[g, me, t] == sum(model.generation_profiles[g, t]
                                                                  * model.nominal_cap[g] for g in model.GENERATORS
                                                                  if me == pm_object.get_component(g).get_generated_stream())
            else:
                return model.mass_energy_generation[g, me, t] == 0
        model.power_generation_con = Constraint(model.GENERATORS, model.ME_STREAMS, model.TIME,
                                                     rule=power_generation_rule)

        def total_power_generation_rule(model, me, t):
            return model.mass_energy_total_generation[me, t] == sum(model.mass_energy_generation[g, me, t]
                                                                    for g in model.GENERATORS)
        model.total_power_generation_con = Constraint(model.ME_STREAMS, model.TIME,
                                                           rule=total_power_generation_rule)

        def _conversion_maximal_component_capacity_rule(model, c, me_in, t):
            # Limits conversion on capacity of conversion unit and defines conversions
            # Important: Capacity is always matched with input
            if (c, me_in) in self.main_tuples:
                return model.mass_energy_component_in_streams[c, me_in, t] <= model.nominal_cap[c] * model.max_p[c]
            else:
                return Constraint.Skip
        model._conversion_maximal_component_capacity_con = \
            Constraint(model.CONVERSION_COMPONENTS, model.ME_STREAMS, model.TIME,
                       rule=_conversion_maximal_component_capacity_rule)

        def _conversion_minimal_component_capacity_rule(model, c, me_in, t):
            # Limits conversion on capacity of conversion unit and defines conversions
            # Important: Capacity is always matched with input
            if c not in model.SHUT_DOWN_COMPONENTS:
                if (c, me_in) in self.main_tuples:
                    return model.mass_energy_component_in_streams[c, me_in, t] >= model.nominal_cap[c] * model.min_p[c]
                else:
                    return Constraint.Skip
            else:
                return Constraint.Skip
        model._conversion_minimal_component_capacity_con = \
            Constraint(model.CONVERSION_COMPONENTS, model.ME_STREAMS, model.TIME,
                       rule=_conversion_minimal_component_capacity_rule)

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
        model._ramp_up_con = Constraint(model.CONVERSION_COMPONENTS, model.ME_STREAMS,
                                             model.TIME, rule=_ramp_up_rule)

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
        model._ramp_down_con = Constraint(model.CONVERSION_COMPONENTS, model.ME_STREAMS,
                                               model.TIME, rule=_ramp_down_rule)

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
            model._correct_power_con = Constraint(model.SHUT_DOWN_COMPONENTS,
                                                       model.ME_STREAMS, model.TIME,
                                                       rule=_correct_power_rule)

        def _active_component_rule(model, c, me_in, t):
            # Set binary to 1 if component is active
            if (c, me_in) in self.main_tuples:
                return model.mass_energy_component_in_streams[c, me_in, t] \
                       - model.component_status[c, t] * model.M <= 0
            else:
                return Constraint.Skip
        model._active_component_con = Constraint(model.SHUT_DOWN_COMPONENTS,
                                                      model.ME_STREAMS, model.TIME,
                                                      rule=_active_component_rule)

        def _balance_switch_rule(model, c, t):
            # forbids simultaneous switch on and off
            return model.status_switch_off[c, t] + model.status_switch_on[c, t] <= 1
        model._balance_switch_con = Constraint(model.SHUT_DOWN_COMPONENTS, model.TIME,
                                                    rule=_balance_switch_rule)

        def _define_status_rule(model, c, t):
            # status is either 1 or 0 and can be changed with switch on (0 -> 1) or switch off (1 -> 0)
            if t > 0:
                return model.component_status[c, t] == model.component_status[c, t - 1] + \
                       model.status_switch_on[c, t] - model.status_switch_off[c, t]
            else:
                return Constraint.Skip
        model._define_status_con = Constraint(model.SHUT_DOWN_COMPONENTS, model.TIME,
                                                   rule=_define_status_rule)

        if False:
            def _define_machine_rule(model, c, t):
                # todo: delete
                return model.component_status[c, t] - model.component_correct_p[c, t] == model.component_status_1[c, t]
            model._define_machine_con = Constraint(model.SHUT_DOWN_COMPONENTS, model.TIME,
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
        model._deactivate_component_con = Constraint(model.SHUT_DOWN_COMPONENTS, model.TIME,
                                                          rule=_deactivate_component_rule)

        """ Capacity of scalable units """
        def capacity_binary_sum_rule(model, c):
            # For each component, only one capacity over all integer steps can be 1
            return sum(model.capacity_binary[c, i] for i in model.INTEGER_STEPS) <= 1
        model.capacity_binary_sum_con = Constraint(model.SCALABLE_COMPONENTS,
                                                        rule=capacity_binary_sum_rule)

        def capacity_binary_activation_rule(model, c, i):
            # Capacity binary will be 1 if the capacity of the integer step is higher than 0
            return model.capacity_binary[c, i] >= model.nominal_cap_pre[c, i] / 10000
        model.capacity_binary_activation_con = Constraint(model.SCALABLE_COMPONENTS, model.INTEGER_STEPS,
                                                               rule=capacity_binary_activation_rule)

        def set_lower_bound_rule(model, c, i):
            # capacity binary sets lower bound. Lower bound is not predefined as each capacity step can be 0
            return model.nominal_cap_pre[c, i] >= self.lower_bound_dict[c, i] * model.capacity_binary[c, i]
        model.set_lower_bound_con = Constraint(model.SCALABLE_COMPONENTS, model.INTEGER_STEPS,
                                                    rule=set_lower_bound_rule)

        def final_capacity_rule(model, c):
            # Final capacity of component is sum of capacity over all integer steps
            return model.nominal_cap[c] == sum(model.nominal_cap_pre[c, i] for i in model.INTEGER_STEPS)
        model.final_capacity_con = Constraint(model.SCALABLE_COMPONENTS, rule=final_capacity_rule)

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
            model.lower_bound_adherence_con = Constraint(model.SCALABLE_COMPONENTS,
                                                              model.INTEGER_STEPS,
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

        model.storage_balance_con = Constraint(model.ME_STREAMS, model.TIME,
                                                    rule=storage_balance_rule)

        def last_soc_rule(model, me):
            # Defines SOC in last to as no charging and discharging is possible
            return model.soc[me, max(model.TIME)] == model.initial_soc[me] * model.nominal_cap[me]

        model.last_soc_con = Constraint(model.STORAGES, rule=last_soc_rule)

        def soc_max_bound_rule(model, me, t):
            # Sets upper bound of SOC
            return model.soc[me, t] <= model.maximal_soc[me] * model.nominal_cap[me]

        model.soc_max = Constraint(model.STORAGES, model.TIME, rule=soc_max_bound_rule)

        def soc_min_bound_rule(model, me, t):
            # Sets lower bound of SOC
            return model.soc[me, t] >= model.minimal_soc[me] * model.nominal_cap[me]

        model.soc_min = Constraint(model.STORAGES, model.TIME, rule=soc_min_bound_rule)

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

        model.storage_charge_upper_bound_con = Constraint(model.ME_STREAMS, model.TIME,
                                                               rule=storage_charge_upper_bound_rule)

        def storage_discharge_upper_bound_rule(model, me, t):
            # Sets maximal out stream into storage based on set ratio
            if me in model.STORAGES:
                if t == model.TIME[-1]:
                    return model.mass_energy_storage_out_streams[me, t] == 0
                else:
                    return model.mass_energy_storage_out_streams[me, t] / model.discharging_efficiency[me] \
                           <= model.nominal_cap[me] / model.ratio_capacity_p[me]
            else:
                return model.mass_energy_storage_out_streams[
                           me, t] == 0  # Defines all streams of non storable streams

        model.storage_discharge_upper_bound_con = Constraint(model.ME_STREAMS, model.TIME,
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

        model.storage_limitation_to_component_con = Constraint(model.LIMITED_STORAGES,
                                                                    rule=storage_limitation_to_component_rule)

        """ STORAGE BINARY DECISIONS """

        def storage_binary_sum_rule(model, s, t):
            # Constraints simultaneous charging and discharging
            return model.storage_charge_binary[s, t] + model.storage_discharge_binary[s, t] <= 1

        model.storage_binary_sum_con = Constraint(model.STORAGES, model.TIME,
                                                       rule=storage_binary_sum_rule)

        def charge_binary_activation_rule(model, s, t):
            # Define charging binary -> if charged, binary = 1
            return model.mass_energy_storage_in_streams[s, t] - model.storage_charge_binary[s, t] * model.M <= 0

        model.charge_binary_activation_con = Constraint(model.STORAGES, model.TIME,
                                                             rule=charge_binary_activation_rule)

        def discharge_binary_activation_rule(model, s, t):
            # Define discharging binary -> if discharged, binary = 1
            return model.mass_energy_storage_out_streams[s, t] - model.storage_discharge_binary[
                s, t] * model.M <= 0

        model.discharge_binary_activation_con = Constraint(model.STORAGES, model.TIME,
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
        model.investment_con = Constraint(model.COMPONENTS, rule=_investment_rule)

        def _annuity_rule(model, c):
            # Calculates annuity for each component
            return model.annuity[c] == model.investment[c] * model.ANF[c]
        model.annuity_con = Constraint(model.COMPONENTS, rule=_annuity_rule)

        def _total_annuity_rule(model):
            # Sums total annuity over all components
            return model.total_annuity == sum(model.annuity[c] for c in model.COMPONENTS)
        model.total_annuity_con = Constraint(rule=_total_annuity_rule)

        def _maintenance_cost_rule(model, c):
            # Calculates maintenance cost for each component
            return model.maintenance_costs[c] == model.investment[c] * model.maintenance[c]
        model.maintenance_cost_con = Constraint(model.COMPONENTS, rule=_maintenance_cost_rule)

        def total_maintenance_cost_rule(model):
            # Sum maintenance costs over all components
            return model.total_maintenance_costs == sum(model.maintenance_costs[c] for c in model.COMPONENTS)
        model.total_maintenance_cost_con = Constraint(rule=total_maintenance_cost_rule)

        def taxes_and_insurance_cost_rule(model, c):
            # Calculate taxes and insurance
            if pm_object.get_applied_parameter_for_component('taxes_and_insurance', c):
                return model.taxes_and_insurance_costs[c] == model.investment[c] * model.taxes_and_insurance
            else:
                return model.taxes_and_insurance_costs[c] == 0
        model.taxes_and_insurance_cost_con = Constraint(model.COMPONENTS, rule=taxes_and_insurance_cost_rule)

        def total_taxes_and_insurance_cost_rule(model):
            # Calculate total taxes and insurance
            return model.total_taxes_and_insurance_costs == sum(model.taxes_and_insurance_costs[c] for c in model.COMPONENTS)
        model.total_taxes_and_insurance_cost_con = Constraint(rule=total_taxes_and_insurance_cost_rule)

        def overhead_costs_rule(model, c):
            # Calculate total overhead costs
            if pm_object.get_applied_parameter_for_component('overhead', c):
                return model.overhead_costs[c] == model.investment[c] * model.overhead
            else:
                return model.overhead_costs[c] == 0
        model.overhead_costs_con = Constraint(model.COMPONENTS, rule=overhead_costs_rule)

        def total_overhead_costs_rule(model):
            # Calculate total overhead costs
            return model.total_overhead_costs == sum(model.overhead_costs[c] for c in model.COMPONENTS)
        model.total_overhead_costs_con = Constraint(rule=total_overhead_costs_rule)

        def personnel_costs_rule(model, c):
            # Calculate total personal costs
            if pm_object.get_applied_parameter_for_component('personnel_costs', c):
                return model.personnel_costs[c] == model.investment[c] * model.personnel_cost
            else:
                return model.personnel_costs[c] == 0
        model.personnel_costs_con = Constraint(model.COMPONENTS, rule=personnel_costs_rule)

        def total_personnel_costs_rule(model):
            # Calculate total personal costs
            return model.total_personnel_costs == sum(model.personnel_costs[c] for c in model.COMPONENTS)
        model.total_personnel_costs_con = Constraint(rule=total_personnel_costs_rule)

        def working_capital_rule(model, c):
            # calculate total working capital
            if pm_object.get_applied_parameter_for_component('working_capital', c):
                return model.working_capital_costs[c] == (model.investment[c]
                                                          / (1 - model.working_capital)
                                                          * model.working_capital) * model.wacc
            else:
                return model.working_capital_costs[c] == 0
        model.working_capital_con = Constraint(model.COMPONENTS, rule=working_capital_rule)

        def total_working_capital_rule(model):
            # calculate total working capital
            return model.total_working_capital_costs == sum(model.working_capital_costs[c] for c in model.COMPONENTS)
        model.total_working_capital_con = Constraint(rule=total_working_capital_rule)

        def _purchase_costs_rule(model, me):
            # calculate purchase costs of each stream
            return model.purchase_costs[me] == sum(model.mass_energy_purchase_stream[me, t]
                                                   * model.purchase_price[me, t] for t in model.TIME)
        model._purchase_costs_con = Constraint(model.PURCHASABLE_STREAMS, rule=_purchase_costs_rule)

        def _total_purchase_costs_rule(model):
            # Sum purchase costs over all streams
            return model.total_purchase_costs == sum(model.purchase_costs[me] for me in model.PURCHASABLE_STREAMS)
        model.total_purchase_costs_rule = Constraint(rule=_total_purchase_costs_rule)

        def _revenue_rule(model, me):
            # Calculate revenue for each stream
            return model.revenue[me] == sum(model.mass_energy_sell_stream[me, t]
                                            * model.selling_price[me, t] for t in model.TIME)
        model.revenue_con = Constraint(model.SALEABLE_STREAMS, rule=_revenue_rule)

        def _total_revenue_rule(model):
            # sum revenue over all streams
            return model.total_revenue == sum(model.revenue[me] for me in model.SALEABLE_STREAMS)
        model._total_revenue_con = Constraint(rule=_total_revenue_rule)

        def power_lower_bound_ignoring_penalty_rule(model):
            # Penalize capacities lower than lower bound
            if False:
                return model.power_penalty == sum(-(model.component_status[c, t]
                                                   - model.component_correct_p[c, t] - 1) * model.M
                                                  for c in model.SHUT_DOWN_COMPONENTS
                                                  for t in model.TIME)
            else:
                return model.power_penalty == sum(model.wrong_power[c] * 1000000000
                                                  for c in model.SHUT_DOWN_COMPONENTS)
        model.capacity_lower_bound_ignoring_penalty_con = Constraint(
            rule=power_lower_bound_ignoring_penalty_rule)

        def wrong_power_rule(model, c):
            return model.wrong_power[c] * 10000000000 >= sum((model.component_status[c, t]
                                                              + model.component_correct_p[c, t] - 1)
                                                             for t in model.TIME)
        model.wrong_power_con = Constraint(model.SHUT_DOWN_COMPONENTS, rule=wrong_power_rule)

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
        model.obj = Objective(rule=objective_function, sense=minimize)

        return model

    def optimize(self, model, instance=None):

        opt = pyo.SolverFactory(self.solver, solver_io="python")
        if instance is None:
            instance = model.create_instance()
        opt.options["mipgap"] = 0.05
        if instance is None:
            instance = model.create_instance()
            results = opt.solve(instance, tee=True)
        else:
            results = opt.solve(instance, tee=True, warmstart=True)
        print(results)

        return instance

    def reset_information(self):
        self.conversion_tuples = []
        self.conversion_tuples_dict = {}
        self.main_tuples = []
        self.side_tuples = []
        self.main_out_streams = []
        self.input_tuples = []
        self.output_tuples = []

    def __init__(self, pm_object, path_data, solver):

        self.conversion_tuples = []
        self.conversion_tuples_dict = {}
        self.main_tuples = []
        self.side_tuples = []
        self.main_out_streams = []
        self.input_tuples = []
        self.output_tuples = []

        # ----------------------------------
        # Set up problem

        self.path_data = path_data
        self.solver = solver
        self.instance = None

        # Check if shutdown ability is available -> creates problems as many binaries will be created
        conv_components = pm_object.get_specific_components('final', 'conversion')
        shutdown_exists = False
        for c in conv_components:
            if c.get_shut_down_ability():
                shutdown_exists = True
                break

        if shutdown_exists:
            solved_feasible, self.model, self.instance, self.pm_object \
                = self.create_initial_solution(pm_object)
            if solved_feasible:
                self.instance = self.optimize(self.model, self.instance)
            else:
                self.pm_object = self.pre_adjustments(pm_object)
                model = self.initialize_problem(self.pm_object)
                model = self.post_adjustments(self.pm_object, model)
                self.model = self.attach_constraints(self.pm_object, model)
                self.instance = self.optimize(model)
        else:
            self.pm_object = self.pre_adjustments(pm_object)
            model = self.initialize_problem(self.pm_object)
            model = self.post_adjustments(self.pm_object, model)
            self.model = self.attach_constraints(self.pm_object, model)
            self.instance = self.optimize(model)

        # print(self.instance.pprint())
