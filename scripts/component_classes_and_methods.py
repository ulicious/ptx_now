import tkinter as tk
from tkinter import ttk
from tkinter import *
import random
import pandas as pd

from objects_formulation import Stream
from objects_formulation import ConversionComponent


class ComponentFrame:

    def __init__(self, parent, root, component, pm_object, pm_object_original):

        """
        Component base frame
        Builds basis for component parameters frame and component streams frame

        Input:
        - parent: to access function of parents (e.g., update whole interface)
        - root: to create new frames
        - component: name of component
        - pm_object_copy: Has stored all information and will be changed if adjustments conducted
        - pm_object_original: To restore default settings
        """

        self.root = root
        self.parent = parent
        self.pm_object = pm_object
        self.pm_object_original = pm_object_original
        self.component = component

        self.frame = tk.Frame(parent.sub_frame)

        if self.component != '':

            # Create frame for parameters, main conversion and side conversions
            self.parameter_frame = ComponentParametersFrame(self.parent, self.root, self.frame, self.component,
                                                            self.pm_object, self.pm_object_original)
            self.conversion_frame_main = ConversionFrame(self, self.root, self.frame, self.component, 'main',
                                                         self.pm_object, self.pm_object_original)
            self.conversion_frame_side = ConversionFrame(self, self.root, self.frame, self.component, 'side',
                                                         self.pm_object, self.pm_object_original)

            # Attach frames to interface and separate with separators
            ttk.Separator(self.frame, orient='horizontal').pack(fill="both", expand=True)
            self.parameter_frame.frame.pack(fill="both", expand=True)
            ttk.Separator(self.frame, orient='horizontal').pack(fill="both", expand=True)
            self.conversion_frame_main.frame.pack(fill="both", expand=True)
            self.conversion_frame_side.frame.pack(fill="both", expand=True)
            ttk.Separator(self.frame, orient='horizontal').pack(fill="both", expand=True)


