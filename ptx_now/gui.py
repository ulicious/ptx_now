import os

import tkinter as tk
from tkinter import *
from tkinter import ttk
import pandas as pd
from datetime import datetime

from _helpers_gui import AssumptionsInterface, ComponentInterface, CommodityInterface, StorageInterface,\
    GeneratorInterface, DataInterface
from optimization_classes_and_methods import OptimizationProblem
from analysis_classes_and_methods import Result
from _helpers_visualization import create_visualization
from parameter_object import ParameterObject
from load_projects import load_setting

from os import walk


class Interface:

    def __init__(self, path_data, path_result, path_projects, solver, path_optimize=None):

        self.path_data = path_data
        self.path_result = path_result
        self.path_projects = path_projects
        self.path_optimize = path_optimize
        self.working_path = os.getcwd()
        self.solver = solver

        self.root = Tk()
        try:
            ttk.Style().theme_use('vista')
        except:
            pass

        if self.path_optimize is None:  # New project

            self.pm_object_original = ParameterObject('parameter', integer_steps=10, path_data=path_data)
            self.pm_object_original.create_new_project()

            self.pm_object_copy = ParameterObject('parameter2', integer_steps=10, path_data=path_data)
            self.pm_object_copy.create_new_project()

            self.root.title('New Project')
            self.project_name = None

        else:  # Custom project

            custom_title = self.path_optimize.split('/')[-1].split('.')[0]
            self.root.title(custom_title)
            self.project_name = custom_title

            self.pm_object_original = ParameterObject('parameter', integer_steps=10,
                                                      path_data=path_data, project_name=custom_title)
            self.pm_object_copy = ParameterObject('parameter2', integer_steps=10,
                                                  path_data=path_data, project_name=custom_title)

            path = self.path_projects + '/' + self.path_optimize
            case_data = pd.read_excel(path, index_col=0)

            self.pm_object_original = load_setting(self.pm_object_original, case_data)
            self.pm_object_copy = load_setting(self.pm_object_copy, case_data)

        self.me_checked = False  # boolean if mass energy balance was checked

        self.general_parameters_df = pd.DataFrame()
        self.components_df = pd.DataFrame()
        self.commodities_df = pd.DataFrame()
        self.storages_df = pd.DataFrame()
        self.generators_df = pd.DataFrame()

        self.widgets()

    def widgets(self):

        self.overall_notebook = ttk.Notebook(self.root)

        self.general_assumptions = AssumptionsInterface(self, self.overall_notebook,
                                                pm_object_original=self.pm_object_original,
                                                pm_object_copy=self.pm_object_copy,)
        self.general_assumptions.pack(fill='both', expand=True)

        self.components = ComponentInterface(self, self.overall_notebook,
                                             pm_object_original=self.pm_object_original,
                                             pm_object_copy=self.pm_object_copy)
        self.components.pack(fill='both', expand=True)

        self.commodities = CommodityInterface(self, self.overall_notebook,
                                       pm_object_original=self.pm_object_original,
                                       pm_object_copy=self.pm_object_copy)
        self.commodities.pack(fill='both', expand=True)

        self.storages = StorageInterface(self, self.overall_notebook,
                                         pm_object_original=self.pm_object_original,
                                         pm_object_copy=self.pm_object_copy)
        self.storages.pack(fill='both', expand=True)

        self.generators = GeneratorInterface(self, self.overall_notebook,
                                             pm_object_original=self.pm_object_original,
                                             pm_object_copy=self.pm_object_copy)
        self.generators.pack(fill='both', expand=True)

        self.data = DataInterface(self, self.overall_notebook,
                                  pm_object_original=self.pm_object_original,
                                  pm_object_copy=self.pm_object_copy)
        self.data.pack(fill='both', expand=True)

        self.overall_notebook.add(self.general_assumptions, text='General Assumptions')
        self.overall_notebook.add(self.components, text='Components')
        self.overall_notebook.add(self.commodities, text='Commodities')
        self.overall_notebook.add(self.storages, text='Storages')
        self.overall_notebook.add(self.generators, text='Generators')
        self.overall_notebook.add(self.data, text='Data')

        self.overall_notebook.pack(pady=10, expand=True, anchor='n')

        button_frame = ttk.Frame(self.root)

        check_commodities_button = ttk.Button(button_frame, text='Check settings', command=self.check_all_settings)
        check_commodities_button.grid(row=0, column=0, sticky='ew')

        self.optimize_button = ttk.Button(button_frame, text='Optimize', state=DISABLED, command=self.optimize)
        self.optimize_button.grid(row=0, column=1, sticky='ew')

        save_settings = ttk.Button(button_frame, text='Save settings', command=self.save_setting_window)
        save_settings.grid(row=1, column=0, sticky='ew')

        return_to_start = ttk.Button(button_frame, text='Cancel', command=self.cancel)
        return_to_start.grid(row=1, column=1, sticky='ew')

        button_frame.grid_columnconfigure(0, weight=1, uniform='a')
        button_frame.grid_columnconfigure(1, weight=1, uniform='a')

        button_frame.pack(fill="both", expand=True)

        self.root.mainloop()

    def update_widgets(self):
        # Simply recreate the frames with the new pm object

        self.general_assumptions.update_self_pm_object(self.pm_object_copy)
        self.general_assumptions.update_frame()

        self.components.update_self_pm_object(self.pm_object_copy)
        self.components.update_frame()

        self.commodities.update_self_pm_object(self.pm_object_copy)
        self.commodities.update_frame()

        self.storages.update_self_pm_object(self.pm_object_copy)
        self.storages.update_frame()

        self.generators.update_self_pm_object(self.pm_object_copy)
        self.generators.update_frame()

        self.data.update_self_pm_object(self.pm_object_copy)
        self.data.update_frame()

        self.optimize_button.config(state=DISABLED)

    def check_all_settings(self):

        def kill_window():
            alert_window.destroy()

        valid_me_for_commodity = {}
        commodities_without_well = []
        commodities_without_sink = []
        profile_not_exist = []

        if not self.pm_object_copy.get_market_data_status():
            try:
                sell_purchase_profile = pd.read_excel(self.path_data + self.pm_object_copy.get_market_data(),
                                                      index_col=0)
            except:
                sell_purchase_profile = None
        else:
            sell_purchase_profile = None

        for commodity in self.pm_object_copy.get_final_commodities_objects():

            well_existing = False
            sink_existing = False

            # Check if commodity has a well
            if commodity.is_available():
                well_existing = True
            elif commodity.is_purchasable():

                if commodity.get_purchase_price_type() == 'variable':
                    profile_exists = False
                    if sell_purchase_profile is not None:
                        for c in sell_purchase_profile.columns:
                            if c.split('_')[0] == commodity.get_nice_name():
                                profile_exists = True

                    if not profile_exists:
                        profile_not_exist.append(commodity.get_nice_name())

                well_existing = True

            # If no well exists, the commodity has to be generated or converted from other commodity
            if not well_existing:
                for component in self.pm_object_copy.get_final_conversion_components_objects():
                    outputs = component.get_outputs()
                    for o in [*outputs.keys()]:
                        if o == commodity.get_name():
                            well_existing = True
                            break

            if not well_existing:
                for component in self.pm_object_copy.get_final_generator_components_objects():
                    if commodity.get_name() == component.get_generated_commodity():
                        well_existing = True
                        break

            if not well_existing:
                commodities_without_well.append(commodity.get_name())

            # Check if commodity has a sink
            if commodity.is_emittable():
                sink_existing = True
            elif commodity.is_saleable():
                sink_existing = True

                if commodity.get_sale_price_type() == 'variable':
                    profile_exists = False
                    if sell_purchase_profile is not None:
                        for c in sell_purchase_profile.columns:
                            if c.split('_')[0] == commodity.get_nice_name():
                                profile_exists = True

                    if not profile_exists:
                        profile_not_exist.append(commodity.get_nice_name())

            elif commodity.is_demanded():
                sink_existing = True

            # If no well exists, the commodity has to be generated or converted from other commodity
            if not sink_existing:
                for component in self.pm_object_copy.get_final_conversion_components_objects():
                    inputs = component.get_inputs()
                    for i in [*inputs.keys()]:
                        if i == commodity.get_name():
                            sink_existing = True
                            break

            if not sink_existing:
                commodities_without_sink.append(commodity.get_name())

            if well_existing & sink_existing:
                valid_me_for_commodity.update({commodity.get_name(): True})
            else:
                valid_me_for_commodity.update({commodity.get_name(): False})

        all_commodities_valid = True
        for commodity in self.pm_object_copy.get_final_commodities_objects():
            if not valid_me_for_commodity[commodity.get_name()]:
                all_commodities_valid = False

        # Check if a profile for the generation unit exists, if generation unit is enabled
        profiles_exist = True
        if len(self.pm_object_copy.get_final_generator_components_names()) > 0:
            if self.pm_object_copy.get_generation_data_status():
                generation_profile = pd.read_excel(self.path_data + self.pm_object_copy.get_generation_data(), index_col=0)
            else:
                path_to_generation_files = self.path_data + '/' + self.pm_object_copy.get_generation_data()
                _, _, filenames = next(walk(path_to_generation_files))
                generation_profile = pd.read_excel(path_to_generation_files + '/' + filenames[0], index_col=0)

            for generator in self.pm_object_copy.get_final_generator_components_objects():
                if generator.get_nice_name() not in generation_profile.columns:
                    profiles_exist = False
                    profile_not_exist.append(generator.get_nice_name())

        error_in_setting = False
        if (not profiles_exist) | (not all_commodities_valid):
            error_in_setting = True

        if error_in_setting:
            self.optimize_button.config(state=DISABLED)
            alert_window = Toplevel(self.root)
            alert_window.title('')

            if not all_commodities_valid:

                no_well_text = ''
                no_sink_text = ''

                if len(commodities_without_well) > 0:

                    if len(commodities_without_well) == 1:
                        no_well_text = 'The following commodity has no well: '
                    else:
                        no_well_text = 'The following commodities have no well: '

                    for commodity in commodities_without_well:
                        if commodities_without_well.index(commodity) != len(commodities_without_well) - 1:
                            no_well_text += self.pm_object_copy.get_nice_name(commodity) + ', '
                        else:
                            no_well_text += self.pm_object_copy.get_nice_name(commodity)

                if len(commodities_without_sink) > 0:

                    if len(commodities_without_well) == 1:
                        no_sink_text = 'The following commodity has no sink: '
                    else:
                        no_sink_text = 'The following commodities have no sink: '

                    for commodity in commodities_without_sink:
                        if commodities_without_sink.index(commodity) != len(commodities_without_sink) - 1:
                            no_sink_text += self.pm_object_copy.get_nice_name(commodity) + ', '
                        else:
                            no_sink_text += self.pm_object_copy.get_nice_name(commodity)

                if no_well_text != '':

                    tk.Label(alert_window, text=no_well_text).pack()
                    tk.Label(alert_window,
                             text='It is important that every commodity has a well. \n' +
                                  ' That means that it is either generated, converted from another commodity,' +
                                  ' freely available or purchasable. \n'
                                  ' Please adjust your inputs/outputs or the individual commodity').pack()
                    tk.Label(alert_window, text='').pack()

                if no_sink_text != '':

                    tk.Label(alert_window, text=no_sink_text).pack()
                    tk.Label(alert_window,
                             text='It is important that every commodity has a sink. \n'
                                  ' That means that it is either converted to another commodity,' +
                                  ' emitted, saleable or implemented as demand. \n' +
                                  ' Please adjust your inputs/outputs or the individual commodity').pack()
                    tk.Label(alert_window, text='').pack()

            if not profiles_exist:
                no_profile_text = 'The following generators and commodities have no profile: '

                for u in profile_not_exist:
                    if profile_not_exist.index(u) != len(profile_not_exist) - 1:
                        no_profile_text += u + ', '
                    else:
                        no_profile_text += u

                tk.Label(alert_window, text=no_profile_text).pack()
                tk.Label(alert_window,
                         text='It is important that every generator/commodity has a profile. \n'
                              ' Please adjust your generators/commodities').pack()
                tk.Label(alert_window, text='').pack()

            ttk.Button(alert_window, text='OK', command=kill_window).pack(fill='both', expand=True)
        else:
            self.optimize_button.config(state=NORMAL)

    def save_setting_window(self):

        def kill_window_and_save():

            if name_entry.get() is None:
                # dd/mm/YY H:M:S
                now = datetime.now()
                dt_string = now.strftime("%d%m%Y_%H%M%S")

                path_name = self.path_projects + "/" + dt_string + ".xlsx"
            else:
                path_name = self.path_projects + "/" + name_entry.get() + ".xlsx"

                self.root.title(name_entry.get())
                self.pm_object_copy.set_project_name(name_entry.get())

            save_current_parameters_and_options(self.pm_object_copy, path_name)
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

    def optimize(self):

        """ Optimization either with one single case or several cases
        depend on number of generation, purchase and sale data"""

        generation_data_before = self.pm_object_copy.get_generation_data()
        market_data_before = self.pm_object_copy.get_market_data()

        if len(self.pm_object_copy.get_final_generator_components_names()) > 0:
            # Case generators are used

            if self.pm_object_copy.get_market_data_needed():  # Case market data available

                if self.pm_object_copy.get_generation_data_status():  # Case single file generation

                    path_to_generation_files = self.path_data + self.pm_object_copy.get_generation_data()
                    self.pm_object_copy.set_generation_data(path_to_generation_files)

                    path_to_sell_purchase_files = self.path_data + self.pm_object_copy.get_market_data()

                    if self.pm_object_copy.get_market_data_status():  # Case single market data file

                        self.pm_object_copy.set_market_data(path_to_sell_purchase_files)

                        optimization_problem = OptimizationProblem(self.pm_object_copy, self.path_data, self.solver)

                    else:  # Case with several market data files

                        _, _, filenames_sell_purchase = next(walk(path_to_sell_purchase_files))
                        for fsp in filenames_sell_purchase:
                            self.pm_object_copy.set_market_data(path_to_sell_purchase_files + '/' + fsp)

                            optimization_problem = OptimizationProblem(self.pm_object_copy, self.path_data, self.solver)

                else:  # Case several generation files
                    path_to_generation_files = self.path_data + self.pm_object_copy.get_generation_data()
                    path_to_sell_purchase_files = self.path_data + self.pm_object_copy.get_market_data()

                    if self.pm_object_copy.get_market_data_status():
                        # Case with several generation profiles but only one market profile

                        self.pm_object_copy.set_market_data(path_to_sell_purchase_files)

                        _, _, filenames_generation = next(walk(path_to_generation_files))
                        for fg in filenames_generation:
                            self.pm_object_copy.set_generation_data(path_to_generation_files + '/' + fg)

                            optimization_problem = OptimizationProblem(self.pm_object_copy, self.path_data, self.solver)
                    else:
                        # Case with several generation and purchase/sale profiles

                        _, _, filenames_generation = next(walk(path_to_generation_files))
                        _, _, filenames_sell_purchase = next(walk(path_to_sell_purchase_files))
                        for fg in filenames_generation:
                            for fsp in filenames_sell_purchase:
                                self.pm_object_copy.set_generation_data(path_to_generation_files + '/' + fg)

                                self.pm_object_copy.set_market_data(path_to_sell_purchase_files + '/' + fsp)

                                optimization_problem = OptimizationProblem(self.pm_object_copy, self.path_data,
                                                                           self.solver)

            else:  # Case no market data
                if self.pm_object_copy.get_generation_data_status():  # Case only generation with single file

                    path_to_generation_files = self.path_data + self.pm_object_copy.get_generation_data()
                    self.pm_object_copy.set_generation_data(path_to_generation_files)

                    optimization_problem = OptimizationProblem(self.pm_object_copy, self.path_data, self.solver)

                else:  # Case only generation with several files
                    path_to_generation_files = self.path_data + self.pm_object_copy.get_generation_data()

                    _, _, filenames_generation = next(walk(path_to_generation_files))
                    for fg in filenames_generation:
                        self.pm_object_copy.set_generation_data(path_to_generation_files + '/' + fg)

                        optimization_problem = OptimizationProblem(self.pm_object_copy, self.path_data, self.solver)

        else:  # Case generators are not used

            if self.pm_object_copy.get_market_data_needed():
                if self.pm_object_copy.get_market_data_status():
                    #  one case
                    optimization_problem = OptimizationProblem(self.pm_object_copy, self.path_data, self.solver)
                else:
                    # Case with several purchase and selling price data
                    path_to_sell_purchase_files = self.path_data + self.pm_object_copy.get_market_data()

                    _, _, filenames_sell_purchase = next(walk(path_to_sell_purchase_files))
                    for fsp in filenames_sell_purchase:
                        self.pm_object_copy.set_market_data(path_to_sell_purchase_files + '/' + fsp)

                        optimization_problem = OptimizationProblem(self.pm_object_copy, self.path_data, self.solver)

            else:
                optimization_problem = OptimizationProblem(self.pm_object_copy, self.path_data, self.solver)

        self.pm_object_copy.set_generation_data(generation_data_before)
        self.pm_object_copy.set_market_data(market_data_before)
        self.analyze_results(optimization_problem)

    def analyze_results(self, optimization_problem):

        result = Result(optimization_problem, self.path_result)
        save_current_parameters_and_options(self.pm_object_copy, result.new_result_folder + '/7_settings.xlsx')

    def cancel(self):

        self.root.destroy()

        from _helpers_gui import SettingWindow
        from os import walk
        from parameter_object import ParameterObject
        from optimization_classes_and_methods import OptimizationProblem
        from analysis_classes_and_methods import Result

        setting_window = SettingWindow()

        if setting_window.go_on:

            path_data = setting_window.path_data
            path_result = setting_window.path_result
            path_projects = setting_window.path_projects
            path_optimize = setting_window.path_optimize
            solver = setting_window.solver
            path_visualization = setting_window.path_visualization

            if setting_window.optimize_or_visualize_projects_variable.get() == 'optimize':

                if setting_window.optimize_variable.get() == 'new':

                    Interface(path_data=path_data, path_result=path_result, path_projects=path_projects, solver=solver)

                elif setting_window.optimize_variable.get() == 'custom':
                    Interface(path_data=path_data, path_result=path_result, path_projects=path_projects,
                              path_optimize=path_optimize, solver=solver)

                else:

                    path_to_settings = setting_window.path_projects + setting_window.path_optimize
                    print(path_to_settings)

                    # Get path of every object in folder
                    _, _, filenames = next(walk(path_to_settings))

                    for file in filenames:
                        file = file.split('/')[0]

                        print('Currently optimized: ' + file)

                        path = path_to_settings + '/' + file
                        file_without_ending = file.split('.')[0]

                        pm_object = ParameterObject('parameter', integer_steps=10)
                        case_data = pd.read_excel(path, index_col=0)
                        pm_object = load_setting(pm_object, case_data)
                        pm_object.set_project_name(file_without_ending)

                        optimization_problem = OptimizationProblem(pm_object, path_data=path_data, solver=solver)
                        Result(optimization_problem, path_result)

            else:

                path_visualization = path_result + path_visualization + '/'
                create_visualization(path_visualization)


