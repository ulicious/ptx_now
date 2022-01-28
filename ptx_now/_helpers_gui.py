import math
import tkinter as tk
from tkinter import *
from tkinter import ttk
from tkinter import filedialog

import pandas as pd

from general_assumptions_classes_and_methods import GeneralAssumptionsFrame
from component_classes_and_methods import ComponentFrame, AddNewComponentWindow
from streams_classes_and_methods import StreamFrame
from storage_classes_and_methods import StorageFrame
from generators_classes_and_methods import GeneratorFrame

from components import GenerationComponent, StorageComponent

import os

from datetime import datetime


class AssumptionsInterface(ttk.Frame):

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

            for c in self.pm_object_copy.get_specific_components('final'):
                self.pm_object_copy.set_applied_parameter_for_component(p,
                                                                        c.get_name(),
                                                                        self.pm_object_original
                                                                        .get_applied_parameter_for_component(p,
                                                                                                             c.get_name()))

        if self.pm_object_original.get_uses_representative_weeks():
            self.pm_object_copy.set_uses_representative_weeks(True)
            representative_weeks = self.pm_object_original.get_number_representative_weeks()
            path_file = self.pm_object_original.get_path_weighting()

            self.pm_object_copy.set_number_representative_weeks(representative_weeks)
            self.pm_object_copy.set_path_weighting(path_file)

        else:
            self.pm_object_copy.set_uses_representative_weeks(False)
            covered_period = self.pm_object_original.get_covered_period()
            self.pm_object_copy.set_covered_period(covered_period)

        self.parent.pm_object_copy = self.pm_object_copy
        self.parent.update_widgets()


class ComponentInterface(ttk.Frame):

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
        for c in self.pm_object_copy.get_specific_components(component_group='final', component_type='conversion'):
            entries.append(c.get_nice_name())

        self.components_combo = ttk.Combobox(widget_frame, values=entries, state='readonly')
        self.components_combo.bind("<<ComboboxSelected>>", self.callbackFuncDecideComponent)
        self.components_combo.set('Choose component')
        self.components_combo.delete(0, 'end')

        self.components_combo.grid(row=1, sticky='ew')

        widget_frame.grid_columnconfigure(0, weight=1)
        widget_frame.grid(row=0, sticky='ew')#pack(fill="both", expand=True)

        self.component_frame.grid_columnconfigure(0, weight=1)
        self.component_frame.pack(fill="both", expand=True)

    def update_self_pm_object(self, pm_object):
        # Updates the Parameter object
        self.pm_object_copy = pm_object

    def update_frame(self):
        # If changes in parameters etc. occur, the whole frame is updated so that updates are shown immediately

        entries = []
        for c in self.pm_object_copy.get_specific_components('final', 'conversion'):
            entries.append(c.get_nice_name())
        self.components_combo.config(values=entries)

        if self.parameter_frame is not None:

            self.parameter_frame.frame.destroy()

            if self.component != '':
                if entries:
                    for c in self.pm_object_copy.get_specific_components('final', 'conversion'):
                        if self.component == c.get_name():
                            component = self.pm_object_copy.get_component(self.component)
                            component_nice_name = component.get_nice_name()
                            self.components_combo.set(component_nice_name)
                            self.parameter_frame = ComponentFrame(self, self.component_frame, self.component,
                                                                  self.pm_object_copy, self.pm_object_original)
                            self.parameter_frame.frame.grid(row=1, sticky='ew')#pack(fill='both', expand=True)
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
        self.parameter_frame.frame.grid(row=1, sticky='ew')#pack(fill="both", expand=True)

    def set_components_to_default(self):
        # Set all component parameters and streams to default

        for component in self.pm_object_copy.get_specific_components(component_type='conversion'):
            self.pm_object_copy.remove_component_entirely(component.get_name())

        for component in self.pm_object_original.get_specific_components(component_type='conversion'):
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

                    # Set all streams to not final if stream is not used anymore
                    for stream in self.pm_object_copy.get_specific_streams('final'):
                        stream_used_elsewhere = False
                        for other_component in self.pm_object_copy.get_specific_components('final', 'conversion'):
                            if other_component != component:
                                if stream.get_name() in [*other_component.get_inputs().keys()]:
                                    stream_used_elsewhere = True
                                    break
                                if stream.get_name() in [*other_component.get_outputs().keys()]:
                                    stream_used_elsewhere = True
                                    break

                        if not stream_used_elsewhere:
                            self.pm_object_copy.remove_stream(stream.get_name())

            self.parent.pm_object_copy = self.pm_object_copy
            self.parent.update_widgets()

            delete_component_window.destroy()

        delete_component_window = Toplevel()
        delete_component_window.grab_set()

        delete_component_dict = {}

        var_list = []
        i = 0

        for c in self.pm_object_copy.get_specific_components(component_group='final', component_type='conversion'):
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


