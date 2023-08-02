import copy


class Component:

    def set_name(self, name):
        self.name = name

    def get_name(self):
        return self.name

    def set_capex(self, capex):
        if capex is not None:
            self.capex = float(capex)

    def get_capex(self):
        return self.capex

    def set_lifetime(self, lifetime):
        self.lifetime = float(lifetime)

    def get_lifetime(self):
        return self.lifetime

    def set_variable_OM(self, variable_om):
        self.variable_om = float(variable_om)

    def get_variable_OM(self):
        return self.variable_om

    def set_fixed_OM(self, maintenance):
        self.fixed_om = float(maintenance)

    def get_fixed_OM(self):
        return self.fixed_om

    def set_has_fixed_capacity(self, status):
        self.has_fixed_capacity = bool(status)

    def get_has_fixed_capacity(self):
        return self.has_fixed_capacity

    def set_fixed_capacity(self, fixed_capacity):
        self.fixed_capacity = float(fixed_capacity)

    def get_fixed_capacity(self):
        return self.fixed_capacity

    def set_final(self, status):
        self.final_unit = status

    def set_custom(self, status):
        self.custom_unit = status

    def is_final(self):
        return self.final_unit

    def is_custom(self):
        return self.custom_unit

    def get_component_type(self):
        return self.component_type

    def __copy__(self):
        return Component(name=self.name, final_unit=self.final_unit,
                         custom_unit=self.custom_unit, capex=self.capex, lifetime=self.lifetime,
                         fixed_om=self.fixed_om, variable_om=self.variable_om,
                         has_fixed_capacity=self.has_fixed_capacity, fixed_capacity=self.fixed_capacity)

    def __init__(self, name, lifetime, fixed_om, variable_om, capex=None,
                 final_unit=False, custom_unit=False,
                 has_fixed_capacity=False, fixed_capacity=0.):

        """
        Defines basic component class

        :param name: [string] - abbreviation of component
        :param lifetime: [int] - lifetime of component
        :param fixed_om: [float] - fixed operation and maintenance
        :param variable_om: [float] - variable operation and maintenance
        :param capex: [float] - Capex
        :param final_unit: [boolean] - if part of the final optimization problem
        :param custom_unit: [boolean] - if not default component
        """
        self.name = str(name)
        self.component_type = None

        self.final_unit = bool(final_unit)
        self.custom_unit = bool(custom_unit)

        self.capex = float(capex)

        self.lifetime = int(lifetime)
        self.fixed_om = float(fixed_om)
        self.variable_om = float(variable_om)

        self.has_fixed_capacity = bool(has_fixed_capacity)
        self.fixed_capacity = float(fixed_capacity)


