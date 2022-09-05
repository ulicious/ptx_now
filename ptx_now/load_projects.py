from components import ConversionComponent, StorageComponent, GenerationComponent
from commodity import Commodity

import pandas as pd


def load_project(pm_object, case_data):
    if isinstance(case_data, pd.DataFrame):
        if 'version' in case_data.columns:
            version = str(case_data.loc[0, 'version'])

            if version == '0.0.1':
                pm_object = load_001(pm_object, case_data)
            elif version == '0.0.2':
                pm_object = load_002(pm_object, case_data)
            elif version == '0.0.3':
                pm_object = load_003(pm_object, case_data)
            elif version == '0.0.4':
                pm_object = load_004(pm_object, case_data)
            elif version == '0.0.5':
                pm_object = load_005(pm_object, case_data)
            elif version == '0.0.6':
                pm_object = load_006(pm_object, case_data)
            elif version == '0.0.7':
                pm_object = load_007(pm_object, case_data)
            elif version == '0.0.8':
                pm_object = load_008(pm_object, case_data)

        else:  # Case where no version exists
            pm_object = load_001(pm_object, case_data)

    else:
        pm_object = load_009(pm_object, case_data)

    pm_object.check_commodity_data_needed()

    return pm_object


def load_009(pm_object, case_data):
    """ Set general parameters """

    for param in [*case_data['general_parameter'].keys()]:
        value = case_data['general_parameter'][param]['value']
        nice_name = case_data['general_parameter'][param]['nice_name']
        pm_object.set_general_parameter_value(param, value)
        pm_object.set_general_parameter(param)

        pm_object.set_nice_name(param, nice_name)
        pm_object.set_abbreviation(nice_name, param)

    pm_object.set_uses_representative_periods(case_data['representative_periods']['uses_representative_periods'])
    pm_object.set_representative_periods_length(case_data['representative_periods']['representative_periods_length'])
    pm_object.set_covered_period(case_data['representative_periods']['covered_period'])

    pm_object.set_monetary_unit(case_data['monetary_unit'])

    """ Add generation data """
    pm_object.set_single_or_multiple_profiles(case_data['data']['single_or_multiple_profiles'])
    pm_object.set_profile_data(case_data['data']['profile_data'])

    """Allocate components and parameters"""
    for component in [*case_data['component'].keys()]:

        name = case_data['component'][component]['name']
        nice_name = case_data['component'][component]['nice_name']
        capex = case_data['component'][component]['capex']
        lifetime = case_data['component'][component]['lifetime']
        maintenance = case_data['component'][component]['maintenance']
        final_unit = case_data['component'][component]['final']

        if case_data['component'][component]['component_type'] == 'conversion':

            min_p = case_data['component'][component]['min_p']
            max_p = case_data['component'][component]['max_p']
            scalable = case_data['component'][component]['scalable']
            capex_basis = case_data['component'][component]['capex_basis']
            base_investment = case_data['component'][component]['base_investment']
            base_capacity = case_data['component'][component]['base_capacity']
            economies_of_scale = case_data['component'][component]['economies_of_scale']
            max_capacity_economies_of_scale = case_data['component'][component]['max_capacity_economies_of_scale']
            number_parallel_units = case_data['component'][component]['number_parallel_units']

            ramp_up = case_data['component'][component]['ramp_up']
            ramp_down = case_data['component'][component]['ramp_down']

            shut_down_ability = case_data['component'][component]['shut_down_ability']
            start_up_time = case_data['component'][component]['start_up_time']
            start_up_costs = case_data['component'][component]['start_up_costs']

            hot_standby_ability = case_data['component'][component]['hot_standby_ability']
            hot_standby_demand = {
                case_data['component'][component]['hot_standby_commodity']:
                case_data['component'][component]['hot_standby_demand']}
            hot_standby_startup_time = case_data['component'][component]['hot_standby_startup_time']

            conversion_component = ConversionComponent(name=name, nice_name=nice_name, lifetime=lifetime,
                                                       maintenance=maintenance, base_investment=base_investment,
                                                       capex=capex, scalable=scalable,
                                                       capex_basis=capex_basis, base_capacity=base_capacity,
                                                       economies_of_scale=economies_of_scale,
                                                       max_capacity_economies_of_scale=max_capacity_economies_of_scale,
                                                       number_parallel_units=number_parallel_units,
                                                       min_p=min_p, max_p=max_p, ramp_up=ramp_up, ramp_down=ramp_down,
                                                       shut_down_ability=shut_down_ability,
                                                       start_up_time=start_up_time, start_up_costs=start_up_costs,
                                                       hot_standby_ability=hot_standby_ability,
                                                       hot_standby_demand=hot_standby_demand,
                                                       hot_standby_startup_time=hot_standby_startup_time,
                                                       final_unit=final_unit, custom_unit=False)

            pm_object.add_component(name, conversion_component)

        elif case_data['component'][component]['component_type'] == 'storage':

            min_soc = case_data['component'][component]['min_soc']
            max_soc = case_data['component'][component]['max_soc']
            initial_soc = case_data['component'][component]['initial_soc']
            charging_efficiency = case_data['component'][component]['charging_efficiency']
            discharging_efficiency = case_data['component'][component]['discharging_efficiency']
            leakage = case_data['component'][component]['leakage']
            ratio_capacity_p = case_data['component'][component]['ratio_capacity_p']

            storage_component = StorageComponent(name, nice_name, lifetime, maintenance, capex,
                                                 charging_efficiency, discharging_efficiency, min_soc, max_soc,
                                                 initial_soc, leakage=leakage, ratio_capacity_p=ratio_capacity_p,
                                                 final_unit=final_unit, custom_unit=False)
            pm_object.add_component(name, storage_component)

        elif case_data['component'][component]['component_type'] == 'generator':
            generated_commodity = case_data['component'][component]['generated_commodity']

            curtailment_possible = case_data['component'][component]['curtailment_possible']

            has_fixed_capacity = case_data['component'][component]['has_fixed_capacity']
            fixed_capacity = case_data['component'][component]['fixed_capacity']

            generator = GenerationComponent(name, nice_name, lifetime, maintenance, capex,
                                            generated_commodity=generated_commodity,
                                            curtailment_possible=curtailment_possible,
                                            has_fixed_capacity=has_fixed_capacity,
                                            fixed_capacity=fixed_capacity,
                                            final_unit=final_unit, custom_unit=False)
            pm_object.add_component(name, generator)

        pm_object.set_applied_parameter_for_component('taxes_and_insurance', name,
                                                      bool(case_data['component'][component]['taxes_and_insurance']))
        pm_object.set_applied_parameter_for_component('personnel_costs', name,
                                                      bool(case_data['component'][component]['personnel_costs']))
        pm_object.set_applied_parameter_for_component('overhead', name,
                                                      bool(case_data['component'][component]['overhead']))
        pm_object.set_applied_parameter_for_component('working_capital', name,
                                                      bool(case_data['component'][component]['working_capital']))

        pm_object.set_nice_name(name, nice_name)
        pm_object.set_abbreviation(nice_name, name)

    """ Conversions """
    for c in [*case_data['conversions'].keys()]:
        component = pm_object.get_component(c)
        for i in [*case_data['conversions'][c]['input'].keys()]:
            component.add_input(i, case_data['conversions'][c]['input'][i])

        for o in [*case_data['conversions'][c]['output'].keys()]:
            component.add_output(o, case_data['conversions'][c]['output'][o])

        component.set_main_input(case_data['conversions'][c]['main_input'])
        component.set_main_output(case_data['conversions'][c]['main_output'])

    """ Commodities """
    for c in [*case_data['commodity'].keys()]:
        name = case_data['commodity'][c]['name']
        nice_name = case_data['commodity'][c]['nice_name']
        commodity_unit = case_data['commodity'][c]['unit']

        available = case_data['commodity'][c]['available']
        emittable = case_data['commodity'][c]['emitted']
        purchasable = case_data['commodity'][c]['purchasable']
        saleable = case_data['commodity'][c]['saleable']
        demanded = case_data['commodity'][c]['demanded']
        total_demand = case_data['commodity'][c]['total_demand']
        final_commodity = case_data['commodity'][c]['final']

        # Purchasable commodities
        purchase_price_type = case_data['commodity'][c]['purchase_price_type']
        purchase_price = case_data['commodity'][c]['purchase_price']

        # Saleable commodities
        selling_price_type = case_data['commodity'][c]['selling_price_type']
        selling_price = case_data['commodity'][c]['selling_price']

        # Demand
        demand = case_data['commodity'][c]['demand']
        demand_type = case_data['commodity'][c]['demand_type']

        energy_content = case_data['commodity'][c]['energy_content']

        pm_object.set_nice_name(name, nice_name)
        pm_object.set_abbreviation(nice_name, name)

        commodity = Commodity(name, nice_name, commodity_unit, energy_content=energy_content,
                        final_commodity=final_commodity,
                        available=available, purchasable=purchasable, saleable=saleable, emittable=emittable,
                        demanded=demanded, total_demand=total_demand, demand_type=demand_type, demand=demand,
                        purchase_price=purchase_price, purchase_price_type=purchase_price_type,
                        sale_price=selling_price, sale_price_type=selling_price_type)
        pm_object.add_commodity(name, commodity)

    return pm_object


