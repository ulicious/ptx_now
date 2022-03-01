import tkinter as tk
from tkinter import *
from tkinter import ttk
from tkinter import filedialog

import pandas as pd

from general_assumptions_classes_and_methods import GeneralAssumptionsFrame
from component_classes_and_methods import ComponentFrame, AddNewComponentWindow
from commodities_classes_and_methods import CommodityFrame
from storage_classes_and_methods import StorageFrame
from generators_classes_and_methods import GeneratorFrame

from components import GenerationComponent, StorageComponent

import os

from datetime import datetime


class AssumptionsInterface(ttk.Frame):

    def update_self_pm_object(self, pm_object):
        # Updates the Parameter object
        self.pm_object_copy = pm_object

    def update_frame(self):
        # If changes in parameters etc. occur, the whole frame is updated so that updates are shown immediately
        self.parameter_frame.frame.destroy()
        self.parameter_frame = GeneralAssumptionsFrame(self, self.parent, self.general_assumptions_frame,
                                                       self.pm_object_copy)

    def set_general_assumptions_to_default(self):
        # Set general assumption parameters to default

        for p in self.pm_object_copy.get_general_parameters():
            self.pm_object_copy.set_general_parameter_value(p, self.pm_object_original.get_general_parameter_value(p))

            if p == 'wacc':
                continue

            for c in self.pm_object_copy.get_final_components_objects():
                self.pm_object_copy.set_applied_parameter_for_component(p,
                                                                        c.get_name(),
                                                                        self.pm_object_original
                                                                        .get_applied_parameter_for_component(p,
                                                                                                             c.get_name()))

        if self.pm_object_original.get_uses_representative_periods():
            self.pm_object_copy.set_uses_representative_periods(True)
            representative_periods = self.pm_object_original.get_number_representative_periods()
            path_file = self.pm_object_original.get_path_weighting()

            self.pm_object_copy.set_number_representative_periods(representative_periods)
            self.pm_object_copy.set_path_weighting(path_file)

        else:
            self.pm_object_copy.set_uses_representative_periods(False)
            covered_period = self.pm_object_original.get_covered_period()
            self.pm_object_copy.set_covered_period(covered_period)

        self.parent.pm_object_copy = self.pm_object_copy
        self.parent.update_widgets()

    def __init__(self, parent, notebook, pm_object_copy=None, pm_object_original=None):

        """
        Creates Toggled Frame object, which contains Parameter, settings etc. based on the frame type

        :param parent: Interface object - to access functions of Interface
        :param pm_object_copy: Parameter object - stores information
        :param pm_object_original: Parameter object - to restore default values
        """

        self.pm_object_copy = pm_object_copy
        self.pm_object_original = pm_object_original
        self.parent = parent
        self.notebook = notebook

        ttk.Frame.__init__(self, self.notebook)

        self.general_assumptions_frame = ttk.Frame(self)
        self.parameter_frame = GeneralAssumptionsFrame(self, self.parent,
                                                       self.general_assumptions_frame, self.pm_object_copy)
        self.general_assumptions_frame.pack(expand=True, fill='both')


