import tkinter as tk
from tkinter import ttk
from tkinter import *
import random

from stream import Stream
from components import ConversionComponent


class ComponentFrame:

    def __init__(self, parent, frame, component, pm_object, pm_object_original):

        """
        Component base frame
        Builds basis for component parameters frame and component streams frame

        Input:
        - parent: to access function of parents (e.g., update whole interface)
        - component: name of component
        - pm_object_copy: Has stored all information and will be changed if adjustments conducted
        - pm_object_original: To restore default settings
        """

        self.parent = parent
        self.pm_object = pm_object
        self.pm_object_original = pm_object_original
        self.component = component

        self.frame = ttk.Frame(frame)

        if self.component != '':

            # Create frame for parameters, main conversion and side conversions
            self.parameter_frame = ComponentParametersFrame(self.parent, self.frame, self.component,
                                                            self.pm_object, self.pm_object_original)
            self.conversion_frame = ConversionFrame(self, self.frame, self.component,
                                                    self.pm_object, self.pm_object_original)

            # Attach frames to interface and separate with separators
            ttk.Separator(self.frame, orient='horizontal').pack(fill="both", expand=True)
            self.parameter_frame.frame.pack(fill="both", expand=True)
            ttk.Separator(self.frame, orient='horizontal').pack(fill="both", expand=True)
            self.conversion_frame.frame.pack(fill="both", expand=True)


