from util import Util
from hashtable import HashTable


# contains route data and performs route calculations and optimization
class Route:
    # static members, references intended to be set from the outside to valid references for proper operation
    package_table = HashTable(0)
    distance_table = HashTable(0)
    truck_table = HashTable(0)

    # class constructor
    # O(n) = 1
    def __init__(self, truck_id, start_time):
        self.truck_id = truck_id
        self.start_time = start_time
        self.return_time = "TBD"
        self.total_miles = 0
        self.package_ids = []
        self.current_miles = 0
        self.current_package_ids = []

    # branch and bound algorithm for reordering a package list to optimize total distance (including return) without
    # violating any of the required constraints (notably deadlines); finds a good solution fast, not the best solution;
    # theoretically O(n) = n * n, but realistically the heuristic culling should reject enough nodes to be closer to
    # roughly O(n) = n * log(n); it also helps that the starting order should be nearest neighbor, which means the
    # initial best solution found should be a fairly decent benchmark for eliminating dead end branches
    def find_optimal_path(self):
        global best_solution, best_cost, current_solution, current_cost
        # for building and checking a solution while traversing the tree
        current_solution = []
        current_solution_table = HashTable(2 * Util.MAX_TRUCK_PACKAGES)
        current_cost = 0
        # for tracking the best solution so far
        best_solution = []
        best_cost = float("inf")

        # recursive inner function for traversing the tree
        def tsp_traverse():
            global best_solution, best_cost, current_solution, current_cost

            packages_to_route = len(self.package_ids)
            # for keeping track of next nodes that seem not unlikely to contain a better solution
            package_candidates = []
            # since we need to calculate cost to find out if the deadline will be violated, keep track of it in a
            # hashtable to make it quick to look up later
            package_candidate_cost_table = HashTable(2 * packages_to_route)

            # consider each package assigned to this route
            for package_id in self.package_ids:
                # skip any package already in the current solution
                if current_solution_table.get(package_id) is not None:
                    continue

                # get package object
                package = Route.package_table.get(package_id)

                # either use hub address if this is the first package in the solution or use last package address
                if len(current_solution) == 0:
                    last_address = Util.HUB_ADDRESS
                else:
                    last_address = Route.package_table.get(current_solution[len(current_solution) - 1]).address

                # use distance truth table to find how much the considered package would cost in miles
                package_cost = Route.distance_table.get(last_address).get(package.address)

                # find out what the total cost would be at this point in the route, rejecting if it is under par
                # when compared to the current best solution as of where it would have been at this depth
                potential_current_cost = current_cost + float(package_cost)
                if potential_current_cost > best_cost * ((len(current_solution) + 1) / packages_to_route) * 0.95:
                    # predicted to not be a good candidate for significant gains
                    continue
                # reject the package if the time cost would put it past its deadline
                if Util.time_f(self.start_time) + (potential_current_cost / Util.TRUCK_MPH) > Util.time_f(package.deadline):
                    continue

                # add the package to the list of valid candidates
                package_candidates.append(package_id)
                package_candidate_cost_table.set(package_id, float(package_cost))

            # reject this entire branch if there are no valid candidates to choose from for the next route step
            if len(package_candidates) == 0:
                return

            # cull the top performing quarter of the package candidates (no fewer than 1) to branch into next
            package_candidates.sort(key=lambda x: package_candidate_cost_table.get(x))
            top_package_candidates = []
            for idx, package_candidate in enumerate(package_candidates):
                top_package_candidates.append(package_candidate)
                if idx > len(package_candidates) / 4:
                    break

            # look through the top candidates, checking if it's the best solution if it's a leaf or digging deeper if
            # it's an intermediate branch node
            for package_id in top_package_candidates:
                # add to the solution, including the current cumulative solution cost, remembering the previous cost
                current_solution.append(package_id)
                current_solution_table.set(package_id, "")
                previous_cost = current_cost
                current_cost += package_candidate_cost_table.get(package_id)

                cur_len = len(current_solution)
                # this is a leaf; check if it's a new best solution
                if cur_len == packages_to_route:
                    current_cost += float(Route.distance_table.get(Route.package_table.get(current_solution[cur_len - 1]).address).get(Util.HUB_ADDRESS))
                    if current_cost < best_cost:
                        best_solution = Util.clone_list(current_solution)
                        best_cost = current_cost
                    # peel this node back off the stack before the return back up to a parent node
                    current_solution.pop()
                    current_solution_table.unset(package_id)
                    current_cost = previous_cost
                else:
                    # traverse deeper into the tree with the stack containing the current candidate package node
                    tsp_traverse()
                    # peel this node back off the stack before the return back up to a parent node
                    current_solution.pop()
                    current_solution_table.unset(package_id)
                    current_cost = previous_cost

        # start traversing the tree starting from the root (the hub)
        tsp_traverse()

        # write back the best solution found from the solver
        self.package_ids = best_solution

    # calculates and sets info on the route and packages as they are at the end of the day
    # if at_time is set, it also sets info on the route and packages reflecting what the status should be at that time;
    # since this needs to iterate through the list of packages once, O(n) = n
    def calc_route(self, at_time=None):
        self.current_package_ids = []
        cumulative_cost = 0  # keeps track of how many miles have been driven as derived from distance truth table
        if len(self.package_ids) == 0:
            return 0
        # loop through tha packages on this route to both set their status info and add up the cumulative mileage
        for idx, package_id in enumerate(self.package_ids):
            if idx == 0:
                prev_address = Util.HUB_ADDRESS
            else:
                prev_address = Route.package_table.get(self.package_ids[idx - 1]).address
            package = Route.package_table.get(package_id)
            cumulative_cost += float(Route.distance_table.get(prev_address).get(package.address))
            delivery_time_f = Util.time_f(self.start_time) + (cumulative_cost / Util.TRUCK_MPH)
            # set status on package based on route not having started yet
            if at_time is not None and Util.time_f(at_time) < Util.time_f(self.start_time):
                package.status = "At Hub"
                package.delivery_time = "TBD"
            # set status on package based on if the route has started but the package address hasn't been reached yet
            elif at_time is not None and Util.time_f(at_time) < delivery_time_f:
                self.current_package_ids.append(package_id)
                package.status = "En Route"
                package.delivery_time = "TBD"
            # set package status based on if the estimated delivery time has passed, recording estimated as actual
            else:
                package.status = "Delivered"
                package.delivery_time = Util.time_s(delivery_time_f)
        cumulative_cost += float(Route.distance_table.get(package.address).get(Util.HUB_ADDRESS))
        self.total_miles = cumulative_cost
        # set status of how many miles have been driven on this route based on duration into the route's timespan;
        # doing this as a function of how much time has elapsed since the start so it is much simpler to report back
        # an accurate figure of miles driven since a picked time might be between stops or the return to hub
        if at_time is not None:
            if Util.time_f(at_time) < Util.time_f(self.start_time):
                self.current_miles = 0
            elif Util.time_f(at_time) < Util.time_f(self.return_time):
                self.current_miles = (Util.time_f(at_time) - Util.time_f(self.start_time)) * Util.TRUCK_MPH
            else:
                self.current_miles = self.total_miles
        else:
            self.current_miles = self.total_miles
        # this is calculated much teh same way; it also gets written back to the global list so the routing code
        # knows when a truck is next available as routes are processed in sequence (irrelevant after routing completes)
        self.return_time = Util.time_s(Util.time_f(self.start_time) + (cumulative_cost / Util.TRUCK_MPH))
        Route.truck_table.set(self.truck_id, self.return_time)
