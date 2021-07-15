import tkinter as tk
from tkinter import ttk
from tkinter import *
from tkinter import filedialog

from objects_formulation import StorageComponent


class StreamFrame:

    def adjust_values(self):
        AdjustStreamWindow(self, self.root, self.pm_object, self.stream)

    def set_stream_settings_to_default(self):

        self.pm_object.remove_stream_entirely(self.stream_object.get_name())

        stream_original = self.pm_object_original.get_stream(self.stream)
        self.pm_object.add_stream(self.stream, stream_original.__copy__())

        self.parent.parent.pm_object_copy = self.pm_object
        self.parent.parent.update_widgets()

    def create_widgets_in_frame(self):
        for child_parameters in self.frame.winfo_children():
            child_parameters.destroy()

        self.initialize_stream()
        max_columns = 1

        i = 0

        tk.Label(self.frame, text='Stream freely available?').grid(row=i, column=0, sticky='w')
        if self.available_var.get():
            text_dummy = 'Yes'
        else:
            text_dummy = 'No'
        tk.Label(self.frame, text=text_dummy).grid(row=i, column=1)

        i += 1

        tk.Label(self.frame, text='Stream purchasable?').grid(row=i, column=0, sticky='w')
        if self.purchasable_var.get():
            text_dummy = 'Yes'
            tk.Label(self.frame, text=text_dummy).grid(row=i, column=1)

            if self.stream_object.get_purchase_price() == '':
                if self.purchase_price_type_var.get() == 'fixed':
                    text_purchase_price = 'Please enter fix purchase price'
                else:
                    text_purchase_price = 'Please choose purchase price curve'

                text_purchase_price_unit = ''
            else:
                text_purchase_price = self.stream_object.get_purchase_price()
                text_purchase_price_unit = '€ / ' + self.stream_object.get_unit()

            tk.Label(self.frame, text='Purchase price type:').grid(row=i+1, column=0, sticky='w')
            if self.purchase_price_type_var.get() == 'fixed':
                tk.Label(self.frame, text='Fixed price').grid(row=i+1, column=1)
                tk.Label(self.frame, text='Purchase price:').grid(row=i+1, column=2)
                tk.Label(self.frame, text=text_purchase_price).grid(row=i+1, column=3)
                tk.Label(self.frame, text=text_purchase_price_unit).grid(row=i+1, column=4)
                max_columns = max(max_columns, 4)
            else:
                tk.Label(self.frame, text='Variable price').grid(row=i+1, column=1)
                tk.Label(self.frame, text='For price time series see:').grid(row=i+1, column=2)
                tk.Label(self.frame, text=text_purchase_price).grid(row=i+1, column=3)
                max_columns = max(max_columns, 3)

            i += 2
        else:
            text_dummy = 'No'
            tk.Label(self.frame, text=text_dummy).grid(row=i, column=1)

            i += 1

        tk.Label(self.frame, text='Excess stream emitted?').grid(row=i, column=0, sticky='w')
        if self.emitted_var.get():
            text_dummy = 'Yes'
        else:
            text_dummy = 'No'
        tk.Label(self.frame, text=text_dummy).grid(row=i, column=1)
        i += 1

        tk.Label(self.frame, text='Stream saleable?').grid(row=i, column=0, sticky='w')
        if self.saleable_var.get():
            text_dummy = 'Yes'
            tk.Label(self.frame, text=text_dummy).grid(row=i, column=1)

            if self.stream_object.get_sale_price() == '':
                if self.sale_price_type_var.get() == 'fixed':
                    text_sale_price = 'Please enter fix selling price'
                else:
                    text_sale_price = 'Please choose selling price curve'

                text_sale_price_unit = ''
            else:
                text_sale_price = self.stream_object.get_sale_price()
                text_sale_price_unit = '€ / ' + self.stream_object.get_unit()

            tk.Label(self.frame, text='Sale price type:').grid(row=i+1, column=0, sticky='w')
            if self.sale_price_type_var.get() == 'fixed':
                tk.Label(self.frame, text='Fixed price').grid(row=i+1, column=1)
                tk.Label(self.frame, text='Sale price:').grid(row=i+1, column=2)
                tk.Label(self.frame, text=text_sale_price).grid(row=i+1, column=3)
                tk.Label(self.frame, text=text_sale_price_unit).grid(row=i+1, column=4)
                max_columns = max(max_columns,4)
            else:
                tk.Label(self.frame, text='Variable price').grid(row=i+1, column=1)
                tk.Label(self.frame, text='For price time series see:').grid(row=i+1, column=2)
                tk.Label(self.frame, text=text_sale_price).grid(row=i+1, column=3)
                max_columns = max(max_columns, 3)

            i += 2
        else:
            text_dummy = 'No'
            tk.Label(self.frame, text=text_dummy).grid(row=i, column=1)

            i += 1

        tk.Label(self.frame, text='Stream demanded?').grid(row=i, column=0, sticky='w')
        if self.demand_var.get():
            text_dummy = 'Yes'
            tk.Label(self.frame, text=text_dummy).grid(row=i, column=1)
            if not self.total_demand_var.get():
                tk.Label(self.frame, text='Hourly demand:').grid(row=i+1, column=0, sticky='w')
                tk.Label(self.frame, text=self.demand_text_var.get()).grid(row=i+1, column=1)
                tk.Label(self.frame, text=self.stream_object.get_unit()).grid(row=i+1, column=2)
                max_columns = max(max_columns, 2)
            else:
                tk.Label(self.frame, text='Total demand:').grid(row=i+1, column=0, sticky='w')
                tk.Label(self.frame, text=self.demand_text_var.get()).grid(row=i+1, column=1)
                tk.Label(self.frame, text=self.stream_object.get_unit()).grid(row=i+1, column=2)
                max_columns = max(max_columns, 2)

            i += 2
        else:
            text_dummy = 'No'
            tk.Label(self.frame, text=text_dummy).grid(row=i, column=1)

            i += 1

        tk.Label(self.frame, text='Stream storable?').grid(row=i, column=0, sticky='w')
        if self.storable_var.get():
            tk.Label(self.frame, text='Yes').grid(row=i, column=1)
        else:
            tk.Label(self.frame, text='No').grid(row=i, column=1)

        i += 1

        button_frame = ttk.Frame(self.frame)
        ttk.Button(button_frame, text='Adjust setting', command=self.adjust_values)\
            .grid(row=0, column=0, sticky='ew')
        ttk.Button(button_frame, text='Reset setting', command=self.set_stream_settings_to_default)\
            .grid(row=0, column=1, sticky='ew')
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        button_frame.grid(row=i, column=0, columnspan=max_columns+1, sticky='ew')

        for i in range(max_columns + 1):
            self.frame.grid_columnconfigure(i, weight=1)

    def initialize_stream(self):

        if self.stream_object.is_available():
            self.available_var.set(True)
        else:
            self.available_var.set(False)

        if self.stream_object.is_purchasable():
            self.purchasable_var.set(True)
            self.purchase_price_type_var.set(self.stream_object.get_purchase_price_type())

            if self.stream_object.get_purchase_price_type() == 'fixed':
                self.purchase_price_fixed_text_var.set(self.stream_object.get_purchase_price())
                self.purchase_price_curve_text_var.set('')
            else:
                path = self.stream_object.get_purchase_price()
                file_name = path.split('/')[-1]

                self.purchase_price_fixed_text_var.set('')
                self.purchase_price_curve_text_var.set(file_name)
        else:
            self.purchasable_var.set(False)
            self.purchase_price_type_var.set(self.stream_object.get_purchase_price_type())

        if self.stream_object.is_emittable():
            self.emitted_var.set(True)
        else:
            self.emitted_var.set(False)

        if self.stream_object.is_saleable():
            self.saleable_var.set(True)
            if self.stream_object.get_sale_price_type() == 'fixed':
                self.sale_price_type_var.set('fixed')
                self.sale_price_fixed_text_var.set(self.stream_object.get_sale_price())
                self.sale_price_curve_text_var.set('')
            else:
                self.sale_price_type_var.set('variable')

                path = self.stream_object.get_sale_price()
                file_name = path.split('/')[-1]

                self.sale_price_fixed_text_var.set('')
                self.sale_price_curve_text_var.set(file_name)

        else:
            self.saleable_var.set(False)
            self.sale_price_type_var.set('fixed')

        if self.stream_object.is_demanded():
            self.demand_var.set(True)
        else:
            self.demand_var.set(False)

        if self.stream_object.is_total_demand():
            self.total_demand_var.set(True)
        else:
            self.total_demand_var.set(False)

        if self.stream_object.is_storable():
            self.storable_var.set(True)
        else:
            self.storable_var.set(False)

        self.demand_text_var.set(self.stream_object.get_demand())

    def __init__(self, parent, root, stream, pm_object, pm_object_original):

        self.parent = parent
        self.root = root
        self.frame = tk.Frame(self.parent.sub_frame)
        self.pm_object = pm_object
        self.pm_object_original = pm_object_original
        self.stream = self.pm_object.get_abbreviation(stream)
        self.stream_object = self.pm_object.get_stream(self.stream)

        self.streams_nice_names = []

        self.available_var = tk.BooleanVar()

        self.emitted_var = tk.BooleanVar()

        self.purchasable_var = tk.BooleanVar()
        self.purchase_price_type_var = tk.StringVar()
        self.purchase_price_fixed_text_var = tk.StringVar()
        self.purchase_price_curve_text_var = tk.StringVar()

        self.saleable_var = tk.BooleanVar()
        self.sale_price_type_var = tk.StringVar()
        self.sale_price_fixed_text_var = tk.StringVar()
        self.sale_price_curve_text_var = tk.StringVar()

        self.demand_var = tk.BooleanVar()
        self.total_demand_var = tk.BooleanVar()
        self.demand_text_var = StringVar()

        self.storable_var = tk.BooleanVar()

        self.create_widgets_in_frame()