class ComponentParametersFrame:

    def adjust_component_value(self):
        def get_value_and_kill_window():

            self.capex_basis_var.set(capex_basis_var.get())
            self.component_object.set_capex_basis(capex_basis_var.get())

            if not self.scalable_var.get():
                self.component_object.set_scalable(False)
                self.component_object.set_capex(float(self.label_capex_value_str.get()))
            else:
                self.component_object.set_scalable(True)
                self.component_object.set_base_investment(float(self.label_base_investment_value_str.get()))
                self.component_object.set_base_capacity(self.label_base_capacity_value_str.get())
                self.component_object.set_economies_of_scale(float(self.label_scaling_factor_value_str.get()))
                self.component_object.set_max_capacity_economies_of_scale(float(self.label_max_capacity_eoc_value_str.get()))

            self.component_object.set_lifetime(float(self.label_lifetime_value_str.get()))
            self.component_object.set_maintenance(float(self.label_maintenance_value_str.get()) / 100)
            self.component_object.set_min_p(float(self.label_min_capacity_value_str.get()) / 100)
            self.component_object.set_max_p(float(self.label_max_capacity_value_str.get()) / 100)
            self.component_object.set_ramp_down(float(self.label_ramp_down_value_str.get()) / 100)
            self.component_object.set_ramp_up(float(self.label_ramp_up_value_str.get()) / 100)

            if not self.shut_down_ability_var.get():
                self.component_object.set_shut_down_ability(False)
            else:
                self.component_object.set_shut_down_ability(True)
                self.component_object.set_start_up_time(float(self.label_start_up_value_str.get()))

            if not self.hot_standby_ability_var.get():
                self.component_object.set_hot_standby_ability(False)
            else:
                self.component_object.set_hot_standby_ability(True)
                self.component_object.set_hot_standby_demand(self.pm_object.get_abbreviation(hot_standby_combobox.get()),
                                                             float(hot_standby_entry.get()))
                self.component_object.set_hot_standby_startup_time(int(hot_standby_startup_time_entry.get()))

            self.component_object.set_number_parallel_units(float(self.label_number_parallel_units_str.get()))

            self.parent.parent.pm_object_copy = self.pm_object
            self.parent.parent.update_widgets()

            newWindow.destroy()

        def activate_scale_no_scale():
            if self.scalable_var.get():
                entry_capex_var.config(state=DISABLED)

                label_base_investment_value.config(state=NORMAL)
                label_base_capacity_value.config(state=NORMAL)
                label_scaling_factor_value.config(state=NORMAL)
                label_max_capacity_eoc_value.config(state=NORMAL)

            else:
                entry_capex_var.config(state=NORMAL)

                label_base_investment_value.config(state=DISABLED)
                label_base_capacity_value.config(state=DISABLED)
                label_scaling_factor_value.config(state=DISABLED)
                label_max_capacity_eoc_value.config(state=DISABLED)

        def activate_shut_down():
            if self.shut_down_ability_var.get():
                entry_start_up.config(state=NORMAL)

            else:
                entry_start_up.config(state=DISABLED)

        def activate_hot_standby():
            if self.hot_standby_ability_var.get():
                hot_standby_combobox.config(state='readonly')
                hot_standby_entry.config(state=NORMAL)
                hot_standby_startup_time_entry.config(state=NORMAL)
            else:
                hot_standby_combobox.config(state=DISABLED)
                hot_standby_entry.config(state=DISABLED)
                hot_standby_startup_time_entry.config(state=DISABLED)

        def change_capex_basis():

            if capex_basis_var.get() == 'input':
                nice_name_new = self.pm_object.get_nice_name(self.component_object.get_main_input())
                unit_new = self.pm_object.get_stream(self.component_object.get_main_input()).get_unit()
            else:
                nice_name_new = self.pm_object.get_nice_name(self.component_object.get_main_output())
                unit_new = self.pm_object.get_stream(self.component_object.get_main_output()).get_unit()

            if unit_new == 'GWh':
                unit_new = 'GW'
                capex_unit_new = '€/' + unit_new + ' ' + nice_name_new
                capacity_unit_new = 'GW ' + nice_name_new
            elif unit_new == 'MWh':
                unit_new = 'MW'
                capex_unit_new = '€/' + unit_new + ' ' + nice_name_new
                capacity_unit_new = 'MW ' + nice_name_new
            elif unit_new == 'kWh':
                unit_new = 'kW'
                capex_unit_new = '€/' + unit_new + ' ' + nice_name_new
                capacity_unit_new = 'kW ' + nice_name_new
            else:
                capex_unit_new = '€/' + unit_new + '*h ' + nice_name_new
                capacity_unit_new = unit_new + '/h ' + nice_name_new

            capex_unit_var.set('Capex [' + capex_unit_new + ']')
            base_capacity_var.set('Base Capacity [' + capacity_unit_new + ']')
            max_capacity_var.set('Maximal Capacity [' + capacity_unit_new + ']')

        # Toplevel object which will
        # be treated as a new window
        newWindow = Toplevel()
        newWindow.grid_columnconfigure(0, weight=1)
        newWindow.grid_columnconfigure(1, weight=1)
        newWindow.grab_set()

        # sets the title of the
        # Toplevel widget
        newWindow.title('Adjust Component Parameters')

        tk.Checkbutton(newWindow, text='Scalable?',
                       variable=self.scalable_var,
                       command=activate_scale_no_scale).grid(row=0, column=0, columnspan=2, sticky='w')

        if self.component_object.is_scalable():
            status_scale = NORMAL
            status_no_scale = DISABLED
        else:
            status_scale = DISABLED
            status_no_scale = NORMAL

        ttk.Label(newWindow, text='Investment Basis').grid(row=1, column=0, sticky='w')

        capex_basis_frame = ttk.Frame(newWindow)

        capex_basis_var = StringVar()
        capex_basis_var.set(self.capex_basis_var.get())

        capex_basis_input_rb = ttk.Radiobutton(capex_basis_frame, text='Main Input', value='input',
                                               variable=capex_basis_var, state=NORMAL, command=change_capex_basis)
        capex_basis_input_rb.grid(row=0, column=0)
        capex_basis_output_rb = ttk.Radiobutton(capex_basis_frame, text='Main Output', value='output',
                                                variable=capex_basis_var, state=NORMAL, command=change_capex_basis)
        capex_basis_output_rb.grid(row=0, column=1)

        capex_basis_frame.grid(row=1, column=1, sticky='ew')

        if self.capex_basis_var.get() == 'input':
            nice_name = self.pm_object.get_nice_name(self.component_object.get_main_input())
            unit = self.pm_object.get_stream(self.component_object.get_main_input()).get_unit()
        else:
            nice_name = self.pm_object.get_nice_name(self.component_object.get_main_output())
            unit = self.pm_object.get_stream(self.component_object.get_main_output()).get_unit()

        if unit == 'GWh':
            unit = 'GW'
            capex_unit = '€/' + unit + ' ' + nice_name
            capacity_unit = 'GW ' + nice_name
        elif unit == 'MWh':
            unit = 'MW'
            capex_unit = '€/' + unit + ' ' + nice_name
            capacity_unit = 'MW ' + nice_name
        elif unit == 'kWh':
            unit = 'kW'
            capex_unit = '€/' + unit + ' ' + nice_name
            capacity_unit = 'kW ' + nice_name
        else:
            capex_unit = '€/' + unit + '*h ' + nice_name
            capacity_unit = unit + '/h ' + nice_name

        capex_unit_var = StringVar()
        capex_unit_var.set('Capex [' + capex_unit + ']')

        base_capacity_var = StringVar()
        base_capacity_var.set('Base Capacity [' + capacity_unit + ']')

        max_capacity_var = StringVar()
        max_capacity_var.set('Maximal Capacity [' + capacity_unit + ']')

        ttk.Label(newWindow, textvariable=capex_unit_var).grid(row=2, column=0, sticky='w')
        entry_capex_var = ttk.Entry(newWindow, text=self.label_capex_value_str, state=status_no_scale)
        entry_capex_var.grid(row=2, column=1, sticky='w')

        label_base_investment = ttk.Label(newWindow, text='€')
        label_base_investment.grid(column=0, row=3, sticky='w')
        label_base_investment_value = ttk.Entry(newWindow,
                                                text=self.label_base_investment_value_str,
                                                state=status_scale)
        label_base_investment_value.grid(column=1, row=3, sticky='w')

        label_base_capacity = ttk.Label(newWindow, textvariable=base_capacity_var)
        label_base_capacity.grid(column=0, row=4, sticky='w')
        label_base_capacity_value = ttk.Entry(newWindow, text=self.label_base_capacity_value_str, state=status_scale)
        label_base_capacity_value.grid(column=1, row=4, sticky='w')

        label_scaling_factor = ttk.Label(newWindow, text='Scaling factor')
        label_scaling_factor.grid(column=0, row=5, sticky='w')
        label_scaling_factor_value = ttk.Entry(newWindow,
                                               text=self.label_scaling_factor_value_str,
                                               state=status_scale)
        label_scaling_factor_value.grid(column=1, row=5, sticky='w')

        label_max_capacity_eoc = ttk.Label(newWindow, textvariable=max_capacity_var)
        label_max_capacity_eoc.grid(column=0, row=6, sticky='w')
        label_max_capacity_eoc_value = ttk.Entry(newWindow,
                                                 text=self.label_max_capacity_eoc_value_str,
                                                 state=status_scale)
        label_max_capacity_eoc_value.grid(column=1, row=6, sticky='w')

        ttk.Label(newWindow, text='Lifetime [Years]').grid(row=7, column=0, sticky='w')
        entry_lifetime = ttk.Entry(newWindow, text=self.label_lifetime_value_str)
        entry_lifetime.grid(row=7, column=1, sticky='w')

        ttk.Label(newWindow, text='Maintenance [%]').grid(row=8, column=0, sticky='w')
        entry_maintenance = ttk.Entry(newWindow, text=self.label_maintenance_value_str)
        entry_maintenance.grid(row=8, column=1, sticky='w')

        ttk.Label(newWindow, text='Minimal power [%]').grid(row=9, column=0, sticky='w')
        entry_min_capacity = ttk.Entry(newWindow, text=self.label_min_capacity_value_str)
        entry_min_capacity.grid(row=9, column=1, sticky='w')

        ttk.Label(newWindow, text='Maximal power [%]').grid(row=10, column=0, sticky='w')
        entry_max_capacity = ttk.Entry(newWindow, text=self.label_max_capacity_value_str)
        entry_max_capacity.grid(row=10, column=1, sticky='w')

        ttk.Label(newWindow, text='Ramp down [%/h]').grid(row=11, column=0, sticky='w')
        entry_ramp_down = ttk.Entry(newWindow, text=self.label_ramp_down_value_str)
        entry_ramp_down.grid(row=11, column=1, sticky='w')

        ttk.Label(newWindow, text='Ramp up [%/h]').grid(row=12, column=0, sticky='w')
        entry_ramp_up = ttk.Entry(newWindow, text=self.label_ramp_up_value_str)
        entry_ramp_up.grid(row=12, column=1, sticky='w')

        ttk.Checkbutton(newWindow, text='Shut down possible?',
                       variable=self.shut_down_ability_var,
                       command=activate_shut_down).grid(row=13, column=0, columnspan=2, sticky='w')

        if self.component_object.get_shut_down_ability():
            shut_down_state = NORMAL
        else:
            shut_down_state = DISABLED

        ttk.Label(newWindow, text='Cold Start up Time [h]').grid(row=14, column=0, sticky='w')
        entry_start_up = ttk.Entry(newWindow, text=self.label_start_up_value_str, state=shut_down_state)
        entry_start_up.grid(row=14, column=1, sticky='w')

        # Hot standby ability
        if self.hot_standby_ability_var.get():
            state_hot_standby = NORMAL
            state_hot_standby_combobox = 'readonly'
        else:
            state_hot_standby = DISABLED
            state_hot_standby_combobox = DISABLED

        ttk.Checkbutton(newWindow, text='Hot Standby possible?', variable=self.hot_standby_ability_var,
                        command=activate_hot_standby).grid(row=15, column=0, columnspan=2, sticky='w')

        streams = []
        for s in self.pm_object.get_specific_streams('final'):
            streams.append(s.get_nice_name())

        ttk.Label(newWindow, text='Hot Standby Input Stream').grid(row=16, column=0, sticky='w')
        hot_standby_combobox = ttk.Combobox(newWindow, text='', values=streams, state=state_hot_standby_combobox)
        hot_standby_combobox.set(self.hot_standby_stream_var.get())
        hot_standby_combobox.grid(row=16, column=1, sticky='w')

        ttk.Label(newWindow, text='Hot Standby Hourly Demand').grid(row=17, column=0, sticky='w')
        hot_standby_entry = ttk.Entry(newWindow, text=self.hot_standby_demand_var, state=state_hot_standby)
        hot_standby_entry.grid(row=17, column=1, sticky='w')

        ttk.Label(newWindow, text='Hot Standby Startup Time [h]').grid(row=18, column=0, sticky='w')
        hot_standby_startup_time_entry = ttk.Entry(newWindow, text=self.hot_standby_demand_startup_time,
                                                   state=state_hot_standby)
        hot_standby_startup_time_entry.grid(row=18, column=1, sticky='w')

        # Number of units of same type in system
        tk.Label(newWindow, text='Number of units in system').grid(row=19, column=0, sticky='w')
        entry_number_units = ttk.Entry(newWindow, text=self.label_number_parallel_units_str)
        entry_number_units.grid(row=19, column=1, sticky='w')

        button = ttk.Button(newWindow, text='Adjust values', command=get_value_and_kill_window)
        button.grid(row=20, column=0, sticky='ew')

        button = ttk.Button(newWindow, text='Cancel', command=newWindow.destroy)
        button.grid(row=20, column=1, sticky='ew')

        newWindow.grid_columnconfigure(0, weight=1, uniform='a')
        newWindow.grid_columnconfigure(1, weight=1, uniform='a')

        newWindow.mainloop()

    def set_component_parameters_to_default(self):

        # Important: Not only delete component and get copy of pm_object_original
        # because conversions should not be deleted

        component_original = self.pm_object_original.get_component(self.component)
        component_copy = self.pm_object.get_component(self.component)

        component_copy.set_scalable(component_original.is_scalable())
        component_copy.set_capex_basis(component_original.get_capex_basis())
        component_copy.set_capex(component_original.get_capex())
        component_copy.set_base_investment(component_original.get_base_investment())
        component_copy.set_base_capacity(component_original.get_base_capacity())
        component_copy.set_economies_of_scale(component_original.get_economies_of_scale())
        component_copy.set_max_capacity_economies_of_scale(component_original.get_max_capacity_economies_of_scale())
        component_copy.set_number_parallel_units(component_original.get_number_parallel_units())

        component_copy.set_lifetime(component_original.get_lifetime())
        component_copy.set_maintenance(float(component_original.get_maintenance()))
        component_copy.set_min_p(float(component_original.get_min_p()))
        component_copy.set_max_p(float(component_original.get_max_p()))
        component_copy.set_ramp_down(component_original.get_ramp_down())
        component_copy.set_ramp_up(component_original.get_ramp_up())
        component_copy.set_shut_down_ability(component_original.get_shut_down_ability())
        component_copy.set_start_up_time(component_original.get_start_up_time())

        if component_original.get_hot_standby_ability():
            component_copy.set_hot_standby_ability(component_original.get_hot_standby_ability())
            component_copy.set_hot_standby_startup_time(component_original.get_hot_standby_startup_time())
            component_copy.set_hot_standby_demand(component_original.get_hot_standby_demand())

        self.pm_object.set_all_applied_parameters(self.pm_object_original.get_all_applied_parameters())

        self.parent.parent.pm_object_copy = self.pm_object
        self.parent.parent.update_widgets()

    def __init__(self, parent, super_frame, component, pm_object, pm_object_original):

        """
        Frame which contains all financial and technical parameters as well as the ability to change these

        Input
        - parent: Interface object - To access functions of Interface class
        - root: Tk.root - To add new windows
        - super_frame: tk.Frame - Frame of component, which contains this frame
        - component: string - Name of component
        - pm_object: Parameter object - Contains all information
        - pm_object_original: Parameter object - Contains all information (to set default values)

        Function
        - Creates parameter frame and shows all parameters
        - Has functions to change, store and reset parameters
        """

        self.parent = parent
        self.pm_object = pm_object
        self.pm_object_original = pm_object_original
        self.component = component
        self.component_object = self.pm_object.get_component(component)

        self.frame = tk.Frame(super_frame)

        if self.component != '':

            # Initiate values for different parameters

            self.parameter_label = ttk.Label(self.frame, text='Parameter', font='Helvetica 10 bold')
            self.parameter_label.grid(column=0, row=0, sticky='w')
            self.value_label = ttk.Label(self.frame, text='Value', font='Helvetica 10 bold')
            self.value_label.grid(column=1, row=0, sticky='w')

            capex_basis = self.component_object.get_capex_basis()
            lifetime = self.component_object.get_lifetime()
            maintenance = round(float(self.component_object.get_maintenance() * 100), 2)

            min_p = round(float(self.component_object.get_min_p() * 100), 2)
            max_p = round(float(self.component_object.get_max_p() * 100), 2)
            ramp_down = round(float(self.component_object.get_ramp_down() * 100), 2)
            ramp_up = round(float(self.component_object.get_ramp_up() * 100), 2)

            shut_down_ability = bool(self.component_object.get_shut_down_ability())
            self.shut_down_ability_var = BooleanVar()
            self.shut_down_ability_var.set(shut_down_ability)
            self.label_start_up_value_str = StringVar()
            if shut_down_ability:
                start_up_time = self.component_object.get_start_up_time()
                self.label_start_up_value_str.set(start_up_time)
            else:
                self.label_start_up_value_str.set(0)

            hot_standby_ability = bool(self.component_object.get_hot_standby_ability())
            self.hot_standby_ability_var = BooleanVar()
            self.hot_standby_ability_var.set(hot_standby_ability)
            self.hot_standby_stream_var = StringVar()
            self.hot_standby_demand_var = StringVar()
            self.hot_standby_demand_startup_time = IntVar()
            if hot_standby_ability:
                hot_standby_demand = self.component_object.get_hot_standby_demand()
                stream = [*hot_standby_demand.keys()][0]
                stream_nice_name = self.pm_object.get_nice_name(stream)
                hot_standby_unit = self.pm_object.get_stream(stream).get_unit()
                hot_standby_startup_time = self.component_object.get_hot_standby_startup_time()

                self.hot_standby_ability_var.set(hot_standby_ability)
                self.hot_standby_stream_var.set(stream_nice_name)
                self.hot_standby_demand_var.set(hot_standby_demand[stream])
                self.hot_standby_demand_startup_time.set(hot_standby_startup_time)
            else:
                self.hot_standby_stream_var.set('')
                self.hot_standby_demand_var.set(0)
                self.hot_standby_demand_startup_time.set(0)

            number_parallel_units = int(self.component_object.get_number_parallel_units())

            self.label_capex_value_str = StringVar()
            self.capex_basis_var = StringVar()
            self.capex_basis_var.set(capex_basis)

            self.scalable_var = BooleanVar()
            self.scalable_var.set(False)
            self.label_base_investment_value_str = StringVar()
            self.label_base_capacity_value_str = StringVar()
            self.label_scaling_factor_value_str = StringVar()
            self.label_max_capacity_eoc_value_str = StringVar()

            self.label_lifetime_value_str = StringVar()
            self.label_lifetime_value_str.set(int(lifetime))
            self.label_maintenance_value_str = StringVar()
            self.label_maintenance_value_str.set(maintenance)
            self.label_min_capacity_value_str = StringVar()
            self.label_min_capacity_value_str.set(min_p)
            self.label_max_capacity_value_str = StringVar()
            self.label_max_capacity_value_str.set(max_p)
            self.label_ramp_down_value_str = StringVar()
            self.label_ramp_down_value_str.set(ramp_down)
            self.label_ramp_up_value_str = StringVar()
            self.label_ramp_up_value_str.set(ramp_up)

            self.label_number_parallel_units_str = StringVar()
            self.label_number_parallel_units_str.set(number_parallel_units)

            # Capex Basis
            ttk.Label(self.frame, text='Investment Basis').grid(row=1, column=0, sticky='ew')

            capex_basis_frame = ttk.Frame(self.frame)

            ttk.Radiobutton(capex_basis_frame, text='Main Input', value='input',
                            variable=self.capex_basis_var, state=DISABLED).grid(row=0, column=0)
            ttk.Radiobutton(capex_basis_frame, text='Main Output', value='output',
                            variable=self.capex_basis_var, state=DISABLED).grid(row=0, column=1)

            capex_basis_frame.grid(row=1, column=1, sticky='ew')

            i = 2

            if self.capex_basis_var.get() == 'input':
                nice_name = self.pm_object.get_nice_name(self.component_object.get_main_input())
                unit = self.pm_object.get_stream(self.component_object.get_main_input()).get_unit()
            else:
                nice_name = self.pm_object.get_nice_name(self.component_object.get_main_output())
                unit = self.pm_object.get_stream(self.component_object.get_main_output()).get_unit()

            if unit == 'GWh':
                unit = 'GW'
                capex_unit = '€/' + unit + ' ' + nice_name
                capacity_unit = 'GW ' + nice_name
            elif unit == 'MWh':
                unit = 'MW'
                capex_unit = '€/' + unit + ' ' + nice_name
                capacity_unit = 'MW ' + nice_name
            elif unit == 'kWh':
                unit = 'kW'
                capex_unit = '€/' + unit + ' ' + nice_name
                capacity_unit = 'kW ' + nice_name
            else:
                capex_unit = '€/' + unit + '*h ' + nice_name
                capacity_unit = unit + '/h ' + nice_name

            if not self.component_object.is_scalable():

                # The parameters below only exist if component is not scalable

                capex = self.component_object.get_capex()
                self.label_capex_value_str.set(capex)

                ttk.Label(self.frame, text='CAPEX [' + capex_unit + ']').grid(column=0,
                                                                                                   row=i, sticky='w')
                ttk.Label(self.frame, text=self.label_capex_value_str.get()).grid(column=1, row=i, sticky='w')

                i += 1

            else:

                # The parameters below only exist if component is scalable

                self.scalable_var.set(True)
                base_investment = self.component_object.get_base_investment()
                base_capacity = self.component_object.get_base_capacity()
                scaling_factor = self.component_object.get_economies_of_scale()
                max_capacity_eoc = self.component_object.get_max_capacity_economies_of_scale()

                self.label_base_investment_value_str.set(base_investment)
                self.label_base_capacity_value_str.set(base_capacity)
                self.label_scaling_factor_value_str.set(scaling_factor)
                self.label_max_capacity_eoc_value_str.set(max_capacity_eoc)

                self.label_base_investment = ttk.Label(self.frame, text='Base investment [€]')
                self.label_base_investment.grid(column=0, row=i+1, sticky='w')
                self.label_base_investment_value = ttk.Label(self.frame,
                                                             text=self.label_base_investment_value_str.get())
                self.label_base_investment_value.grid(column=1, row=i+1, sticky='w')

                self.label_base_capacity = ttk.Label(self.frame, text='Base capacity [' + capacity_unit + ']')
                self.label_base_capacity.grid(column=0, row=i+2, sticky='w')
                self.label_base_capacity_value = ttk.Label(self.frame, text=self.label_base_capacity_value_str.get())
                self.label_base_capacity_value.grid(column=1, row=i+2, sticky='w')

                self.label_scaling_factor = ttk.Label(self.frame, text='Scaling factor')
                self.label_scaling_factor.grid(column=0, row=i+3, sticky='w')
                self.label_scaling_factor_value = ttk.Label(self.frame,
                                                            text=self.label_scaling_factor_value_str.get())
                self.label_scaling_factor_value.grid(column=1, row=i+3, sticky='w')

                self.label_max_capacity_eoc = ttk.Label(self.frame, text='Max capacity [' + capacity_unit + ']')
                self.label_max_capacity_eoc.grid(column=0, row=i+4, sticky='w')
                self.label_max_capacity_eoc_value = ttk.Label(self.frame,
                                                              text=self.label_max_capacity_eoc_value_str.get())
                self.label_max_capacity_eoc_value.grid(column=1, row=i+4, sticky='w')

                i += 4

            ttk.Label(self.frame, text='Lifetime [Years]').grid(column=0, row=i+1, sticky='w')
            ttk.Label(self.frame, text=self.label_lifetime_value_str.get()).grid(column=1, row=i+1, sticky='w')

            ttk.Label(self.frame, text='Maintenance [%]').grid(column=0, row=i+2, sticky='w')
            ttk.Label(self.frame, text=self.label_maintenance_value_str.get()).grid(column=1, row=i+2, sticky='w')

            ttk.Label(self.frame, text='Minimal power [%]').grid(column=0, row=i+3, sticky='w')
            ttk.Label(self.frame, text=self.label_min_capacity_value_str.get()).grid(column=1, row=i+3, sticky='w')

            ttk.Label(self.frame, text='Maximal power [%]').grid(column=0, row=i+4, sticky='w')
            ttk.Label(self.frame, text=self.label_max_capacity_value_str.get()).grid(column=1, row=i+4, sticky='w')

            ttk.Label(self.frame, text='Ramp down time [%/h]').grid(column=0, row=i+5, sticky='w')
            ttk.Label(self.frame, text=self.label_ramp_down_value_str.get()).grid(column=1, row=i+5, sticky='w')

            ttk.Label(self.frame, text='Ramp up time [%/h]').grid(column=0, row=i+6, sticky='w')
            ttk.Label(self.frame, text=self.label_ramp_up_value_str.get()).grid(column=1, row=i+6, sticky='w')

            i += 6

            if self.component_object.get_shut_down_ability():
                ttk.Label(self.frame, text='Cold Start up time [h]').grid(column=0, row=i+1, sticky='w')
                ttk.Label(self.frame, text=self.label_start_up_value_str.get()).grid(column=1, row=i+1, sticky='w')

                i += 2

            if hot_standby_ability:

                ttk.Label(self.frame, text='Hot Standby Input Stream').grid(row=i+1, column=0, sticky='w')
                ttk.Label(self.frame, text=self.hot_standby_stream_var.get()).grid(row=i + 1, column=1, sticky='w')

                if hot_standby_unit == 'MWh':
                    hot_standby_unit = 'MW'
                elif hot_standby_unit == 'kWh':
                    hot_standby_unit = 'kW'
                elif hot_standby_unit == 'GWh':
                    hot_standby_unit = 'GW'
                else:
                    hot_standby_unit = hot_standby_unit + ' / h'

                ttk.Label(self.frame, text='Hot Standby Input Demand [' + hot_standby_unit + ']').grid(row=i + 2,
                                                                                                       column=0,
                                                                                                       sticky='w')
                ttk.Label(self.frame, text=self.hot_standby_demand_var.get()).grid(row=i + 2, column=1, sticky='w')

                ttk.Label(self.frame, text='Hot Standby Start up Time [h]').grid(row=i + 3, column=0, sticky='w')
                ttk.Label(self.frame, text=self.hot_standby_demand_startup_time.get()).grid(row=i + 3, column=1,
                                                                                            sticky='w')

                i += 3

            ttk.Label(self.frame, text='Number of units in system').grid(column=0, row=i + 1, sticky='w')
            ttk.Label(self.frame, text=self.label_number_parallel_units_str.get()).grid(column=1, row=i + 1, sticky='w')

            self.delete_component_dict = {}

            ttk.Button(self.frame, text='Adjust parameters',
                       command=self.adjust_component_value).grid(column=0, row=i + 2, sticky='ew')

            if self.component_object.is_custom():
                ttk.Button(self.frame, text='Default parameters',
                           command=self.set_component_parameters_to_default,
                           state=DISABLED).grid(column=1, row=i + 2, sticky='ew')
            else:
                ttk.Button(self.frame, text='Default parameters',
                           command=self.set_component_parameters_to_default).grid(column=1, row=i + 2, sticky='ew')

            self.frame.grid_columnconfigure(0, weight=1, uniform="a")
            self.frame.grid_columnconfigure(1, weight=1, uniform="a")