def load_008(pm_object, case_data):
    """ Set general parameters """

    for param in [*case_data['general_parameter'].keys()]:
        value = case_data['general_parameter'][param]['value']
        nice_name = case_data['general_parameter'][param]['nice_name']
        pm_object.set_general_parameter_value(param, value)
        pm_object.set_general_parameter(param)

        pm_object.set_nice_name(param, nice_name)
        pm_object.set_abbreviation(nice_name, param)

    pm_object.set_uses_representative_periods(case_data['representative_periods']['uses_representative_periods'])
    pm_object.set_representative_periods_length(case_data['representative_periods']['representative_periods_length'])
    pm_object.set_covered_period(case_data['representative_periods']['covered_period'])

    pm_object.set_monetary_unit(case_data['monetary_unit'])

    """ Add generation data """
    pm_object.set_single_or_multiple_profiles(case_data['generation_data']['single_or_multiple_profiles'])
    pm_object.set_profile_data(case_data['generation_data']['generation_data'])

    """ Add purchase/sale data """
    pm_object.set_single_or_multiple_commodity_profiles(case_data['commodity_data']['single_or_multiple_profiles'])
    pm_object.set_commodity_data(case_data['commodity_data']['commodity_data'])

    """Allocate components and parameters"""
    for component in [*case_data['component'].keys()]:

        name = case_data['component'][component]['name']
        nice_name = case_data['component'][component]['nice_name']
        capex = case_data['component'][component]['capex']
        lifetime = case_data['component'][component]['lifetime']
        maintenance = case_data['component'][component]['maintenance']
        final_unit = case_data['component'][component]['final']

        if case_data['component'][component]['component_type'] == 'conversion':

            min_p = case_data['component'][component]['min_p']
            max_p = case_data['component'][component]['max_p']
            scalable = case_data['component'][component]['scalable']
            capex_basis = case_data['component'][component]['capex_basis']
            base_investment = case_data['component'][component]['base_investment']
            base_capacity = case_data['component'][component]['base_capacity']
            economies_of_scale = case_data['component'][component]['economies_of_scale']
            max_capacity_economies_of_scale = case_data['component'][component]['max_capacity_economies_of_scale']
            number_parallel_units = case_data['component'][component]['number_parallel_units']

            ramp_up = case_data['component'][component]['ramp_up']
            ramp_down = case_data['component'][component]['ramp_down']

            shut_down_ability = case_data['component'][component]['shut_down_ability']
            start_up_time = case_data['component'][component]['start_up_time']
            start_up_costs = case_data['component'][component]['start_up_costs']

            hot_standby_ability = case_data['component'][component]['hot_standby_ability']
            hot_standby_demand = {
                case_data['component'][component]['hot_standby_commodity']:
                case_data['component'][component]['hot_standby_demand']}
            hot_standby_startup_time = case_data['component'][component]['hot_standby_startup_time']

            conversion_component = ConversionComponent(name=name, nice_name=nice_name, lifetime=lifetime,
                                                       maintenance=maintenance, base_investment=base_investment,
                                                       capex=capex, scalable=scalable,
                                                       capex_basis=capex_basis, base_capacity=base_capacity,
                                                       economies_of_scale=economies_of_scale,
                                                       max_capacity_economies_of_scale=max_capacity_economies_of_scale,
                                                       number_parallel_units=number_parallel_units,
                                                       min_p=min_p, max_p=max_p, ramp_up=ramp_up, ramp_down=ramp_down,
                                                       shut_down_ability=shut_down_ability,
                                                       start_up_time=start_up_time, start_up_costs=start_up_costs,
                                                       hot_standby_ability=hot_standby_ability,
                                                       hot_standby_demand=hot_standby_demand,
                                                       hot_standby_startup_time=hot_standby_startup_time,
                                                       final_unit=final_unit, custom_unit=False)

            pm_object.add_component(name, conversion_component)

        elif case_data['component'][component]['component_type'] == 'storage':

            min_soc = case_data['component'][component]['min_soc']
            max_soc = case_data['component'][component]['max_soc']
            initial_soc = case_data['component'][component]['initial_soc']
            charging_efficiency = case_data['component'][component]['charging_efficiency']
            discharging_efficiency = case_data['component'][component]['discharging_efficiency']
            leakage = case_data['component'][component]['leakage']
            ratio_capacity_p = case_data['component'][component]['ratio_capacity_p']

            storage_component = StorageComponent(name, nice_name, lifetime, maintenance, capex,
                                                 charging_efficiency, discharging_efficiency, min_soc, max_soc,
                                                 initial_soc, leakage=leakage, ratio_capacity_p=ratio_capacity_p,
                                                 final_unit=final_unit, custom_unit=False)
            pm_object.add_component(name, storage_component)

        elif case_data['component'][component]['component_type'] == 'generator':
            generated_commodity = case_data['component'][component]['generated_commodity']

            curtailment_possible = case_data['component'][component]['curtailment_possible']

            has_fixed_capacity = case_data['component'][component]['has_fixed_capacity']
            fixed_capacity = case_data['component'][component]['fixed_capacity']

            generator = GenerationComponent(name, nice_name, lifetime, maintenance, capex,
                                            generated_commodity=generated_commodity,
                                            curtailment_possible=curtailment_possible,
                                            has_fixed_capacity=has_fixed_capacity,
                                            fixed_capacity=fixed_capacity,
                                            final_unit=final_unit, custom_unit=False)
            pm_object.add_component(name, generator)

        pm_object.set_applied_parameter_for_component('taxes_and_insurance', name,
                                                      bool(case_data['component'][component]['taxes_and_insurance']))
        pm_object.set_applied_parameter_for_component('personnel_costs', name,
                                                      bool(case_data['component'][component]['personnel_costs']))
        pm_object.set_applied_parameter_for_component('overhead', name,
                                                      bool(case_data['component'][component]['overhead']))
        pm_object.set_applied_parameter_for_component('working_capital', name,
                                                      bool(case_data['component'][component]['working_capital']))

        pm_object.set_nice_name(name, nice_name)
        pm_object.set_abbreviation(nice_name, name)

    """ Conversions """
    for c in [*case_data['conversions'].keys()]:
        component = pm_object.get_component(c)
        for i in [*case_data['conversions'][c]['input'].keys()]:
            component.add_input(i, case_data['conversions'][c]['input'][i])

        for o in [*case_data['conversions'][c]['output'].keys()]:
            component.add_output(o, case_data['conversions'][c]['output'][o])

        component.set_main_input(case_data['conversions'][c]['main_input'])
        component.set_main_output(case_data['conversions'][c]['main_output'])

    """ Commodities """
    for c in [*case_data['commodity'].keys()]:
        name = case_data['commodity'][c]['name']
        nice_name = case_data['commodity'][c]['nice_name']
        commodity_unit = case_data['commodity'][c]['unit']

        available = case_data['commodity'][c]['available']
        emittable = case_data['commodity'][c]['emitted']
        purchasable = case_data['commodity'][c]['purchasable']
        saleable = case_data['commodity'][c]['saleable']
        demanded = case_data['commodity'][c]['demanded']
        total_demand = case_data['commodity'][c]['total_demand']
        final_commodity = case_data['commodity'][c]['final']

        # Purchasable commodities
        purchase_price_type = case_data['commodity'][c]['purchase_price_type']
        purchase_price = case_data['commodity'][c]['purchase_price']

        # Saleable commodities
        selling_price_type = case_data['commodity'][c]['selling_price_type']
        selling_price = case_data['commodity'][c]['selling_price']

        # Demand
        demand = case_data['commodity'][c]['demand']
        demand_type = case_data['commodity'][c]['demand_type']

        energy_content = case_data['commodity'][c]['energy_content']

        pm_object.set_nice_name(name, nice_name)
        pm_object.set_abbreviation(nice_name, name)

        commodity = Commodity(name, nice_name, commodity_unit, energy_content=energy_content,
                        final_commodity=final_commodity,
                        available=available, purchasable=purchasable, saleable=saleable, emittable=emittable,
                        demanded=demanded, total_demand=total_demand, demand_type=demand_type, demand=demand,
                        purchase_price=purchase_price, purchase_price_type=purchase_price_type,
                        sale_price=selling_price, sale_price_type=selling_price_type)
        pm_object.add_commodity(name, commodity)

    return pm_object


def load_007(pm_object, case_data):
    """ Set general parameters """
    general_parameter_df = case_data[case_data['type'] == 'general_parameter']

    for i in general_parameter_df.index:
        parameter = general_parameter_df.loc[i, 'parameter']
        value = general_parameter_df.loc[i, 'value']
        pm_object.set_general_parameter_value(parameter, value)
        pm_object.set_general_parameter(parameter)

    representative_periods_df = case_data[case_data['type'] == 'representative_periods']
    index = representative_periods_df.index[0]
    pm_object.set_uses_representative_periods(representative_periods_df.loc[index, 'representative_periods'])
    pm_object.set_representative_periods_length(representative_periods_df.loc[index, 'representative_periods_length'])
    pm_object.set_path_weighting(representative_periods_df.loc[index, 'path_weighting'])
    pm_object.set_covered_period(representative_periods_df.loc[index, 'covered_period'])

    monetary_unit_index = case_data[case_data['type'] == 'monetary_unit'].index
    monetary_unit = case_data.loc[monetary_unit_index, 'monetary_unit'].values[0]
    pm_object.set_monetary_unit(monetary_unit)

    """ Add generation data """
    generation_data_df = case_data[case_data['type'] == 'generation_data']
    index = generation_data_df.index[0]
    pm_object.set_single_or_multiple_profiles(generation_data_df.loc[index, 'single_profile'])
    pm_object.set_profile_data(generation_data_df.loc[index, 'generation_data'])

    """ Add purchase/sale data """
    commodity_data = case_data[case_data['type'] == 'commodity_data']
    index = commodity_data.index[0]
    pm_object.set_single_or_multiple_commodity_profiles(commodity_data.loc[index, 'single_profile'])
    pm_object.set_commodity_data(commodity_data.loc[index, 'commodity_data'])

    """Allocate components and parameters"""
    component_df = case_data[case_data['type'] == 'component']

    for i in component_df.index:
        name = component_df.loc[i, 'name']
        nice_name = component_df.loc[i, 'nice_name']
        capex = component_df.loc[i, 'capex']
        capex_basis = component_df.loc[i, 'capex_basis']
        lifetime = component_df.loc[i, 'lifetime']
        maintenance = component_df.loc[i, 'maintenance']
        final_unit = component_df.loc[i, 'final']

        if component_df.loc[i, 'component_type'] == 'conversion':

            min_p = component_df.loc[i, 'min_p']
            max_p = component_df.loc[i, 'max_p']
            scalable = component_df.loc[i, 'scalable']
            base_investment = component_df.loc[i, 'base_investment']
            base_capacity = component_df.loc[i, 'base_capacity']
            economies_of_scale = component_df.loc[i, 'economies_of_scale']
            max_capacity_economies_of_scale = component_df.loc[i, 'max_capacity_economies_of_scale']
            number_parallel_units = case_data.loc[i, 'number_parallel_units']

            ramp_up = component_df.loc[i, 'ramp_up']
            ramp_down = component_df.loc[i, 'ramp_down']

            shut_down_ability = component_df.loc[i, 'shut_down_ability']
            start_up_time = component_df.loc[i, 'start_up_time']
            if 'start_up_costs' in component_df.columns:
                start_up_costs = component_df.loc[i, 'start_up_costs']
            else:
                start_up_costs = 0

            hot_standby_ability = component_df.loc[i, 'hot_standby_ability']
            hot_standby_demand = {component_df.loc[i, 'hot_standby_commodity']: component_df.loc[i, 'hot_standby_demand']}
            hot_standby_startup_time = component_df.loc[i, 'hot_standby_startup_time']

            conversion_component = ConversionComponent(name=name, nice_name=nice_name, lifetime=lifetime,
                                                       maintenance=maintenance, base_investment=base_investment,
                                                       capex=capex, scalable=scalable,
                                                       capex_basis=capex_basis, base_capacity=base_capacity,
                                                       economies_of_scale=economies_of_scale,
                                                       max_capacity_economies_of_scale=max_capacity_economies_of_scale,
                                                       number_parallel_units=number_parallel_units,
                                                       min_p=min_p, max_p=max_p, ramp_up=ramp_up, ramp_down=ramp_down,
                                                       shut_down_ability=shut_down_ability,
                                                       start_up_time=start_up_time, start_up_costs=start_up_costs,
                                                       hot_standby_ability=hot_standby_ability,
                                                       hot_standby_demand=hot_standby_demand,
                                                       hot_standby_startup_time=hot_standby_startup_time,
                                                       final_unit=final_unit, custom_unit=False)

            pm_object.add_component(name, conversion_component)

        elif component_df.loc[i, 'component_type'] == 'storage':

            min_soc = case_data.loc[i, 'min_soc']
            max_soc = case_data.loc[i, 'max_soc']
            initial_soc = case_data.loc[i, 'initial_soc']
            charging_efficiency = case_data.loc[i, 'charging_efficiency']
            discharging_efficiency = case_data.loc[i, 'discharging_efficiency']
            leakage = case_data.loc[i, 'leakage']
            ratio_capacity_p = case_data.loc[i, 'ratio_capacity_p']

            storage_component = StorageComponent(name, nice_name, lifetime, maintenance, capex,
                                                 charging_efficiency, discharging_efficiency, min_soc, max_soc,
                                                 initial_soc, leakage=leakage, ratio_capacity_p=ratio_capacity_p,
                                                 final_unit=final_unit, custom_unit=False)
            pm_object.add_component(name, storage_component)

        elif component_df.loc[i, 'component_type'] == 'generator':
            generated_commodity = case_data.loc[i, 'generated_commodity']

            if 'curtailment_possible' in case_data.columns:
                curtailment_possible = case_data.loc[i, 'curtailment_possible']
            else:
                curtailment_possible = True

            generator = GenerationComponent(name, nice_name, lifetime, maintenance, capex,
                                            generated_commodity=generated_commodity,
                                            curtailment_possible=curtailment_possible,
                                            final_unit=final_unit, custom_unit=False)
            pm_object.add_component(name, generator)

        pm_object.set_applied_parameter_for_component('taxes_and_insurance', name,
                                                      bool(case_data.loc[i, 'taxes_and_insurance']))
        pm_object.set_applied_parameter_for_component('personnel_costs', name,
                                                      bool(case_data.loc[i, 'personnel_costs']))
        pm_object.set_applied_parameter_for_component('overhead', name,
                                                      bool(case_data.loc[i, 'overhead']))
        pm_object.set_applied_parameter_for_component('working_capital', name,
                                                      bool(case_data.loc[i, 'working_capital']))

    """ Conversions """
    main_conversions = case_data[case_data['type'] == 'main_conversion']
    if not main_conversions.empty:
        components = main_conversions.loc[:, 'component'].tolist()
        for c in components:
            component = pm_object.get_component(c)

            comp_index = main_conversions[main_conversions['component'] == c].index
            main_in_commodity = main_conversions.loc[comp_index, 'input_commodity'].values[0]
            main_out_commodity = main_conversions.loc[comp_index, 'output_commodity'].values[0]
            main_coefficient = float(main_conversions.loc[comp_index, 'coefficient'].values[0])

            component.add_input(main_in_commodity, 1)
            component.set_main_input(main_in_commodity)
            component.add_output(main_out_commodity, main_coefficient)
            component.set_main_output(main_out_commodity)

            side_conversions = case_data[(case_data['type'] == 'side_conversion') & (case_data['component'] == c)]
            for i in side_conversions.index:
                in_commodity = side_conversions.loc[i, 'input_commodity']
                out_commodity = side_conversions.loc[i, 'output_commodity']
                coefficient = float(side_conversions.loc[i, 'coefficient'])

                if in_commodity == main_in_commodity:
                    component.add_output(out_commodity, coefficient)
                else:
                    component.add_input(in_commodity, round(main_coefficient / coefficient, 3))
    else:
        inputs_index = case_data[case_data['type'] == 'input'].index
        for i in inputs_index:
            component = pm_object.get_component(case_data.loc[i, 'component'])
            component.add_input(case_data.loc[i, 'input_commodity'], case_data.loc[i, 'coefficient'])

            if case_data.loc[i, 'main_input']:
                component.set_main_input(case_data.loc[i, 'input_commodity'])

        outputs_index = case_data[case_data['type'] == 'output'].index
        for o in outputs_index:
            component = pm_object.get_component(case_data.loc[o, 'component'])
            component.add_output(case_data.loc[o, 'output_commodity'], case_data.loc[o, 'coefficient'])

            if case_data.loc[o, 'main_output']:
                component.set_main_output(case_data.loc[o, 'output_commodity'])

    """ Commodities """
    commodities = case_data[case_data['type'] == 'commodity']
    for i in commodities.index:
        abbreviation = case_data.loc[i, 'name']
        nice_name = case_data.loc[i, 'nice_name']
        commodity_unit = case_data.loc[i, 'unit']

        available = case_data.loc[i, 'available']
        emittable = case_data.loc[i, 'emitted']
        purchasable = case_data.loc[i, 'purchasable']
        saleable = case_data.loc[i, 'saleable']
        demanded = case_data.loc[i, 'demanded']
        total_demand = case_data.loc[i, 'total_demand']
        final_commodity = case_data.loc[i, 'final']

        # Purchasable commodities
        purchase_price_type = case_data.loc[i, 'purchase_price_type']
        purchase_price = case_data.loc[i, 'purchase_price']

        # Saleable commodities
        selling_price_type = case_data.loc[i, 'selling_price_type']
        selling_price = case_data.loc[i, 'selling_price']

        # Demand
        demand = case_data.loc[i, 'demand']

        if 'energy_content' in case_data.columns:
            energy_content = case_data.loc[i, 'energy_content']
        else:
            energy_content = None

        commodity = Commodity(abbreviation, nice_name, commodity_unit, energy_content=energy_content,
                        final_commodity=final_commodity,
                        available=available, purchasable=purchasable, saleable=saleable, emittable=emittable,
                        demanded=demanded, total_demand=total_demand,
                        purchase_price=purchase_price, purchase_price_type=purchase_price_type,
                        sale_price=selling_price, sale_price_type=selling_price_type, demand=demand)
        pm_object.add_commodity(abbreviation, commodity)

    """ Set nice names and abbreviations """
    name_df = case_data[case_data['type'] == 'names']

    for i in name_df.index:
        nice_name = name_df.loc[i, 'nice_name']
        abbreviation = name_df.loc[i, 'name']

        pm_object.set_nice_name(abbreviation, nice_name)
        pm_object.set_abbreviation(nice_name, abbreviation)

    return pm_object


