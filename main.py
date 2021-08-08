# Misty Hurley 000743151

from package import Package
from route import Route
from hashtable import HashTable
from util import Util
import csv
import re

if __name__ == '__main__':
    print("Welcome to WGUPS package routing and tracking system.")
    print("")
    print("Please stand by while package data is processed and routed...")

    # read distances from csv file
    # use nested hashtables by address pair for quick lookups
    # O(n) = n
    with open('distance.csv') as df:
        reader = csv.reader(df)
        for idx, row in enumerate(reader):
            # first row is expected to specify address strings
            if idx == 0:
                addresses = row
                distance_table = HashTable(2 * len(addresses))
            # all other rows are the distance truth table
            else:
                distance_table.set(addresses[idx - 1], HashTable(2 * len(addresses)))
                for idx2 in range(0, len(addresses)):
                    distance_table.get(addresses[idx - 1]).set(addresses[idx2], row[idx2])

    # search for blank entries and fill them in with the opposite side of the truth table
    # O(n) = n
    for address in addresses:
        for address2 in addresses:
            if distance_table.get(address).get(address2) == "":
                distance_table.get(address).set(address2, distance_table.get(address2).get(address))

    # read packages from csv file
    # O(n) = n
    packages = []
    with open('package.csv') as pf:
        reader = csv.reader(pf)
        for row in reader:
            package = Package(row)
            packages.append(package)

    # store packages in hashtable by id for quick lookups and keep a list of package ids separately
    # O(n) = n
    package_table = HashTable(2 * len(packages))
    package_ids = []
    for package in packages:
        package_table.set(package.package_id, package)
        package_ids.append(package.package_id)

    # delete package object array to recover some memory and prevent it from being used and causing de-sync
    del packages

    # double check that all package addresses are in truth table
    # O(n) = n
    has_invalid = False
    for package_id in package_ids:
        package = package_table.get(package_id)
        if distance_table.get(package.address) is None:
            print("encountered invalid address: " + package.address)
            has_invalid = True
    if has_invalid:
        exit(1)

    # define trucks and availability times
    truck_ids = ["1", "2"]
    truck_table = HashTable(2 * len(truck_ids))
    for truck_id in truck_ids:
        truck_table.set(truck_id, Util.DEFAULT_START_TIME)

    # find out if and until when to delay a truck
    # O(n) = n
    earliest_delay_time = None
    for package_id in package_ids:
        package = package_table.get(package_id)
        if package.delay_time != "" and (earliest_delay_time is None or Util.time_f(package.delay_time) < Util.time_f(earliest_delay_time)):
            earliest_delay_time = package.delay_time
    if earliest_delay_time is not None:
        delay_truck_id = truck_ids[len(truck_ids) - 1]
        truck_table.set(delay_truck_id, earliest_delay_time)

    # set references as static members on Route so it has the data it needs to do routing
    Route.package_table = package_table
    Route.distance_table = distance_table
    Route.truck_table = truck_table

    # noinspection PyTypeChecker
    remaining_package_ids = Util.clone_list(package_ids)
    routes = []

    # O(n) = n (where n = the total number of packages that need to be routed)
    while len(remaining_package_ids) > 0:

        # sort packages based on deadline, tiebreak by package group
        # O(n) = log(n) for each (assumed for python's built-in sorting)
        remaining_package_ids.sort(key=lambda x: package_table.get(x).group_id, reverse=True)
        remaining_package_ids.sort(key=lambda x: Util.time_f(package_table.get(x).deadline))

        # filter function used later on to remove packages that
        # O(n) = n
        def filter_packages(package_id):
            package = package_table.get(package_id)
            # package must have no limitation on truck or must be the right truck
            if package.requires_truck != "" and package.requires_truck != route.truck_id:
                return False
            # package must not be delayed until after this route starts
            if Util.time_f(package.delay_time) > Util.time_f(route.start_time):
                return False
            return True

        # figure out which truck to use for this route and create the route object
        # prefer to load to a required truck if there are still outstanding packages that require one
        # O(n) = n
        remainder_truck_id = ""
        if len(remaining_package_ids) <= Util.MAX_TRUCK_PACKAGES:
            for remaining_package_id in remaining_package_ids:
                remaining_package = package_table.get(remaining_package_id)
                if remaining_package.requires_truck != "":
                    remainder_truck_id = remaining_package.requires_truck
        if remainder_truck_id != "":
            route = Route(remainder_truck_id, truck_table.get(remainder_truck_id))
        # otherwise look for the truck that has the earliest availability time
        # O(n) = n
        else:
            earliest_truck_id = None
            earliest_truck_time = "8:00 PM"
            for truck_id in truck_ids:
                # noinspection PyTypeChecker
                if earliest_truck_time is None or Util.time_f(truck_table.get(truck_id)) < Util.time_f(earliest_truck_time):
                    earliest_truck_id = truck_id
                    earliest_truck_time = truck_table.get(earliest_truck_id)
            route = Route(earliest_truck_id, truck_table.get(earliest_truck_id))

        # TODO?: make this solution more general
        # the reality would be that this is updated in a database in realtime, but for this project that correction
        # must be simulated, so we're just correcting it as of when a route is started after the correction time,
        # storing the incorrect address for safekeeping for display purposes during status simulation
        # noinspection PyTypeChecker
        if Util.time_f(route.start_time) >= Util.time_f("10:20 AM"):
            corrected_package = package_table.get("9")
            corrected_package.incorrect_address = corrected_package.address
            corrected_package.address = "410 S State St"

        # reduce down to packages that are valid for the given route (not delayed beyond start time and correct truck)
        filtered_package_ids = list(filter(filter_packages, remaining_package_ids))

        # find unique deadlines so we can prefer to deliver packages with deadlines grouped by the earliest deadline
        # O(n) = n
        unique_deadlines = []
        for filtered_package_id in filtered_package_ids:
            filtered_package = package_table.get(filtered_package_id)
            if filtered_package.deadline not in unique_deadlines:
                unique_deadlines.append(filtered_package.deadline)

        # prefer to load based on grouping of earliest deadlines
        # not including the contained sorting, should be O(n) = n where n <= Util.MAX_TRUCK_PACKAGES
        # should cumulatively be O(n) = n * log(n)
        for unique_deadline in unique_deadlines:
            if len(route.package_ids) == 0:
                prev_address = Util.HUB_ADDRESS
            else:
                prev_address = package_table.get(route.package_ids[len(route.package_ids) - 1]).address
            deadline_packages = list(filter(lambda x: package_table.get(x).deadline == unique_deadline, filtered_package_ids))
            while len(deadline_packages) > 0:
                if len(route.package_ids) >= Util.MAX_TRUCK_PACKAGES:
                    break
                # sort so we try to grab this deadline group's packages sorted by whichever is the closest address to
                # the last address; tiebreak by preferring those that have a package group
                # O(n) = log(n) for each (assumed for python's built-in sorting)
                deadline_packages.sort(key=lambda x: distance_table.get(prev_address).get(package_table.get(x).address))
                deadline_packages.sort(
                    key=lambda x: package_table.get(x).deadline != "EOD" or package_table.get(x).group_id != "",
                    reverse=True)
                nearest_next_package_id = deadline_packages[0]
                nearest_next_package = package_table.get(nearest_next_package_id)
                # force this list to include outstanding grouped packages if we add a package belonging to one
                # keep track of the addresses among those
                if nearest_next_package.group_id != "":
                    added_group_package_addresses = []
                    for group_package_id in filtered_package_ids:
                        # immediately add rest of the group packages
                        if group_package_id in route.package_ids:
                            continue
                        group_package = package_table.get(group_package_id)
                        if group_package.group_id != nearest_next_package.group_id:
                            continue
                        route.package_ids.append(group_package_id)
                        added_group_package_addresses.append(group_package.address)
                    # see if there are any packages that share an address with the package group and add them afterwards
                    # since they are effectively free outside of the truck's max package budget
                    for same_address_package_id in filtered_package_ids:
                        if same_address_package_id in route.package_ids:
                            continue
                        same_address_package = package_table.get(same_address_package_id)
                        if same_address_package.address in added_group_package_addresses:
                            route.package_ids.append(same_address_package_id)
                # if iterated into a package that's already added, skip and move on
                if nearest_next_package_id in route.package_ids:
                    deadline_packages.remove(nearest_next_package_id)
                    continue
                # add the package to the route
                route.package_ids.append(nearest_next_package_id)
                # see if there are any packages that share an address with this package and add them afterwards
                # since they are effectively free outside of the truck's max package budget
                nearest_next_package = package_table.get(nearest_next_package_id)
                for same_address_package_id in filtered_package_ids:
                    if same_address_package_id in route.package_ids:
                        continue
                    same_address_package = package_table.get(same_address_package_id)
                    if same_address_package.address == nearest_next_package.address:
                        route.package_ids.append(same_address_package_id)
                deadline_packages.remove(nearest_next_package_id)

            if len(route.package_ids) >= Util.MAX_TRUCK_PACKAGES:
                break

        # if we ended up with more packages than the truck can carry (freebies tacked on), truncate the list down
        # O(n) = n where n <= Util.MAX_TRUCK_PACKAGES
        if len(route.package_ids) > Util.MAX_TRUCK_PACKAGES:
            truncated_route_package_ids = []
            for i in range(0, Util.MAX_TRUCK_PACKAGES):
                truncated_route_package_ids.append(route.package_ids[i])
            route.package_ids = truncated_route_package_ids

        # do finer grained tsp solving based on the packages we decided are suitable then calculate the final route info
        route.find_optimal_path()
        route.calc_route()

        # add completed route to list
        routes.append(route)

        # remove packages from remaining_package_ids
        # O(n) = n
        for package_id in route.package_ids:
            remaining_package_ids.remove(package_id)

    print("")
    print("Today's estimated route information:")
    print("")

    # display the final route information
    total_miles = 0
    for idx, route in enumerate(routes):
        total_miles += route.total_miles
        print("Route " + str(idx + 1))
        print("Truck: " + route.truck_id)
        print("Starts: " + route.start_time)
        print("Ends: " + route.return_time)
        print("Total Miles: " + "{:.2f}".format(route.total_miles))
        print("Package Order: " + ", ".join(route.package_ids))
        print("")
    print("Grand Total: " + "{:.2f}".format(total_miles) + " miles")

    table_formatter = "{:>4} {:<40} {:>8} {:<20} {:>5} {:>6} {:<9} {:>8}"  # used for displaying package table info
    time_matcher = re.compile("^(1[012]|[1-9]):[0-5][0-9] [AP]M$")  # used for validating user entered time strings
    while True:
        print("")
        print("Please enter a time in HH:MM AM/PM format to display status of packages and trucks")
        print("or type 'exit' to leave the program.")
        input_string = input("> ")
        input_string = str.upper(input_string)
        if input_string == "EXIT":
            print("Goodbye.")
            exit(0)
        if time_matcher.match(input_string):
            print("")
            print("Status information for: " + input_string)

            # calculate routes at given time and add up the total number of miles driven
            # not including the complexity of contained call to calc_route, O(n) = n (where n = the number of routes)
            all_truck_miles = 0
            for route in routes:
                route.calc_route(input_string)
                all_truck_miles += route.current_miles

            # print status of all packages
            # O(n) = n (where n = the number of packages)
            print("")
            print("Package information:")
            print("")
            print(table_formatter.format("ID", "Address", "Deadline", "City", "Zip", "Weight", "Status", "Delivery"))
            for package_id in package_ids:
                package = package_table.get(package_id)
                package.print_info(table_formatter, input_string)

            # print current info for each truck
            # O(n) = n (where n = the number of trucks)
            for truck_id in truck_ids:
                print("")
                active_route = None
                for route in routes:
                    # noinspection PyTypeChecker
                    if route.truck_id == truck_id and Util.time_f(route.start_time) <= Util.time_f(
                            input_string) and Util.time_f(route.return_time) > Util.time_f(input_string):
                        active_route = route
                        break
                if active_route is not None:
                    print("Truck " + truck_id + " is en route and currently contains: ")
                    if len(active_route.current_package_ids):
                        print(", ".join(active_route.current_package_ids))
                    else:
                        print("Nothing")
                else:
                    print("Truck " + truck_id + " is at hub with no packages.")

            # print total miles travelled by all trucks so far
            print("")
            print("Total miles driven by all trucks at this time: " + "{:.2f}".format(all_truck_miles))
        else:
            print("Invalid time or format.")

    # preference for package loading choices
    # deadline
    # correct truck_id or no truck_id
    # delivery group must fit together in solution
    # delay_time >= route start_time
    # package count <= 16 per truck
    # TODO?: delay any packages with same address as a delayed package if still meets deadline

    # while packages left > 0
    #    pick truck with earliest availability time
    #    create route with picked truck_id and start_time
    #        if fewer than a max load of packages is left and any of them require a specific truck, wait to use required truck
    #    attempt to intelligently fill route with packages with regards to constraints and ease; rough nearest neighbor
    #        prefer meeting deadlines first
    #        prefer packages that belong to groups
    #        try to use all package in a group if adding a single package from a group
    #        prefer the closest package to the last package loaded (or the hub if there are none)
    #    branch and bound to find distance/time optimized route for the packages selected, trunk to leaf (depth-wise)
    #        prune any branch out of bounds or violating rules:
    #            deadline must be met
    #            has correct truck_id or no truck_id
    #            delivery group must fit together in solution
    #            delay_time <= route start_time
    #            package count <= MAX_TRUCK_PACKAGES
    #            heuristically determined to be likely better than best solution so far
    #        track best solution, reject branches that are impossible/not within 95% of expected target at current depth