class StreamInterface(ttk.Frame):

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

        self.stream = ''

        self.stream_frame = ttk.Frame(self)
        widget_frame = ttk.Frame(self.stream_frame)
        self.parameter_frame = None

        unused_streams = self.pm_object_copy.get_specific_streams(final_stream=False)
        if unused_streams:
            self.delete_stream_button = ttk.Button(widget_frame, text='Delete unused streams',
                                                   command=self.delete_unused_streams)
        else:
            self.delete_stream_button = ttk.Button(widget_frame, text='Delete unused streams',
                                                   command=self.delete_unused_streams, state=DISABLED)
        self.delete_stream_button.grid(row=0, sticky='ew')

        self.nice_names = []
        for stream in self.pm_object_copy.get_specific_streams(final_stream=True):
            self.nice_names.append(stream.get_nice_name())

        self.combobox_stream = ttk.Combobox(widget_frame, values=self.nice_names, state='readonly')
        self.combobox_stream.grid(row=1, sticky='ew')
        self.combobox_stream.bind("<<ComboboxSelected>>", self.callbackFuncDecideStream)
        self.combobox_stream.set('Choose stream')

        widget_frame.grid_columnconfigure(0, weight=1)
        widget_frame.grid(row=0, sticky='ew')#pack(expand=True, fill='both')

        self.stream_frame.grid_columnconfigure(0, weight=1)
        self.stream_frame.pack(expand=True, fill='both')

    def update_self_pm_object(self, pm_object):
        # Updates the Parameter object
        self.pm_object_copy = pm_object

    def update_frame(self):
        # If changes in parameters etc. occur, the whole frame is updated so that updates are shown immediately

        unused_streams = self.pm_object_copy.get_specific_streams(final_stream=False)
        if unused_streams:
            self.delete_stream_button.config(state=NORMAL)
        else:
            self.delete_stream_button.config(state=DISABLED)

        self.nice_names = []
        for stream in self.pm_object_copy.get_specific_streams(final_stream=True):
            self.nice_names.append(stream.get_nice_name())
        self.combobox_stream.config(values=self.nice_names)

        if self.combobox_stream.get() != 'Choose stream':

            nice_name = self.combobox_stream.get()
            self.stream = self.pm_object_copy.get_abbreviation(nice_name)

            if nice_name not in self.nice_names:
                self.stream = ''
                self.combobox_stream.set('Choose stream')

            if self.parameter_frame is not None:
                self.parameter_frame.frame.destroy()

            if self.combobox_stream.get() != 'Choose stream':

                self.parameter_frame = StreamFrame(self, self.stream_frame, self.stream, self.pm_object_copy,
                                                   self.pm_object_original)
                self.parameter_frame.frame.grid(row=1, sticky='ew') #pack(fill="both", expand=True)

    def callbackFuncDecideStream(self, event=None):
        # Function of stream combo box
        # Destroy old frame (if exist) and create new frame

        nice_name = self.combobox_stream.get()
        self.stream = self.pm_object_copy.get_abbreviation(nice_name)

        if nice_name not in self.nice_names:
            self.stream = ''
            self.combobox_stream.set('Choose stream')

        if self.parameter_frame is not None:
            self.parameter_frame.frame.destroy()

        if self.combobox_stream.get() != 'Choose stream':
            self.parameter_frame = StreamFrame(self, self.stream_frame, self.stream, self.pm_object_copy,
                                               self.pm_object_original)
            self.parameter_frame.frame.grid(row=1, sticky='ew')#pack(fill="both", expand=True)

    def delete_unused_streams(self):

        def delete_chosen_streams():
            for s in [*check_stream.keys()]:
                if check_stream[s].get():
                    self.pm_object_copy.remove_stream_entirely(s)
            delete_streams.destroy()

            self.parent.pm_object_copy = self.pm_object_copy
            self.parent.update_widgets()

        def kill_only():
            delete_streams.destroy()

        delete_streams = Toplevel()
        delete_streams.title('')
        delete_streams.grab_set()

        unused_streams = self.pm_object_copy.get_specific_streams(final_stream=False)
        i = 0
        check_stream = {}
        for stream in unused_streams:
            check_stream[stream.get_name()] = BooleanVar()
            ttk.Checkbutton(delete_streams, text=stream.get_nice_name(), variable=check_stream[stream.get_name()])\
                .grid(row=i, columnspan=2, sticky='w')
            i += 1

        ttk.Button(delete_streams, text='Delete', command=delete_chosen_streams).grid(row=i, column=0, sticky='ew')
        ttk.Button(delete_streams, text='Cancel', command=kill_only).grid(row=i, column=1, sticky='ew')


class StorageInterface(ttk.Frame):

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
        for s in self.pm_object_copy.get_specific_components('final', 'storage'):
            self.storages_nice_names.append(s.get_nice_name())

        # Add dummy storages for not yet existing storages
        for s in self.pm_object_copy.get_specific_streams(final_stream=True):

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
        widget_frame.grid(row=0, sticky='ew') #pack(fill='both', expand=True)

        self.storage_frame.grid_columnconfigure(0, weight=1)
        self.storage_frame.pack(fill='both', expand=True)

    def update_self_pm_object(self, pm_object):
        # Updates the Parameter object
        self.pm_object_copy = pm_object

    def update_frame(self):
        # If changes in parameters etc. occur, the whole frame is updated so that updates are shown immediately

        # Add storages to collection of existing storages
        self.storages_nice_names = []
        for s in self.pm_object_copy.get_specific_components('final', 'storage'):
            self.storages_nice_names.append(s.get_nice_name())

        # Add dummy storages for not yet existing storages
        for s in self.pm_object_copy.get_specific_streams(final_stream=True):

            if s.get_nice_name() not in self.storages_nice_names:

                self.storages_nice_names.append(s.get_nice_name())

                storage = StorageComponent(s.get_name(), s.get_nice_name(),
                                           final_unit=False, custom_unit=True)
                self.pm_object_copy.add_component(s.get_name(), storage)

                for p in self.pm_object_copy.get_general_parameters():
                    self.pm_object_copy.set_applied_parameter_for_component(p, s.get_name(), True)

        self.combobox_storage.config(values=self.storages_nice_names)

        # Check if stream still in system and set combobox to stream or to "choose storage"
        if self.parameter_frame is not None:

            self.parameter_frame.frame.destroy()

            if self.pm_object_copy.get_nice_name(self.storage) in self.storages_nice_names:

                self.combobox_storage.set(self.pm_object_copy.get_nice_name(self.storage))

                self.parameter_frame = StorageFrame(self, self.storage_frame, self.storage,
                                      self.pm_object_copy, self.pm_object_original)
                self.parameter_frame.frame.grid(row=1, sticky='ew') #pack(fill='both', expand=True)

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
        self.parameter_frame.frame.grid(row=1, sticky='ew') #pack(fill='both', expand=True)


class GeneratorInterface(ttk.Frame):

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
        for generator in self.pm_object_copy.get_specific_components(component_type='generator'):
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
        for generator in self.pm_object_copy.get_specific_components(component_type='generator'):
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
        for gen in self.pm_object_copy.get_specific_components(component_type='generator'):
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