class ComponentInterface(ttk.Frame):

    def update_self_pm_object(self, pm_object):
        # Updates the Parameter object
        self.pm_object_copy = pm_object

    def update_frame(self):
        # If changes in parameters etc. occur, the whole frame is updated so that updates are shown immediately

        entries = []
        for c in self.pm_object_copy.get_final_conversion_components_objects():
            entries.append(c.get_nice_name())
        self.components_combo.config(values=entries)

        if self.parameter_frame is not None:

            self.parameter_frame.frame.destroy()

            if self.component != '':
                if entries:
                    for c in self.pm_object_copy.get_final_conversion_components_objects():
                        if self.component == c.get_name():
                            component = self.pm_object_copy.get_component(self.component)
                            component_nice_name = component.get_nice_name()
                            self.components_combo.set(component_nice_name)
                            self.parameter_frame = ComponentFrame(self, self.component_frame, self.component,
                                                                  self.pm_object_copy, self.pm_object_original)
                            self.parameter_frame.frame.grid(row=1, sticky='ew')
                            break
                        else:
                            self.components_combo.set('Choose component')
                else:
                    self.components_combo.set('Choose component')
            else:
                self.components_combo.set('Choose component')

    def callbackFuncDecideComponent(self, event=None):
        # Function of component combo box
        # Destroy old frame (if exist) and create new frame

        if self.parameter_frame is not None:
            self.parameter_frame.frame.destroy()

        nice_name = self.components_combo.get()
        self.component = self.pm_object_copy.get_abbreviation(nice_name)

        self.parameter_frame = ComponentFrame(self, self.component_frame, self.component,
                                              self.pm_object_copy, self.pm_object_original)
        self.parameter_frame.frame.grid(row=1, sticky='ew')

    def set_components_to_default(self):
        # Set all component parameters and commodities to default

        for component in self.pm_object_copy.get_conversion_components():
            self.pm_object_copy.remove_component_entirely(component.get_name())

        for component in self.pm_object_original.get_conversion_components():
            copied_component = component.__copy__()
            self.pm_object_copy.add_component(component.get_name(), copied_component)

        self.parent.pm_object_copy = self.pm_object_copy
        self.parent.update_widgets()

    def create_new_component_window(self):
        # Adds dummy component which then can be adjusted
        AddNewComponentWindow(self.parent, self.pm_object_copy)

    def delete_components(self):
        # Deletes components based on choice

        def set_component(component, index):
            delete_component_dict[component] = var_list[index].get()

        def kill_only():
            delete_component_window.destroy()

        def delete_and_kill():

            for component in [*delete_component_dict]:
                if delete_component_dict[component]:

                    component.set_final(False)

                    # Set all commodities to not final if commodity is not used anymore
                    for commodity in self.pm_object_copy.get_final_commodities_objects():
                        commodity_used_elsewhere = False
                        for other_component in self.pm_object_copy.get_final_conversion_components_objects():
                            if other_component != component:
                                if commodity.get_name() in [*other_component.get_inputs().keys()]:
                                    commodity_used_elsewhere = True
                                    break
                                if commodity.get_name() in [*other_component.get_outputs().keys()]:
                                    commodity_used_elsewhere = True
                                    break

                        if not commodity_used_elsewhere:
                            self.pm_object_copy.remove_commodity(commodity.get_name())

            self.parent.pm_object_copy = self.pm_object_copy
            self.parent.update_widgets()

            delete_component_window.destroy()

        delete_component_window = Toplevel()
        delete_component_window.grab_set()

        delete_component_dict = {}

        var_list = []
        i = 0

        for c in self.pm_object_copy.get_final_conversion_components_objects():
            delete_component_dict.update({c: False})
            var_list.append(tk.IntVar())
            tk.Checkbutton(delete_component_window, text=c.get_nice_name(),
                           variable=var_list[i], onvalue=1, offvalue=0,
                           command=lambda c=c, i=i: set_component(c, i)).grid(row=i, column=0, columnspan=2, sticky='w')
            i += 1

        ttk.Button(delete_component_window, text='Delete components', command=delete_and_kill).grid(row=i + 1,
                                                                                                    column=0,
                                                                                                    sticky='we')
        ttk.Button(delete_component_window, text='Cancel', command=kill_only).grid(row=i + 1, column=1, sticky='we')

        delete_component_window.grid_columnconfigure(0, weight=1, uniform='a')
        delete_component_window.grid_columnconfigure(1, weight=1, uniform='a')

        delete_component_window.mainloop()

    def __init__(self, parent, notebook, pm_object_copy=None, pm_object_original=None):

        """
        Creates Toggled Frame object, which contains Parameter, settings etc. based on the frame type

        :param parent: Interface object - to access functions of Interface
        :param pm_object_copy: Parameter object - stores information
        :param pm_object_original: Parameter object - to restore default values
        """

        self.pm_object_copy = pm_object_copy
        self.pm_object_original = pm_object_original
        self.parent = parent
        self.notebook = notebook

        ttk.Frame.__init__(self, self.notebook)

        self.component = ''

        self.component_frame = ttk.Frame(self)
        widget_frame = ttk.Frame(self.component_frame)
        self.parameter_frame = None

        button_frame = ttk.Frame(widget_frame)

        ttk.Button(button_frame, text='Add component', command=self.create_new_component_window)\
            .grid(row=0, column=0, sticky='ew')

        ttk.Button(button_frame, text='Delete components', command=self.delete_components)\
            .grid(row=0, column=1, sticky='ew')

        ttk.Button(button_frame, text='Reset all components',
                   command=self.set_components_to_default).grid(row=0, column=2, sticky='ew')

        button_frame.grid_columnconfigure(0, weight=1, uniform='a')
        button_frame.grid_columnconfigure(1, weight=1, uniform='a')
        button_frame.grid_columnconfigure(2, weight=1, uniform='a')

        button_frame.grid(row=0, sticky='ew')

        entries = []
        for c in self.pm_object_copy.get_final_conversion_components_objects():
            entries.append(c.get_nice_name())

        self.components_combo = ttk.Combobox(widget_frame, values=entries, state='readonly')
        self.components_combo.bind("<<ComboboxSelected>>", self.callbackFuncDecideComponent)
        self.components_combo.set('Choose component')
        self.components_combo.delete(0, 'end')

        self.components_combo.grid(row=1, sticky='ew')

        widget_frame.grid_columnconfigure(0, weight=1)
        widget_frame.grid(row=0, sticky='ew')

        self.component_frame.grid_columnconfigure(0, weight=1)
        self.component_frame.pack(fill="both", expand=True)


class CommodityInterface(ttk.Frame):

    def update_self_pm_object(self, pm_object):
        # Updates the Parameter object
        self.pm_object_copy = pm_object

    def update_frame(self):
        # If changes in parameters etc. occur, the whole frame is updated so that updates are shown immediately

        unused_commodities = self.pm_object_copy.get_not_used_commodities_names()
        if unused_commodities:
            self.delete_commodity_button.config(state=NORMAL)
        else:
            self.delete_commodity_button.config(state=DISABLED)

        self.nice_names = []
        for commodity in self.pm_object_copy.get_final_commodities_objects():
            self.nice_names.append(commodity.get_nice_name())
        self.combobox_commodity.config(values=self.nice_names)

        if self.combobox_commodity.get() != 'Choose commodity':

            nice_name = self.combobox_commodity.get()
            self.commodity = self.pm_object_copy.get_abbreviation(nice_name)

            if nice_name not in self.nice_names:
                self.commodity = ''
                self.combobox_commodity.set('Choose commodity')

            if self.parameter_frame is not None:
                self.parameter_frame.frame.destroy()

            if self.combobox_commodity.get() != 'Choose commodity':

                self.parameter_frame = CommodityFrame(self, self.commodity_frame, self.commodity, self.pm_object_copy,
                                                   self.pm_object_original)
                self.parameter_frame.frame.grid(row=1, sticky='ew')

    def callbackFuncDecideCommodity(self, event=None):
        # Function of commodity combo box
        # Destroy old frame (if exist) and create new frame

        nice_name = self.combobox_commodity.get()
        self.commodity = self.pm_object_copy.get_abbreviation(nice_name)

        if nice_name not in self.nice_names:
            self.commodity = ''
            self.combobox_commodity.set('Choose commodity')

        if self.parameter_frame is not None:
            self.parameter_frame.frame.destroy()

        if self.combobox_commodity.get() != 'Choose commodity':
            self.parameter_frame = CommodityFrame(self, self.commodity_frame, self.commodity, self.pm_object_copy,
                                               self.pm_object_original)
            self.parameter_frame.frame.grid(row=1, sticky='ew')

    def delete_unused_commodities(self):

        def delete_chosen_commodities():
            for s in [*check_commodity.keys()]:
                if check_commodity[s].get():
                    self.pm_object_copy.remove_commodity_entirely(s)
            delete_commodities.destroy()

            self.parent.pm_object_copy = self.pm_object_copy
            self.parent.update_widgets()

        def kill_only():
            delete_commodities.destroy()

        delete_commodities = Toplevel()
        delete_commodities.title('')
        delete_commodities.grab_set()

        unused_commodities = self.pm_object_copy.get_not_used_commodities()
        i = 0
        check_commodity = {}
        for commodity in unused_commodities:
            check_commodity[commodity.get_name()] = BooleanVar()
            ttk.Checkbutton(delete_commodities, text=commodity.get_nice_name(), variable=check_commodity[commodity.get_name()])\
                .grid(row=i, columnspan=2, sticky='w')
            i += 1

        ttk.Button(delete_commodities, text='Delete', command=delete_chosen_commodities).grid(row=i, column=0, sticky='ew')
        ttk.Button(delete_commodities, text='Cancel', command=kill_only).grid(row=i, column=1, sticky='ew')

    def __init__(self, parent, notebook, pm_object_copy=None, pm_object_original=None):

        """
        Creates Toggled Frame object, which contains Parameter, settings etc. based on the frame type

        :param parent: Interface object - to access functions of Interface
        :param pm_object_copy: Parameter object - stores information
        :param pm_object_original: Parameter object - to restore default values
        """

        self.pm_object_copy = pm_object_copy
        self.pm_object_original = pm_object_original
        self.parent = parent
        self.notebook = notebook

        ttk.Frame.__init__(self, self.notebook)

        self.commodity = ''

        self.commodity_frame = ttk.Frame(self)
        widget_frame = ttk.Frame(self.commodity_frame)
        self.parameter_frame = None

        unused_commodities = self.pm_object_copy.get_not_used_commodities_names()
        if unused_commodities:
            self.delete_commodity_button = ttk.Button(widget_frame, text='Delete unused commodities',
                                                   command=self.delete_unused_commodities)
        else:
            self.delete_commodity_button = ttk.Button(widget_frame, text='Delete unused commodities',
                                                   command=self.delete_unused_commodities, state=DISABLED)
        self.delete_commodity_button.grid(row=0, sticky='ew')

        self.nice_names = []
        for commodity in self.pm_object_copy.get_final_commodities_objects():
            self.nice_names.append(commodity.get_nice_name())

        self.combobox_commodity = ttk.Combobox(widget_frame, values=self.nice_names, state='readonly')
        self.combobox_commodity.grid(row=1, sticky='ew')
        self.combobox_commodity.bind("<<ComboboxSelected>>", self.callbackFuncDecideCommodity)
        self.combobox_commodity.set('Choose commodity')

        widget_frame.grid_columnconfigure(0, weight=1)
        widget_frame.grid(row=0, sticky='ew')

        self.commodity_frame.grid_columnconfigure(0, weight=1)
        self.commodity_frame.pack(expand=True, fill='both')