class AddNewComponentWindow:

    def add_component_and_kill_window(self):

        # Creates component with dummy parameters and random main conversion

        new_component = ConversionComponent(self.name.get(), self.nice_name.get(), final_unit=True, custom_unit=True)

        input_random = random.choice([*self.pm_object.get_all_streams().keys()])
        new_component.add_input(input_random, 1)
        new_component.set_main_input(input_random)

        output_random = random.choice([*self.pm_object.get_all_streams().keys()])
        new_component.add_output(output_random, 1)
        new_component.set_main_output(output_random)

        self.pm_object.add_component(self.name.get(), new_component)

        for gp in self.pm_object.get_general_parameters():
            self.pm_object.set_applied_parameter_for_component(gp, self.name.get(), True)

        self.parent.pm_object_copy = self.pm_object
        self.parent.update_widgets()

        self.newWindow.destroy()

    def __init__(self, parent, pm_object):

        """
        Window to add new component

        :param parent: Interface object - needed to access Interface functions
        :param pm_object: Parameter object - needed to access and store information
        """

        self.parent = parent
        self.pm_object = pm_object

        self.newWindow = Toplevel()
        self.newWindow.grab_set()
        self.newWindow.title('Add New Component')

        self.nice_name = StringVar()
        self.name = StringVar()

        ttk.Label(self.newWindow, text='Nice name').grid(row=0, column=0, sticky='ew')
        ttk.Entry(self.newWindow, text=self.nice_name).grid(row=0, column=1, sticky='ew')
        ttk.Label(self.newWindow, text='Name').grid(row=1, column=0, sticky='ew')
        ttk.Entry(self.newWindow, text=self.name).grid(row=1, column=1, sticky='ew')

        ttk.Button(self.newWindow, text='Add component',
                   command=self.add_component_and_kill_window).grid(row=2, column=0, sticky='ew')
        ttk.Button(self.newWindow, text='Cancel',
                   command=self.newWindow.destroy).grid(row=2, column=1, sticky='ew')

        self.newWindow.grid_columnconfigure(0, weight=1, uniform='a')
        self.newWindow.grid_columnconfigure(1, weight=1, uniform='a')


