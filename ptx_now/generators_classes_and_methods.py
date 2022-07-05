import tkinter as tk
from tkinter import ttk
from tkinter import *


class GeneratorFrame:

    def activate_entry(self):

        if self.checkbox_var.get():

            self.capex_label.config(state=NORMAL)
            self.lifetime_label.config(state=NORMAL)
            self.maintenance_label.config(state=NORMAL)
            self.adjust_values_button.config(state=NORMAL)
            self.generated_commodity_label.config(state=NORMAL)

            self.pm_object.get_component(self.generator).set_final(True)

        else:

            self.capex_label.config(state=DISABLED)
            self.lifetime_label.config(state=DISABLED)
            self.maintenance_label.config(state=DISABLED)
            self.adjust_values_button.config(state=DISABLED)
            self.generated_commodity_label.config(state=DISABLED)

            self.pm_object.get_component(self.generator).set_final(False)

        self.parent.parent.pm_object_copy = self.pm_object
        self.parent.parent.update_widgets()

    def adjust_values(self):

        def check_fixed_capacity():

            if self.checkbox_fixed_capacity_var.get():
                fixed_capacity_label.config(state=NORMAL)
                fixed_capacity_entry.config(state=NORMAL)

            else:
                fixed_capacity_label.config(state=DISABLED)
                fixed_capacity_entry.config(state=DISABLED)

        def get_values_and_kill_window():
            generator = self.pm_object.get_component(self.generator)
            if capex_entry.get() != '':
                generator.set_capex(capex_entry.get())
            if lifetime_entry.get() != '':
                generator.set_lifetime(lifetime_entry.get())
            if maintenance_entry.get() != '':
                generator.set_maintenance(float(maintenance_entry.get()) / 100)

            generator.set_generated_commodity(self.pm_object.get_abbreviation(generated_commodity_cb.get()))
            generator.set_curtailment_possible(self.checkbox_curtailment_var.get())

            generator.set_has_fixed_capacity(self.checkbox_fixed_capacity_var.get())
            generator.set_fixed_capacity(self.fixed_capacity_var.get())

            self.parent.parent.pm_object_copy = self.pm_object
            self.parent.parent.update_widgets()

            window.destroy()

        def kill_window():
            window.destroy()

        window = Toplevel(self.frame)
        window.title('Adjust Parameters')
        window.grab_set()

        window.grid_columnconfigure(0, weight=1)
        window.grid_columnconfigure(2, weight=1)

        tk.Label(window, text='CAPEX in ' + self.monetary_unit + '/' + self.commodity_unit).grid(row=0, column=0, sticky='w')
        tk.Label(window, text='Lifetime in years').grid(row=1, column=0, sticky='w')
        tk.Label(window, text='Maintenance in %').grid(row=2, column=0, sticky='w')
        tk.Label(window, text='Generated commodity').grid(row=3, column=0, sticky='w')

        capex_entry = tk.Entry(window, text=self.capex)
        capex_entry.grid(row=0, column=1, sticky='ew')
        lifetime_entry = tk.Entry(window, text=self.lifetime)
        lifetime_entry.grid(row=1, column=1, sticky='ew')
        maintenance_entry = tk.Entry(window, text=self.maintenance)
        maintenance_entry.grid(row=2, column=1, sticky='ew')

        commodities = []
        for commodity in self.pm_object.get_final_commodities_objects():
            commodities.append(commodity.get_nice_name())

        generated_commodity_cb = ttk.Combobox(window, values=commodities, state='readonly')
        generated_commodity_cb.grid(row=3, column=1, sticky='ew')
        generated_commodity_cb.set(self.generated_commodity_var.get())

        ttk.Checkbutton(window, text='Curtailment possible?', variable=self.checkbox_curtailment_var).grid(row=4,
                                                                                                           column=0,
                                                                                                           sticky='ew')

        ttk.Checkbutton(window, text='Fixed Capacity used?', variable=self.checkbox_fixed_capacity_var,
                        command=check_fixed_capacity).grid(row=5, column=0, sticky='ew')

        fixed_capacity_label = ttk.Label(window, text='Fixed Capacity [' + self.commodity_unit + ']:')
        fixed_capacity_label.grid(row=6, column=0)
        fixed_capacity_entry = ttk.Entry(window, text=self.fixed_capacity_var)
        fixed_capacity_entry.grid(row=6, column=1)

        ttk.Button(window, text='Adjust values', command=get_values_and_kill_window).grid(row=7, column=0,  sticky='ew')

        ttk.Button(window, text='Cancel', command=kill_window).grid(row=7, column=1, sticky='ew')

        window.grid_columnconfigure(0, weight=1, uniform='a')
        window.grid_columnconfigure(1, weight=1, uniform='a')

        check_fixed_capacity()

    def set_generator_settings_to_default(self):

        self.pm_object.remove_component_entirely(self.generator)

        generator_original = self.pm_object_original.get_component(self.generator)
        self.pm_object.add_component(self.generator, generator_original.__copy__())

        self.parent.parent.pm_object_copy = self.pm_object
        self.parent.parent.update_widgets()

    def initialize_generator_frame(self):

        if self.commodity_unit == 'MWh':
            self.commodity_unit = 'MW'
        elif self.commodity_unit == 'GWh':
            self.commodity_unit = 'GW'
        elif self.commodity_unit == 'kWh':
            self.commodity_unit = 'kW'
        else:
            self.commodity_unit = self.commodity_unit + ' / h'

        ttk.Label(self.frame, text='Parameter', font='Helvetica 10 bold').grid(row=1, column=0, sticky='w')
        ttk.Label(self.frame, text='Value', font='Helvetica 10 bold').grid(row=1, column=1, sticky='w')

        self.capex.set(self.generator_object.get_capex())
        self.lifetime.set(self.generator_object.get_lifetime())
        self.maintenance.set(round(float(self.generator_object.get_maintenance()) * 100, 2))
        self.generated_commodity_var.set(self.generated_commodity)
        self.checkbox_curtailment_var.set(self.curtailment_possible)
        self.checkbox_fixed_capacity_var.set(self.has_fixed_capacity)
        self.fixed_capacity_var.set(self.fixed_capacity)

        if self.generator_object in self.pm_object.get_final_generator_components_objects():
            state = NORMAL
            self.checkbox_var.set(True)
        else:
            state = DISABLED
            self.checkbox_var.set(False)

        self.checkbox = ttk.Checkbutton(self.frame, text='Generator available', onvalue=True,
                                        offvalue=False, variable=self.checkbox_var, command=self.activate_entry)
        self.checkbox.grid(row=0, columnspan=2, sticky='w')

        ttk.Label(self.frame, text='CAPEX [' + self.monetary_unit + '/' + self.commodity_unit + ']').grid(row=2, column=0, sticky='w')
        self.capex_label = ttk.Label(self.frame, text=self.capex.get(), state=state)
        self.capex_label.grid(row=2, column=1, sticky='w')

        ttk.Label(self.frame, text='Lifetime [Years]').grid(row=3, column=0, sticky='w')
        self.lifetime_label = ttk.Label(self.frame, text=self.lifetime.get(), state=state)
        self.lifetime_label.grid(row=3, column=1, sticky='w')

        ttk.Label(self.frame, text='Maintenance [%]').grid(row=4, column=0, sticky='w')
        self.maintenance_label = ttk.Label(self.frame, text=self.maintenance.get(), state=state)
        self.maintenance_label.grid(row=4, column=1, sticky='w')

        ttk.Label(self.frame, text='Generated commodity').grid(row=5, column=0, sticky='w')
        self.generated_commodity_label = ttk.Label(self.frame, text=self.generated_commodity_var.get(), state=state)
        self.generated_commodity_label.grid(row=5, column=1, sticky='w')

        ttk.Label(self.frame, text='Curtailment possible: ').grid(row=6, column=0, sticky='w')
        if self.checkbox_curtailment_var.get():
            text_curtailment = 'Yes'
        else:
            text_curtailment = 'No'

        self.curtailment_label = ttk.Label(self.frame, text=text_curtailment, state=state)
        self.curtailment_label.grid(row=6, column=1, sticky='w')

        ttk.Label(self.frame, text='Fixed Capacity [' + self.commodity_unit + ']: ').grid(row=7, column=0, sticky='w')
        if self.checkbox_fixed_capacity_var.get():
            text_fixed_capacity = self.fixed_capacity_var.get()

        else:
            text_fixed_capacity = 'Not used'

        self.fixed_capacity_label = ttk.Label(self.frame, text=text_fixed_capacity, state=state)
        self.fixed_capacity_label.grid(row=7, column=1, sticky='w')

        button_frame = ttk.Frame(self.frame)
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)

        self.adjust_values_button = ttk.Button(button_frame, text='Adjust values', command=self.adjust_values,
                                               state=state)
        self.adjust_values_button.grid(row=0, column=0, sticky='ew')

        self.default_generators_button = ttk.Button(button_frame, text='Default values',
                                                    command=self.set_generator_settings_to_default)
        self.default_generators_button.grid(row=0, column=1, sticky='ew')

        if self.generator_object.is_custom():
            self.default_generators_button.config(state=DISABLED)

        button_frame.grid(row=8, columnspan=2, sticky='ew')

    def __init__(self, parent, frame, generator, pm_object, pm_object_original):

        self.parent = parent
        self.pm_object = pm_object
        self.pm_object_original = pm_object_original
        self.generator = generator

        self.frame = ttk.Frame(frame)
        self.frame.grid_columnconfigure(0, weight=1, uniform='a')
        self.frame.grid_columnconfigure(1, weight=1, uniform='a')

        self.generator_object = self.pm_object.get_component(self.generator)
        self.generated_commodity = self.pm_object.get_nice_name(self.generator_object.get_generated_commodity())
        self.commodity_unit = self.pm_object.get_commodity(self.generator_object.get_generated_commodity()).get_unit()
        self.curtailment_possible = self.generator_object.get_curtailment_possible()
        self.has_fixed_capacity = self.generator_object.get_has_fixed_capacity()
        self.fixed_capacity = self.generator_object.get_fixed_capacity()

        self.textvar_profile = StringVar()
        self.checkbox_var = BooleanVar()

        self.capex = StringVar()
        self.lifetime = StringVar()
        self.maintenance = StringVar()
        self.generated_commodity_var = StringVar()
        self.checkbox_curtailment_var = BooleanVar()
        self.checkbox_fixed_capacity_var = BooleanVar()
        self.fixed_capacity_var = StringVar()

        self.monetary_unit = self.pm_object.get_monetary_unit()

        self.initialize_generator_frame()
