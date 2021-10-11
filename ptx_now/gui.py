import os

import tkinter as tk
from tkinter import *
from tkinter import ttk
import pandas as pd
from datetime import datetime

from _helpers_gui import AssumptionsInterface, ComponentInterface, StreamInterface, StorageInterface, GeneratorInterface
from optimization_classes_and_methods import OptimizationProblem
from analysis_classes_and_methods import Result
from parameter_object import ParameterObject

from load_projects import load_setting


class Interface:

    def __init__(self, path_data, path_result, path_settings, solver, path_custom=None):

        self.path_data = path_data
        self.path_result = path_result
        self.path_settings = path_settings
        self.path_custom = path_custom
        self.working_path = os.getcwd()
        self.solver = solver

        self.root = Tk()
        #self.root.geometry('500x750')
        ttk.Style().theme_use('vista')

        if self.path_custom is None:  # New project

            self.pm_object_original = ParameterObject('parameter', integer_steps=10)
            self.pm_object_original.create_new_project()

            self.pm_object_copy = ParameterObject('parameter2', integer_steps=10)
            self.pm_object_copy.create_new_project()

            self.root.title('New Project')

        else:  # Custom project

            self.pm_object_original = ParameterObject('parameter', integer_steps=10)
            self.pm_object_copy = ParameterObject('parameter2', integer_steps=10)

            case_data = pd.read_excel(self.path_custom, index_col=0)

            self.pm_object_original = load_setting(self.pm_object_original, case_data)
            self.pm_object_copy = load_setting(self.pm_object_copy, case_data)

            custom_title = self.path_custom.split('/')[-1].split('.')[0]
            self.root.title(custom_title)

        self.me_checked = False  # boolean if mass energy balance was checked

        self.general_parameters_df = pd.DataFrame()
        self.components_df = pd.DataFrame()
        self.streams_df = pd.DataFrame()
        self.storages_df = pd.DataFrame()
        self.generators_df = pd.DataFrame()

        self.widgets()
        if False:
            self.save_current_parameters_and_options()

    def widgets(self):

        if False:

            self.canvas = tk.Canvas(self.root)
            self.scrollbar = ttk.Scrollbar(self.root, orient="vertical")
            self.scrollbar.config(command=self.canvas.yview)

            self.scrollable_frame = ttk.Frame(self.canvas)
            interior_id = self.canvas.create_window(0, 0, window=self.scrollable_frame, anchor=NW)
            self.canvas.configure(yscrollcommand=self.scrollbar.set)

            def _configure_interior(event):
                # update the scrollbars to match the size of the inner frame
                size = (self.scrollable_frame.winfo_reqwidth(), self.scrollable_frame.winfo_reqheight())
                self.canvas.config(scrollregion="0 0 %s %s" % size)
            self.scrollable_frame.bind('<Configure>', _configure_interior)

            def _configure_canvas(event):
                if self.scrollable_frame.winfo_reqwidth() != self.canvas.winfo_width():
                    # update the inner frame's width to fill the canvas
                    self.canvas.itemconfigure(interior_id, width=self.canvas.winfo_width())
            self.canvas.bind('<Configure>', _configure_canvas)

            def _on_mousewheel(event):
                self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            self.canvas.bind_all("<MouseWheel>", _on_mousewheel)

            self.general_assumptions = ToggledFrame(self, self.root, self.scrollable_frame, text='General assumptions',
                                   pm_object_original=self.pm_object_original, pm_object_copy=self.pm_object_copy,
                                   frame_type='general', relief="raised", borderwidth=1)
            self.general_assumptions.pack(fill="x", expand=1, pady=2, padx=2, anchor="n")

            self.components = ToggledFrame(self, self.root, self.scrollable_frame, text='Components',
                                   pm_object_original=self.pm_object_original, pm_object_copy=self.pm_object_copy,
                                   frame_type='component', relief="raised", borderwidth=1)
            self.components.pack(fill="x", expand=1, pady=2, padx=2, anchor="n")

            self.streams = ToggledFrame(self, self.root, self.scrollable_frame, text='Streams',
                                   pm_object_original=self.pm_object_original, pm_object_copy=self.pm_object_copy,
                                   frame_type='stream', relief="raised", borderwidth=1)
            self.streams.pack(fill="x", expand=1, pady=2, padx=2, anchor="n")

            self.storages = ToggledFrame(self, self.root, self.scrollable_frame, text='Storage',
                                   pm_object_original=self.pm_object_original, pm_object_copy=self.pm_object_copy,
                                   frame_type='storage', relief="raised", borderwidth=1)
            self.storages.pack(fill="x", expand=1, pady=2, padx=2, anchor="n")

            self.generators = ToggledFrame(self, self.root, self.scrollable_frame, text='Generators',
                                   pm_object_original=self.pm_object_original, pm_object_copy=self.pm_object_copy,
                                   frame_type='generator', relief="raised", borderwidth=1)
            self.generators.pack(fill="x", expand=1, pady=2, padx=2, anchor="n")

            self.canvas.pack(side="left", fill="both", expand=True)
            self.scrollbar.pack(side="right", fill="y", expand=False)

            self.scrollable_frame.grid_rowconfigure(0, weight=1)
            self.scrollable_frame.grid_columnconfigure(0, weight=1)

        else:
            self.overall_notebook = ttk.Notebook(self.root)

            # def

            self.general_assumptions = AssumptionsInterface(self, self.overall_notebook,
                                                    pm_object_original=self.pm_object_original,
                                                    pm_object_copy=self.pm_object_copy,)
            self.general_assumptions.pack(fill='both', expand=True)

            self.components = ComponentInterface(self, self.overall_notebook,
                                                 pm_object_original=self.pm_object_original,
                                                 pm_object_copy=self.pm_object_copy)
            self.components.pack(fill='both', expand=True)

            self.streams = StreamInterface(self, self.overall_notebook,
                                           pm_object_original=self.pm_object_original,
                                           pm_object_copy=self.pm_object_copy)
            self.streams.pack(fill='both', expand=True)

            self.storages = StorageInterface(self, self.overall_notebook,
                                             pm_object_original=self.pm_object_original,
                                             pm_object_copy=self.pm_object_copy)
            self.storages.pack(fill='both', expand=True)

            self.generators = GeneratorInterface(self, self.overall_notebook,
                                                 pm_object_original=self.pm_object_original,
                                                 pm_object_copy=self.pm_object_copy)
            self.generators.pack(fill='both', expand=True)

            self.overall_notebook.add(self.general_assumptions, text='General Assumptions')
            self.overall_notebook.add(self.components, text='Components')
            self.overall_notebook.add(self.streams, text='Streams')
            self.overall_notebook.add(self.storages, text='Storages')
            self.overall_notebook.add(self.generators, text='Generators')

            self.overall_notebook.pack(pady=10, expand=True, anchor='n')

        button_frame = ttk.Frame(self.root)

        check_streams_button = ttk.Button(button_frame, text='Check settings', command=self.check_all_settings)
        check_streams_button.grid(row=0, column=0, sticky='ew')

        save_settings = ttk.Button(button_frame, text='Save settings', command=self.save_setting_window)
        save_settings.grid(row=0, column=1, sticky='ew')

        self.optimize_button = ttk.Button(button_frame, text='Optimize', state=DISABLED, command=self.optimize)
        self.optimize_button.grid(row=0, column=2, sticky='ew')

        button_frame.grid_columnconfigure(0, weight=1, uniform='a')
        button_frame.grid_columnconfigure(1, weight=1, uniform='a')
        button_frame.grid_columnconfigure(2, weight=1, uniform='a')

        button_frame.pack(fill="both", expand=True)

        button_frame_2 = ttk.Frame(self.root)

        get_data_template_button = ttk.Button(button_frame_2, text='Get Data Template',
                                              command=self.get_data_template)
        get_data_template_button.grid(row=0, column=0, sticky='ew')

        return_to_start = ttk.Button(button_frame_2, text='Cancel', command=self.cancel)
        return_to_start.grid(row=0, column=1, sticky='ew')

        button_frame_2.grid_columnconfigure(0, weight=1, uniform='a')
        button_frame_2.grid_columnconfigure(1, weight=1, uniform='a')

        button_frame_2.pack(fill="both", expand=True)

        self.root.mainloop()

    def update_widgets(self):
        # Simply recreate the frames with the new pm object

        self.general_assumptions.update_self_pm_object(self.pm_object_copy)
        self.general_assumptions.update_frame()

        self.components.update_self_pm_object(self.pm_object_copy)
        self.components.update_frame()

        self.streams.update_self_pm_object(self.pm_object_copy)
        self.streams.update_frame()

        self.storages.update_self_pm_object(self.pm_object_copy)
        self.storages.update_frame()

        self.generators.update_self_pm_object(self.pm_object_copy)
        self.generators.update_frame()

        self.optimize_button.config(state=DISABLED)

    def check_all_settings(self):

        def kill_window():
            alert_window.destroy()

        valid_me_for_stream = {}
        streams_without_well = []
        streams_without_sink = []

        for stream in self.pm_object_copy.get_specific_streams(final_stream=True):

            well_existing = False
            sink_existing = False

            # Check if stream has a well
            if stream.is_available():
                well_existing = True
            elif stream.is_purchasable():
                well_existing = True

            # If no well exists, the stream has to be generated or converted from other stream
            if not well_existing:
                for component in self.pm_object_copy.get_specific_components('final', 'conversion'):
                    outputs = component.get_outputs()
                    for o in [*outputs.keys()]:
                        if o == stream.get_name():
                            well_existing = True
                            break

                if not well_existing:
                    for component in self.pm_object_copy.get_specific_components('final', 'generator'):
                        if stream.get_name() == component.get_generated_stream():
                            well_existing = True
                            break

            if not well_existing:
                streams_without_well.append(stream.get_name())

            # Check if stream has a sink
            if stream.is_emittable():
                sink_existing = True
            elif stream.is_saleable():
                sink_existing = True
            elif stream.is_demanded():
                sink_existing = True

            # If no well exists, the stream has to be generated or converted from other stream
            if not sink_existing:
                for component in self.pm_object_copy.get_specific_components('final', 'conversion'):
                    inputs = component.get_inputs()
                    for i in [*inputs.keys()]:
                        if i == stream.get_name():
                            sink_existing = True
                            break

            if not sink_existing:
                streams_without_sink.append(stream.get_name())

            if well_existing & sink_existing:
                valid_me_for_stream.update({stream.get_name(): True})
            else:
                valid_me_for_stream.update({stream.get_name(): False})

        all_streams_valid = True
        for stream in self.pm_object_copy.get_specific_streams(final_stream=True):
            if not valid_me_for_stream[stream.get_name()]:
                all_streams_valid = False

        # Check if a profile for the generation unit exists, if generation unit is enabled
        profiles_exist = True
        generators_without_profile = []
        for generator in self.pm_object_copy.get_specific_components('final', 'generator'):
            try:
                generator.get_generation_data()
            except:
                profiles_exist = False
                generators_without_profile.append(generator.get_nice_name())

        error_in_setting = False
        if (not profiles_exist) | (not all_streams_valid):
            error_in_setting = True

        if error_in_setting:
            self.optimize_button.config(state=DISABLED)
            alert_window = Toplevel(self.root)
            alert_window.title('')

            if not all_streams_valid:

                no_well_text = ''
                no_sink_text = ''

                if len(streams_without_well) > 0:

                    if len(streams_without_well) == 1:
                        no_well_text = 'The following stream has no well: '
                    else:
                        no_well_text = 'The following streams have no well: '

                    for stream in streams_without_well:
                        if streams_without_well.index(stream) != len(streams_without_well) - 1:
                            no_well_text += self.pm_object_copy.get_nice_name(stream) + ', '
                        else:
                            no_well_text += self.pm_object_copy.get_nice_name(stream)

                if len(streams_without_sink) > 0:

                    if len(streams_without_well) == 1:
                        no_sink_text = 'The following stream has no sink: '
                    else:
                        no_sink_text = 'The following streams have no sink: '

                    for stream in streams_without_sink:
                        if streams_without_sink.index(stream) != len(streams_without_sink) - 1:
                            no_sink_text += self.pm_object_copy.get_nice_name(stream) + ', '
                        else:
                            no_sink_text += self.pm_object_copy.get_nice_name(stream)

                if no_well_text != '':

                    tk.Label(alert_window, text=no_well_text).pack()
                    tk.Label(alert_window,
                             text='It is important that every stream has a well. \n' +
                                  ' That means that it is either generated, converted from another stream,' +
                                  ' freely available or purchasable. \n'
                                  ' Please adjust your inputs/outputs or the individual stream').pack()
                    tk.Label(alert_window, text='').pack()

                if no_sink_text != '':

                    tk.Label(alert_window, text=no_sink_text).pack()
                    tk.Label(alert_window,
                             text='It is important that every stream has a sink. \n'
                                  ' That means that it is either converted to another stream,' +
                                  ' emitted, saleable or implemented as demand. \n' +
                                  ' Please adjust your inputs/outputs or the individual stream').pack()
                    tk.Label(alert_window, text='').pack()

            if not profiles_exist:
                no_profile_text = 'The following generators have no profile: '

                for generator in generators_without_profile:
                    if generators_without_profile.index(generator) != len(generators_without_profile) - 1:
                        no_profile_text += self.pm_object_copy.get_nice_name(generator) + ', '
                    else:
                        no_profile_text += self.pm_object_copy.get_nice_name(generator)

                tk.Label(alert_window, text=no_profile_text).pack()
                tk.Label(alert_window,
                         text='It is important that every generator has a profile. Please adjust your generators').pack()
                tk.Label(alert_window, text='').pack()

            ttk.Button(alert_window, text='OK', command=kill_window).pack(fill='both', expand=True)
        else:
            self.optimize_button.config(state=NORMAL)

    def save_setting_window(self): #Todo: Only save when closed or optimized

        def kill_window_and_save():
            self.save_current_parameters_and_options(name_entry.get())
            newWindow.destroy()

        def kill_only():
            newWindow.destroy()

        newWindow = Toplevel(self.root)

        Label(newWindow, text='Enter name of settings file').grid(row=0, column=0, sticky='ew')

        name_entry = Entry(newWindow)
        name_entry.grid(row=0, column=1, sticky='ew')

        ttk.Button(newWindow, text='Save', command=kill_window_and_save).grid(row=1, column=0, sticky='ew')
        ttk.Button(newWindow, text='Cancel', command=kill_only).grid(row=1, column=1, sticky='ew')

        newWindow.grid_columnconfigure(0, weight=1, uniform='a')
        newWindow.grid_columnconfigure(1, weight=1, uniform='a')

    def save_current_parameters_and_options(self, name=None):

        case_data = pd.DataFrame()

        k = 0

        case_data.loc[k, 'version'] = '0.0.3'

        k += 1

        for parameter in self.pm_object_copy.get_general_parameters():
            value = self.pm_object_copy.get_general_parameter_value(parameter)

            case_data.loc[k, 'type'] = 'general_parameter'
            case_data.loc[k, 'parameter'] = parameter
            case_data.loc[k, 'value'] = value

            k += 1

        case_data.loc[k, 'type'] = 'representative_weeks'
        case_data.loc[k, 'representative_weeks'] = self.pm_object_copy.get_uses_representative_weeks()
        case_data.loc[k, 'number_representative_weeks'] = self.pm_object_copy.get_number_representative_weeks()
        case_data.loc[k, 'path_weighting'] = self.pm_object_copy.get_path_weighting()
        case_data.loc[k, 'covered_period'] = self.pm_object_copy.get_covered_period()

        k += 1

        for component in self.pm_object_copy.get_all_components():

            case_data.loc[k, 'type'] = 'component'
            case_data.loc[k, 'component_type'] = component.get_component_type()
            case_data.loc[k, 'final'] = component.is_final()
            case_data.loc[k, 'name'] = component.get_name()
            case_data.loc[k, 'nice_name'] = component.get_nice_name()
            case_data.loc[k, 'capex'] = component.get_capex()
            case_data.loc[k, 'lifetime'] = component.get_lifetime()
            case_data.loc[k, 'maintenance'] = component.get_maintenance()

            if component.get_component_type() == 'conversion':

                case_data.loc[k, 'capex_basis'] = component.get_capex_basis()
                case_data.loc[k, 'scalable'] = component.is_scalable()
                case_data.loc[k, 'base_investment'] = component.get_base_investment()
                case_data.loc[k, 'base_capacity'] = component.get_base_capacity()
                case_data.loc[k, 'economies_of_scale'] = component.get_economies_of_scale()
                case_data.loc[k, 'max_capacity_economies_of_scale'] = component.get_max_capacity_economies_of_scale()

                case_data.loc[k, 'min_p'] = component.get_min_p()
                case_data.loc[k, 'max_p'] = component.get_max_p()

                case_data.loc[k, 'ramp_up'] = component.get_ramp_up()
                case_data.loc[k, 'ramp_down'] = component.get_ramp_down()

                case_data.loc[k, 'shut_down_ability'] = component.get_shut_down_ability()
                if component.get_shut_down_ability():
                    case_data.loc[k, 'start_up_time'] = component.get_start_up_time()
                else:
                    case_data.loc[k, 'start_up_time'] = 0

                case_data.loc[k, 'hot_standby_ability'] = component.get_hot_standby_ability()
                if component.get_hot_standby_ability():
                    case_data.loc[k, 'hot_standby_stream'] = [*component.get_hot_standby_demand().keys()][0]
                    case_data.loc[k, 'hot_standby_demand'] = component.get_hot_standby_demand()[
                        [*component.get_hot_standby_demand().keys()][0]]
                    case_data.loc[k, 'hot_standby_startup_time'] = component.get_hot_standby_startup_time()
                else:
                    case_data.loc[k, 'hot_standby_stream'] = ''
                    case_data.loc[k, 'hot_standby_demand'] = 0
                    case_data.loc[k, 'hot_standby_startup_time'] = 0

                case_data.loc[k, 'number_parallel_units'] = component.get_number_parallel_units()

            elif component.get_component_type() == 'generator':

                case_data.loc[k, 'generated_stream'] = component.get_generated_stream()
                case_data.loc[k, 'generation_data'] = component.get_generation_data()

            elif component.get_component_type() == 'storage':

                case_data.loc[k, 'min_soc'] = component.get_min_soc()
                case_data.loc[k, 'max_soc'] = component.get_max_soc()
                case_data.loc[k, 'initial_soc'] = component.get_initial_soc()
                case_data.loc[k, 'charging_efficiency'] = component.get_charging_efficiency()
                case_data.loc[k, 'discharging_efficiency'] = component.get_discharging_efficiency()
                case_data.loc[k, 'leakage'] = component.get_leakage()
                case_data.loc[k, 'ratio_capacity_p'] = component.get_ratio_capacity_p()
                case_data.loc[k, 'limited_storage'] = component.is_limited()
                case_data.loc[k, 'storage_limiting_component'] = component.get_storage_limiting_component()
                case_data.loc[k, 'storage_limiting_component_ratio'] = component.get_storage_limiting_component_ratio()

            case_data.loc[k, 'taxes_and_insurance'] = self.pm_object_copy\
                .get_applied_parameter_for_component('taxes_and_insurance', component.get_name())
            case_data.loc[k, 'personnel_costs'] = self.pm_object_copy\
                .get_applied_parameter_for_component('personnel_costs', component.get_name())
            case_data.loc[k, 'overhead'] = self.pm_object_copy\
                .get_applied_parameter_for_component('overhead', component.get_name())
            case_data.loc[k, 'working_capital'] = self.pm_object_copy\
                .get_applied_parameter_for_component('working_capital', component.get_name())

            k += 1

        for component in self.pm_object_copy.get_specific_components('final', 'conversion'):

            inputs = component.get_inputs()
            for i in [*inputs.keys()]:
                case_data.loc[k, 'type'] = 'input'
                case_data.loc[k, 'component'] = component.get_name()
                case_data.loc[k, 'input_stream'] = i
                case_data.loc[k, 'coefficient'] = inputs[i]

                if i == component.get_main_input():
                    case_data.loc[k, 'main_input'] = True
                else:
                    case_data.loc[k, 'main_input'] = False

                k += 1

            outputs = component.get_outputs()
            for o in [*outputs.keys()]:
                case_data.loc[k, 'type'] = 'output'
                case_data.loc[k, 'component'] = component.get_name()
                case_data.loc[k, 'output_stream'] = o
                case_data.loc[k, 'coefficient'] = outputs[o]

                if o == component.get_main_output():
                    case_data.loc[k, 'main_output'] = True
                else:
                    case_data.loc[k, 'main_output'] = False

                k += 1

        for stream in self.pm_object_copy.get_specific_streams('final'):

            case_data.loc[k, 'type'] = 'stream'
            case_data.loc[k, 'name'] = stream.get_name()
            case_data.loc[k, 'nice_name'] = stream.get_nice_name()
            case_data.loc[k, 'unit'] = stream.get_unit()

            case_data.loc[k, 'available'] = stream.is_available()
            case_data.loc[k, 'emitted'] = stream.is_emittable()
            case_data.loc[k, 'purchasable'] = stream.is_purchasable()
            case_data.loc[k, 'saleable'] = stream.is_saleable()
            case_data.loc[k, 'demanded'] = stream.is_demanded()
            case_data.loc[k, 'total_demand'] = stream.is_total_demand()
            case_data.loc[k, 'final'] = stream.is_final()

            # Purchasable streams
            case_data.loc[k, 'purchase_price_type'] = stream.get_purchase_price_type()
            case_data.loc[k, 'purchase_price'] = stream.get_purchase_price()

            # Saleable streams
            case_data.loc[k, 'selling_price_type'] = stream.get_sale_price_type()
            case_data.loc[k, 'selling_price'] = stream.get_sale_price()

            # Demand
            case_data.loc[k, 'demand'] = stream.get_demand()

            k += 1

        for abbreviation in self.pm_object_copy.get_all_abbreviations():
            case_data.loc[k, 'type'] = 'names'
            case_data.loc[k, 'abbreviation'] = abbreviation
            case_data.loc[k, 'nice_name'] = self.pm_object_copy.get_nice_name(abbreviation)

            k += 1

        if name is None:
            # dd/mm/YY H:M:S
            now = datetime.now()
            dt_string = now.strftime("%d%m%Y_%H%M%S")

            path_name = self.path_settings + "/" + dt_string + ".xlsx"
        else:
            path_name = self.path_settings + "/" + name + ".xlsx"

            self.root.title(name)

        case_data.to_excel(path_name, index=True)

    def optimize(self):

        optimization_problem = OptimizationProblem(self.pm_object_copy, self.path_data, self.solver)

        self.analyze_results(optimization_problem)

    def analyze_results(self, optimization_problem):

        result = Result(optimization_problem, self.path_result, self.path_data)

    def get_data_template(self):

        os.system('start "excel" "data_template.xlsx"')

    def cancel(self):

        self.root.destroy()

        from _helpers_gui import SettingWindow
        from os import walk
        from parameter_object import ParameterObject
        from optimization_classes_and_methods import OptimizationProblem
        from analysis_classes_and_methods import Result

        setting_window = SettingWindow()

        if setting_window.go_on:

            path_data = setting_window.folder_data
            path_result = setting_window.folder_result
            path_settings = setting_window.folder_settings
            solver = setting_window.solver

            if setting_window.radiobutton_variable.get() == 'new':

                interface = Interface(path_data=path_data, path_result=path_result,
                                      path_settings=path_settings, solver=solver)

            elif setting_window.radiobutton_variable.get() == 'custom':

                path_custom = setting_window.selected_custom
                interface = Interface(path_data=path_data, path_result=path_result,
                                      path_settings=path_settings,
                                      path_custom=path_custom, solver=solver)

                custom_title = path_custom.split('/')[-1].split('.')[0]
                self.root.title(custom_title)

            elif setting_window.radiobutton_variable.get() == 'optimize_only':

                path_to_settings = setting_window.folder_optimize

                # Get path of every object in folder
                _, _, filenames = next(walk(path_to_settings))

                for file in filenames:
                    file = file.split('/')[0]

                    print('Currently optimized: ' + file)

                    path = path_to_settings + file
                    file_without_ending = file.split('.')[0]

                    pm_object = ParameterObject('parameter', integer_steps=10)
                    case_data = pd.read_excel(path, index_col=0)
                    pm_object = load_setting(pm_object, case_data)

                    optimization_problem = OptimizationProblem(pm_object, path_data=path_data, solver=solver)
                    result = Result(optimization_problem, path_result, path_data, file_without_ending)