class ComponentParametersFrame:

    def adjust_component_value(self):
        def get_value_and_kill_window():

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
                self.component_object.set_shut_down_time(float(self.label_shut_down_value_str.get()))
                self.component_object.set_start_up_time(float(self.label_start_up_value_str.get()))

            self.component_object.set_number_parallel_units(float(self.label_number_parallel_units_str.get()))

            self.parent.parent.pm_object_copy = self.pm_object
            self.parent.parent.update_widgets()

            newWindow.destroy()

        def kill_window():
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
                entry_shut_down.config(state=NORMAL)
                entry_start_up.config(state=NORMAL)

            else:
                entry_shut_down.config(state=DISABLED)
                entry_start_up.config(state=DISABLED)

        # Toplevel object which will
        # be treated as a new window
        newWindow = Toplevel(self.root)
        newWindow.grid_columnconfigure(0, weight=1)
        newWindow.grid_columnconfigure(1, weight=1)
        newWindow.grab_set()

        # sets the title of the
        # Toplevel widget
        newWindow.title('Adjust component values')

        tk.Checkbutton(newWindow, text='Scalable?',
                       variable=self.scalable_var,
                       command=activate_scale_no_scale).grid(row=0, column=0, columnspan=2, sticky='w')

        if self.component_object.is_scalable():
            status_scale = NORMAL
            status_no_scale = DISABLED
        else:
            status_scale = DISABLED
            status_no_scale = NORMAL

        tk.Label(newWindow, text='Capex [' + self.component_object.get_capex_unit() + ']').grid(row=1, column=0,
                                                                                                sticky='w')
        entry_capex_var = ttk.Entry(newWindow, text=self.label_capex_value_str, state=status_no_scale)
        entry_capex_var.grid(row=1, column=1, sticky='w')

        unit = self.label_capex_unit_str.get().split('/')[-1]
        if unit == 'MWh':
            unit = 'MW'

        label_base_investment = ttk.Label(newWindow,
                                          text='Base investment [' + self.label_capex_unit_str.get() + ']')
        label_base_investment.grid(column=0, row=2, sticky='w')
        label_base_investment_value = ttk.Entry(newWindow,
                                                text=self.label_base_investment_value_str,
                                                state=status_scale)
        label_base_investment_value.grid(column=1, row=2, sticky='w')

        label_base_capacity = ttk.Label(newWindow, text='Base capacity [' + unit + ']')
        label_base_capacity.grid(column=0, row=3, sticky='w')
        label_base_capacity_value = ttk.Entry(newWindow, text=self.label_base_capacity_value_str, state=status_scale)
        label_base_capacity_value.grid(column=1, row=3, sticky='w')

        label_scaling_factor = ttk.Label(newWindow, text='Scaling factor')
        label_scaling_factor.grid(column=0, row=4, sticky='w')
        label_scaling_factor_value = ttk.Entry(newWindow,
                                               text=self.label_scaling_factor_value_str,
                                               state=status_scale)
        label_scaling_factor_value.grid(column=1, row=4, sticky='w')

        label_max_capacity_eoc = ttk.Label(newWindow, text='Max capacity [' + unit + ']')
        label_max_capacity_eoc.grid(column=0, row=5, sticky='w')
        label_max_capacity_eoc_value = ttk.Entry(newWindow,
                                                 text=self.label_max_capacity_eoc_value_str,
                                                 state=status_scale)
        label_max_capacity_eoc_value.grid(column=1, row=5, sticky='w')

        tk.Label(newWindow, text='Lifetime [Years]').grid(row=6, column=0, sticky='w')
        entry_lifetime = ttk.Entry(newWindow, text=self.label_lifetime_value_str)
        entry_lifetime.grid(row=6, column=1, sticky='w')

        tk.Label(newWindow, text='Maintenance [%]').grid(row=7, column=0, sticky='w')
        entry_maintenance = ttk.Entry(newWindow, text=self.label_maintenance_value_str)
        entry_maintenance.grid(row=7, column=1, sticky='w')

        tk.Label(newWindow, text='Minimal power [%]').grid(row=8, column=0, sticky='w')
        entry_min_capacity = ttk.Entry(newWindow, text=self.label_min_capacity_value_str)
        entry_min_capacity.grid(row=8, column=1, sticky='w')

        tk.Label(newWindow, text='Maximal power [%]').grid(row=9, column=0, sticky='w')
        entry_max_capacity = ttk.Entry(newWindow, text=self.label_max_capacity_value_str)
        entry_max_capacity.grid(row=9, column=1, sticky='w')

        tk.Label(newWindow, text='Ramp down [%/h]').grid(row=10, column=0, sticky='w')
        entry_ramp_down = ttk.Entry(newWindow, text=self.label_ramp_down_value_str)
        entry_ramp_down.grid(row=10, column=1, sticky='w')

        tk.Label(newWindow, text='Ramp up [%/h]').grid(row=11, column=0, sticky='w')
        entry_ramp_up = ttk.Entry(newWindow, text=self.label_ramp_up_value_str)
        entry_ramp_up.grid(row=11, column=1, sticky='w')

        tk.Checkbutton(newWindow, text='Shut down possible?',
                       variable=self.shut_down_ability_var,
                       command=activate_shut_down).grid(row=12, column=0, columnspan=2, sticky='w')

        if self.component_object.get_shut_down_ability():
            shut_down_state = NORMAL
        else:
            shut_down_state = DISABLED

        tk.Label(newWindow, text='Shut down [h]').grid(row=13, column=0, sticky='w')
        entry_shut_down = ttk.Entry(newWindow, text=self.label_shut_down_value_str, state=shut_down_state)
        entry_shut_down.grid(row=13, column=1, sticky='w')

        tk.Label(newWindow, text='Start up [h]').grid(row=14, column=0, sticky='w')
        entry_start_up = ttk.Entry(newWindow, text=self.label_start_up_value_str, state=shut_down_state)
        entry_start_up.grid(row=14, column=1, sticky='w')

        tk.Label(newWindow, text='Number of units in system').grid(row=15, column=0, sticky='w')
        entry_number_units = ttk.Entry(newWindow, text=self.label_number_parallel_units_str)
        entry_number_units.grid(row=15, column=1, sticky='w')

        button = ttk.Button(newWindow, text='Adjust values', command=get_value_and_kill_window)
        button.grid(row=16, column=0, sticky='ew')

        button = ttk.Button(newWindow, text='Cancel', command=kill_window)
        button.grid(row=16, column=1, sticky='ew')

        newWindow.mainloop()

    def set_component_parameters_to_default(self):

        # Important: Not only delete component and get copy of pm_object_original
        # because conversions should not be deleted

        component_original = self.pm_object_original.get_component(self.component)
        component_copy = self.pm_object.get_component(self.component)

        component_copy.set_scalable(component_original.is_scalable())
        component_copy.set_capex(component_original.get_capex())
        component_copy.set_base_investment(component_original.get_base_investment())
        component_copy.set_base_capacity(component_original.get_base_capacity())
        component_copy.set_economies_of_scale(component_original.get_economies_of_scale())
        component_copy.set_max_capacity_economies_of_scale(component_original.get_max_capacity_economies_of_scale())
        component_copy.set_number_parallel_units(component_original.get_number_parallel_units())

        component_copy.set_capex_unit(component_original.get_capex_unit())
        component_copy.set_lifetime(component_original.get_lifetime())
        component_copy.set_maintenance(float(component_original.get_maintenance()))
        component_copy.set_min_p(float(component_original.get_min_p()))
        component_copy.set_max_p(float(component_original.get_max_p()))
        component_copy.set_ramp_down(component_original.get_ramp_down())
        component_copy.set_ramp_up(component_original.get_ramp_up())
        component_copy.set_shut_down_ability(component_original.get_shut_down_ability())
        component_copy.set_shut_down_time(component_original.get_shut_down_time())
        component_copy.set_start_up_time(component_original.get_start_up_time())

        self.pm_object.applied_parameter_for_component = self.pm_object_original.applied_parameter_for_component

        self.parent.parent.pm_object_copy = self.pm_object
        self.parent.parent.update_widgets()

    def __init__(self, parent, root, super_frame, component, pm_object, pm_object_original):

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
        self.root = root
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

            capex_unit = self.component_object.get_capex_unit()
            lifetime = self.component_object.get_lifetime()
            maintenance = round(float(self.component_object.get_maintenance() * 100), 2)
            min_p = round(float(self.component_object.get_min_p() * 100), 2)
            max_p = round(float(self.component_object.get_max_p() * 100), 2)
            ramp_down = round(float(self.component_object.get_ramp_down() * 100), 2)
            ramp_up = round(float(self.component_object.get_ramp_up() * 100), 2)
            number_parallel_units = int(self.component_object.get_number_parallel_units())

            self.label_capex_value_str = StringVar()
            self.label_capex_unit_str = StringVar()
            self.label_capex_unit_str.set(capex_unit)

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

            self.shut_down_ability_var = BooleanVar()
            self.shut_down_ability_var.set(False)
            self.label_shut_down_value_str = StringVar()
            self.label_start_up_value_str = StringVar()

            self.label_number_parallel_units_str = StringVar()
            self.label_number_parallel_units_str.set(number_parallel_units)

            if not self.component_object.is_scalable():

                # The parameters below only exist if component is not scalable

                capex = self.component_object.get_capex()
                self.label_capex_value_str.set(capex)

                self.label_capex = ttk.Label(self.frame, text='CAPEX [' + self.label_capex_unit_str.get() + ']')
                self.label_capex.grid(column=0, row=1, sticky='w')
                self.label_capex_value = ttk.Label(self.frame, text=self.label_capex_value_str.get())
                self.label_capex_value.grid(column=1, row=1, sticky='w')

                i = 0

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

                self.label_base_investment = ttk.Label(self.frame, text='Base investment [' + self.label_capex_unit_str.get() + ']')
                self.label_base_investment.grid(column=0, row=1, sticky='w')
                self.label_base_investment_value = ttk.Label(self.frame,
                                                             text=self.label_base_investment_value_str.get())
                self.label_base_investment_value.grid(column=1, row=1, sticky='w')

                unit = self.label_capex_unit_str.get().split('/')[-1]
                if unit == 'MWh':
                    unit = 'MW'

                self.label_base_capacity = ttk.Label(self.frame, text='Base capacity [' + unit + ']')
                self.label_base_capacity.grid(column=0, row=2, sticky='w')
                self.label_base_capacity_value = ttk.Label(self.frame, text=self.label_base_capacity_value_str.get())
                self.label_base_capacity_value.grid(column=1, row=2, sticky='w')

                self.label_scaling_factor = ttk.Label(self.frame, text='Scaling factor')
                self.label_scaling_factor.grid(column=0, row=3, sticky='w')
                self.label_scaling_factor_value = ttk.Label(self.frame,
                                                            text=self.label_scaling_factor_value_str.get())
                self.label_scaling_factor_value.grid(column=1, row=3, sticky='w')

                self.label_max_capacity_eoc = ttk.Label(self.frame, text='Max capacity [' + unit + ']')
                self.label_max_capacity_eoc.grid(column=0, row=4, sticky='w')
                self.label_max_capacity_eoc_value = ttk.Label(self.frame,
                                                              text=self.label_max_capacity_eoc_value_str.get())
                self.label_max_capacity_eoc_value.grid(column=1, row=4, sticky='w')

                i = 3

            self.label_lifetime = ttk.Label(self.frame, text='Lifetime [Years]')
            self.label_lifetime.grid(column=0, row=2+i, sticky='w')
            self.label_lifetime_value = ttk.Label(self.frame, text=self.label_lifetime_value_str.get())
            self.label_lifetime_value.grid(column=1, row=2+i, sticky='w')

            self.label_maintenance = ttk.Label(self.frame, text='Maintenance [%]')
            self.label_maintenance.grid(column=0, row=3+i, sticky='w')
            self.label_maintenance_value = ttk.Label(self.frame, text=self.label_maintenance_value_str.get())
            self.label_maintenance_value.grid(column=1, row=3+i, sticky='w')

            self.label_min_capacity = ttk.Label(self.frame, text='Minimal power [%]')
            self.label_min_capacity.grid(column=0, row=4+i, sticky='w')
            self.label_min_capacity_value = ttk.Label(self.frame, text=self.label_min_capacity_value_str.get())
            self.label_min_capacity_value.grid(column=1, row=4+i, sticky='w')

            self.label_max_capacity = ttk.Label(self.frame, text='Maximal power [%]')
            self.label_max_capacity.grid(column=0, row=5+i, sticky='w')
            self.label_max_capacity_value = ttk.Label(self.frame, text=self.label_max_capacity_value_str.get())
            self.label_max_capacity_value.grid(column=1, row=5+i, sticky='w')

            self.label_ramp_down = ttk.Label(self.frame, text='Ramp down time [%/h]')
            self.label_ramp_down.grid(column=0, row=6 + i, sticky='w')
            self.label_ramp_down_value = ttk.Label(self.frame, text=self.label_ramp_down_value_str.get())
            self.label_ramp_down_value.grid(column=1, row=6 + i, sticky='w')

            self.label_ramp_up = ttk.Label(self.frame, text='Ramp up time [%/h]')
            self.label_ramp_up.grid(column=0, row=7 + i, sticky='w')
            self.label_ramp_up_value = ttk.Label(self.frame, text=self.label_ramp_up_value_str.get())
            self.label_ramp_up_value.grid(column=1, row=7 + i, sticky='w')

            j = 0

            if self.component_object.get_shut_down_ability():
                shut_down = self.component_object.get_shut_down_time()
                start_up = self.component_object.get_start_up_time()

                self.shut_down_ability_var.set(True)
                self.label_shut_down_value_str.set(shut_down)
                self.label_start_up_value_str.set(start_up)

                self.label_shut_down = ttk.Label(self.frame, text='Shut down time [h]')
                self.label_shut_down.grid(column=0, row=8 + i, sticky='w')
                self.label_shut_down_value = ttk.Label(self.frame, text=self.label_shut_down_value_str.get())
                self.label_shut_down_value.grid(column=1, row=8 + i, sticky='w')

                self.label_start_up = ttk.Label(self.frame, text='Start up time [h]')
                self.label_start_up.grid(column=0, row=9 + i, sticky='w')
                self.label_start_up_value = ttk.Label(self.frame, text=self.label_start_up_value_str.get())
                self.label_start_up_value.grid(column=1, row=9 + i, sticky='w')

                j = 2

            self.label_number_parallel_units = ttk.Label(self.frame, text='Number of units in system')
            self.label_number_parallel_units.grid(column=0, row=10 + i + j, sticky='w')
            self.label_number_parallel_units_value = ttk.Label(self.frame,
                                                               text=self.label_number_parallel_units_str.get())
            self.label_number_parallel_units_value.grid(column=1, row=10 + i + j, sticky='w')

            self.delete_component_dict = {}

            ttk.Button(self.frame, text='Adjust parameters',
                       command=self.adjust_component_value).grid(column=0, row=11+i+j, sticky=W+E)

            ttk.Button(self.frame, text='Default parameters',
                       command=self.set_component_parameters_to_default).grid(column=1, row=11+i+j, sticky=W+E)

            self.frame.grid_columnconfigure(0, weight=1)
            self.frame.grid_columnconfigure(1, weight=1)


