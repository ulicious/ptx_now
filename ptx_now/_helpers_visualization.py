import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output

import plotly.graph_objects as go
import plotly.express as px

import pandas as pd

from itertools import cycle

import webbrowser
from threading import Timer


def create_visualization(path):
    def create_browser_visualization():

        # prepare time series for graph plot
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
                            html.Div(
                                [
                                    html.H2(
                                        ["Assumptions"], className="subtitle padded", style={'font-family': 'Calibri'}

                                    ),
                                    dash_table.DataTable(
                                        id='assumptions',
                                        columns=[{"name": i, "id": i} for i in assumptions_table.columns],
                                        data=assumptions_table.to_dict('records'),
                                        style_as_list_view=True,
                                        style_cell_conditional=[
                                            {
                                                'if': {'column_id': assumptions_table_columns},
                                                'textAlign': 'left',
                                                'font-family': 'Calibri',
                                                'width': '10%'
                                            },
                                            {
                                                'if': {'column_id': ''},
                                                'textAlign': 'left',
                                                'font-family': 'Calibri',
                                                'width': '10%',
                                                'background-color': '#f5f2f2'
                                            }
                                        ],
                                        style_data_conditional=[
                                            {
                                                'if': {'column_id': ''},
                                                'fontWeight': 'bold',
                                            }
                                        ],
                                        style_header={
                                            'fontWeight': 'bold',
                                            'background-color': '#edebeb'
                                        },
                                    )
                                ],
                                #style={'width': '50%'}
                            ),
                        ]
                        ),
                dcc.Tab(label='Overview Results',
                        children=[
                            html.Div(
                                [
                                    html.H2(
                                        ["Results"], className="subtitle padded", style={'font-family': 'Calibri'}

                                    ),
                                    dash_table.DataTable(
                                        id='overview_table',
                                        columns=[{"name": i, "id": i} for i in overview_table.columns],
                                        data=overview_table.to_dict('records'),
                                        style_as_list_view=True,
                                        style_cell_conditional=[
                                            {
                                                'if': {'column_id': 'Value'},
                                                'textAlign': 'left',
                                                'font-family': 'Calibri',
                                                'width': '10%'
                                            },
                                            {
                                                'if': {'column_id': ''},
                                                'textAlign': 'left',
                                                'font-family': 'Calibri',
                                                'width': '10%',
                                                'background-color': '#f5f2f2'
                                            }
                                        ],
                                        style_data_conditional=[
                                            {
                                                'if': {'column_id': ''},
                                                'fontWeight': 'bold',
                                            }
                                        ],
                                        style_header={
                                            'fontWeight': 'bold',
                                            'background-color': '#edebeb'
                                        },
                                    )
                                ],
                                style={'width': '50%'}
                            ),
                        ]
                        ),
                dcc.Tab(label='Conversion Components',
                        children=[
                            html.Div(
                                [
                                    html.H2(
                                        ["Conversion Components"],
                                        className="subtitle padded",
                                        style={'font-family': 'Calibri'}
                                    ),
                                    dash_table.DataTable(
                                        id='conversion_components_table',
                                        columns=[{"name": i, "id": i} for i in conversion_components_table.columns],
                                        data=conversion_components_table.to_dict('records'),
                                        style_as_list_view=True,
                                        style_cell_conditional=[
                                            {
                                                'if': {'column_id': conversion_components_table_columns},
                                                'textAlign': 'left',
                                                'font-family': 'Calibri',
                                                'width': '10%'
                                            },
                                            {
                                                'if': {'column_id': ''},
                                                'textAlign': 'left',
                                                'font-family': 'Calibri',
                                                'width': '10%',
                                                'background-color': '#f5f2f2'
                                            }
                                        ],
                                        style_data_conditional=[
                                            {
                                                'if': {'column_id': ''},
                                                'fontWeight': 'bold',
                                            }
                                        ],
                                        style_header={
                                            'fontWeight': 'bold',
                                            'background-color': '#edebeb'
                                        },
                                    )
                                ],
                            ),
                        ]
                        ),
                dcc.Tab(label='Storage Components',
                        children=[
                            html.Div(
                                [
                                    html.H2(
                                        ["Storage Components"],
                                        className="subtitle padded",
                                        style={'font-family': 'Calibri'}
                                    ),
                                    dash_table.DataTable(
                                        id='storage_components_table',
                                        columns=[{"name": i, "id": i} for i in storage_components_table.columns],
                                        data=storage_components_table.to_dict('records'),
                                        style_as_list_view=True,
                                        style_cell_conditional=[
                                            {
                                                'if': {'column_id': storage_components_table_columns},
                                                'textAlign': 'left',
                                                'font-family': 'Calibri',
                                                'width': '10%'
                                            },
                                            {
                                                'if': {'column_id': ''},
                                                'textAlign': 'left',
                                                'font-family': 'Calibri',
                                                'width': '10%',
                                                'background-color': '#f5f2f2'
                                            }
                                        ],
                                        style_data_conditional=[
                                            {
                                                'if': {'column_id': ''},
                                                'fontWeight': 'bold',
                                            }
                                        ],
                                        style_header={
                                            'fontWeight': 'bold',
                                            'background-color': '#edebeb'
                                        },
                                    )
                                ],
                            ),
                        ]
                        ),
                dcc.Tab(label='Generation Components',
                        children=[
                            html.Div(
                                [
                                    html.H2(
                                        ["Generation Components"],
                                        className="subtitle padded",
                                        style={'font-family': 'Calibri'}
                                    ),
                                    dash_table.DataTable(
                                        id='generation_table',
                                        columns=[{"name": i, "id": i} for i in generation_table.columns],
                                        data=generation_table.to_dict('records'),
                                        style_as_list_view=True,
                                        style_cell_conditional=[
                                            {
                                                'if': {'column_id': ''},
                                                'textAlign': 'left',
                                                'font-family': 'Calibri',
                                                'width': '10%'
                                            },
                                            {
                                                'if': {'column_id': ''},
                                                'textAlign': 'left',
                                                'font-family': 'Calibri',
                                                'width': '10%',
                                                'background-color': '#f5f2f2'
                                            }
                                        ],
                                        style_data_conditional=[
                                            {
                                                'if': {'column_id': ''},
                                                'fontWeight': 'bold',
                                            }
                                        ],
                                        style_header={
                                            'fontWeight': 'bold',
                                            'background-color': '#edebeb'
                                        },
                                    )
                                ], style={'width': '100%'}
                            ),
                        ]
                        ),
                dcc.Tab(label='Streams',
                        children=[
                            html.Div(
                                [
                                    html.H2(
                                        ["Streams"],
                                        className="subtitle padded",
                                        style={'font-family': 'Calibri'}
                                    ),
                                    dash_table.DataTable(
                                        id='stream_table',
                                        columns=[{"name": i, "id": i} for i in stream_table.columns],
                                        data=stream_table.to_dict('records'),
                                        style_as_list_view=True,
                                        style_cell_conditional=[
                                            {
                                                'if': {'column_id': ''},
                                                'textAlign': 'left',
                                                'font-family': 'Calibri',
                                                'width': '10%'
                                            },
                                            {
                                                'if': {'column_id': ''},
                                                'textAlign': 'left',
                                                'font-family': 'Calibri',
                                                'width': '10%',
                                                'background-color': '#f5f2f2'
                                            }
                                        ],
                                        style_data_conditional=[
                                            {
                                                'if': {'column_id': ''},
                                                'fontWeight': 'bold',
                                            }
                                        ],
                                        style_header={
                                            'fontWeight': 'bold',
                                            'background-color': '#edebeb'
                                        },
                                    )
                                ],
                            ),
                        ]
                        ),
                dcc.Tab(label='Cost Distribution',
                        children=[
                            html.Div([
                                html.Div([
                                    html.Div(children=dcc.Graph(figure=cost_share_figure),
                                             style={
                                                 'height': '100px',
                                                 'margin-left': '10px',
                                                 'width': '45%',
                                                 'text-align': 'center',
                                                 'display': 'inline-block'
                                             }),

                                    html.Div(
                                        children=[
                                            dash_table.DataTable(
                                                id='cost_structure_table',
                                                columns=[{"name": i, "id": i} for i in cost_structure_dataframe.columns],
                                                data=cost_structure_dataframe.to_dict('records'),
                                                style_as_list_view=True,
                                                style_cell_conditional=[
                                                    {
                                                        'if': {'column_id': ''},
                                                        'textAlign': 'left',
                                                        'font-family': 'Calibri',
                                                        'width': '10%',
                                                        'background-color': '#f5f2f2'
                                                    }
                                                ],
                                                style_header={
                                                    'fontWeight': 'bold',
                                                    'background-color': '#edebeb'
                                                },
                                            )
                                        ],
                                        style={
                                            'height': '100px',
                                            'margin-left': '50px',
                                            'text-align': 'center',
                                            'width': '30%',
                                            'display': 'inline-block'
                                        })
                                ])
                            ])
                        ]),
                dcc.Tab(label='Graph',
                        children=[
                            html.Div([
                                html.Div(
                                    dcc.Graph(id='indicator_graphic')),
                                html.Div([
                                    html.Div([
                                        "left Y-axis",
                                        dcc.Dropdown(
                                            className='Y-axis left',
                                            id='yaxis_main',
                                            options=[{'label': str(i), 'value': str(i)} for i in
                                                     time_series_unit.unique()]
                                        ),
                                        dcc.Checklist(
                                            id='checklist_left',
                                            labelStyle={'display': 'block'}
                                        )
                                    ],
                                        style={'width': '48%', 'display': 'inline-block'}
                                    ),
                                    html.Div([
                                        "right Y-axis",
                                        dcc.Dropdown(
                                            className='Y-axis right',
                                            id='yaxis_right',
                                            options=[{'label': str(i), 'value': str(i)} for i in
                                                     time_series_unit.unique()]
                                        ),
                                        dcc.Checklist(
                                            id='checklist_right',
                                            labelStyle={'display': 'block'}
                                        )
                                    ],
                                        style={'width': '48%', 'float': 'right', 'display': 'inline-block'}),

                                ])
                            ],
                            )
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
                                                time_series.loc['Generation'].index],
                                            labelStyle={'display': 'block'}
                                        )
                                    ],
                                        style={'width': '85%', 'display': 'inline-block'}),
                                ],
                                    style={'width': '16%', 'display': 'inline-block',
                                           'vertical-align': 'top', 'marginTop': '40px', 'marginLeft': '20px'}
                                ),
                                dcc.Graph(id='load_profile',
                                          figure=go.Figure(
                                              data=[],
                                              layout=go.Layout(
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
                                          ),
                                          style={'width': '80%', 'display': 'inline-block'})
                            ])
                        ]
                        ),
            ]),
        ])

        @app.callback(
            Output('checklist_left', 'options'),
            Input('yaxis_main', 'value'),
        )
        def update_dropdown_left(selection):
            t = time_series_unit == str(selection)
            return [{'label': str(time_series.at[i, 'Name']), 'value': str(i)} for i in t.index[t.tolist()]]

        @app.callback(
            Output('checklist_right', 'options'),
            Input('yaxis_right', 'value'),
        )
        def update_dropdown_right(selection):
            t = time_series_unit == str(selection)
            return [{'label': str(time_series.at[i, 'Name']), 'value': str(i)} for i in t.index[t.tolist()]]

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
                                name=time_series.at[index_dictionary[left_checklist[i]], 'Name'] + ', '
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
                        name=time_series.at[index_dictionary[left_checklist[i]], 'Name'],
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
                            name=time_series.at[index_dictionary[right_checklist[i]], 'Name'],
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

        # @app.callback(
        #    Output('load_profile_checklist', 'options'),
        #    Input('load_profile_drop', 'value'),
        #  )
        # def update_dropdown_load_profile(selection):
        #    t = timeseries_unit == str(selection)
        #    return [{'label': str(timeseries.at[i,'Name']),'value': str(i)} for i in t.index[t.tolist()]]

        @app.callback(
            Output('load_profile', 'figure'),
            Output('load_profile', 'style'),
            # Input('load_profile_drop','value'),
            Input('load_profile_checklist', 'value')
        )
        def update_load_profile(check):
            load_profile_data = []
            # layout = go.Layout(title='Load profile', yaxis=dict(ticksuffix=''),
            #                   barmode='stack', colorway=px.colors.qualitative.Pastel)
            # load_profile_fig= go.Figure()
            if check is not None:
                for i in range(0, len(check)):
                    cache = time_series_data.sort_values(axis=1, by=index_dictionary[check[i]],
                                                        ignore_index=True, ascending=False).loc[
                        index_dictionary[check[i]]]
                    load_profile_data.append(
                        go.Bar(
                            x=cache.index,
                            y=cache,
                            name=time_series.at[index_dictionary[check[i]], 'Name'],
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

    def load_data():

        assumptions_file = pd.read_excel(path + '0_assumptions.xlsx', index_col=0)
        overview_file = pd.read_excel(path + '1_results_overview.xlsx', index_col=0)
        components_file = pd.read_excel(path + '2_components.xlsx', index_col=0)
        cost_distribution = pd.read_excel(path + '3_cost_distribution.xlsx', index_col=0)
        streams_file = pd.read_excel(path + '4_streams.xlsx', index_col=0)
        time_series_file = pd.read_excel(path + '5_time_series_streams.xlsx', index_col=(0, 1, 2))
        print(time_series_file)
        generation_file = pd.read_excel(path + '6_generation.xlsx', index_col=0)

        return assumptions_file, overview_file, components_file, cost_distribution,\
               streams_file, time_series_file, generation_file


    def create_overview_table():

        total_investment = "%.2f" % overview.loc['Total Investment'].values[0]
        total_fix_costs = "%.2f" % overview.loc['Total Fix Costs'].values[0]
        total_variable_costs = "%.2f" % overview.loc['Total Variable Costs'].values[0]
        annual_costs = "%.2f" % overview.loc['Annual Costs'].values[0]
        cost_per_unit = "%.2f" % overview.loc['Production Costs per Unit'].values[0]
        efficiency = "%.2f" % (overview.loc['Efficiency'].values[0] * 100)

        # Table Overview
        tab_overview = pd.DataFrame({
            '': ('Annual production', 'Total investment', 'Total Fix Costs', 'Total Variable Costs',
                 'Annual costs', 'Production cost per unit', 'Efficiency'),
            'Value':
                (str(round(annual_production)) + " " + annual_production_unit,
                 str(total_investment) + " €",
                 str(total_fix_costs) + " €",
                 str(total_variable_costs) + " €",
                 str(annual_costs) + " €",
                 str(cost_per_unit) + " €/" + annual_production_unit,
                 str(efficiency) + ' %')}
        )

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

        for component in components.index:

            # only consider conversion components
            if components.loc[component, 'Capacity Basis'] == 'input':
                component_list.append(component)

                capacity.append("%.3f" % components.loc[component, 'Capacity [input]'])
                capacity_unit.append(components.loc[component, 'Capacity Unit [input]'])
                CAPEX.append("%.2f" % components.loc[component, 'Investment [per input]'])
            elif components.loc[component, 'Capacity Basis'] == 'output':
                component_list.append(component)
                capacity.append("%.3f" % components.loc[component, 'Capacity [output]'])
                capacity_unit.append(components.loc[component, 'Capacity Unit [output]'])
                CAPEX.append("%.2f" % components.loc[component, 'Investment [per output]'])
            else:
                # All non-conversion components have no Capacity Basis
                continue

            total_investment.append("%.2f" % components.loc[component, 'Total Investment'])
            annuity.append("%.2f" % components.loc[component, 'Annuity'])
            maintenance.append("%.2f" % components.loc[component, 'Maintenance'])
            taxes_and_insurance.append("%.2f" % components.loc[component, 'Taxes and Insurance'])
            personnel_costs.append("%.2f" % components.loc[component, 'Personnel'])
            overhead.append("%.2f" % components.loc[component, 'Overhead'])
            working_capital.append("%.2f" % components.loc[component, 'Working Capital'])
            full_load_hours.append("%.2f" % components.loc[component, 'Full-load Hours'])

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
        value_relative = []
        for i in cost_distribution.index:

            matter_of_expense.append(i)

            value = cost_distribution.loc[i, 'Per Output']
            p_dict = {'name': i, 'width': [0.4], 'x': [''], 'y': [value]}
            value_absolute.append("%.2f" % value + ' €/' + annual_production_unit)
            if i != 'Total':
                bar_list.append(go.Bar(p_dict))

            value = cost_distribution.loc[i, '%']
            p_share_dict = {'name': i, 'width': [0.4], 'x': [''], 'y': [value * 100]}
            value_relative.append("%.2f" % (value * 100) + ' %')
            if i != 'Total':
                bar_share_list.append(go.Bar(p_share_dict))

        cost_structure_df = pd.DataFrame()
        cost_structure_df['Matter of Expense'] = matter_of_expense
        cost_structure_df['Absolute'] = value_absolute
        cost_structure_df['Relative'] = value_relative

        layout = go.Layout(title='Bar Chart', yaxis=dict(ticksuffix=' %'), barmode='stack',
                           colorway=px.colors.qualitative.Pastel)

        cost_fig = go.Figure(data=bar_list, layout=layout)
        cost_share_fig = go.Figure(data=bar_share_list, layout=layout)

        return cost_fig, cost_share_fig, cost_structure_df

    def create_assumptions_table():
        columns = ['Maintenance', 'Taxes and Insurance', 'Personnel', 'Overhead', 'Working Capital']
        assumptions_tab = pd.DataFrame(index=assumptions.index)
        assumptions_tab[''] = assumptions.index
        assumptions_tab['Capex Unit'] = assumptions['Capex Unit']

        for i in assumptions.index:

            assumptions_tab.loc[i, 'Capex'] = "%.2f" % assumptions.loc[i, 'Capex']

            for c in columns:
                assumptions_tab.loc[i, c] = "%.2f" % (assumptions.loc[i, c] * 100) + ' %'

        assumptions_tab['Lifetime'] = assumptions['Lifetime']

        return assumptions_tab

    def create_generation_table():
        generation_tab = pd.DataFrame(index=generation.index)
        for i in generation.index:
            generation_tab.loc[i, 'Generator'] = i
            generation_tab.loc[i, 'Generated Stream'] = generation.loc[i, 'Generated Stream']
            generation_tab.loc[i, 'Capacity'] = "%.2f" % generation.loc[i, 'Capacity']
            generation_tab.loc[i, 'Investment'] = "%.2f" % generation.loc[i, 'Investment']
            generation_tab.loc[i, 'Annuity'] = "%.2f" % generation.loc[i, 'Annuity']
            generation_tab.loc[i, 'Maintenance'] = "%.2f" % generation.loc[i, 'Maintenance']
            generation_tab.loc[i, 'T&I'] = "%.2f" % generation.loc[i, 'Taxes and Insurance']
            generation_tab.loc[i, 'Overhead'] = "%.2f" % generation.loc[i, 'Overhead']
            generation_tab.loc[i, 'Personnel'] = "%.2f" % generation.loc[i, 'Personnel']
            generation_tab.loc[i, 'Potential Generation'] = "%.0f" % generation.loc[i, 'Potential Generation']
            generation_tab.loc[i, 'Potential FLH'] = "%.2f" % generation.loc[i, 'Potential Full-load Hours']
            generation_tab.loc[i, 'LCOE pre Curtailment'] = "%.4f" % generation.loc[i, 'LCOE before Curtailment']
            generation_tab.loc[i, 'Actual Generation'] = "%.0f" % generation.loc[i, 'Actual Generation']
            generation_tab.loc[i, 'Actual FLH'] = "%.2f" % generation.loc[i, 'Actual Full-load Hours']
            generation_tab.loc[i, 'Curtailment'] = "%.0f" % generation.loc[i, 'Curtailment']
            generation_tab.loc[i, 'LCOE post Curtailment'] = "%.4f" % generation.loc[i, 'LCOE after Curtailment']

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
        for component in components.index:

            if component in generation.index:
                continue

            # only consider conversion components
            if not(components.loc[component, 'Capacity Basis'] == 'input'
                   or components.loc[component, 'Capacity Basis'] == 'output'):
                component_list.append(component)

                capacity.append("%.3f" % components.loc[component, 'Capacity [input]'])
                capacity_unit.append(components.loc[component, 'Capacity Unit [input]'])
                CAPEX.append("%.2f" % components.loc[component, 'Investment [per input]'])

                total_investment.append("%.2f" % components.loc[component, 'Total Investment'])
                annuity.append("%.2f" % components.loc[component, 'Annuity'])
                maintenance.append("%.2f" % components.loc[component, 'Maintenance'])
                taxes_and_insurance.append("%.2f" % components.loc[component, 'Taxes and Insurance'])
                personnel_costs.append("%.2f" % components.loc[component, 'Personnel'])
                overhead.append("%.2f" % components.loc[component, 'Overhead'])
                working_capital.append("%.2f" % components.loc[component, 'Working Capital'])

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

    def create_stream_table():
        stream_tab = pd.DataFrame(index=streams.index)

        for i in stream_tab.index:
            stream_tab.loc[i, 'Stream'] = i
            stream_tab.loc[i, 'Unit'] = streams.loc[i, 'unit']
            stream_tab.loc[i, 'Freely Available'] = "%.0f" % streams.loc[i, 'Available Stream']
            stream_tab.loc[i, 'Purchased'] = "%.0f" % streams.loc[i, 'Purchased Stream']
            stream_tab.loc[i, 'Sold'] = "%.0f" % streams.loc[i, 'Sold Stream']
            stream_tab.loc[i, 'Generated'] = "%.0f" % streams.loc[i, 'Generated Stream']
            stream_tab.loc[i, 'Stored'] = "%.0f" % streams.loc[i, 'Stored Stream']
            stream_tab.loc[i, 'From Conversion'] = "%.0f" % streams.loc[i, 'Conversed Stream']
            stream_tab.loc[i, 'Total Fixed Costs'] = "%.2f" % streams.loc[i, 'Total Fix Costs'] + ' €'
            stream_tab.loc[i, 'Total Variable Costs'] = "%.2f" % streams.loc[i, 'Total Variable Costs'] + ' €'
            stream_tab.loc[i, 'Intrinsic Costs per Unit'] = "%.2f" % streams.loc[i, 'Total Costs per Unit'] + ' €/' + streams.loc[i, 'unit']
            stream_tab.loc[i, 'Costs from other Streams per Unit'] = "%.2f" % (streams.loc[i, 'Production Costs per Unit']
                                                                                     - streams.loc[i, 'Total Costs per Unit']) + ' €/' + streams.loc[i, 'unit']
            stream_tab.loc[i, 'Total Costs per Unit'] = "%.2f" % streams.loc[i, 'Production Costs per Unit'] + ' €/' + streams.loc[i, 'unit']

        return stream_tab

    name_scenario = ''
    first = True
    for string in path.split('/')[-2].split('_')[2:]:
        if first:
            name_scenario += string
            first = False
        else:
            name_scenario += '_' + string

    assumptions, overview, components, cost_distribution, streams, time_series, generation = load_data()
    assumptions_table = create_assumptions_table()
    assumptions_table_columns = assumptions_table.columns[1:]

    create_assumptions_table()

    annual_production = overview.loc['Annual Production'].values[0]
    annual_production_unit = time_series.loc[['Demand']].loc[:, 'unit'].values[0].split(' / ')[0]

    overview_table = create_overview_table()

    conversion_components_table = create_conversion_components_table()
    conversion_components_table_columns = conversion_components_table.columns[1:]

    storage_components_table = create_storage_table()
    storage_components_table_columns = storage_components_table.columns[1:]

    cost_figure, cost_share_figure, cost_structure_dataframe = create_cost_structure_graph()

    generation_table = create_generation_table()

    stream_table = create_stream_table()

    create_browser_visualization()
