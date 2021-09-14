from gui import Interface
from _helpers_gui import SettingWindow
from os import walk
from parameter_object import ParameterObject
from optimization_classes_and_methods import OptimizationProblem
from analysis_classes_and_methods import Result
from load_projects import load_setting
import pandas as pd

setting_window = SettingWindow()

if setting_window.go_on:

    path_data = setting_window.folder_data
    path_result = setting_window.folder_result
    path_settings = setting_window.folder_settings
    solver = setting_window.solver

    if setting_window.radiobutton_variable.get() == 'new':

        interface = Interface(path_data=path_data, path_result=path_result,
                              path_settings=path_settings, solver=solver)

    elif setting_window.radiobutton_variable.get() == 'custom':

        path_custom = setting_window.selected_custom
        interface = Interface(path_data=path_data, path_result=path_result,
                              path_settings=path_settings,
                              path_custom=path_custom, solver=solver)

    elif setting_window.radiobutton_variable.get() == 'optimize_only':

        path_to_settings = setting_window.folder_optimize

        # Get path of every object in folder
        _, _, filenames = next(walk(path_to_settings))

        for file in filenames:
            file = file.split('/')[0]

            print('Currently optimized: ' + file)

            path = path_to_settings + file
            file_without_ending = file.split('.')[0]

            pm_object = ParameterObject('parameter', integer_steps=10)
            case_data = pd.read_excel(path, index_col=0)
            pm_object = load_setting(pm_object, case_data)

            optimization_problem = OptimizationProblem(pm_object, path_data=path_data, solver=solver)
            result = Result(optimization_problem, path_result, path_data, file_without_ending)







