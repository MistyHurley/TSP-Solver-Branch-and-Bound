from util import Util


# contains package data
class Package:
    """
    TODO: paper - removed notes column so that new requirements can be implemented properly
    """

    # class constructor
    # O(n) = 1
    def __init__(self, new_package):
        self.package_id = new_package[0]
        self.address = new_package[1]
        self.city = new_package[2]
        self.state = new_package[3]
        self.zip_code = new_package[4]
        self.deadline = new_package[5]
        self.weight = new_package[6]
        self.group_id = new_package[7]
        self.requires_truck = new_package[8]
        self.delay_time = new_package[9]
        self.status = "At Hub"
        self.delivery_time = "TBD"

    # print a tabular row of this package's information including status
    # O(n) = 1
    def print_info(self, table_formatter, at_time):
        # this is a little dirty, but in reality the data would have been simply updated in the database
        # at the appropriate time, and since the application is querying as if it were actually at a given time,
        # display the incorrect address if it hasn't been corrected yet or the correct one if it has
        if hasattr(self, "incorrect_address") and Util.time_f(at_time) < Util.time_f(self.delay_time):
            display_address = self.incorrect_address
        else:
            display_address = self.address
        print(table_formatter.format(self.package_id, display_address, self.deadline, self.city, self.zip_code,
                                     self.weight, self.status, self.delivery_time))