def load_006(pm_object, case_data):
    """ Set general parameters """
    general_parameter_df = case_data[case_data['type'] == 'general_parameter']

    for i in general_parameter_df.index:
        parameter = general_parameter_df.loc[i, 'parameter']
        value = general_parameter_df.loc[i, 'value']
        pm_object.set_general_parameter_value(parameter, value)
        pm_object.set_general_parameter(parameter)

    representative_periods_df = case_data[case_data['type'] == 'representative_periods']
    index = representative_periods_df.index[0]
    pm_object.set_uses_representative_periods(representative_periods_df.loc[index, 'representative_periods'])
    pm_object.set_representative_periods_length(representative_periods_df.loc[index, 'representative_periods_length'])
    pm_object.set_path_weighting(representative_periods_df.loc[index, 'path_weighting'])
    pm_object.set_covered_period(representative_periods_df.loc[index, 'covered_period'])

    monetary_unit_index = case_data[case_data['type'] == 'monetary_unit'].index
    monetary_unit = case_data.loc[monetary_unit_index, 'monetary_unit'].values[0]
    pm_object.set_monetary_unit(monetary_unit)

    """ Add generation data """
    generation_data_df = case_data[case_data['type'] == 'generation_data']
    index = generation_data_df.index[0]
    pm_object.set_single_or_multiple_profiles(generation_data_df.loc[index, 'single_profile'])
    pm_object.set_profile_data(generation_data_df.loc[index, 'generation_data'])

    """ Add purchase/sale data """
    commodity_data = case_data[case_data['type'] == 'commodity_data']
    index = commodity_data.index[0]
    pm_object.set_single_or_multiple_commodity_profiles(commodity_data.loc[index, 'single_profile'])
    pm_object.set_commodity_data(commodity_data.loc[index, 'commodity_data'])

    """Allocate components and parameters"""
    component_df = case_data[case_data['type'] == 'component']

    for i in component_df.index:
        name = component_df.loc[i, 'name']
        nice_name = component_df.loc[i, 'nice_name']
        capex = component_df.loc[i, 'capex']
        capex_basis = component_df.loc[i, 'capex_basis']
        lifetime = component_df.loc[i, 'lifetime']
        maintenance = component_df.loc[i, 'maintenance']
        final_unit = component_df.loc[i, 'final']

        if component_df.loc[i, 'component_type'] == 'conversion':

            min_p = component_df.loc[i, 'min_p']
            max_p = component_df.loc[i, 'max_p']
            scalable = component_df.loc[i, 'scalable']
            base_investment = component_df.loc[i, 'base_investment']
            base_capacity = component_df.loc[i, 'base_capacity']
            economies_of_scale = component_df.loc[i, 'economies_of_scale']
            max_capacity_economies_of_scale = component_df.loc[i, 'max_capacity_economies_of_scale']
            number_parallel_units = case_data.loc[i, 'number_parallel_units']

            ramp_up = component_df.loc[i, 'ramp_up']
            ramp_down = component_df.loc[i, 'ramp_down']

            shut_down_ability = component_df.loc[i, 'shut_down_ability']
            start_up_time = component_df.loc[i, 'start_up_time']
            if 'start_up_costs' in component_df.columns:
                start_up_costs = component_df.loc[i, 'start_up_costs']
            else:
                start_up_costs = 0

            hot_standby_ability = component_df.loc[i, 'hot_standby_ability']
            hot_standby_demand = {component_df.loc[i, 'hot_standby_stream']: component_df.loc[i, 'hot_standby_demand']}
            hot_standby_startup_time = component_df.loc[i, 'hot_standby_startup_time']

            conversion_component = ConversionComponent(name=name, nice_name=nice_name, lifetime=lifetime,
                                                       maintenance=maintenance, base_investment=base_investment,
                                                       capex=capex, scalable=scalable,
                                                       capex_basis=capex_basis, base_capacity=base_capacity,
                                                       economies_of_scale=economies_of_scale,
                                                       max_capacity_economies_of_scale=max_capacity_economies_of_scale,
                                                       number_parallel_units=number_parallel_units,
                                                       min_p=min_p, max_p=max_p, ramp_up=ramp_up, ramp_down=ramp_down,
                                                       shut_down_ability=shut_down_ability,
                                                       start_up_time=start_up_time, start_up_costs=start_up_costs,
                                                       hot_standby_ability=hot_standby_ability,
                                                       hot_standby_demand=hot_standby_demand,
                                                       hot_standby_startup_time=hot_standby_startup_time,
                                                       final_unit=final_unit, custom_unit=False)

            pm_object.add_component(name, conversion_component)

        elif component_df.loc[i, 'component_type'] == 'storage':

            min_soc = case_data.loc[i, 'min_soc']
            max_soc = case_data.loc[i, 'max_soc']
            initial_soc = case_data.loc[i, 'initial_soc']
            charging_efficiency = case_data.loc[i, 'charging_efficiency']
            discharging_efficiency = case_data.loc[i, 'discharging_efficiency']
            leakage = case_data.loc[i, 'leakage']
            ratio_capacity_p = case_data.loc[i, 'ratio_capacity_p']

            storage_component = StorageComponent(name, nice_name, lifetime, maintenance, capex,
                                                 charging_efficiency, discharging_efficiency, min_soc, max_soc,
                                                 initial_soc, leakage=leakage, ratio_capacity_p=ratio_capacity_p,
                                                 final_unit=final_unit, custom_unit=False)
            pm_object.add_component(name, storage_component)

        elif component_df.loc[i, 'component_type'] == 'generator':
            generated_stream = case_data.loc[i, 'generated_stream']

            if 'curtailment_possible' in case_data.columns:
                curtailment_possible = case_data.loc[i, 'curtailment_possible']
            else:
                curtailment_possible = True

            generator = GenerationComponent(name, nice_name, lifetime, maintenance, capex,
                                            generated_commodity=generated_stream,
                                            curtailment_possible=curtailment_possible,
                                            final_unit=final_unit, custom_unit=False)
            pm_object.add_component(name, generator)

        pm_object.set_applied_parameter_for_component('taxes_and_insurance', name,
                                                      bool(case_data.loc[i, 'taxes_and_insurance']))
        pm_object.set_applied_parameter_for_component('personnel_costs', name,
                                                      bool(case_data.loc[i, 'personnel_costs']))
        pm_object.set_applied_parameter_for_component('overhead', name,
                                                      bool(case_data.loc[i, 'overhead']))
        pm_object.set_applied_parameter_for_component('working_capital', name,
                                                      bool(case_data.loc[i, 'working_capital']))

    """ Conversions """
    main_conversions = case_data[case_data['type'] == 'main_conversion']
    if not main_conversions.empty:
        components = main_conversions.loc[:, 'component'].tolist()
        for c in components:
            component = pm_object.get_component(c)

            comp_index = main_conversions[main_conversions['component'] == c].index
            main_in_stream = main_conversions.loc[comp_index, 'input_stream'].values[0]
            main_out_stream = main_conversions.loc[comp_index, 'output_stream'].values[0]
            main_coefficient = float(main_conversions.loc[comp_index, 'coefficient'].values[0])

            component.add_input(main_in_stream, 1)
            component.set_main_input(main_in_stream)
            component.add_output(main_out_stream, main_coefficient)
            component.set_main_output(main_out_stream)

            side_conversions = case_data[(case_data['type'] == 'side_conversion') & (case_data['component'] == c)]
            for i in side_conversions.index:
                in_stream = side_conversions.loc[i, 'input_stream']
                out_stream = side_conversions.loc[i, 'output_stream']
                coefficient = float(side_conversions.loc[i, 'coefficient'])

                if in_stream == main_in_stream:
                    component.add_output(out_stream, coefficient)
                else:
                    component.add_input(in_stream, round(main_coefficient / coefficient, 3))
    else:
        inputs_index = case_data[case_data['type'] == 'input'].index
        for i in inputs_index:
            component = pm_object.get_component(case_data.loc[i, 'component'])
            component.add_input(case_data.loc[i, 'input_stream'], case_data.loc[i, 'coefficient'])

            if case_data.loc[i, 'main_input']:
                component.set_main_input(case_data.loc[i, 'input_stream'])

        outputs_index = case_data[case_data['type'] == 'output'].index
        for o in outputs_index:
            component = pm_object.get_component(case_data.loc[o, 'component'])
            component.add_output(case_data.loc[o, 'output_stream'], case_data.loc[o, 'coefficient'])

            if case_data.loc[o, 'main_output']:
                component.set_main_output(case_data.loc[o, 'output_stream'])

    """ Streams """
    streams = case_data[case_data['type'] == 'stream']
    for i in streams.index:
        abbreviation = case_data.loc[i, 'name']
        nice_name = case_data.loc[i, 'nice_name']
        stream_unit = case_data.loc[i, 'unit']

        available = case_data.loc[i, 'available']
        emittable = case_data.loc[i, 'emitted']
        purchasable = case_data.loc[i, 'purchasable']
        saleable = case_data.loc[i, 'saleable']
        demanded = case_data.loc[i, 'demanded']
        total_demand = case_data.loc[i, 'total_demand']
        final_commodity = case_data.loc[i, 'final']

        # Purchasable streams
        purchase_price_type = case_data.loc[i, 'purchase_price_type']
        purchase_price = case_data.loc[i, 'purchase_price']

        # Saleable streams
        selling_price_type = case_data.loc[i, 'selling_price_type']
        selling_price = case_data.loc[i, 'selling_price']

        # Demand
        demand = case_data.loc[i, 'demand']

        if 'energy_content' in case_data.columns:
            energy_content = case_data.loc[i, 'energy_content']
        else:
            energy_content = None

        commodity = Commodity(abbreviation, nice_name, stream_unit, energy_content=energy_content,
                        final_commodity=final_commodity,
                        available=available, purchasable=purchasable, saleable=saleable, emittable=emittable,
                        demanded=demanded, total_demand=total_demand,
                        purchase_price=purchase_price, purchase_price_type=purchase_price_type,
                        sale_price=selling_price, sale_price_type=selling_price_type, demand=demand)
        pm_object.add_commodity(abbreviation, commodity)

    """ Set nice names and abbreviations """
    name_df = case_data[case_data['type'] == 'names']

    for i in name_df.index:
        nice_name = name_df.loc[i, 'nice_name']
        abbreviation = name_df.loc[i, 'name']

        pm_object.set_nice_name(abbreviation, nice_name)
        pm_object.set_abbreviation(nice_name, abbreviation)

    return pm_object