class DataInterface(ttk.Frame):

    def set_profile_generation(self):
        if self.generation_profile_var.get() == 'single':
            path = filedialog.askopenfilename()
            file_name = path.split('/')[-1]

            if file_name != '':
                if file_name.split('.')[-1] == 'xlsx':
                    self.pm_object_copy.set_generation_data(file_name)
                    self.pm_object_copy.set_generation_profile_status(True)

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
            self.pm_object_copy.set_generation_profile_status(False)

            self.parent.pm_object_copy = self.pm_object_copy
            self.parent.update_widgets()

    def create_generation_template(self):

        if self.pm_object_copy.get_project_name() is None:
            project_name = ''
        else:
            project_name = self.pm_object_copy.get_project_name()

        generators = []
        for g in self.pm_object_copy.get_specific_components('final', 'generator'):
            generators.append((g.get_nice_name()))

        if self.pm_object_copy.get_uses_representative_weeks():
            number_weeks = len(pd.read_excel(self.pm_object_copy.get_path_data() + self.pm_object_copy.get_path_weighting(),
                                             index_col=0).index)
            covered_period = number_weeks * 7 * 24
        else:
            covered_period = self.pm_object_copy.get_covered_period()

        now = datetime.now()
        dt_string = now.strftime("%d%m%Y_%H%M%S")

        path = self.pm_object_copy.get_path_data() + dt_string + '_' + project_name + '_generation_profiles.xlsx'
        pd.DataFrame(index=[i for i in range(int(covered_period))], columns=generators).to_excel(path)

        os.system('start excel.exe "%s"' % (path,))

        self.pm_object_copy.set_generation_data(dt_string + '_' + project_name + '_generation_profiles.xlsx')
        self.pm_object_copy.set_generation_profile_status(True)

        self.parent.pm_object_copy = self.pm_object_copy
        self.parent.update_widgets()

    def set_profile_purchase_selling(self):
        if self.market_data_profile_var.get() == 'single':
            path = filedialog.askopenfilename()
            file_name = path.split('/')[-1]

            if file_name != '':
                if file_name.split('.')[-1] == 'xlsx':
                    self.market_data_profile_textvar.set(file_name)
                    self.pm_object_copy.set_sell_purchase_data(file_name)
                    self.pm_object_copy.set_sell_purchase_profile_status(True)

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

            self.market_data_profile_textvar.set(folder_name)
            self.pm_object_copy.set_sell_purchase_data(folder_name)
            self.pm_object_copy.set_sell_purchase_profile_status(False)

            self.parent.pm_object_copy = self.pm_object_copy
            self.parent.update_widgets()

    def create_market_price_template(self):

        if self.pm_object_copy.get_project_name() is None:
            project_name = ''
        else:
            project_name = self.pm_object_copy.get_project_name()

        columns = []
        for s in self.pm_object_copy.get_all_streams():
            stream_object = self.pm_object_copy.get_stream(s)
            if stream_object.is_purchasable():
                columns.append(stream_object.get_nice_name() + '_Purchase_Price')
            if stream_object.is_saleable():
                columns.append(stream_object.get_nice_name() + '_Selling_Price')

        if self.pm_object_copy.get_uses_representative_weeks():
            number_weeks = len(pd.read_excel(self.pm_object_copy.get_path_data() + self.pm_object_copy.get_path_weighting(), index_col=0).index)
            covered_period = number_weeks * 7 * 24
        else:
            covered_period = self.pm_object_copy.get_covered_period()

        now = datetime.now()
        dt_string = now.strftime("%d%m%Y_%H%M%S")

        path = self.pm_object_copy.get_path_data() + dt_string + '_' + project_name + '_market_prices.xlsx'
        pd.DataFrame(index=[i for i in range(int(covered_period))], columns=columns).to_excel(path)

        os.system('start excel.exe "%s"' % (path, ))

        self.pm_object_copy.set_sell_purchase_data(dt_string + '_' + project_name + '_market_prices.xlsx')
        self.pm_object_copy.set_sell_purchase_profile_status(True)

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

        self.generation_profile_var = StringVar()
        if self.pm_object_copy.get_generation_profile_status():
            self.generation_profile_var.set('single')
        else:
            self.generation_profile_var.set('multiple')

        self.rb_single_generation = ttk.Radiobutton(generation_data_frame, text='Use single profile', value='single',
                                                    variable=self.generation_profile_var)
        self.rb_single_generation.grid(row=1, column=0, sticky='w')

        self.rb_several = ttk.Radiobutton(generation_data_frame, text='Use multiple profiles', value='multiple',
                                          variable=self.generation_profile_var)
        self.rb_several.grid(row=1, column=1, sticky='w')

        self.generation_profile_textvar = StringVar()
        try:
            path_generation = self.pm_object_copy.get_generation_data()
            file_name_generation = path_generation.split('/')[-1]
            self.generation_profile_textvar.set(file_name_generation)
        except:
            self.generation_profile_textvar.set('')

        ttk.Label(generation_data_frame, text='Profile file/Folder').grid(row=2, column=0, sticky='w')
        self.profile_label = ttk.Label(generation_data_frame, text=self.generation_profile_textvar.get())
        self.profile_label.grid(row=2, column=1, sticky='w')

        self.select_profile_button = ttk.Button(generation_data_frame, text='Select profile(s)',
                                                command=self.set_profile_generation)
        self.select_profile_button.grid(row=3, column=0, sticky='ew')

        self.create_generation_template_button = ttk.Button(generation_data_frame,
                                                            text='Create new Generation Template',
                                                            command=self.create_generation_template)
        self.create_generation_template_button.grid(row=3, column=1, sticky='ew')

        generation_data_frame.grid_columnconfigure(0, weight=1)
        generation_data_frame.grid_columnconfigure(1, weight=1)

        generation_data_frame.pack(fill='both', expand=True)

        # ----------
        # Market data

        market_data_frame = ttk.Frame(self.data_frame)
        ttk.Separator(market_data_frame).grid(row=0, columnspan=2, sticky='ew')

        self.market_data_profile_var = StringVar()
        if self.pm_object_copy.get_sell_purchase_profile_status():
            self.market_data_profile_var.set('single')
        else:
            self.market_data_profile_var.set('multiple')

        self.rb_single = ttk.Radiobutton(market_data_frame, text='Use single profile', value='single',
                                         variable=self.market_data_profile_var)
        self.rb_single.grid(row=1, column=0, sticky='ew')

        self.rb_several = ttk.Radiobutton(market_data_frame, text='Use multiple profiles', value='multiple',
                                          variable=self.market_data_profile_var)
        self.rb_several.grid(row=1, column=1, sticky='ew')

        self.market_data_profile_textvar = StringVar()
        try:
            path = self.pm_object_copy.get_sell_purchase_data()
            file_name = path.split('/')[-1]
            self.market_data_profile_textvar.set(file_name)
        except:
            self.market_data_profile_textvar.set('')

        ttk.Label(market_data_frame, text='Profile file/Folder').grid(row=2, column=0, sticky='ew')
        self.profile_label = ttk.Label(market_data_frame, text=self.market_data_profile_textvar.get())
        self.profile_label.grid(row=2, column=1, sticky='ew')

        self.select_profile_button = ttk.Button(market_data_frame, text='Select profile(s)',
                                                command=self.set_profile_purchase_selling)
        self.select_profile_button.grid(row=3, column=0, sticky='ew')
        self.create_market_price_template_button = ttk.Button(market_data_frame,
                                                              text='Create new Market Price Template',
                                                              command=self.create_market_price_template)
        self.create_market_price_template_button.grid(row=3, column=1, sticky='ew')

        market_data_frame.grid_columnconfigure(0, weight=1)
        market_data_frame.grid_columnconfigure(1, weight=1)
        market_data_frame.pack(fill='both', expand=True)

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

        # ------
        # Generation data
        generation_data_frame = ttk.Frame(self.data_frame)

        self.generation_profile_var = StringVar()
        if self.pm_object_copy.get_generation_profile_status():
            self.generation_profile_var.set('single')
        else:
            self.generation_profile_var.set('multiple')

        self.rb_single_generation = ttk.Radiobutton(generation_data_frame, text='Use single profile', value='single',
                                         variable=self.generation_profile_var)
        self.rb_single_generation.grid(row=0, column=0, sticky='ew')

        self.rb_several = ttk.Radiobutton(generation_data_frame, text='Use multiple profiles', value='multiple',
                                          variable=self.generation_profile_var)
        self.rb_several.grid(row=0, column=1, sticky='ew')

        self.generation_profile_textvar = StringVar()
        try:
            path_generation = self.pm_object_copy.get_generation_data()
            file_name_generation = path_generation.split('/')[-1]
            self.generation_profile_textvar.set(file_name_generation)
        except:
            self.generation_profile_textvar.set('')

        ttk.Label(generation_data_frame, text='Profile file/Folder').grid(row=1, column=0, sticky='w')
        self.profile_label = ttk.Label(generation_data_frame, text=self.generation_profile_textvar.get())
        self.profile_label.grid(row=1, column=1, sticky='ew')

        self.select_profile_button = ttk.Button(generation_data_frame, text='Select profile(s)',
                                                command=self.set_profile_generation)
        self.select_profile_button.grid(row=2, column=0, sticky='ew')

        self.create_generation_template_button = ttk.Button(generation_data_frame, text='Create new generation template',
                                                            command=self.create_generation_template)
        self.create_generation_template_button.grid(row=2, column=1, sticky='ew')

        generation_data_frame.grid_columnconfigure(0, weight=1, uniform='a')
        generation_data_frame.grid_columnconfigure(1, weight=1, uniform='a')
        generation_data_frame.grid(row=0, sticky='ew')

        # ----------
        # Market data

        market_data_frame = ttk.Frame(self.data_frame)
        ttk.Separator(market_data_frame).grid(row=0, columnspan=2, sticky='ew')

        self.market_data_profile_var = StringVar()
        if self.pm_object_copy.get_sell_purchase_profile_status():
            self.market_data_profile_var.set('single')
        else:
            self.market_data_profile_var.set('multiple')

        self.rb_single = ttk.Radiobutton(market_data_frame, text='Use single profile', value='single',
                                         variable=self.market_data_profile_var)
        self.rb_single.grid(row=1, column=0, sticky='ew')

        self.rb_several = ttk.Radiobutton(market_data_frame, text='Use multiple profiles', value='multiple',
                                          variable=self.market_data_profile_var)
        self.rb_several.grid(row=1, column=1, sticky='ew')

        self.market_data_profile_textvar = StringVar()
        try:
            path = self.pm_object_copy.get_sell_purchase_data()
            file_name = path.split('/')[-1]
            self.market_data_profile_textvar.set(file_name)
        except:
            self.market_data_profile_textvar.set('')

        ttk.Label(market_data_frame, text='Profile file/Folder').grid(row=2, column=0, sticky='ew')
        self.profile_label = ttk.Label(market_data_frame, text=self.market_data_profile_textvar.get())
        self.profile_label.grid(row=2, column=1, sticky='ew')

        self.select_profile_button = ttk.Button(market_data_frame, text='Select profile(s)',
                                                command=self.set_profile_purchase_selling)
        self.select_profile_button.grid(row=3, column=0, sticky='ew')
        self.create_market_price_template_button = ttk.Button(market_data_frame, text='Create new price template',
                                                              command=self.create_market_price_template)
        self.create_market_price_template_button.grid(row=3, column=1, sticky='ew')

        market_data_frame.grid_columnconfigure(0, weight=1, uniform='a')
        market_data_frame.grid_columnconfigure(1, weight=1, uniform='a')
        market_data_frame.grid(row=1, sticky='ew')

        self.data_frame.grid_columnconfigure(0, weight=1)
        self.data_frame.pack(fill='both', expand=True)


