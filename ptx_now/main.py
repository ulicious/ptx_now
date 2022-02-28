from gui import Interface, save_current_parameters_and_options
from _helpers_gui import SettingWindow
from os import walk
from parameter_object import ParameterObject
from optimization_classes_and_methods import OptimizationProblem
from analysis_classes_and_methods import Result
from load_projects import load_setting
import pandas as pd
from _helpers_visualization import create_visualization


setting_window = SettingWindow()

if setting_window.go_on:

    path_data = setting_window.path_data
    path_result = setting_window.path_result
    path_projects = setting_window.path_projects
    path_optimize = setting_window.path_optimize
    solver = setting_window.solver
    path_visualization = setting_window.path_visualization

    if setting_window.optimize_or_visualize_projects_variable.get() == 'optimize':

        if setting_window.optimize_variable.get() == 'new':

            interface = Interface(path_data=path_data, path_result=path_result,
                                  path_projects=path_projects, solver=solver)

        elif setting_window.optimize_variable.get() == 'custom':
            interface = Interface(path_data=path_data, path_result=path_result,
                                  path_projects=path_projects,
                                  path_optimize=path_optimize, solver=solver)

        else:
            path_to_settings = setting_window.path_projects + setting_window.path_optimize

            # Get path of every object in folder
            _, _, filenames = next(walk(path_to_settings))

            for file in filenames:
                file = file.split('/')[0]

                print('Currently optimized: ' + file)

                path = path_to_settings + '/' + file
                file_without_ending = file.split('.')[0]

                pm_object = ParameterObject('parameter', integer_steps=10)
                case_data = pd.read_excel(path, index_col=0)
                pm_object = load_setting(pm_object, case_data)
                pm_object.set_project_name(file_without_ending)

                optimization_problem = OptimizationProblem(pm_object, path_data=path_data, solver=solver)
                result = Result(optimization_problem, path_result)
                save_current_parameters_and_options(pm_object, result.new_result_folder + '/7_settings.xlsx')

    else:

        path_visualization = path_result + path_visualization + '/'
        create_visualization(path_visualization)