def load_005(pm_object, case_data):
    """ Set general parameters """
    general_parameter_df = case_data[case_data['type'] == 'general_parameter']

    for i in general_parameter_df.index:
        parameter = general_parameter_df.loc[i, 'parameter']
        value = general_parameter_df.loc[i, 'value']
        pm_object.set_general_parameter_value(parameter, value)
        pm_object.set_general_parameter(parameter)

    """ Add generation data """
    generation_data_df = case_data[case_data['type'] == 'generation_data']
    index = generation_data_df.index[0]
    pm_object.set_single_or_multiple_profiles(generation_data_df.loc[index, 'single_profile'])
    pm_object.set_profile_data(generation_data_df.loc[index, 'generation_data'])

    """ Add purchase/sale data """
    commodity_data = case_data[case_data['type'] == 'commodity_data']
    index = commodity_data.index[0]
    pm_object.set_single_or_multiple_commodity_profiles(commodity_data.loc[index, 'single_profile'])
    pm_object.set_commodity_data(commodity_data.loc[index, 'commodity_data'])

    """Allocate components and parameters"""
    component_df = case_data[case_data['type'] == 'component']

    for i in component_df.index:
        name = component_df.loc[i, 'name']
        nice_name = component_df.loc[i, 'nice_name']
        capex = component_df.loc[i, 'capex']
        capex_basis = component_df.loc[i, 'capex_basis']
        lifetime = component_df.loc[i, 'lifetime']
        maintenance = component_df.loc[i, 'maintenance']
        final_unit = component_df.loc[i, 'final']

        if component_df.loc[i, 'component_type'] == 'conversion':

            min_p = component_df.loc[i, 'min_p']
            max_p = component_df.loc[i, 'max_p']
            scalable = component_df.loc[i, 'scalable']
            base_investment = component_df.loc[i, 'base_investment']
            base_capacity = component_df.loc[i, 'base_capacity']
            economies_of_scale = component_df.loc[i, 'economies_of_scale']
            max_capacity_economies_of_scale = component_df.loc[i, 'max_capacity_economies_of_scale']
            number_parallel_units = component_df.loc[i, 'number_parallel_units']

            ramp_up = component_df.loc[i, 'ramp_up']
            ramp_down = component_df.loc[i, 'ramp_down']

            shut_down_ability = component_df.loc[i, 'shut_down_ability']
            start_up_time = component_df.loc[i, 'start_up_time']

            hot_standby_ability = component_df.loc[i, 'hot_standby_ability']
            hot_standby_demand = {component_df.loc[i, 'hot_standby_stream']: component_df.loc[i, 'hot_standby_demand']}
            hot_standby_startup_time = component_df.loc[i, 'hot_standby_startup_time']

            conversion_component = ConversionComponent(name=name, nice_name=nice_name, lifetime=lifetime,
                                                       maintenance=maintenance, base_investment=base_investment,
                                                       capex=capex, scalable=scalable,
                                                       capex_basis=capex_basis, base_capacity=base_capacity,
                                                       economies_of_scale=economies_of_scale,
                                                       max_capacity_economies_of_scale=max_capacity_economies_of_scale,
                                                       number_parallel_units=number_parallel_units,
                                                       min_p=min_p, max_p=max_p, ramp_up=ramp_up, ramp_down=ramp_down,
                                                       shut_down_ability=shut_down_ability,
                                                       start_up_time=start_up_time,
                                                       hot_standby_ability=hot_standby_ability,
                                                       hot_standby_demand=hot_standby_demand,
                                                       hot_standby_startup_time=hot_standby_startup_time,
                                                       final_unit=final_unit, custom_unit=False)

            pm_object.add_component(name, conversion_component)

        elif component_df.loc[i, 'component_type'] == 'storage':

            min_soc = case_data.loc[i, 'min_soc']
            max_soc = case_data.loc[i, 'max_soc']
            initial_soc = case_data.loc[i, 'initial_soc']
            charging_efficiency = case_data.loc[i, 'charging_efficiency']
            discharging_efficiency = case_data.loc[i, 'discharging_efficiency']
            leakage = case_data.loc[i, 'leakage']
            ratio_capacity_p = case_data.loc[i, 'ratio_capacity_p']

            storage_component = StorageComponent(name, nice_name, lifetime, maintenance, capex,
                                                 charging_efficiency, discharging_efficiency, min_soc, max_soc,
                                                 initial_soc, leakage=leakage, ratio_capacity_p=ratio_capacity_p,
                                                 final_unit=final_unit, custom_unit=False)
            pm_object.add_component(name, storage_component)

        elif component_df.loc[i, 'component_type'] == 'generator':
            generated_stream = case_data.loc[i, 'generated_stream']

            if 'curtailment_possible' in case_data.columns:
                curtailment_possible = case_data.loc[i, 'curtailment_possible']
            else:
                curtailment_possible = True

            generator = GenerationComponent(name, nice_name, lifetime, maintenance, capex,
                                            generated_commodity=generated_stream,
                                            curtailment_possible=curtailment_possible,
                                            final_unit=final_unit, custom_unit=False)
            pm_object.add_component(name, generator)

        pm_object.set_applied_parameter_for_component('taxes_and_insurance', name,
                                                      bool(case_data.loc[i, 'taxes_and_insurance']))
        pm_object.set_applied_parameter_for_component('personnel_costs', name,
                                                      bool(case_data.loc[i, 'personnel_costs']))
        pm_object.set_applied_parameter_for_component('overhead', name,
                                                      bool(case_data.loc[i, 'overhead']))
        pm_object.set_applied_parameter_for_component('working_capital', name,
                                                      bool(case_data.loc[i, 'working_capital']))

    """ Conversions """
    main_conversions = case_data[case_data['type'] == 'main_conversion']
    if not main_conversions.empty:
        components = main_conversions.loc[:, 'component'].tolist()
        for c in components:
            component = pm_object.get_component(c)

            comp_index = main_conversions[main_conversions['component'] == c].index
            main_in_stream = main_conversions.loc[comp_index, 'input_stream'].values[0]
            main_out_stream = main_conversions.loc[comp_index, 'output_stream'].values[0]
            main_coefficient = float(main_conversions.loc[comp_index, 'coefficient'].values[0])

            component.add_input(main_in_stream, 1)
            component.set_main_input(main_in_stream)
            component.add_output(main_out_stream, main_coefficient)
            component.set_main_output(main_out_stream)

            side_conversions = case_data[(case_data['type'] == 'side_conversion') & (case_data['component'] == c)]
            for i in side_conversions.index:
                in_stream = side_conversions.loc[i, 'input_stream']
                out_stream = side_conversions.loc[i, 'output_stream']
                coefficient = float(side_conversions.loc[i, 'coefficient'])

                if in_stream == main_in_stream:
                    component.add_output(out_stream, coefficient)
                else:
                    component.add_input(in_stream, round(main_coefficient / coefficient, 3))
    else:
        inputs_index = case_data[case_data['type'] == 'input'].index
        for i in inputs_index:
            component = pm_object.get_component(case_data.loc[i, 'component'])
            component.add_input(case_data.loc[i, 'input_stream'], case_data.loc[i, 'coefficient'])

            if case_data.loc[i, 'main_input']:
                component.set_main_input(case_data.loc[i, 'input_stream'])

        outputs_index = case_data[case_data['type'] == 'output'].index
        for o in outputs_index:
            component = pm_object.get_component(case_data.loc[o, 'component'])
            component.add_output(case_data.loc[o, 'output_stream'], case_data.loc[o, 'coefficient'])

            if case_data.loc[o, 'main_output']:
                component.set_main_output(case_data.loc[o, 'output_stream'])

    """ Streams """
    streams = case_data[case_data['type'] == 'stream']
    for i in streams.index:
        abbreviation = case_data.loc[i, 'name']
        nice_name = case_data.loc[i, 'nice_name']
        stream_unit = case_data.loc[i, 'unit']

        available = case_data.loc[i, 'available']
        emittable = case_data.loc[i, 'emitted']
        purchasable = case_data.loc[i, 'purchasable']
        saleable = case_data.loc[i, 'saleable']
        demanded = case_data.loc[i, 'demanded']
        total_demand = case_data.loc[i, 'total_demand']
        final_commodity = case_data.loc[i, 'final']

        # Purchasable streams
        purchase_price_type = case_data.loc[i, 'purchase_price_type']
        purchase_price = case_data.loc[i, 'purchase_price']

        # Saleable streams
        selling_price_type = case_data.loc[i, 'selling_price_type']
        selling_price = case_data.loc[i, 'selling_price']

        # Demand
        demand = case_data.loc[i, 'demand']

        if 'energy_content' in case_data.columns:
            energy_content = case_data.loc[i, 'energy_content']
        else:
            energy_content = None

        commodity = Commodity(abbreviation, nice_name, stream_unit, energy_content=energy_content,
                              final_commodity=final_commodity,
                              available=available, purchasable=purchasable, saleable=saleable, emittable=emittable,
                              demanded=demanded, total_demand=total_demand,
                              purchase_price=purchase_price, purchase_price_type=purchase_price_type,
                              sale_price=selling_price, sale_price_type=selling_price_type, demand=demand)
        pm_object.add_commodity(abbreviation, commodity)

    """ Set nice names and abbreviations """
    name_df = case_data[case_data['type'] == 'names']

    for i in name_df.index:
        nice_name = name_df.loc[i, 'nice_name']
        abbreviation = name_df.loc[i, 'name']

        pm_object.set_nice_name(abbreviation, nice_name)
        pm_object.set_abbreviation(nice_name, abbreviation)

    return pm_object