def save_current_parameters_and_options(pm_object, path_name):

    case_data = pd.DataFrame()

    k = 0

    case_data.loc[k, 'version'] = '0.0.7'

    k += 1

    for parameter in pm_object.get_general_parameters():
        value = pm_object.get_general_parameter_value(parameter)

        case_data.loc[k, 'type'] = 'general_parameter'
        case_data.loc[k, 'parameter'] = parameter
        case_data.loc[k, 'value'] = value

        k += 1

    case_data.loc[k, 'type'] = 'representative_periods'
    case_data.loc[k, 'representative_periods'] = pm_object.get_uses_representative_periods()
    case_data.loc[k, 'representative_periods_length'] = pm_object.get_representative_periods_length()
    case_data.loc[k, 'path_weighting'] = pm_object.get_path_weighting()
    case_data.loc[k, 'covered_period'] = pm_object.get_covered_period()

    k += 1

    case_data.loc[k, 'type'] = 'monetary_unit'
    case_data.loc[k, 'monetary_unit'] = pm_object.get_monetary_unit()

    k += 1

    case_data.loc[k, 'type'] = 'generation_data'
    case_data.loc[k, 'single_profile'] = pm_object.get_generation_data_status()
    case_data.loc[k, 'generation_data'] = pm_object.get_generation_data()

    k += 1

    case_data.loc[k, 'type'] = 'market_data'
    case_data.loc[k, 'single_profile'] = pm_object.get_market_data_status()
    case_data.loc[k, 'market_data'] = pm_object.get_market_data()

    k += 1

    for component in pm_object.get_all_components():

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
                case_data.loc[k, 'start_up_costs'] = component.get_start_up_costs()
            else:
                case_data.loc[k, 'start_up_time'] = 0
                case_data.loc[k, 'start_up_costs'] = 0

            case_data.loc[k, 'hot_standby_ability'] = component.get_hot_standby_ability()
            if component.get_hot_standby_ability():
                case_data.loc[k, 'hot_standby_commodity'] = [*component.get_hot_standby_demand().keys()][0]
                case_data.loc[k, 'hot_standby_demand'] = component.get_hot_standby_demand()[
                    [*component.get_hot_standby_demand().keys()][0]]
                case_data.loc[k, 'hot_standby_startup_time'] = component.get_hot_standby_startup_time()
            else:
                case_data.loc[k, 'hot_standby_commodity'] = ''
                case_data.loc[k, 'hot_standby_demand'] = 0
                case_data.loc[k, 'hot_standby_startup_time'] = 0

            case_data.loc[k, 'number_parallel_units'] = component.get_number_parallel_units()

        elif component.get_component_type() == 'generator':

            case_data.loc[k, 'generated_commodity'] = component.get_generated_commodity()
            case_data.loc[k, 'curtailment_possible'] = component.get_curtailment_possible()

        elif component.get_component_type() == 'storage':

            case_data.loc[k, 'min_soc'] = component.get_min_soc()
            case_data.loc[k, 'max_soc'] = component.get_max_soc()
            case_data.loc[k, 'initial_soc'] = component.get_initial_soc()
            case_data.loc[k, 'charging_efficiency'] = component.get_charging_efficiency()
            case_data.loc[k, 'discharging_efficiency'] = component.get_discharging_efficiency()
            case_data.loc[k, 'leakage'] = component.get_leakage()
            case_data.loc[k, 'ratio_capacity_p'] = component.get_ratio_capacity_p()

        case_data.loc[k, 'taxes_and_insurance'] = pm_object\
            .get_applied_parameter_for_component('taxes_and_insurance', component.get_name())
        case_data.loc[k, 'personnel_costs'] = pm_object\
            .get_applied_parameter_for_component('personnel_costs', component.get_name())
        case_data.loc[k, 'overhead'] = pm_object\
            .get_applied_parameter_for_component('overhead', component.get_name())
        case_data.loc[k, 'working_capital'] = pm_object\
            .get_applied_parameter_for_component('working_capital', component.get_name())

        k += 1

    for component in pm_object.get_final_conversion_components_objects():

        inputs = component.get_inputs()
        for i in [*inputs.keys()]:
            case_data.loc[k, 'type'] = 'input'
            case_data.loc[k, 'component'] = component.get_name()
            case_data.loc[k, 'input_commodity'] = i
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
            case_data.loc[k, 'output_commodity'] = o
            case_data.loc[k, 'coefficient'] = outputs[o]

            if o == component.get_main_output():
                case_data.loc[k, 'main_output'] = True
            else:
                case_data.loc[k, 'main_output'] = False

            k += 1

    for commodity in pm_object.get_final_commodities_objects():

        case_data.loc[k, 'type'] = 'commodity'
        case_data.loc[k, 'name'] = commodity.get_name()
        case_data.loc[k, 'nice_name'] = commodity.get_nice_name()
        case_data.loc[k, 'unit'] = commodity.get_unit()

        case_data.loc[k, 'available'] = commodity.is_available()
        case_data.loc[k, 'emitted'] = commodity.is_emittable()
        case_data.loc[k, 'purchasable'] = commodity.is_purchasable()
        case_data.loc[k, 'saleable'] = commodity.is_saleable()
        case_data.loc[k, 'demanded'] = commodity.is_demanded()
        case_data.loc[k, 'total_demand'] = commodity.is_total_demand()
        case_data.loc[k, 'final'] = commodity.is_final()

        # Purchasable commodities
        case_data.loc[k, 'purchase_price_type'] = commodity.get_purchase_price_type()
        case_data.loc[k, 'purchase_price'] = commodity.get_purchase_price()

        # Saleable commodities
        case_data.loc[k, 'selling_price_type'] = commodity.get_sale_price_type()
        case_data.loc[k, 'selling_price'] = commodity.get_sale_price()

        # Demand
        case_data.loc[k, 'demand'] = commodity.get_demand()

        case_data.loc[k, 'energy_content'] = commodity.get_energy_content()

        k += 1

    for abbreviation in pm_object.get_all_abbreviations():
        case_data.loc[k, 'type'] = 'names'
        case_data.loc[k, 'name'] = abbreviation
        case_data.loc[k, 'nice_name'] = pm_object.get_nice_name(abbreviation)

        k += 1

    case_data.to_excel(path_name, index=True)
