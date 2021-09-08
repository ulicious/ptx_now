import copy


class Component:

    def set_nice_name(self, nice_name):
        self.nice_name = nice_name

    def get_nice_name(self):
        return self.nice_name

    def set_name(self, name):
        self.name = name

    def get_name(self):
        return self.name

    def set_capex(self, capex):
        if capex is not None:
            self.capex = float(capex)

    def get_capex(self):
        return self.capex

    def set_capex_unit(self, capex_unit):
        self.capex_unit = capex_unit

    def get_capex_unit(self):
        return self.capex_unit

    def set_lifetime(self, lifetime):
        self.lifetime = float(lifetime)

    def get_lifetime(self):
        return self.lifetime

    def set_maintenance(self, maintenance):
        self.maintenance = float(maintenance)

    def get_maintenance(self):
        return self.maintenance

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
        return Component(name=self.name, nice_name=self.nice_name, final_unit=self.final_unit,
                         custom_unit=self.custom_unit, capex=self.capex,
                         capex_unit=self.capex_unit, lifetime=self.lifetime, maintenance=self.maintenance)

    def __init__(self, name, nice_name, lifetime, maintenance, capex_unit, capex=None,
                 final_unit=False, custom_unit=False):

        """
        Defines basic component class

        :param name: [string] - abbreviation of component
        :param nice_name: [string] - Nice name of component
        :param lifetime: [int] - lifetime of component
        :param maintenance: [float] - Maintenance of component
        :param capex_unit: [string] - Unit of CAPEX
        :param capex: [float] - Capex
        :param final_unit: [boolean] - if part of the final optimization problem
        :param custom_unit: [boolean] - if not default component
        """
        self.name = name
        self.nice_name = nice_name
        self.component_type = None

        self.final_unit = bool(final_unit)
        self.custom_unit = bool(custom_unit)

        self.capex = capex
        self.capex_unit = capex_unit

        self.lifetime = lifetime
        self.maintenance = maintenance


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

    def set_hot_standby_ability(self, hot_standby_ability):
        self.hot_standby_ability = bool(hot_standby_ability)

    def get_hot_standby_ability(self):
        return self.hot_standby_ability

    def set_hot_standby_demand(self, stream, demand):
        self.hot_standby_demand.clear()  # todo: Check if only one input?
        self.hot_standby_demand[stream] = float(demand)

    def get_hot_standby_demand(self):
        return self.hot_standby_demand

    def set_hot_standby_startup_time(self, time):
        self.hot_standby_startup_time = int(time)

    def get_hot_standby_startup_time(self):
        return self.hot_standby_startup_time

    def get_inputs(self):
        return self.inputs

    def add_input(self, input_stream, coefficient):
        self.inputs.update({input_stream: float(coefficient)})
        self.add_stream(input_stream)

    def remove_input(self, input_stream):
        self.inputs.pop(input_stream)
        self.remove_stream(input_stream)

    def set_main_input(self, input_stream):
        self.main_input = input_stream

    def get_main_input(self):
        return self.main_input

    def get_outputs(self):
        return self.outputs

    def add_output(self, output_stream, coefficient):
        self.outputs.update({output_stream: float(coefficient)})
        self.add_stream(output_stream)

    def remove_output(self, output_stream):
        self.outputs.pop(output_stream)
        self.remove_stream(output_stream)

    def set_main_output(self, output_stream):
        self.main_output = output_stream

    def get_main_output(self):
        return self.main_output

    def set_capex_basis(self, basis):
        self.capex_basis = basis

    def get_capex_basis(self):
        return self.capex_basis

    def add_stream(self, stream):
        if stream not in self.streams:
            self.streams.append(stream)

    def remove_stream(self, stream):
        if stream in self.streams:
            self.streams.remove(stream)

    def get_streams(self):
        return self.streams

    def set_min_p(self, min_p):
        self.min_p = float(min_p)

    def get_min_p(self):
        return self.min_p

    def set_max_p(self, max_p):
        self.max_p = float(max_p)

    def get_max_p(self):
        return self.max_p

    def __copy__(self, name=None, nice_name=None):

        if name is None:
            name = self.name
        if nice_name is None:
            nice_name = self.nice_name

        # deepcopy mutable objects
        inputs = copy.deepcopy(self.inputs)
        outputs = copy.deepcopy(self.outputs)
        streams = copy.deepcopy(self.streams)
        hot_standby_demand = copy.deepcopy(self.hot_standby_demand)

        return ConversionComponent(name=name, nice_name=nice_name, lifetime=self.lifetime,
                                   maintenance=self.maintenance, capex=self.capex, capex_unit=self.capex_unit,
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
                                   main_input=self.main_input, main_output=self.main_output, streams=streams,
                                   final_unit=self.final_unit)

    def __init__(self, name, nice_name, lifetime=0., maintenance=0., capex=0., capex_unit='€/MWh Electricity',
                 capex_basis='input', scalable=False, base_investment=0., base_capacity=0., economies_of_scale=0.,
                 max_capacity_economies_of_scale=0., ramp_down=1., ramp_up=1., shut_down_ability=False,
                 start_up_time=0., hot_standby_ability=False, hot_standby_demand=None, hot_standby_startup_time=0,
                 number_parallel_units=1,
                 min_p=0., max_p=1., inputs=None, outputs=None, main_input=None, main_output=None, streams=None,
                 final_unit=False, custom_unit=False):

        """
        Class of conversion units
        :param name: [string] - Abbreviation of unit
        :param nice_name: [string] - Nice name of unit
        :param lifetime: [int] - lifetime of unit
        :param maintenance: [float] - maintenance of unit in % of investment
        :param capex: [float] - CAPEX of component
        :param capex_unit: [string] - Unit of capex
        :param capex_basis: [str] - Decide if input or output sets basis of capex
        :param scalable: [boolean] - Boolean if scalable unit
        :param base_investment: [float] - If scalable, base investment of unit
        :param base_capacity: [float] - If scalable, base capacity of unit
        :param economies_of_scale: [float] - Economies of scale of investment and capacity
        :param max_capacity_economies_of_scale: [float] - Maximal capacity, where scaling factor is still applied. Above, constant investment follows
        :param ramp_down: [float] - Ramp down between time steps in % / h
        :param ramp_up: [float] - Ramp up between time steps in % / h
        :param shut_down_ability: [boolean] - Boolean if component can be turned off
        :param shut_down_time: [int] - Time to shut down component
        :param start_up_time: [int] - Time to start up component
        :param number_parallel_units: [int] - Number parallel components with same parameters
        :param inputs: [Dict] - inputs of component
        :param outputs: [Dict] - outputs of component
        :param main_input: [str] - main input of component
        :param main_output: [str] - main output of component
        :param min_p: [float] - Minimal power of the unit when operating
        :param max_p: [float] - Maximal power of the unit when operating
        :param streams: [list] - Streams of the unit
        :param final_unit: [boolean] - if part of the final optimization problem
        :param custom_unit: [boolean] - if unit is custom
        """

        super().__init__(name, nice_name, lifetime, maintenance, capex_unit, capex, final_unit, custom_unit)

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

        if streams is None:
            self.streams = []
        else:
            self.streams = streams

        self.min_p = min_p
        self.max_p = max_p
        self.ramp_down = ramp_down
        self.ramp_up = ramp_up
        self.shut_down_ability = shut_down_ability
        self.start_up_time = int(start_up_time)
        self.hot_standby_ability = hot_standby_ability
        if hot_standby_demand is None:
            self.hot_standby_demand = {}
        else:
            self.hot_standby_demand = hot_standby_demand
        self.hot_standby_startup_time = int(hot_standby_startup_time)

        self.capex = capex
        self.capex_basis = capex_basis
        self.base_investment = base_investment
        self.base_capacity = base_capacity
        self.economies_of_scale = economies_of_scale
        self.max_capacity_economies_of_scale = max_capacity_economies_of_scale

        self.number_parallel_units = number_parallel_units


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

    def set_limitation(self, status):
        self.limited_storage = status

    def is_limited(self):
        return self.limited_storage

    def set_storage_limiting_component(self, component):
        self.storage_limiting_component = component

    def get_storage_limiting_component(self):
        return self.storage_limiting_component

    def set_storage_limiting_component_ratio(self, storage_limiting_component_ratio):
        self.storage_limiting_component_ratio = float(storage_limiting_component_ratio)

    def get_storage_limiting_component_ratio(self):
        return self.storage_limiting_component_ratio

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
        return StorageComponent(name=self.name, nice_name=self.nice_name, lifetime=self.lifetime,
                                maintenance=self.maintenance, capex_unit=self.capex_unit, capex=self.capex,
                                charging_efficiency=self.charging_efficiency,
                                discharging_efficiency=self.discharging_efficiency,
                                min_soc=self.min_soc, max_soc=self.max_soc, initial_soc=self.initial_soc,
                                leakage=self.leakage, ratio_capacity_p=self.ratio_capacity_p,
                                limited_storage=self.limited_storage,
                                storage_limiting_component=self.storage_limiting_component,
                                storage_limiting_component_ratio=self.storage_limiting_component_ratio,
                                final_unit=self.final_unit, custom_unit=self.custom_unit)

    def __init__(self, name, nice_name, lifetime=0., maintenance=0., capex_unit='€/MWh', capex=0.,
                 charging_efficiency=1., discharging_efficiency=1., min_soc=0., max_soc=1.,
                 initial_soc=0.5, leakage=0., ratio_capacity_p=1.,
                 limited_storage=False, storage_limiting_component=None, storage_limiting_component_ratio=None,
                 final_unit=False, custom_unit=False):

        """
        Class of Storage component

        :param name: [string] - Abbreviation of unit
        :param nice_name: [string] - Nice name of unit
        :param lifetime: [int] - lifetime of unit
        :param maintenance: [float] - maintenance of unit in % of investment
        :param capex: [float] - CAPEX of component
        :param capex_unit:[string] - Unit of capex
        :param charging_efficiency: [float] - Charging efficiency when charging storage
        :param discharging_efficiency: [float] - Charging efficiency when discharging storage
        :param min_soc: [float] - minimal SOC of storage
        :param max_soc: [float] - maximal SOC of storage
        :param initial_soc: [float] - Initial SOC of storage
        :param leakage: [float] - Leakage over time #todo: delete or implement
        :param ratio_capacity_p: [float] - Ratio between capacity of storage and charging or discharging power
        :param limited_storage: [boolean] - Boolean, if storage is limited by certain component
        :param storage_limiting_component: [string] - Component, which limits storage
        :param storage_limiting_component_ratio: [float] - Ratio between limiting component capacity and storage capacity
        :param final_unit: [boolean] - if part of the final optimization problem
        :param custom_unit: [boolean] - if not default component
        """

        super().__init__(name, nice_name, lifetime, maintenance, capex_unit, capex,
                         final_unit, custom_unit)

        self.component_type = 'storage'

        self.charging_efficiency = float(charging_efficiency)
        self.discharging_efficiency = float(discharging_efficiency)
        self.leakage = float(leakage)
        self.ratio_capacity_p = float(ratio_capacity_p)

        self.limited_storage = limited_storage
        if limited_storage:
            self.storage_limiting_component = storage_limiting_component
            self.storage_limiting_component_ratio = float(storage_limiting_component_ratio)
        else:
            self.storage_limiting_component = None
            self.storage_limiting_component_ratio = 0.

        self.min_soc = float(min_soc)
        self.max_soc = float(max_soc)
        self.initial_soc = float(initial_soc)