class ToggledFrame(tk.Frame):

    def __init__(self, parent, root, super_frame, text="", pm_object_copy=None, pm_object_original=None,
                 frame_type='general', *args, **options):

        """
        Creates Toggled Frame object, which contains Parameter, settings etc. based on the frame type

        :param parent: Interface object - to access functions of Interface
        :param root: tk.root - to create new windows
        :param super_frame: Scrollable Frame - to create widgets inside this frame
        :param text: string - to set name of toggled frame
        :param pm_object_copy: Parameter object - stores information
        :param pm_object_original: Parameter object - to restore default values
        :param frame_type: string - defines type of toggled frame which decides on functions of frame
        :param args: See Toggled Frame object
        :param options: See Toggled Frame object
        """

        self.pm_object_copy = pm_object_copy
        self.pm_object_original = pm_object_original
        self.root = root
        self.parent = parent
        self.super_frame = super_frame
        self.frame_type = frame_type

        self.show = tk.IntVar()
        self.show.set(0)

        self.box_update = False
        self.frame_update = False

        self.generator = ''
        self.stream = ''
        self.component_type = ''
        self.component = ''

        tk.Frame.__init__(self, super_frame, *args, **options)

        self.title_frame = ttk.Frame(self)
        self.title_frame.pack(fill="both", expand=1)

        ttk.Label(self.title_frame, text=text).pack(side="left", fill="x", expand=1)

        self.toggle_button = ttk.Checkbutton(self.title_frame, width=2, text='+', command=self.toggle,
                                             variable=self.show, style='Toolbutton')
        self.toggle_button.pack(side="left")

        self.sub_frame = tk.Frame(self, relief="sunken", borderwidth=1, width=root.winfo_width() - 20)

        if self.frame_type == 'general':

            self.general_assumptions_frame = GeneralAssumptionsFrame(self, self.root, self.pm_object_copy)

        elif self.frame_type == 'component':

            button_frame = tk.Frame(self.sub_frame)

            ttk.Button(button_frame, text='Add component', command=self.create_new_component_window)\
                .grid(row=0, column=0, sticky='ew')

            ttk.Button(button_frame, text='Delete components', command=self.delete_components)\
                .grid(row=0, column=1, sticky='ew')

            ttk.Button(button_frame, text='Reset all components',
                       command=self.set_components_to_default).grid(row=0, column=2, sticky='ew')

            button_frame.grid_columnconfigure(0, weight=1)
            button_frame.grid_columnconfigure(1, weight=1)
            button_frame.grid_columnconfigure(2, weight=1)

            entries = []
            for c in self.pm_object_copy.get_specific_components(component_group='final', component_type='conversion'):
                entries.append(c.get_nice_name())

            self.components_combo = ttk.Combobox(self.sub_frame, values=entries, state='readonly')
            self.components_combo.bind("<<ComboboxSelected>>", self.callbackFuncDecideComponent)
            self.components_combo.delete(0, 'end')

            button_frame.pack(fill="both", expand=True)
            self.components_combo.pack(fill='both', expand=True)
            self.components_combo.set('Choose component')

        elif self.frame_type == 'stream':

            unused_streams = self.pm_object_copy.get_specific_streams(final_stream=False)
            if unused_streams:
                self.delete_stream_button = ttk.Button(self.sub_frame, text='Delete unused streams',
                                                       command=self.delete_unused_streams)
                self.delete_stream_button.pack(fill='both', expand=True)
            else:
                self.delete_stream_button = ttk.Button(self.sub_frame, text='Delete unused streams',
                                                       command=self.delete_unused_streams, state=DISABLED)
                self.delete_stream_button.pack(fill='both', expand=True)

            self.nice_names = []
            for stream in self.pm_object_copy.get_specific_streams(final_stream=True):
                self.nice_names.append(stream.get_nice_name())

            self.combobox_stream = ttk.Combobox(self.sub_frame, values=self.nice_names, state='readonly')
            self.combobox_stream.pack(fill="both", expand=True)
            self.combobox_stream.bind("<<ComboboxSelected>>", self.callbackFuncDecideStream)
            self.combobox_stream.set('Choose stream')

        elif self.frame_type == 'storage':

            # Add storages to collection of existing storages
            self.storages_nice_names = []
            for s in self.pm_object_copy.get_specific_components('final', 'storage'):
                self.storages_nice_names.append(s.get_nice_name())

            # Add dummy storages for not yet existing storages
            for s in self.pm_object_copy.get_specific_streams(final_stream=True):

                if s.get_nice_name() not in self.storages_nice_names:

                    self.storages_nice_names.append(s.get_nice_name())

                    storage = StorageComponent(s.get_name(), s.get_nice_name(),
                                               final_unit=False, custom_unit=True)
                    self.pm_object_copy.add_component(s.get_name(), storage)

                    for p in self.pm_object_copy.get_general_parameters():
                        self.pm_object_copy.set_applied_parameter_for_component(p, s.get_name(), True)

            self.combobox_storage = ttk.Combobox(self.sub_frame, values=self.storages_nice_names, state='readonly')
            self.combobox_storage.pack(fill='both', expand=True)
            self.combobox_storage.set('Choose storage')
            self.combobox_storage.bind("<<ComboboxSelected>>", self.callbackFuncStorage)

        elif self.frame_type == 'generator':

            button_frame = tk.Frame(self.sub_frame)

            self.add_generator_button = ttk.Button(button_frame, text='Add Generator', command=self.add_generator)
            self.add_generator_button.grid(row=0, column=0, sticky='ew')

            self.delete_generator_button = ttk.Button(button_frame, text='Delete Generator',
                                                      command=self.delete_generator)
            self.delete_generator_button.grid(row=0, column=1, sticky='ew')

            button_frame.grid_columnconfigure(0, weight=1)
            button_frame.grid_columnconfigure(1, weight=1)

            button_frame.pack(fill='both', expand=True)

            generators = []
            for generator in self.pm_object_copy.get_specific_components(component_type='generator'):
                generators.append(generator.get_nice_name())

            if len(generators) == 0:
                self.delete_generator_button.config(state=DISABLED)
            else:
                self.delete_generator_button.config(state=NORMAL)

            self.components_generator_combo = ttk.Combobox(self.sub_frame, values=generators, state='readonly')
            self.components_generator_combo.pack(fill='both', expand=True)
            self.components_generator_combo.set('Choose generator')
            self.components_generator_combo.bind("<<ComboboxSelected>>", self.callbackFuncDecideGenerator)

    def toggle(self):

        # Defines the ability to toggle the window
        self.update_self_pm_object(self.parent.pm_object_copy)

        if bool(self.show.get()):
            self.sub_frame.pack(fill="x", expand=1)
            self.toggle_button.configure(text='-')
            self.box_update = True
        else:
            self.sub_frame.forget()
            self.toggle_button.configure(text='+')
            self.box_update = False
            self.frame_update = False

    def update_self_pm_object(self, pm_object):
        # Updates the Parameter object
        self.pm_object_copy = pm_object

    def update_frame(self, frame_type):
        # If changes in parameters etc. occur, the whole frame is updated so that updates are shown immediately

        if frame_type == 'general':

            if self.box_update:
                self.general_assumptions_frame.frame.destroy()

                self.general_assumptions_frame = GeneralAssumptionsFrame(self, self.root, self.pm_object_copy)

        elif frame_type == 'component':

            entries = []
            for c in self.pm_object_copy.get_specific_components('final', 'conversion'):
                entries.append(c.get_nice_name())
            self.components_combo.config(values=entries)

            if self.frame_update:

                self.component_frame.frame.destroy()

                if self.current_component_selection != '':
                    for c in self.pm_object_copy.get_specific_components('final', 'conversion'):
                        if self.current_component_selection == c.get_name():
                            component = self.pm_object_copy.get_component(self.current_component_selection)
                            component_nice_name = component.get_nice_name()
                            self.components_combo.set(component_nice_name)
                            self.component_frame = ComponentFrame(self, self.root, self.current_component_selection,
                                                                  self.pm_object_copy, self.pm_object_original)
                            self.component_frame.frame.pack(fill='both', expand=True)
                            break
                        else:
                            self.components_combo.set('Choose component')
                else:
                    self.components_combo.set('Choose component')

        elif frame_type == 'stream':

            unused_streams = self.pm_object_copy.get_specific_streams(final_stream=False)
            if unused_streams:
                self.delete_stream_button.config(state=NORMAL)
            else:
                self.delete_stream_button.config(state=DISABLED)

            self.nice_names = []
            for stream in self.pm_object_copy.get_specific_streams(final_stream=True):
                self.nice_names.append(stream.get_nice_name())
            self.combobox_stream.config(values=self.nice_names)

            self.stream = self.combobox_stream.get()

            if self.frame_update:
                self.stream_frame.frame.destroy()

                if self.stream not in self.nice_names:
                    self.stream = ''
                    self.combobox_stream.set('Choose stream')

                if self.stream != '':

                    self.stream_frame = StreamFrame(self, self.root, self.stream, self.pm_object_copy,
                                                    self.pm_object_original)
                    self.stream_frame.frame.pack(fill="both", expand=True)

        elif frame_type == 'storage':

            # Add storages to collection of existing storages
            self.storages_nice_names = []
            for s in self.pm_object_copy.get_specific_components('final', 'storage'):
                self.storages_nice_names.append(s.get_nice_name())

            # Add dummy storages for not yet existing storages
            for s in self.pm_object_copy.get_specific_streams(final_stream=True):

                if s.get_nice_name() not in self.storages_nice_names:

                    self.storages_nice_names.append(s.get_nice_name())

                    storage = StorageComponent(s.get_name(), s.get_nice_name(),
                                               final_unit=False, custom_unit=True)
                    self.pm_object_copy.add_component(s.get_name(), storage)

                    for p in self.pm_object_copy.get_general_parameters():
                        self.pm_object_copy.set_applied_parameter_for_component(p, s.get_name(), True)

            self.combobox_storage.config(values=self.storages_nice_names)

            # Check if stream still in system and set combobox to stream or to "choose storage"
            if self.frame_update:

                self.storage_frame.frame.destroy()

                if self.pm_object_copy.get_nice_name(self.storage_stream) in self.storages_nice_names:

                    self.combobox_storage.set(self.pm_object_copy.get_nice_name(self.storage_stream))

                    self.storage_frame = StorageFrame(self, self.root, self.storage_stream,
                                          self.pm_object_copy, self.pm_object_original)
                    self.storage_frame.frame.pack(fill='both', expand=True)

                else:
                    self.combobox_storage.set('Choose Storage')

        elif frame_type == 'generator':
            no_new_frame = False

            if self.box_update:

                generators = []
                generators_abbreviations = []
                for generator in self.pm_object_copy.get_specific_components(component_type='generator'):
                    generators.append(generator.get_nice_name())
                    generators_abbreviations.append(generator.get_name())

                self.components_generator_combo.config(values=generators)

                if self.generator == '':  # Case no generator was chosen
                    no_new_frame = True
                    self.components_generator_combo.set('Choose generator')
                else:
                    if self.generator not in generators_abbreviations:
                        self.components_generator_combo.set('Choose generator')
                        no_new_frame = True

                if len(generators) == 0:
                    self.delete_generator_button.config(state=DISABLED)
                else:
                    self.delete_generator_button.config(state=NORMAL)

            if self.frame_update:
                self.generator_frame.frame.destroy()

                if not no_new_frame:

                    self.generator_frame = GeneratorFrame(self, self.root, self.generator,
                                                          self.pm_object_copy, self.pm_object_original)
                    self.generator_frame.frame.pack(fill='both', expand=True)

    def callbackFuncDecideComponent(self, event=None):
        # Function of component combo box
        # Destroy old frame (if exist) and create new frame

        try:
            self.component_frame.frame.destroy()
        except:
            pass

        nice_name = self.components_combo.get()
        self.current_component_selection = self.pm_object_copy.get_abbreviation(nice_name)

        self.component_frame = ComponentFrame(self, self.root, self.current_component_selection,
                                              self.pm_object_copy, self.pm_object_original)
        self.component_frame.frame.pack(fill="both", expand=True)

        self.frame_update = True

    def callbackFuncDecideStream(self, event=None):
        # Function of stream combo box
        # Destroy old frame (if exist) and create new frame

        try:
            self.stream_frame.frame.destroy()
        except:
            pass

        self.stream = self.combobox_stream.get()

        self.stream_frame = StreamFrame(self, self.root, self.stream, self.pm_object_copy, self.pm_object_original)
        self.stream_frame.frame.pack(fill="both", expand=True)

        self.frame_update = True

    def callbackFuncStorage(self, event=None):
        # Function of storage combo box
        # Destroy old frame (if exist) and create new frame

        try:
            self.storage_frame.frame.destroy()
        except:
            pass

        self.storage_stream = self.pm_object_copy.get_abbreviation(self.combobox_storage.get())

        self.storage_frame = StorageFrame(self, self.root, self.storage_stream,
                                          self.pm_object_copy, self.pm_object_original)
        self.storage_frame.frame.pack(fill='both', expand=True)

        self.frame_update = True

    def callbackFuncDecideGenerator(self, event=None):
        # Function of generator combo box
        # Destroy old frame (if exist) and create new frame

        try:
            self.generator_frame.frame.destroy()
        except:
            pass

        self.generator = self.pm_object_copy.get_abbreviation(self.components_generator_combo.get())

        self.generator_frame = GeneratorFrame(self, self.root, self.generator,
                                              self.pm_object_copy, self.pm_object_original)
        self.generator_frame.frame.pack(fill="both", expand=True)

        self.frame_update = True

    def set_general_assumptions_to_default(self):
        # Set general assumption parameters to default

        exclude = ['wacc', 'covered_period']

        for p in self.pm_object_copy.get_general_parameters():
            self.pm_object_copy.set_general_parameter_value(p, self.pm_object_original.get_general_parameter_value(p))

            if p in exclude:
                continue

            for c in self.pm_object_copy.get_specific_components('final'):
                self.pm_object_copy.set_applied_parameter_for_component(p,
                                                                        c.get_name(),
                                                                        self.pm_object_original
                                                                        .get_applied_parameter_for_component(p,
                                                                                                             c.get_name()))

        self.parent.pm_object_copy = self.pm_object_copy
        self.parent.update_widgets()

    def set_components_to_default(self):
        # Set all component parameters and streams to default

        for component in self.pm_object_copy.get_specific_components(component_type='conversion'):
            self.pm_object_copy.remove_component_entirely(component.get_name())

        for component in self.pm_object_original.get_specific_components(component_type='conversion'):
            copied_component = component.__copy__()
            self.pm_object_copy.add_component(component.get_name(), copied_component)

        self.parent.pm_object_copy = self.pm_object_copy
        self.parent.update_widgets()

    def delete_unused_streams(self):

        def delete_chosen_streams():
            for s in [*check_stream.keys()]:
                if check_stream[s].get():
                    self.pm_object_copy.remove_stream_entirely(s)
            delete_streams.destroy()

            self.parent.pm_object_copy = self.pm_object_copy
            self.parent.update_widgets()

        def kill_only():
            delete_streams.destroy()

        delete_streams = Toplevel(self.root)
        delete_streams.title('')
        delete_streams.grab_set()

        unused_streams = self.pm_object_copy.get_specific_streams(final_stream=False)
        i = 0
        check_stream = {}
        for stream in unused_streams:
            check_stream[stream.get_name()] = BooleanVar()
            ttk.Checkbutton(delete_streams, text=stream.get_nice_name(), variable=check_stream[stream.get_name()])\
                .grid(row=i, columnspan=2, sticky='w')
            i += 1

        ttk.Button(delete_streams, text='Delete', command=delete_chosen_streams).grid(row=i, column=0, sticky='ew')
        ttk.Button(delete_streams, text='Cancel', command=kill_only).grid(row=i, column=1, sticky='ew')

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

        newWindow = Toplevel(self.root)
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
        for gen in self.pm_object_copy.get_specific_components(component_type='generator'):
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

    def create_new_component_window(self):
        # Adds dummy component which then can be adjusted
        AddNewComponentWindow(self.parent, self.root, self.pm_object_copy)

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

            for stream in self.pm_object_copy.get_specific_streams('final'):
                self.pm_object_copy.remove_stream(stream.get_name())

            self.parent.pm_object_copy = self.pm_object_copy
            self.parent.update_widgets()

            delete_component_window.destroy()

        delete_component_window = Toplevel(self.root)
        delete_component_window.grab_set()

        delete_component_dict = {}

        var_list = []
        i = 0

        for c in self.pm_object_copy.get_specific_components(component_group='final', component_type='conversion'):
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
        delete_component_window.grid_columnconfigure(2, weight=1, uniform='a')

        delete_component_window.mainloop()