class StorageInterface(ttk.Frame):

    def update_self_pm_object(self, pm_object):
        # Updates the Parameter object
        self.pm_object_copy = pm_object

    def update_frame(self):
        # If changes in parameters etc. occur, the whole frame is updated so that updates are shown immediately

        # Add storages to collection of existing storages
        self.storages_nice_names = []
        for s in self.pm_object_copy.get_final_storage_components_objects():
            self.storages_nice_names.append(s.get_nice_name())

        # Add dummy storages for not yet existing storages
        for s in self.pm_object_copy.get_final_commodities_objects():

            if s.get_nice_name() not in self.storages_nice_names:

                self.storages_nice_names.append(s.get_nice_name())

                storage = StorageComponent(s.get_name(), s.get_nice_name(),
                                           final_unit=False, custom_unit=True)
                self.pm_object_copy.add_component(s.get_name(), storage)

                for p in self.pm_object_copy.get_general_parameters():
                    self.pm_object_copy.set_applied_parameter_for_component(p, s.get_name(), True)

        self.combobox_storage.config(values=self.storages_nice_names)

        # Check if commodity still in system and set combobox to commodity or to "choose storage"
        if self.parameter_frame is not None:

            self.parameter_frame.frame.destroy()

            if self.pm_object_copy.get_nice_name(self.storage) in self.storages_nice_names:

                self.combobox_storage.set(self.pm_object_copy.get_nice_name(self.storage))

                self.parameter_frame = StorageFrame(self, self.storage_frame, self.storage,
                                      self.pm_object_copy, self.pm_object_original)
                self.parameter_frame.frame.grid(row=1, sticky='ew')

            else:
                self.combobox_storage.set('Choose Storage')

    def callbackFuncStorage(self, event=None):
        # Function of storage combo box
        # Destroy old frame (if exist) and create new frame
        if self.parameter_frame is not None:
            self.parameter_frame.frame.destroy()

        self.storage = self.pm_object_copy.get_abbreviation(self.combobox_storage.get())

        self.parameter_frame = StorageFrame(self, self.storage_frame, self.storage,
                                          self.pm_object_copy, self.pm_object_original)
        self.parameter_frame.frame.grid(row=1, sticky='ew')

    def __init__(self, parent, notebook, pm_object_copy=None, pm_object_original=None):

        """
        Creates Toggled Frame object, which contains Parameter, settings etc. based on the frame type

        :param parent: Interface object - to access functions of Interface
        :param pm_object_copy: Parameter object - stores information
        :param pm_object_original: Parameter object - to restore default values
        """

        self.pm_object_copy = pm_object_copy
        self.pm_object_original = pm_object_original
        self.parent = parent
        self.notebook = notebook

        ttk.Frame.__init__(self, self.notebook)

        self.storage = ''

        self.storage_frame = ttk.Frame(self)
        widget_frame = ttk.Frame(self.storage_frame)
        self.parameter_frame = None

        # Add storages to collection of existing storages
        self.storages_nice_names = []
        for s in self.pm_object_copy.get_final_storage_components_objects():
            self.storages_nice_names.append(s.get_nice_name())

        # Add dummy storages for not yet existing storages
        for s in self.pm_object_copy.get_final_commodities_objects():

            if s.get_nice_name() not in self.storages_nice_names:

                self.storages_nice_names.append(s.get_nice_name())

                storage = StorageComponent(s.get_name(), s.get_nice_name(),
                                           final_unit=False, custom_unit=True)
                self.pm_object_copy.add_component(s.get_name(), storage)

                for p in self.pm_object_copy.get_general_parameters():
                    self.pm_object_copy.set_applied_parameter_for_component(p, s.get_name(), True)

        self.combobox_storage = ttk.Combobox(widget_frame, values=self.storages_nice_names, state='readonly')
        self.combobox_storage.grid(sticky='ew')
        self.combobox_storage.set('Choose storage')
        self.combobox_storage.bind("<<ComboboxSelected>>", self.callbackFuncStorage)

        widget_frame.grid_columnconfigure(0, weight=1)
        widget_frame.grid(row=0, sticky='ew')

        self.storage_frame.grid_columnconfigure(0, weight=1)
        self.storage_frame.pack(fill='both', expand=True)


