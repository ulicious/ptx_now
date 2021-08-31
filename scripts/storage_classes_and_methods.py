import tkinter as tk
from tkinter import ttk
from tkinter import *
from objects_formulation import StorageComponent


class StorageFrame:

    def adjust_values(self):

        def activate_entry_limiting_component():
            if self.limiting_component_checkbox_var.get():
                limit_cap_component.configure(state=NORMAL)
                limit_cap_component_ratio_entry.configure(state=NORMAL)
            else:
                limit_cap_component.configure(state=DISABLED)
                limit_cap_component_ratio_entry.configure(state=DISABLED)

        def safe_adjustments():

            self.storage_object.set_capex(self.capex_entry_var.get())
            self.storage_object.set_maintenance(str(float(self.maintenance_entry_var.get()) / 100))
            self.storage_object.set_lifetime(self.lifetime_entry_var.get())
            self.storage_object.set_charging_efficiency(str(float(self.charging_entry_var.get()) / 100))
            self.storage_object.set_discharging_efficiency(str(float(self.discharging_entry_var.get()) / 100))
            self.storage_object.set_min_soc(str(float(self.min_soc_entry_var.get()) / 100))
            self.storage_object.set_max_soc(str(float(self.max_soc_entry_var.get()) / 100))
            self.storage_object.set_initial_soc(str(float(self.initial_soc_entry_var.get()) / 100))
            self.storage_object.set_ratio_capacity_p(self.ratio_capacity_p_entry_var.get())

            if self.limiting_component_checkbox_var.get():
                self.storage_object.set_limitation(True)
                self.storage_object.set_storage_limiting_component(self.pm_object.get_abbreviation(limit_cap_component.get()))
                self.storage_object.set_storage_limiting_component_ratio(self.limiting_component_ratio_entry_var.get())
            else:
                self.storage_object.set_limitation(False)

            self.parent.parent.pm_object_copy = self.pm_object
            self.parent.parent.update_widgets()

            newWindow.destroy()

        def kill_only():
            newWindow.destroy()

        newWindow = Toplevel(self.root)
        newWindow.title('Adjust Storage')

        newWindow.grid_columnconfigure(0, weight=1)
        newWindow.grid_columnconfigure(1, weight=1)
        newWindow.grid_columnconfigure(2, weight=1)

        stream_unit = self.stream_object.get_unit()

        tk.Label(newWindow, text='CAPEX [€/' + stream_unit + ']').grid(row=0, column=0, sticky='w')
        capex_entry = tk.Entry(newWindow, text=self.capex_entry_var)
        capex_entry.grid(row=0, column=1, columnspan=2, sticky='ew')

        tk.Label(newWindow, text='Maintenance [%]').grid(row=1, column=0, sticky='w')
        maintenance_entry = tk.Entry(newWindow, text=self.maintenance_entry_var)
        maintenance_entry.grid(row=1, column=1, columnspan=2, sticky='ew')

        tk.Label(newWindow, text='Lifetime [Years]').grid(row=3, column=0, sticky='w')
        lifetime_entry = tk.Entry(newWindow, text=self.lifetime_entry_var)
        lifetime_entry.grid(row=3, column=1, columnspan=2, sticky='ew')

        tk.Label(newWindow, text='Charging efficiency [%]').grid(row=4, column=0, sticky='w')
        charging_entry = tk.Entry(newWindow, text=self.charging_entry_var)
        charging_entry.grid(row=4, column=1, columnspan=2, sticky='ew')

        tk.Label(newWindow, text='Discharging efficiency [%]').grid(row=5, column=0, sticky='w')
        discharging_entry = tk.Entry(newWindow, text=self.discharging_entry_var)
        discharging_entry.grid(row=5, column=1, columnspan=2, sticky='ew')

        tk.Label(newWindow, text='Minimal SOC [%]').grid(row=6, column=0, sticky='w')
        min_soc_entry = tk.Entry(newWindow, text=self.min_soc_entry_var)
        min_soc_entry.grid(row=6, column=1, columnspan=2, sticky='ew')

        tk.Label(newWindow, text='Maximal SOC [%]').grid(row=7, column=0, sticky='w')
        max_soc_entry = tk.Entry(newWindow, text=self.max_soc_entry_var)
        max_soc_entry.grid(row=7, column=1, columnspan=2, sticky='ew')

        tk.Label(newWindow, text='Initial SOC [%]').grid(row=8, column=0, sticky='w')
        initial_soc_entry = tk.Entry(newWindow, text=self.initial_soc_entry_var)
        initial_soc_entry.grid(row=8, column=1, columnspan=2, sticky='ew')

        ttk.Label(newWindow, text='Ratio between storage capacity and power [hours]').grid(row=9, column=0, sticky='w')
        ratio_capacity_p_entry = tk.Entry(newWindow, text=self.ratio_capacity_p_entry_var)
        ratio_capacity_p_entry.grid(row=9, column=1, columnspan=2, sticky='ew')

        checkbutton_limit_capacity_to_component = tk.Checkbutton(newWindow,
                                                                 text='Limit capacity to component input',
                                                                 variable=self.limiting_component_checkbox_var,
                                                                 command=activate_entry_limiting_component,
                                                                 onvalue=True,
                                                                 offvalue=False)
        checkbutton_limit_capacity_to_component.grid(row=10, column=0, sticky='w')

        entries = []
        for entry in self.pm_object.get_specific_components('final', 'conversion'):
            if self.stream in entry.get_streams():
                entries.append(entry.get_nice_name())

        limit_cap_component = ttk.Combobox(newWindow, values=entries, state='readonly')
        limit_cap_component.grid(row=10, column=1, sticky='w')

        ttk.Label(newWindow, text='Ratio between storage capacity and limiting component capacity [hours]').grid(row=11, column=0, sticky='w')
        limit_cap_component_ratio_entry = ttk.Entry(newWindow, text=self.limiting_component_ratio_entry_var)
        limit_cap_component_ratio_entry.grid(row=11, column=1, sticky='w')

        if self.limiting_component_checkbox_var.get():
            limit_cap_component.set(self.storage_object.get_storage_limiting_component())
        else:
            limit_cap_component.config(state=DISABLED)
            limit_cap_component.set('')
            limit_cap_component_ratio_entry.config(state=DISABLED)

        button_frame = ttk.Frame(newWindow)
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)

        ttk.Button(button_frame, text='Ok', command=safe_adjustments).grid(row=0, column=0, sticky='ew')
        ttk.Button(button_frame, text='Cancel', command=kill_only).grid(row=0, column=1, sticky='ew')

        button_frame.grid(row=12, columnspan=2, sticky='ew')

    def set_storage_settings_to_default(self):

        if self.stream in self.pm_object_original.get_specific_components('final', 'storage'):
            self.pm_object.remove_component_entirely(self.stream)

            storage_original = self.pm_object_original.get_component(self.stream)
            self.pm_object.add_component(self.stream, storage_original.__copy__())

        self.parent.parent.pm_object_copy = self.pm_object
        self.parent.parent.update_widgets()

    def create_storage(self):

        # Set storage settings
        # Check if storage object exits but is not set

        if self.storable_var.get():
            self.storage_object.set_final(True)
        else:
            self.storage_object.set_final(False)

        self.parent.parent.pm_object_copy = self.pm_object
        self.parent.parent.update_widgets()

    def initialize_storage_frame(self):

        self.storable_checkbox.config(text='Storage available?')
        self.storable_checkbox.grid(row=0, column=0, sticky='w')

        if self.storable_var.get():

            storage = self.pm_object.get_component(self.stream)

            self.capex = storage.get_capex()
            self.maintenance = round(100 * storage.get_maintenance(), 2)
            self.lifetime = storage.get_lifetime()
            self.charging_efficiency = 100 * float(storage.get_charging_efficiency())
            self.discharging_efficiency = 100 * float(storage.get_discharging_efficiency())
            self.min_soc = 100 * float(storage.get_min_soc())
            self.max_soc = 100 * float(storage.get_max_soc())
            self.initial_soc = 100 * float(storage.get_initial_soc())
            self.ratio_capacity_p = storage.get_ratio_capacity_p()

            self.capex_entry_var.set(self.capex)
            self.maintenance_entry_var.set(self.maintenance)
            self.lifetime_entry_var.set(self.lifetime)
            self.charging_entry_var.set(self.charging_efficiency)
            self.discharging_entry_var.set(self.discharging_efficiency)
            self.min_soc_entry_var.set(self.min_soc)
            self.max_soc_entry_var.set(self.max_soc)
            self.initial_soc_entry_var.set(self.initial_soc)
            self.ratio_capacity_p_entry_var.set(self.ratio_capacity_p)

            stream_unit = self.pm_object.get_stream(self.stream).get_unit()

            if storage.is_limited():
                self.limiting_component = self.pm_object.get_nice_name(storage.get_storage_limiting_component())
                self.limiting_component_entry_var.set(self.limiting_component)
                self.limiting_component_checkbox_var.set(True)

                self.limiting_component_ratio = storage.get_storage_limiting_component_ratio()
                self.limiting_component_ratio_entry_var.set(self.limiting_component_ratio)

            tk.Label(self.frame, text='CAPEX [€/' + stream_unit + ']').grid(row=1, column=0, sticky='w')
            self.capex_label.config(text=self.capex_entry_var.get())
            self.capex_label.grid(row=1, column=1, sticky='w')

            tk.Label(self.frame, text='Maintenance [%]').grid(row=2, column=0, sticky='w')
            self.maintenance_label.config(text=self.maintenance_entry_var.get())
            self.maintenance_label.grid(row=2, column=1, sticky='w')

            tk.Label(self.frame, text='Lifetime [years]').grid(row=3, column=0, sticky='w')
            self.lifetime_label.config(text=self.lifetime_entry_var.get())
            self.lifetime_label.grid(row=3, column=1, sticky='w')

            tk.Label(self.frame, text='Charging efficiency [%]').grid(row=4, column=0, sticky='w')
            self.charge_label.config(text=self.charging_entry_var.get())
            self.charge_label.grid(row=4, column=1, sticky='w')

            tk.Label(self.frame, text='Discharging efficiency [%]').grid(row=5, column=0, sticky='w')
            self.discharge_label.config(text=self.discharging_entry_var.get())
            self.discharge_label.grid(row=5, column=1, sticky='w')

            tk.Label(self.frame, text='Minimal SOC [%]').grid(row=6, column=0, sticky='w')
            self.min_soc_entry.config(text=self.min_soc_entry_var.get())
            self.min_soc_entry.grid(row=6, column=1, sticky='w')

            tk.Label(self.frame, text='Maximal SOC [%]').grid(row=7, column=0, sticky='w')
            self.max_soc_entry.config(text=self.max_soc_entry_var.get())
            self.max_soc_entry.grid(row=7, column=1, sticky='w')

            tk.Label(self.frame, text='Initial SOC [%]').grid(row=8, column=0, sticky='w')
            self.initial_soc_entry.config(text=self.initial_soc_entry_var.get())
            self.initial_soc_entry.grid(row=8, column=1, sticky='w')

            tk.Label(self.frame, text='Ratio between capacity and power [hours]').grid(row=9, column=0, sticky='w')
            self.ratio_capacity_p_entry.config(text=self.ratio_capacity_p_entry_var.get())
            self.ratio_capacity_p_entry.grid(row=9, column=1, sticky='w')

            self.checkbutton_limit_capacity_to_component.config(text='Limit capacity to component input',
                                                                variable=self.limiting_component_checkbox_var,
                                                                onvalue=True,
                                                                offvalue=False, state=DISABLED)
            self.checkbutton_limit_capacity_to_component.grid(row=10, column=0, sticky='w')

            if self.limiting_component_checkbox_var.get():

                ttk.Label(self.frame, text='Limiting component').grid(row=11, column=0, sticky='w')
                self.limit_cap_component_label.config(text=self.limiting_component_entry_var.get())
                self.limit_cap_component_label.grid(row=11, column=1, sticky='w')

                ttk.Label(self.frame, text='Ratio between storage and limiting component [hours]').grid(row=12, column=0, sticky='w')
                self.limit_cap_component_ratio_entry.config(text=self.limiting_component_ratio_entry_var.get())
                self.limit_cap_component_ratio_entry.grid(row=12, column=1, sticky='w')

                row = 13

            else:
                row = 11

            button_frame = ttk.Frame(self.frame)
            button_frame.grid_columnconfigure(0, weight=1)
            button_frame.grid_columnconfigure(1, weight=1)

            ttk.Button(button_frame, text='Adjust values', command=self.adjust_values)\
                .grid(row=0, column=0, sticky='ew')

            if self.storage_object.is_custom():
                ttk.Button(button_frame, text='Reset values', command=self.set_storage_settings_to_default,
                           state=DISABLED).grid(row=0, column=1, sticky='ew')
            else:
                ttk.Button(button_frame, text='Reset values',
                           command=self.set_storage_settings_to_default).grid(row=0, column=1, sticky='ew')

            button_frame.grid(row=row, columnspan=2, sticky='ew')

    def __init__(self, parent, root, storage, pm_object, pm_object_original):

        self.parent = parent
        self.root = root
        self.pm_object = pm_object
        self.pm_object_original = pm_object_original

        self.frame = tk.Frame(self.parent.sub_frame)
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_columnconfigure(1, weight=1)

        self.storable_var = BooleanVar()
        self.storage_object = self.pm_object.get_component(storage)
        if self.storage_object.is_final():
            self.storable_var.set(True)
        else:
            self.storable_var.set(False)

        self.stream = self.storage_object.get_name()
        self.stream_object = self.pm_object.get_stream(self.stream)

        self.capex = None
        self.maintenance = None
        self.lifetime = None
        self.charging_efficiency = None
        self.discharging_efficiency = None
        self.max_cap = None
        self.min_soc = None
        self.max_soc = None
        self.initial_soc = None
        self.ratio_capacity_p = None
        self.limiting_component = None
        self.limiting_component_ratio = None

        self.capex_entry_var = StringVar()
        self.maintenance_entry_var = StringVar()
        self.lifetime_entry_var = StringVar()
        self.charging_entry_var = StringVar()
        self.discharging_entry_var = StringVar()
        self.ratio_capacity_p_entry_var = StringVar()
        self.min_soc_entry_var = StringVar()
        self.max_soc_entry_var = StringVar()
        self.initial_soc_entry_var = StringVar()
        self.limiting_component_entry_var = StringVar()
        self.limiting_component_ratio_entry_var = StringVar()

        self.ratio_capacity_p_checkbox_var = BooleanVar()
        self.limiting_component_checkbox_var = BooleanVar()

        self.storable_checkbox = ttk.Checkbutton(self.frame, command=self.create_storage, variable=self.storable_var)
        self.capex_label = ttk.Label(self.frame)
        self.maintenance_label = ttk.Label(self.frame)
        self.lifetime_label = ttk.Label(self.frame)
        self.charge_label = ttk.Label(self.frame)
        self.discharge_label = ttk.Label(self.frame)
        self.min_soc_entry = ttk.Label(self.frame)
        self.max_soc_entry = ttk.Label(self.frame)
        self.initial_soc_entry = ttk.Label(self.frame)
        self.ratio_capacity_p_entry = ttk.Label(self.frame)
        self.ratio_capacity_p_label = ttk.Label(self.frame)
        self.limit_cap_component_label = ttk.Label(self.frame)
        self.limit_cap_component_ratio_entry = ttk.Label(self.frame)

        self.checkbutton_max_storage_capacity = ttk.Checkbutton(self.frame)
        self.max_cap_unit_label = ttk.Label(self.frame)

        self.checkbutton_limit_capacity_to_component = ttk.Checkbutton(self.frame)

        self.initialize_storage_frame()