def load_004(pm_object, case_data):
    """ Set general parameters """
    general_parameter_df = case_data[case_data['type'] == 'general_parameter']

    for i in general_parameter_df.index:
        parameter = general_parameter_df.loc[i, 'parameter']
        value = general_parameter_df.loc[i, 'value']
        pm_object.set_general_parameter_value(parameter, value)
        pm_object.set_general_parameter(parameter)

    representative_periods_df = case_data[case_data['type'] == 'representative_weeks']
    index = representative_periods_df.index[0]
    pm_object.set_uses_representative_periods(representative_periods_df.loc[index, 'representative_weeks'])
    pm_object.set_path_weighting(representative_periods_df.loc[index, 'path_weighting'])
    pm_object.set_covered_period(representative_periods_df.loc[index, 'covered_period'])

    """Allocate components and parameters"""
    component_df = case_data[case_data['type'] == 'component']

    for i in component_df.index:
        name = component_df.loc[i, 'name']
        nice_name = component_df.loc[i, 'nice_name']
        capex = component_df.loc[i, 'capex']
        capex_basis = component_df.loc[i, 'capex_basis']
        lifetime = component_df.loc[i, 'lifetime']
        maintenance = component_df.loc[i, 'maintenance']
        final_unit = component_df.loc[i, 'final']

        if component_df.loc[i, 'component_type'] == 'conversion':

            min_p = component_df.loc[i, 'min_p']
            max_p = component_df.loc[i, 'max_p']
            scalable = component_df.loc[i, 'scalable']
            base_investment = component_df.loc[i, 'base_investment']
            base_capacity = component_df.loc[i, 'base_capacity']
            economies_of_scale = component_df.loc[i, 'economies_of_scale']
            max_capacity_economies_of_scale = component_df.loc[i, 'max_capacity_economies_of_scale']
            number_parallel_units = case_data.loc[i, 'number_parallel_units']
            ramp_up = case_data.loc[i, 'ramp_up']
            ramp_down = case_data.loc[i, 'ramp_down']
            shut_down_ability = case_data.loc[i, 'shut_down_ability']
            start_up_time = case_data.loc[i, 'start_up_time']
            hot_standby_ability = case_data.loc[i, 'hot_standby_ability']
            hot_standby_demand = {case_data.loc[i, 'hot_standby_stream']: case_data.loc[i, 'hot_standby_demand']}
            hot_standby_startup_time = case_data.loc[i, 'hot_standby_startup_time']

            conversion_component = ConversionComponent(name=name, nice_name=nice_name, lifetime=lifetime,
                                                       maintenance=maintenance, base_investment=base_investment,
                                                       capex=capex, scalable=scalable,
                                                       capex_basis=capex_basis, base_capacity=base_capacity,
                                                       economies_of_scale=economies_of_scale,
                                                       max_capacity_economies_of_scale=max_capacity_economies_of_scale,
                                                       number_parallel_units=number_parallel_units,
                                                       min_p=min_p, max_p=max_p, ramp_up=ramp_up, ramp_down=ramp_down,
                                                       shut_down_ability=shut_down_ability,
                                                       start_up_time=start_up_time,
                                                       hot_standby_ability=hot_standby_ability,
                                                       hot_standby_demand=hot_standby_demand,
                                                       hot_standby_startup_time=hot_standby_startup_time,
                                                       final_unit=final_unit, custom_unit=False)

            pm_object.add_component(name, conversion_component)

        elif component_df.loc[i, 'component_type'] == 'storage':

            min_soc = case_data.loc[i, 'min_soc']
            max_soc = case_data.loc[i, 'max_soc']
            initial_soc = case_data.loc[i, 'initial_soc']
            charging_efficiency = case_data.loc[i, 'charging_efficiency']
            discharging_efficiency = case_data.loc[i, 'discharging_efficiency']
            leakage = case_data.loc[i, 'leakage']
            ratio_capacity_p = case_data.loc[i, 'ratio_capacity_p']

            storage_component = StorageComponent(name, nice_name, lifetime, maintenance, capex,
                                                 charging_efficiency, discharging_efficiency, min_soc, max_soc,
                                                 initial_soc, leakage=leakage, ratio_capacity_p=ratio_capacity_p,
                                                 final_unit=final_unit, custom_unit=False)
            pm_object.add_component(name, storage_component)

        elif component_df.loc[i, 'component_type'] == 'generator':
            generated_stream = case_data.loc[i, 'generated_stream']

            if 'curtailment_possible' in case_data.columns:
                curtailment_possible = case_data.loc[i, 'curtailment_possible']
            else:
                curtailment_possible = True

            generator = GenerationComponent(name, nice_name, lifetime, maintenance, capex,
                                            generated_commodity=generated_stream,
                                            curtailment_possible=curtailment_possible,
                                            final_unit=final_unit, custom_unit=False)
            pm_object.add_component(name, generator)

        pm_object.set_applied_parameter_for_component('taxes_and_insurance', name,
                                                      bool(case_data.loc[i, 'taxes_and_insurance']))
        pm_object.set_applied_parameter_for_component('personnel_costs', name,
                                                      bool(case_data.loc[i, 'personnel_costs']))
        pm_object.set_applied_parameter_for_component('overhead', name,
                                                      bool(case_data.loc[i, 'overhead']))
        pm_object.set_applied_parameter_for_component('working_capital', name,
                                                      bool(case_data.loc[i, 'working_capital']))

    """ Conversions """
    main_conversions = case_data[case_data['type'] == 'main_conversion']
    if not main_conversions.empty:
        components = main_conversions.loc[:, 'component'].tolist()
        for c in components:
            component = pm_object.get_component(c)

            comp_index = main_conversions[main_conversions['component'] == c].index
            main_in_stream = main_conversions.loc[comp_index, 'input_stream'].values[0]
            main_out_stream = main_conversions.loc[comp_index, 'output_stream'].values[0]
            main_coefficient = float(main_conversions.loc[comp_index, 'coefficient'].values[0])

            component.add_input(main_in_stream, 1)
            component.set_main_input(main_in_stream)
            component.add_output(main_out_stream, main_coefficient)
            component.set_main_output(main_out_stream)

            side_conversions = case_data[(case_data['type'] == 'side_conversion') & (case_data['component'] == c)]
            for i in side_conversions.index:
                in_stream = side_conversions.loc[i, 'input_stream']
                out_stream = side_conversions.loc[i, 'output_stream']
                coefficient = float(side_conversions.loc[i, 'coefficient'])

                if in_stream == main_in_stream:
                    component.add_output(out_stream, coefficient)
                else:
                    component.add_input(in_stream, round(main_coefficient / coefficient, 3))
    else:
        inputs_index = case_data[case_data['type'] == 'input'].index
        for i in inputs_index:
            component = pm_object.get_component(case_data.loc[i, 'component'])
            component.add_input(case_data.loc[i, 'input_stream'], case_data.loc[i, 'coefficient'])

            if case_data.loc[i, 'main_input']:
                component.set_main_input(case_data.loc[i, 'input_stream'])

        outputs_index = case_data[case_data['type'] == 'output'].index
        for o in outputs_index:
            component = pm_object.get_component(case_data.loc[o, 'component'])
            component.add_output(case_data.loc[o, 'output_stream'], case_data.loc[o, 'coefficient'])

            if case_data.loc[o, 'main_output']:
                component.set_main_output(case_data.loc[o, 'output_stream'])

    """ Streams """
    streams = case_data[case_data['type'] == 'stream']
    for i in streams.index:
        abbreviation = case_data.loc[i, 'name']
        nice_name = case_data.loc[i, 'nice_name']
        stream_unit = case_data.loc[i, 'unit']

        available = case_data.loc[i, 'available']
        emittable = case_data.loc[i, 'emitted']
        purchasable = case_data.loc[i, 'purchasable']
        saleable = case_data.loc[i, 'saleable']
        demanded = case_data.loc[i, 'demanded']
        total_demand = case_data.loc[i, 'total_demand']
        final_commodity = case_data.loc[i, 'final']

        # Purchasable streams
        purchase_price_type = case_data.loc[i, 'purchase_price_type']
        purchase_price = case_data.loc[i, 'purchase_price']

        # Saleable streams
        selling_price_type = case_data.loc[i, 'selling_price_type']
        selling_price = case_data.loc[i, 'selling_price']

        # Demand
        demand = case_data.loc[i, 'demand']

        if 'energy_content' in case_data.columns:
            energy_content = case_data.loc[i, 'energy_content']
        else:
            energy_content = None

        commodity = Commodity(abbreviation, nice_name, stream_unit, energy_content=energy_content,
                        final_commodity=final_commodity,
                        available=available, purchasable=purchasable, saleable=saleable, emittable=emittable,
                        demanded=demanded, total_demand=total_demand,
                        purchase_price=purchase_price, purchase_price_type=purchase_price_type,
                        sale_price=selling_price, sale_price_type=selling_price_type, demand=demand)
        pm_object.add_commodity(abbreviation, commodity)

    """ Set nice names and abbreviations """
    name_df = case_data[case_data['type'] == 'names']

    for i in name_df.index:
        nice_name = name_df.loc[i, 'nice_name']
        abbreviation = name_df.loc[i, 'abbreviation']

        pm_object.set_nice_name(abbreviation, nice_name)
        pm_object.set_abbreviation(nice_name, abbreviation)

    return pm_object