class ConversionComponent(Component):

    def set_scalable(self, status):
        self.scalable = status

    def is_scalable(self):
        return self.scalable

    def set_base_investment(self, base_investment):
        if base_investment is not None:
            self.base_investment = float(base_investment)

    def get_base_investment(self):
        return self.base_investment

    def set_base_capacity(self, base_capacity):
        if base_capacity is not None:
            self.base_capacity = float(base_capacity)

    def get_base_capacity(self):
        return self.base_capacity

    def set_economies_of_scale(self, eoc):
        if eoc is not None:
            self.economies_of_scale = float(eoc)

    def get_economies_of_scale(self):
        return self.economies_of_scale

    def set_max_capacity_economies_of_scale(self, max_capacity_economies_of_scale):
        if max_capacity_economies_of_scale is not None:
            self.max_capacity_economies_of_scale = float(max_capacity_economies_of_scale)

    def get_max_capacity_economies_of_scale(self):
        return self.max_capacity_economies_of_scale

    def set_number_parallel_units(self, number_units):
        self.number_parallel_units = int(number_units)

    def get_number_parallel_units(self):
        return self.number_parallel_units

    def set_ramp_down(self, ramp_down):
        self.ramp_down = float(ramp_down)

    def get_ramp_down(self):
        return self.ramp_down

    def set_ramp_up(self, ramp_up):
        self.ramp_up = float(ramp_up)

    def get_ramp_up(self):
        return self.ramp_up

    def set_shut_down_ability(self, shut_down_ability):
        self.shut_down_ability = bool(shut_down_ability)

    def get_shut_down_ability(self):
        return self.shut_down_ability

    def set_start_up_time(self, start_up_time):
        self.start_up_time = int(start_up_time)

    def get_start_up_time(self):
        return self.start_up_time

    def set_start_up_costs(self, start_up_costs):
        self.start_up_costs = start_up_costs

    def get_start_up_costs(self):
        return self.start_up_costs

    def set_hot_standby_ability(self, hot_standby_ability):
        self.hot_standby_ability = bool(hot_standby_ability)

    def get_hot_standby_ability(self):
        return self.hot_standby_ability

    def set_hot_standby_demand(self, commodity, demand=None):
        if demand is not None:
            hot_standby_demand = {commodity: demand}
            self.hot_standby_demand.clear()
            self.hot_standby_demand = hot_standby_demand
        else:
            self.hot_standby_demand = commodity

    def get_hot_standby_demand(self):
        return self.hot_standby_demand

    def set_hot_standby_startup_time(self, time):
        self.hot_standby_startup_time = int(time)

    def get_hot_standby_startup_time(self):
        return self.hot_standby_startup_time

    def set_inputs(self, inputs):
        self.inputs = inputs

    def get_inputs(self):
        return self.inputs

    def add_input(self, input_commodity, coefficient):
        self.inputs.update({input_commodity: float(coefficient)})
        self.add_commodity(input_commodity)

    def remove_input(self, input_commodity):
        self.inputs.pop(input_commodity)
        self.remove_commodity(input_commodity)

    def set_main_input(self, input_commodity):
        self.main_input = input_commodity

    def get_main_input(self):
        return self.main_input

    def set_outputs(self, outputs):
        self.outputs = outputs

    def get_outputs(self):
        return self.outputs

    def add_output(self, output_commodity, coefficient):
        self.outputs.update({output_commodity: float(coefficient)})
        self.add_commodity(output_commodity)

    def remove_output(self, output_commodity):
        self.outputs.pop(output_commodity)
        self.remove_commodity(output_commodity)

    def set_main_output(self, output_commodity):
        self.main_output = output_commodity

    def get_main_output(self):
        return self.main_output

    def set_capex_basis(self, basis):
        self.capex_basis = basis

    def get_capex_basis(self):
        return self.capex_basis

    def add_commodity(self, commodity):
        if commodity not in self.commodities:
            self.commodities.append(commodity)

    def remove_commodity(self, commodity):
        if commodity in self.commodities:
            self.commodities.remove(commodity)

    def get_commodities(self):
        return self.commodities

    def set_min_p(self, min_p):
        self.min_p = float(min_p)

    def get_min_p(self):
        return self.min_p

    def set_max_p(self, max_p):
        self.max_p = float(max_p)

    def get_max_p(self):
        return self.max_p

    def __copy__(self, name=None):

        if name is None:
            name = self.name

        # deepcopy mutable objects
        inputs = copy.deepcopy(self.inputs)
        outputs = copy.deepcopy(self.outputs)
        commodities = copy.deepcopy(self.commodities)
        hot_standby_demand = copy.deepcopy(self.hot_standby_demand)

        return ConversionComponent(name=name, lifetime=self.lifetime,
                                   fixed_om=self.fixed_om, variable_om=self.variable_om, capex=self.capex,
                                   capex_basis=self.capex_basis, scalable=self.scalable,
                                   base_investment=self.base_investment, base_capacity=self.base_capacity,
                                   economies_of_scale=self.economies_of_scale,
                                   max_capacity_economies_of_scale=self.max_capacity_economies_of_scale,
                                   ramp_down=self.ramp_down, ramp_up=self.ramp_up,
                                   shut_down_ability=self.shut_down_ability,
                                   start_up_time=self.start_up_time, hot_standby_ability=self.hot_standby_ability,
                                   hot_standby_demand=hot_standby_demand,
                                   hot_standby_startup_time=self.hot_standby_startup_time,
                                   number_parallel_units=self.number_parallel_units,
                                   min_p=self.min_p, max_p=self.max_p, inputs=inputs, outputs=outputs,
                                   main_input=self.main_input, main_output=self.main_output, commodities=commodities,
                                   has_fixed_capacity=self.has_fixed_capacity, fixed_capacity=self.fixed_capacity,
                                   final_unit=self.final_unit)

    def __init__(self, name, lifetime=1, fixed_om=0., variable_om=0., capex=0.,
                 capex_basis='input', scalable=False, base_investment=0., base_capacity=0., economies_of_scale=0.,
                 max_capacity_economies_of_scale=0., ramp_down=1., ramp_up=1.,
                 shut_down_ability=False, start_up_time=0., start_up_costs=0,
                 hot_standby_ability=False, hot_standby_demand=None, hot_standby_startup_time=0,
                 number_parallel_units=1,
                 min_p=0., max_p=1., inputs=None, outputs=None, main_input=None, main_output=None, commodities=None,
                 has_fixed_capacity=False, fixed_capacity=0.1,
                 final_unit=False, custom_unit=False):

        """
        Class of conversion units
        :param name: [string] - Abbreviation of unit
        :param lifetime: [int] - lifetime of unit
        :param fixed_om: [float] - fixed operation and maintenance
        :param variable_om: [float] - variable operation and maintenance
        :param capex: [float] - CAPEX of component
        :param capex_basis: [str] - Decide if input or output sets basis of capex
        :param scalable: [boolean] - Boolean if scalable unit
        :param base_investment: [float] - If scalable, base investment of unit
        :param base_capacity: [float] - If scalable, base capacity of unit
        :param economies_of_scale: [float] - Economies of scale of investment and capacity
        :param max_capacity_economies_of_scale: [float] - Maximal capacity, where scaling factor is still applied. Above, constant investment follows
        :param ramp_down: [float] - Ramp down between time steps in % / h
        :param ramp_up: [float] - Ramp up between time steps in % / h
        :param shut_down_ability: [boolean] - Boolean if component can be turned off
        :param start_up_time: [int] - Time to start up component
        :param number_parallel_units: [int] - Number parallel components with same parameters
        :param inputs: [Dict] - inputs of component
        :param outputs: [Dict] - outputs of component
        :param main_input: [str] - main input of component
        :param main_output: [str] - main output of component
        :param min_p: [float] - Minimal power of the unit when operating
        :param max_p: [float] - Maximal power of the unit when operating
        :param commodities: [list] - Commodities of the unit
        :param final_unit: [boolean] - if part of the final optimization problem
        :param custom_unit: [boolean] - if unit is custom
        """

        super().__init__(name, lifetime, fixed_om, variable_om, capex, final_unit, custom_unit,
                         has_fixed_capacity, fixed_capacity)

        self.component_type = 'conversion'
        self.scalable = bool(scalable)

        if inputs is None:
            self.inputs = {}
            self.outputs = {}
            self.main_input = str
            self.main_output = str
        else:
            self.inputs = inputs
            self.outputs = outputs
            self.main_input = main_input
            self.main_output = main_output

        if commodities is None:
            self.commodities = []
        else:
            self.commodities = commodities

        self.min_p = float(min_p)
        self.max_p = float(max_p)
        self.ramp_down = float(ramp_down)
        self.ramp_up = float(ramp_up)

        self.shut_down_ability = bool(shut_down_ability)
        self.start_up_time = int(start_up_time)
        self.start_up_costs = float(start_up_costs)

        self.hot_standby_ability = bool(hot_standby_ability)
        if hot_standby_demand is None:
            self.hot_standby_demand = {}
        else:
            self.hot_standby_demand = hot_standby_demand
        self.hot_standby_startup_time = int(hot_standby_startup_time)

        self.capex_basis = capex_basis
        self.base_investment = float(base_investment)
        self.base_capacity = float(base_capacity)
        self.economies_of_scale = float(economies_of_scale)
        self.max_capacity_economies_of_scale = float(max_capacity_economies_of_scale)

        self.number_parallel_units = int(number_parallel_units)