class ConversionFrame:

    def set_component_conversions_to_default(self):

        # Remove all inputs and outputs from component
        all_inputs = dict(self.component_object.get_inputs())

        for comp_input in all_inputs:
            self.component_object.remove_input(comp_input)

        all_outputs = dict(self.component_object.get_outputs())

        for comp_output in all_outputs:
            self.component_object.remove_output(comp_output)

        # get inputs and outputs from original parameter object
        original_component = self.pm_object_original.get_component(self.component_object.get_name())

        all_inputs = dict(original_component.get_inputs())
        all_outputs = dict(original_component.get_outputs())

        # add inputs and outputs to component
        for comp_input in all_inputs:
            self.component_object.add_input(comp_input, original_component.get_inputs()[comp_input])

        for comp_output in all_outputs:
            self.component_object.add_output(comp_output, original_component.get_outputs()[comp_output])

        # set main input and output
        main_input = original_component.get_main_input()
        main_output = original_component.get_main_output()

        self.component_object.set_main_input(main_input)
        self.component_object.set_main_output(main_output)

        self.parent.parent.parent.pm_object_copy = self.pm_object
        self.parent.parent.parent.update_widgets()

    def create_me_balance_window(self):

        def get_values_and_kill_me_balance_window():

            def main_input_or_output_problem():

                def kill_main_i_o_window():
                    missing_main_i_o_window.destroy()

                missing_main_i_o_window = Toplevel()
                missing_main_i_o_window.title('')
                missing_main_i_o_window.grab_set()

                ttk.Label(missing_main_i_o_window, text=text).pack()
                ttk.Button(missing_main_i_o_window, text='Ok', command=kill_main_i_o_window).pack()

            # Check if main input and output are chosen and inform user if not
            main_input_exists = False
            for inp in self.current_inputs:
                if inp == current_main_input_var.get():
                    main_input_exists = True

            main_output_exists = False
            for inp in self.current_outputs:
                if inp == current_main_output_var.get():
                    main_output_exists = True

            if (not main_input_exists) & (not main_output_exists):
                text = 'Please choose main input and output'
                main_input_or_output_problem()
            elif main_input_exists & (not main_output_exists):
                text = 'Please choose main output'
                main_input_or_output_problem()
            elif (not main_input_exists) & main_output_exists:
                text = 'Please choose main input'
                main_input_or_output_problem()
            else:  # case main input and output are chosen

                # Delete all inputs and outputs from component
                all_inputs = dict(self.component_object.get_inputs())

                for comp_input in all_inputs:
                    self.component_object.remove_input(comp_input)

                all_outputs = dict(self.component_object.get_outputs())

                for comp_output in all_outputs:
                    self.component_object.remove_output(comp_output)

                # Add adjusted inputs and outputs to component
                main_input = current_main_input_var.get()
                main_output = current_main_output_var.get()

                for comp_input in self.current_inputs:
                    self.component_object.add_input(comp_input, self.current_input_coefficients[comp_input])

                    if comp_input not in self.pm_object.get_all_streams():
                        s = Stream(comp_input, self.current_nice_names[comp_input], self.current_units[comp_input],
                                   final_stream=True, custom_stream=True)
                        self.pm_object.add_stream(comp_input, s)

                for comp_output in self.current_outputs:
                    self.component_object.add_output(comp_output, self.current_output_coefficients[comp_output])

                    if comp_output not in self.pm_object.get_all_streams():
                        s = Stream(comp_output, self.current_nice_names[comp_output], self.current_units[comp_output],
                                   final_stream=True, custom_stream=True)
                        self.pm_object.add_stream(comp_output, s)

                # set main input and output, and adjust capex unit depending on main input
                self.component_object.set_main_input(main_input)
                self.component_object.set_main_output(main_output)

                # Check if streams are not used anymore and delete them from all streams
                for stream in self.pm_object.get_all_streams():
                    stream_used = False
                    for c in self.pm_object.get_specific_components('final', 'conversion'):
                        inputs = c.get_inputs()
                        for inp in [*inputs.keys()]:
                            if inp == stream:
                                stream_used = True
                                break

                        outputs = c.get_outputs()
                        for outp in [*outputs.keys()]:
                            if outp == stream:
                                stream_used = True
                                break

                    if not stream_used:
                        self.pm_object.remove_stream(stream)

                # Check if stream is used again and add it to all streams
                used_streams = []
                for c in self.pm_object.get_specific_components('final', 'conversion'):
                    inputs = c.get_inputs()
                    for inp in [*inputs.keys()]:
                        if inp not in used_streams:
                            used_streams.append(inp)

                    outputs = c.get_outputs()
                    for outp in [*outputs.keys()]:
                        if outp not in used_streams:
                            used_streams.append(outp)

                for stream in used_streams:
                    if stream not in self.pm_object.get_specific_streams('final'):
                        self.pm_object.activate_stream(stream)

                me_balance_window.destroy()

                self.parent.parent.parent.pm_object_copy = self.pm_object
                self.parent.parent.parent.update_widgets()

        def kill_only_me_balance_window():
            me_balance_window.destroy()

        def adjust_input(number_to_adjust):

            input_stream_to_adjust = input_streams[number_to_adjust]
            input_stream_nice_name_to_adjust = input_nice_names[number_to_adjust]
            coefficient_to_adjust = input_coefficients[number_to_adjust]

            def change_input_entry():
                if input_radiobutton_var.get() == 'existing':
                    combobox_existing_stream_input.config(state=NORMAL)

                    input_stream_name_entry.config(state=DISABLED)
                    input_stream_abbreviation_entry.config(state=DISABLED)
                    input_unit_entry.config(state=DISABLED)
                else:
                    combobox_existing_stream_input.config(state=DISABLED)
                    input_stream_name_entry.config(state=NORMAL)
                    input_stream_abbreviation_entry.config(state=NORMAL)
                    input_unit_entry.config(state=NORMAL)

            def get_values_and_kill():

                if input_radiobutton_var.get() == 'existing':

                    if combobox_existing_stream_input.get() in [*self.current_nice_names.values()]:
                        for name, nice_name in self.current_nice_names.items():
                            if nice_name == combobox_existing_stream_input.get():
                                stream = name

                        for n, stream_n in enumerate(self.current_inputs):
                            if stream_n == input_stream_to_adjust:
                                self.current_inputs[n] = stream
                    else:
                        stream = self.pm_object.get_abbreviation(combobox_existing_stream_input.get())

                        for n, stream_n in enumerate(self.current_inputs):
                            if stream_n == input_stream_to_adjust:
                                self.current_inputs[n] = stream

                        self.current_nice_names[stream] = self.pm_object.get_nice_name(stream)
                        self.current_units[stream] = self.pm_object.get_stream(stream).get_unit()

                    for n, stream_n in enumerate(self.current_inputs):
                        if stream_n == input_stream_to_adjust:
                            self.current_inputs[n] = stream

                else:
                    stream = input_stream_abbreviation_entry.get()
                    for n, stream_n in enumerate(self.current_inputs):
                        if stream_n == input_stream_to_adjust:
                            self.current_inputs[n] = stream

                    self.current_nice_names[stream] = input_stream_name_entry.get()
                    self.current_units[stream] = input_unit_entry.get()

                    self.streams_add_conversion_nice_names.append(input_stream_name_entry.get())

                self.current_input_coefficients[stream] = coefficient_entry_var.get()

                adjust_input_window.destroy()
                me_balance_window.grab_set()
                update_me_balance_window()

            def kill_only():

                if input_radiobutton_var.get() == 'new':
                    if input_stream_name_entry.get() in self.streams_add_conversion_nice_names:
                        self.streams_add_conversion_nice_names.remove(input_stream_name_entry.get())

                adjust_input_window.destroy()
                me_balance_window.grab_set()

            adjust_input_window = Toplevel()
            adjust_input_window.title('Adjust Input')
            adjust_input_window.grab_set()

            input_radiobutton_var = StringVar()
            input_radiobutton_var.set('existing')
            input_radiobutton_existing = ttk.Radiobutton(adjust_input_window, text='Existing stream',
                                                         variable=input_radiobutton_var,
                                                         value='existing', command=change_input_entry)
            input_radiobutton_existing.grid(row=1, column=0, sticky='ew')

            combobox_existing_stream_input = ttk.Combobox(adjust_input_window,
                                                          values=self.streams_add_conversion_nice_names,
                                                          state='readonly')
            combobox_existing_stream_input.grid(row=2, column=0, sticky='ew')
            combobox_existing_stream_input.set(input_stream_nice_name_to_adjust)

            input_radiobutton_new = ttk.Radiobutton(adjust_input_window, text='New stream',
                                                    variable=input_radiobutton_var, value='new',
                                                    command=change_input_entry)
            input_radiobutton_new.grid(row=3, column=0, sticky='ew')

            input_stream_name_entry = ttk.Entry(adjust_input_window)
            input_stream_name_entry.insert(END, 'Nice Name')
            input_stream_name_entry.config(state=DISABLED)
            input_stream_name_entry.grid(row=4, column=0, sticky='ew')

            input_stream_abbreviation_entry = ttk.Entry(adjust_input_window)
            input_stream_abbreviation_entry.insert(END, 'Abbreviation')
            input_stream_abbreviation_entry.config(state=DISABLED)
            input_stream_abbreviation_entry.grid(row=5, column=0, sticky='ew')

            input_unit_entry = ttk.Entry(adjust_input_window)
            input_unit_entry.insert(END, 'Unit')
            input_unit_entry.config(state=DISABLED)
            input_unit_entry.grid(row=6, column=0, sticky='ew')

            coefficient_entry_var = StringVar()
            coefficient_entry_var.set(coefficient_to_adjust)
            tk.Label(adjust_input_window, text='Coefficient').grid(row=7, column=0, columnspan=3, sticky='ew')
            coefficient_entry = Entry(adjust_input_window, text=coefficient_entry_var)
            coefficient_entry.grid(row=8, column=0, columnspan=3, sticky='ew')

            adjust_input_button_frame = ttk.Frame(adjust_input_window)

            ttk.Button(adjust_input_button_frame, text='Ok', command=get_values_and_kill).grid(row=0, column=0)
            ttk.Button(adjust_input_button_frame, text='Cancel', command=kill_only).grid(row=0, column=1)

            adjust_input_button_frame.grid_columnconfigure(0, weight=1, uniform='a')
            adjust_input_button_frame.grid_columnconfigure(1, weight=1, uniform='a')

            adjust_input_button_frame.grid(row=9, column=0, sticky='ew')

        def adjust_output(number_to_adjust):

            output_stream_to_adjust = output_streams[number_to_adjust]
            output_stream_nice_name_to_adjust = output_nice_names[number_to_adjust]
            coefficient_to_adjust = output_coefficients[number_to_adjust]

            def change_output_entry():
                if output_radiobutton_var.get() == 'existing':
                    combobox_existing_stream_output.config(state=NORMAL)

                    output_stream_name_entry.config(state=DISABLED)
                    output_stream_abbreviation_entry.config(state=DISABLED)
                    output_unit_entry.config(state=DISABLED)
                else:
                    combobox_existing_stream_output.config(state=DISABLED)
                    output_stream_name_entry.config(state=NORMAL)
                    output_stream_abbreviation_entry.config(state=NORMAL)
                    output_unit_entry.config(state=NORMAL)

            def get_values_and_kill():

                if output_radiobutton_var.get() == 'existing':
                    if combobox_existing_stream_output.get() in [*self.current_nice_names.values()]:
                        for name, nice_name in self.current_nice_names.items():
                            if nice_name == combobox_existing_stream_output.get():
                                stream = name

                        for n, stream_n in enumerate(self.current_outputs):
                            if stream_n == output_stream_to_adjust:
                                self.current_outputs[n] = stream
                    else:
                        stream = self.pm_object.get_abbreviation(combobox_existing_stream_output.get())

                        for n, stream_n in enumerate(self.current_outputs):
                            if stream_n == output_stream_to_adjust:
                                self.current_outputs[n] = stream

                        self.current_nice_names[stream] = self.pm_object.get_nice_name(stream)
                        self.current_units[stream] = self.pm_object.get_stream(stream).get_unit()

                else:
                    stream = output_stream_abbreviation_entry.get()
                    for n, stream_n in enumerate(self.current_outputs):
                        if stream_n == output_stream_to_adjust:
                            self.current_outputs[n] = stream

                    self.current_nice_names[stream] = output_stream_name_entry.get()
                    self.current_units[stream] = output_unit_entry.get()

                    self.streams_add_conversion_nice_names.append(output_stream_name_entry.get())

                self.current_output_coefficients[stream] = coefficient_entry_var.get()

                adjust_output_window.destroy()
                me_balance_window.grab_set()
                update_me_balance_window()

            def kill_only():

                if output_radiobutton_var.get() == 'new':
                    if output_stream_name_entry.get() in self.streams_add_conversion_nice_names:
                        self.streams_add_conversion_nice_names.remove(output_stream_name_entry.get())

                adjust_output_window.destroy()
                me_balance_window.grab_set()

            adjust_output_window = Toplevel()
            adjust_output_window.title('Adjust Output')
            adjust_output_window.grab_set()

            output_radiobutton_var = StringVar()
            output_radiobutton_var.set('existing')
            output_radiobutton_existing = ttk.Radiobutton(adjust_output_window, text='Existing stream',
                                                         variable=output_radiobutton_var,
                                                         value='existing', command=change_output_entry)
            output_radiobutton_existing.grid(row=1, column=0, sticky='ew')

            combobox_existing_stream_output = ttk.Combobox(adjust_output_window,
                                                          values=self.streams_add_conversion_nice_names,
                                                           state='readonly')
            combobox_existing_stream_output.grid(row=2, column=0, sticky='ew')
            combobox_existing_stream_output.set(output_stream_nice_name_to_adjust)

            output_radiobutton_new = ttk.Radiobutton(adjust_output_window, text='New stream',
                                                    variable=output_radiobutton_var, value='new',
                                                    command=change_output_entry)
            output_radiobutton_new.grid(row=3, column=0, sticky='ew')

            output_stream_name_entry = ttk.Entry(adjust_output_window)
            output_stream_name_entry.insert(END, 'Nice Name')
            output_stream_name_entry.config(state=DISABLED)
            output_stream_name_entry.grid(row=4, column=0, sticky='ew')

            output_stream_abbreviation_entry = ttk.Entry(adjust_output_window)
            output_stream_abbreviation_entry.insert(END, 'Abbreviation')
            output_stream_abbreviation_entry.config(state=DISABLED)
            output_stream_abbreviation_entry.grid(row=5, column=0, sticky='ew')

            output_unit_entry = ttk.Entry(adjust_output_window)
            output_unit_entry.insert(END, 'Unit')
            output_unit_entry.config(state=DISABLED)
            output_unit_entry.grid(row=6, column=0, sticky='ew')

            coefficient_entry_var = StringVar()
            coefficient_entry_var.set(coefficient_to_adjust)
            tk.Label(adjust_output_window, text='Coefficient').grid(row=7, column=0, columnspan=3, sticky='ew')
            coefficient_entry = Entry(adjust_output_window, text=coefficient_entry_var)
            coefficient_entry.grid(row=8, column=0, columnspan=3, sticky='ew')

            adjust_output_button_frame = ttk.Frame(adjust_output_window)

            ttk.Button(adjust_output_button_frame, text='Ok', command=get_values_and_kill).grid(row=0, column=0)
            ttk.Button(adjust_output_button_frame, text='Cancel', command=kill_only).grid(row=0, column=1)

            adjust_output_button_frame.grid_columnconfigure(0, weight=1, uniform='a')
            adjust_output_button_frame.grid_columnconfigure(1, weight=1, uniform='a')

            adjust_output_button_frame.grid(row=9, column=0, sticky='ew')

        def delete_input():

            def delete_and_kill():

                for ind_choice in [*choice.keys()]:
                    if choice[ind_choice].get():
                        self.current_inputs.remove(input_streams[ind_choice])

                delete_input_window.destroy()
                me_balance_window.grab_set()
                update_me_balance_window()

            def kill_only():
                delete_input_window.destroy()
                me_balance_window.grab_set()

            delete_input_window = Toplevel()
            delete_input_window.title('Delete Input')
            delete_input_window.grab_set()

            choice = {}

            d = 0
            for ind in [*input_nice_names.keys()]:
                choice[ind] = BooleanVar()
                ttk.Checkbutton(delete_input_window, text=input_nice_names[ind],
                                variable=choice[ind]).grid(row=d, columnspan=2, sticky='ew')

                d += 1

            ttk.Button(delete_input_window, text='Delete', command=delete_and_kill).grid(row=d, column=0)
            ttk.Button(delete_input_window, text='Cancel', command=kill_only).grid(row=d, column=1)

        def delete_output():

            def delete_and_kill():

                for ind_choice in [*choice.keys()]:
                    if choice[ind_choice].get():
                        self.current_outputs.remove(output_streams[ind_choice])

                delete_output_window.destroy()
                me_balance_window.grab_set()
                update_me_balance_window()

            def kill_only():
                delete_output_window.destroy()
                me_balance_window.grab_set()

            delete_output_window = Toplevel()
            delete_output_window.title('Delete Output')
            delete_output_window.grab_set()

            choice = {}

            d = 0
            for ind in [*output_nice_names.keys()]:
                choice[ind] = BooleanVar()
                ttk.Checkbutton(delete_output_window, text=output_nice_names[ind],
                                variable=choice[ind]).grid(row=d, columnspan=2, sticky='ew')

                d += 1

            ttk.Button(delete_output_window, text='Delete', command=delete_and_kill).grid(row=d, column=0)
            ttk.Button(delete_output_window, text='Cancel', command=kill_only).grid(row=d, column=1)
            
        def add_input():

            def change_input_entry():
                if input_radiobutton_var.get() == 'existing':
                    combobox_existing_stream_input.config(state=NORMAL)

                    input_stream_name_entry.config(state=DISABLED)
                    input_stream_abbreviation_entry.config(state=DISABLED)
                    input_unit_entry.config(state=DISABLED)
                else:
                    combobox_existing_stream_input.config(state=DISABLED)
                    input_stream_name_entry.config(state=NORMAL)
                    input_stream_abbreviation_entry.config(state=NORMAL)
                    input_unit_entry.config(state=NORMAL)

            def get_values_and_kill():

                if input_radiobutton_var.get() == 'existing':

                    if combobox_existing_stream_input.get() in [*self.current_nice_names.values()]:
                        for name, nice_name in self.current_nice_names.items():
                            if nice_name == combobox_existing_stream_input.get():
                                stream = name
                    else:
                        stream = self.pm_object.get_abbreviation(combobox_existing_stream_input.get())

                        self.current_units[stream] = self.pm_object.get_stream(stream).get_unit()
                        self.current_nice_names[stream] = self.pm_object.get_nice_name(stream)

                    self.current_inputs.append(stream)

                else:
                    stream = input_stream_abbreviation_entry.get()
                    self.current_inputs.append(stream)
                    self.current_units[stream] = input_unit_entry.get()
                    self.current_nice_names[stream] = input_stream_name_entry.get()
                    self.streams_add_conversion_nice_names.append(input_stream_name_entry.get())

                self.current_input_coefficients[stream] = coefficient_entry_var.get()

                add_input_window.destroy()
                me_balance_window.grab_set()
                update_me_balance_window()

            def kill_only():

                if input_radiobutton_var.get() == 'new':
                    if input_stream_name_entry.get() in self.streams_add_conversion_nice_names:
                        self.streams_add_conversion_nice_names.remove(input_stream_name_entry.get())

                add_input_window.destroy()
                me_balance_window.grab_set()

            add_input_window = Toplevel()
            add_input_window.title('Add Input')
            add_input_window.grab_set()

            input_radiobutton_var = StringVar()
            input_radiobutton_var.set('existing')
            input_radiobutton_existing = ttk.Radiobutton(add_input_window, text='Existing stream',
                                                         variable=input_radiobutton_var,
                                                         value='existing', command=change_input_entry)
            input_radiobutton_existing.grid(row=1, column=0, sticky='ew')

            combobox_existing_stream_input = ttk.Combobox(add_input_window,
                                                          values=self.streams_add_conversion_nice_names,
                                                          state='readonly')
            combobox_existing_stream_input.grid(row=2, column=0, sticky='ew')
            combobox_existing_stream_input.set('')

            input_radiobutton_new = ttk.Radiobutton(add_input_window, text='New stream',
                                                    variable=input_radiobutton_var, value='new',
                                                    command=change_input_entry)
            input_radiobutton_new.grid(row=3, column=0, sticky='ew')

            input_stream_name_entry = ttk.Entry(add_input_window)
            input_stream_name_entry.insert(END, 'Nice Name')
            input_stream_name_entry.config(state=DISABLED)
            input_stream_name_entry.grid(row=4, column=0, sticky='ew')

            input_stream_abbreviation_entry = ttk.Entry(add_input_window)
            input_stream_abbreviation_entry.insert(END, 'Abbreviation')
            input_stream_abbreviation_entry.config(state=DISABLED)
            input_stream_abbreviation_entry.grid(row=5, column=0, sticky='ew')

            input_unit_entry = ttk.Entry(add_input_window)
            input_unit_entry.insert(END, 'Unit')
            input_unit_entry.config(state=DISABLED)
            input_unit_entry.grid(row=6, column=0, sticky='ew')

            coefficient_entry_var = StringVar()
            coefficient_entry_var.set(1)
            tk.Label(add_input_window, text='Coefficient').grid(row=7, column=0, columnspan=3, sticky='ew')
            coefficient_entry = Entry(add_input_window, text=coefficient_entry_var)
            coefficient_entry.grid(row=8, column=0, columnspan=3, sticky='ew')

            add_input_button_frame = ttk.Frame(add_input_window)

            ttk.Button(add_input_button_frame, text='Ok', command=get_values_and_kill).grid(row=0, column=0)
            ttk.Button(add_input_button_frame, text='Cancel', command=kill_only).grid(row=0, column=1)

            add_input_button_frame.grid_columnconfigure(0, weight=1, uniform='a')
            add_input_button_frame.grid_columnconfigure(1, weight=1, uniform='a')

            add_input_button_frame.grid(row=9, column=0, sticky='ew')
            
        def add_output():
            
            def change_output_entry():
                if output_radiobutton_var.get() == 'existing':
                    combobox_existing_stream_output.config(state=NORMAL)

                    output_stream_name_entry.config(state=DISABLED)
                    output_stream_abbreviation_entry.config(state=DISABLED)
                    output_unit_entry.config(state=DISABLED)
                else:
                    combobox_existing_stream_output.config(state=DISABLED)
                    output_stream_name_entry.config(state=NORMAL)
                    output_stream_abbreviation_entry.config(state=NORMAL)
                    output_unit_entry.config(state=NORMAL)

            def get_values_and_kill():

                if output_radiobutton_var.get() == 'existing':
                    if combobox_existing_stream_output.get() in [*self.current_nice_names.values()]:
                        for name, nice_name in self.current_nice_names.items():
                            if nice_name == combobox_existing_stream_output.get():
                                stream = name
                    else:
                        stream = self.pm_object.get_abbreviation(combobox_existing_stream_output.get())

                        self.current_units[stream] = self.pm_object.get_stream(stream).get_unit()
                        self.current_nice_names[stream] = self.pm_object.get_nice_name(stream)

                    self.current_outputs.append(stream)

                else:
                    stream = output_stream_abbreviation_entry.get()
                    self.current_outputs.append(stream)
                    self.current_units[stream] = output_unit_entry.get()
                    self.current_nice_names[stream] = output_stream_name_entry.get()
                    self.streams_add_conversion_nice_names.append(output_stream_name_entry.get())

                self.current_output_coefficients[stream] = coefficient_entry_var.get()

                add_output_window.destroy()
                me_balance_window.grab_set()
                update_me_balance_window()

            def kill_only():

                if output_radiobutton_var.get() == 'new':
                    if output_stream_name_entry.get() in self.streams_add_conversion_nice_names:
                        self.streams_add_conversion_nice_names.remove(output_stream_name_entry.get())

                add_output_window.destroy()
                me_balance_window.grab_set()

            add_output_window = Toplevel()
            add_output_window.title('Add Output')
            add_output_window.grab_set()

            output_radiobutton_var = StringVar()
            output_radiobutton_var.set('existing')
            output_radiobutton_existing = ttk.Radiobutton(add_output_window, text='Existing stream',
                                                         variable=output_radiobutton_var,
                                                         value='existing', command=change_output_entry)
            output_radiobutton_existing.grid(row=1, column=0, sticky='ew')

            combobox_existing_stream_output = ttk.Combobox(add_output_window,
                                                          values=self.streams_add_conversion_nice_names,
                                                           state='readonly')
            combobox_existing_stream_output.grid(row=2, column=0, sticky='ew')
            combobox_existing_stream_output.set('')

            output_radiobutton_new = ttk.Radiobutton(add_output_window, text='New stream',
                                                    variable=output_radiobutton_var, value='new',
                                                    command=change_output_entry)
            output_radiobutton_new.grid(row=3, column=0, sticky='ew')

            output_stream_name_entry = ttk.Entry(add_output_window)
            output_stream_name_entry.insert(END, 'Nice Name')
            output_stream_name_entry.config(state=DISABLED)
            output_stream_name_entry.grid(row=4, column=0, sticky='ew')

            output_stream_abbreviation_entry = ttk.Entry(add_output_window)
            output_stream_abbreviation_entry.insert(END, 'Abbreviation')
            output_stream_abbreviation_entry.config(state=DISABLED)
            output_stream_abbreviation_entry.grid(row=5, column=0, sticky='ew')

            output_unit_entry = ttk.Entry(add_output_window)
            output_unit_entry.insert(END, 'Unit')
            output_unit_entry.config(state=DISABLED)
            output_unit_entry.grid(row=6, column=0, sticky='ew')

            coefficient_entry_var = StringVar()
            coefficient_entry_var.set(1)
            tk.Label(add_output_window, text='Coefficient').grid(row=7, column=0, columnspan=3, sticky='ew')
            coefficient_entry = Entry(add_output_window, text=coefficient_entry_var)
            coefficient_entry.grid(row=8, column=0, columnspan=3, sticky='ew')

            add_output_button_frame = ttk.Frame(add_output_window)

            ttk.Button(add_output_button_frame, text='Ok', command=get_values_and_kill).grid(row=0, column=0)
            ttk.Button(add_output_button_frame, text='Cancel', command=kill_only).grid(row=0, column=1)

            add_output_button_frame.grid_columnconfigure(0, weight=1, uniform='a')
            add_output_button_frame.grid_columnconfigure(1, weight=1, uniform='a')

            add_output_button_frame.grid(row=9, column=0, sticky='ew')

        def update_me_balance_window():

            # delete widgets
            for child in me_balance_window.winfo_children():
                child.destroy()

            input_frame = ttk.Frame(me_balance_window)

            # Inputs
            ttk.Label(input_frame, text='Inputs', font='Helvetica 10 bold').grid(row=0, column=0, columnspan=5, sticky='ew')

            ttk.Label(input_frame, text='Main').grid(row=1, column=1, sticky='ew')
            ttk.Label(input_frame, text='Coefficient').grid(row=1, column=2, sticky='ew')
            ttk.Label(input_frame, text='Unit').grid(row=1, column=3, sticky='ew')
            ttk.Label(input_frame, text='Stream').grid(row=1, column=4, sticky='ew')

            i = 2
            for input_stream in self.current_inputs:
                input_streams[i] = input_stream

                ttk.Button(input_frame, text='Adjust',
                           command=lambda i=i: adjust_input(i)).grid(row=i, column=0, sticky='ew')

                coefficient = self.current_input_coefficients[input_stream]
                input_coefficients[i] = coefficient

                unit = self.current_units[input_stream]

                stream_nice_name = self.current_nice_names[input_stream]
                input_nice_names[i] = stream_nice_name

                ttk.Radiobutton(input_frame, variable=current_main_input_var, value=input_stream).grid(row=i, column=1, sticky='ew')
                ttk.Label(input_frame, text=coefficient).grid(row=i, column=2, sticky='ew')
                ttk.Label(input_frame, text=unit).grid(row=i, column=3, sticky='ew')
                ttk.Label(input_frame, text=stream_nice_name).grid(row=i, column=4, sticky='ew')

                i += 1

            input_frame.grid(row=0, column=0, sticky='new')

            output_frame = ttk.Frame(me_balance_window)

            # Outputs
            ttk.Label(output_frame, text='Outputs', font='Helvetica 10 bold').grid(row=0, column=0, columnspan=5, sticky='ew')

            ttk.Label(output_frame, text='Main').grid(row=1, column=1, sticky='ew')
            ttk.Label(output_frame, text='Coefficient').grid(row=1, column=2, sticky='ew')
            ttk.Label(output_frame, text='Unit').grid(row=1, column=3, sticky='ew')
            ttk.Label(output_frame, text='Stream').grid(row=1, column=4, sticky='ew')

            j = 2
            for output_stream in self.current_outputs:
                output_streams[j] = output_stream

                ttk.Button(output_frame, text='Adjust',
                           command=lambda j=j: adjust_output(j)).grid(row=j, column=0, sticky='ew')

                coefficient = self.current_output_coefficients[output_stream]
                output_coefficients[j] = coefficient

                unit = self.current_units[output_stream]

                stream_nice_name = self.current_nice_names[output_stream]
                output_nice_names[j] = stream_nice_name

                rb = ttk.Radiobutton(output_frame, variable=current_main_output_var, value=output_stream)
                rb.grid(row=j, column=1, sticky='ew')
                ttk.Label(output_frame, text=coefficient).grid(row=j, column=2, sticky='ew')
                ttk.Label(output_frame, text=unit).grid(row=j, column=3, sticky='ew')
                ttk.Label(output_frame, text=stream_nice_name).grid(row=j, column=4, sticky='ew')

                j += 1

            output_frame.grid(row=0, column=2, sticky='new')

            if i >= j:
                ttk.Separator(me_balance_window, orient='vertical').grid(row=0, rowspan=i + 1, column=1, sticky=N + S)
            else:
                ttk.Separator(me_balance_window, orient='vertical').grid(row=0, rowspan=j + 1, column=1, sticky=N + S)

            me_balance_window.grid_columnconfigure(0, weight=1, uniform='a')
            me_balance_window.grid_columnconfigure(1, weight=0)
            me_balance_window.grid_columnconfigure(2, weight=1, uniform='a')

            button_frame = ttk.Frame(me_balance_window)

            button_frame.grid_columnconfigure(0, weight=1)
            button_frame.grid_columnconfigure(1, weight=1)

            ttk.Button(button_frame, text='Add Input',
                       command=add_input).grid(row=0, column=0, sticky=W + E)
            ttk.Button(button_frame, text='Add Output',
                       command=add_output).grid(row=0, column=1, sticky=W + E)

            ttk.Button(button_frame, text='Delete Input',
                       command=delete_input).grid(row=1, column=0, sticky=W + E)
            ttk.Button(button_frame, text='Delete Output',
                       command=delete_output).grid(row=1, column=1, sticky=W + E)
            ttk.Button(button_frame, text='Ok',
                       command=get_values_and_kill_me_balance_window).grid(row=2, column=0, sticky=W + E)
            ttk.Button(button_frame, text='Cancel',
                       command=kill_only_me_balance_window).grid(row=2, column=1, sticky=W + E)

            if i >= j:
                button_frame.grid(row=i, column=0, columnspan=3, sticky='ew')
            else:
                button_frame.grid(row=j, column=0, columnspan=3, sticky='ew')

        me_balance_window = Toplevel()
        me_balance_window.title('Adjust Mass Energy Balance')
        me_balance_window.grab_set()

        input_frame = ttk.Frame(me_balance_window)

        # Inputs
        ttk.Label(input_frame, text='Inputs', font='Helvetica 10 bold').grid(row=0, column=0, columnspan=5)

        ttk.Label(input_frame, text='Main').grid(row=1, column=1)
        ttk.Label(input_frame, text='Coefficient').grid(row=1, column=2)
        ttk.Label(input_frame, text='Unit').grid(row=1, column=3)
        ttk.Label(input_frame, text='Stream').grid(row=1, column=4)

        input_streams = {}
        input_nice_names = {}
        input_coefficients = {}

        current_main_input_var = StringVar()
        current_main_input_var.set(self.current_input_main)

        i = 2
        for input_stream in self.current_inputs:
            input_streams[i] = input_stream

            ttk.Button(input_frame, text='Adjust',
                       command=lambda i=i: adjust_input(i)).grid(row=i, column=0)

            coefficient = self.current_input_coefficients[input_stream]
            input_coefficients[i] = coefficient

            unit = self.current_units[input_stream]

            stream_nice_name = self.current_nice_names[input_stream]
            input_nice_names[i] = stream_nice_name

            ttk.Radiobutton(input_frame, variable=current_main_input_var, value=input_stream).grid(row=i, column=1)
            ttk.Label(input_frame, text=coefficient).grid(row=i, column=2)
            ttk.Label(input_frame, text=unit).grid(row=i, column=3)
            ttk.Label(input_frame, text=stream_nice_name).grid(row=i, column=4)

            i += 1

        input_frame.grid(row=0, column=0, sticky='new')

        output_frame = ttk.Frame(me_balance_window)

        # Outputs
        ttk.Label(output_frame, text='Outputs', font='Helvetica 10 bold').grid(row=0, column=0, columnspan=5)

        ttk.Label(output_frame, text='Main').grid(row=1, column=1)
        ttk.Label(output_frame, text='Coefficient').grid(row=1, column=2)
        ttk.Label(output_frame, text='Unit').grid(row=1, column=3)
        ttk.Label(output_frame, text='Stream').grid(row=1, column=4)

        output_streams = {}
        output_nice_names = {}
        output_coefficients = {}

        current_main_output_var = StringVar()
        current_main_output_var.set(self.current_output_main)

        j = 2
        for output_stream in self.current_outputs:
            output_streams[j] = output_stream

            ttk.Button(output_frame, text='Adjust',
                       command=lambda j=j: adjust_output(j)).grid(row=j, column=0)

            coefficient = self.current_output_coefficients[output_stream]
            output_coefficients[j] = coefficient

            unit = self.current_units[output_stream]

            stream_nice_name = self.current_nice_names[output_stream]
            output_nice_names[j] = stream_nice_name

            rb = ttk.Radiobutton(output_frame, variable=current_main_output_var, value=output_stream)
            rb.grid(row=j, column=1)
            ttk.Label(output_frame, text=coefficient).grid(row=j, column=2)
            ttk.Label(output_frame, text=unit).grid(row=j, column=3)
            ttk.Label(output_frame, text=stream_nice_name).grid(row=j, column=4)

            j += 1

        output_frame.grid(row=0, column=2, sticky='new')

        if i >= j:
            ttk.Separator(me_balance_window, orient='vertical').grid(row=0, rowspan=i + 1, column=1, sticky=N + S)
        else:
            ttk.Separator(me_balance_window, orient='vertical').grid(row=0, rowspan=j + 1, column=1, sticky=N + S)

        me_balance_window.grid_columnconfigure(0, weight=1, uniform='a')
        me_balance_window.grid_columnconfigure(1, weight=0)
        me_balance_window.grid_columnconfigure(2, weight=1, uniform='a')

        button_frame = ttk.Frame(me_balance_window)

        button_frame.grid_columnconfigure(0, weight=1, uniform='a')
        button_frame.grid_columnconfigure(1, weight=1, uniform='a')

        ttk.Button(button_frame, text='Add Input',
                   command=add_input).grid(row=0, column=0, sticky=W + E)
        ttk.Button(button_frame, text='Add Output',
                   command=add_output).grid(row=0, column=1, sticky=W + E)

        ttk.Button(button_frame, text='Delete Input',
                   command=delete_input).grid(row=1, column=0, sticky=W + E)
        ttk.Button(button_frame, text='Delete Output',
                   command=delete_output).grid(row=1, column=1, sticky=W + E)
        ttk.Button(button_frame, text='Ok',
                   command=get_values_and_kill_me_balance_window).grid(row=2, column=0, sticky=W + E)
        ttk.Button(button_frame, text='Cancel',
                   command=kill_only_me_balance_window).grid(row=2, column=1, sticky=W + E)

        if i >= j:
            button_frame.grid(row=i, column=0, columnspan=3, sticky='ew')
        else:
            button_frame.grid(row=j, column=0, columnspan=3, sticky='ew')

        me_balance_window.mainloop()

    def __init__(self, parent, super_frame, component, pm_object, pm_object_original):

        self.parent = parent
        self.pm_object = pm_object
        self.pm_object_original = pm_object_original
        self.component = component

        self.frame = ttk.Frame(super_frame)

        self.component_object = self.pm_object.get_component(self.component)

        self.streams_add_conversion_nice_names = []
        for s in self.pm_object.get_all_streams():
            self.streams_add_conversion_nice_names.append(self.pm_object.get_nice_name(s))

        self.input_frame = ttk.Frame(self.frame)

        # Inputs
        ttk.Label(self.input_frame, text='Inputs', font='Helvetica 10 bold').grid(row=0, column=0, columnspan=4, sticky='ew')

        ttk.Label(self.input_frame, text='Main').grid(row=1, column=0, sticky='ew')
        ttk.Label(self.input_frame, text='Coefficient').grid(row=1, column=1, sticky='ew')
        ttk.Label(self.input_frame, text='Unit').grid(row=1, column=2, sticky='ew')
        ttk.Label(self.input_frame, text='Stream').grid(row=1, column=3, sticky='ew')

        self.main_input_var = StringVar()
        self.current_inputs = []
        self.current_input_main = str
        self.current_nice_names = {}
        self.current_input_coefficients = {}
        self.current_units = {}

        for s in [*self.pm_object.get_all_streams().values()]:
            self.current_nice_names.update({s.get_name(): s.get_nice_name()})
            self.current_units.update({s.get_name(): s.get_unit()})

        i = 2
        inputs = self.component_object.get_inputs()
        for input_stream in [*inputs.keys()]:

            coefficient = inputs[input_stream]
            unit = self.pm_object.get_stream(input_stream).get_unit()
            stream_nice_name = self.pm_object.get_nice_name(input_stream)

            if input_stream == self.component_object.get_main_input():
                self.main_input_var.set(input_stream)
                self.current_input_main = input_stream

            self.current_inputs.append(input_stream)
            self.current_input_coefficients.update({input_stream: coefficient})

            main_input_radiobutton = ttk.Radiobutton(self.input_frame, variable=self.main_input_var, value=input_stream,
                                                     state=DISABLED)
            main_input_radiobutton.grid(row=i, column=0, sticky='ew')

            ttk.Label(self.input_frame, text=coefficient).grid(row=i, column=1, sticky='ew')
            ttk.Label(self.input_frame, text=unit).grid(row=i, column=2, sticky='ew')
            ttk.Label(self.input_frame, text=stream_nice_name).grid(row=i, column=3, sticky='ew')

            i += 1

        # Outputs
        self.output_frame = ttk.Frame(self.frame)

        ttk.Label(self.output_frame, text='Outputs', font='Helvetica 10 bold').grid(row=0, column=0, columnspan=4,
                                                                                    sticky='ew')

        ttk.Label(self.output_frame, text='Main').grid(row=1, column=0, sticky='ew')
        ttk.Label(self.output_frame, text='Coefficient').grid(row=1, column=1, sticky='ew')
        ttk.Label(self.output_frame, text='Unit').grid(row=1, column=2, sticky='ew')
        ttk.Label(self.output_frame, text='Stream').grid(row=1, column=3, sticky='ew')

        self.main_output_var = StringVar()
        self.current_outputs = []
        self.current_output_main = str
        self.current_output_coefficients = {}

        j = 2
        outputs = self.component_object.get_outputs()
        for output_stream in [*outputs.keys()]:

            coefficient = outputs[output_stream]
            unit = self.pm_object.get_stream(output_stream).get_unit()
            stream_nice_name = self.pm_object.get_nice_name(output_stream)

            if output_stream == self.component_object.get_main_output():
                self.main_output_var.set(output_stream)
                self.current_output_main = output_stream

            self.current_outputs.append(output_stream)
            self.current_output_coefficients.update({output_stream: coefficient})

            main_output_radiobutton = ttk.Radiobutton(self.output_frame, variable=self.main_output_var,
                                                      value=output_stream, state=DISABLED)
            main_output_radiobutton.grid(row=j, column=0, sticky='ew')

            ttk.Label(self.output_frame, text=coefficient).grid(row=j, column=1, sticky='ew')
            ttk.Label(self.output_frame, text=unit).grid(row=j, column=2, sticky='ew')
            ttk.Label(self.output_frame, text=stream_nice_name).grid(row=j, column=3, sticky='ew')

            j += 1

        self.frame.grid_columnconfigure(0, weight=1, uniform="a")
        self.frame.grid_columnconfigure(1, weight=0)
        self.frame.grid_columnconfigure(2, weight=1, uniform="a")

        self.input_frame.grid_columnconfigure(0, weight=1)
        self.input_frame.grid_columnconfigure(1, weight=1)
        self.input_frame.grid_columnconfigure(2, weight=1)
        self.input_frame.grid_columnconfigure(3, weight=1)

        self.input_frame.grid(row=0, column=0, sticky='new')

        if i >= j:
            ttk.Separator(self.frame, orient='vertical').grid(row=0, rowspan=2, column=1, sticky=N+S)
        else:
            ttk.Separator(self.frame, orient='vertical').grid(row=0, rowspan=2, column=1, sticky=N+S)

        self.output_frame.grid_columnconfigure(0, weight=1)
        self.output_frame.grid_columnconfigure(1, weight=1)
        self.output_frame.grid_columnconfigure(2, weight=1)
        self.output_frame.grid_columnconfigure(3, weight=1)

        self.output_frame.grid(row=0, column=2, sticky='new')

        button_frame = ttk.Frame(self.frame)

        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)

        ttk.Button(button_frame, text='Adjust',
                   command=self.create_me_balance_window).grid(row=0, column=0, sticky=W + E)

        if self.component_object.is_custom():
            ttk.Button(button_frame, text='Reset',
                       command=self.set_component_conversions_to_default, state=DISABLED) \
                .grid(row=0, column=1, sticky=W + E)
        else:
            ttk.Button(button_frame, text='Reset',
                       command=self.set_component_conversions_to_default, state=NORMAL) \
                .grid(row=0, column=1, sticky=W + E)

        if i >= j:
            button_frame.grid(row=2, column=0, columnspan=3, sticky='ew')
        else:
            button_frame.grid(row=2, column=0, columnspan=3, sticky='ew')