def load_000(pm_object, case_data):
    """ Set general parameters """
    general_parameter_df = case_data[case_data['type'] == 'general_parameter']

    for i in general_parameter_df.index:
        parameter = general_parameter_df.loc[i, 'parameter']
        value = general_parameter_df.loc[i, 'value']
        if parameter != 'covered_period':
            pm_object.set_general_parameter_value(parameter, value)
            pm_object.set_general_parameter(parameter)
        else:
            pm_object.set_covered_period(value)

    """Allocate components and parameters"""
    component_df = case_data[case_data['type'] == 'component']

    for i in component_df.index:
        name = component_df.loc[i, 'name']
        nice_name = component_df.loc[i, 'nice_name']
        capex = component_df.loc[i, 'capex']
        lifetime = component_df.loc[i, 'lifetime']
        maintenance = component_df.loc[i, 'maintenance']
        final_unit = component_df.loc[i, 'final']

        if component_df.loc[i, 'component_type'] == 'conversion':

            min_p = component_df.loc[i, 'min_p']
            max_p = component_df.loc[i, 'max_p']
            scalable = component_df.loc[i, 'scalable']
            base_investment = component_df.loc[i, 'base_investment']
            base_capacity = component_df.loc[i, 'base_capacity']
            economies_of_scale = component_df.loc[i, 'economies_of_scale']
            max_capacity_economies_of_scale = component_df.loc[i, 'max_capacity_economies_of_scale']
            number_parallel_units = case_data.loc[i, 'number_parallel_units']
            ramp_up = case_data.loc[i, 'ramp_up']
            ramp_down = case_data.loc[i, 'ramp_down']
            shut_down_ability = case_data.loc[i, 'shut_down_ability']
            start_up_time = case_data.loc[i, 'start_up_time']

            conversion_component = ConversionComponent(name=name, nice_name=nice_name, lifetime=lifetime,
                                                       maintenance=maintenance, base_investment=base_investment,
                                                       capex=capex, scalable=scalable,
                                                       base_capacity=base_capacity,
                                                       economies_of_scale=economies_of_scale,
                                                       max_capacity_economies_of_scale=max_capacity_economies_of_scale,
                                                       number_parallel_units=number_parallel_units,
                                                       min_p=min_p, max_p=max_p, ramp_up=ramp_up,
                                                       shut_down_ability=shut_down_ability,
                                                       ramp_down=ramp_down,
                                                       start_up_time=start_up_time,
                                                       final_unit=final_unit, custom_unit=False)

            pm_object.add_component(name, conversion_component)

        elif component_df.loc[i, 'component_type'] == 'storage':

            min_soc = case_data.loc[i, 'min_soc']
            max_soc = case_data.loc[i, 'max_soc']
            initial_soc = case_data.loc[i, 'initial_soc']
            charging_efficiency = case_data.loc[i, 'charging_efficiency']
            discharging_efficiency = case_data.loc[i, 'discharging_efficiency']
            leakage = case_data.loc[i, 'leakage']
            ratio_capacity_p = case_data.loc[i, 'ratio_capacity_p']

            storage_component = StorageComponent(name, nice_name, lifetime, maintenance, capex,
                                                 charging_efficiency, discharging_efficiency, min_soc, max_soc,
                                                 initial_soc, leakage=leakage, ratio_capacity_p=ratio_capacity_p,
                                                 final_unit=final_unit, custom_unit=False)
            pm_object.add_component(name, storage_component)

        elif component_df.loc[i, 'component_type'] == 'generator':
            generated_stream = case_data.loc[i, 'generated_stream']

            generator = GenerationComponent(name, nice_name, lifetime, maintenance, capex,
                                            generated_commodity=generated_stream,
                                            final_unit=final_unit, custom_unit=False)
            pm_object.add_component(name, generator)

        try:
            pm_object.set_applied_parameter_for_component('taxes_and_insurance', name,
                                                     bool(case_data.loc[i, 'taxes_and_insurance']))
            pm_object.set_applied_parameter_for_component('personnel_costs', name,
                                                     bool(case_data.loc[i, 'personnel_costs']))
            pm_object.set_applied_parameter_for_component('overhead', name,
                                                     bool(case_data.loc[i, 'overhead']))
            pm_object.set_applied_parameter_for_component('working_capital', name,
                                                     bool(case_data.loc[i, 'working_capital']))

        except:
            for p in pm_object.get_general_parameters():
                pm_object.set_applied_parameter_for_component(p, name, True)

    """ Conversions """
    main_conversions = case_data[case_data['type'] == 'main_conversion']
    if not main_conversions.empty:
        components = main_conversions.loc[:, 'component'].tolist()
        for c in components:
            component = pm_object.get_component(c)

            comp_index = main_conversions[main_conversions['component'] == c].index
            main_in_stream = main_conversions.loc[comp_index, 'input_stream'].values[0]
            main_out_stream = main_conversions.loc[comp_index, 'output_stream'].values[0]
            main_coefficient = float(main_conversions.loc[comp_index, 'coefficient'].values[0])

            component.add_input(main_in_stream, 1)
            component.set_main_input(main_in_stream)
            component.add_output(main_out_stream, main_coefficient)
            component.set_main_output(main_out_stream)

            side_conversions = case_data[(case_data['type'] == 'side_conversion') & (case_data['component'] == c)]
            for i in side_conversions.index:
                in_stream = side_conversions.loc[i, 'input_stream']
                out_stream = side_conversions.loc[i, 'output_stream']
                coefficient = float(side_conversions.loc[i, 'coefficient'])

                if in_stream == main_in_stream:
                    component.add_output(out_stream, coefficient)
                else:
                    component.add_input(in_stream, round(main_coefficient / coefficient, 3))
    else:
        inputs_index = case_data[case_data['type'] == 'input'].index
        for i in inputs_index:
            component = pm_object.get_component(case_data.loc[i, 'component'])
            component.add_input(case_data.loc[i, 'input_stream'], case_data.loc[i, 'coefficient'])

            if case_data.loc[i, 'main_input']:
                component.set_main_input(case_data.loc[i, 'input_stream'])

        outputs_index = case_data[case_data['type'] == 'output'].index
        for o in outputs_index:
            component = pm_object.get_component(case_data.loc[o, 'component'])
            component.add_output(case_data.loc[o, 'output_stream'], case_data.loc[o, 'coefficient'])

            if case_data.loc[o, 'main_output']:
                component.set_main_output(case_data.loc[o, 'output_stream'])

    """ Streams """
    streams = case_data[case_data['type'] == 'stream']
    for i in streams.index:
        abbreviation = case_data.loc[i, 'name']
        nice_name = case_data.loc[i, 'nice_name']
        stream_unit = case_data.loc[i, 'unit']

        available = case_data.loc[i, 'available']
        emittable = case_data.loc[i, 'emitted']
        purchasable = case_data.loc[i, 'purchasable']
        saleable = case_data.loc[i, 'saleable']
        demanded = case_data.loc[i, 'demanded']
        total_demand = case_data.loc[i, 'total_demand']
        final_commodity = case_data.loc[i, 'final']

        # Purchasable streams
        purchase_price_type = case_data.loc[i, 'purchase_price_type']
        purchase_price = case_data.loc[i, 'purchase_price']

        # Saleable streams
        selling_price_type = case_data.loc[i, 'selling_price_type']
        selling_price = case_data.loc[i, 'selling_price']

        # Demand
        demand = case_data.loc[i, 'demand']

        commodity = Commodity(abbreviation, nice_name, stream_unit, final_commodity=final_commodity,
                        available=available, purchasable=purchasable, saleable=saleable, emittable=emittable,
                        demanded=demanded, total_demand=total_demand,
                        purchase_price=purchase_price, purchase_price_type=purchase_price_type,
                        sale_price=selling_price, sale_price_type=selling_price_type, demand=demand)
        pm_object.add_commodity(abbreviation, commodity)

    """ Set nice names and abbreviations """
    name_df = case_data[case_data['type'] == 'names']

    for i in name_df.index:
        nice_name = name_df.loc[i, 'nice_name']
        abbreviation = name_df.loc[i, 'abbreviation']

        pm_object.set_nice_name(abbreviation, nice_name)
        pm_object.set_abbreviation(nice_name, abbreviation)

    return pm_object


