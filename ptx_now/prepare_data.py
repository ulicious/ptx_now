import pandas as pd
idx = pd.IndexSlice


def load_data(year, path):

    # Load data files
    technical_assumptions = pd.read_excel(path + 'technical_assumptions.xlsx', index_col=list(range(4))).sort_index()

    financial_assumptions = pd.read_excel(path + 'financial_assumptions.xlsx', index_col=list(range(4))).sort_index()

    general_assumptions = pd.read_excel(path + 'general_assumptions.xlsx')

    conversion_factor = pd.read_excel(path + 'conversion_factor.xlsx')#, index_col=list(range(7))).sort_index()

    settings = pd.read_excel(path + 'settings.xlsx', index_col=list(range(2))).sort_index()

    allocations = pd.read_excel(path + 'allocations.xlsx', index_col=list(range(1))).sort_index()

    nice_names = pd.read_excel(path + 'nice_names.xlsx')

    stream_settings = pd.read_excel(path + 'stream_settings.xlsx', index_col=0)

    # Get assumptions from specific year
    technical_assumptions = technical_assumptions.loc[idx[:, :, :, :], year]
    technical_assumptions.loc[technical_assumptions.index.get_level_values('unit_numerator').str.contains('kW')] /= 1e3
    technical_assumptions.loc[technical_assumptions.index.get_level_values('unit_denominator').str.contains('kW')] *= 1e3

    financial_assumptions = financial_assumptions.loc[idx[:, :, :], year]
    financial_assumptions.loc[financial_assumptions.index.get_level_values('unit').str.contains('kW')] *= 1e3
    financial_assumptions.loc[financial_assumptions.index.get_level_values('unit').str.contains('d')] /= 24

    return technical_assumptions, financial_assumptions, general_assumptions, conversion_factor, settings, allocations,\
               nice_names, stream_settings


def calculate_investment(financial_assumptions):
    """ Investment value calculation """

    # ToDo: create tuples in dictionary
    capex_dict = {}
    lifetime_dict = {}
    capex_unit_dict = {}
    base_investment_dict = {}
    base_capacity_dict = {}
    max_capacity_dict = {}
    base_year_dict = {}
    economies_of_scale_dict = {}
    investment_parameter_dict = {}
    maintenance_dict = {}

    eos_components = financial_assumptions.loc[financial_assumptions.index.get_level_values('parameter')
        .str.contains('economies_of_scale')].copy().index.get_level_values('component').tolist()

    all_components = financial_assumptions.index.get_level_values('component').tolist()
    for c in set(all_components):
        c_df = financial_assumptions.loc[financial_assumptions.index.get_level_values('component') == c]

        if c not in eos_components:
            sub_df = c_df.loc[c_df.index.get_level_values('parameter').str.contains('capex')]
            capex_dict[c] = sub_df.values[0]

            capex_unit_dict[c] = sub_df.index.get_level_values('unit')[0]
        else:
            capex_dict[c] = financial_assumptions.loc[idx[c, :, 'capex', :]].values[0]
            base_investment_dict[c] = financial_assumptions.loc[idx[c, :, 'base_investment', :]].values[0]
            base_capacity_dict[c] = financial_assumptions.loc[idx[c, :, 'base_capacity', :]].values[0]
            max_capacity_dict[c] = financial_assumptions.loc[idx[c, :, 'max_capacity', :]].values[0]
            base_year_dict[c] = financial_assumptions.loc[idx[c, :, 'base_year', :]].values[0]
            economies_of_scale_dict[c] = financial_assumptions.loc[idx[c, :, 'economies_of_scale', :]].values[0]

            sub_df = c_df.loc[c_df.index.get_level_values('parameter').str.contains('base_investment')]
            capex_unit_dict[c] = sub_df.index.get_level_values('unit')[0]

        sub_df = c_df.loc[c_df.index.get_level_values('parameter').str.contains('lifetime')]
        lifetime_dict[c] = sub_df.values[0]

        sub_df = c_df.loc[c_df.index.get_level_values('parameter').str.contains('maintenance')]
        maintenance_dict[c] = sub_df.values[0]

    investment_parameter_dict['capex_dict'] = capex_dict
    investment_parameter_dict['capex_unit_dict'] = capex_unit_dict
    investment_parameter_dict['base_investment_dict'] = base_investment_dict
    investment_parameter_dict['base_capacity_dict'] = base_capacity_dict
    investment_parameter_dict['max_capacity_dict'] = max_capacity_dict
    investment_parameter_dict['base_year_dict'] = base_year_dict
    investment_parameter_dict['economies_of_scale_dict'] = economies_of_scale_dict
    investment_parameter_dict['lifetime_dict'] = lifetime_dict
    investment_parameter_dict['maintenance_dict'] = maintenance_dict

    return investment_parameter_dict, eos_components