class GeneratorInterface(ttk.Frame):

    def update_self_pm_object(self, pm_object):
        # Updates the Parameter object
        self.pm_object_copy = pm_object

    def callbackFuncDecideGenerator(self, event=None):
        # Function of generator combo box
        # Destroy old frame (if exist) and create new frame

        self.generator = self.pm_object_copy.get_abbreviation(self.components_generator_combo.get())

        if self.parameter_frame is not None:
            self.parameter_frame.frame.destroy()

        self.parameter_frame = GeneratorFrame(self, self.generator_frame, self.generator,
                                              self.pm_object_copy, self.pm_object_original)
        self.parameter_frame.frame.grid(row=1, sticky='ew')  # pack(fill="both", expand=True)

    def update_frame(self):
        # If changes in parameters etc. occur, the whole frame is updated so that updates are shown immediately

        # Update combobox with new values
        generators = []
        generators_abbreviations = []
        for generator in self.pm_object_copy.get_generator_components_objects():
            generators.append(generator.get_nice_name())
            generators_abbreviations.append(generator.get_name())
        self.components_generator_combo.config(values=generators)

        # Enable / Disable delete generator button
        if len(generators) == 0:
            self.delete_generator_button.config(state=DISABLED)
        else:
            self.delete_generator_button.config(state=NORMAL)

        # Delete parameter frame
        if self.parameter_frame is not None:
            self.parameter_frame.frame.destroy()

        if self.generator == '':  # Case no generator was chosen
            self.components_generator_combo.set('Choose generator')
        else:
            if self.generator not in generators_abbreviations:
                self.components_generator_combo.set('Choose generator')
            else:  # create new parameter frame if generator was chosen and exists
                self.parameter_frame = GeneratorFrame(self, self.generator_frame, self.generator,
                                                      self.pm_object_copy, self.pm_object_original)
                self.parameter_frame.frame.grid(row=1, sticky='ew')  # pack(fill='both', expand=True)

    def add_generator(self):
        # Adds dummy generator, which then can be adjusted

        def get_generator_and_kill():
            nice_name = nice_name_entry.get()
            abbreviation = abbreviation_entry.get()

            generator = GenerationComponent(abbreviation, nice_name, final_unit=True, custom_unit=True)
            self.pm_object_copy.add_component(abbreviation, generator)

            for p in self.pm_object_copy.get_general_parameters():
                self.pm_object_copy.set_applied_parameter_for_component(p, abbreviation, True)

            self.parent.pm_object_copy = self.pm_object_copy
            self.parent.update_widgets()

            newWindow.destroy()

        def kill_only():
            newWindow.destroy()

        newWindow = Toplevel()
        newWindow.title('Add Generator')
        newWindow.grab_set()

        ttk.Label(newWindow, text='Nice name').grid(row=0, column=0, sticky='ew')
        nice_name_entry = ttk.Entry(newWindow)
        nice_name_entry.grid(row=0, column=1, sticky='ew')

        ttk.Label(newWindow, text='Abbreviation').grid(row=1, column=0, sticky='ew')
        abbreviation_entry = ttk.Entry(newWindow)
        abbreviation_entry.grid(row=1, column=1, sticky='ew')

        newWindow.grid_columnconfigure(0, weight=1, uniform='a')
        newWindow.grid_columnconfigure(1, weight=1, uniform='a')

        button_frame = ttk.Frame(newWindow)

        ttk.Button(button_frame, text='OK', command=get_generator_and_kill).grid(row=0, column=0, sticky='ew')
        ttk.Button(button_frame, text='Cancel', command=kill_only).grid(row=0, column=1, sticky='ew')

        button_frame.grid_columnconfigure(0, weight=1, uniform='a')
        button_frame.grid_columnconfigure(1, weight=1, uniform='a')
        button_frame.grid(row=2, column=0, columnspan=2, sticky='ew')

    def delete_generator(self):

        def delete_checked_generators():
            for g in generators:
                if checked_generators[g]:
                    self.pm_object_copy.remove_component_entirely(g)

            self.parent.pm_object_copy = self.pm_object_copy
            self.parent.update_widgets()

            delete_generators_window.destroy()

        def kill_delete_generators():

            delete_generators_window.destroy()

        delete_generators_window = Toplevel()
        delete_generators_window.grab_set()
        delete_generators_window.title('Delete Generators')

        generators = []
        for gen in self.pm_object_copy.get_generator_components():
            generators.append(gen.get_name())

        checked_generators = {}
        i = 0
        for gen in generators:
            checked_generators[gen] = BooleanVar()
            ttk.Checkbutton(delete_generators_window, text=self.pm_object_copy.get_nice_name(gen),
                            variable=checked_generators[gen]).grid(row=i, columnspan=2, sticky='w')
            i += 1

        ttk.Button(delete_generators_window, text='Delete', command=delete_checked_generators).grid(row=i, column=0)
        ttk.Button(delete_generators_window, text='Cancel', command=kill_delete_generators).grid(row=i, column=1)

    def __init__(self, parent, notebook, pm_object_copy=None, pm_object_original=None):

        """
        Creates Toggled Frame object, which contains Parameter, settings etc. based on the frame type

        :param parent: Interface object - to access functions of Interface
        :param pm_object_copy: Parameter object - stores information
        :param pm_object_original: Parameter object - to restore default values
        """

        self.pm_object_copy = pm_object_copy
        self.pm_object_original = pm_object_original
        self.parent = parent
        self.notebook = notebook

        ttk.Frame.__init__(self, self.notebook)

        self.generator = ''

        self.generator_frame = ttk.Frame(self)

        # Button frame contains button to add and delete generators
        widget_frame = ttk.Frame(self.generator_frame)
        self.parameter_frame = None

        self.add_generator_button = ttk.Button(widget_frame, text='Add Generator', command=self.add_generator)
        self.add_generator_button.grid(row=0, column=0, sticky='ew')

        self.delete_generator_button = ttk.Button(widget_frame, text='Delete Generator',
                                                  command=self.delete_generator)
        self.delete_generator_button.grid(row=0, column=1, sticky='ew')

        # Create Combobox, which contains all generators and can be selected
        generators = []
        for generator in self.pm_object_copy.get_final_generator_components_objects():
            generators.append(generator.get_nice_name())

        if len(generators) == 0:
            self.delete_generator_button.config(state=DISABLED)
        else:
            self.delete_generator_button.config(state=NORMAL)

        self.components_generator_combo = ttk.Combobox(widget_frame, values=generators, state='readonly')
        self.components_generator_combo.grid(row=1, columnspan=2, sticky='ew')
        self.components_generator_combo.set('Choose generator')
        self.components_generator_combo.bind("<<ComboboxSelected>>", self.callbackFuncDecideGenerator)

        widget_frame.grid_columnconfigure(0, weight=1, uniform='a')
        widget_frame.grid_columnconfigure(1, weight=1, uniform='a')
        widget_frame.grid(row=0, sticky='ew')  # pack(fill='both', expand=True)

        self.generator_frame.grid_columnconfigure(0, weight=1)
        self.generator_frame.pack(fill='both', expand=True)


