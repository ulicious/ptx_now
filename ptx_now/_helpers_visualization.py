import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output

import plotly.graph_objects as go
import plotly.express as px

import pandas as pd

from itertools import cycle

import webbrowser
from threading import Timer

import os
import numpy as np

import plotly.figure_factory as ff


def create_visualization(path):

    def check_visualization_type():

        if '0_assumptions.xlsx' in os.listdir(path=path):
            visualization_type_str = 'single_results'

        else:
            # Check structure of folder
            if len([f for f in os.listdir(path=path + '/' + os.listdir(path=path)[0]) if
                    os.path.isdir(path + '/' + os.listdir(path=path)[0] + '/' + f)]) > 0:
                visualization_type_str = 'multiple_results_with_different_scenarios'

            else:
                visualization_type_str = 'multiple_results_with_single_scenario'

        return visualization_type_str

    def load_data_single_result():
        assumptions_file = pd.read_excel(path + '0_assumptions.xlsx', index_col=0)
        overview_file = pd.read_excel(path + '1_results_overview.xlsx', index_col=0)
        components_file = pd.read_excel(path + '2_components.xlsx', index_col=0)
        cost_distribution_file = pd.read_excel(path + '3_cost_distribution.xlsx', index_col=0)

        try:
            commodities_file = pd.read_excel(path + '4_commodities.xlsx', index_col=0)
            time_series_file = pd.read_excel(path + '5_time_series_commodities.xlsx', index_col=(0, 1, 2))
        except:
            commodities_file = pd.read_excel(path + '4_streams.xlsx', index_col=0)
            time_series_file = pd.read_excel(path + '5_time_series_streams.xlsx', index_col=(0, 1, 2))

        generation_file = pd.read_excel(path + '6_generation.xlsx', index_col=0)
        settings_file = pd.read_excel(path + '7_settings.xlsx', index_col=0).fillna('')

        return assumptions_file, overview_file, components_file, cost_distribution_file, \
            commodities_file, time_series_file, generation_file, settings_file

    def load_data_multiple_results_with_single_scenario():
        assumptions_dict = {}
        results_overview_dict = {}
        components_dict = {}
        cost_distribution_dict = {}
        commodities_dict = {}
        time_series_dict = {}
        generation_dict = {}
        settings_dict = {}
        generation_profiles_dict = {}

        folders_list = []
        # This is the case when all results are based on same setting
        for folder in os.listdir(path=path):
            folders_list.append(folder)
            assumptions_dict[folder] = pd.read_excel(path + '\\' + folder + '\\' + '0_assumptions.xlsx',
                                                     index_col=0).fillna('')
            results_overview_dict[folder] = pd.read_excel(path + '\\' + folder + '\\' + '1_results_overview.xlsx',
                                                          index_col=0).fillna('')
            components_dict[folder] = pd.read_excel(path + '\\' + folder + '\\' + '2_components.xlsx',
                                                    index_col=0).fillna('')
            cost_distribution_dict[folder] = pd.read_excel(path + '\\' + folder + '\\' + '3_cost_distribution.xlsx',
                                                           index_col=0).fillna('')
            try:
                commodities_dict[folder] = pd.read_excel(path + '\\' + folder + '\\' + '4_commodities.xlsx',
                                                     index_col=0).fillna('')
                time_series_dict[folder] = pd.read_excel(path + '\\' + folder + '\\' + '5_time_series_commodities.xlsx',
                                                         index_col=[0, 1, 2]).fillna('')
            except:
                commodities_dict[folder] = pd.read_excel(path + '\\' + folder + '\\' + '4_streams.xlsx',
                                                         index_col=0).fillna('')
                time_series_dict[folder] = pd.read_excel(path + '\\' + folder + '\\' + '5_time_series_streams.xlsx',
                                                         index_col=[0, 1, 2]).fillna('')

            generation_dict[folder] = pd.read_excel(path + '\\' + folder + '\\' + '6_generation.xlsx',
                                                    index_col=0).fillna('')
            settings_dict[folder] = pd.read_excel(path + '\\' + folder + '\\' + '7_settings.xlsx',
                                                  index_col=0).fillna('')
            generation_profiles_dict[folder] = pd.read_excel(
                path + '\\' + folder + '\\' + '8_generation_profile.xlsx',
                index_col=0).fillna('')

        return folders_list, assumptions_dict, results_overview_dict, components_dict, \
            cost_distribution_dict, commodities_dict, time_series_dict, generation_dict, settings_dict, \
            generation_profiles_dict

    def load_data_multiple_results_with_different_scenarios():
        assumptions_dict = {}
        results_overview_dict = {}
        components_dict = {}
        cost_distribution_dict = {}
        commodities_dict = {}
        time_series_dict = {}
        generation_dict = {}
        settings_dict = {}
        generation_profiles_dict = {}

        folders_list = []
        for f1 in os.listdir(path=path):

            assumptions_dict[f1] = {}
            results_overview_dict[f1] = {}
            components_dict[f1] = {}
            cost_distribution_dict[f1] = {}
            commodities_dict[f1] = {}
            time_series_dict[f1] = {}
            generation_dict[f1] = {}
            settings_dict[f1] = {}
            generation_profiles_dict[f1] = {}

            for f2 in os.listdir(path=path + '\\' + f1):
                folders_list.append((f1, f2))
                assumptions_dict[f1][f2] = pd.read_excel(
                    path + '\\' + f1 + '\\' + f2 + '\\' + '0_assumptions.xlsx',
                    index_col=0).fillna('')

                results_overview_dict[f1][f2] = pd.read_excel(
                    path + '\\' + f1 + '\\' + f2 + '\\' + '1_results_overview.xlsx',
                    index_col=0).fillna('')

                components_dict[f1][f2] = pd.read_excel(
                    path + '\\' + f1 + '\\' + f2 + '\\' + '2_components.xlsx',
                    index_col=0).fillna('')

                cost_distribution_dict[f1][f2] = pd.read_excel(
                    path + '\\' + f1 + '\\' + f2 + '\\' + '3_cost_distribution.xlsx',
                    index_col=0).fillna('')

                try:
                    commodities_dict[f1][f2] = pd.read_excel(path + '\\' + f1 + '\\' + f2 + '\\' + '4_commodities.xlsx',
                                                         index_col=0).fillna('')
                    time_series_dict[f1][f2] = pd.read_excel(
                        path + '\\' + f1 + '\\' + f2 + '\\' + '5_time_series_commodities.xlsx',
                        index_col=[0, 1, 2]).fillna('')
                except:
                    commodities_dict[f1][f2] = pd.read_excel(path + '\\' + f1 + '\\' + f2 + '\\' + '4_streams.xlsx',
                                                             index_col=0).fillna('')
                    time_series_dict[f1][f2] = pd.read_excel(
                        path + '\\' + f1 + '\\' + f2 + '\\' + '5_time_series_streams.xlsx',
                        index_col=[0, 1, 2]).fillna('')

                generation_dict[f1][f2] = pd.read_excel(path + '\\' + f1 + '\\' + f2 + '\\' + '6_generation.xlsx',
                                                        index_col=0).fillna('')
                settings_dict[f1][f2] = pd.read_excel(path + '\\' + f1 + '\\' + f2 + '\\' + '7_settings.xlsx',
                                                      index_col=0).fillna('')
                generation_profiles_dict[f1][f2] = pd.read_excel(
                    path + '\\' + f1 + '\\' + f2 + '\\' + '8_generation_profile.xlsx',
                    index_col=0).fillna('')

        return folders_list, assumptions_dict, results_overview_dict, components_dict, \
            cost_distribution_dict, commodities_dict, time_series_dict, generation_dict, settings_dict, \
            generation_profiles_dict

    def extract_data_single_results():

        def create_overview_table():

            total_investment = "%.2f" % overview_df.loc['Total Investment'].values[0]
            total_fix_costs = "%.2f" % overview_df.loc['Total Fix Costs'].values[0]
            total_variable_costs = "%.2f" % overview_df.loc['Total Variable Costs'].values[0]
            annual_costs = "%.2f" % overview_df.loc['Annual Costs'].values[0]
            cost_per_unit = "%.2f" % overview_df.loc['Production Costs per Unit'].values[0]
            efficiency = "%.2f" % (overview_df.loc['Efficiency'].values[0] * 100)

            # Table Overview
            tab_overview = pd.DataFrame({
                '': ('Annual production', 'Total investment', 'Total Fix Costs', 'Total Variable Costs',
                     'Annual costs', 'Production cost per unit', 'Efficiency'),
                'Value':
                    (str(round(annual_production)) + " " + annual_production_unit,
                     str(total_investment) + " " + monetary_unit,
                     str(total_fix_costs) + " " + monetary_unit,
                     str(total_variable_costs) + " " + monetary_unit,
                     str(annual_costs) + " " + monetary_unit,
                     str(cost_per_unit) + " " + monetary_unit + " /" + monetary_unit,
                     str(efficiency) + ' %')})

            return tab_overview

        def create_conversion_components_table():
            # Create table which contains information on the different components

            component_list = []
            capacity = []
            capacity_unit = []
            CAPEX = []
            total_investment = []
            annuity = []
            maintenance = []
            taxes_and_insurance = []
            personnel_costs = []
            overhead = []
            working_capital = []
            full_load_hours = []

            for component in components_df.index:

                # only consider conversion components
                if components_df.loc[component, 'Capacity Basis'] == 'input':
                    component_list.append(component)

                    capacity.append("%.3f" % components_df.loc[component, 'Capacity [input]'])
                    capacity_unit.append(components_df.loc[component, 'Capacity Unit [input]'])
                    CAPEX.append("%.2f" % components_df.loc[component, 'Investment [per input]'])
                elif components_df.loc[component, 'Capacity Basis'] == 'output':
                    component_list.append(component)
                    capacity.append("%.3f" % components_df.loc[component, 'Capacity [output]'])
                    capacity_unit.append(components_df.loc[component, 'Capacity Unit [output]'])
                    CAPEX.append("%.2f" % components_df.loc[component, 'Investment [per output]'])
                else:
                    # All non-conversion components have no Capacity Basis
                    continue

                total_investment.append("%.2f" % components_df.loc[component, 'Total Investment'])
                annuity.append("%.2f" % components_df.loc[component, 'Annuity'])
                maintenance.append("%.2f" % components_df.loc[component, 'Maintenance'])
                taxes_and_insurance.append("%.2f" % components_df.loc[component, 'Taxes and Insurance'])
                personnel_costs.append("%.2f" % components_df.loc[component, 'Personnel'])
                overhead.append("%.2f" % components_df.loc[component, 'Overhead'])
                working_capital.append("%.2f" % components_df.loc[component, 'Working Capital'])
                full_load_hours.append("%.2f" % components_df.loc[component, 'Full-load Hours'])

            conversion_components_tab = pd.DataFrame({'': component_list,
                                                      'Capacity': capacity,
                                                      'Capacity Unit': capacity_unit,
                                                      'Capex': CAPEX,
                                                      'Total Investment': total_investment,
                                                      'Annuity': annuity,
                                                      'Maintenance': maintenance,
                                                      'Personnel': personnel_costs,
                                                      'Overhead': overhead,
                                                      'Working Capital': working_capital,
                                                      'Full-load Hours': full_load_hours})

            return conversion_components_tab

        def create_cost_structure_graph():
            # Cost structure

            bar_list = []
            bar_share_list = []
            matter_of_expense = []
            value_absolute = []
            value_absolute_unit = []
            value_relative = []
            value_relative_list_unit = []
            for i in cost_distribution_df.index:

                matter_of_expense.append(i)

                value = cost_distribution_df.loc[i, 'Per Output']
                p_dict = {'name': i, 'width': [0.4], 'x': [''], 'y': [value]}
                value_absolute_unit.append("%.2f" % value + ' ' + monetary_unit + ' /' + annual_production_unit)
                value_absolute.append(value)
                if i != 'Total':
                    bar_list.append(go.Bar(p_dict))

                value = cost_distribution_df.loc[i, '%']
                p_share_dict = {'name': i, 'width': [0.4], 'x': [''], 'y': [value * 100]}
                value_relative_list_unit.append("%.2f" % (value * 100) + ' %')
                value_relative.append(value * 100)
                if i != 'Total':
                    bar_share_list.append(go.Bar(p_share_dict))

            cost_structure_df_with_unit = pd.DataFrame()
            cost_structure_df_with_unit['Matter of Expense'] = matter_of_expense
            cost_structure_df_with_unit['Absolute'] = value_absolute_unit
            cost_structure_df_with_unit['Relative'] = value_relative_list_unit

            cost_structure_df = pd.DataFrame()
            cost_structure_df['Matter of Expense'] = matter_of_expense
            cost_structure_df['Absolute'] = value_absolute
            cost_structure_df['Relative'] = value_relative

            layout = go.Layout(title='Bar Chart', yaxis=dict(ticksuffix=' %'), barmode='stack',
                               colorway=px.colors.qualitative.Pastel)

            cost_fig = go.Figure(data=bar_list, layout=layout)

            cost_share_fig = px.pie(cost_structure_df[cost_structure_df['Matter of Expense'] != 'Total'],
                                    values='Relative', names='Matter of Expense')

            return cost_fig, cost_share_fig, cost_structure_df_with_unit

        def create_assumptions_table():
            columns = ['Maintenance', 'Taxes and Insurance', 'Personnel', 'Overhead', 'Working Capital']
            assumptions_tab = pd.DataFrame(index=assumptions_df.index)
            assumptions_tab[''] = assumptions_df.index
            assumptions_tab['Capex Unit'] = assumptions_df['Capex Unit']

            for i in assumptions_df.index:

                assumptions_tab.loc[i, 'Capex'] = "%.2f" % assumptions_df.loc[i, 'Capex']

                for c in columns:
                    assumptions_tab.loc[i, c] = "%.2f" % (assumptions_df.loc[i, c] * 100) + ' %'

            assumptions_tab['Lifetime'] = assumptions_df['Lifetime']

            return assumptions_tab

        def create_generation_table():
            generation_tab = pd.DataFrame(index=generation_df.index)
            for i in generation_df.index:
                generation_tab.loc[i, 'Generator'] = i
                generation_tab.loc[i, 'Generated Stream'] = generation_df.loc[i, 'Generated Stream']
                generation_tab.loc[i, 'Capacity'] = "%.2f" % generation_df.loc[i, 'Capacity']
                generation_tab.loc[i, 'Investment'] = "%.2f" % generation_df.loc[i, 'Investment']
                generation_tab.loc[i, 'Annuity'] = "%.2f" % generation_df.loc[i, 'Annuity']
                generation_tab.loc[i, 'Maintenance'] = "%.2f" % generation_df.loc[i, 'Maintenance']
                generation_tab.loc[i, 'T&I'] = "%.2f" % generation_df.loc[i, 'Taxes and Insurance']
                generation_tab.loc[i, 'Overhead'] = "%.2f" % generation_df.loc[i, 'Overhead']
                generation_tab.loc[i, 'Personnel'] = "%.2f" % generation_df.loc[i, 'Personnel']
                generation_tab.loc[i, 'Potential Generation'] = "%.0f" % generation_df.loc[i, 'Potential Generation']
                generation_tab.loc[i, 'Potential FLH'] = "%.2f" % generation_df.loc[i, 'Potential Full-load Hours']
                generation_tab.loc[i, 'LCOE pre Curtailment'] = "%.4f" % generation_df.loc[i, 'LCOE before Curtailment']
                generation_tab.loc[i, 'Actual Generation'] = "%.0f" % generation_df.loc[i, 'Actual Generation']
                generation_tab.loc[i, 'Actual FLH'] = "%.2f" % generation_df.loc[i, 'Actual Full-load Hours']
                generation_tab.loc[i, 'Curtailment'] = "%.0f" % generation_df.loc[i, 'Curtailment']
                generation_tab.loc[i, 'LCOE post Curtailment'] = "%.4f" % generation_df.loc[i, 'LCOE after Curtailment']

            return generation_tab

        def create_storage_table():
            # Create table which contains information on the different components

            component_list = []
            capacity = []
            capacity_unit = []
            CAPEX = []
            total_investment = []
            annuity = []
            maintenance = []
            taxes_and_insurance = []
            personnel_costs = []
            overhead = []
            working_capital = []
            for component in components_df.index:

                if component in generation_df.index:
                    continue

                # only consider conversion components
                if not (components_df.loc[component, 'Capacity Basis'] == 'input'
                        or components_df.loc[component, 'Capacity Basis'] == 'output'):
                    component_list.append(component)

                    capacity.append("%.3f" % components_df.loc[component, 'Capacity [input]'])
                    capacity_unit.append(components_df.loc[component, 'Capacity Unit [input]'])
                    CAPEX.append("%.2f" % components_df.loc[component, 'Investment [per input]'])

                    total_investment.append("%.2f" % components_df.loc[component, 'Total Investment'])
                    annuity.append("%.2f" % components_df.loc[component, 'Annuity'])
                    maintenance.append("%.2f" % components_df.loc[component, 'Maintenance'])
                    taxes_and_insurance.append("%.2f" % components_df.loc[component, 'Taxes and Insurance'])
                    personnel_costs.append("%.2f" % components_df.loc[component, 'Personnel'])
                    overhead.append("%.2f" % components_df.loc[component, 'Overhead'])
                    working_capital.append("%.2f" % components_df.loc[component, 'Working Capital'])

            storage_components_tab = pd.DataFrame({'': component_list,
                                                   'Capacity': capacity,
                                                   'Capacity Unit': capacity_unit,
                                                   'Capex': CAPEX,
                                                   'Total Investment': total_investment,
                                                   'Annuity': annuity,
                                                   'Maintenance': maintenance,
                                                   'Personnel': personnel_costs,
                                                   'Overhead': overhead,
                                                   'Working Capital': working_capital})

            return storage_components_tab

        def create_commodity_table():
            commodity_tab = pd.DataFrame(index=commodities_df.index)

            for i in commodity_tab.index:

                commodity_tab.loc[i, 'Commodity'] = i
                commodity_tab.loc[i, 'Unit'] = commodities_df.loc[i, 'unit']
                commodity_tab.loc[i, 'Freely Available'] = "%.0f" % commodities_df.loc[i, 'Available Stream']
                commodity_tab.loc[i, 'Purchased'] = "%.0f" % commodities_df.loc[i, 'Purchased Stream']
                commodity_tab.loc[i, 'Sold'] = "%.0f" % commodities_df.loc[i, 'Sold Stream']
                commodity_tab.loc[i, 'Generated'] = "%.0f" % commodities_df.loc[i, 'Generated Stream']
                commodity_tab.loc[i, 'Stored'] = "%.0f" % commodities_df.loc[i, 'Stored Stream']
                commodity_tab.loc[i, 'From Conversion'] = "%.0f" % commodities_df.loc[i, 'Conversed Stream']
                commodity_tab.loc[i, 'Total Fixed Costs'] = "%.2f" % commodities_df.loc[i, 'Total Fix Costs'] \
                                                            + monetary_unit
                commodity_tab.loc[i, 'Total Variable Costs'] = "%.2f" % commodities_df.loc[i, 'Total Variable Costs'] \
                                                               + monetary_unit
                commodity_tab.loc[i, 'Intrinsic Costs per Unit'] = "%.2f" % commodities_df.loc[
                    i, 'Total Costs per Unit'] \
                                                                   + monetary_unit + '/' + commodities_df.loc[
                                                                       i, 'unit']
                commodity_tab.loc[i, 'Costs from other Streams per Unit'] = "%.2f" % (
                            commodities_df.loc[i, 'Production Costs per Unit']
                            - commodities_df.loc[i, 'Total Costs per Unit']) + ' ' + monetary_unit + '/' + \
                                                                            commodities_df.loc[i, 'unit']
                commodity_tab.loc[i, 'Total Costs per Unit'] = "%.2f" % commodities_df.loc[
                    i, 'Production Costs per Unit'] + ' ' \
                                                               + monetary_unit + '/' + commodities_df.loc[i, 'unit']

            return commodity_tab

        assumptions_tab = create_assumptions_table()
        assumptions_tab_columns = assumptions_tab.columns[1:]

        monetary_unit = settings_df.loc[settings_df[settings_df['type'] == 'monetary_unit'].index, 'monetary_unit'].values[0]

        create_assumptions_table()

        annual_production = overview_df.loc['Annual Production'].values[0]
        annual_production_unit = time_series_df.loc[['Demand']].loc[:, 'unit'].values[0].split(' / ')[0]

        overview_tab = create_overview_table()

        conversion_components_tab = create_conversion_components_table()
        conversion_components_tab_columns = conversion_components_tab.columns[1:]

        storage_components_tab = create_storage_table()
        storage_components_tab_columns = storage_components_tab.columns[1:]

        cost_fig, cost_share_fig, cost_structure_df = create_cost_structure_graph()

        generation_tab = create_generation_table()

        commodity_tab = create_commodity_table()

        return monetary_unit, assumptions_tab, assumptions_tab_columns, annual_production, annual_production_unit,\
            overview_tab, conversion_components_tab, conversion_components_tab_columns, \
            storage_components_tab, storage_components_tab_columns, \
            cost_fig, cost_share_fig, cost_structure_df, generation_tab, commodity_tab

    def create_browser_visualization_single_result():

        # prepare time series for graph plot
        time_series_unit = time_series_df.iloc[:, 0]
        time_series_data = time_series_df.iloc[:, 1:]

        # Dictionary to get index-triple from str(i)
        index_dictionary = dict([(str(i), i) for i in time_series_df.index])

        # Readable names for checklist
        def merge_tuples(*t):
            return tuple(j for i in t for j in (i if isinstance(i, tuple) else (i,)))

        first_column_index = ['Charging', 'Discharging', 'Demand', 'Emitting', 'Freely Available', 'Generation',
                              'Purchase', 'Selling', 'Input', 'Output', 'State of Charge', 'Total Generation',
                              'Hot Standby Demand']

        time_series_df['Name'] = time_series_df.index.tolist()
        for c in first_column_index:
            if c in time_series_df.index.get_level_values(0):
                for i in time_series_df.loc[c].index:
                    if str(i[0]) == 'nan':
                        name = str(i[1]) + ' ' + c
                    else:
                        name = str(i[1]) + ' ' + c + ' ' + str(i[0])

                    time_series_df.at[merge_tuples(c, i), 'Name'] = name

        # Implement web application
        app = dash.Dash(__name__)

        app.title = name_scenario
        app.layout = html.Div([
            html.Div(
                [
                    html.H2(
                        ["PtX-Results"], className="subtitle padded", style={'font-family': 'Arial'}
                    ),
                    html.Div(children='This website is a tool to visualize and display model results.',
                             style={'margin-bottom': '20px'}),
                ]
            ),
            dcc.Tabs([
                dcc.Tab(label='Assumptions',
                    children=[
                        html.Div([
                            html.H2(
                                ["Assumptions"],
                                className="subtitle padded",
                                style={'font-family': 'Calibri'}),
                            dash_table.DataTable(
                                id='assumptions',
                                columns=[{"name": i, "id": i} for i in assumptions_table.columns],
                                data=assumptions_table.to_dict('records'),
                                style_as_list_view=True,
                                style_cell_conditional=[
                                    {'if': {'column_id': assumptions_table_columns},
                                     'textAlign': 'left',
                                     'font-family': 'Calibri',
                                     'width': '10%'},
                                    {'if': {'column_id': ''},
                                     'textAlign': 'left',
                                     'font-family': 'Calibri',
                                     'width': '10%',
                                     'background-color': '#f5f2f2'}],
                                style_data_conditional=[
                                    {'if': {'column_id': ''},
                                     'fontWeight': 'bold'}],
                                style_header={
                                    'fontWeight': 'bold',
                                    'background-color': '#edebeb'})],
                            style={'width': '50%'}
                        )
                    ]
                ),
                dcc.Tab(label='Overview Results',
                    children=[
                        html.Div([
                            html.H2(
                                ["Results"],
                                className="subtitle padded",
                                style={'font-family': 'Calibri'}),
                            dash_table.DataTable(
                                id='overview_table',
                                columns=[{"name": i, "id": i} for i in overview_table.columns],
                                data=overview_table.to_dict('records'),
                                style_as_list_view=True,
                                style_cell_conditional=[
                                    {'if': {'column_id': 'Value'},
                                     'textAlign': 'left',
                                     'font-family': 'Calibri',
                                     'width': '10%'},
                                    {'if': {'column_id': ''},
                                     'textAlign': 'left',
                                     'font-family': 'Calibri',
                                     'width': '10%',
                                     'background-color': '#f5f2f2'}],
                                style_data_conditional=[
                                    {'if': {'column_id': ''},
                                     'fontWeight': 'bold', }],
                                style_header={
                                    'fontWeight': 'bold',
                                    'background-color': '#edebeb'}
                            )
                        ],
                            style={'width': '50%'}
                        )
                    ]
                ),
                dcc.Tab(label='Conversion Components',
                    children=[
                        html.Div([
                            html.H2(
                                ["Conversion Components"],
                                className="subtitle padded",
                                style={'font-family': 'Calibri'}),
                            dash_table.DataTable(
                                id='conversion_components_table',
                                columns=[{"name": i, "id": i} for i in conversion_components_table.columns],
                                data=conversion_components_table.to_dict('records'),
                                style_as_list_view=True,
                                style_cell_conditional=[
                                    {'if': {'column_id': conversion_components_table_columns},
                                     'textAlign': 'left',
                                     'font-family': 'Calibri',
                                     'width': '10%'},
                                    {'if': {'column_id': ''},
                                     'textAlign': 'left',
                                     'font-family': 'Calibri',
                                     'width': '10%',
                                     'background-color': '#f5f2f2'}],
                                style_data_conditional=[
                                    {'if': {'column_id': ''},
                                     'fontWeight': 'bold'}],
                                style_header={
                                    'fontWeight': 'bold',
                                    'background-color': '#edebeb'}
                            )
                        ])
                    ]
                ),
                dcc.Tab(label='Storage Components',
                    children=[
                        html.Div([
                            html.H2(
                                ["Storage Components"],
                                className="subtitle padded",
                                style={'font-family': 'Calibri'}),
                            dash_table.DataTable(
                                id='storage_components_table',
                                columns=[{"name": i, "id": i} for i in storage_components_table.columns],
                                data=storage_components_table.to_dict('records'),
                                style_as_list_view=True,
                                style_cell_conditional=[
                                    {'if': {'column_id': storage_components_table_columns},
                                     'textAlign': 'left',
                                     'font-family': 'Calibri',
                                     'width': '10%'},
                                    {'if': {'column_id': ''},
                                     'textAlign': 'left',
                                     'font-family': 'Calibri',
                                     'width': '10%',
                                     'background-color': '#f5f2f2'}],
                                style_data_conditional=[
                                    {'if': {'column_id': ''},
                                     'fontWeight': 'bold'}],
                                style_header={
                                    'fontWeight': 'bold',
                                    'background-color': '#edebeb'},
                            )
                        ])
                    ]
                ),
                dcc.Tab(
                    label='Generation Components',
                    children=[
                        html.Div([
                            html.H2(
                                ["Generation Components"],
                                className="subtitle padded",
                                style={'font-family': 'Calibri'}),
                            dash_table.DataTable(
                                id='generation_table',
                                columns=[{"name": i, "id": i} for i in generation_table.columns],
                                data=generation_table.to_dict('records'),
                                style_as_list_view=True,
                                style_cell_conditional=[
                                    {'if': {'column_id': ''},
                                     'textAlign': 'left',
                                     'font-family': 'Calibri',
                                     'width': '10%'},
                                    {'if': {'column_id': ''},
                                     'textAlign': 'left',
                                     'font-family': 'Calibri',
                                     'width': '10%',
                                     'background-color': '#f5f2f2'}],
                                style_data_conditional=[
                                    {'if': {'column_id': ''},
                                     'fontWeight': 'bold'}],
                                style_header={
                                    'fontWeight': 'bold',
                                    'background-color': '#edebeb'})
                        ],
                            style={'width': '100%'}
                        )
                    ]
                ),
                dcc.Tab(
                    label='Streams',
                    children=[
                        html.Div([
                            html.H2(
                                ["Streams"],
                                className="subtitle padded",
                                style={'font-family': 'Calibri'}),
                            dash_table.DataTable(
                                id='commodity_table',
                                columns=[{"name": i, "id": i} for i in commodity_table.columns],
                                data=commodity_table.to_dict('records'),
                                style_as_list_view=True,
                                style_cell_conditional=[
                                    {'if': {'column_id': ''},
                                     'textAlign': 'left',
                                     'font-family': 'Calibri',
                                     'width': '10%'},
                                    {'if': {'column_id': ''},
                                     'textAlign': 'left',
                                     'font-family': 'Calibri',
                                     'width': '10%',
                                     'background-color': '#f5f2f2'}],
                                style_data_conditional=[
                                    {'if': {'column_id': ''},
                                     'fontWeight': 'bold'}],
                                style_header={
                                    'fontWeight': 'bold',
                                    'background-color': '#edebeb'})
                        ],
                            style={'width': '100%'}
                        )
                    ]
                ),
                dcc.Tab(
                    label='Cost Distribution',
                    children=[
                        html.Div([
                            html.Div([
                                html.Div(
                                    children=dcc.Graph(figure=cost_share_figure),
                                     style={
                                         'height': '100px',
                                         'margin-left': '10px',
                                         'width': '45%',
                                         'text-align': 'center',
                                         'display': 'inline-block'}),
                                html.Div(
                                    children=[
                                        dash_table.DataTable(
                                            id='cost_structure_table',
                                            columns=[{"name": i, "id": i} for i in cost_structure_dataframe.columns],
                                            data=cost_structure_dataframe.to_dict('records'),
                                            style_as_list_view=True,
                                            style_cell_conditional=[
                                                {'if': {'column_id': ''},
                                                 'textAlign': 'left',
                                                 'font-family': 'Calibri',
                                                 'width': '10%'},
                                                {'if': {'column_id': ''},
                                                 'textAlign': 'left',
                                                 'font-family': 'Calibri',
                                                 'width': '10%',
                                                 'background-color': '#f5f2f2'}],
                                            style_data_conditional=[
                                                {'if': {'column_id': ''},
                                                 'fontWeight': 'bold'}],
                                            style_header={
                                                'fontWeight': 'bold',
                                                'background-color': '#edebeb'})
                                    ],
                                    style={'width': '50%', 'float': 'right'}
                                )
                            ])
                        ])
                    ]
                ),
                dcc.Tab(label='Graph',
                    children=[
                        html.Div([
                            html.Div(dcc.Graph(id='indicator_graphic')),
                            html.Div([
                                html.Div([
                                    "left Y-axis",
                                    dcc.Dropdown(
                                        className='Y-axis left',
                                        id='yaxis_main',
                                        options=[{'label': str(i), 'value': str(i)} for i in
                                                 time_series_unit.unique()]),
                                    dcc.Checklist(
                                        id='checklist_left',
                                        labelStyle={'display': 'block'})],
                                    style={'width': '48%', 'display': 'inline-block'}),
                                html.Div([
                                    "right Y-axis",
                                    dcc.Dropdown(
                                        className='Y-axis right',
                                        id='yaxis_right',
                                        options=[{'label': str(i), 'value': str(i)} for i in
                                                 time_series_unit.unique()]),
                                    dcc.Checklist(
                                        id='checklist_right',
                                        labelStyle={'display': 'block'})],
                                    style={'width': '48%', 'float': 'right', 'display': 'inline-block'}
                                )
                            ])
                        ])
                    ]
                ),
                dcc.Tab(label='Load profile',
                    children=[
                        html.Div([
                            html.Div([
                                html.Div([
                                    html.H4(children="Generator Selection",
                                            className="subtitle padded", style={'font-family': 'Arial'}),
                                    dcc.Checklist(
                                        id='load_profile_checklist',
                                        options=[{
                                            'label': c[0] + ' ' + c[1],
                                            'value': str(('Generation',) + c)} for c in
                                            time_series_df.loc['Generation'].index],
                                        labelStyle={'display': 'block'})],
                                    style={'width': '85%', 'display': 'inline-block'})],
                                style={'width': '16%', 'display': 'inline-block',
                                       'vertical-align': 'top', 'marginTop': '40px', 'marginLeft': '20px'}),
                            dcc.Graph(
                                id='load_profile',
                                figure=go.Figure(
                                    data=[],
                                    layout=go.Layout(
                                        title="Load profile",
                                        xaxis=dict(
                                            title='h',
                                            categoryorder='category descending'),
                                        yaxis=dict(
                                            title='kW',
                                            rangemode='tozero'),
                                        barmode='stack',
                                        legend=dict(
                                            orientation='h',
                                            bgcolor='rgba(255, 255, 255, 0)',
                                            bordercolor='rgba(255, 255, 255, 0)'),
                                        paper_bgcolor='rgba(255, 255, 255, 255)',
                                        plot_bgcolor='#f7f7f7')),
                                style={'width': '80%', 'display': 'inline-block'})
                        ])
                    ]
                )
            ])
        ])

        @app.callback(
            Output('checklist_left', 'options'),
            Input('yaxis_main', 'value'),
        )
        def update_dropdown_left(selection):
            t = time_series_unit == str(selection)
            return [{'label': str(time_series_df.at[i, 'Name']), 'value': str(i)} for i in t.index[t.tolist()]]

        @app.callback(
            Output('checklist_right', 'options'),
            Input('yaxis_right', 'value'),
        )
        def update_dropdown_right(selection):
            t = time_series_unit == str(selection)
            return [{'label': str(time_series_df.at[i, 'Name']), 'value': str(i)} for i in t.index[t.tolist()]]

        @app.callback(
            Output('indicator_graphic', 'figure'),
            Input('checklist_left', 'value'),
            Input('checklist_right', 'value'),
            Input('yaxis_main', 'value'),
            Input('yaxis_right', 'value')
        )
        def update_graph(left_checklist, right_checklist, unit_left, unit_right):
            color_left = cycle(px.colors.qualitative.Plotly)
            color_right = cycle(px.colors.qualitative.Plotly[::-1])
            if unit_right is None:
                data_graph = []
                if left_checklist is not None:
                    for i in range(0, len(left_checklist)):
                        globals()['right_trace%s' % i] = \
                            go.Scatter(
                                x=time_series_data.columns,
                                y=time_series_data.loc[index_dictionary[left_checklist[i]]],
                                name=time_series_df.at[index_dictionary[left_checklist[i]], 'Name'] + ', '
                                    + time_series_unit.loc[index_dictionary[left_checklist[i]]],
                                line=dict(color=next(color_left))
                            )
                        data_graph.append(globals()['right_trace%s' % i])
                layout = go.Layout(
                    title="PtX-Model: Stream Visualization",
                    xaxis=dict(
                        title='h',
                        range=[0, time_series_data.shape[1] + 10]
                    ),
                    yaxis=dict(
                        title=unit_left,
                        rangemode="tozero",
                        showgrid=True
                    ),
                    legend=dict(
                        # orientation='h',
                        # x=0,
                        # y=-1,
                        bgcolor='rgba(255, 255, 255, 0)',
                        bordercolor='rgba(255, 255, 255, 0)'
                    ),
                    showlegend=True,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='#f7f7f7'
                )
                fig = go.Figure(data=data_graph, layout=layout)
                return fig
            elif unit_right is not None:
                data_graph = []
                for i in range(0, len(left_checklist)):
                    globals()['left_trace%s' % i] = go.Scatter(
                        x=time_series_data.columns,
                        y=time_series_data.loc[index_dictionary[left_checklist[i]]],
                        name=time_series_df.at[index_dictionary[left_checklist[i]], 'Name'],
                        legendgroup='left',
                        legendgrouptitle=dict(
                            text=str(time_series_unit.loc[index_dictionary[left_checklist[i]]]) + ':'
                        ),
                        line=dict(color=next(color_left)),
                    )
                    data_graph.append(globals()['left_trace%s' % i])
                if right_checklist is not None:
                    for i in range(0, len(right_checklist)):
                        globals()['right_trace%s' % i] = go.Scatter(
                            x=time_series_data.columns,
                            y=time_series_data.loc[index_dictionary[right_checklist[i]]],
                            name=time_series_df.at[index_dictionary[right_checklist[i]], 'Name'],
                            yaxis='y2',
                            legendgroup='right',
                            legendgrouptitle=dict(
                                text=str(time_series_unit.loc[index_dictionary[right_checklist[i]]]) + ':'
                            ),
                            line=dict(color=next(color_right)))
                        data_graph.append(globals()['right_trace%s' % i])
                layout = go.Layout(
                    title="PtX-Model: Stream Visualization",
                    xaxis=dict(
                        title='h',
                        domain=[0, 0.95]
                    ),
                    yaxis=dict(
                        title=unit_left,
                        rangemode='tozero'
                    ),
                    yaxis2=dict(
                        title=unit_right,
                        rangemode='tozero',
                        overlaying='y',
                        side='right',
                    ),
                    legend=dict(
                        # orientation='h',
                        bgcolor='rgba(255, 255, 255, 0)',
                        bordercolor='rgba(255, 255, 255, 0)'
                    ),
                    legend_tracegroupgap=25,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='#f7f7f7'
                )
                fig = go.Figure(data=data_graph, layout=layout)
                return fig

        @app.callback(
            Output('load_profile', 'figure'),
            Output('load_profile', 'style'),
            Input('load_profile_checklist', 'value'))
        def update_load_profile(check):
            load_profile_data = []
            if check is not None:
                for i in range(0, len(check)):
                    cache = time_series_data.sort_values(axis=1, by=index_dictionary[check[i]],
                                                        ignore_index=True, ascending=False).loc[
                        index_dictionary[check[i]]]
                    load_profile_data.append(
                        go.Bar(
                            x=cache.index,
                            y=cache,
                            name=time_series_df.at[index_dictionary[check[i]], 'Name'],
                            width=1,
                            marker=dict(line=dict(width=0))
                        )
                    )
                layout = go.Layout(
                    title="Load profile",
                    xaxis=dict(
                        title='h',
                        categoryorder='category descending'
                    ),
                    yaxis=dict(
                        title='kW',
                        rangemode='tozero'
                    ),
                    barmode='stack',
                    legend=dict(
                        orientation='h',
                        bgcolor='rgba(255, 255, 255, 0)',
                        bordercolor='rgba(255, 255, 255, 0)'
                    ),
                    paper_bgcolor='rgba(255, 255, 255, 255)',
                    plot_bgcolor='#f7f7f7',
                )
                fig = go.Figure(data=load_profile_data, layout=layout)
                style = {'width': '80%', 'display': 'inline-block'}
                return fig, style

        def open_page():
            return webbrowser.open('http://127.0.0.1:8050/')

        Timer(1.0, open_page()).start(),
        app.run_server(debug=False, use_reloader=False)

    def extract_results_multiple_results_single_scenario():

        results_df = pd.DataFrame()
        for f in folders_single:
            folder_df = pd.DataFrame(index=[f])
            for s in generation_single[f]['Generated Stream'].unique():

                generators_with_s = generation_single[f][generation_single[f]['Generated Stream'] == s].index

                potential_generation_s = 0
                total_capacity_s = 0
                actual_generation_s = 0
                curtailment_s = 0

                for g in generators_with_s:
                    folder_df.loc[f, g + ' Capacity'] = generation_single[f].loc[g, 'Capacity']
                    folder_df.loc[f, g + ' Potential Full-load Hours'] = generation_single[f].loc[
                        g, 'Potential Full-load Hours']
                    folder_df.loc[f, g + ' Potential LCOE'] = generation_single[f].loc[g, 'LCOE before Curtailment']
                    folder_df.loc[f, g + ' Curtailment'] = generation_single[f].loc[g, 'Curtailment'] / generation_single[f].loc[g, 'Potential Full-load Hours'] * 100
                    folder_df.loc[f, g + ' Actual Full-load Hours'] = generation_single[f].loc[g, 'Actual Full-load Hours']
                    folder_df.loc[f, g + ' Actual LCOE'] = generation_single[f].loc[g, 'LCOE after Curtailment']

                    potential_generation_s += generation_single[f].loc[g, 'Potential Generation']
                    total_capacity_s += generation_single[f].loc[g, 'Capacity']
                    actual_generation_s += generation_single[f].loc[g, 'Actual Generation']
                    curtailment_s += generation_single[f].loc[g, 'Curtailment'] / generation_single[f].loc[g, 'Potential Full-load Hours'] * 100

                if len(generators_with_s) > 1:
                    generators_with_s_df = generation_profiles_single[f][generators_with_s]
                    maximal_flh = calculate_maximal_full_load_hours(generators_with_s_df)

                    folder_df.loc[f, s + ' Capacity'] = total_capacity_s
                    folder_df.loc[f, s + ' Maximal Full-load Hours'] = maximal_flh
                    folder_df.loc[f, s + ' Potential Full-load Hours'] = potential_generation_s / (
                            total_capacity_s * 8760) * 8760
                    folder_df.loc[f, s + ' Potential LCOE'] = commodities_single[f].loc[s, 'Total Generation Fix Costs'] / (
                            total_capacity_s * 8760) * 8760
                    folder_df.loc[f, s + ' Curtailment'] = curtailment_s
                    folder_df.loc[f, s + ' Actual Full-load Hours'] = actual_generation_s / (
                            total_capacity_s * 8760) * 8760
                    folder_df.loc[f, s + ' Actual LCOE'] = commodities_single[f].loc[
                                                               s, 'Production Costs per Unit'] / actual_generation_s
                    folder_df.loc[f, s + ' Generation Costs'] = commodities_single[f].loc[s, 'Costs per used unit']

            for c in components_single[f].index:
                if components_single[f].loc[c, 'Capacity Basis'] == 'input':
                    folder_df.loc[f, c + ' Capacity'] = components_single[f].loc[c, 'Capacity [input]']
                    folder_df.loc[f, c + ' Full-load Hours'] = components_single[f].loc[c, 'Full-load Hours']
                elif components_single[f].loc[c, 'Capacity Basis'] == 'output':
                    folder_df.loc[f, c + ' Capacity'] = components_single[f].loc[c, 'Capacity [output]']
                    folder_df.loc[f, c + ' Full-load Hours'] = components_single[f].loc[c, 'Full-load Hours']
                elif components_single[f].loc[c, 'Capacity [output]'] == '':
                    folder_df.loc[f, c + ' Capacity'] = components_single[f].loc[c, 'Capacity [input]']
                else:
                    folder_df.loc[f, c + ' Capacity'] = components_single[f].loc[c, 'Capacity [output]']

            folder_df.loc[f, 'Production Costs'] = results_overview_single[f].loc['Production Costs per Unit', 0]

            results_df = pd.concat([results_df, folder_df], axis=0)

        return results_df

    def extract_results_multiple_results_different_scenarios():

        results_df = pd.DataFrame()

        for f in folders_multiple:

            f1 = f[0]
            f2 = f[1]

            folder_df = pd.DataFrame(index=[f2])
            folder_df.loc[f2, 'Super Folder'] = f1

            for s in generation_multiple[f1][f2]['Generated Stream'].unique():

                generators_with_s = generation_multiple[f1][f2][generation_multiple[f1][f2]['Generated Stream'] == s].index

                potential_generation_s = 0
                total_capacity_s = 0
                actual_generation_s = 0
                curtailment_s = 0

                for g in generators_with_s:
                    folder_df.loc[f2, g + ' Capacity'] = generation_multiple[f1][f2].loc[g, 'Capacity']
                    folder_df.loc[f2, g + ' Potential Full-load Hours'] = generation_multiple[f1][f2].loc[
                        g, 'Potential Full-load Hours']
                    folder_df.loc[f2, g + ' Potential LCOE'] = generation_multiple[f1][f2].loc[g, 'LCOE before Curtailment']
                    folder_df.loc[f2, g + ' Curtailment'] = generation_multiple[f1][f2].loc[g, 'Curtailment']
                    folder_df.loc[f2, g + ' Actual Full-load Hours'] = generation_multiple[f1][f2].loc[
                        g, 'Actual Full-load Hours']
                    folder_df.loc[f2, g + ' Actual LCOE'] = generation_multiple[f1][f2].loc[g, 'LCOE after Curtailment']

                    potential_generation_s += generation_multiple[f1][f2].loc[g, 'Potential Generation']
                    total_capacity_s += generation_multiple[f1][f2].loc[g, 'Capacity']
                    actual_generation_s += generation_multiple[f1][f2].loc[g, 'Actual Generation']
                    curtailment_s += generation_multiple[f1][f2].loc[g, 'Curtailment']

                if len(generators_with_s) > 1:
                    generators_with_s_df = generation_profiles_multiple[f1][f2][generators_with_s]
                    maximal_flh = calculate_maximal_full_load_hours(generators_with_s_df)

                    folder_df.loc[f2, s + ' Capacity'] = total_capacity_s
                    folder_df.loc[f2, s + ' Maximal Full-load Hours'] = maximal_flh
                    folder_df.loc[f2, s + ' Potential Full-load Hours'] = potential_generation_s / (
                            total_capacity_s * 8760) * 8760
                    folder_df.loc[f2, s + ' Potential LCOE'] = commodities_multiple[f1][f2].loc[
                                                                   s, 'Total Generation Fix Costs'] / (
                                                                       total_capacity_s * 8760) * 8760
                    folder_df.loc[f2, s + ' Curtailment'] = curtailment_s
                    folder_df.loc[f2, s + ' Actual Full-load Hours'] = actual_generation_s / (
                            total_capacity_s * 8760) * 8760
                    folder_df.loc[f2, s + ' Actual LCOE'] = commodities_multiple[f1][f2].loc[
                                                                s, 'Production Costs per Unit'] / actual_generation_s
                    folder_df.loc[f2, s + ' Generation Costs'] = commodities_multiple[f1][f2].loc[s, 'Costs per used unit']

            for c in components_multiple[f1][f2].index:
                if components_multiple[f1][f2].loc[c, 'Capacity Basis'] == 'input':
                    folder_df.loc[f2, c + ' Capacity'] = components_multiple[f1][f2].loc[c, 'Capacity [input]']
                    folder_df.loc[f2, c + ' Full-load Hours'] = components_multiple[f1][f2].loc[c, 'Full-load Hours']
                elif components_multiple[f1][f2].loc[c, 'Capacity Basis'] == 'output':
                    folder_df.loc[f2, c + ' Capacity'] = components_multiple[f1][f2].loc[c, 'Capacity [output]']
                    folder_df.loc[f2, c + ' Full-load Hours'] = components_multiple[f1][f2].loc[c, 'Full-load Hours']
                elif components_multiple[f1][f2].loc[c, 'Capacity [output]'] == '':
                    folder_df.loc[f2, c + ' Capacity'] = components_multiple[f1][f2].loc[c, 'Capacity [input]']
                else:
                    folder_df.loc[f2, c + ' Capacity'] = components_multiple[f1][f2].loc[c, 'Capacity [output]']

            folder_df.loc[f2, 'Production Costs'] = results_overview_multiple[f1][f2].loc['Production Costs per Unit', 0]

            results_df = pd.concat([results_df, folder_df], axis=0)

        return results_df

    def calculate_maximal_full_load_hours(generator_profiles):

        def create_combinations(initial_values=None, scale=10, direction_up=True):

            capacities = {}
            if initial_values is None:
                for g in generators:
                    capacities[g] = np.array([round(i / scale, 3) for i in range(11)])
            else:
                if direction_up:
                    for ind, g in enumerate(generators):
                        if initial_values[ind] == 1:
                            capacities[g] = np.array([initial_values[ind]])
                        else:
                            capacities[g] = np.array([round(initial_values[ind] + (i / scale), 3) for i in range(11)])
                else:
                    for ind, g in enumerate(generators):
                        if initial_values[ind] == 0:
                            capacities[g] = np.array([initial_values[ind]])
                        else:
                            capacities[g] = np.array(
                                [round(initial_values[ind] - (1 / scale * 10) + (i / scale), 3) for i in range(11)])

            import itertools

            capacities_combinations = itertools.product(capacities[[*capacities.keys()][0]],
                                                        capacities[[*capacities.keys()][1]])

            if len(generators) > 2:
                combinations = []
                for i in range(2, len([*capacities.keys()])):
                    sub_list = []
                    for c in capacities_combinations:
                        sub_list.append(list(c))

                    b = itertools.product(sub_list, capacities[[*capacities.keys()][i]])

                    for c in b:
                        sub_sub_list = c[0].copy()
                        sub_sub_list.append(c[1])
                        combinations.append(sub_sub_list)
            else:
                combinations = []
                for c in capacities_combinations:
                    combinations.append(list(c))

            return combinations

        def calculate_flh(flh=0):

            max_value = None
            for c in all_combinations:
                all_zeros = True
                for c_value in c:
                    if c_value != float(0):
                        all_zeros = False
                        break

                if not all_zeros:

                    flh_array = np.zeros(8760)
                    capacity = 0
                    for i, key in enumerate(generators_with_s_profiles):
                        flh_array = np.add(flh_array, generators_with_s_profiles[key] * c[i])
                        capacity += c[i]

                    if round(flh_array.sum() / capacity, 3) >= flh:
                        flh = round(flh_array.sum() / capacity, 3)
                        max_value = c

            return flh, max_value

        generators_with_s_profiles = {}
        generators = []
        for g in generator_profiles.columns:
            generators_with_s_profiles[g] = np.array([i[0] for i in generator_profiles.loc[:, g].values])
            generators.append(g)

        all_combinations = create_combinations()
        highest_flh, highest_flh_combination = calculate_flh()

        all_combinations = create_combinations(initial_values=highest_flh_combination, scale=100)
        highest_flh, highest_flh_combination = calculate_flh(flh=highest_flh)

        all_combinations = create_combinations(initial_values=highest_flh_combination, scale=100, direction_up=False)
        highest_flh, highest_flh_combination = calculate_flh(flh=highest_flh)

        all_combinations = create_combinations(initial_values=highest_flh_combination, scale=1000)
        highest_flh, highest_flh_combination = calculate_flh(flh=highest_flh)

        all_combinations = create_combinations(initial_values=highest_flh_combination, scale=1000, direction_up=False)
        highest_flh, highest_flh_combination = calculate_flh(flh=highest_flh)

        return highest_flh

    def create_web_page_multiple_results():

        time_series = results_per_case[[*results_per_case.keys()][0]]['time_series_df']

        time_series_unit = time_series.iloc[:, 0]
        time_series_data = time_series.iloc[:, 1:]

        # Dictionary to get index-triple from str(i)
        index_dictionary = dict([(str(i), i) for i in time_series.index])

        # Readable names for checklist
        def merge_tuples(*t):
            return tuple(j for i in t for j in (i if isinstance(i, tuple) else (i,)))

        first_column_index = ['Charging', 'Discharging', 'Demand', 'Emitting', 'Freely Available', 'Generation',
                              'Purchase', 'Selling', 'Input', 'Output', 'State of Charge', 'Total Generation',
                              'Hot Standby Demand']

        time_series['Name'] = time_series.index.tolist()
        for c in first_column_index:
            if c in time_series.index.get_level_values(0):
                for i in time_series.loc[c].index:
                    if str(i[0]) == 'nan':
                        name = str(i[1]) + ' ' + c
                    else:
                        name = str(i[1]) + ' ' + c + ' ' + str(i[0])

                    time_series.at[merge_tuples(c, i), 'Name'] = name

        entries = results_dataframe.columns.tolist()
        if 'Super Folder' in entries:
            entries.remove('Super Folder')

        # Implement web application
        app = dash.Dash(__name__)

        if False:
            dcc.Tab(label='Assumptions',
                    children=[
                        html.Div([
                            html.H2(
                                ["Assumptions"],
                                className="subtitle padded",
                                style={'font-family': 'Calibri'}),
                            dash_table.DataTable(
                                id='assumptions',
                                columns=[{"name": i, "id": i} for i in assumptions_table.columns],
                                data=assumptions_table.to_dict('records'),
                                style_as_list_view=True,
                                style_cell_conditional=[
                                    {'if': {'column_id': assumptions_table_columns},
                                     'textAlign': 'left',
                                     'font-family': 'Calibri',
                                     'width': '10%'},
                                    {'if': {'column_id': ''},
                                     'textAlign': 'left',
                                     'font-family': 'Calibri',
                                     'width': '10%',
                                     'background-color': '#f5f2f2'}],
                                style_data_conditional=[
                                    {'if': {'column_id': ''},
                                     'fontWeight': 'bold'}],
                                style_header={
                                    'fontWeight': 'bold',
                                    'background-color': '#edebeb'})],
                            style={'width': '50%'}
                        )
                    ]
                    ),
            dcc.Tab(label='Overview Results',
                    children=[
                        html.Div([
                            html.H2(
                                ["Results"],
                                className="subtitle padded",
                                style={'font-family': 'Calibri'}),
                            dash_table.DataTable(
                                id='overview_table',
                                columns=[{"name": i, "id": i} for i in overview_table.columns],
                                data=overview_table.to_dict('records'),
                                style_as_list_view=True,
                                style_cell_conditional=[
                                    {'if': {'column_id': 'Value'},
                                     'textAlign': 'left',
                                     'font-family': 'Calibri',
                                     'width': '10%'},
                                    {'if': {'column_id': ''},
                                     'textAlign': 'left',
                                     'font-family': 'Calibri',
                                     'width': '10%',
                                     'background-color': '#f5f2f2'}],
                                style_data_conditional=[
                                    {'if': {'column_id': ''},
                                     'fontWeight': 'bold', }],
                                style_header={
                                    'fontWeight': 'bold',
                                    'background-color': '#edebeb'}
                            )
                        ],
                            style={'width': '50%'}
                        )
                    ]
                    ),
            dcc.Tab(
                label='Conversion Components',
                children=[
                    html.Div([
                        html.H2(
                            ["Conversion Components"],
                            className="subtitle padded",
                            style={'font-family': 'Calibri'}),
                        dash_table.DataTable(
                            id='conversion_components_table',
                            columns=[{"name": i, "id": i} for i in conversion_components_table.columns],
                            data=conversion_components_table.to_dict('records'),
                            style_as_list_view=True,
                            style_cell_conditional=[
                                {'if': {'column_id': conversion_components_table_columns},
                                 'textAlign': 'left',
                                 'font-family': 'Calibri',
                                 'width': '10%'},
                                {'if': {'column_id': ''},
                                 'textAlign': 'left',
                                 'font-family': 'Calibri',
                                 'width': '10%',
                                 'background-color': '#f5f2f2'}],
                            style_data_conditional=[
                                {'if': {'column_id': ''},
                                 'fontWeight': 'bold'}],
                            style_header={
                                'fontWeight': 'bold',
                                'background-color': '#edebeb'})
                    ])
                ]
            ),
            dcc.Tab(
                label='Storage Components',
                children=[
                    html.Div([
                        html.H2(
                            ["Storage Components"],
                            className="subtitle padded",
                            style={'font-family': 'Calibri'}),
                        dash_table.DataTable(
                            id='storage_components_table',
                            columns=[{"name": i, "id": i} for i in storage_components_table.columns],
                            data=storage_components_table.to_dict('records'),
                            style_as_list_view=True,
                            style_cell_conditional=[
                                {'if': {'column_id': storage_components_table_columns},
                                 'textAlign': 'left',
                                 'font-family': 'Calibri',
                                 'width': '10%'},
                                {'if': {'column_id': ''},
                                 'textAlign': 'left',
                                 'font-family': 'Calibri',
                                 'width': '10%',
                                 'background-color': '#f5f2f2'}],
                            style_data_conditional=[
                                {'if': {'column_id': ''},
                                 'fontWeight': 'bold'}],
                            style_header={
                                'fontWeight': 'bold',
                                'background-color': '#edebeb'})
                    ])
                ]
            ),
            dcc.Tab(
                label='Generation Components',
                children=[
                    html.Div([
                        html.H2(
                            ["Generation Components"],
                            className="subtitle padded",
                            style={'font-family': 'Calibri'}),
                        dash_table.DataTable(
                            id='generation_table',
                            columns=[{"name": i, "id": i} for i in generation_table.columns],
                            data=generation_table.to_dict('records'),
                            style_as_list_view=True,
                            style_cell_conditional=[
                                {'if': {'column_id': ''},
                                 'textAlign': 'left',
                                 'font-family': 'Calibri',
                                 'width': '10%'},
                                {'if': {'column_id': ''},
                                 'textAlign': 'left',
                                 'font-family': 'Calibri',
                                 'width': '10%',
                                 'background-color': '#f5f2f2'}],
                            style_data_conditional=[
                                {'if': {'column_id': ''},
                                 'fontWeight': 'bold'}],
                            style_header={
                                'fontWeight': 'bold',
                                'background-color': '#edebeb'})
                    ],
                        style={'width': '100%'}
                    )
                ]
            ),
            dcc.Tab(
                label='Streams',
                children=[
                    html.Div([
                        html.H2(
                            ["Streams"],
                            className="subtitle padded",
                            style={'font-family': 'Calibri'}),
                        dash_table.DataTable(
                            id='commodity_table',
                            columns=[{"name": i, "id": i} for i in commodity_table.columns],
                            data=commodity_table.to_dict('records'),
                            style_as_list_view=True,
                            style_cell_conditional=[
                                {'if': {'column_id': ''},
                                 'textAlign': 'left',
                                 'font-family': 'Calibri',
                                 'width': '10%'},
                                {'if': {'column_id': ''},
                                 'textAlign': 'left',
                                 'font-family': 'Calibri',
                                 'width': '10%',
                                 'background-color': '#f5f2f2'}],
                            style_data_conditional=[
                                {'if': {'column_id': ''},
                                 'fontWeight': 'bold'}],
                            style_header={
                                'fontWeight': 'bold',
                                'background-color': '#edebeb'})
                    ],
                        style={'width': '100%'}
                    )
                ]
            ),
            dcc.Tab(
                label='Cost Distribution',
                children=[
                    html.Div([
                        html.Div([
                            html.Div(
                                children=dcc.Graph(id='cost_share_figure'),
                                style={
                                    'height': '100px',
                                    'margin-left': '10px',
                                    'width': '45%',
                                    'text-align': 'center',
                                    'display': 'inline-block'}),
                            html.Div(
                                children=[
                                    dash_table.DataTable(
                                        id='cost_structure_table',
                                        columns=[{"name": i, "id": i} for i in cost_structure_dataframe.columns],
                                        data=cost_structure_dataframe.to_dict('records'),
                                        style_as_list_view=True,
                                        style_cell_conditional=[
                                            {'if': {'column_id': ''},
                                             'textAlign': 'left',
                                             'font-family': 'Calibri',
                                             'width': '10%'},
                                            {'if': {'column_id': ''},
                                             'textAlign': 'left',
                                             'font-family': 'Calibri',
                                             'width': '10%',
                                             'background-color': '#f5f2f2'}],
                                        style_data_conditional=[
                                            {'if': {'column_id': ''},
                                             'fontWeight': 'bold'}],
                                        style_header={
                                            'fontWeight': 'bold',
                                            'background-color': '#edebeb'})
                                ],
                                style={'width': '50%', 'float': 'right'}
                            )
                        ])
                    ])
                ]
            ),
            dcc.Tab(label='Graph',
                    children=[
                        html.Div([
                            html.Div(dcc.Graph(id='indicator_graphic')),
                            html.Div([
                                html.Div([
                                    "left Y-axis",
                                    dcc.Dropdown(
                                        className='Y-axis left',
                                        id='yaxis_main',
                                        options=[{'label': str(i), 'value': str(i)} for i in
                                                 time_series_unit.unique()]),
                                    dcc.Checklist(
                                        id='checklist_left',
                                        labelStyle={'display': 'block'})],
                                    style={'width': '48%', 'display': 'inline-block'}),
                                html.Div([
                                    "right Y-axis",
                                    dcc.Dropdown(
                                        className='Y-axis right',
                                        id='yaxis_right',
                                        options=[{'label': str(i), 'value': str(i)} for i in
                                                 time_series_unit.unique()]),
                                    dcc.Checklist(
                                        id='checklist_right',
                                        labelStyle={'display': 'block'})],
                                    style={'width': '48%', 'float': 'right', 'display': 'inline-block'}
                                )
                            ])
                        ])
                    ]
                    ),
            dcc.Tab(
                label='Load profile',
                children=[
                    html.Div([
                        html.Div([
                            html.Div([
                                html.H4(children="Generator Selection",
                                        className="subtitle padded", style={'font-family': 'Arial'}),
                                dcc.Checklist(
                                    id='load_profile_checklist',
                                    options=[{
                                        'label': c[0] + ' ' + c[1],
                                        'value': str(('Generation',) + c)} for c in
                                        time_series_df.loc['Generation'].index],
                                    labelStyle={'display': 'block'})],
                                style={'width': '85%', 'display': 'inline-block'})],
                            style={'width': '16%', 'display': 'inline-block',
                                   'vertical-align': 'top', 'marginTop': '40px', 'marginLeft': '20px'}),
                        dcc.Graph(
                            id='load_profile',
                            figure=go.Figure(
                                data=[],
                                layout=go.Layout(
                                    title="Load profile",
                                    xaxis=dict(
                                        title='h',
                                        categoryorder='category descending'),
                                    yaxis=dict(
                                        title='kW',
                                        rangemode='tozero'),
                                    barmode='stack',
                                    legend=dict(
                                        orientation='h',
                                        bgcolor='rgba(255, 255, 255, 0)',
                                        bordercolor='rgba(255, 255, 255, 0)'),
                                    paper_bgcolor='rgba(255, 255, 255, 255)',
                                    plot_bgcolor='#f7f7f7')),
                            style={'width': '80%', 'display': 'inline-block'})
                    ])
                ]
            ),

        app.title = 'Result comparison'
        app.layout = html.Div([
            html.Div([
                html.H2(["PtX-Results"], className="subtitle padded", style={'font-family': 'Arial'}),
                html.Div([
                    html.Div([
                        'Select Case',
                        dcc.Dropdown(
                            className='Cases',
                            id='case',
                            options=[{'label': str(i), 'value': str(i)} for i in [*results_per_case.keys()]])
                        ])
                    ])
                ]),
            dcc.Tabs([
                dcc.Tab(label='Overview Results',
                        children=[
                            html.Div([
                                html.H2(
                                    ["Results"],
                                    className="subtitle padded",
                                    style={'font-family': 'Calibri'}),
                                dash_table.DataTable(
                                    id='overview_table',
                                    columns=[{"name": i, "id": i} for i in overview_table.columns],
                                    data=overview_table.to_dict('records'),
                                    style_as_list_view=True,
                                    style_cell_conditional=[
                                        {'if': {'column_id': 'Value'},
                                         'textAlign': 'left',
                                         'font-family': 'Calibri',
                                         'width': '10%'},
                                        {'if': {'column_id': ''},
                                         'textAlign': 'left',
                                         'font-family': 'Calibri',
                                         'width': '10%',
                                         'background-color': '#f5f2f2'}],
                                    style_data_conditional=[
                                        {'if': {'column_id': ''},
                                         'fontWeight': 'bold', }],
                                    style_header={
                                        'fontWeight': 'bold',
                                        'background-color': '#edebeb'}
                                )
                            ],
                                style={'width': '50%'}
                            )
                        ]
                        ),

                dcc.Tab(
                    label='Features',
                    children=[
                        html.Div([
                            html.Div([
                                html.Div([
                                    "Feature",
                                    dcc.Dropdown(
                                        className='Feature',
                                        id='feature',
                                        options=[{'label': str(i), 'value': str(i)} for i in entries])],
                                    style={'width': '48%', 'display': 'inline-block'}),
                            ]),
                            html.Div(
                                dcc.Graph(id='bar_plot')),
                        ]),
                    ]
                ),
                dcc.Tab(
                    label='Parameter Correlation',
                    children=[
                        html.Div([
                            html.Div([
                                html.Div([
                                    "X-axis",
                                    dcc.Dropdown(
                                        className='X-axis',
                                        id='x_axis',
                                        options=[{'label': str(i), 'value': str(i)} for i in entries])],
                                    style={'width': '48%', 'display': 'inline-block'}),
                                html.Div([
                                    "Y-axis",
                                    dcc.Dropdown(
                                        className='Y-axis',
                                        id='y_axis',
                                        options=[{'label': str(i), 'value': str(i)} for i in entries])],
                                    style={'width': '48%', 'float': 'right', 'display': 'inline-block'}),
                            ]),
                            html.Div([
                                dcc.RadioItems(
                                    className='Show Trendline',
                                    id='radioitem_trendline',
                                    options=[
                                        {'label': 'None', 'value': 'None'},
                                        {'label': 'Linear', 'value': 'Linear'},
                                        {'label': 'Logarithmic', 'value': 'Logarithmic'}
                                    ],
                                    value='None',
                                    labelStyle={'display': 'inline-block'}),
                            ]),
                            html.Div(
                                dcc.Graph(id='scatter_plot')),
                        ])
                    ]
                ),
                dcc.Tab(
                    label='Parameter Distribution',
                    children=[
                        html.Div([
                            html.Div([
                                html.Div([
                                    "parameter",
                                    dcc.Dropdown(
                                        className='Parameter',
                                        id='parameter',
                                        options=[{'label': str(i), 'value': str(i)} for i in entries])],
                                    style={'width': '48%', 'display': 'inline-block'}),
                            ]),
                            html.Div(
                                dcc.Graph(id='histogram_plot')),
                            html.Div(
                                dcc.Graph(id='pdf_plot'))
                        ])
                    ]
                )
            ])
        ])

        if True:

            @app.callback(
                [Output("overview_table", "data"), Output('overview_table', 'columns')],
                Input("case", "value")
            )
            def stuff(selected_case):

                table = results_per_case[selected_case]['assumptions_table']

                columns = [{"name": i, "id": i} for i in table.columns],
                data = table.to_dict('records')

                return data, columns

        if False:



            @app.callback(
                Output("assumptions", "table"),
                Output("overview_table", "table"),
                Output("conversion_components_table", "table"),
                Output("storage_components_table", "table"),
                Output("generation_table", "table"),
                Output("cost_share_figure", "figure"),
                Output("cost_structure_table", "table"),
                Output("commodity_table", "table"),
                Output("indicator_graphic", "figure"),
                Output("load_profile", "figure"),
                Output('yaxis_right', 'options'),
                Output('yaxis_left', 'options'),

                Input("case", "value"))
            def change_case(case):

                time_series_dataframe = results_per_case[case]['time_series_df']

                units = time_series_dataframe.iloc[:, 0]

                time_series_dataframe['Name'] = time_series_dataframe.index.tolist()
                for c in first_column_index:
                    if c in time_series_dataframe.index.get_level_values(0):
                        for i in time_series_dataframe.loc[c].index:
                            if str(i[0]) == 'nan':
                                name = str(i[1]) + ' ' + c
                            else:
                                name = str(i[1]) + ' ' + c + ' ' + str(i[0])

                            time_series_dataframe.at[merge_tuples(c, i), 'Name'] = name

                options = [{'label': str(i), 'value': str(i)} for i in units.unique()]

                return results_per_case[case]['assumptions_table'], results_per_case[case]['overview_table'],\
                    results_per_case[case]['conversion_components_table'], results_per_case[case]['storage_components_table'],\
                    results_per_case[case]['generation_table'], results_per_case[case]['cost_share_figure'],\
                    results_per_case[case]['cost_structure_dataframe'], results_per_case[case]['commodity_table'],\
                    time_series_df, {'options': options}, {'options': options}

            @app.callback(
                Output('indicator_graphic', 'figure'),
                Input('checklist_left', 'value'),
                Input('checklist_right', 'value'),
                Input('yaxis_main', 'value'),
                Input('yaxis_right', 'value'),
                Input("case", "value")
            )
            def update_graph(left_checklist, right_checklist, unit_left, unit_right, case):

                time_series_dataframe = results_per_case[case]['time_series_df']

                units = time_series_dataframe.iloc[:, 0]
                data = time_series_dataframe.iloc[:, 1:]

                # Dictionary to get index-triple from str(i)
                index = dict([(str(i), i) for i in time_series_dataframe.index])

                color_left = cycle(px.colors.qualitative.Plotly)
                color_right = cycle(px.colors.qualitative.Plotly[::-1])
                if unit_right is None:
                    data_graph = []
                    if left_checklist is not None:
                        for i in range(0, len(left_checklist)):
                            globals()['right_trace%s' % i] = \
                                go.Scatter(
                                    x=data.columns,
                                    y=data.loc[index[left_checklist[i]]],
                                    name=time_series_dataframe.at[index[left_checklist[i]], 'Name'] + ', '
                                        + units.loc[index[left_checklist[i]]],
                                    line=dict(color=next(color_left))
                                )
                            data_graph.append(globals()['right_trace%s' % i])
                    layout = go.Layout(
                        title="PtX-Model: Stream Visualization",
                        xaxis=dict(
                            title='h',
                            range=[0, data.shape[1] + 10]
                        ),
                        yaxis=dict(
                            title=unit_left,
                            rangemode="tozero",
                            showgrid=True
                        ),
                        legend=dict(
                            # orientation='h',
                            # x=0,
                            # y=-1,
                            bgcolor='rgba(255, 255, 255, 0)',
                            bordercolor='rgba(255, 255, 255, 0)'
                        ),
                        showlegend=True,
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='#f7f7f7'
                    )
                    fig = go.Figure(data=data_graph, layout=layout)
                    return fig
                elif unit_right is not None:
                    data_graph = []
                    for i in range(0, len(left_checklist)):
                        globals()['left_trace%s' % i] = go.Scatter(
                            x=data.columns,
                            y=data.loc[index[left_checklist[i]]],
                            name=time_series_dataframe.at[index[left_checklist[i]], 'Name'],
                            legendgroup='left',
                            legendgrouptitle=dict(
                                text=str(units.loc[index[left_checklist[i]]]) + ':'
                            ),
                            line=dict(color=next(color_left)),
                        )
                        data_graph.append(globals()['left_trace%s' % i])
                    if right_checklist is not None:
                        for i in range(0, len(right_checklist)):
                            globals()['right_trace%s' % i] = go.Scatter(
                                x=data.columns,
                                y=data.loc[index[right_checklist[i]]],
                                name=time_series_dataframe.at[index[right_checklist[i]], 'Name'],
                                yaxis='y2',
                                legendgroup='right',
                                legendgrouptitle=dict(
                                    text=str(units.loc[index[right_checklist[i]]]) + ':'
                                ),
                                line=dict(color=next(color_right)))
                            data_graph.append(globals()['right_trace%s' % i])
                    layout = go.Layout(
                        title="PtX-Model: Stream Visualization",
                        xaxis=dict(
                            title='h',
                            domain=[0, 0.95]
                        ),
                        yaxis=dict(
                            title=unit_left,
                            rangemode='tozero'
                        ),
                        yaxis2=dict(
                            title=unit_right,
                            rangemode='tozero',
                            overlaying='y',
                            side='right',
                        ),
                        legend=dict(
                            # orientation='h',
                            bgcolor='rgba(255, 255, 255, 0)',
                            bordercolor='rgba(255, 255, 255, 0)'
                        ),
                        legend_tracegroupgap=25,
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='#f7f7f7'
                    )
                    fig = go.Figure(data=data_graph, layout=layout)
                    return fig

            @app.callback(
                Output('load_profile', 'figure'),
                Output('load_profile', 'style'),
                Input('load_profile_checklist', 'value'),
                Input("case", "value"))
            def update_load_profile(check, case):

                time_series_dataframe = results_per_case[case]['time_series_df']

                units = time_series_dataframe.iloc[:, 0]
                data = time_series_dataframe.iloc[:, 1:]

                # Dictionary to get index-triple from str(i)
                index = dict([(str(i), i) for i in time_series_dataframe.index])

                load_profile_data = []
                if check is not None:
                    for i in range(0, len(check)):
                        cache = data.sort_values(axis=1, by=index[check[i]],
                                                 ignore_index=True, ascending=False).loc[index[check[i]]]
                        load_profile_data.append(
                            go.Bar(
                                x=cache.index,
                                y=cache,
                                name=time_series_dataframe.at[index[check[i]], 'Name'],
                                width=1,
                                marker=dict(line=dict(width=0))
                            )
                        )
                    layout = go.Layout(
                        title="Load profile",
                        xaxis=dict(
                            title='h',
                            categoryorder='category descending'
                        ),
                        yaxis=dict(
                            title='kW',
                            rangemode='tozero'
                        ),
                        barmode='stack',
                        legend=dict(
                            orientation='h',
                            bgcolor='rgba(255, 255, 255, 0)',
                            bordercolor='rgba(255, 255, 255, 0)'
                        ),
                        paper_bgcolor='rgba(255, 255, 255, 255)',
                        plot_bgcolor='#f7f7f7',
                    )
                    fig = go.Figure(data=load_profile_data, layout=layout)
                    style = {'width': '80%', 'display': 'inline-block'}
                    return fig, style

        @app.callback(
            Output("bar_plot", "figure"),
            Input("feature", "value"))
        def update_bar_chart(feature):

            sub_df = results_dataframe.copy()
            sub_df.sort_values(by=[feature], inplace=True)

            if 'Super Folder' not in results_dataframe.columns:

                sub_df['Case Name'] = sub_df.index

            else:

                index = []
                for c in results_dataframe.index:
                    index.append(results_dataframe.loc[c, 'Super Folder'] + ' ' + c)

                sub_df['Case Name'] = index

            fig = px.bar(sub_df, x='Case Name', y=feature)

            return fig

        @app.callback(
            Output("scatter_plot", "figure"),
            [Input("x_axis", "value"),
             Input("y_axis", "value"),
             Input('radioitem_trendline', 'value')])
        def update_scatter_chart(x_axis, y_axis, ri_value):

            if 'Super Folder' not in results_dataframe.columns:
                if ri_value == 'None':
                    fig = px.scatter(results_dataframe, x=x_axis, y=y_axis)
                elif ri_value == 'Linear':
                    fig = px.scatter(results_dataframe, x=x_axis, y=y_axis, trendline="ols")
                else:
                    fig = px.scatter(results_dataframe, x=x_axis, y=y_axis, trendline="ols", trendline_options=dict(log_x=True))

            else:
                if ri_value == 'None':
                    fig = px.scatter(results_dataframe, x=x_axis, y=y_axis, color='Super Folder')
                elif ri_value == 'Linear':
                    fig = px.scatter(results_dataframe, x=x_axis, y=y_axis, color='Super Folder', trendline="ols")
                else:
                    fig = px.scatter(results_dataframe, x=x_axis, y=y_axis, color='Super Folder', trendline="ols",
                                     trendline_options=dict(log_x=True))

            return fig

        @app.callback(
            [Output("histogram_plot", "figure"),
             Output("pdf_plot", "figure")],
            Input("parameter", "value"))
        def update_dist_charts(parameter):

            if 'Super Folder' in results_dataframe.columns:

                hist_data = []
                group_labels = []
                for f in results_dataframe['Super Folder'].unique():
                    ind = results_dataframe[results_dataframe['Super Folder'] == f].index
                    hist_data.append(results_dataframe.loc[ind, parameter].values)
                    group_labels.append(f)  # name of the dataset

                fig1 = px.histogram(results_dataframe, x=parameter, color='Super Folder', marginal="box", barmode='group')
                fig2 = ff.create_distplot(hist_data, group_labels, show_hist=False)

            else:
                hist_data = [results_dataframe[parameter].values]
                group_labels = [parameter]  # name of the dataset

                fig1 = px.histogram(results_dataframe[parameter], marginal="box")
                fig2 = ff.create_distplot(hist_data, group_labels, show_hist=False)

            return fig1, fig2

        def open_page():
            return webbrowser.open('http://127.0.0.1:8050/')

        Timer(1.0, open_page()).start(),
        app.run_server(debug=False, use_reloader=False)

    visualization_type = check_visualization_type()

    if visualization_type == 'single_results':

        name_scenario = path.split('/')[-2]

        assumptions_df, overview_df, components_df, cost_distribution_df, commodities_df, time_series_df, generation_df,\
            settings_df = load_data_single_result()

        monetary_unit_str, assumptions_table, assumptions_table_columns,\
            annual_production_value, annual_production_unit_str, \
            overview_table, conversion_components_table, conversion_components_table_columns, \
            storage_components_table, storage_components_table_columns, \
            cost_figure, cost_share_figure, cost_structure_dataframe, \
            generation_table, commodity_table = extract_data_single_results()

        create_browser_visualization_single_result()

    else:

        if visualization_type == 'multiple_results_with_single_scenario':

            name_scenario = ''
            first = True
            for string in path.split('/')[-2].split('_')[2:]:
                if first:
                    name_scenario += string
                    first = False
                else:
                    name_scenario += '_' + string

            folders_single, assumptions_single, results_overview_single, components_single, cost_distribution_single,\
                commodities_single, time_series_single, generation_single, settings_single, generation_profiles_single \
                = load_data_multiple_results_with_single_scenario()

            results_dataframe = extract_results_multiple_results_single_scenario()

            results_per_case = {}
            for f in folders_single:

                assumptions_df = assumptions_single[f]
                overview_df = results_overview_single[f]
                components_df = components_single[f]
                cost_distribution_df = cost_distribution_single[f]
                commodities_df = commodities_single[f]
                time_series_df = time_series_single[f]
                generation_df = generation_single[f]
                settings_df = settings_single[f]

                monetary_unit_str, assumptions_table, assumptions_table_columns, \
                    annual_production_value, annual_production_unit_str, \
                    overview_table, conversion_components_table, conversion_components_table_columns, \
                    storage_components_table, storage_components_table_columns, \
                    cost_figure, cost_share_figure, cost_structure_dataframe, \
                    generation_table, commodity_table = extract_data_single_results()

                results_per_case[f] = {'monetary_unit_str': monetary_unit_str,
                                       'assumptions_table': assumptions_table,
                                       'assumptions_table_columns': assumptions_table_columns,
                                       'annual_production_value': annual_production_value,
                                       'annual_production_unit_str': annual_production_unit_str,
                                       'overview_table': overview_table,
                                       'conversion_components_table': conversion_components_table,
                                       'conversion_components_table_columns': conversion_components_table_columns,
                                       'storage_components_table': storage_components_table,
                                       'storage_components_table_columns': storage_components_table_columns,
                                       'cost_figure': cost_figure,
                                       'cost_share_figure': cost_share_figure,
                                       'cost_structure_dataframe': cost_structure_dataframe,
                                       'generation_table': generation_table,
                                       'commodity_table': commodity_table,
                                       'time_series_df': time_series_df}

            create_web_page_multiple_results()

        else:

            name_scenario = ''
            first = True
            for string in path.split('/')[-2].split('_')[2:]:
                if first:
                    name_scenario += string
                    first = False
                else:
                    name_scenario += '_' + string

            folders_multiple, assumptions_multiple, results_overview_multiple, components_multiple,\
                cost_distribution_multiple, commodities_multiple, time_series_multiple, generation_multiple,\
                settings_multiple, generation_profiles_multiple = load_data_multiple_results_with_different_scenarios()

            results_dataframe = extract_results_multiple_results_different_scenarios()

            results_per_case = {}
            for f in folders_multiple:
                f1 = f[0]
                f2 = f[1]

                assumptions_df = assumptions_multiple[f1][f2]
                overview_df = results_overview_multiple[f1][f2]
                components_df = components_multiple[f1][f2]
                cost_distribution_df = cost_distribution_multiple[f1][f2]
                commodities_df = commodities_multiple[f1][f2]
                time_series_df = time_series_multiple[f1][f2]
                generation_df = generation_multiple[f1][f2]
                settings_df = settings_multiple[f1][f2]

                monetary_unit_str, assumptions_table, assumptions_table_columns, \
                    annual_production_value, annual_production_unit_str, \
                    overview_table, conversion_components_table, conversion_components_table_columns, \
                    storage_components_table, storage_components_table_columns, \
                    cost_figure, cost_share_figure, cost_structure_dataframe, \
                    generation_table, commodity_table = extract_data_single_results()

                results_per_case[f1 + '_' + f2] = {'monetary_unit_str': monetary_unit_str,
                                                   'assumptions_table': assumptions_table,
                                                   'assumptions_table_columns': assumptions_table_columns,
                                                   'annual_production_value': annual_production_value,
                                                   'annual_production_unit_str': annual_production_unit_str,
                                                   'overview_table': overview_table,
                                                   'conversion_components_table': conversion_components_table,
                                                   'conversion_components_table_columns': conversion_components_table_columns,
                                                   'storage_components_table': storage_components_table,
                                                   'storage_components_table_columns': storage_components_table_columns,
                                                   'cost_figure': cost_figure,
                                                   'cost_share_figure': cost_share_figure,
                                                   'cost_structure_dataframe': cost_structure_dataframe,
                                                   'generation_table': generation_table,
                                                   'commodity_table': commodity_table,
                                                   'time_series_df': time_series_df}

            create_web_page_multiple_results()


