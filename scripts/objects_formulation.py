import pandas as pd
from prepare_data import load_data, calculate_investment
from _helper_optimization import create_conversion_factor_matrix

idx = pd.IndexSlice


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

    def set_default(self, status):
        self.default_unit = status

    def set_final(self, status):
        self.final_unit = status

    def set_custom(self, status):
        self.custom_unit = status

    def is_default(self):
        return self.default_unit

    def is_final(self):
        return self.final_unit

    def is_custom(self):
        return self.custom_unit

    def get_component_type(self):
        return self.component_type

    def __copy__(self):
        return Component(name=self.name, nice_name=self.nice_name, final_unit=self.final_unit,
                         default_unit=self.default_unit, custom_unit=self.custom_unit, capex=self.capex,
                         capex_unit=self.capex_unit, lifetime=self.lifetime, maintenance=self.maintenance)

    def __init__(self, name, nice_name, lifetime, maintenance, capex_unit, capex=None,
                 final_unit=False, default_unit=False, custom_unit=False):

        """
        Defines basic component class

        :param name: [string] - abbreviation of component
        :param nice_name: [string] - Nice name of component
        :param lifetime: [int] - lifetime of component
        :param maintenance: [float] - Maintenance of component
        :param capex_unit: [string] - Unit of CAPEX
        :param capex: [float] - Capex
        :param final_unit: [boolean] - if part of the final optimization problem
        :param default_unit: [boolean] - if default component #todo: delete
        :param custom_unit: [boolean] - if not default component #todo: delete
        """
        self.name = name
        self.nice_name = nice_name
        self.component_type = None

        self.final_unit = bool(final_unit)
        self.default_unit = bool(default_unit)
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
        self.shut_down_ability = shut_down_ability

    def get_shut_down_ability(self):
        return self.shut_down_ability

    def set_shut_down_time(self, shut_down_time):
        self.shut_down_time = int(shut_down_time)

    def get_shut_down_time(self):
        return self.shut_down_time

    def set_start_up_time(self, start_up_time):
        self.start_up_time = int(start_up_time)

    def get_start_up_time(self):
        return self.start_up_time

    def set_main_conversion(self, input_me, output_me, coefficient):

        # Check if stream is attached in another way than the deleted conversion. If not, delete stream from component
        if self.main_conversion is not None:
            if not self.main_conversion.empty:
                if (input_me not in self.main_conversion['input_me']) \
                        | (input_me not in self.main_conversion['output_me']):
                    if self.side_conversions.empty:
                        self.remove_stream(input_me)
                    else:
                        if (input_me not in self.side_conversions['input_me']) | (
                                input_me not in self.side_conversions['output_me']):
                            self.remove_stream(input_me)

                if (output_me not in self.main_conversion['input_me']) \
                        | (output_me not in self.main_conversion['output_me']):
                    if self.side_conversions.empty:
                        self.remove_stream(output_me)
                    else:
                        if (output_me not in self.side_conversions['input_me']) | (
                                output_me not in self.side_conversions['output_me']):
                            self.remove_stream(output_me)

        stream = {'input_me': input_me,
                  'output_me': output_me,
                  'coefficient': float(coefficient)}
        self.main_conversion = pd.Series(stream)

        self.add_stream(input_me)
        self.add_stream(output_me)

    def get_main_conversion(self):
        return self.main_conversion

    def add_side_conversion(self, input_me, output_me, coefficient):

        if self.side_conversions is None:
            self.side_conversions = pd.DataFrame()
            stream = {'input_me': input_me,
                      'output_me': output_me,
                      'coefficient': float(coefficient)}
            self.side_conversions = self.side_conversions.append(stream, ignore_index=True)
        else:
            if self.side_conversions.empty:
                stream = {'input_me': input_me,
                          'output_me': output_me,
                          'coefficient': float(coefficient)}
                self.side_conversions = self.side_conversions.append(stream, ignore_index=True)

            else:
                index = self.side_conversions[(self.side_conversions['input_me'] == input_me)
                                              & (self.side_conversions['output_me'] == output_me)].index

                if len(index) == 1:
                    self.side_conversions.loc[index, 'coefficient'] = coefficient

                else:
                    stream = {'input_me': input_me,
                              'output_me': output_me,
                              'coefficient': float(coefficient)}
                    self.side_conversions = self.side_conversions.append(stream, ignore_index=True)

        self.add_stream(input_me)
        self.add_stream(output_me)

    def remove_side_conversion(self, in_stream, out_stream):
        index = self.side_conversions[(self.side_conversions['input_me'] == in_stream)
                                      & (self.side_conversions['output_me'] == out_stream)].index
        self.side_conversions.drop(index, inplace=True)

        # Check if stream is attached in another way than the deleted conversion. If not, delete stream from component
        if ((out_stream not in self.main_conversion['input_me']) | (out_stream not in self.main_conversion['output_me'])
                | (out_stream not in self.side_conversions['input_me']) | (
                        out_stream not in self.side_conversions['output_me'])):
            self.remove_stream(out_stream)

        if ((in_stream not in self.main_conversion['input_me']) | (in_stream not in self.main_conversion['output_me'])
                | (in_stream not in self.side_conversions['input_me']) | (
                        in_stream not in self.side_conversions['output_me'])):
            self.remove_stream(in_stream)

    def get_side_conversions(self):
        return self.side_conversions

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

        return ConversionComponent(name=name, nice_name=nice_name, lifetime=self.lifetime,
                                   maintenance=self.maintenance, capex=self.capex, capex_unit=self.capex_unit,
                                   scalable=self.scalable, base_investment=self.base_investment,
                                   base_capacity=self.base_capacity, economies_of_scale=self.economies_of_scale,
                                   max_capacity_economies_of_scale=self.max_capacity_economies_of_scale,
                                   ramp_down=self.ramp_down, ramp_up=self.ramp_up,
                                   shut_down_ability=self.shut_down_ability, shut_down_time=self.shut_down_time,
                                   start_up_time=self.start_up_time, number_parallel_units=self.number_parallel_units,
                                   main_conversion=self.main_conversion, side_conversions=self.side_conversions,
                                   min_p=self.min_p, max_p=self.max_p, final_unit=self.final_unit,
                                   default_unit=self.default_unit, custom_unit=self.custom_unit)

    def __init__(self, name, nice_name, lifetime=0., maintenance=0., capex=0., capex_unit='€/MWh Electricity', scalable=False,
                 base_investment=0., base_capacity=0., economies_of_scale=0.,
                 max_capacity_economies_of_scale=0., ramp_down=1., ramp_up=1., shut_down_ability=False,
                 shut_down_time=0., start_up_time=0., number_parallel_units=1,
                 main_conversion=pd.Series(), side_conversions=pd.DataFrame(), min_p=0., max_p=1., streams=None,
                 final_unit=False, default_unit=False, custom_unit=False):

        """
        Class of conversion units
        :param name: [string] - Abbreviation of unit
        :param nice_name: [string] - Nice name of unit
        :param lifetime: [int] - lifetime of unit
        :param maintenance: [float] - maintenance of unit in % of investment
        :param capex: [float] - CAPEX of component
        :param capex_unit: [string] - Unit of capex
        :param scalable: [boolean] - Boolean if scalable unit
        :param base_investment: [float] - If scalable, base investment of unit
        :param base_capacity: [float] - If scalable, base capacity of unit
        :param base_year: [int] - If scalable, year of base investment of unit
        :param economies_of_scale: [float] - Economies of scale of investment and capacity
        :param max_capacity_economies_of_scale: [float] - Maximal capacity, where scaling factor is still applied. Above, constant investment follows
        :param ramp_down: [float] - Ramp down between time steps in % / h
        :param ramp_up: [float] - Ramp up between time steps in % / h
        :param shut_down_ability: [boolean] - Boolean if component can be turned off
        :param shut_down_time: [int] - Time to shut down component
        :param start_up_time: [int] - Time to start up component
        :param number_parallel_units: [int] - Number parallel components with same parameters
        :param main_conversion: [DataFrame] - Main conversion of unit
        :param side_conversions: [DataFrame] - Side conversions of unit
        :param min_p: [float] - Minimal power of the unit when operating
        :param max_p: [float] - Maximal power of the unit when operating
        :param streams: [list] - Streams of the unit
        :param final_unit: [boolean] - if part of the final optimization problem
        :param default_unit: [boolean] - if default component #todo: delete
        :param custom_unit: [boolean] - if not default component #todo: delete
        """

        super().__init__(name, nice_name, lifetime, maintenance, capex_unit, capex,
                         final_unit, default_unit, custom_unit)

        self.component_type = 'conversion'
        self.scalable = bool(scalable)

        self.main_conversion = main_conversion
        self.side_conversions = side_conversions
        if streams is None:
            self.streams = []
        else:
            self.streams = streams

        if main_conversion is not None:
            if not main_conversion.empty:
                self.add_stream(self.main_conversion.loc['input_me'])
                self.add_stream(self.main_conversion.loc['output_me'])

        if side_conversions is not None:
            if not side_conversions.empty:
                for stream in self.side_conversions['input_me'].tolist():
                    self.add_stream(stream)

                for stream in self.side_conversions['output_me'].tolist():
                    self.add_stream(stream)

        self.min_p = min_p
        self.max_p = max_p
        self.ramp_down = ramp_down
        self.ramp_up = ramp_up
        self.shut_down_ability = shut_down_ability
        self.shut_down_time = shut_down_time
        self.start_up_time = start_up_time

        self.capex = capex
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
                                final_unit=self.final_unit, default_unit=self.default_unit,
                                custom_unit=self.custom_unit)

    def __init__(self, name, nice_name, lifetime=0., maintenance=0., capex_unit='€/MWh', capex=0.,
                 charging_efficiency=1., discharging_efficiency=1., min_soc=0., max_soc=1.,
                 initial_soc=0.5, leakage=0., ratio_capacity_p=1.,
                 limited_storage=False, storage_limiting_component=None, storage_limiting_component_ratio=None,
                 final_unit=False, default_unit=False, custom_unit=False):

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
        :param default_unit: [boolean] - if default component #todo: delete
        :param custom_unit: [boolean] - if not default component #todo: delete
        """

        super().__init__(name, nice_name, lifetime, maintenance, capex_unit, capex,
                         final_unit, default_unit, custom_unit)

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
                                   final_unit=self.final_unit, default_unit=self.default_unit,
                                   custom_unit=self.custom_unit)

    def __init__(self, name, nice_name, lifetime=0., maintenance=0., capex_unit='€/MW', capex=0.,
                 generation_data=None, generated_stream='electricity', generation_profile=None,
                 final_unit=False, default_unit=False, custom_unit=False):

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
        :param generation_profile: [list] - contains timeseries of normalized capacity factor
        :param final_unit: [boolean] - if part of the final optimization problem
        :param default_unit: [boolean] - if default component #todo: delete
        :param custom_unit: [boolean] - if not default component #todo: delete
        """
        super().__init__(name, nice_name, lifetime, maintenance, capex_unit, capex,
                         final_unit, default_unit, custom_unit)

        self.component_type = 'generator'

        self.generated_stream = generated_stream
        self.generation_data = generation_data
        self.generation_profile = generation_profile