class AddNewComponentWindow:

    def add_component_and_kill_window(self):

        # Creates component with dummy parameters and random main conversion

        random_main_conversion = pd.Series()
        random_main_conversion.loc['input_me'] = random.choice([*self.pm_object.get_all_streams().keys()])
        random_main_conversion.loc['output_me'] = random.choice([*self.pm_object.get_all_streams().keys()])
        random_main_conversion.loc['coefficient'] = 1

        new_component = ConversionComponent(self.name.get(), self.nice_name.get(),
                                            main_conversion=random_main_conversion, final_unit=True)
        self.pm_object.add_component(self.name.get(), new_component)

        self.pm_object.get_stream(random_main_conversion.loc['input_me']).set_final(True)
        self.pm_object.get_stream(random_main_conversion.loc['output_me']).set_final(True)

        for gp in self.pm_object.get_general_parameters():
            self.pm_object.set_applied_parameter_for_component(gp, self.name.get(), True)

        self.parent.pm_object_copy = self.pm_object
        self.parent.update_widgets()

        self.newWindow.destroy()

    def kill_window(self):
        self.newWindow.destroy()

    def __init__(self, parent, root, pm_object):

        """
        Window to add new component

        :param parent: Interface object - needed to access Interface functions
        :param root: Tk.root - needed to create new windows
        :param pm_object: Parameter object - needed to access and store information
        """

        self.root = root
        self.parent = parent
        self.pm_object = pm_object

        self.newWindow = Toplevel(self.root)
        self.newWindow.grab_set()

        self.nice_name = StringVar()
        self.name = StringVar()

        ttk.Label(self.newWindow, text='Nice name').grid(row=0, column=0)
        ttk.Entry(self.newWindow, text=self.nice_name).grid(row=0, column=1)
        ttk.Label(self.newWindow, text='Name').grid(row=1, column=0)
        ttk.Entry(self.newWindow, text=self.name).grid(row=1, column=1)

        ttk.Button(self.newWindow, text='Add component', command=self.add_component_and_kill_window).grid(row=2, column=0)
        ttk.Button(self.newWindow, text='Cancel', command=self.kill_window).grid(row=2, column=1)


