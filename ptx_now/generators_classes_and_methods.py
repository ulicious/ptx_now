import tkinter as tk
from tkinter import ttk
from tkinter import *


class GeneratorFrame:

    def activate_entry(self):

        if self.checkbox_var.get():

            self.pm_object.get_component(self.generator).set_final(True)
            self.state = NORMAL

        else:

            self.pm_object.get_component(self.generator).set_final(False)
            self.state = DISABLED

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
            if fixed_om_entry.get() != '':
                generator.set_fixed_OM(float(fixed_om_entry.get()) / 100)
            if variable_om_entry.get() != '':
                generator.set_variable_OM(float(variable_om_entry.get()))

            generator.set_generated_commodity(generated_commodity_cb.get())

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

        if self.commodity_unit in ['kWh', 'MWh', 'GWh', 'TWh']:
            commodity_unit = self.commodity_unit[0:2]
        else:
            commodity_unit = self.commodity_unit + ' / h'

        tk.Label(window, text='CAPEX [' + self.monetary_unit + '/' + commodity_unit + ']').grid(row=0,
                                                                                                column=0,
                                                                                                sticky='w')
        tk.Label(window, text='Lifetime [years]').grid(row=1, column=0, sticky='w')
        tk.Label(window, text='Fixed O&M [%]').grid(row=2, column=0, sticky='w')
        tk.Label(window, text='Variable O&M [' + self.pm_object.get_monetary_unit() + ' / ' + self.commodity_unit + ']').grid(row=3, column=0, sticky='w')
        tk.Label(window, text='Generated commodity').grid(row=4, column=0, sticky='w')

        capex_entry = tk.Entry(window, text=self.capex)
        capex_entry.grid(row=0, column=1, sticky='ew')
        lifetime_entry = tk.Entry(window, text=self.lifetime)
        lifetime_entry.grid(row=1, column=1, sticky='ew')
        fixed_om_entry = tk.Entry(window, text=self.fixed_om)
        fixed_om_entry.grid(row=2, column=1, sticky='ew')
        variable_om_entry = tk.Entry(window, text=self.variable_om)
        variable_om_entry.grid(row=3, column=1, sticky='ew')

        commodities = []
        for commodity in self.pm_object.get_final_commodities_objects():
            commodities.append(commodity.get_name())

        generated_commodity_cb = ttk.Combobox(window, values=commodities, state='readonly')
        generated_commodity_cb.grid(row=4, column=1, sticky='ew')
        generated_commodity_cb.set(self.generated_commodity_var.get())

        ttk.Checkbutton(window, text='Curtailment possible?', variable=self.checkbox_curtailment_var).grid(row=5,
                                                                                                           column=0,
                                                                                                           sticky='ew')

        ttk.Checkbutton(window, text='Fixed Capacity used?', variable=self.checkbox_fixed_capacity_var,
                        command=check_fixed_capacity).grid(row=6, column=0, sticky='ew')

        fixed_capacity_label = ttk.Label(window, text='Fixed Capacity [' + commodity_unit + ']:')
        fixed_capacity_label.grid(row=7, column=0)
        fixed_capacity_entry = ttk.Entry(window, text=self.fixed_capacity_var)
        fixed_capacity_entry.grid(row=7, column=1)

        ttk.Button(window, text='Adjust values', command=get_values_and_kill_window).grid(row=8, column=0,  sticky='ew')

        ttk.Button(window, text='Cancel', command=kill_window).grid(row=8, column=1, sticky='ew')

        window.grid_columnconfigure(0, weight=1, uniform='a')
        window.grid_columnconfigure(1, weight=1, uniform='a')

        check_fixed_capacity()

    def set_generator_settings_to_default(self):

        # Delete all current generators
        for generator in self.pm_object.get_generator_components_names():
            self.pm_object.remove_component_entirely(generator)

        # Get all generators from original pm object
        for self.generator in self.pm_object_original.get_generator_components_names():
            generator_original = self.pm_object_original.get_component(self.generator)
            self.pm_object.add_component(self.generator, generator_original.__copy__())

        self.parent.parent.pm_object_copy = self.pm_object
        self.parent.parent.update_widgets()

    def initialize_generator_frame(self):

        if self.commodity_unit in ['kWh', 'MWh', 'GWh', 'TWh']:
            commodity_unit = self.commodity_unit[0:2]
        else:
            commodity_unit = self.commodity_unit + ' / h'

        self.capex.set(self.generator_object.get_capex())
        self.lifetime.set(self.generator_object.get_lifetime())
        self.fixed_om.set(round(float(self.generator_object.get_fixed_OM()) * 100, 2))
        self.variable_om.set(round(float(self.generator_object.get_variable_OM()), 2))
        self.generated_commodity_var.set(self.generated_commodity)
        self.checkbox_curtailment_var.set(self.curtailment_possible)
        self.checkbox_fixed_capacity_var.set(self.has_fixed_capacity)
        self.fixed_capacity_var.set(self.fixed_capacity)

        self.checkbox.config(text='Generator available', onvalue=True, offvalue=False, variable=self.checkbox_var,
                             command=self.activate_entry)
        self.checkbox.grid(row=0, columnspan=2, sticky='w')

        ttk.Label(self.frame, text='CAPEX [' + self.monetary_unit + '/' + commodity_unit + ']', state=self.state)\
            .grid(row=1, column=0, sticky='w')
        self.capex_label.config(text=self.capex.get(), state=self.state)
        self.capex_label.grid(row=1, column=1, sticky='w')

        ttk.Label(self.frame, text='Lifetime [Years]', state=self.state).grid(row=2, column=0, sticky='w')
        self.lifetime_label.config(text=self.lifetime.get(), state=self.state)
        self.lifetime_label.grid(row=2, column=1, sticky='w')

        ttk.Label(self.frame, text='Fixed O&M [%]', state=self.state).grid(row=3, column=0, sticky='w')
        self.fixed_om_label.config(text=self.fixed_om.get(), state=self.state)
        self.fixed_om_label.grid(row=3, column=1, sticky='w')

        ttk.Label(self.frame,
                  text='Variable O&M [' + self.pm_object.get_monetary_unit() + ' / ' + self.commodity_unit + ']',
                  state=self.state).grid(row=4, column=0, sticky='w')
        self.variable_om_label.config(text=self.variable_om.get(), state=self.state)
        self.variable_om_label.grid(row=4, column=1, sticky='w')

        ttk.Label(self.frame, text='Generated commodity', state=self.state).grid(row=5, column=0, sticky='w')
        self.generated_commodity_label.config(text=self.generated_commodity_var.get(), state=self.state)
        self.generated_commodity_label.grid(row=5, column=1, sticky='w')

        ttk.Label(self.frame, text='Curtailment possible: ', state=self.state).grid(row=6, column=0, sticky='w')
        if self.checkbox_curtailment_var.get():
            text_curtailment = 'Yes'
        else:
            text_curtailment = 'No'

        self.curtailment_label.config(text=text_curtailment, state=self.state)
        self.curtailment_label.grid(row=6, column=1, sticky='w')

        ttk.Label(self.frame, text='Fixed Capacity [' + commodity_unit + ']: ', state=self.state)\
            .grid(row=7, column=0, sticky='w')
        if self.checkbox_fixed_capacity_var.get():
            text_fixed_capacity = self.fixed_capacity_var.get()

        else:
            text_fixed_capacity = 'Not used'

        self.fixed_capacity_label.config(text=text_fixed_capacity, state=self.state)
        self.fixed_capacity_label.grid(row=7, column=1, sticky='w')

        button_frame = ttk.Frame(self.frame)
        button_frame.grid_columnconfigure(0, weight=1)

        self.adjust_values_button = ttk.Button(button_frame, text='Adjust values', command=self.adjust_values,
                                               state=self.state)
        self.adjust_values_button.grid(row=0, column=0, sticky='ew')

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
        self.generated_commodity = self.generator_object.get_generated_commodity()
        self.commodity_unit = self.pm_object.get_commodity(self.generator_object.get_generated_commodity()).get_unit()
        self.curtailment_possible = self.generator_object.get_curtailment_possible()
        self.has_fixed_capacity = self.generator_object.get_has_fixed_capacity()
        self.fixed_capacity = self.generator_object.get_fixed_capacity()

        self.textvar_profile = StringVar()
        self.checkbox_var = BooleanVar()

        self.capex = DoubleVar()
        self.lifetime = DoubleVar()
        self.fixed_om = DoubleVar()
        self.variable_om = DoubleVar()
        self.generated_commodity_var = StringVar()
        self.checkbox_curtailment_var = BooleanVar()
        self.checkbox_fixed_capacity_var = BooleanVar()
        self.fixed_capacity_var = DoubleVar()

        self.monetary_unit = self.pm_object.get_monetary_unit()

        self.checkbox = ttk.Checkbutton(self.frame)
        self.capex_label = ttk.Label(self.frame)
        self.lifetime_label = ttk.Label(self.frame)
        self.fixed_om_label = ttk.Label(self.frame)
        self.variable_om_label = ttk.Label(self.frame)
        self.generated_commodity_label = ttk.Label(self.frame)
        self.curtailment_label = ttk.Label(self.frame)
        self.fixed_capacity_label = ttk.Label(self.frame)

        if self.generator_object in self.pm_object.get_final_generator_components_objects():
            self.state = NORMAL
            self.checkbox_var.set(True)
        else:
            self.state = DISABLED
            self.checkbox_var.set(False)

        self.initialize_generator_frame()
