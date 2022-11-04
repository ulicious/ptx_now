import tkinter as tk
from tkinter import ttk
from tkinter import *
from tkinter import filedialog


class GeneralAssumptionsFrame:

    def adjust_component_value(self):

        def get_value_and_kill_window():

            def wrong_format():

                wrong_format_window = Toplevel(self.frame)
                wrong_format_window.title('')
                wrong_format_window.grab_set()

                tk.Label(wrong_format_window, text='Please only use numbers and use dots as separators').pack()
                tk.Button(wrong_format_window, text='Ok', command=wrong_format_window.destroy).pack()

            self.pm_object.set_wacc(wacc.get() / 100)

            self.pm_object.set_uses_representative_periods(representative_periods.get())

            if rb_variable.get() == 'representative_periods':
                self.pm_object.set_uses_representative_periods(True)
                self.pm_object.set_representative_periods_length(int(period_length.get()))
            else:
                self.pm_object.set_uses_representative_periods(False)
                self.pm_object.set_covered_period(int(covered_period.get()))

            self.pm_object.set_monetary_unit(monetary_unit.get())

            self.parent.pm_object_copy = self.pm_object
            self.parent.update_widgets()

            newWindow.destroy()

        def kill_window():
            newWindow.destroy()

        def change_rb():
            if rb_variable.get() == 'covered_period':
                label_covered_period.config(state=NORMAL)
                entry_covered_period.config(state=NORMAL)

                label_period_length.config(state=DISABLED)
                entry_period_length.config(state=DISABLED)
            else:
                label_covered_period.config(state=DISABLED)
                entry_covered_period.config(state=DISABLED)

                label_period_length.config(state=NORMAL)
                entry_period_length.config(state=NORMAL)

        # Toplevel object which will
        # be treated as a new window
        newWindow = Toplevel(self.frame)
        newWindow.title('Adjust Parameter')
        newWindow.grid_columnconfigure(0, weight=1, uniform='a')
        newWindow.grid_columnconfigure(1, weight=1, uniform='a')
        newWindow.grab_set()

        i = 0

        wacc = DoubleVar()
        wacc.set(round(self.pm_object.get_wacc()*100, 2))

        representative_periods = BooleanVar()
        representative_periods.set(self.pm_object.get_uses_representative_periods())

        period_length = IntVar()
        period_length.set(int(self.pm_object.get_representative_periods_length()))

        rb_variable = StringVar()

        if representative_periods.get():
            state_repr_weeks = NORMAL
            state_covered_period = DISABLED
            rb_variable.set('representative_periods')
        else:
            state_repr_weeks = DISABLED
            state_covered_period = NORMAL
            rb_variable.set('covered_period')

        label_period_length = ttk.Label(newWindow, text='WACC [%]')
        label_period_length.grid(column=0, row=i, sticky='w')
        entry_period_length = ttk.Entry(newWindow, text=wacc)
        entry_period_length.grid(column=1, row=i, sticky='w')

        i += 1

        ttk.Radiobutton(newWindow, text='Use Representative Periods?', variable=rb_variable,
                        value='representative_periods', command=change_rb).grid(column=0, row=i, sticky='w')

        label_period_length = ttk.Label(newWindow, text='Representative Periods Length [h]', state=state_repr_weeks)
        label_period_length.grid(column=0, row=i + 1, sticky='w')
        entry_period_length = ttk.Entry(newWindow, text=period_length, state=state_repr_weeks)
        entry_period_length.grid(column=1, row=i + 1, sticky='w')

        i += 2

        covered_period = IntVar()
        covered_period.set(int(self.pm_object.get_covered_period()))

        ttk.Radiobutton(newWindow, text='Use Full Time Series?', variable=rb_variable,
                        value='covered_period', command=change_rb).grid(column=0, row=i, sticky='w')

        label_covered_period = ttk.Label(newWindow, text=' Covered Period [h]', state=state_covered_period)
        label_covered_period.grid(column=0, row=i+1, sticky='w')
        entry_covered_period = ttk.Entry(newWindow, text=covered_period, state=state_covered_period)
        entry_covered_period.grid(column=1, row=i+1, sticky='w')

        i += 2

        monetary_unit = StringVar()
        monetary_unit.set(self.pm_object.get_monetary_unit())
        ttk.Label(newWindow, text='Monetary Unit').grid(column=0, row=i, sticky='w')
        ttk.Entry(newWindow, text=monetary_unit).grid(column=1, row=i, sticky='w')

        i += 1

        button = ttk.Button(newWindow, text='Adjust values', command=get_value_and_kill_window)
        button.grid(row=i, column=0, sticky='ew')
        button = ttk.Button(newWindow, text='Cancel', command=kill_window)
        button.grid(row=i, column=1, sticky='ew')

        newWindow.mainloop()

    def initiate_frame(self):

        i = 0
        ttk.Label(self.frame, text='WACC [%]').grid(column=0, row=i, sticky='w')
        ttk.Label(self.frame, text=round(self.pm_object.get_wacc() * 100, 2)).grid(column=1, row=i, sticky='w')

        i += 1

        if self.pm_object.get_uses_representative_periods():

            ttk.Label(self.frame, text='Representative Periods used').grid(columnspan=2, row=i, sticky='w')
            ttk.Label(self.frame, text='Representative Periods Length [h]').grid(column=0, row=i+1, sticky='w')
            ttk.Label(self.frame, text=int(self.pm_object.get_representative_periods_length())).grid(column=1,
                                                                                                     row=i+1,
                                                                                                     sticky='w')

            i += 2
        else:
            ttk.Label(self.frame, text='Continuous Time Series used').grid(columnspan=2, row=i, sticky='w')
            ttk.Label(self.frame, text='Covered Period [h]').grid(column=0, row=i+1, sticky='w')
            ttk.Label(self.frame, text=int(self.pm_object.get_covered_period())).grid(column=1, row=i+1, sticky='w')

            i += 2

        ttk.Label(self.frame, text='Monetary Unit').grid(column=0, row=i, sticky='w')
        ttk.Label(self.frame, text=self.pm_object.get_monetary_unit()).grid(column=1, row=i, sticky='w')

        i += 1

        button_frame = ttk.Frame(self.frame)

        button_frame.grid_columnconfigure(0, weight=1, uniform="a")

        self.adjust_values_button = ttk.Button(button_frame, text='Adjust Parameters',
                                               command=self.adjust_component_value)
        self.adjust_values_button.grid(row=0, column=0, sticky='ew')

        button_frame.grid(row=i, column=0, columnspan=2, sticky='ew')

    def __init__(self, interface, parent, frame, pm_object):

        self.interface = interface
        self.parent = parent
        self.frame = ttk.Frame(frame)
        self.pm_object = pm_object

        self.label_dict = {}

        self.adjust_values_button = ttk.Button()
        self.default_values_ga_button = ttk.Button()

        self.initiate_frame()
        self.frame.pack(fill="both", expand=True)
        self.frame.grid_columnconfigure(0, weight=1, uniform='a')
        self.frame.grid_columnconfigure(1, weight=1, uniform='a')