class StorageComponent(Component):

    def set_charging_efficiency(self, charging_efficiency_component):
        self.charging_efficiency = float(charging_efficiency_component)

    def get_charging_efficiency(self):
        return self.charging_efficiency

    def set_discharging_efficiency(self, discharging_efficiency_component):
        self.discharging_efficiency = float(discharging_efficiency_component)

    def get_discharging_efficiency(self):
        return self.discharging_efficiency

    def set_leakage(self, leakage):
        self.leakage = float(leakage)

    def get_leakage(self):
        return self.leakage

    def set_ratio_capacity_p(self, ratio_capacity_p):
        self.ratio_capacity_p = float(ratio_capacity_p)

    def get_ratio_capacity_p(self):
        return self.ratio_capacity_p

    def set_max_soc(self, max_soc_component):
        self.max_soc = float(max_soc_component)

    def get_max_soc(self):
        return self.max_soc

    def set_min_soc(self, min_soc_component):
        self.min_soc = float(min_soc_component)

    def get_min_soc(self):
        return self.min_soc

    def set_initial_soc(self, initial_soc_component):
        self.initial_soc = float(initial_soc_component)

    def get_initial_soc(self):
        return self.initial_soc

    def __copy__(self):
        return StorageComponent(name=self.name, lifetime=self.lifetime,
                                fixed_om=self.fixed_om, variable_om=self.variable_om, capex=self.capex,
                                charging_efficiency=self.charging_efficiency,
                                discharging_efficiency=self.discharging_efficiency,
                                min_soc=self.min_soc, max_soc=self.max_soc, initial_soc=self.initial_soc,
                                leakage=self.leakage, ratio_capacity_p=self.ratio_capacity_p,
                                has_fixed_capacity=self.has_fixed_capacity, fixed_capacity=self.fixed_capacity,
                                final_unit=self.final_unit, custom_unit=self.custom_unit)

    def __init__(self, name, lifetime=1, fixed_om=0., variable_om=0., capex=0.,
                 charging_efficiency=1., discharging_efficiency=1., min_soc=0., max_soc=1.,
                 initial_soc=0.5,
                 leakage=0., ratio_capacity_p=1., has_fixed_capacity=False, fixed_capacity=0.,
                 final_unit=False, custom_unit=False):

        """
        Class of Storage component

        :param name: [string] - Abbreviation of unit
        :param lifetime: [int] - lifetime of unit
        :param fixed_om: [float] - fixed operation and maintenance
        :param variable_om: [float] - variable operation and maintenance
        :param capex: [float] - CAPEX of component
        :param charging_efficiency: [float] - Charging efficiency when charging storage
        :param discharging_efficiency: [float] - Charging efficiency when discharging storage
        :param min_soc: [float] - minimal SOC of storage
        :param max_soc: [float] - maximal SOC of storage
        :param initial_soc: [float] - Initial SOC of storage
        :param leakage: [float] - Leakage over time #todo: delete or implement
        :param ratio_capacity_p: [float] - Ratio between capacity of storage and charging or discharging power
        :param final_unit: [boolean] - if part of the final optimization problem
        :param custom_unit: [boolean] - if not default component
        """

        super().__init__(name, lifetime, fixed_om, variable_om, capex,
                         final_unit, custom_unit, has_fixed_capacity, fixed_capacity)

        self.component_type = 'storage'

        self.charging_efficiency = float(charging_efficiency)
        self.discharging_efficiency = float(discharging_efficiency)
        self.leakage = float(leakage)
        self.ratio_capacity_p = float(ratio_capacity_p)

        self.min_soc = float(min_soc)
        self.max_soc = float(max_soc)
        self.initial_soc = float(initial_soc)


