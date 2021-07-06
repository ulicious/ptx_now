import tkinter as tk
from tkinter import ttk
from tkinter import *
from tkinter import filedialog


class GeneratorFrame:

    def activate_entry(self):

        if self.checkbox_var.get():

            self.capex_label.config(state=NORMAL)
            self.lifetime_label.config(state=NORMAL)
            self.maintenance_label.config(state=NORMAL)
            self.set_profile_button.config(state=NORMAL)
            self.adjust_values_button.config(state=NORMAL)
            self.profile_label.config(state=NORMAL)
            self.generated_stream_label.config(state=NORMAL)

            self.pm_object.get_component(self.generator).set_final(True)

        else:

            self.capex_label.config(state=DISABLED)
            self.lifetime_label.config(state=DISABLED)
            self.maintenance_label.config(state=DISABLED)
            self.set_profile_button.config(state=DISABLED)
            self.adjust_values_button.config(state=DISABLED)
            self.profile_label.config(state=DISABLED)
            self.generated_stream_label.config(state=DISABLED)

            self.pm_object.get_component(self.generator).set_final(False)

        self.parent.parent.pm_object_copy = self.pm_object
        self.parent.parent.update_widgets()

    def adjust_values(self):

        def get_values_and_kill_window():
            generator = self.pm_object.get_component(self.generator)
            if capex_entry.get() != '':
                generator.set_capex(capex_entry.get())
            if lifetime_entry.get() != '':
                generator.set_lifetime(lifetime_entry.get())
            if maintenance_entry.get() != '':
                generator.set_maintenance(float(maintenance_entry.get()) / 100)

            generator.set_generated_stream(self.pm_object.get_abbreviation(generated_stream_cb.get()))

            self.parent.parent.pm_object_copy = self.pm_object
            self.parent.parent.update_widgets()

            window.destroy()

        window = Toplevel(self.root)
        window.grid_columnconfigure(0, weight=1)
        window.grid_columnconfigure(2, weight=1)

        tk.Label(window, text='CAPEX in €/MW').grid(row=0, column=0, sticky='w')
        tk.Label(window, text='Lifetime in years').grid(row=1, column=0, sticky='w')
        tk.Label(window, text='Maintenance in %').grid(row=2, column=0, sticky='w')
        tk.Label(window, text='Generated stream').grid(row=3, column=0, sticky='w')

        capex_entry = tk.Entry(window, text=self.capex)
        capex_entry.grid(row=0, column=1, sticky='ew')
        lifetime_entry = tk.Entry(window, text=self.lifetime)
        lifetime_entry.grid(row=1, column=1, sticky='ew')
        maintenance_entry = tk.Entry(window, text=self.maintenance)
        maintenance_entry.grid(row=2, column=1, sticky='ew')

        streams = []
        for stream in self.pm_object.get_specific_streams('final'):
            streams.append(stream.get_nice_name())

        generated_stream_cb = ttk.Combobox(window, values=streams)
        generated_stream_cb.grid(row=3, column=1, sticky='ew')
        generated_stream_cb.set(self.generated_stream.get())

        ttk.Button(window, text='Adjust values', command=get_values_and_kill_window).grid(row=4, columnspan=2,
                                                                                          sticky='ew')

    def set_profile_generation(self):
        path = filedialog.askopenfilename()
        file_name = path.split('/')[-1]

        if file_name.split('.')[-1] == 'xlsx':
            self.textvar_profile.set(file_name)
            self.pm_object.get_component(self.generator).set_generation_data(file_name)

            self.parent.parent.pm_object_copy = self.pm_object
            self.parent.parent.update_widgets()

        else:
            window_wrong_file = Tk()
            frame_wrong_file = Frame(window_wrong_file)
            frame_wrong_file.pack()

            tk.Label(frame_wrong_file, text='File is not xlsx format').pack()

            def kill_window():
                window_wrong_file.destroy()

            tk.Button(frame_wrong_file, text='OK', command=kill_window).pack()

    def set_generator_settings_to_default(self):

        self.pm_object.remove_component_entirely(self.generator)

        generator_original = self.pm_object_original.get_component(self.generator)
        self.pm_object.add_component(self.generator, generator_original.__copy__())

        self.parent.parent.pm_object_copy = self.pm_object
        self.parent.parent.update_widgets()

    def __init__(self, parent, root, generator, pm_object, pm_object_original):

        self.parent = parent
        self.root = root
        self.pm_object = pm_object
        self.pm_object_original = pm_object_original
        self.generator = generator

        self.frame = tk.Frame(self.parent.sub_frame)
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_columnconfigure(1, weight=1)

        generator_object = self.pm_object.get_component(self.generator)
        generated_stream = self.pm_object.get_nice_name(generator_object.get_generated_stream())
        stream_unit = self.pm_object.get_stream(generator_object.get_generated_stream()).get_unit()

        if stream_unit == 'MWh':
            stream_unit = 'MW'
        else:
            stream_unit = stream_unit * ' / h'

        tk.Label(self.frame, text='Parameter', font='Helvetica 10 bold').grid(row=1, column=0, sticky='w')
        tk.Label(self.frame, text='Value', font='Helvetica 10 bold').grid(row=1, column=1, sticky='w')
        tk.Label(self.frame, text='CAPEX [€/' + stream_unit + ']').grid(row=2, column=0, sticky='w')
        tk.Label(self.frame, text='Lifetime [Years]').grid(row=3, column=0, sticky='w')
        tk.Label(self.frame, text='Maintenance [%]').grid(row=4, column=0, sticky='w')
        tk.Label(self.frame, text='Generated stream').grid(row=5, column=0, sticky='w')
        tk.Label(self.frame, text='Profile file').grid(row=6, column=0, sticky='w')

        self.textvar_profile = StringVar()
        self.checkbox_var = BooleanVar()

        self.capex = StringVar()
        self.capex.set(generator_object.get_capex())
        self.lifetime = StringVar()
        self.lifetime.set(generator_object.get_lifetime())
        self.maintenance = StringVar()
        self.maintenance.set(round(float(generator_object.get_maintenance()) * 100, 2))
        self.generated_stream = StringVar()
        self.generated_stream.set(generated_stream)

        if generator_object in self.pm_object.get_specific_components('final', 'generator'):
            state = NORMAL
            self.checkbox_var.set(True)
        else:
            state = DISABLED
            self.checkbox_var.set(False)

        self.checkbox = ttk.Checkbutton(self.frame, text='Generator available', onvalue=True,
                                        offvalue=False, variable=self.checkbox_var, command=self.activate_entry)
        self.checkbox.grid(row=0, columnspan=2, sticky='w')

        self.capex_label = ttk.Label(self.frame, text=self.capex.get(), state=state)
        self.capex_label.grid(row=2, column=1, sticky='w')

        self.lifetime_label = tk.Label(self.frame, text=self.lifetime.get(), state=state)
        self.lifetime_label.grid(row=3, column=1, sticky='w')

        self.maintenance_label = tk.Label(self.frame, text=self.maintenance.get(), state=state)
        self.maintenance_label.grid(row=4, column=1, sticky='w')

        self.generated_stream_label = ttk.Label(self.frame, text=self.generated_stream.get(), state=state)
        self.generated_stream_label.grid(row=5, column=1, sticky='w')

        try:
            path = generator_object.get_generation_data()
            file_name = path.split('/')[-1]
            self.textvar_profile.set(file_name)
        except:
            self.textvar_profile.set('')

        self.profile_label = ttk.Label(self.frame, text=self.textvar_profile.get(), state=state)
        self.profile_label.grid(row=6, column=1, sticky='w')

        button_frame = ttk.Frame(self.frame)
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        button_frame.grid_columnconfigure(2, weight=1)

        if True:

            self.adjust_values_button = ttk.Button(button_frame, text='Adjust values', command=self.adjust_values,
                                                   state=state)
            self.adjust_values_button.grid(row=0, column=0, sticky='ew')

            self.set_profile_button = ttk.Button(button_frame, text='Set profile', command=self.set_profile_generation,
                                                 state=state)
            self.set_profile_button.grid(row=0, column=1, sticky='ew')

            self.default_generators_button = ttk.Button(button_frame, text='Default values',
                                                   command=self.set_generator_settings_to_default)
            self.default_generators_button.grid(row=0, column=2, sticky='ew')

        button_frame.grid(row=7, columnspan=2, sticky='ew')
