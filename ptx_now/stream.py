class Stream:

    def set_nice_name(self, nice_name):
        self.nice_name = nice_name

    def get_nice_name(self):
        return self.nice_name

    def set_name(self, name):
        self.name = name

    def get_name(self):
        return self.name

    def set_unit(self, unit):
        self.stream_unit = unit

    def get_unit(self):
        return self.stream_unit

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
        self.purchase_price = purchase_price

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
        self.sale_price = sale_price

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
        self.demand = demand

    def get_demand(self):
        return self.demand

    def set_total_demand(self, status):
        self.total_demand = status

    def is_total_demand(self):
        return self.total_demand

    def set_default(self, status):
        self.default_stream = status

    def set_final(self, status):
        self.final_stream = status

    def set_custom(self, status):
        self.custom_stream = status

    def is_default(self):
        return self.default_stream

    def is_final(self):
        return self.final_stream

    def is_custom(self):
        return self.custom_stream

    def __copy__(self):
        return Stream(name=self.name, nice_name=self.nice_name, stream_unit=self.stream_unit,
                      energy_content=self.energy_content,
                      final_stream=self.final_stream, custom_stream=self.custom_stream, emittable=self.emittable,
                      available=self.available, purchasable=self.purchasable, purchase_price=self.purchase_price,
                      purchase_price_type=self.purchase_price_type, saleable=self.saleable, sale_price=self.sale_price,
                      sale_price_type=self.sale_price_type, demanded=self.demanded, demand=self.demand,
                      total_demand=self.total_demand)

    def __init__(self, name, nice_name, stream_unit, energy_content=None, final_stream=False, custom_stream=False,
                 emittable=False, available=False,
                 purchasable=False, purchase_price=None, purchase_price_type='fixed',
                 saleable=False, sale_price=None, sale_price_type='fixed',
                 demanded=False, demand=0, total_demand=False):

        """

        :param name: [string] - Abbreviation of stream
        :param nice_name: [string] - Nice name of stream
        :param stream_unit: [string] - Unit of stream
        :param energy_content: [float] - Energy content per unit
        :param final_stream: [boolean] - Is used in the final optimization?
        :param custom_stream: [boolean] - Is a custom stream?
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
        self.stream_unit = stream_unit
        if energy_content is not None:
            self.energy_content = energy_content
        elif self.stream_unit == 'kWh':
            self.energy_content = 0.001
        elif self.stream_unit == 'MWh':
            self.energy_content = 1
        elif self.stream_unit == 'GWh':
            self.energy_content = 1000
        elif self.stream_unit == 'kJ':
            self.energy_content = 2.7777e-7
        elif self.stream_unit == 'MJ':
            self.energy_content = 2.7777e-4
        elif self.stream_unit == 'GJ':
            self.energy_content = 2.7777e-1
        else:
            self.energy_content = 0

        self.final_stream = final_stream
        self.custom_stream = custom_stream

        self.emittable = emittable
        self.available = available
        self.purchasable = purchasable
        self.purchase_price = purchase_price
        self.purchase_price_type = purchase_price_type
        self.saleable = saleable
        self.sale_price = sale_price
        self.sale_price_type = sale_price_type
        self.demanded = demanded
        self.demand = demand
        self.total_demand = total_demand