def load_001(pm_object, case_data):
    """ Set general parameters """
    general_parameter_df = case_data[case_data['type'] == 'general_parameter']

    for i in general_parameter_df.index:
        parameter = general_parameter_df.loc[i, 'parameter']
        value = general_parameter_df.loc[i, 'value']
        if parameter != 'covered_period':
            pm_object.set_general_parameter_value(parameter, value)
            pm_object.set_general_parameter(parameter)
        else:
            pm_object.set_covered_period(value)

    """Allocate components and parameters"""
    component_df = case_data[case_data['type'] == 'component']

    for i in component_df.index:
        name = component_df.loc[i, 'name']
        nice_name = component_df.loc[i, 'nice_name']
        capex = component_df.loc[i, 'capex']

        if 'capex_basis' in component_df.columns:
            capex_basis = component_df.loc[i, 'capex_basis']
        else:
            capex_basis = 'input'

        lifetime = component_df.loc[i, 'lifetime']
        maintenance = component_df.loc[i, 'maintenance']
        final_unit = component_df.loc[i, 'final']

        if component_df.loc[i, 'component_type'] == 'conversion':

            min_p = component_df.loc[i, 'min_p']
            max_p = component_df.loc[i, 'max_p']
            scalable = component_df.loc[i, 'scalable']
            base_investment = component_df.loc[i, 'base_investment']
            base_capacity = component_df.loc[i, 'base_capacity']
            economies_of_scale = component_df.loc[i, 'economies_of_scale']
            max_capacity_economies_of_scale = component_df.loc[i, 'max_capacity_economies_of_scale']
            number_parallel_units = case_data.loc[i, 'number_parallel_units']
            ramp_up = case_data.loc[i, 'ramp_up']
            ramp_down = case_data.loc[i, 'ramp_down']
            shut_down_ability = case_data.loc[i, 'shut_down_ability']
            start_up_time = case_data.loc[i, 'start_up_time']

            conversion_component = ConversionComponent(name=name, nice_name=nice_name, lifetime=lifetime,
                                                       maintenance=maintenance, base_investment=base_investment,
                                                       capex=capex, scalable=scalable,
                                                       capex_basis=capex_basis, base_capacity=base_capacity,
                                                       economies_of_scale=economies_of_scale,
                                                       max_capacity_economies_of_scale=max_capacity_economies_of_scale,
                                                       number_parallel_units=number_parallel_units,
                                                       min_p=min_p, max_p=max_p, ramp_up=ramp_up,
                                                       shut_down_ability=shut_down_ability,
                                                       ramp_down=ramp_down,
                                                       start_up_time=start_up_time,
                                                       final_unit=final_unit, custom_unit=False)

            pm_object.add_component(name, conversion_component)

        elif component_df.loc[i, 'component_type'] == 'storage':

            min_soc = case_data.loc[i, 'min_soc']
            max_soc = case_data.loc[i, 'max_soc']
            initial_soc = case_data.loc[i, 'initial_soc']
            charging_efficiency = case_data.loc[i, 'charging_efficiency']
            discharging_efficiency = case_data.loc[i, 'discharging_efficiency']
            leakage = case_data.loc[i, 'leakage']
            ratio_capacity_p = case_data.loc[i, 'ratio_capacity_p']

            storage_component = StorageComponent(name, nice_name, lifetime, maintenance, capex,
                                                 charging_efficiency, discharging_efficiency, min_soc, max_soc,
                                                 initial_soc, ratio_capacity_p=ratio_capacity_p,
                                                 final_unit=final_unit, custom_unit=False)
            pm_object.add_component(name, storage_component)

        elif component_df.loc[i, 'component_type'] == 'generator':
            generated_stream = case_data.loc[i, 'generated_stream']

            generator = GenerationComponent(name, nice_name, lifetime, maintenance, capex,
                                            generated_commodity=generated_stream,
                                            final_unit=final_unit, custom_unit=False)
            pm_object.add_component(name, generator)

        try:
            pm_object.set_applied_parameter_for_component('taxes_and_insurance', name,
                                                     bool(case_data.loc[i, 'taxes_and_insurance']))
            pm_object.set_applied_parameter_for_component('personnel_costs', name,
                                                     bool(case_data.loc[i, 'personnel_costs']))
            pm_object.set_applied_parameter_for_component('overhead', name,
                                                     bool(case_data.loc[i, 'overhead']))
            pm_object.set_applied_parameter_for_component('working_capital', name,
                                                     bool(case_data.loc[i, 'working_capital']))

        except:
            for p in pm_object.get_general_parameters():
                pm_object.set_applied_parameter_for_component(p, name, True)

    """ Conversions """
    main_conversions = case_data[case_data['type'] == 'main_conversion']
    if not main_conversions.empty:
        components = main_conversions.loc[:, 'component'].tolist()
        for c in components:
            component = pm_object.get_component(c)

            comp_index = main_conversions[main_conversions['component'] == c].index
            main_in_stream = main_conversions.loc[comp_index, 'input_stream'].values[0]
            main_out_stream = main_conversions.loc[comp_index, 'output_stream'].values[0]
            main_coefficient = float(main_conversions.loc[comp_index, 'coefficient'].values[0])

            component.add_input(main_in_stream, 1)
            component.set_main_input(main_in_stream)
            component.add_output(main_out_stream, main_coefficient)
            component.set_main_output(main_out_stream)

            side_conversions = case_data[(case_data['type'] == 'side_conversion') & (case_data['component'] == c)]
            for i in side_conversions.index:
                in_stream = side_conversions.loc[i, 'input_stream']
                out_stream = side_conversions.loc[i, 'output_stream']
                coefficient = float(side_conversions.loc[i, 'coefficient'])

                if in_stream == main_in_stream:
                    component.add_output(out_stream, coefficient)
                else:
                    component.add_input(in_stream, round(main_coefficient / coefficient, 3))
    else:
        inputs_index = case_data[case_data['type'] == 'input'].index
        for i in inputs_index:
            component = pm_object.get_component(case_data.loc[i, 'component'])
            component.add_input(case_data.loc[i, 'input_stream'], case_data.loc[i, 'coefficient'])

            if case_data.loc[i, 'main_input']:
                component.set_main_input(case_data.loc[i, 'input_stream'])

        outputs_index = case_data[case_data['type'] == 'output'].index
        for o in outputs_index:
            component = pm_object.get_component(case_data.loc[o, 'component'])
            component.add_output(case_data.loc[o, 'output_stream'], case_data.loc[o, 'coefficient'])

            if case_data.loc[o, 'main_output']:
                component.set_main_output(case_data.loc[o, 'output_stream'])

    """ Streams """
    streams = case_data[case_data['type'] == 'stream']
    for i in streams.index:
        abbreviation = case_data.loc[i, 'name']
        nice_name = case_data.loc[i, 'nice_name']
        stream_unit = case_data.loc[i, 'unit']

        available = case_data.loc[i, 'available']
        emittable = case_data.loc[i, 'emitted']
        purchasable = case_data.loc[i, 'purchasable']
        saleable = case_data.loc[i, 'saleable']
        demanded = case_data.loc[i, 'demanded']
        total_demand = case_data.loc[i, 'total_demand']
        final_commodity = case_data.loc[i, 'final']

        # Purchasable streams
        purchase_price_type = case_data.loc[i, 'purchase_price_type']
        purchase_price = case_data.loc[i, 'purchase_price']

        # Saleable streams
        selling_price_type = case_data.loc[i, 'selling_price_type']
        selling_price = case_data.loc[i, 'selling_price']

        # Demand
        demand = case_data.loc[i, 'demand']

        commodity = Commodity(abbreviation, nice_name, stream_unit, final_commodity=final_commodity,
                        available=available, purchasable=purchasable, saleable=saleable, emittable=emittable,
                        demanded=demanded, total_demand=total_demand,
                        purchase_price=purchase_price, purchase_price_type=purchase_price_type,
                        sale_price=selling_price, sale_price_type=selling_price_type, demand=demand)
        pm_object.add_commodity(abbreviation, commodity)

    """ Set nice names and abbreviations """
    name_df = case_data[case_data['type'] == 'names']

    for i in name_df.index:
        nice_name = name_df.loc[i, 'nice_name']
        abbreviation = name_df.loc[i, 'abbreviation']

        pm_object.set_nice_name(abbreviation, nice_name)
        pm_object.set_abbreviation(nice_name, abbreviation)

    return pm_object


def load_002(pm_object, case_data):
    """ Set general parameters """
    general_parameter_df = case_data[case_data['type'] == 'general_parameter']

    for i in general_parameter_df.index:
        parameter = general_parameter_df.loc[i, 'parameter']
        value = general_parameter_df.loc[i, 'value']
        if parameter != 'covered_period':
            pm_object.set_general_parameter_value(parameter, value)
            pm_object.set_general_parameter(parameter)
        else:
            pm_object.set_covered_period(value)

    """Allocate components and parameters"""
    component_df = case_data[case_data['type'] == 'component']

    for i in component_df.index:
        name = component_df.loc[i, 'name']
        nice_name = component_df.loc[i, 'nice_name']
        capex = component_df.loc[i, 'capex']
        capex_basis = component_df.loc[i, 'capex_basis']
        lifetime = component_df.loc[i, 'lifetime']
        maintenance = component_df.loc[i, 'maintenance']
        final_unit = component_df.loc[i, 'final']

        if component_df.loc[i, 'component_type'] == 'conversion':

            min_p = component_df.loc[i, 'min_p']
            max_p = component_df.loc[i, 'max_p']
            scalable = component_df.loc[i, 'scalable']
            base_investment = component_df.loc[i, 'base_investment']
            base_capacity = component_df.loc[i, 'base_capacity']
            economies_of_scale = component_df.loc[i, 'economies_of_scale']
            max_capacity_economies_of_scale = component_df.loc[i, 'max_capacity_economies_of_scale']
            number_parallel_units = case_data.loc[i, 'number_parallel_units']
            ramp_up = case_data.loc[i, 'ramp_up']
            ramp_down = case_data.loc[i, 'ramp_down']
            shut_down_ability = case_data.loc[i, 'shut_down_ability']
            start_up_time = case_data.loc[i, 'start_up_time']
            hot_standby_ability = case_data.loc[i, 'hot_standby_ability']
            hot_standby_demand = {case_data.loc[i, 'hot_standby_stream']: case_data.loc[i, 'hot_standby_demand']}
            hot_standby_startup_time = case_data.loc[i, 'hot_standby_startup_time']

            conversion_component = ConversionComponent(name=name, nice_name=nice_name, lifetime=lifetime,
                                                       maintenance=maintenance, base_investment=base_investment,
                                                       capex=capex, scalable=scalable,
                                                       capex_basis=capex_basis, base_capacity=base_capacity,
                                                       economies_of_scale=economies_of_scale,
                                                       max_capacity_economies_of_scale=max_capacity_economies_of_scale,
                                                       number_parallel_units=number_parallel_units,
                                                       min_p=min_p, max_p=max_p, ramp_up=ramp_up, ramp_down=ramp_down,
                                                       shut_down_ability=shut_down_ability,
                                                       start_up_time=start_up_time,
                                                       hot_standby_ability=hot_standby_ability,
                                                       hot_standby_demand=hot_standby_demand,
                                                       hot_standby_startup_time=hot_standby_startup_time,
                                                       final_unit=final_unit, custom_unit=False)

            pm_object.add_component(name, conversion_component)

        elif component_df.loc[i, 'component_type'] == 'storage':

            min_soc = case_data.loc[i, 'min_soc']
            max_soc = case_data.loc[i, 'max_soc']
            initial_soc = case_data.loc[i, 'initial_soc']
            charging_efficiency = case_data.loc[i, 'charging_efficiency']
            discharging_efficiency = case_data.loc[i, 'discharging_efficiency']
            leakage = case_data.loc[i, 'leakage']
            ratio_capacity_p = case_data.loc[i, 'ratio_capacity_p']

            storage_component = StorageComponent(name, nice_name, lifetime, maintenance, capex,
                                                 charging_efficiency, discharging_efficiency, min_soc, max_soc,
                                                 initial_soc, leakage=leakage, ratio_capacity_p=ratio_capacity_p,
                                                 final_unit=final_unit, custom_unit=False)
            pm_object.add_component(name, storage_component)

        elif component_df.loc[i, 'component_type'] == 'generator':
            generated_stream = case_data.loc[i, 'generated_stream']

            generator = GenerationComponent(name, nice_name, lifetime, maintenance, capex,
                                            generated_commodity=generated_stream,
                                            final_unit=final_unit, custom_unit=False)
            pm_object.add_component(name, generator)

        pm_object.set_applied_parameter_for_component('taxes_and_insurance', name,
                                                      bool(case_data.loc[i, 'taxes_and_insurance']))
        pm_object.set_applied_parameter_for_component('personnel_costs', name,
                                                      bool(case_data.loc[i, 'personnel_costs']))
        pm_object.set_applied_parameter_for_component('overhead', name,
                                                      bool(case_data.loc[i, 'overhead']))
        pm_object.set_applied_parameter_for_component('working_capital', name,
                                                      bool(case_data.loc[i, 'working_capital']))

    """ Conversions """
    main_conversions = case_data[case_data['type'] == 'main_conversion']
    if not main_conversions.empty:
        components = main_conversions.loc[:, 'component'].tolist()
        for c in components:
            component = pm_object.get_component(c)

            comp_index = main_conversions[main_conversions['component'] == c].index
            main_in_stream = main_conversions.loc[comp_index, 'input_stream'].values[0]
            main_out_stream = main_conversions.loc[comp_index, 'output_stream'].values[0]
            main_coefficient = float(main_conversions.loc[comp_index, 'coefficient'].values[0])

            component.add_input(main_in_stream, 1)
            component.set_main_input(main_in_stream)
            component.add_output(main_out_stream, main_coefficient)
            component.set_main_output(main_out_stream)

            side_conversions = case_data[(case_data['type'] == 'side_conversion') & (case_data['component'] == c)]
            for i in side_conversions.index:
                in_stream = side_conversions.loc[i, 'input_stream']
                out_stream = side_conversions.loc[i, 'output_stream']
                coefficient = float(side_conversions.loc[i, 'coefficient'])

                if in_stream == main_in_stream:
                    component.add_output(out_stream, coefficient)
                else:
                    component.add_input(in_stream, round(main_coefficient / coefficient, 3))
    else:
        inputs_index = case_data[case_data['type'] == 'input'].index
        for i in inputs_index:
            component = pm_object.get_component(case_data.loc[i, 'component'])
            component.add_input(case_data.loc[i, 'input_stream'], case_data.loc[i, 'coefficient'])

            if case_data.loc[i, 'main_input']:
                component.set_main_input(case_data.loc[i, 'input_stream'])

        outputs_index = case_data[case_data['type'] == 'output'].index
        for o in outputs_index:
            component = pm_object.get_component(case_data.loc[o, 'component'])
            component.add_output(case_data.loc[o, 'output_stream'], case_data.loc[o, 'coefficient'])

            if case_data.loc[o, 'main_output']:
                component.set_main_output(case_data.loc[o, 'output_stream'])

    """ Streams """
    streams = case_data[case_data['type'] == 'stream']
    for i in streams.index:
        abbreviation = case_data.loc[i, 'name']
        nice_name = case_data.loc[i, 'nice_name']
        stream_unit = case_data.loc[i, 'unit']

        available = case_data.loc[i, 'available']
        emittable = case_data.loc[i, 'emitted']
        purchasable = case_data.loc[i, 'purchasable']
        saleable = case_data.loc[i, 'saleable']
        demanded = case_data.loc[i, 'demanded']
        total_demand = case_data.loc[i, 'total_demand']
        final_commodity = case_data.loc[i, 'final']

        # Purchasable streams
        purchase_price_type = case_data.loc[i, 'purchase_price_type']
        purchase_price = case_data.loc[i, 'purchase_price']

        # Saleable streams
        selling_price_type = case_data.loc[i, 'selling_price_type']
        selling_price = case_data.loc[i, 'selling_price']

        # Demand
        demand = case_data.loc[i, 'demand']

        commodity = Commodity(abbreviation, nice_name, stream_unit, final_commodity=final_commodity,
                        available=available, purchasable=purchasable, saleable=saleable, emittable=emittable,
                        demanded=demanded, total_demand=total_demand,
                        purchase_price=purchase_price, purchase_price_type=purchase_price_type,
                        sale_price=selling_price, sale_price_type=selling_price_type, demand=demand)
        pm_object.add_commodity(abbreviation, commodity)

    """ Set nice names and abbreviations """
    name_df = case_data[case_data['type'] == 'names']

    for i in name_df.index:
        nice_name = name_df.loc[i, 'nice_name']
        abbreviation = name_df.loc[i, 'abbreviation']

        pm_object.set_nice_name(abbreviation, nice_name)
        pm_object.set_abbreviation(nice_name, abbreviation)

    return pm_object