class GenerationComponent(Component):

    def set_generated_stream(self, generated_stream):
        self.generated_stream = generated_stream

    def get_generated_stream(self):
        return self.generated_stream

    def set_generation_data(self, generation_data):
        self.generation_data = generation_data

    def get_generation_data(self):
        return self.generation_data

    def __copy__(self):
        return GenerationComponent(name=self.name, nice_name=self.nice_name, lifetime=self.lifetime,
                                   maintenance=self.maintenance, capex_unit=self.capex_unit, capex=self.capex,
                                   generation_data=self.generation_data, generated_stream=self.generated_stream,
                                   generation_profile=self.generation_profile,
                                   final_unit=self.final_unit, custom_unit=self.custom_unit)

    def __init__(self, name, nice_name, lifetime=0., maintenance=0., capex_unit='€/MW', capex=0.,
                 generation_data=None, generated_stream='electricity', generation_profile=None,
                 final_unit=False, custom_unit=False):

        """
        Class of Generator component

        :param name: [string] - Abbreviation of unit
        :param nice_name: [string] -  Nice name of unit
        :param lifetime: [int] - lifetime of unit
        :param maintenance: [float] - maintenance of unit in % of investment
        :param capex: [float] - CAPEX of unit
        :param capex_unit: [string] -  Unit of capex
        :param generation_data: [string] -  Path to csv file which contains normalized capacity factor
        :param generated_stream: [string] - Stream, which is generated by generator
        :param generation_profile: [list] - contains time series of normalized capacity factor
        :param final_unit: [boolean] - if part of the final optimization problem
        :param custom_unit: [boolean] - if not default component
        """
        super().__init__(name, nice_name, lifetime, maintenance, capex_unit, capex,
                         final_unit, custom_unit)

        self.component_type = 'generator'

        self.generated_stream = generated_stream
        self.generation_data = generation_data
        self.generation_profile = generation_profile