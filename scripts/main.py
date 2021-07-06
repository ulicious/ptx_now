from gui import Interface
from _helpers_gui import SettingWindow
from os import walk
from objects_formulation import ParameterObject
from optimization_classes_and_methods import OptimizationProblem
from analysis_classes_and_methods import Result

setting_window = SettingWindow()

if setting_window.go_on:

    path_data = setting_window.folder_data.replace('/', '\\')
    path_result = setting_window.folder_result.replace('/', '\\')
    path_settings = setting_window.folder_settings.replace('/', '\\')

    if setting_window.radiobutton_variable.get() == 'new':

        interface = Interface(path_data=path_data, path_result=path_result,
                              path_settings=path_settings)

    elif setting_window.radiobutton_variable.get() == 'custom':

        path_custom = setting_window.selected_custom.replace('/', '\\')
        interface = Interface(path_data=path_data, path_result=path_result,
                              path_settings=path_settings,
                              path_custom=path_custom)

    elif setting_window.radiobutton_variable.get() == 'optimize_only':

        path_to_settings = setting_window.folder_optimize.replace('/', '\\')

        # Get path of every object in folder
        _, _, filenames = next(walk(path_to_settings))

        for file in filenames:
            file = file.split('/')[0]
            path = path_to_settings + file
            file_without_ending = file.split('.')[0]

            pm_object = ParameterObject('parameter2', path_custom=path, integer_steps=10)

            optimization_problem = OptimizationProblem(pm_object, path_data=path_data)
            result = Result(optimization_problem, path_result, file_without_ending)







