import pandas as pd
import copy

from components import ConversionComponent
from stream import Stream

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

    # Parameters
    def set_general_parameter_value(self, parameter, value):  # checked
        self.general_parameter_values.update({parameter: float(value)})

    def get_general_parameter_value(self, parameter):  # checked
        return self.general_parameter_values[parameter]

    def get_general_parameter_value_dictionary(self):  # checked
        return self.general_parameter_values

    def set_general_parameter(self, parameter):  # checked
        if parameter not in self.general_parameters:
            self.general_parameters.append(parameter)

            if parameter not in ['wacc', 'covered_period', 'representative_weeks']:
                self.applied_parameter_for_component[parameter] = {}

    def get_general_parameters(self):  # checked
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

    # Components
    def add_component(self, abbreviation, component):  # checked
        self.components.update({abbreviation: component})
        self.set_nice_name(abbreviation, component.get_nice_name())
        self.set_abbreviation(component.get_nice_name(), abbreviation)

        self.applied_parameter_for_component[abbreviation] = {'taxes_and_insurance': True,
                                                              'personnel_costs': True,
                                                              'overhead': True,
                                                              'working_capital': True}

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

    def get_specific_streams(self, final_stream=None, custom_stream=None):
        streams = []
        for stream in self.get_all_streams():

            if final_stream is not None:
                if final_stream:
                    if self.get_stream(stream).is_final():
                        streams.append(self.get_stream(stream))
                else:
                    if not self.get_stream(stream).is_final():
                        streams.append(self.get_stream(stream))

        if custom_stream is not None:
            if streams:
                for stream in streams:
                    if custom_stream:
                        if self.get_stream(stream).is_custom():
                            streams.append(self.get_stream(stream))
                    else:
                        if not self.get_stream(stream).is_custom():
                            streams.append(self.get_stream(stream))

            else:
                for stream in self.get_all_streams():
                    if custom_stream:
                        if self.get_stream(stream).is_custom():
                            streams.append(self.get_stream(stream))
                    else:
                        if not self.get_stream(stream).is_custom():
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
        all_streams = []
        for s in [*self.get_all_streams().keys()]:
            if s not in all_streams:
                all_streams.append(s)
        return all_streams

    def get_stream(self, name):  # checked
        return self.streams[name]

    def get_stream_by_nice_name(self, nice_name):
        abbreviation = self.get_abbreviation(nice_name)
        return self.get_stream(abbreviation)

    def get_stream_by_component(self, component):  # checked
        return self.components[component].get_streams()

    def get_component_by_stream(self, stream):  # checked
        components = []

        for c in self.components:
            if stream in self.get_stream_by_component(c):
                components.append(c)

        return components

    def remove_stream(self, stream):
        self.get_stream(stream).set_final(False)

    def activate_stream(self, stream):
        self.get_stream(stream).set_final(True)

    def set_integer_steps(self, integer_steps):
        self.integer_steps = integer_steps

    def get_integer_steps(self):
        return self.integer_steps

    def set_uses_representative_weeks(self, uses_weeks):
        self.uses_representative_weeks = bool(uses_weeks)

    def get_uses_representative_weeks(self):
        return self.uses_representative_weeks

    def set_path_weighting(self, path):
        self.path_weighting = str(path)

    def get_path_weighting(self):
        return self.path_weighting

    def set_covered_period(self, covered_period):
        self.covered_period = covered_period

    def get_covered_period(self):
        return self.covered_period

    def set_generation_profile_status(self, status):
        self.generation_profile_status = status

    def get_generation_profile_status(self):
        return self.generation_profile_status

    def set_generation_data(self, generation_data):
        self.generation_data = generation_data

    def get_generation_data(self):
        return self.generation_data

    def set_sell_purchase_profile_status(self, status):
        self.sell_purchase_profile_status = status

    def get_sell_purchase_profile_status(self):
        return self.sell_purchase_profile_status

    def set_sell_purchase_data(self, sell_purchase_data):
        self.sell_purchase_data = sell_purchase_data

    def get_sell_purchase_data(self):
        return self.sell_purchase_data

    def get_path_data(self):
        return self.path_data

    def get_project_name(self):
        return self.project_name

    def set_project_name(self, project_name):
        self.project_name = project_name

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
        input_stream = 'electricity'
        output_stream = 'electricity'

        self.get_component(c).add_input(input_stream, 1)
        self.get_component(c).add_output(output_stream, 1)

        self.get_component(c).set_main_input(input_stream)
        self.get_component(c).set_main_output(output_stream)

        s = Stream('electricity', 'Electricity', 'MWh', final_stream=True)
        self.add_stream('electricity', s)

        self.set_nice_name('electricity', 'Electricity')
        self.set_abbreviation('Electricity', 'electricity')

    def __copy__(self):

        # deepcopy mutable objects
        general_parameters = copy.deepcopy(self.general_parameters)
        general_parameter_values = copy.deepcopy(self.general_parameter_values)
        nice_names = copy.deepcopy(self.nice_names)
        abbreviations_dict = copy.deepcopy(self.abbreviations_dict)
        streams = copy.deepcopy(self.streams)

        return ParameterObject(name=self.name,
                               integer_steps=self.integer_steps,
                               general_parameters=general_parameters,
                               general_parameter_values=general_parameter_values,
                               nice_names=nice_names,
                               abbreviations_dict=abbreviations_dict,
                               streams=streams,
                               components=self.components,
                               generation_data=self.generation_data,
                               generation_profile_status=self.generation_profile_status,
                               sell_purchase_data=self.sell_purchase_data,
                               sell_purchase_profile_status=self.sell_purchase_profile_status,
                               uses_representative_weeks=self.uses_representative_weeks,
                               path_weighting=self.path_weighting,
                               covered_period=self.covered_period,
                               copy_object=True)

    def __init__(self, name=None, integer_steps=5,
                 general_parameters=None, general_parameter_values=None,
                 nice_names=None, abbreviations_dict=None, streams=None, components=None,
                 generation_data=None, generation_profile_status=True,
                 sell_purchase_data=None, sell_purchase_profile_status=None,
                 uses_representative_weeks=False, path_weighting='',  covered_period=8760,
                 project_name=None, path_data=None,
                 copy_object=False):

        """
        Object, which stores all components, streams, settings etc.
        :param name: [string] - name of parameter object
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

            self.streams = {}
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

            self.streams = streams
            self.components = components

        self.covered_period = covered_period
        self.uses_representative_weeks = uses_representative_weeks
        self.path_weighting = path_weighting
        self.integer_steps = integer_steps

        self.generation_data = generation_data
        self.generation_profile_status = bool(generation_profile_status)

        self.sell_purchase_data = sell_purchase_data
        self.sell_purchase_profile_status = bool(sell_purchase_profile_status)

        self.path_data = path_data
        self.project_name = project_name


ParameterObjectCopy = type('CopyOfB', ParameterObject.__bases__, dict(ParameterObject.__dict__))
