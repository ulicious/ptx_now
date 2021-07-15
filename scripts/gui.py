import os

import tkinter as tk
from tkinter import *
from tkinter import ttk
import pandas as pd
from datetime import datetime

from _helpers_gui import ToggledFrame
from optimization_classes_and_methods import OptimizationProblem
from analysis_classes_and_methods import Result
from objects_formulation import ParameterObject


class Interface:

    def __init__(self, path_data, path_result, path_settings, solver, path_custom=None):

        self.path_data = path_data
        self.path_result = path_result
        self.path_settings = path_settings
        self.path_custom = path_custom
        self.working_path = os.getcwd()
        self.solver = solver

        if self.path_custom is None:

            self.pm_object_original = ParameterObject('parameter', integer_steps=10)
            self.pm_object_copy = ParameterObject('parameter2', integer_steps=10)
        else:
            self.pm_object_original = ParameterObject('parameter', path_custom=self.path_custom, integer_steps=10)
            self.pm_object_copy = ParameterObject('parameter2', path_custom=self.path_custom, integer_steps=10)

        self.root = Tk()
        self.root.geometry('500x750')

        self.me_checked = False

        self.general_parameters_df = pd.DataFrame()
        self.components_df = pd.DataFrame()
        self.streams_df = pd.DataFrame()
        self.storages_df = pd.DataFrame()
        self.generators_df = pd.DataFrame()

        self.widgets()
        if False:
            self.save_current_parameters_and_options()

    def widgets(self):

        self.canvas = tk.Canvas(self.root)
        self.scrollbar = ttk.Scrollbar(self.root, orient="vertical")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.canvas.yview)

        self.scrollable_frame = ttk.Frame(self.canvas)
        interior_id = self.canvas.create_window(0, 0, window=self.scrollable_frame, anchor=NW)

        def _configure_interior(event):
            # update the scrollbars to match the size of the inner frame
            size = (self.scrollable_frame.winfo_reqwidth(), self.scrollable_frame.winfo_reqheight())
            self.canvas.config(scrollregion="0 0 %s %s" % size)
            if self.scrollable_frame.winfo_reqwidth() != self.canvas.winfo_width():
                # update the canvas's width to fit the inner frame
                self.canvas.config(width=self.scrollable_frame.winfo_reqwidth())
        self.scrollable_frame.bind('<Configure>', _configure_interior)

        def _configure_canvas(event):
            if self.scrollable_frame.winfo_reqwidth() != self.canvas.winfo_width():
                # update the inner frame's width to fill the canvas
                self.canvas.itemconfigure(interior_id, width=self.canvas.winfo_width())
        self.canvas.bind('<Configure>', _configure_canvas)

        self.t1 = ToggledFrame(self, self.root, self.scrollable_frame, text='General assumptions',
                               pm_object_original=self.pm_object_original, pm_object_copy=self.pm_object_copy,
                               frame_type='general', relief="raised", borderwidth=1)
        self.t1.pack(fill="x", expand=1, pady=2, padx=2, anchor="n")

        self.t2 = ToggledFrame(self, self.root, self.scrollable_frame, text='Components',
                               pm_object_original=self.pm_object_original, pm_object_copy=self.pm_object_copy,
                               frame_type='component', relief="raised", borderwidth=1)
        self.t2.pack(fill="x", expand=1, pady=2, padx=2, anchor="n")

        self.t3 = ToggledFrame(self, self.root, self.scrollable_frame, text='Streams',
                               pm_object_original=self.pm_object_original, pm_object_copy=self.pm_object_copy,
                               frame_type='stream', relief="raised", borderwidth=1)
        self.t3.pack(fill="x", expand=1, pady=2, padx=2, anchor="n")

        self.t4 = ToggledFrame(self, self.root, self.scrollable_frame, text='Storage',
                               pm_object_original=self.pm_object_original, pm_object_copy=self.pm_object_copy,
                               frame_type='storage', relief="raised", borderwidth=1)
        self.t4.pack(fill="x", expand=1, pady=2, padx=2, anchor="n")

        self.t5 = ToggledFrame(self, self.root, self.scrollable_frame, text='Generators',
                               pm_object_original=self.pm_object_original, pm_object_copy=self.pm_object_copy,
                               frame_type='generator', relief="raised", borderwidth=1)
        self.t5.pack(fill="x", expand=1, pady=2, padx=2, anchor="n")

        button_frame = ttk.Frame(self.scrollable_frame)

        self.check_streams_button = ttk.Button(button_frame, text='Check settings', command=self.check_all_settings)
        self.check_streams_button.grid(row=0, column=0, sticky='ew')

        self.save_settings = ttk.Button(button_frame, text='Save settings', command=self.save_setting_window)
        self.save_settings.grid(row=0, column=1, sticky='ew')

        self.optimize_button = ttk.Button(button_frame, text='Optimize', state=DISABLED, command=self.optimize)
        self.optimize_button.grid(row=0, column=2, sticky='ew')

        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        button_frame.grid_columnconfigure(2, weight=1)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y", expand=False)
        button_frame.pack(fill="both", expand=True)

        self.scrollable_frame.grid_rowconfigure(0, weight=1)
        self.scrollable_frame.grid_columnconfigure(0, weight=1)

        self.root.mainloop()

    def update_widgets(self):
        # Simply recreate the frames with the new pm object

        self.t1.update_self_pm_object(self.pm_object_copy)
        self.t1.update_frame(self.t1.frame_type)

        self.t2.update_self_pm_object(self.pm_object_copy)
        self.t2.update_frame(self.t2.frame_type)

        self.t3.update_self_pm_object(self.pm_object_copy)
        self.t3.update_frame(self.t3.frame_type)

        self.t4.update_self_pm_object(self.pm_object_copy)
        self.t4.update_frame(self.t4.frame_type)

        self.t5.update_self_pm_object(self.pm_object_copy)
        self.t5.update_frame(self.t5.frame_type)

        self.optimize_button.config(state=DISABLED)

    def check_all_settings(self):

        def kill_window():
            alert_window.destroy()

        valid_me_for_stream = {}
        streams_without_well = []
        streams_without_sink = []

        for stream in self.pm_object_copy.get_specific_streams('final'):

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
                    main_conversions = component.get_main_conversion()
                    if main_conversions.loc['output_me'] == stream.get_name():
                        well_existing = True
                        break

                    if not well_existing:
                        side_conversions = component.get_side_conversions()
                        for i in side_conversions.index:
                            if side_conversions.loc[i, 'output_me'] == stream.get_name():
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
                    main_conversions = component.get_main_conversion()
                    if main_conversions.loc['input_me'] == stream.get_name():
                        sink_existing = True
                        break

                    if not sink_existing:
                        side_conversions = component.get_side_conversions()
                        for i in side_conversions.index:
                            if side_conversions.loc[i, 'input_me'] == stream.get_name():
                                sink_existing = True
                                break

            if not sink_existing:
                streams_without_sink.append(stream.get_name())

            if well_existing & sink_existing:
                valid_me_for_stream.update({stream.get_name(): True})
            else:
                valid_me_for_stream.update({stream.get_name(): False})

        all_streams_valid = True
        for stream in self.pm_object_copy.get_specific_streams('final'):
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
                             text='It is important that every stream has a well. That means that it is either generated, converted from another stream, freely available or purchasable. \n Please adjust your conversions or the indivdual stream').pack()
                    tk.Label(alert_window, text='').pack()

                if no_sink_text != '':

                    tk.Label(alert_window, text=no_sink_text).pack()
                    tk.Label(alert_window,
                             text='It is important that every stream has a sink. That means that it is either converted to another stream, emitted, saleable or implemented as demand. \n Please adjust your conversions or the indivdual stream').pack()
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

            tk.Button(alert_window, text='OK', command=kill_window).pack()
        else:
            self.optimize_button.config(state=NORMAL)

    def save_setting_window(self): #Todo: Only save when closed or optimized

        def kill_window_and_save():
            self.save_current_parameters_and_options(name_entry.get())
            newWindow.destroy()

        newWindow = Toplevel(self.root)

        Label(newWindow, text='Enter name of settings file').pack()

        name_entry = Entry(newWindow)
        name_entry.pack()

        Button(newWindow, text='Save', command=kill_window_and_save).pack()

    def save_current_parameters_and_options(self, name=None):

        case_data = pd.DataFrame()

        k = 0

        for parameter in self.pm_object_copy.get_general_parameters():
            value = self.pm_object_copy.get_general_parameter_value(parameter)

            case_data.loc[k, 'type'] = 'general_parameter'
            case_data.loc[k, 'parameter'] = parameter
            case_data.loc[k, 'value'] = value

            k += 1

        for component in self.pm_object_copy.get_all_components():

            case_data.loc[k, 'type'] = 'component'
            case_data.loc[k, 'component_type'] = component.get_component_type()
            case_data.loc[k, 'final'] = component.is_final()
            case_data.loc[k, 'name'] = component.get_name()
            case_data.loc[k, 'nice_name'] = component.get_nice_name()
            case_data.loc[k, 'capex'] = component.get_capex()
            case_data.loc[k, 'capex_unit'] = component.get_capex_unit()
            case_data.loc[k, 'lifetime'] = component.get_lifetime()
            case_data.loc[k, 'maintenance'] = component.get_maintenance()

            if component.get_component_type() == 'conversion':

                case_data.loc[k, 'min_p'] = component.get_min_p()
                case_data.loc[k, 'max_p'] = component.get_max_p()
                case_data.loc[k, 'ramp_up'] = component.get_ramp_up()
                case_data.loc[k, 'ramp_down'] = component.get_ramp_down()
                case_data.loc[k, 'shut_down_ability'] = component.get_shut_down_ability()
                case_data.loc[k, 'shut_down_time'] = component.get_shut_down_time()
                case_data.loc[k, 'start_up_time'] = component.get_start_up_time()
                case_data.loc[k, 'scalable'] = component.is_scalable()
                case_data.loc[k, 'base_investment'] = component.get_base_investment()
                case_data.loc[k, 'base_capacity'] = component.get_base_capacity()
                case_data.loc[k, 'economies_of_scale'] = component.get_economies_of_scale()
                case_data.loc[k, 'max_capacity_economies_of_scale'] = component.get_max_capacity_economies_of_scale()
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
            main_conversion = component.get_main_conversion()
            case_data.loc[k, 'type'] = 'main_conversion'
            case_data.loc[k, 'component'] = component.get_name()
            case_data.loc[k, 'input_stream'] = main_conversion['input_me']
            case_data.loc[k, 'output_stream'] = main_conversion['output_me']
            case_data.loc[k, 'coefficient'] = main_conversion['coefficient']

            k += 1

            side_conversions = component.get_side_conversions()
            for i in side_conversions.index:
                case_data.loc[k, 'type'] = 'side_conversion'
                case_data.loc[k, 'component'] = component.get_name()
                case_data.loc[k, 'input_stream'] = side_conversions.loc[i, 'input_me']
                case_data.loc[k, 'output_stream'] = side_conversions.loc[i, 'output_me']
                case_data.loc[k, 'coefficient'] = side_conversions.loc[i, 'coefficient']

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
            case_data.loc[k, 'storable'] = stream.is_storable()

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

        case_data.to_excel(path_name, index=True)

    def optimize(self):

        optimization_problem = OptimizationProblem(self.pm_object_copy, self.path_data, self.solver)

        self.analyze_results(optimization_problem)

    def analyze_results(self, optimization_problem):

        result = Result(optimization_problem, self.path_result)