class DataInterface(ttk.Frame):

    def set_generation_data(self):
        if self.generation_data_status_var.get() == 'single':
            path = filedialog.askopenfilename()
            file_name = path.split('/')[-1]

            if file_name != '':
                if file_name.split('.')[-1] == 'xlsx':
                    self.pm_object_copy.set_generation_data(file_name)
                    self.pm_object_copy.set_generation_data_status(True)

                    self.parent.pm_object_copy = self.pm_object_copy
                    self.parent.update_widgets()

                else:
                    wrong_file_window = Toplevel()
                    wrong_file_window.title('')
                    wrong_file_window.grab_set()

                    ttk.Label(wrong_file_window, text='File is not xlsx format').pack(fill='both', expand=True)

                    ttk.Button(wrong_file_window, text='OK', command=wrong_file_window.destroy).pack(fill='both',
                                                                                                     expand=True)
        else:
            path = filedialog.askdirectory()
            folder_name = path.split('/')[-1]

            self.pm_object_copy.set_generation_data(folder_name)
            self.pm_object_copy.set_generation_data_status(False)

            self.parent.pm_object_copy = self.pm_object_copy
            self.parent.update_widgets()

    def create_generation_template(self):

        if self.pm_object_copy.get_project_name() is None:
            project_name = ''
        else:
            project_name = self.pm_object_copy.get_project_name()

        generators = []
        for g in self.pm_object_copy.get_final_generator_components_objects():
            generators.append((g.get_nice_name()))

        if self.pm_object_copy.get_uses_representative_periods():
            number_periods = len(pd.read_excel(self.pm_object_copy.get_path_data() + self.pm_object_copy.get_path_weighting(),
                                             index_col=0).index)
            covered_period = number_periods * 7 * 24
        else:
            covered_period = self.pm_object_copy.get_covered_period()

        now = datetime.now()
        dt_string = now.strftime("%d%m%Y_%H%M%S")

        path = self.pm_object_copy.get_path_data() + dt_string + '_' + project_name + '_generation_profiles.xlsx'
        pd.DataFrame(index=[i for i in range(int(covered_period))], columns=generators).to_excel(path)

        os.system('start excel.exe "%s"' % (path,))

        self.pm_object_copy.set_generation_data(dt_string + '_' + project_name + '_generation_profiles.xlsx')
        self.pm_object_copy.set_generation_data_status(True)

        self.parent.pm_object_copy = self.pm_object_copy
        self.parent.update_widgets()

    def set_market_data(self):
        if self.market_data_status_var.get() == 'single':
            path = filedialog.askopenfilename()
            file_name = path.split('/')[-1]

            if file_name != '':
                if file_name.split('.')[-1] == 'xlsx':
                    self.pm_object_copy.set_market_data(file_name)
                    self.pm_object_copy.set_market_data_status(True)

                    self.parent.pm_object_copy = self.pm_object_copy
                    self.parent.update_widgets()

                else:
                    wrong_file_window = Toplevel()
                    wrong_file_window.title('')
                    wrong_file_window.grab_set()

                    ttk.Label(wrong_file_window, text='File is not xlsx format').pack(fill='both', expand=True)

                    ttk.Button(wrong_file_window, text='OK', command=wrong_file_window.destroy).pack(fill='both',
                                                                                                     expand=True)
        else:
            path = filedialog.askdirectory()
            folder_name = path.split('/')[-1]

            self.pm_object_copy.set_market_data(folder_name)
            self.pm_object_copy.set_market_data_status(False)

            self.parent.pm_object_copy = self.pm_object_copy
            self.parent.update_widgets()

    def set_weighting(self):
        path = filedialog.askopenfilename()
        file_name = path.split('/')[-1]

        if file_name != '':
            if file_name.split('.')[-1] == 'xlsx':
                self.pm_object_copy.set_path_weighting(file_name)

                self.parent.pm_object_copy = self.pm_object_copy
                self.parent.update_widgets()

            else:
                wrong_file_window = Toplevel()
                wrong_file_window.title('')
                wrong_file_window.grab_set()

                ttk.Label(wrong_file_window, text='File is not xlsx format').pack(fill='both', expand=True)

                ttk.Button(wrong_file_window, text='OK', command=wrong_file_window.destroy).pack(fill='both',
                                                                                                 expand=True)

    def create_market_data_template(self):

        if self.pm_object_copy.get_project_name() is None:
            project_name = ''
        else:
            project_name = self.pm_object_copy.get_project_name()

        columns = []
        for s in self.pm_object_copy.get_all_commodities():
            commodity_object = self.pm_object_copy.get_commodity(s)
            if commodity_object.is_purchasable():
                columns.append(commodity_object.get_nice_name() + '_Purchase_Price')
            if commodity_object.is_saleable():
                columns.append(commodity_object.get_nice_name() + '_Selling_Price')

        if self.pm_object_copy.get_uses_representative_periods():
            number_periods = len(pd.read_excel(self.pm_object_copy.get_path_data() + self.pm_object_copy.get_path_weighting(), index_col=0).index)
            covered_period = number_periods * 7 * 24
        else:
            covered_period = self.pm_object_copy.get_covered_period()

        now = datetime.now()
        dt_string = now.strftime("%d%m%Y_%H%M%S")

        path = self.pm_object_copy.get_path_data() + dt_string + '_' + project_name + '_market_prices.xlsx'
        pd.DataFrame(index=[i for i in range(int(covered_period))], columns=columns).to_excel(path)

        os.system('start excel.exe "%s"' % (path, ))

        self.pm_object_copy.set_market_data(dt_string + '_' + project_name + '_market_prices.xlsx')
        self.pm_object_copy.set_market_data_status(True)

        self.parent.pm_object_copy = self.pm_object_copy
        self.parent.update_widgets()

    def update_self_pm_object(self, pm_object):
        # Updates the Parameter object
        self.pm_object_copy = pm_object

    def update_frame(self):
        # If changes in parameters etc. occur, the whole frame is updated so that updates are shown immediately

        if self.data_frame is not None:
            self.data_frame.destroy()
        self.data_frame = ttk.Frame(self)

        # ------
        # Generation data
        generation_data_frame = ttk.Frame(self.data_frame)
        ttk.Label(generation_data_frame, text='Generation Data', font='Helvetica 10 bold').grid(row=0, columnspan=2,
                                                                                                sticky='ew')

        self.generation_data_status_var = StringVar()
        if self.pm_object_copy.get_generation_data_status():
            self.generation_data_status_var.set('single')
        else:
            self.generation_data_status_var.set('multiple')

        self.rb_single_generation = ttk.Radiobutton(generation_data_frame, text='Use single profile', value='single',
                                                    variable=self.generation_data_status_var)
        self.rb_single_generation.grid(row=1, column=0, sticky='ew')

        self.rb_several = ttk.Radiobutton(generation_data_frame, text='Use multiple profiles', value='multiple',
                                          variable=self.generation_data_status_var)
        self.rb_several.grid(row=1, column=1, sticky='ew')

        self.generation_data_textvar = StringVar()
        try:
            path_generation = self.pm_object_copy.get_generation_data()
            file_name_generation = path_generation.split('/')[-1]
            self.generation_data_textvar.set(file_name_generation)
        except:
            self.generation_data_textvar.set('')

        ttk.Label(generation_data_frame, text='File/Folder').grid(row=2, column=0, sticky='w')
        ttk.Label(generation_data_frame, text=self.generation_data_textvar.get()).grid(row=2, column=1, sticky='ew')

        ttk.Button(generation_data_frame, text='Select profile(s)', command=self.set_generation_data).grid(row=3,
                                                                                                           column=0,
                                                                                                           sticky='ew')

        ttk.Button(generation_data_frame, text='Create new generation template',
                   command=self.create_generation_template).grid(row=3, column=1, sticky='ew')

        generation_data_frame.grid_columnconfigure(0, weight=1, uniform='a')
        generation_data_frame.grid_columnconfigure(1, weight=1, uniform='a')
        generation_data_frame.grid(row=0, sticky='ew')

        # ----------
        # Market data

        market_data_frame = ttk.Frame(self.data_frame)
        ttk.Separator(market_data_frame).grid(row=0, columnspan=2, sticky='ew')
        ttk.Label(market_data_frame, text='Market Data', font='Helvetica 10 bold').grid(row=1, columnspan=2,
                                                                                        sticky='ew')

        self.market_data_status_var = StringVar()
        if self.pm_object_copy.get_market_data_status():
            self.market_data_status_var.set('single')
        else:
            self.market_data_status_var.set('multiple')

        self.rb_single = ttk.Radiobutton(market_data_frame, text='Use single profile', value='single',
                                         variable=self.market_data_status_var)
        self.rb_single.grid(row=2, column=0, sticky='ew')

        self.rb_several = ttk.Radiobutton(market_data_frame, text='Use multiple profiles', value='multiple',
                                          variable=self.market_data_status_var)
        self.rb_several.grid(row=2, column=1, sticky='ew')

        self.market_data_textvar = StringVar()
        try:
            path = self.pm_object_copy.get_market_data()
            file_name = path.split('/')[-1]
            self.market_data_textvar.set(file_name)
        except:
            self.market_data_textvar.set('')

        ttk.Label(market_data_frame, text='File/Folder').grid(row=3, column=0, sticky='ew')
        ttk.Label(market_data_frame, text=self.market_data_textvar.get()).grid(row=3, column=1, sticky='ew')

        ttk.Button(market_data_frame, text='Select profile(s)', command=self.set_market_data).grid(row=4, column=0,
                                                                                                   sticky='ew')
        ttk.Button(market_data_frame, text='Create new price template',
                   command=self.create_market_data_template).grid(row=4, column=1, sticky='ew')

        market_data_frame.grid_columnconfigure(0, weight=1, uniform='a')
        market_data_frame.grid_columnconfigure(1, weight=1, uniform='a')
        market_data_frame.grid(row=1, sticky='ew')

        # ----
        # Representative Period Data

        if self.pm_object_copy.get_uses_representative_periods():
            weighting_data_frame = ttk.Frame(self.data_frame)
            ttk.Separator(weighting_data_frame).grid(row=0, columnspan=2, sticky='ew')
            ttk.Label(weighting_data_frame, text='Representative Period Weighting', font='Helvetica 10 bold').grid(
                row=1, columnspan=2, sticky='ew')

            self.path_weighting_textvar = StringVar()
            self.path_weighting_textvar.set(self.pm_object_copy.get_path_weighting())

            ttk.Label(weighting_data_frame, text='File').grid(row=2, column=0, sticky='ew')
            ttk.Label(weighting_data_frame, text=self.path_weighting_textvar.get()).grid(row=2, column=1, sticky='w')

            ttk.Button(weighting_data_frame, text='Select Weighting', command=self.set_weighting).grid(row=3,
                                                                                                       columnspan=2,
                                                                                                       sticky='ew')

            weighting_data_frame.grid_columnconfigure(0, weight=1, uniform='a')
            weighting_data_frame.grid_columnconfigure(1, weight=1, uniform='a')
            weighting_data_frame.grid(row=2, sticky='ew')

        self.data_frame.grid_columnconfigure(0, weight=1)
        self.data_frame.pack(fill='both', expand=True)

    def __init__(self, parent, notebook, pm_object_copy=None, pm_object_original=None):

        """
        Creates Toggled Frame object, which contains data

        :param parent: Interface object - to access functions of Interface
        :param pm_object_copy: Parameter object - stores information
        :param pm_object_original: Parameter object - to restore default values
        """

        self.pm_object_copy = pm_object_copy
        self.pm_object_original = pm_object_original
        self.parent = parent
        self.notebook = notebook

        ttk.Frame.__init__(self, self.notebook)

        self.data_frame = ttk.Frame(self)

        self.update_frame()