class AdjustStreamWindow:

    def create_widgets_in_frame(self):

        self.initialize_stream()

        basic_setting_frame = ttk.Frame(self.newWindow)

        ttk.Checkbutton(basic_setting_frame, text='Freely available', variable=self.available_var, onvalue=True,
                        offvalue=False).grid(row=0, column=0, sticky='ew')
        ttk.Checkbutton(basic_setting_frame, text='Emitted', variable=self.emitted_var, onvalue=True,
                        offvalue=False).grid(row=0, column=1, sticky='ew')
        ttk.Checkbutton(basic_setting_frame, text='Stream storable', variable=self.storable_var, onvalue=True,
                        offvalue=False).grid(row=0, column=2, sticky='ew')

        basic_setting_frame.grid_columnconfigure(0, weight=1)
        basic_setting_frame.grid_columnconfigure(1, weight=1)
        basic_setting_frame.grid_columnconfigure(2, weight=1)

        basic_setting_frame.grid(row=0, columnspan=3, sticky='ew')

        ttk.Separator(self.newWindow).grid(row=1, columnspan=3, sticky='ew')

        ttk.Checkbutton(self.newWindow, text='Purchasable', variable=self.purchasable_var, onvalue=True, offvalue=False,
                       command=self.configure_purchasable_streams) \
            .grid(row=2, column=0, rowspan=3, sticky='w')

        self.purchase_fixed_price_radiobutton.config(text='Fixed price [€ / ' + self.stream_object.get_unit() + ']',
                                                     variable=self.purchase_price_type_var, value='fixed',
                                                     command=self.set_purchase_fixed_price)
        self.purchase_fixed_price_radiobutton.grid(row=2, column=1, sticky='w')

        self.purchase_price_curve_radiobutton.config(text='Price curve',
                                                     variable=self.purchase_price_type_var, value='variable',
                                                     command=self.set_purchase_fixed_price)
        self.purchase_price_curve_radiobutton.grid(row=3, rowspan=2, column=1, sticky='w')

        self.purchase_fixed_price_entry.config(text=self.purchase_price_fixed_text_var)
        self.purchase_fixed_price_entry.grid(row=2, column=2, sticky='ew')

        self.purchase_price_button.config(text='Choose purchase price curve',
                                          command=self.choose_purchase_price_curve)
        self.purchase_price_button.grid(row=3, column=2, sticky='ew')

        self.purchase_curve_label.config(text=self.purchase_price_curve_text_var.get())
        self.purchase_curve_label.grid(row=4, column=2, sticky='w')

        ttk.Separator(self.newWindow).grid(row=5, columnspan=3, sticky='ew')

        ttk.Checkbutton(self.newWindow, text='Saleable', variable=self.saleable_var,
                        onvalue=True, offvalue=False, command=self.configure_saleable_streams) \
            .grid(row=6, column=0, rowspan=3, sticky='w')

        self.sale_fixed_price_radiobutton.config(text='Fixed price [€ / ' + self.stream_object.get_unit() + ']',
                                                 variable=self.sale_price_type_var, value='fixed',
                                                 command=self.set_sell_fixed_price)
        self.sale_fixed_price_radiobutton.grid(row=6, column=1, sticky='w')

        self.sale_price_curve_radiobutton.config(text='Price curve',
                                                 variable=self.sale_price_type_var,
                                                 value='variable',
                                                 command=self.set_sell_fixed_price)
        self.sale_price_curve_radiobutton.grid(row=7, column=1, rowspan=2, sticky='w')

        self.sale_fixed_price_entry.config(text=self.sale_price_fixed_text_var)
        self.sale_fixed_price_entry.grid(row=6, column=2, sticky='ew')

        self.sale_price_button.config(text='Choose selling price curve',
                                      command=self.choose_sell_price_curve)
        self.sale_price_button.grid(row=7, column=2, sticky='ew')

        self.sale_curve_label.config(text=self.sale_price_curve_text_var.get())
        self.sale_curve_label.grid(row=8, column=2, sticky='w')

        ttk.Separator(self.newWindow).grid(row=9, columnspan=3, sticky='ew')

        ttk.Checkbutton(self.newWindow, text='Demand [' + self.stream_object.get_unit() + ' / h]',
                       variable=self.demand_var, onvalue=True,
                       offvalue=False, command=self.configure_demand_streams) \
            .grid(row=10, column=0, sticky='w')

        self.demand_entry.config(text=self.demand_text_var)
        self.demand_entry.grid(row=10, column=1, sticky='ew')

        self.demand_total_demand_button.config(text='Cumulated Demand', variable=self.total_demand_var,
                                               onvalue=True, offvalue=False)
        self.demand_total_demand_button.grid(row=10, column=2, sticky='w')

        button_frame = ttk.Frame(self.newWindow)
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)

        ttk.Button(button_frame, text='Ok', command=self.safe_values)\
            .grid(row=0, column=0, sticky='ew')
        ttk.Button(button_frame, text='Cancel', command=self.kill_only) \
            .grid(row=0, column=1, sticky='ew')

        button_frame.grid(row=11, columnspan=3, sticky='ew')

        self.configure_purchasable_streams()
        self.configure_saleable_streams()
        self.configure_demand_streams()

    def initialize_stream(self):

        if self.stream_object.is_available():
            self.available_var.set(True)
        else:
            self.available_var.set(False)

        if self.stream_object.is_purchasable():
            self.purchasable_var.set(True)
            self.purchase_price_type_var.set(self.stream_object.get_purchase_price_type())

            if self.stream_object.get_purchase_price_type() == 'fixed':
                self.purchase_price_fixed_text_var.set(self.stream_object.get_purchase_price())
                self.purchase_price_curve_text_var.set('')
            else:
                path = self.stream_object.get_purchase_price()
                file_name = path.split('/')[-1]

                self.purchase_price_fixed_text_var.set('')
                self.purchase_price_curve_text_var.set(file_name)
        else:
            self.purchasable_var.set(False)
            self.purchase_price_type_var.set(self.stream_object.get_purchase_price_type())

        if self.stream_object.is_emittable():
            self.emitted_var.set(True)
        else:
            self.emitted_var.set(False)

        if self.stream_object.is_saleable():
            self.saleable_var.set(True)
            if self.stream_object.get_sale_price_type() == 'fixed':
                self.sale_price_type_var.set('fixed')
                self.sale_price_fixed_text_var.set(self.stream_object.get_sale_price())
                self.sale_price_curve_text_var.set('')
            else:
                self.sale_price_type_var.set('variable')

                path = self.stream_object.get_sale_price()
                file_name = path.split('/')[-1]

                self.sale_price_fixed_text_var.set('')
                self.sale_price_curve_text_var.set(file_name)

        else:
            self.saleable_var.set(False)
            self.sale_price_type_var.set('fixed')

        if self.stream_object.is_demanded():
            self.demand_var.set(True)
        else:
            self.demand_var.set(False)

        if self.stream_object.is_total_demand():
            self.total_demand_var.set(True)
        else:
            self.total_demand_var.set(False)

        if self.stream_object.is_storable():
            self.storable_var.set(True)
        else:
            self.storable_var.set(False)

        self.demand_text_var.set(self.stream_object.get_demand())

    def configure_purchasable_streams(self):
        if self.purchasable_var.get():
            self.purchase_fixed_price_radiobutton.config(state=NORMAL)
            self.purchase_price_curve_radiobutton.config(state=NORMAL)
            self.purchase_fixed_price_entry.config(state=NORMAL)
            self.purchase_price_button.config(state=NORMAL)
            self.purchase_curve_label.config(state=NORMAL)

        else:
            self.purchase_fixed_price_radiobutton.config(state=DISABLED)
            self.purchase_price_curve_radiobutton.config(state=DISABLED)
            self.purchase_fixed_price_entry.config(state=DISABLED)
            self.purchase_price_button.config(state=DISABLED)
            self.purchase_curve_label.config(state=DISABLED)

        self.set_purchase_fixed_price()

    def set_purchase_fixed_price(self):
        if not self.purchasable_var.get():
            self.purchase_fixed_price_radiobutton.config(state=DISABLED)
            self.purchase_price_curve_radiobutton.config(state=DISABLED)
            self.purchase_fixed_price_entry.config(state=DISABLED)
            self.purchase_price_button.config(state=DISABLED)
            self.purchase_curve_label.config(state=DISABLED)
        else:
            if self.purchase_price_type_var.get() == 'fixed':
                self.purchase_fixed_price_entry.config(state=NORMAL)
                self.purchase_price_button.config(state=DISABLED)
                self.purchase_curve_label.config(state=DISABLED)
            else:
                self.purchase_price_button.config(state=NORMAL)
                self.purchase_curve_label.config(state=NORMAL)
                self.purchase_fixed_price_entry.config(state=DISABLED)

    def choose_purchase_price_curve(self):
        folder_selected = filedialog.askopenfilename()
        file_name = folder_selected.split('/')[-1]
        self.purchase_price_curve_text_var.set(file_name)

    def configure_saleable_streams(self):
        if self.saleable_var.get():
            self.sale_fixed_price_radiobutton.config(state=NORMAL)
            self.sale_price_curve_radiobutton.config(state=NORMAL)
            self.sale_fixed_price_entry.config(state=NORMAL)
            self.sale_price_button.config(state=NORMAL)
            self.sale_curve_label.config(state=NORMAL)
        else:
            self.sale_fixed_price_radiobutton.config(state=DISABLED)
            self.sale_price_curve_radiobutton.config(state=DISABLED)
            self.sale_fixed_price_entry.config(state=DISABLED)
            self.sale_price_button.config(state=DISABLED)
            self.sale_curve_label.config(state=DISABLED)

        self.set_sell_fixed_price()

    def set_sell_fixed_price(self):
        if not self.saleable_var.get():
            self.sale_fixed_price_radiobutton.config(state=DISABLED)
            self.sale_price_curve_radiobutton.config(state=DISABLED)
            self.sale_fixed_price_entry.config(state=DISABLED)
            self.sale_price_button.config(state=DISABLED)
            self.sale_curve_label.config(state=DISABLED)
        else:
            if self.sale_price_type_var.get() == 'fixed':
                self.sale_fixed_price_entry.config(state=NORMAL)
                self.sale_price_button.config(state=DISABLED)
                self.sale_curve_label.config(state=DISABLED)
            else:
                self.sale_price_button.config(state=NORMAL)
                self.sale_curve_label.config(state=NORMAL)
                self.sale_fixed_price_entry.config(state=DISABLED)

    def choose_sell_price_curve(self):
        folder_selected = filedialog.askopenfilename()
        file_name = folder_selected.split('/')[-1]
        self.sale_price_curve_text_var.set(file_name)

    def configure_demand_streams(self):

        if self.demand_var.get():
            self.demand_entry.config(state=NORMAL)
            self.demand_total_demand_button.config(state=NORMAL)
        else:
            self.demand_entry.config(state=DISABLED)
            self.total_demand_var.set(False)
            self.demand_total_demand_button.config(state=DISABLED)

    def kill_only(self):
        self.newWindow.destroy()

    def safe_values(self):

        # Set availability settings
        if self.available_var.get():
            self.stream_object.set_available(True)
        else:
            self.stream_object.set_available(False)

        # Set purchase settings
        if self.purchasable_var.get():
            self.stream_object.set_purchasable(True)

            if self.purchase_price_type_var.get() == 'fixed':
                self.stream_object.set_purchase_price_type('fixed')
            else:
                self.stream_object.set_purchase_price_type('variable')
                self.stream_object.set_purchase_price(self.purchase_price_curve_text_var.get())
        else:
            self.stream_object.set_purchasable(False)

        # Set emittable settings
        if self.emitted_var.get():
            self.stream_object.set_emittable(True)
        else:
            self.stream_object.set_emittable(False)

        # Set selling settings
        if self.saleable_var.get():
            self.stream_object.set_saleable(True)
            if self.sale_price_type_var.get() == 'fixed':
                self.stream_object.set_sale_price_type('fixed')
            else:
                self.stream_object.set_sale_price_type('variable')
                self.stream_object.set_sale_price(self.sale_price_curve_text_var.get())
        else:
            self.stream_object.set_saleable(False)

        # Set demand settings
        if self.demand_var.get():
            self.stream_object.set_demanded(True)
            self.stream_object.set_demand(self.demand_entry.get())
        else:
            self.stream_object.set_demanded(False)

        # Set total demand settings
        if self.total_demand_var.get():
            self.stream_object.set_total_demand(True)
        else:
            self.stream_object.set_total_demand(False)

        # Set storage settings
        # Check if storage object exits but is not set
        exists = False
        storages = self.pm_object.get_specific_components(component_type='storage')
        for c in storages:
            if c.get_name() == self.stream_object.get_name():
                exists = True

        if self.storable_var.get():
            self.stream_object.set_storable(True)

            if exists:
                storage = self.pm_object.get_component(self.stream_object.get_name())
                storage.set_final(True)
            else:
                storage = StorageComponent(self.stream_object.get_name(), self.stream_object.get_nice_name(),
                                           final_unit=True)
                self.pm_object.add_component(self.stream_object.get_name(), storage)

                for p in self.pm_object.get_general_parameters():
                    self.pm_object.set_applied_parameter_for_component(p, self.stream_object.get_name(), True)

        else:
            self.stream_object.set_storable(False)
            if exists:
                self.pm_object.get_component(self.stream).set_final(False)

        if self.purchasable_var.get():
            if self.purchase_price_type_var.get() == 'fixed':
                self.stream_object.set_purchase_price(self.purchase_fixed_price_entry.get())
            else:
                self.stream_object.set_purchase_price(self.purchase_price_curve_text_var.get())

        if self.saleable_var.get():
            if self.sale_price_type_var.get() == 'fixed':
                self.stream_object.set_sale_price(self.sale_fixed_price_entry.get())
            else:
                self.stream_object.set_sale_price(self.sale_price_curve_text_var.get())

        self.parent.parent.parent.pm_object_copy = self.pm_object
        self.parent.parent.parent.update_widgets()

        self.newWindow.destroy()

    def __init__(self, parent, root, pm_object, stream):

        self.parent = parent
        self.pm_object = pm_object
        self.root = root
        self.stream = stream
        self.stream_object = self.pm_object.get_stream(self.stream)

        self.newWindow = Toplevel(self.root)
        self.newWindow.grab_set()

        self.purchasable_var = tk.BooleanVar()
        self.purchase_price_type_var = tk.StringVar()
        self.purchase_price_fixed_text_var = tk.StringVar()
        self.purchase_price_curve_text_var = tk.StringVar()

        self.saleable_var = tk.BooleanVar()
        self.sale_price_type_var = tk.StringVar()
        self.sale_price_fixed_text_var = tk.StringVar()
        self.sale_price_curve_text_var = tk.StringVar()

        self.available_var = tk.BooleanVar()
        self.emitted_var = tk.BooleanVar()
        self.demand_var = tk.BooleanVar()
        self.total_demand_var = tk.BooleanVar()
        self.storable_var = tk.BooleanVar()

        self.demand_text_var = StringVar()
        self.initial_purchase_price_var = StringVar()

        self.purchase_fixed_price_radiobutton = ttk.Radiobutton(self.newWindow)
        self.purchase_fixed_price_entry = ttk.Entry(self.newWindow)
        self.purchase_price_curve_radiobutton = ttk.Radiobutton(self.newWindow)
        self.purchase_price_button = ttk.Button(self.newWindow)
        self.purchase_curve_label = ttk.Label(self.newWindow)

        self.sale_fixed_price_radiobutton = ttk.Radiobutton(self.newWindow)
        self.sale_fixed_price_entry = ttk.Entry(self.newWindow)
        self.sale_price_curve_radiobutton = ttk.Radiobutton(self.newWindow)
        self.sale_price_button = ttk.Button(self.newWindow)
        self.sale_curve_label = ttk.Label(self.newWindow)

        self.demand_entry = ttk.Entry(self.newWindow)
        self.demand_total_demand_button = ttk.Checkbutton(self.newWindow)

        self.create_widgets_in_frame()