class SettingWindow:

    def getFolderData(self):
        folder_path = filedialog.askdirectory() + '/'
        if folder_path != '/':
            self.folder_data = folder_path
            self.path_data = folder_path
            self.choose_data_folder_var.set(self.folder_data)

    def getFolderResult(self):
        folder_path = filedialog.askdirectory() + '/'
        if folder_path != '/':
            self.folder_result = folder_path
            self.path_result = folder_path
            self.choose_result_folder_var.set(self.folder_result)

    def getFolderSettings(self):
        folder_path = filedialog.askdirectory() + '/'
        if folder_path != '/':
            self.folder_settings = folder_path
            self.path_settings = folder_path
            self.choose_saved_settings_folder_var.set(self.folder_settings)

    def getFolderPathCustom(self):
        folder_path = filedialog.askopenfilename()
        if folder_path != '':
            self.selected_custom = folder_path
            self.path_custom = folder_path
            self.choose_custom_path_label_var.set(self.selected_custom)

    def getFolderPathOptimize(self):
        folder_path = filedialog.askdirectory() + '/'
        if folder_path != '/':
            self.folder_optimize = folder_path
            self.path_optimize = folder_path
            self.choose_optimize_folder_var.set(self.folder_optimize)

    def getFolderPathResultVisualization(self):
        folder_path = filedialog.askdirectory() + '/'
        if folder_path != '/':
            self.folder_visualization = folder_path
            self.path_visualization = folder_path
            self.choose_visualize_folder_var.set(self.folder_visualization)

    def radiobutton_command(self):

        self.choose_result_folder_button.config(state=NORMAL)
        self.choose_result_folder_label.config(state=NORMAL)

        self.choose_settings_folder_button.config(state=NORMAL)
        self.choose_settings_folder_label.config(state=NORMAL)

        self.optimize_only_path_label.config(state=DISABLED)
        self.optimize_only_path_button.config(state=DISABLED)

        self.choose_custom_path_label.config(state=DISABLED)
        self.choose_custom_path_button.config(state=DISABLED)

        self.visualize_only_path_button.config(state=DISABLED)
        self.visualize_only_path_button.config(state=DISABLED)

        if self.radiobutton_variable.get() == 'custom':
            self.choose_custom_path_label.config(state=NORMAL)
            self.choose_custom_path_button.config(state=NORMAL)

        elif self.radiobutton_variable.get() == 'optimize_only':

            self.choose_settings_folder_button.config(state=DISABLED)
            self.choose_settings_folder_label.config(state=DISABLED)

            self.optimize_only_path_label.config(state=NORMAL)
            self.optimize_only_path_button.config(state=NORMAL)

        elif self.radiobutton_variable.get() == 'visualize_only':
            self.choose_result_folder_button.config(state=DISABLED)
            self.choose_result_folder_label.config(state=DISABLED)

            self.choose_settings_folder_button.config(state=DISABLED)
            self.choose_settings_folder_label.config(state=DISABLED)

            self.visualize_only_path_button.config(state=NORMAL)
            self.visualize_only_path_button.config(state=NORMAL)

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

        if (check_empty(self.folder_data)) | (check_empty(self.folder_result)) | (check_empty(self.folder_settings)):
            window_no_paths = Toplevel(self.window)
            ttk.Label(window_no_paths,
                      text='Please choose data folder, result folder and location for saved settings').pack()
            ttk.Button(window_no_paths, text='Ok', command=kill_no_paths_window).pack()

        elif (self.radiobutton_variable.get() == 'custom') & (check_empty(self.selected_custom)):
            window_no_paths = Toplevel(self.window)
            ttk.Label(window_no_paths, text='Please choose setting').pack()
            ttk.Button(window_no_paths, text='Ok', command=kill_no_paths_window).pack()

        elif (self.radiobutton_variable.get() == 'optimize_only') & (check_empty(self.folder_optimize)):
            window_no_paths = Toplevel(self.window)
            ttk.Label(window_no_paths, text='Please choose folder with settings').pack()
            ttk.Button(window_no_paths, text='Ok', command=kill_no_paths_window).pack()

        elif (self.radiobutton_variable.get() == 'visualize_only') & (check_empty(self.folder_visualization)):
            window_no_paths = Toplevel(self.window)
            ttk.Label(window_no_paths, text='Please choose result folder').pack()
            ttk.Button(window_no_paths, text='Ok', command=kill_no_paths_window).pack()

        else:

            self.base_settings.loc['path_data'] = self.folder_data
            self.base_settings.loc['path_result'] = self.folder_result
            self.base_settings.loc['path_settings'] = self.folder_settings
            self.base_settings.loc['path_custom'] = self.selected_custom
            self.base_settings.loc['chosen_setting'] = self.radiobutton_variable.get()
            self.base_settings.loc['path_optimize'] = self.folder_optimize
            self.base_settings.loc['solver'] = self.solver_combobox.get()
            self.base_settings.loc['path_visualization'] = self.folder_visualization

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
        self.path_settings = self.base_settings.loc['path_settings'].values[0]
        self.path_custom = self.base_settings.loc['path_custom'].values[0]
        self.path_optimize = self.base_settings.loc['path_optimize'].values[0]
        self.solver = self.base_settings.loc['solver'].values[0]
        self.path_visualization = self.base_settings.loc['path_visualization'].values[0]

        radiobutton_frame = ttk.Frame(self.frame)
        radiobutton_frame.grid_columnconfigure(0, weight=1, uniform='a')
        radiobutton_frame.grid_columnconfigure(1, weight=1, uniform='a')
        radiobutton_frame.grid_columnconfigure(2, weight=1, uniform='a')
        radiobutton_frame.grid_columnconfigure(3, weight=1, uniform='a')

        self.radiobutton_variable = StringVar()

        if (type(self.base_settings.loc['chosen_setting'].values[0]) != str) \
                | (self.base_settings.loc['chosen_setting'].values[0] == ''):
            self.radiobutton_variable.set('new')
        else:
            self.radiobutton_variable.set(self.base_settings.loc['chosen_setting'].values[0])

        tk.Radiobutton(radiobutton_frame, text='New project', variable=self.radiobutton_variable,
                       value='new', command=self.radiobutton_command).grid(row=0, column=0, sticky='ew')

        tk.Radiobutton(radiobutton_frame, text='Load existing project', variable=self.radiobutton_variable,
                       value='custom', command=self.radiobutton_command).grid(row=0, column=1, sticky='ew')

        tk.Radiobutton(radiobutton_frame, text='Optimize existing projects', variable=self.radiobutton_variable,
                       value='optimize_only', command=self.radiobutton_command).grid(row=0, column=2, sticky='ew')

        tk.Radiobutton(radiobutton_frame, text='Visualize project', variable=self.radiobutton_variable,
                       value='visualize_only', command=self.radiobutton_command).grid(row=0, column=3, sticky='ew')

        radiobutton_frame.grid(row=0, columnspan=2, sticky='ew')

        self.choose_data_folder_var = StringVar()
        self.choose_result_folder_var = StringVar()
        self.choose_saved_settings_folder_var = StringVar()
        self.choose_custom_path_label_var = StringVar()
        self.choose_optimize_folder_var = StringVar()
        self.choose_solver_var = StringVar()
        self.choose_visualize_folder_var = StringVar()

        if type(self.path_result) == str:

            self.choose_data_folder_var.set(self.path_data)
            self.folder_data = self.path_data

            self.choose_result_folder_var.set(self.path_result)
            self.folder_result = self.path_result

            self.choose_saved_settings_folder_var.set(self.path_settings)
            self.folder_settings = self.path_settings

            self.choose_custom_path_label_var.set(self.path_custom)
            self.selected_custom = self.path_custom

            self.choose_optimize_folder_var.set(self.path_optimize)
            self.folder_optimize = self.path_optimize

            self.choose_solver_var.set(self.solver)

            self.choose_visualize_folder_var.set(self.path_visualization)
            self.folder_visualization = self.path_visualization

        else:
            self.choose_data_folder_var.set('')
            self.choose_result_folder_var.set('')
            self.choose_saved_settings_folder_var.set('')
            self.choose_custom_path_label_var.set('')
            self.choose_optimize_folder_var.set('')
            self.choose_solver_var.set('')
            self.choose_visualize_folder_var.set('')

            self.folder_data = None
            self.selected_custom = None
            self.folder_optimize = None
            self.folder_result = None
            self.folder_settings = None
            self.folder_visualization = None

        self.choose_data_folder_button = ttk.Button(self.frame, text='Select data folder',
                                                    command=self.getFolderData)
        self.choose_data_folder_button.grid(row=1, column=0, sticky='ew')

        self.choose_data_folder_label = tk.Label(self.frame, textvariable=self.choose_data_folder_var)
        self.choose_data_folder_label.grid(row=1, column=1, sticky='w')

        self.choose_result_folder_button = ttk.Button(self.frame, text='Select result folder',
                                                      command=self.getFolderResult)
        self.choose_result_folder_button.grid(row=2, column=0, sticky='ew')

        self.choose_result_folder_label = tk.Label(self.frame, textvariable=self.choose_result_folder_var)
        self.choose_result_folder_label.grid(row=2, column=1, sticky='w')

        self.choose_settings_folder_button = ttk.Button(self.frame, text='Select folder for saved settings',
                                                        command=self.getFolderSettings)
        self.choose_settings_folder_button.grid(row=3, column=0, sticky='ew')

        self.choose_settings_folder_label = tk.Label(self.frame, textvariable=self.choose_saved_settings_folder_var)
        self.choose_settings_folder_label.grid(row=3, column=1, sticky='w')

        self.choose_custom_path_button = ttk.Button(self.frame, text='Select setting',
                                                   command=self.getFolderPathCustom)
        self.choose_custom_path_button.grid(row=4, column=0, sticky='ew')

        self.choose_custom_path_label = tk.Label(self.frame, textvariable=self.choose_custom_path_label_var)
        self.choose_custom_path_label.grid(row=4, column=1, sticky='w')

        self.optimize_only_path_button = ttk.Button(self.frame, text='Select settings folder',
                                                    command=self.getFolderPathOptimize)
        self.optimize_only_path_button.grid(row=5, column=0, sticky='ew')

        self.optimize_only_path_label = tk.Label(self.frame, textvariable=self.choose_optimize_folder_var)
        self.optimize_only_path_label.grid(row=5, column=1, sticky='w')

        tk.Label(self.frame, text='Solver').grid(row=6, column=0, sticky='w')
        solvers = ['gurobi', 'cplex', 'glpk']
        self.solver_combobox = ttk.Combobox(self.frame, values=solvers, state='readonly')
        self.solver_combobox.set(self.choose_solver_var.get())
        self.solver_combobox.grid(row=6, column=1, sticky='ew')

        self.visualize_only_path_button = ttk.Button(self.frame, text='Select result for visualization',
                                                    command=self.getFolderPathResultVisualization)
        self.visualize_only_path_button.grid(row=7, column=0, sticky='ew')

        self.visualize_only_path_label = tk.Label(self.frame, textvariable=self.choose_visualize_folder_var)
        self.visualize_only_path_label.grid(row=7, column=1, sticky='w')

        button_frame = ttk.Frame(self.frame)
        button_frame.grid_columnconfigure(0, weight=1, uniform='a')
        button_frame.grid_columnconfigure(1, weight=1, uniform='a')

        self.button_ok = ttk.Button(button_frame, text='Ok', command=self.kill_window)
        self.button_ok.grid(row=0, column=0, sticky='ew')
        self.button_ok = ttk.Button(button_frame, text='Cancel', command=self.kill_window_without)
        self.button_ok.grid(row=0, column=1, sticky='ew')

        button_frame.grid(row=8, columnspan=2, sticky='ew')

        self.radiobutton_command()
        self.window.mainloop()