class Stream:

    def set_nice_name(self, nice_name):
        self.nice_name = nice_name

    def get_nice_name(self):
        return self.nice_name

    def set_name(self, name):
        self.name = name

    def get_name(self):
        return self.name

    def set_unit(self, unit):
        self.stream_unit = unit

    def get_unit(self):
        return self.stream_unit

    def set_purchasable(self, status):
        self.purchasable = status

    def is_purchasable(self):
        return self.purchasable

    def set_purchase_price_type(self, purchase_price_type):
        self.purchase_price_type = purchase_price_type

    def get_purchase_price_type(self):
        return self.purchase_price_type

    def set_purchase_price(self, purchase_price):
        self.purchase_price = purchase_price

    def get_purchase_price(self):
        return self.purchase_price

    def set_saleable(self, status):
        self.saleable = status

    def is_saleable(self):
        return self.saleable

    def set_sale_price_type(self, sale_price_type):
        self.sale_price_type = sale_price_type

    def get_sale_price_type(self):
        return self.sale_price_type

    def set_sale_price(self, sale_price):
        self.sale_price = sale_price

    def get_sale_price(self):
        return self.sale_price

    def set_available(self, status):
        self.available = status

    def is_available(self):
        return self.available

    def set_emittable(self, status):
        self.emittable = status

    def is_emittable(self):
        return self.emittable

    def set_demanded(self, status):
        self.demanded = status

    def is_demanded(self):
        return self.demanded

    def set_demand(self, demand):
        self.demand = demand

    def get_demand(self):
        return self.demand

    def set_total_demand(self, status):
        self.total_demand = status

    def is_total_demand(self):
        return self.total_demand

    def set_storable(self, status):
        self.storable = status

    def is_storable(self):
        return self.storable

    def set_default(self, status):
        self.default_stream = status

    def set_final(self, status):
        self.final_stream = status

    def set_custom(self, status):
        self.custom_stream = status

    def is_default(self):
        return self.default_stream

    def is_final(self):
        return self.final_stream

    def is_custom(self):
        return self.custom_stream

    def __copy__(self):
        return Stream(name=self.name, nice_name=self.nice_name, stream_unit=self.stream_unit,
                      default_stream=self.default_stream, final_stream=self.final_stream,
                      custom_stream=self.custom_stream, emittable=self.emittable, available=self.available,
                      storable=self.storable, purchasable=self.purchasable, purchase_price=self.purchase_price,
                      purchase_price_type=self.purchase_price_type, saleable=self.saleable, sale_price=self.sale_price,
                      sale_price_type=self.sale_price_type, demanded=self.demanded, demand=self.demand,
                      total_demand=self.total_demand)

    def __init__(self, name, nice_name, stream_unit,
                 default_stream=False, final_stream=False, custom_stream=False,
                 emittable=False, available=False, storable=False,
                 purchasable=False, purchase_price=None, purchase_price_type='fixed',
                 saleable=False, sale_price=None, sale_price_type='fixed',
                 demanded=False, demand=0, total_demand=False):

        """

        :param name: [string] - Abbreviation of stream
        :param nice_name: [string] - Nice name of stream
        :param stream_unit: [string] - Unit of stream
        :param default_stream: [boolean] - Is a default stream?
        :param final_stream: [boolean] - Is used in the final optimization?
        :param custom_stream: [boolean] - Is a custom stream?
        :param emittable: [boolean] - can be emitted?
        :param available: [boolean] - is freely available without limitation or price?
        :param storable: [boolean] - can be stored?
        :param purchasable: [boolean] - can be purchased?
        :param purchase_price: [float or list] - fixed price or time varying price
        :param purchase_price_type: [string] - fixed price or time varying price
        :param saleable: [boolean] - can be sold?
        :param sale_price: [float or list] - fixed price or time varying price
        :param sale_price_type: [string] - fixed price or time varying price
        :param demanded: [boolean] - is demanded?
        :param demand: [float] - Demand
        :param total_demand: [boolean] - Demand over all time steps or for each time step
        """

        self.name = name
        self.nice_name = nice_name
        self.stream_unit = stream_unit

        self.default_stream = default_stream
        self.final_stream = final_stream
        self.custom_stream = custom_stream

        self.emittable = emittable
        self.available = available
        self.storable = storable
        self.purchasable = purchasable
        self.purchase_price = purchase_price
        self.purchase_price_type = purchase_price_type
        self.saleable = saleable
        self.sale_price = sale_price
        self.sale_price_type = sale_price_type
        self.demanded = demanded
        self.demand = demand
        self.total_demand = total_demand


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

    # Parameters
    def set_general_parameter_value(self, parameter, value):  # checked
        self.general_parameter_values.update({parameter: float(value)})

    def get_general_parameter_value(self, parameter):  # checked
        return self.general_parameter_values[parameter]

    def get_general_parameter_value_dictionary(self):  # checked
        return self.general_parameter_values

    def set_general_parameter(self, parameter):  # checked
        self.general_parameters.append(parameter)
        self.applied_parameter_for_component[parameter] = {}

    def get_general_parameters(self):  # checked
        return self.general_parameters

    def set_applied_parameter_for_component(self, general_parameter, component, status):
        self.applied_parameter_for_component[general_parameter][component] = status

    def get_applied_parameter_for_component(self, general_parameter, component):
        return self.applied_parameter_for_component[general_parameter][component]

    # Components
    def add_component(self, abbreviation, component):  # checked
        self.components.update({abbreviation: component})
        self.set_nice_name(abbreviation, component.get_nice_name())
        self.set_abbreviation(component.get_nice_name(), abbreviation)

    def get_all_component_names(self):  # checked
        return [*self.components.keys()]

    def get_all_components(self):  # checked
        components = []
        for c in self.get_all_component_names():
            components.append(self.get_component(c))
        return components

    def get_component(self, name):  # checked
        return self.components[name]

    def remove_component_entirely(self, name):
        self.components.pop(name)

    def get_component_by_nice_name(self, nice_name):  # checked
        abbreviation = self.get_abbreviation(nice_name)
        return self.get_component(abbreviation)

    def get_specific_components(self, component_group=None, component_type=None):  # checked
        components = []
        all_components = self.get_all_component_names()

        if component_group is not None:
            for c in all_components:
                if component_group == 'default':
                    if self.get_component(c).is_default():
                        components.append(self.get_component(c))
                elif component_group == 'custom':
                    if self.get_component(c).is_custom():
                        components.append(self.get_component(c))
                elif component_group == 'final':
                    if self.get_component(c).is_final():
                        components.append(self.get_component(c))

            component_type_components = []
            if component_type is not None:
                for c in components:
                    if c.get_component_type() == component_type:
                        component_type_components.append(c)
                return component_type_components
            else:
                return components
        else:
            if component_type is not None:
                component_type_components = []
                for c in all_components:
                    if self.get_component(c).get_component_type() == component_type:
                        component_type_components.append(self.get_component(c))
                return component_type_components

    def get_specific_streams(self, stream_type):
        streams = []
        for stream in self.get_all_streams():
            if stream_type == 'final':
                if self.get_stream(stream).is_final():
                    streams.append(self.get_stream(stream))
            elif stream_type == 'default':
                if self.get_stream(stream).is_default():
                    streams.append(self.get_stream(stream))
            elif stream_type == 'custom':
                if self.get_stream(stream).is_custom():
                    streams.append(self.get_stream(stream))

        return streams

    # Streams
    def add_stream(self, abbreviation, stream):  # checked
        self.streams.update({abbreviation: stream})
        self.set_nice_name(abbreviation, stream.get_nice_name())
        self.set_abbreviation(stream.get_nice_name(), abbreviation)

    def remove_stream_entirely(self, name):
        self.streams.pop(name)

    def get_all_streams(self):
        return self.streams

    def get_all_stream_names(self):  # checked
        return [*self.streams.keys()]

    def get_stream(self, name):  # checked
        return self.streams[name]

    def get_stream_by_nice_name(self, nice_name):
        abbreviation = self.get_abbreviation(nice_name)
        return self.get_stream(abbreviation)

    def get_main_conversion_by_component(self, component):  # checked
        return self.get_component(component).get_main_conversion()

    def get_main_conversion_streams_by_component(self, component):  # checked
        main_conversion = self.get_main_conversion_by_component(component)

        if not main_conversion.empty:
            in_stream = main_conversion.loc['input_me']
            out_stream = main_conversion.loc['output_me']
            return [in_stream, out_stream]
        else:
            return []

    def get_all_main_conversion(self):  # checked
        main_conversions = pd.DataFrame()
        for c in self.get_specific_components('final', 'conversion'):
            main_conversion_c = self.get_main_conversion_by_component(c.get_name())
            main_conversion_c.loc['component'] = c.get_name()
            main_conversions = main_conversions.append(main_conversion_c, ignore_index=True)

        return main_conversions

    def get_side_conversions_by_component(self, component):  # checked
        return self.get_component(component).get_side_conversions()

    def get_all_side_conversions(self):  # checked
        side_conversions = pd.DataFrame()
        for c in self.get_specific_components('final', 'conversion'):
            side_conversions_c = self.get_side_conversions_by_component(c.get_name())
            if not side_conversions_c.empty:
                side_conversions_c.loc[:, 'component'] = c.get_name()
                side_conversions = side_conversions.append(side_conversions_c, ignore_index=True)

        return side_conversions

    def check_number_of_side_conversions_per_stream_and_component(self, component, stream):
        """ Checks if stream is attached to several conversions. If so, the stream is still needed after deleting
        one conversion and the stream cannot be deleted"""
        several_conversions = False

        side_conversions = self.get_side_conversions_by_component(component)

        one_input = True
        if len(side_conversions[side_conversions['input_me'] == stream].index) > 1:
            one_input = False

        one_output = True
        if len(side_conversions[side_conversions['output_me'] == stream].index) > 1:
            one_output = False

        if (not one_input) | (not one_output):
            several_conversions = True

        return several_conversions

    def get_stream_by_component(self, component):  # checked
        return self.components[component].get_streams()

    def get_component_by_stream(self, stream):  # checked
        components = []

        for c in self.components:
            if stream in self.get_stream_by_component(c):
                components.append(c)

        return components

    def remove_stream(self, stream):
        """ Remove streams if it is not attached to more than on conversion """

        number_conversions = 0

        for component in self.get_specific_components('final', 'conversion'):
            if component.is_final():

                side_conversions = component.get_side_conversions()
                if side_conversions is not None:
                    if not side_conversions.empty:
                        side_conversions = component.get_side_conversions()
                        number_conversions += len(side_conversions[side_conversions['input_me'] == stream].index)
                        number_conversions += len(side_conversions[side_conversions['output_me'] == stream].index)

                main_conversion = component.get_main_conversion()
                if stream == main_conversion.loc['input_me']:
                    number_conversions += 1

                if stream == main_conversion.loc['output_me']:
                    number_conversions += 1

        if number_conversions == 0:
            self.get_stream(stream).set_final(False)

    def set_integer_steps(self, integer_steps):
        self.integer_steps = integer_steps

    def get_integer_steps(self):
        return self.integer_steps

    def create_new_project(self):
        """ Create new project """

        nice_names = {'WACC': 'wacc',
                      'Personnel Cost': 'personnel_costs',
                      'Taxes and insurance': 'taxes_and_insurance',
                      'Overhead': 'overhead',
                      'Working Capital': 'working_capital',
                      'Covered Period': 'covered_period'}

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

        self.set_general_parameter_value('covered_period', 8760)
        self.set_general_parameter('covered_period')

        conversion_component = ConversionComponent(name='dummy', nice_name='Dummy', final_unit=True)
        self.add_component('dummy', conversion_component)

        for g in self.get_general_parameters():
            self.set_applied_parameter_for_component(g, 'dummy', True)

        c = 'dummy'
        input_stream = 'electricity'
        output_stream = 'electricity'
        coeff = 1

        self.get_component(c).set_main_conversion(input_stream, output_stream, coeff)

        s = Stream('electricity', 'Electricity', 'MWh', final_stream=True)
        self.add_stream('electricity', s)

        self.set_nice_name('electricity', 'Electricity')
        self.set_abbreviation('Electricity', 'electricity')

    def create_from_custom(self):

        case_data = pd.read_excel(self.path_custom, index_col=0)

        """ Set general parameters """
        general_parameter_df = case_data[case_data['type'] == 'general_parameter']

        for i in general_parameter_df.index:
            parameter = general_parameter_df.loc[i, 'parameter']
            value = general_parameter_df.loc[i, 'value']

            self.set_general_parameter_value(parameter, value)
            self.set_general_parameter(parameter)

        """Allocate components and parameters"""
        component_df = case_data[case_data['type'] == 'component']

        for i in component_df.index:
            name = component_df.loc[i, 'name']
            nice_name = component_df.loc[i, 'nice_name']
            capex = component_df.loc[i, 'capex']
            capex_unit = component_df.loc[i, 'capex_unit']
            lifetime = component_df.loc[i, 'lifetime']
            maintenance = component_df.loc[i, 'maintenance']
            final_unit = component_df.loc[i, 'final']

            if component_df.loc[i, 'component_type'] == 'conversion':

                min_p = component_df.loc[i, 'min_p']
                max_p = component_df.loc[i, 'max_p']
                scalable = component_df.loc[i, 'scalable']
                base_investment = component_df.loc[i, 'base_investment']
                base_capacity = component_df.loc[i, 'base_capacity']
                economies_of_scale = component_df.loc[i, 'economies_of_scale']
                max_capacity_economies_of_scale = component_df.loc[i, 'max_capacity_economies_of_scale']
                number_parallel_units = case_data.loc[i, 'number_parallel_units']
                ramp_up = case_data.loc[i, 'ramp_up']
                ramp_down = case_data.loc[i, 'ramp_down']
                shut_down_ability = case_data.loc[i, 'shut_down_ability']
                shut_down_time = case_data.loc[i, 'shut_down_time']
                start_up_time = case_data.loc[i, 'start_up_time']

                conversion_component = ConversionComponent(name=name, nice_name=nice_name, lifetime=lifetime,
                                                           maintenance=maintenance, base_investment=base_investment,
                                                           capex=capex, capex_unit=capex_unit, scalable=scalable,
                                                           base_capacity=base_capacity,
                                                           economies_of_scale=economies_of_scale,
                                                           max_capacity_economies_of_scale=max_capacity_economies_of_scale,
                                                           number_parallel_units=number_parallel_units,
                                                           min_p=min_p, max_p=max_p, ramp_up=ramp_up,
                                                           shut_down_ability=shut_down_ability,
                                                           ramp_down=ramp_down, shut_down_time=shut_down_time,
                                                           start_up_time=start_up_time,
                                                           final_unit=final_unit, default_unit=True)

                self.add_component(name, conversion_component)

                for g in self.get_general_parameters():
                    self.set_applied_parameter_for_component(g, 'dummy', True)

            elif component_df.loc[i, 'component_type'] == 'storage':

                min_soc = case_data.loc[i, 'min_soc']
                max_soc = case_data.loc[i, 'max_soc']
                initial_soc = case_data.loc[i, 'initial_soc']
                charging_efficiency = case_data.loc[i, 'charging_efficiency']
                discharging_efficiency = case_data.loc[i, 'discharging_efficiency']
                leakage = case_data.loc[i, 'leakage']
                ratio_capacity_p = case_data.loc[i, 'ratio_capacity_p']
                limited = case_data.loc[i, 'limited_storage']
                storage_limiting_component = case_data.loc[i, 'storage_limiting_component']
                storage_limiting_component_ratio = case_data.loc[i, 'storage_limiting_component_ratio']

                storage_component = StorageComponent(name, nice_name, lifetime, maintenance, capex_unit, capex,
                                                     charging_efficiency, discharging_efficiency, min_soc, max_soc,
                                                     initial_soc, leakage=leakage, ratio_capacity_p=ratio_capacity_p,
                                                     storage_limiting_component=storage_limiting_component,
                                                     storage_limiting_component_ratio=storage_limiting_component_ratio,
                                                     final_unit=final_unit, default_unit=True, limited_storage=limited)
                self.add_component(name, storage_component)

            elif component_df.loc[i, 'component_type'] == 'generator':
                generated_stream = case_data.loc[i, 'generated_stream']
                generation_data = case_data.loc[i, 'generation_data']

                generator = GenerationComponent(name, nice_name, lifetime, maintenance, capex_unit, capex,
                                                generated_stream=generated_stream, generation_data=generation_data,
                                                final_unit=final_unit, default_unit=True)
                self.add_component(name, generator)

            try:
                self.set_applied_parameter_for_component('taxes_and_insurance', name,
                                                         bool(case_data.loc[i, 'taxes_and_insurance']))
                self.set_applied_parameter_for_component('personnel_costs', name,
                                                         bool(case_data.loc[i, 'personnel_costs']))
                self.set_applied_parameter_for_component('overhead', name,
                                                         bool(case_data.loc[i, 'overhead']))
                self.set_applied_parameter_for_component('working_capital', name,
                                                         bool(case_data.loc[i, 'working_capital']))

            except:
                for p in self.get_general_parameters():
                    self.set_applied_parameter_for_component(p, name, True)

        """ Conversions """
        main_conversions = case_data[case_data['type'] == 'main_conversion']
        for i in main_conversions.index:
            component = main_conversions.loc[i, 'component']
            in_stream = main_conversions.loc[i, 'input_stream']
            out_stream = main_conversions.loc[i, 'output_stream']
            coefficient = float(main_conversions.loc[i, 'coefficient'])

            self.get_component(component).set_main_conversion(in_stream, out_stream, coefficient)

        side_conversions = case_data[case_data['type'] == 'side_conversion']
        for i in side_conversions.index:
            component = side_conversions.loc[i, 'component']
            in_stream = side_conversions.loc[i, 'input_stream']
            out_stream = side_conversions.loc[i, 'output_stream']
            coefficient = float(side_conversions.loc[i, 'coefficient'])

            self.get_component(component).add_side_conversion(in_stream, out_stream, coefficient)

        """ Streams """
        streams = case_data[case_data['type'] == 'stream']
        for i in streams.index:
            abbreviation = case_data.loc[i, 'name']
            nice_name = case_data.loc[i, 'nice_name']
            stream_unit = case_data.loc[i, 'unit']

            available = case_data.loc[i, 'available']
            emittable = case_data.loc[i, 'emitted']
            purchasable = case_data.loc[i, 'purchasable']
            saleable = case_data.loc[i, 'saleable']
            demanded = case_data.loc[i, 'demanded']
            total_demand = case_data.loc[i, 'total_demand']
            final_stream = case_data.loc[i, 'final']
            storable_stream = case_data.loc[i, 'storable']

            # Purchasable streams
            purchase_price_type = case_data.loc[i, 'purchase_price_type']
            purchase_price = case_data.loc[i, 'purchase_price']

            # Saleable streams
            selling_price_type = case_data.loc[i, 'selling_price_type']
            selling_price = case_data.loc[i, 'selling_price']

            # Demand
            demand = case_data.loc[i, 'demand']

            stream = Stream(abbreviation, nice_name, stream_unit, final_stream=final_stream,
                            available=available, purchasable=purchasable, saleable=saleable, emittable=emittable,
                            demanded=demanded, total_demand=total_demand,
                            purchase_price=purchase_price, purchase_price_type=purchase_price_type,
                            sale_price=selling_price, sale_price_type=selling_price_type, demand=demand,
                            storable=storable_stream)
            self.add_stream(abbreviation, stream)

        """ Set nice names and abbreviations """
        name_df = case_data[case_data['type'] == 'names']

        for i in name_df.index:
            nice_name = name_df.loc[i, 'nice_name']
            abbreviation = name_df.loc[i, 'abbreviation']

            self.set_nice_name(abbreviation, nice_name)
            self.set_abbreviation(nice_name, abbreviation)

    def __copy__(self):
        return ParameterObject(name=self.name,
                               integer_steps=self.integer_steps, general_parameters=self.general_parameters,
                               general_parameter_values=self.general_parameter_values, nice_names=self.nice_names,
                               abbreviations_dict=self.abbreviations_dict, streams=self.streams,
                               components=self.components, copy_object=True)

    def __init__(self, name=None, path_custom=None, integer_steps=5,
                 general_parameters=None, general_parameter_values=None,
                 nice_names=None, abbreviations_dict=None, streams=None, components=None,
                 copy_object=False):

        """
        Object, which stores all components, streams, settings etc.
        :param name: [string] - name of parameter object
        :param path_custom: [string] - path to custom settings
        :param integer_steps: [int] - number of integer steps (used to split capacity)
        :param general_parameters: [list] - List of general parameters
        :param general_parameter_values: [dict] - Dictionary with general parameter values
        :param nice_names: [list] - List of nice names of components, streams etc.
        :param abbreviations_dict: [dict] - List of abbreviations of components, streams etc.
        :param streams: [dict] - Dictionary with abbreviations as keys and stream objects as values
        :param components: [dict] - Dictionary with abbreviations as keys and component objects as values
        :param copy_object: [boolean] - Boolean if object is copy
        """
        self.name = name

        if not copy_object:
            self.path_custom = path_custom

            self.general_parameters = []
            self.general_parameter_values = {}
            self.applied_parameter_for_component = {}
            self.nice_names = {}
            self.abbreviations_dict = {}

            self.streams = {}
            self.components = {}

            if self.path_custom is None:
                self.create_new_project()
            else:
                self.create_from_custom()

        else:
            self.path_custom = path_custom

            self.general_parameters = general_parameters
            self.general_parameter_values = general_parameter_values

            self.applied_parameter_for_component = {}
            for g in self.get_general_parameters():
                self.applied_parameter_for_component[g] = {}

            self.nice_names = nice_names
            self.abbreviations_dict = abbreviations_dict

            self.streams = streams
            self.components = components

        self.integer_steps = integer_steps


ParameterObjectCopy = type('CopyOfB', ParameterObject.__bases__, dict(ParameterObject.__dict__))