class ConversionFrame:

    def set_component_conversions_to_default(self):

        component_original = self.pm_object_original.get_component(self.component)
        component_copy = self.pm_object.get_component(self.component)

        main_conversion = component_original.get_main_conversion()

        component_copy.set_main_conversion(main_conversion['input_me'],
                                           main_conversion['output_me'],
                                           main_conversion['coefficient'])

        side_conversion = component_copy.get_side_conversions()
        for i in side_conversion.index:
            component_copy.remove_side_conversion(side_conversion.loc[i, 'input_me'],
                                                  side_conversion.loc[i, 'output_me'])

        side_conversion = component_original.get_side_conversions()
        for i in side_conversion.index:
            input_me = side_conversion.loc[i, 'input_me']
            output_me = side_conversion.loc[i, 'output_me']
            coefficient = side_conversion.loc[i, 'coefficient']

            component_copy.add_side_conversion(input_me, output_me, coefficient)

        for stream in self.pm_object.get_specific_streams('final'):
            self.pm_object.remove_stream(stream.get_name())

        self.parent.parent.parent.pm_object_copy = self.pm_object
        self.parent.parent.parent.update_widgets()

    def add_new_conversion(self):

        new_conversion_window = ConversionWindow(self, self.root, self.pm_object, self.component,
                                                 self.conversion_type)
        new_conversion_window.create_new_window()

    def delete_conversion(self):

        def kill_window():
            newWindow.destroy()

        def check_and_remove_conversions():

            for key in checkbox_vars.keys():
                if checkbox_vars[key].get():
                    input_stream = self.conversions.loc[key, 'input_me']
                    output_stream = self.conversions.loc[key, 'output_me']

                    self.pm_object.get_component(self.component).remove_side_conversion(input_stream, output_stream)

            for stream in self.pm_object.get_specific_streams('final'):
                self.pm_object.remove_stream(stream.get_name())

            self.parent.parent.parent.pm_object_copy = self.pm_object
            self.parent.parent.parent.update_widgets()

            kill_window()

        newWindow = Toplevel(self.root)
        newWindow.grab_set()

        checkbox_vars = {}

        j = 0
        for i in self.conversions.index:

            checkbox_vars.update({i: tk.BooleanVar()})
            checkbox_vars[i].set(False)

            ttk.Checkbutton(newWindow, variable=checkbox_vars[i], onvalue=True, offvalue=False) \
                .grid(row=j, column=0)

            input_me = self.pm_object.get_nice_name(self.conversions.loc[i, 'input_me'])
            input_me_unit = self.pm_object.get_stream(self.conversions.loc[i, 'input_me']).get_unit()
            output_me = self.pm_object.get_nice_name(self.conversions.loc[i, 'output_me'])
            output_me_unit = self.pm_object.get_stream(self.conversions.loc[i, 'output_me']).get_unit()
            coefficient = round(float(self.conversions.loc[i, 'coefficient']), 2)

            top = str(coefficient) + str(' ') + str(output_me_unit) + str(' ') + str(output_me)
            bottom = str(1) + str(' ') + str(input_me_unit) + str(' ') + str(input_me)

            ttk.Label(newWindow, text=top).grid(row=j, column=1)
            ttk.Label(newWindow, text=bottom).grid(row=j + 2, column=1)

            ttk.Separator(newWindow, orient='horizontal').grid(row=j + 1, column=1, sticky='ew')

            j += 3

        ttk.Button(newWindow, text='Delete conversion', command=check_and_remove_conversions).grid(row=j + 1, column=1)
        ttk.Button(newWindow, text='Cancel', command=kill_window).grid(row=j + 1, column=0)

    def adjust_conversion(self, index):

        new_conversion_window = ConversionWindow(self, self.root, self.pm_object,
                                                 self.component, self.conversion_type, self.conversions.loc[index, :])
        new_conversion_window.create_new_window()

    def __init__(self, parent, root, super_frame, component, conversion_type, pm_object, pm_object_original):

        self.parent = parent
        self.root = root
        self.pm_object = pm_object
        self.pm_object_original = pm_object_original
        self.component = component
        self.conversion_type = conversion_type

        self.frame = ttk.Frame(super_frame)

        if self.conversion_type == 'main':
            self.conversions = self.pm_object.get_main_conversion_by_component(self.component).to_frame().transpose()
            ttk.Label(self.frame, text='Conversions [Output / Input]', font='Helvetica 12 bold').grid(row=0, column=0,
                                                                                                      columnspan=3)
        else:
            self.conversions = self.pm_object.get_side_conversions_by_component(self.component)

        j = 1
        k = j

        conversion_frame = ttk.Frame(self.frame)

        if not self.conversions.empty:
            for i in self.conversions.index:
                input_me = self.pm_object.get_nice_name(self.conversions.loc[i, 'input_me'])
                input_me_unit = self.pm_object.get_stream(self.conversions.loc[i, 'input_me']).get_unit()
                output_me = self.pm_object.get_nice_name(self.conversions.loc[i, 'output_me'])
                output_me_unit = self.pm_object.get_stream(self.conversions.loc[i, 'output_me']).get_unit()
                coefficient = round(float(self.conversions.loc[i, 'coefficient']), 2)

                top = str(coefficient) + str(' ') + str(output_me_unit) + str(' ') + str(output_me)
                bottom = str(1) + str(' ') + str(input_me_unit) + str(' ') + str(input_me)

                if self.conversion_type == 'main':
                    ttk.Label(self.frame, text='Main conversion').grid(row=j + 1, rowspan=3, column=0, sticky='w')
                else:
                    ttk.Label(self.frame, text='Side conversion').grid(row=j + 1, rowspan=3, column=0, sticky='w')

                ttk.Label(conversion_frame, text=top).pack(expand=True)
                ttk.Separator(conversion_frame, orient='horizontal').pack(fill='both', expand=True)
                ttk.Label(conversion_frame, text=bottom).pack(expand=True)

                ttk.Button(self.frame, text='Adjust conversion',
                          command=lambda i=i: self.adjust_conversion(i)).grid(row=j + 1, rowspan=3, column=2, sticky='e')

                j += 3

            conversion_frame.grid(row=k + 1, rowspan=j-k, column=1, sticky='ew')

            self.frame.grid_columnconfigure(0, weight=1)
            self.frame.grid_columnconfigure(1, weight=2)
            self.frame.grid_columnconfigure(2, weight=1)

            if self.conversion_type == 'side':
                button_frame = ttk.Frame(self.frame)

                button_frame.grid_columnconfigure(0, weight=1)
                button_frame.grid_columnconfigure(1, weight=1)
                button_frame.grid_columnconfigure(2, weight=1)

                if True:

                    ttk.Button(button_frame, text='Add conversion',
                               command=self.add_new_conversion).grid(row=0, column=0, sticky=W+E)
                    ttk.Button(button_frame, text='Delete conversion',
                               command=self.delete_conversion).grid(row=0, column=1, sticky=W+E)
                    ttk.Button(button_frame, text='Reset conversions',
                               command=self.set_component_conversions_to_default).grid(row=0, column=2, sticky=W+E)

                button_frame.grid(row=j + 1, column=0, columnspan=3, sticky=N + S + E + W)

            self.frame.grid_columnconfigure(0, weight=1)
            self.frame.grid_columnconfigure(1, weight=1)
        else:
            if self.conversion_type == 'side':
                button_frame = ttk.Frame(self.frame)

                button_frame.grid_columnconfigure(0, weight=1)
                button_frame.grid_columnconfigure(1, weight=1)
                button_frame.grid_columnconfigure(2, weight=1)

                if True:
                    ttk.Button(button_frame, text='Add conversion',
                               command=self.add_new_conversion).grid(row=0, column=0, sticky=W + E)
                    ttk.Button(button_frame, text='Delete conversion',
                               command=self.delete_conversion, state=DISABLED).grid(row=0, column=1, sticky=W + E)
                    ttk.Button(button_frame, text='Reset conversions',
                               command=self.set_component_conversions_to_default, state=DISABLED)\
                        .grid(row=0, column=2, sticky=W + E)

                button_frame.pack(fill='both', expand=True)


