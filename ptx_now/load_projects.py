from components import ConversionComponent, StorageComponent, GenerationComponent
from stream import Stream


def load_setting(pm_object, case_data):
    if 'version' in case_data.columns:
        version = str(case_data.loc[0, 'version'])

        if version == '0.0.1':
            pm_object = load_001(pm_object, case_data)
        elif version == '0.0.2':
            pm_object = load_002(pm_object, case_data)
        elif version == '0.0.3':
            pm_object = load_003(pm_object, case_data)

    else:  # Case where no version exists
        pm_object = load_001(pm_object, case_data)

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
            limited = case_data.loc[i, 'limited_storage']
            storage_limiting_component = case_data.loc[i, 'storage_limiting_component']
            storage_limiting_component_ratio = case_data.loc[i, 'storage_limiting_component_ratio']

            storage_component = StorageComponent(name, nice_name, lifetime, maintenance, capex,
                                                 charging_efficiency, discharging_efficiency, min_soc, max_soc,
                                                 initial_soc, leakage=leakage, ratio_capacity_p=ratio_capacity_p,
                                                 storage_limiting_component=storage_limiting_component,
                                                 storage_limiting_component_ratio=storage_limiting_component_ratio,
                                                 final_unit=final_unit, custom_unit=False, limited_storage=limited)
            pm_object.add_component(name, storage_component)

        elif component_df.loc[i, 'component_type'] == 'generator':
            generated_stream = case_data.loc[i, 'generated_stream']
            generation_data = case_data.loc[i, 'generation_data']

            generator = GenerationComponent(name, nice_name, lifetime, maintenance, capex,
                                            generated_stream=generated_stream, generation_data=generation_data,
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
        final_stream = case_data.loc[i, 'final']

        # Purchasable streams
        purchase_price_type = case_data.loc[i, 'purchase_price_type']
        purchase_price = case_data.loc[i, 'purchase_price']

        # Saleable streams
        selling_price_type = case_data.loc[i, 'selling_price_type']
        selling_price = case_data.loc[i, 'selling_price']

        # Demand
        demand = case_data.loc[i, 'demand']

        stream = Stream(abbreviation, nice_name, stream_unit, final_stream=final_stream, custom_stream=False,
                        available=available, purchasable=purchasable, saleable=saleable, emittable=emittable,
                        demanded=demanded, total_demand=total_demand,
                        purchase_price=purchase_price, purchase_price_type=purchase_price_type,
                        sale_price=selling_price, sale_price_type=selling_price_type, demand=demand)
        pm_object.add_stream(abbreviation, stream)

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
            limited = case_data.loc[i, 'limited_storage']
            storage_limiting_component = case_data.loc[i, 'storage_limiting_component']
            storage_limiting_component_ratio = case_data.loc[i, 'storage_limiting_component_ratio']

            storage_component = StorageComponent(name, nice_name, lifetime, maintenance, capex,
                                                 charging_efficiency, discharging_efficiency, min_soc, max_soc,
                                                 initial_soc, ratio_capacity_p=ratio_capacity_p,
                                                 storage_limiting_component=storage_limiting_component,
                                                 storage_limiting_component_ratio=storage_limiting_component_ratio,
                                                 final_unit=final_unit, custom_unit=False, limited_storage=limited)
            pm_object.add_component(name, storage_component)

        elif component_df.loc[i, 'component_type'] == 'generator':
            generated_stream = case_data.loc[i, 'generated_stream']
            generation_data = case_data.loc[i, 'generation_data']

            generator = GenerationComponent(name, nice_name, lifetime, maintenance, capex,
                                            generated_stream=generated_stream, generation_data=generation_data,
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
        final_stream = case_data.loc[i, 'final']

        # Purchasable streams
        purchase_price_type = case_data.loc[i, 'purchase_price_type']
        purchase_price = case_data.loc[i, 'purchase_price']

        # Saleable streams
        selling_price_type = case_data.loc[i, 'selling_price_type']
        selling_price = case_data.loc[i, 'selling_price']

        # Demand
        demand = case_data.loc[i, 'demand']

        stream = Stream(abbreviation, nice_name, stream_unit, final_stream=final_stream, custom_stream=False,
                        available=available, purchasable=purchasable, saleable=saleable, emittable=emittable,
                        demanded=demanded, total_demand=total_demand,
                        purchase_price=purchase_price, purchase_price_type=purchase_price_type,
                        sale_price=selling_price, sale_price_type=selling_price_type, demand=demand)
        pm_object.add_stream(abbreviation, stream)

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
            limited = case_data.loc[i, 'limited_storage']
            storage_limiting_component = case_data.loc[i, 'storage_limiting_component']
            storage_limiting_component_ratio = case_data.loc[i, 'storage_limiting_component_ratio']

            storage_component = StorageComponent(name, nice_name, lifetime, maintenance, capex,
                                                 charging_efficiency, discharging_efficiency, min_soc, max_soc,
                                                 initial_soc, leakage=leakage, ratio_capacity_p=ratio_capacity_p,
                                                 storage_limiting_component=storage_limiting_component,
                                                 storage_limiting_component_ratio=storage_limiting_component_ratio,
                                                 final_unit=final_unit, custom_unit=False, limited_storage=limited)
            pm_object.add_component(name, storage_component)

        elif component_df.loc[i, 'component_type'] == 'generator':
            generated_stream = case_data.loc[i, 'generated_stream']
            generation_data = case_data.loc[i, 'generation_data']

            generator = GenerationComponent(name, nice_name, lifetime, maintenance, capex,
                                            generated_stream=generated_stream, generation_data=generation_data,
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
        final_stream = case_data.loc[i, 'final']

        # Purchasable streams
        purchase_price_type = case_data.loc[i, 'purchase_price_type']
        purchase_price = case_data.loc[i, 'purchase_price']

        # Saleable streams
        selling_price_type = case_data.loc[i, 'selling_price_type']
        selling_price = case_data.loc[i, 'selling_price']

        # Demand
        demand = case_data.loc[i, 'demand']

        stream = Stream(abbreviation, nice_name, stream_unit, final_stream=final_stream, custom_stream=False,
                        available=available, purchasable=purchasable, saleable=saleable, emittable=emittable,
                        demanded=demanded, total_demand=total_demand,
                        purchase_price=purchase_price, purchase_price_type=purchase_price_type,
                        sale_price=selling_price, sale_price_type=selling_price_type, demand=demand)
        pm_object.add_stream(abbreviation, stream)

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

    representative_week_df = case_data[case_data['type'] == 'representative_weeks']
    index = representative_week_df.index[0]
    pm_object.set_uses_representative_weeks(representative_week_df.loc[index, 'representative_weeks'])
    pm_object.set_number_representative_weeks(representative_week_df.loc[index, 'number_representative_weeks'])
    pm_object.set_path_weighting(representative_week_df.loc[index, 'path_weighting'])
    pm_object.set_covered_period(representative_week_df.loc[index, 'covered_period'])

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
            limited = case_data.loc[i, 'limited_storage']
            storage_limiting_component = case_data.loc[i, 'storage_limiting_component']
            storage_limiting_component_ratio = case_data.loc[i, 'storage_limiting_component_ratio']

            storage_component = StorageComponent(name, nice_name, lifetime, maintenance, capex,
                                                 charging_efficiency, discharging_efficiency, min_soc, max_soc,
                                                 initial_soc, leakage=leakage, ratio_capacity_p=ratio_capacity_p,
                                                 storage_limiting_component=storage_limiting_component,
                                                 storage_limiting_component_ratio=storage_limiting_component_ratio,
                                                 final_unit=final_unit, custom_unit=False, limited_storage=limited)
            pm_object.add_component(name, storage_component)

        elif component_df.loc[i, 'component_type'] == 'generator':
            generated_stream = case_data.loc[i, 'generated_stream']
            generation_data = case_data.loc[i, 'generation_data']

            generator = GenerationComponent(name, nice_name, lifetime, maintenance, capex,
                                            generated_stream=generated_stream, generation_data=generation_data,
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
        final_stream = case_data.loc[i, 'final']

        # Purchasable streams
        purchase_price_type = case_data.loc[i, 'purchase_price_type']
        purchase_price = case_data.loc[i, 'purchase_price']

        # Saleable streams
        selling_price_type = case_data.loc[i, 'selling_price_type']
        selling_price = case_data.loc[i, 'selling_price']

        # Demand
        demand = case_data.loc[i, 'demand']

        stream = Stream(abbreviation, nice_name, stream_unit, final_stream=final_stream, custom_stream=False,
                        available=available, purchasable=purchasable, saleable=saleable, emittable=emittable,
                        demanded=demanded, total_demand=total_demand,
                        purchase_price=purchase_price, purchase_price_type=purchase_price_type,
                        sale_price=selling_price, sale_price_type=selling_price_type, demand=demand)
        pm_object.add_stream(abbreviation, stream)

    """ Set nice names and abbreviations """
    name_df = case_data[case_data['type'] == 'names']

    for i in name_df.index:
        nice_name = name_df.loc[i, 'nice_name']
        abbreviation = name_df.loc[i, 'abbreviation']

        pm_object.set_nice_name(abbreviation, nice_name)
        pm_object.set_abbreviation(nice_name, abbreviation)

    return pm_object

