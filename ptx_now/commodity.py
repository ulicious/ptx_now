class Commodity:

    def set_nice_name(self, nice_name):
        self.nice_name = nice_name

    def get_nice_name(self):
        return self.nice_name

    def set_name(self, name):
        self.name = name

    def get_name(self):
        return self.name

    def set_unit(self, unit):
        self.commodity_unit = unit

    def get_unit(self):
        return self.commodity_unit

    def set_energy_content(self, energy_content):
        self.energy_content = energy_content

    def get_energy_content(self):
        return self.energy_content

    def set_purchasable(self, status):
        self.purchasable = status

    def is_purchasable(self):
        return self.purchasable

    def set_purchase_price_type(self, purchase_price_type):
        self.purchase_price_type = purchase_price_type

    def get_purchase_price_type(self):
        return self.purchase_price_type

    def set_purchase_price(self, purchase_price):
        self.purchase_price = float(purchase_price)

    def get_purchase_price(self):
        return self.purchase_price

    def set_saleable(self, status):
        self.saleable = status

    def is_saleable(self):
        return self.saleable

    def set_sale_price_type(self, sale_price_type):
        self.sale_price_type = sale_price_type

    def get_sale_price_type(self):
        return self.sale_price_type

    def set_sale_price(self, sale_price):
        self.sale_price = float(sale_price)

    def get_sale_price(self):
        return self.sale_price

    def set_available(self, status):
        self.available = status

    def is_available(self):
        return self.available

    def set_emittable(self, status):
        self.emittable = status

    def is_emittable(self):
        return self.emittable

    def set_demanded(self, status):
        self.demanded = status

    def is_demanded(self):
        return self.demanded

    def set_demand(self, demand):
        self.demand = float(demand)

    def get_demand(self):
        return self.demand

    def set_demand_type(self, status):
        self.demand_type = status

    def get_demand_type(self):
        return self.demand_type

    def set_total_demand(self, status):
        self.total_demand = status

    def is_total_demand(self):
        return self.total_demand

    def set_default(self, status):
        self.default_commodity = status

    def set_final(self, status):
        self.final_commodity = status

    def set_custom(self, status):
        self.custom_commodity = status

    def is_default(self):
        return self.default_commodity

    def is_final(self):
        return self.final_commodity

    def is_custom(self):
        return self.custom_commodity

    def __copy__(self):
        return Commodity(
            name=self.name, nice_name=self.nice_name, commodity_unit=self.commodity_unit,
            energy_content=self.energy_content, final_commodity=self.final_commodity,
            custom_commodity=self.custom_commodity, emittable=self.emittable, available=self.available,
            purchasable=self.purchasable, purchase_price=self.purchase_price,
            purchase_price_type=self.purchase_price_type, saleable=self.saleable,
            sale_price=self.sale_price, sale_price_type=self.sale_price_type, demanded=self.demanded,
            demand=self.demand, total_demand=self.total_demand, demand_type=self.demand_type)

    def __init__(self, name, nice_name, commodity_unit, energy_content=None, final_commodity=False,
                 custom_commodity=False, emittable=False, available=False,
                 purchasable=False, purchase_price=0, purchase_price_type='fixed',
                 saleable=False, sale_price=0, sale_price_type='fixed',
                 demanded=False, demand=0, total_demand=False, demand_type='fixed'):

        """

        :param name: [string] - Abbreviation of commodity
        :param nice_name: [string] - Nice name of commodity
        :param commodity_unit: [string] - Unit of commodity
        :param energy_content: [float] - Energy content per unit
        :param final_commodity: [boolean] - Is used in the final optimization?
        :param custom_commodity: [boolean] - Is a custom commodity?
        :param emittable: [boolean] - can be emitted?
        :param available: [boolean] - is freely available without limitation or price?
        :param purchasable: [boolean] - can be purchased?
        :param purchase_price: [float or list] - fixed price or time varying price
        :param purchase_price_type: [string] - fixed price or time varying price
        :param saleable: [boolean] - can be sold?
        :param sale_price: [float or list] - fixed price or time varying price
        :param sale_price_type: [string] - fixed price or time varying price
        :param demanded: [boolean] - is demanded?
        :param demand: [float] - Demand
        :param total_demand: [boolean] - Demand over all time steps or for each time step
        """

        self.name = name
        self.nice_name = nice_name
        self.commodity_unit = commodity_unit
        if energy_content is not None:
            self.energy_content = float(energy_content)
        elif self.commodity_unit == 'kWh':
            self.energy_content = 0.001
        elif self.commodity_unit == 'MWh':
            self.energy_content = 1
        elif self.commodity_unit == 'GWh':
            self.energy_content = 1000
        elif self.commodity_unit == 'kJ':
            self.energy_content = 2.7777e-7
        elif self.commodity_unit == 'MJ':
            self.energy_content = 2.7777e-4
        elif self.commodity_unit == 'GJ':
            self.energy_content = 2.7777e-1
        else:
            self.energy_content = 0

        self.final_commodity = bool(final_commodity)
        self.custom_commodity = bool(custom_commodity)

        self.emittable = bool(emittable)
        self.available = bool(available)

        self.purchasable = bool(purchasable)
        if purchase_price_type == 'fixed':
            self.purchase_price = float(purchase_price)
        else:
            self.purchase_price = purchase_price
        self.purchase_price_type = purchase_price_type

        self.saleable = bool(saleable)
        if sale_price_type == 'fixed':
            self.sale_price = float(sale_price)
        else:
            self.sale_price = sale_price
        self.sale_price_type = sale_price_type

        self.demanded = bool(demanded)
        self.total_demand = bool(total_demand)
        if demand_type == 'fixed':
            self.demand = float(demand)
        else:
            self.demand = demand
        self.demand_type = demand_type
