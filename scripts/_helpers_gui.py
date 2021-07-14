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

from objects_formulation import GenerationComponent

import os


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

            self.components_combo = ttk.Combobox(self.sub_frame)

            entries = []
            for c in self.pm_object_copy.get_specific_components(component_group='final', component_type='conversion'):
                entries.append(c.get_nice_name())
            self.components_combo.config(values=entries)
            self.components_combo.bind("<<ComboboxSelected>>", self.callbackFuncDecideComponent)
            self.components_combo.delete(0, 'end')

            button_frame.pack(fill="both", expand=True)
            self.components_combo.pack(fill='both', expand=True)
            self.components_combo.set('Choose component')

        elif self.frame_type == 'stream':

            self.nice_names = []
            for stream in self.pm_object_copy.get_specific_streams('final'):
                self.nice_names.append(stream.get_nice_name())

            self.combobox_stream = ttk.Combobox(self.sub_frame, values=self.nice_names)
            self.combobox_stream.pack(fill="both", expand=True)
            self.combobox_stream.bind("<<ComboboxSelected>>", self.callbackFuncDecideStream)
            self.combobox_stream.set('Choose stream')

        elif self.frame_type == 'storage':

            self.storage_components_nice_names = []
            for s in self.pm_object_copy.get_specific_components(component_group='final', component_type='storage'):
                self.storage_components_nice_names.append(s.get_nice_name())

            self.combobox_storage = ttk.Combobox(self.sub_frame, values=self.storage_components_nice_names)
            self.combobox_storage.pack(fill='both', expand=True)
            self.combobox_storage.set('Choose storage')
            self.combobox_storage.bind("<<ComboboxSelected>>", self.callbackFuncStorage)

        elif self.frame_type == 'generator':

            self.add_generator_button = ttk.Button(self.sub_frame, text='Add generator', command=self.add_generator)
            self.add_generator_button.pack(fill='both', expand=True)

            generators = []
            for generator in self.pm_object_copy.get_specific_components(component_type='generator'):
                generators.append(generator.get_nice_name())

            self.components_generator_combo = ttk.Combobox(self.sub_frame, values=generators)
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

            self.stream = self.combobox_stream.get()

            self.nice_names = []
            for stream in self.pm_object_copy.get_specific_streams('final'):
                self.nice_names.append(stream.get_nice_name())
            self.combobox_stream.config(values=self.nice_names)

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

            self.storage_components_nice_names = []
            for s in self.pm_object_copy.get_specific_components('final', 'storage'):
                self.storage_components_nice_names.append(s.get_nice_name())

            self.combobox_storage.config(values=self.storage_components_nice_names)

            if self.frame_update:

                self.storage_frame.frame.destroy()

                final_storages = []
                for storage in self.pm_object_copy.get_specific_components('final', 'storage'):
                    final_storages.append(storage.get_name())

                if self.storage_stream in final_storages:
                    self.combobox_storage.set(self.pm_object_copy.get_component(self.storage_stream).get_nice_name())

                    self.storage_frame = StorageFrame(self, self.root, self.storage_stream,
                                          self.pm_object_copy, self.pm_object_original)
                    self.storage_frame.frame.pack(fill='both', expand=True)

                else:
                    self.storage_stream = 'Choose storage'
                    self.combobox_storage.set(self.storage_stream)

                    self.frame_update = False

        elif frame_type == 'generator':
            no_new_frame = False

            if self.box_update:

                generators = []
                for generator in self.pm_object_copy.get_specific_components(component_type='generator'):
                    generators.append(generator.get_nice_name())

                self.components_generator_combo.config(values=generators)

                if self.generator == '':  # Case no generator was chosen
                    no_new_frame = True
                    self.components_generator_combo.set('Choose generator')
                else:
                    if self.pm_object_copy.get_component(self.generator).get_nice_name() not in generators:  # Case chosen generator was deleted
                        self.components_generator_combo.set('Choose generator')
                        no_new_frame = True

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
            self.pm_object_copy.add_component(component.get_name(), component.__copy__())

        self.parent.pm_object_copy = self.pm_object_copy
        self.parent.update_widgets()

    def add_generator(self):
        # Adds dummy generator, which then can be adjusted

        def get_generator_and_kill():
            nice_name = nice_name_entry.get()
            abbreviation = abbreviation_entry.get()

            generator = GenerationComponent(abbreviation, nice_name, final_unit=True)
            self.pm_object_copy.add_component(abbreviation, generator)

            for p in self.pm_object_copy.get_general_parameters():
                self.pm_object_copy.set_applied_parameter_for_component(p, abbreviation, True)

            self.parent.pm_object_copy = self.pm_object_copy
            self.parent.update_widgets()

            newWindow.destroy()

        def kill_only():
            newWindow.destroy()

        newWindow = Toplevel(self.root)

        Label(newWindow, text='Nice name').grid(row=0, column=0)
        nice_name_entry = ttk.Entry(newWindow)
        nice_name_entry.grid(row=0, column=1)

        Label(newWindow, text='Abbreviation').grid(row=1, column=0)
        abbreviation_entry = ttk.Entry(newWindow)
        abbreviation_entry.grid(row=1, column=1)

        Button(newWindow, text='OK', command=get_generator_and_kill).grid(row=2, column=0)
        Button(newWindow, text='Cancel', command=kill_only).grid(row=2, column=1)

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

        ttk.Button(delete_component_window, text='Delete components', command=delete_and_kill).grid(row=i + 1, column=0, sticky='we')
        ttk.Button(delete_component_window, text='Cancel', command=kill_only).grid(row=i + 1, column=1, sticky='we')

        delete_component_window.grid_columnconfigure(0, weight=1)
        delete_component_window.grid_columnconfigure(2, weight=1)

        delete_component_window.mainloop()