def load_003(pm_object, case_data):
    """ Set general parameters """
    general_parameter_df = case_data[case_data['type'] == 'general_parameter']

    for i in general_parameter_df.index:
        parameter = general_parameter_df.loc[i, 'parameter']
        value = general_parameter_df.loc[i, 'value']
        pm_object.set_general_parameter_value(parameter, value)
        pm_object.set_general_parameter(parameter)

    representative_periods_df = case_data[case_data['type'] == 'representative_weeks']
    index = representative_periods_df.index[0]
    pm_object.set_uses_representative_periods(representative_periods_df.loc[index, 'representative_weeks'])
    pm_object.set_path_weighting(representative_periods_df.loc[index, 'path_weighting'])
    pm_object.set_covered_period(representative_periods_df.loc[index, 'covered_period'])

    """Allocate components and parameters"""
    component_df = case_data[case_data['type'] == 'component']

    for i in component_df.index:
        name = component_df.loc[i, 'name']
        nice_name = component_df.loc[i, 'nice_name']
        capex = component_df.loc[i, 'capex']
        capex_basis = component_df.loc[i, 'capex_basis']
        lifetime = component_df.loc[i, 'lifetime']
        maintenance = component_df.loc[i, 'maintenance']
        final_unit = component_df.loc[i, 'final']

        if component_df.loc[i, 'component_type'] == 'conversion':

            min_p = component_df.loc[i, 'min_p']
            max_p = component_df.loc[i, 'max_p']
            scalable = component_df.loc[i, 'scalable']
            base_investment = component_df.loc[i, 'base_investment']
            base_capacity = component_df.loc[i, 'base_capacity']
            economies_of_scale = component_df.loc[i, 'economies_of_scale']
            max_capacity_economies_of_scale = component_df.loc[i, 'max_capacity_economies_of_scale']
            number_parallel_units = case_data.loc[i, 'number_parallel_units']
            ramp_up = case_data.loc[i, 'ramp_up']
            ramp_down = case_data.loc[i, 'ramp_down']
            shut_down_ability = case_data.loc[i, 'shut_down_ability']
            start_up_time = case_data.loc[i, 'start_up_time']
            hot_standby_ability = case_data.loc[i, 'hot_standby_ability']
            hot_standby_demand = {case_data.loc[i, 'hot_standby_stream']: case_data.loc[i, 'hot_standby_demand']}
            hot_standby_startup_time = case_data.loc[i, 'hot_standby_startup_time']

            conversion_component = ConversionComponent(name=name, nice_name=nice_name, lifetime=lifetime,
                                                       maintenance=maintenance, base_investment=base_investment,
                                                       capex=capex, scalable=scalable,
                                                       capex_basis=capex_basis, base_capacity=base_capacity,
                                                       economies_of_scale=economies_of_scale,
                                                       max_capacity_economies_of_scale=max_capacity_economies_of_scale,
                                                       number_parallel_units=number_parallel_units,
                                                       min_p=min_p, max_p=max_p, ramp_up=ramp_up, ramp_down=ramp_down,
                                                       shut_down_ability=shut_down_ability,
                                                       start_up_time=start_up_time,
                                                       hot_standby_ability=hot_standby_ability,
                                                       hot_standby_demand=hot_standby_demand,
                                                       hot_standby_startup_time=hot_standby_startup_time,
                                                       final_unit=final_unit, custom_unit=False)

            pm_object.add_component(name, conversion_component)

        elif component_df.loc[i, 'component_type'] == 'storage':

            min_soc = case_data.loc[i, 'min_soc']
            max_soc = case_data.loc[i, 'max_soc']
            initial_soc = case_data.loc[i, 'initial_soc']
            charging_efficiency = case_data.loc[i, 'charging_efficiency']
            discharging_efficiency = case_data.loc[i, 'discharging_efficiency']
            leakage = case_data.loc[i, 'leakage']
            ratio_capacity_p = case_data.loc[i, 'ratio_capacity_p']

            storage_component = StorageComponent(name, nice_name, lifetime, maintenance, capex,
                                                 charging_efficiency, discharging_efficiency, min_soc, max_soc,
                                                 initial_soc, leakage=leakage, ratio_capacity_p=ratio_capacity_p,
                                                 final_unit=final_unit, custom_unit=False)
            pm_object.add_component(name, storage_component)

        elif component_df.loc[i, 'component_type'] == 'generator':
            generated_stream = case_data.loc[i, 'generated_stream']

            generator = GenerationComponent(name, nice_name, lifetime, maintenance, capex,
                                            generated_commodity=generated_stream,
                                            final_unit=final_unit, custom_unit=False)
            pm_object.add_component(name, generator)

        pm_object.set_applied_parameter_for_component('taxes_and_insurance', name,
                                                      bool(case_data.loc[i, 'taxes_and_insurance']))
        pm_object.set_applied_parameter_for_component('personnel_costs', name,
                                                      bool(case_data.loc[i, 'personnel_costs']))
        pm_object.set_applied_parameter_for_component('overhead', name,
                                                      bool(case_data.loc[i, 'overhead']))
        pm_object.set_applied_parameter_for_component('working_capital', name,
                                                      bool(case_data.loc[i, 'working_capital']))

    """ Conversions """
    main_conversions = case_data[case_data['type'] == 'main_conversion']
    if not main_conversions.empty:
        components = main_conversions.loc[:, 'component'].tolist()
        for c in components:
            component = pm_object.get_component(c)

            comp_index = main_conversions[main_conversions['component'] == c].index
            main_in_stream = main_conversions.loc[comp_index, 'input_stream'].values[0]
            main_out_stream = main_conversions.loc[comp_index, 'output_stream'].values[0]
            main_coefficient = float(main_conversions.loc[comp_index, 'coefficient'].values[0])

            component.add_input(main_in_stream, 1)
            component.set_main_input(main_in_stream)
            component.add_output(main_out_stream, main_coefficient)
            component.set_main_output(main_out_stream)

            side_conversions = case_data[(case_data['type'] == 'side_conversion') & (case_data['component'] == c)]
            for i in side_conversions.index:
                in_stream = side_conversions.loc[i, 'input_stream']
                out_stream = side_conversions.loc[i, 'output_stream']
                coefficient = float(side_conversions.loc[i, 'coefficient'])

                if in_stream == main_in_stream:
                    component.add_output(out_stream, coefficient)
                else:
                    component.add_input(in_stream, round(main_coefficient / coefficient, 3))
    else:
        inputs_index = case_data[case_data['type'] == 'input'].index
        for i in inputs_index:
            component = pm_object.get_component(case_data.loc[i, 'component'])
            component.add_input(case_data.loc[i, 'input_stream'], case_data.loc[i, 'coefficient'])

            if case_data.loc[i, 'main_input']:
                component.set_main_input(case_data.loc[i, 'input_stream'])

        outputs_index = case_data[case_data['type'] == 'output'].index
        for o in outputs_index:
            component = pm_object.get_component(case_data.loc[o, 'component'])
            component.add_output(case_data.loc[o, 'output_stream'], case_data.loc[o, 'coefficient'])

            if case_data.loc[o, 'main_output']:
                component.set_main_output(case_data.loc[o, 'output_stream'])

    """ Streams """
    streams = case_data[case_data['type'] == 'stream']
    for i in streams.index:
        abbreviation = case_data.loc[i, 'name']
        nice_name = case_data.loc[i, 'nice_name']
        stream_unit = case_data.loc[i, 'unit']

        available = case_data.loc[i, 'available']
        emittable = case_data.loc[i, 'emitted']
        purchasable = case_data.loc[i, 'purchasable']
        saleable = case_data.loc[i, 'saleable']
        demanded = case_data.loc[i, 'demanded']
        total_demand = case_data.loc[i, 'total_demand']
        final_commodity = case_data.loc[i, 'final']

        # Purchasable streams
        purchase_price_type = case_data.loc[i, 'purchase_price_type']
        purchase_price = case_data.loc[i, 'purchase_price']

        # Saleable streams
        selling_price_type = case_data.loc[i, 'selling_price_type']
        selling_price = case_data.loc[i, 'selling_price']

        # Demand
        demand = case_data.loc[i, 'demand']

        commodity = Commodity(abbreviation, nice_name, stream_unit, final_commodity=final_commodity,
                              available=available, purchasable=purchasable, saleable=saleable, emittable=emittable,
                              demanded=demanded, total_demand=total_demand,
                              purchase_price=purchase_price, purchase_price_type=purchase_price_type,
                              sale_price=selling_price, sale_price_type=selling_price_type, demand=demand)
        pm_object.add_commodity(abbreviation, commodity)

    """ Set nice names and abbreviations """
    name_df = case_data[case_data['type'] == 'names']

    for i in name_df.index:
        nice_name = name_df.loc[i, 'nice_name']
        abbreviation = name_df.loc[i, 'abbreviation']

        pm_object.set_nice_name(abbreviation, nice_name)
        pm_object.set_abbreviation(nice_name, abbreviation)

    return pm_object