class SettingWindow:

    def getFolderData(self):
        folder_path = filedialog.askdirectory() + '/'
        if folder_path != '/':
            self.path_data = folder_path
            self.choose_data_folder_var.set(folder_path.split('/')[-2])

    def getFolderResult(self):
        folder_path = filedialog.askdirectory() + '/'
        if folder_path != '/':
            self.path_result = folder_path
            self.choose_result_folder_var.set(folder_path.split('/')[-2])

    def getFolderProjects(self):
        folder_path = filedialog.askdirectory() + '/'
        if folder_path != '/':
            self.path_projects = folder_path
            self.choose_projects_folder_var.set(folder_path.split('/')[-2])

    def getFolderPathOptimize(self):

        if self.optimize_variable.get() == 'custom':
            folder_path = filedialog.askopenfilename()
            if folder_path != '/':
                self.path_optimize = folder_path.split('/')[-1]
                self.choose_optimization_var.set(self.path_optimize)
        else:
            folder_path = filedialog.askdirectory() + '/'
            if folder_path != '/':
                self.path_optimize = folder_path.split('/')[-2]
                self.choose_optimization_var.set(self.path_optimize)

        self.radiobutton_optimization_or_visualization_command()

    def getFolderPathResultVisualization(self):
        folder_path = filedialog.askdirectory() + '/'
        if folder_path != '/':
            self.path_visualization = folder_path.split('/')[-2]
            self.choose_visualize_folder_var.set(self.path_visualization)

            self.radiobutton_optimization_or_visualization_command()

    def radiobutton_optimization_or_visualization_command(self):

        self.optimize_or_visualize_frame.destroy()
        self.optimize_or_visualize_frame = self.create_optimization_or_visualization_frame()
        self.optimize_or_visualize_frame.grid(row=1, columnspan=2, sticky='ew')

    def create_optimization_or_visualization_frame(self):
        frame = ttk.Frame(self.frame)

        if self.optimize_or_visualize_projects_variable.get() == 'optimize':

            def radiobutton_optimize_command():
                if self.optimize_variable.get() == 'new':
                    profile_button.config(state=DISABLED)
                    profile_label.config(state=DISABLED)
                else:
                    profile_button.config(state=NORMAL)
                    profile_label.config(state=NORMAL)

            frame.grid_columnconfigure(0, weight=1, uniform='a')
            frame.grid_columnconfigure(1, weight=1, uniform='a')

            ttk.Radiobutton(frame, text='New Project', variable=self.optimize_variable,
                            value='new', command=radiobutton_optimize_command).grid(row=2, columnspan=2)

            ttk.Radiobutton(frame, text='Load existing Project', variable=self.optimize_variable,
                            value='custom', command=radiobutton_optimize_command).grid(row=3, column=0, sticky='ew')

            ttk.Radiobutton(frame, text='Optimize ready Projects', variable=self.optimize_variable,
                            value='optimize_only', command=radiobutton_optimize_command).grid(row=3, column=1,
                                                                                             sticky='ew')

            profile_button = ttk.Button(frame, text='Select Project(s)', command=self.getFolderPathOptimize)
            profile_button.grid(row=4, column=0, sticky='ew')
            profile_label = ttk.Label(frame, textvariable=self.choose_optimization_var)
            profile_label.grid(row=4, column=1, columnspan=2, sticky='w')

            ttk.Label(frame, text='Solver').grid(row=5, column=0, sticky='w')
            solvers = ['gurobi', 'cplex', 'glpk']
            self.solver_combobox = ttk.Combobox(frame, values=solvers, state='readonly')
            self.solver_combobox.set(self.choose_solver_var.get())
            self.solver_combobox.grid(row=5, column=1, sticky='ew')

            radiobutton_optimize_command()

        else:

            frame.grid_columnconfigure(0, weight=1, uniform='a')
            frame.grid_columnconfigure(1, weight=1, uniform='a')

            visualize_only_path_button = ttk.Button(frame, text='Select Result(s) for Visualization',
                                                    command=self.getFolderPathResultVisualization)
            visualize_only_path_button.grid(row=1, column=0, sticky='ew')
            visualize_only_path_label = ttk.Label(frame, textvariable=self.choose_visualize_folder_var)
            visualize_only_path_label.grid(row=1, column=1, sticky='w')

        return frame

    def kill_window(self):

        def check_empty(path):
            empty = False

            if type(path) != str:
                empty = True
            elif path == '':
                empty = True
            elif path == '/':
                empty = True

            return empty

        def kill_no_paths_window():
            window_no_paths.destroy()

        if (check_empty(self.path_data)) | (check_empty(self.path_result)) | (check_empty(self.path_projects)):
            window_no_paths = Toplevel(self.window)
            ttk.Label(window_no_paths,
                      text='Please choose data folder, result folder and location for saved projects').pack()
            ttk.Button(window_no_paths, text='Ok', command=kill_no_paths_window).pack()

        elif ((self.optimize_variable.get() == 'custom') | (self.optimize_variable.get() == 'optimize_only')) & (check_empty(self.path_optimize)):
            window_no_paths = Toplevel(self.window)
            ttk.Label(window_no_paths, text='Please choose Optimization Project(s)').pack()
            ttk.Button(window_no_paths, text='Ok', command=kill_no_paths_window).pack()

        elif (self.optimize_variable.get() == 'visualize_only') & (check_empty(self.path_visualization)):
            window_no_paths = Toplevel(self.window)
            ttk.Label(window_no_paths, text='Please choose result folder').pack()
            ttk.Button(window_no_paths, text='Ok', command=kill_no_paths_window).pack()

        else:

            self.base_settings.loc['path_data'] = self.path_data
            self.base_settings.loc['path_result'] = self.path_result
            self.base_settings.loc['path_projects'] = self.path_projects

            self.base_settings.loc['optimization_or_visualization'] = self.optimize_or_visualize_projects_variable.get()

            if self.optimize_or_visualize_projects_variable.get() == 'optimize':
                self.base_settings.loc['chosen_optimization_setting'] = self.optimize_variable.get()
                self.base_settings.loc['path_optimize'] = self.path_optimize
                self.base_settings.loc['solver'] = self.solver_combobox.get()
            else:
                self.base_settings.loc['path_visualization'] = self.path_visualization

            self.base_settings.to_excel(os.getcwd() + '/base_settings.xlsx', index=True)

            self.go_on = True
            self.window.destroy()

    def kill_window_without(self):
        self.go_on = False
        self.window.destroy()

    def __init__(self):

        self.window = Tk()
        self.window.title('')
        self.frame = Frame(self.window)
        self.frame.pack()
        self.go_on = False

        path_base_setting = os.getcwd() + '/base_settings.xlsx'
        self.base_settings = pd.read_excel(path_base_setting, index_col=0)

        self.path_data = self.base_settings.loc['path_data'].values[0]
        self.path_result = self.base_settings.loc['path_result'].values[0]
        self.path_projects = self.base_settings.loc['path_projects'].values[0]
        self.path_optimize = self.base_settings.loc['path_optimize'].values[0]
        self.solver = self.base_settings.loc['solver'].values[0]
        self.path_visualization = self.base_settings.loc['path_visualization'].values[0]

        self.optimize_or_visualize_projects_variable = StringVar()
        self.optimize_or_visualize_projects_variable.set(self.base_settings.loc['optimization_or_visualization'].values[0])

        self.optimize_variable = StringVar()
        self.optimize_variable.set(self.base_settings.loc['chosen_optimization_setting'].values[0])

        self.choose_data_folder_var = StringVar()
        self.choose_result_folder_var = StringVar()
        self.choose_projects_folder_var = StringVar()
        self.choose_optimization_var = StringVar()
        self.choose_solver_var = StringVar()
        self.choose_visualize_folder_var = StringVar()

        if type(self.path_result) == str:

            self.choose_data_folder_var.set(self.path_data.split('/')[-2])

            self.choose_result_folder_var.set(self.path_result.split('/')[-2])

            self.choose_projects_folder_var.set(self.path_projects.split('/')[-2])

            self.choose_optimization_var.set(self.path_optimize)

            self.choose_solver_var.set(self.solver)

            self.choose_visualize_folder_var.set(self.path_visualization)

        else:
            self.choose_data_folder_var.set('')
            self.choose_result_folder_var.set('')
            self.choose_projects_folder_var.set('')
            self.choose_optimization_var.set('')
            self.choose_solver_var.set('')
            self.choose_visualize_folder_var.set('')

        base_setting_frame = ttk.Frame(self.frame)
        base_setting_frame.grid_columnconfigure(0, weight=1, uniform='a')
        base_setting_frame.grid_columnconfigure(1, weight=1, uniform='a')

        ttk.Label(base_setting_frame, text='Folder Structure').grid(row=0, columnspan=2, sticky='w')

        self.choose_data_folder_button = ttk.Button(base_setting_frame, text='Select Data Folder',
                                                    command=self.getFolderData)
        self.choose_data_folder_button.grid(row=1, column=0, sticky='ew')

        self.choose_data_folder_label = tk.Label(base_setting_frame, textvariable=self.choose_data_folder_var)
        self.choose_data_folder_label.grid(row=1, column=1, sticky='w')

        self.choose_result_folder_button = ttk.Button(base_setting_frame, text='Select Result Folder',
                                                      command=self.getFolderResult)
        self.choose_result_folder_button.grid(row=2, column=0, sticky='ew')

        self.choose_result_folder_label = tk.Label(base_setting_frame, textvariable=self.choose_result_folder_var)
        self.choose_result_folder_label.grid(row=2, column=1, sticky='w')

        self.choose_projects_folder_button = ttk.Button(base_setting_frame, text='Select Project Folder',
                                                        command=self.getFolderProjects)
        self.choose_projects_folder_button.grid(row=3, column=0, sticky='ew')

        self.choose_projects_folder_label = tk.Label(base_setting_frame, textvariable=self.choose_projects_folder_var)
        self.choose_projects_folder_label.grid(row=3, column=1, sticky='w')

        ttk.Separator(base_setting_frame).grid(row=4, columnspan=2, sticky='ew')

        ttk.Label(base_setting_frame, text='Choose Application').grid(row=5, columnspan=2, sticky='w')

        ttk.Radiobutton(base_setting_frame, text='Create and Optimize Projects',
                        variable=self.optimize_or_visualize_projects_variable, value='optimize',
                        command=self.radiobutton_optimization_or_visualization_command).grid(row=6, column=0,
                                                                                             sticky='ew')

        ttk.Radiobutton(base_setting_frame, text='Visualize Projects',
                        variable=self.optimize_or_visualize_projects_variable, value='visualize',
                        command=self.radiobutton_optimization_or_visualization_command).grid(row=6, column=1,
                                                                                             sticky='ew')

        ttk.Separator(base_setting_frame).grid(row=7, columnspan=2, sticky='ew')

        base_setting_frame.grid(row=0, columnspan=2, sticky='ew')

        self.optimize_or_visualize_frame = self.create_optimization_or_visualization_frame()
        self.optimize_or_visualize_frame.grid(row=1, columnspan=2, sticky='ew')

        button_frame = ttk.Frame(self.frame)
        button_frame.grid_columnconfigure(0, weight=1, uniform='a')
        button_frame.grid_columnconfigure(1, weight=1, uniform='a')

        self.button_ok = ttk.Button(button_frame, text='Ok', command=self.kill_window)
        self.button_ok.grid(row=0, column=0, sticky='ew')
        self.button_ok = ttk.Button(button_frame, text='Cancel', command=self.kill_window_without)
        self.button_ok.grid(row=0, column=1, sticky='ew')

        button_frame.grid(row=4, columnspan=2, sticky='ew')

        self.window.mainloop()


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