class ConversionWindow:

    def callbackFuncAddConversionInput(self, event):

        stream = self.combobox_existing_stream_input.get()
        self.input_unit_var.set(self.pm_object.get_stream(self.pm_object.get_abbreviation(stream)).get_unit())
        self.input_unit_label.config(text=self.input_unit_var.get())

    def change_input_entry(self):

        if self.input_radiobutton_var.get() == 'existing':
            self.combobox_existing_stream_input.config(state=NORMAL)
            self.input_unit_label.config(state=NORMAL)
            self.input_stream_name_entry.config(state=DISABLED)
            self.input_stream_abbreviation_entry.config(state=DISABLED)
            self.input_unit_entry.config(state=DISABLED)

            self.input_unit_entry_var.set('Unit')
            self.input_stream_name_entry_var.set('Nice Name')
            self.input_stream_abbreviation_entry_var.set('Abbreviation')

            self.final_input_var.set(self.combobox_existing_stream_input.get())
            self.final_input_unit_var.set(self.input_unit_var.get())
        else:
            self.combobox_existing_stream_input.config(state=DISABLED)
            self.input_unit_label.config(state=DISABLED)
            self.input_stream_name_entry.config(state=NORMAL)
            self.input_stream_abbreviation_entry.config(state=NORMAL)
            self.input_unit_entry.config(state=NORMAL)

            self.input_unit_entry_var.set('')
            self.input_stream_name_entry_var.set('')
            self.input_stream_abbreviation_entry_var.set('')

            self.final_input_var.set(self.input_stream_name_entry.get())
            self.final_input_unit_var.set(self.input_unit_entry_var.get())

    def callbackFuncAddConversionOutput(self, event):

        stream = self.combobox_existing_stream_output.get()
        self.output_unit_var.set(self.pm_object.get_stream(self.pm_object.get_abbreviation(stream)).get_unit())
        self.output_unit_label.config(text=self.output_unit_var.get())

    def change_output_entry(self):

        if self.output_radiobutton_var.get() == 'existing':
            self.combobox_existing_stream_output.config(state=NORMAL)
            self.output_unit_label.config(state=NORMAL)
            self.output_stream_name_entry.config(state=DISABLED)
            self.output_stream_abbreviation_entry.config(state=DISABLED)
            self.output_unit_entry.config(state=DISABLED)

            self.output_unit_entry_var.set('Unit')
            self.output_stream_name_entry_var.set('Nice Name')
            self.output_stream_abbreviation_entry_var.set('Abbreviation')

            self.final_output_var.set(self.combobox_existing_stream_output.get())
            self.final_output_unit_var.set(self.output_unit_var.get())
        else:
            self.combobox_existing_stream_output.config(state=DISABLED)
            self.output_unit_label.config(state=DISABLED)
            self.output_stream_name_entry.config(state=NORMAL)
            self.output_stream_abbreviation_entry.config(state=NORMAL)
            self.output_unit_entry.config(state=NORMAL)

            self.output_unit_entry_var.set('')
            self.output_stream_name_entry_var.set('')
            self.output_stream_abbreviation_entry_var.set('')

            self.final_output_var.set(self.output_stream_name_entry_var.get())
            self.final_output_unit_var.set(self.output_unit_entry_var.get())

    def check_format(self):
        right_format = False

        if self.input_radiobutton_var.get() == 'existing':
            self.final_input_var.set(self.combobox_existing_stream_input.get())
            self.final_input_unit_var.set(self.input_unit_var.get())
        else:
            self.final_input_var.set(self.input_stream_name_entry_var.get())
            self.final_input_abbreviation_var.set(self.input_stream_abbreviation_entry_var.get())
            self.final_input_unit_var.set(self.input_unit_entry_var.get())

        if self.output_radiobutton_var.get() == 'existing':
            self.final_output_var.set(self.combobox_existing_stream_output.get())
            self.final_output_unit_var.set(self.output_unit_var.get())
        else:
            self.final_output_var.set(self.output_stream_name_entry_var.get())
            self.final_output_abbreviation_var.set(self.output_stream_abbreviation_entry_var.get())
            self.final_output_unit_var.set(self.output_unit_entry_var.get())

        # Check Input
        right_type_coefficient = False
        right_type_output_unit = False
        right_type_output_name = False
        right_type_input_unit = False
        right_type_input_name = False

        try:
            float(self.coefficient_entry.get())
            right_type_coefficient = True
        except:
            pass

        try:
            float(self.final_output_unit_var.get())
        except:
            right_type_output_unit = True

        try:
            float(self.final_output_var.get())
        except:
            right_type_output_name = True

        try:
            float(self.final_input_unit_var.get())
        except:
            right_type_input_unit = True

        try:
            float(self.final_input_var.get())
        except:
            right_type_input_name = True

        if right_type_coefficient & right_type_input_unit & right_type_input_name \
                & right_type_output_name & right_type_output_unit:
            right_format = True

        return right_format

    def create_conversion(self):

        if self.check_format():

            self.top.set(str(self.coefficient_entry_var.get()) + str(' ') + str(self.final_output_unit_var.get()) + str(
                ' ') + str(self.final_output_var.get()))
            self.bottom.set(str('1') + str(' ') + str(self.final_input_unit_var.get()) + str(' ') + str(
                self.final_input_var.get()))

            ttk.Separator(self.conversion_frame, orient='horizontal').grid(row=1, sticky='ew')

            self.ok_button.config(text='Ok', state=NORMAL)
            self.ok_button.grid(row=0, column=1, sticky='ew')

            self.check_format_label.config(text='')
        else:
            self.check_format_label.config(text='Please insert the information in correct format')

    def take_values_and_kill(self):

        # Remove adjusted conversion completely
        if self.conversion is not None:
            if self.conversion_type != 'main':
                self.pm_object.get_component(self.component).remove_side_conversion(self.conversion['input_me'],
                                                                                    self.conversion['output_me'])

        input_stream_nice_name = None
        input_stream_stream_unit = None
        if self.input_radiobutton_var.get() == 'existing':
            input_stream_abbreviation = self.pm_object.get_abbreviation(self.final_input_var.get())
            input_exists = True

        else:
            input_stream_nice_name = self.final_input_var.get()
            input_stream_abbreviation = self.final_input_abbreviation_var.get()
            input_stream_stream_unit = self.final_input_unit_var.get()

            self.pm_object.set_nice_name(input_stream_abbreviation, input_stream_nice_name)
            self.pm_object.set_abbreviation(input_stream_nice_name, input_stream_abbreviation)

            input_exists = False

        output_stream_nice_name = None
        output_stream_stream_unit = None
        if self.output_radiobutton_var.get() == 'existing':
            output_stream_abbreviation = self.pm_object.get_abbreviation(self.final_output_var.get())
            output_exists = True

        else:
            output_stream_nice_name = self.final_output_var.get()
            output_stream_abbreviation = self.final_output_abbreviation_var.get()
            output_stream_stream_unit = self.final_output_unit_var.get()

            self.pm_object.set_nice_name(output_stream_abbreviation, output_stream_nice_name)
            self.pm_object.set_abbreviation(output_stream_nice_name, output_stream_abbreviation)

            output_exists = False

        coefficient = self.coefficient_entry.get()

        if self.conversion_type != 'main':
            self.pm_object.get_component(self.component).add_side_conversion(input_stream_abbreviation,
                                                                             output_stream_abbreviation, coefficient)

        else:
            self.pm_object.get_component(self.component).set_main_conversion(input_stream_abbreviation,
                                                                             output_stream_abbreviation, coefficient)
            # Change capex unit
            unit = self.pm_object.get_stream(input_stream_abbreviation).get_unit()
            if unit == 'MWh':
                unit = 'MW'
            self.pm_object.get_component(self.component).set_capex_unit('€/' + unit + ' '
                                                                        + self.pm_object.get_nice_name(input_stream_abbreviation))

        for stream in self.pm_object.get_specific_streams('final'):
            self.pm_object.remove_stream(stream.get_name())

        if input_exists | output_exists:
            for stream in self.pm_object.get_all_streams():
                stream_object = self.pm_object.get_stream(stream)
                if input_exists:
                    if stream_object.get_name() == input_stream_abbreviation:
                        stream_object.set_final(True)

                if output_exists:
                    if stream_object.get_name() == output_stream_abbreviation:
                        stream_object.set_final(True)

        if not input_exists:
            stream = Stream(input_stream_abbreviation, input_stream_nice_name, input_stream_stream_unit, final_stream=True)
            self.pm_object.add_stream(input_stream_abbreviation, stream)

        if not output_exists:
            stream = Stream(output_stream_abbreviation, output_stream_nice_name, output_stream_stream_unit, final_stream=True)
            self.pm_object.add_stream(output_stream_abbreviation, stream)

        self.parent.parent.parent.parent.pm_object_copy = self.pm_object
        self.parent.parent.parent.parent.update_widgets()

        self.newWindow.destroy()

    def kill_only(self):
        self.newWindow.destroy()

    def create_new_window(self):
        self.newWindow = Toplevel(self.root)
        self.newWindow.grab_set()

        self.conversion_frame = ttk.Frame(self.newWindow)
        button_frame = ttk.Frame(self.newWindow)

        streams_add_conversion = self.pm_object.get_all_streams()
        streams_add_conversion_nice_names = []
        for s in streams_add_conversion:
            streams_add_conversion_nice_names.append(self.pm_object.get_nice_name(s))

        tk.Label(self.newWindow, text='Input').grid(row=0, column=0, sticky='ew')

        self.input_radiobutton_var = StringVar()
        self.input_radiobutton_existing = tk.Radiobutton(self.newWindow)
        self.combobox_existing_stream_input = tk.ttk.Combobox(self.newWindow)
        self.input_unit_var = StringVar()
        self.input_unit_label = tk.Label(self.newWindow)
        self.input_radiobutton_new = tk.Radiobutton(self.newWindow)
        self.input_stream_name_entry_var = StringVar()
        self.input_stream_name_entry = Entry(self.newWindow)
        self.input_stream_abbreviation_entry_var = StringVar()
        self.input_stream_abbreviation_entry = Entry(self.newWindow)
        self.input_unit_entry_var = StringVar()
        self.input_unit_entry = Entry(self.newWindow)

        self.output_radiobutton_var = StringVar()
        self.output_radiobutton_existing = tk.Radiobutton(self.newWindow)
        self.combobox_existing_stream_output = ttk.Combobox(self.newWindow)
        self.output_unit_var = StringVar()
        self.output_unit_label = tk.Label(self.newWindow)
        self.output_radiobutton_new = tk.Radiobutton(self.newWindow)
        self.output_stream_name_entry_var = StringVar()
        self.output_stream_name_entry = Entry(self.newWindow)
        self.output_stream_abbreviation_entry_var = StringVar()
        self.output_stream_abbreviation_entry = Entry(self.newWindow)
        self.output_unit_entry_var = StringVar()
        self.output_unit_entry = Entry(self.newWindow)
        self.coefficient_entry_var = StringVar()
        self.coefficient_entry = tk.Entry(self.newWindow)
        self.check_format_label = tk.Label(self.newWindow)
        self.top = StringVar()
        self.bottom = StringVar()
        self.top_label = tk.Label(self.conversion_frame)
        self.bottom_label = tk.Label(self.conversion_frame)
        self.ok_button = ttk.Button(button_frame)

        self.input_radiobutton_var.set('existing')
        self.input_radiobutton_existing.config(text='Existing stream', variable=self.input_radiobutton_var,
                                               value='existing', command=self.change_input_entry)
        self.input_radiobutton_existing.grid(row=1, column=0, sticky='ew')
        self.combobox_existing_stream_input.config(values=streams_add_conversion_nice_names)
        self.combobox_existing_stream_input.grid(row=2, column=0, sticky='ew')
        self.combobox_existing_stream_input.bind("<<ComboboxSelected>>", self.callbackFuncAddConversionInput)

        self.input_radiobutton_new.config(text='New stream', variable=self.input_radiobutton_var, value='new',
                                          command=self.change_input_entry)
        self.input_radiobutton_new.grid(row=3, column=0, sticky='ew')
        self.input_stream_name_entry_var.set('Nice Name')
        self.input_stream_name_entry.config(text=self.input_stream_name_entry_var, state=DISABLED)
        self.input_stream_name_entry.grid(row=4, column=0, sticky='ew')
        self.input_stream_abbreviation_entry_var.set('Abbreviation')
        self.input_stream_abbreviation_entry.config(text=self.input_stream_abbreviation_entry_var,
                                                    state=DISABLED)
        self.input_stream_abbreviation_entry.grid(row=5, column=0, sticky='ew')
        self.input_unit_entry_var.set('Unit')
        self.input_unit_entry.config(text=self.input_unit_entry_var, state=DISABLED)
        self.input_unit_entry.grid(row=6, column=0, sticky='ew')

        # Initialization of output widgets
        tk.Label(self.newWindow, text='Output').grid(row=0, column=2, sticky='ew')

        self.output_radiobutton_var.set('existing')
        self.output_radiobutton_existing.config(text='Existing stream', variable=self.output_radiobutton_var,
                                                value='existing', command=self.change_output_entry)
        self.output_radiobutton_existing.grid(row=1, column=2, sticky='ew')
        self.combobox_existing_stream_output.config(values=streams_add_conversion_nice_names)
        self.combobox_existing_stream_output.grid(row=2, column=2, sticky='ew')
        self.combobox_existing_stream_output.bind("<<ComboboxSelected>>", self.callbackFuncAddConversionOutput)

        self.output_radiobutton_new.config(text='New stream', variable=self.output_radiobutton_var, value='new',
                                           command=self.change_output_entry)
        self.output_radiobutton_new.grid(row=3, column=2, sticky='ew')
        self.output_stream_name_entry_var.set('Nice Name')
        self.output_stream_name_entry.config(text=self.output_stream_name_entry_var, state=DISABLED)
        self.output_stream_name_entry.grid(row=4, column=2, sticky='ew')

        self.output_stream_abbreviation_entry_var.set('Abbreviation')
        self.output_stream_abbreviation_entry.config(text=self.output_stream_abbreviation_entry_var,
                                                     state=DISABLED)
        self.output_stream_abbreviation_entry.grid(row=5, column=2, sticky='ew')
        self.output_unit_entry_var.set('Unit')
        self.output_unit_entry.config(text=self.output_unit_entry_var, state=DISABLED)
        self.output_unit_entry.grid(row=6, column=2, sticky='ew')

        ttk.Separator(self.newWindow, orient='vertical').grid(row=0, rowspan=7, column=1, sticky='ns')

        tk.Label(self.newWindow, text='Coefficient').grid(row=7, column=0, columnspan=3, sticky='ew')
        self.coefficient_entry.config(text=self.coefficient_entry_var)
        self.coefficient_entry.grid(row=8, column=0, columnspan=3, sticky='ew')

        self.top_label.config(textvariable=self.top)
        self.top_label.grid(row=0, sticky='ew')

        self.bottom_label.config(textvariable=self.bottom)
        self.bottom_label.grid(row=2, sticky='ew')

        self.conversion_frame.grid(row=9, columnspan=3, sticky='ew')

        ttk.Button(button_frame, text='Check conversion', command=self.create_conversion).grid(row=0, column=0, sticky='ew')
        self.ok_button.config(text='Ok (Please check conversion first)',
                              command=self.take_values_and_kill, state=DISABLED)
        self.ok_button.grid(row=0, column=1, sticky='ew')
        ttk.Button(button_frame, text='Cancel', command=self.kill_only).grid(row=0, column=2, sticky='ew')

        button_frame.grid(row=10, columnspan=3, sticky='ew')

        self.newWindow.grid_columnconfigure(0, weight=1)
        self.newWindow.grid_columnconfigure(2, weight=1)

        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        button_frame.grid_columnconfigure(2, weight=1)

        self.conversion_frame.grid_columnconfigure(0, weight=1)

        if self.conversion is not None:
            input_me = self.pm_object.get_nice_name(self.conversion['input_me'])
            input_me_unit = self.pm_object.get_stream(self.conversion['input_me']).get_unit()
            output_me = self.pm_object.get_nice_name(self.conversion['output_me'])
            output_me_unit = self.pm_object.get_stream(self.conversion['output_me']).get_unit()
            coefficient = round(float(self.conversion['coefficient']), 2)

            self.combobox_existing_stream_input.set(input_me)
            self.input_unit_var.set(input_me_unit)
            self.combobox_existing_stream_output.set(output_me)
            self.output_unit_var.set(output_me_unit)
            self.coefficient_entry_var.set(coefficient)

    def __init__(self, parent, root, pm_object, component, conversion_type, conversion=None):

        self.parent = parent
        self.root = root
        self.pm_object = pm_object
        self.component = component
        self.conversion_type = conversion_type

        self.final_input_var = StringVar()
        self.final_input_abbreviation_var = StringVar()
        self.final_input_unit_var = StringVar()
        self.final_output_var = StringVar()
        self.final_output_abbreviation_var = StringVar()
        self.final_output_unit_var = StringVar()

        if conversion is not None:
            self.conversion = conversion
        else:
            self.conversion = None