class SettingWindow:

    def getFolderData(self):
        self.folder_data = filedialog.askdirectory() + '/'
        self.choose_data_folder_var.set(self.folder_data)

    def getFolderResult(self):
        self.folder_result = filedialog.askdirectory() + '/'
        self.choose_result_folder_var.set(self.folder_result)

    def getFolderSettings(self):
        self.folder_settings = filedialog.askdirectory() + '/'
        self.choose_saved_settings_folder_var.set(self.folder_settings)

    def getFolderPathCustom(self):
        self.selected_custom = filedialog.askopenfilename()
        self.choose_custom_path_label_var.set(self.selected_custom)

    def getFolderPathOptimize(self):
        self.folder_optimize = filedialog.askdirectory() + '/'
        self.choose_optimize_folder_var.set(self.folder_optimize)

    def radiobutton_command(self):

        if self.radiobutton_variable.get() == 'new':

            self.optimize_only_path_label.config(state=DISABLED)
            self.optimize_only_path_button.config(state=DISABLED)

            self.choose_custom_path_label.config(state=DISABLED)
            self.choose_custom_path_button.config(state=DISABLED)

        elif self.radiobutton_variable.get() == 'custom':

            self.optimize_only_path_label.config(state=DISABLED)
            self.optimize_only_path_button.config(state=DISABLED)

            self.choose_custom_path_label.config(state=NORMAL)
            self.choose_custom_path_button.config(state=NORMAL)

        elif self.radiobutton_variable.get() == 'optimize_only':

            self.optimize_only_path_label.config(state=NORMAL)
            self.optimize_only_path_button.config(state=NORMAL)

            self.choose_custom_path_label.config(state=DISABLED)
            self.choose_custom_path_button.config(state=DISABLED)
            
        else:
            self.optimize_only_path_label.config(state=DISABLED)
            self.optimize_only_path_button.config(state=DISABLED)

            self.choose_custom_path_label.config(state=DISABLED)
            self.choose_custom_path_button.config(state=DISABLED)

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

        else:

            self.base_settings.loc['path_data'] = self.folder_data
            self.base_settings.loc['path_result'] = self.folder_result
            self.base_settings.loc['path_settings'] = self.folder_settings
            self.base_settings.loc['path_custom'] = self.selected_custom
            self.base_settings.loc['chosen_setting'] = self.radiobutton_variable.get()
            self.base_settings.loc['path_optimize'] = self.folder_optimize

            self.base_settings.to_excel(os.getcwd() + '/base_settings.xlsx', index=True)

            self.go_on = True
            self.window.destroy()

    def kill_window_without(self):
        self.go_on = False
        self.window.destroy()

    def __init__(self):

        self.window = Tk()
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

        radiobutton_frame = ttk.Frame(self.frame)
        radiobutton_frame.grid_columnconfigure(0, weight=1)
        radiobutton_frame.grid_columnconfigure(1, weight=1)
        radiobutton_frame.grid_columnconfigure(2, weight=1)

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

        radiobutton_frame.grid(row=0, columnspan=2, sticky='ew')

        self.choose_data_folder_var = StringVar()
        self.choose_result_folder_var = StringVar()
        self.choose_saved_settings_folder_var = StringVar()
        self.choose_custom_path_label_var = StringVar()
        self.choose_optimize_folder_var = StringVar()

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

        else:
            self.choose_data_folder_var.set('')
            self.choose_result_folder_var.set('')
            self.choose_saved_settings_folder_var.set('')
            self.choose_custom_path_label_var.set('')
            self.choose_optimize_folder_var.set('')

            self.folder_data = None
            self.selected_custom = None
            self.folder_optimize = None
            self.folder_result = None
            self.folder_settings = None

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

        button_frame = ttk.Frame(self.frame)
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)

        self.button_ok = ttk.Button(button_frame, text='Ok', command=self.kill_window)
        self.button_ok.grid(row=0, column=0, sticky='ew')
        self.button_ok = ttk.Button(button_frame, text='Cancel', command=self.kill_window_without)
        self.button_ok.grid(row=0, column=1, sticky='ew')

        button_frame.grid(row=6, columnspan=2, sticky='ew')

        self.radiobutton_command()
        self.window.mainloop()