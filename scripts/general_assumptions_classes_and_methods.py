import tkinter as tk
from tkinter import ttk
from tkinter import *
from tkinter import filedialog


class GeneralAssumptionsFrame:

    # Todo: Add personal cost factor
    def adjust_component_value(self):

        def get_value_and_kill_window():

            def wrong_format():

                wrong_format_window = Toplevel(self.root)
                wrong_format_window.grab_set()

                tk.Label(wrong_format_window, text='Please only use numbers and use dots as separators').pack()
                tk.Button(wrong_format_window, text='Ok', command=wrong_format_window.destroy).pack()

            for gp in self.pm_object.get_general_parameters():
                try:
                    if gp != 'covered_period':
                        self.pm_object.set_general_parameter_value(gp, float(self.label_dict[gp].get()) / 100)
                        self.label_dict[gp].set(round(float(self.label_dict[gp].get()), 2))
                    else:
                        self.pm_object.set_general_parameter_value(gp, int(self.label_dict[gp].get()))
                        self.label_dict[gp].set(int((self.label_dict[gp].get())))
                except:
                    wrong_format()

            self.parent.parent.pm_object_copy = self.pm_object
            self.parent.parent.update_widgets()

            newWindow.destroy()

        def kill_window():
            newWindow.destroy()

        # Toplevel object which will
        # be treated as a new window
        newWindow = Toplevel(self.root)
        newWindow.grid_columnconfigure(0, weight=1)
        newWindow.grid_columnconfigure(1, weight=1)
        newWindow.grab_set()

        # sets the title of the
        # Toplevel widget
        newWindow.title('Adjust component values')

        entries = {}

        i = 0
        for c in self.pm_object.get_general_parameters():
            if c != 'covered_period':
                tk.Label(newWindow, text=self.pm_object.get_nice_name(c) + ' [%]').grid(row=i, column=0, sticky='w')
                ttk.Entry(newWindow, text=self.label_dict[c]).grid(row=i, column=1, sticky='ew')
            else:
                tk.Label(newWindow, text=self.pm_object.get_nice_name(c) + ' [h]').grid(row=i, column=0, sticky='w')
                ttk.Entry(newWindow, text=self.label_dict[c]).grid(row=i, column=1, sticky='ew')
            i += 1

        button = ttk.Button(newWindow, text='Adjust values', command=get_value_and_kill_window)
        button.grid(row=i, column=0, sticky='ew')
        button = ttk.Button(newWindow, text='Cancel', command=kill_window)
        button.grid(row=i, column=1, sticky='ew')

        newWindow.mainloop()

    def initiate_frame(self):

        self.ga_label_parameter = ttk.Label(self.frame, text='Parameter', font='Helvetica 10 bold').grid(column=0,
                                                                                                         row=0,
                                                                                                         sticky='w')
        self.ga_label_value = ttk.Label(self.frame, text='Value', font='Helvetica 10 bold').grid(column=1, row=0,
                                                                                                 sticky='w')

        i = 1
        for c in self.pm_object.get_general_parameters():
            self.label_dict.update({c: StringVar()})
            if c != 'covered_period':
                self.label_dict[c].set(round(float(self.pm_object.get_general_parameter_value(c)) * 100, 2))
                ttk.Label(self.frame, text=self.pm_object.get_nice_name(c) + ' [%]').grid(column=0, row=i, sticky='w')
                ttk.Label(self.frame, text=self.label_dict[c].get()).grid(column=1, row=i, sticky='w')
            else:
                self.label_dict[c].set(int(self.pm_object.get_general_parameter_value(c)))
                ttk.Label(self.frame, text=self.pm_object.get_nice_name(c) + ' [h]').grid(column=0, row=i, sticky='w')
                ttk.Label(self.frame, text=self.label_dict[c].get()).grid(column=1, row=i, sticky='w')

            i += 1

        button_frame = ttk.Frame(self.frame)

        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)

        self.adjust_values_button = ttk.Button(button_frame, text='Adjust parameters',
                                               command=self.adjust_component_value)
        self.adjust_values_button.grid(column=0, row=0, sticky='ew')

        self.default_values_ga_button = ttk.Button(button_frame, text='Reset parameters',
                                                   command=self.parent.set_general_assumptions_to_default)
        self.default_values_ga_button.grid(column=1, row=0, sticky='ew')

        button_frame.grid(row=i, column=0, columnspan=2, sticky='ew')

    def __init__(self, parent, root, pm_object):

        self.parent = parent
        self.root = root
        self.pm_object = pm_object

        self.label_dict = {}

        self.ga_label_parameter = ttk.Label()
        self.ga_label_value = ttk.Label()
        self.ga_button = ttk.Label()

        self.adjust_values_button = ttk.Button()
        self.default_values_ga_button = ttk.Button()

        self.frame = tk.Frame(self.parent.sub_frame)
        self.initiate_frame()
        self.frame.pack(fill="both", expand=True)
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_columnconfigure(1, weight=1)