class GenerationComponent(Component):

    def set_generated_commodity(self, generated_commodity):
        self.generated_commodity = generated_commodity

    def get_generated_commodity(self):
        return self.generated_commodity

    def set_curtailment_possible(self, status):
        self.curtailment_possible = bool(status)

    def get_curtailment_possible(self):
        return self.curtailment_possible

    def set_uses_ppa(self, uses_ppa):
        self.uses_ppa = uses_ppa

    def get_uses_ppa(self):
        return self.uses_ppa

    def set_ppa_price(self, ppa_price):
        self.ppa_price = ppa_price

    def get_ppa_price(self):
        return self.ppa_price

    def set_subsidies(self, subsidies):
        self.subsidies = subsidies

    def get_subsidies(self):
        return self.subsidies

    def __copy__(self):
        return GenerationComponent(name=self.name, lifetime=self.lifetime,
                                   fixed_om=self.fixed_om, variable_om=self.variable_om, capex=self.capex,
                                   generated_commodity=self.generated_commodity,
                                   curtailment_possible=self.curtailment_possible,
                                   has_fixed_capacity=self.has_fixed_capacity, fixed_capacity=self.fixed_capacity,
                                   uses_ppa=self.uses_ppa, ppa_price=self.ppa_price, subsidies=self.subsidies,
                                   final_unit=self.final_unit, custom_unit=self.custom_unit)

    def __init__(self, name, lifetime=1, fixed_om=0., variable_om=0., capex=0.,
                 generated_commodity='Electricity',
                 curtailment_possible=True,
                 uses_ppa=False, ppa_price=0., subsidies=0.,
                 has_fixed_capacity=False, fixed_capacity=0.,
                 final_unit=False, custom_unit=False):

        """
        Class of Generator component

        :param name: [string] - Abbreviation of unit
        :param lifetime: [int] - lifetime of unit
        :param fixed_om: [float] - fixed operation and maintenance
        :param variable_om: [float] - variable operation and maintenance
        :param capex: [float] - CAPEX of unit
        :param generated_commodity: [string] - Stream, which is generated by generator
        :param final_unit: [boolean] - if part of the final optimization problem
        :param custom_unit: [boolean] - if not default component
        """
        super().__init__(name, lifetime, fixed_om, variable_om, capex,
                         final_unit, custom_unit, has_fixed_capacity, fixed_capacity)

        self.component_type = 'generator'

        self.generated_commodity = generated_commodity
        self.curtailment_possible = bool(curtailment_possible)
        self.has_fixed_capacity = bool(has_fixed_capacity)
        self.fixed_capacity = float(fixed_capacity)
        self.uses_ppa = bool(uses_ppa)
        self.ppa_price = float(ppa_price)
        self.subsidies = float(subsidies)
