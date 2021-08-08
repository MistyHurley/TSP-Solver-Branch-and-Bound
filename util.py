# static utility class containing commonly used constants and static functions
class Util:
    # static members, used as global constants
    HUB_ADDRESS = "4001 South 700 East"
    TRUCK_MPH = 18
    NUM_TRUCKS = 2
    MAX_TRUCK_PACKAGES = 16
    DEFAULT_START_TIME = '8:00 AM'

    # helper function for getting a floating point number representing number of hours (w/fraction) since 12:00 AM
    # O(n) = 1
    def time_f(s):
        if s == "":
            return 0
        if s == "EOD":
            return 20
        hour_split = s.split(":")
        minute_split = hour_split[1].split(" ")
        hour = float(hour_split[0])
        minute = float(minute_split[0])
        if minute_split[1].upper() == "PM" and hour != 12:
            hour += 12
        elif minute_split[1].upper() == "AM" and hour == 12:
            hour -= 12
        return hour + (minute / 60)

    # helper function for getting a friendly display formatted time back from the floating point times created above
    # O(n) = 1
    def time_s(f):
        hour = int(f)
        if hour >= 12:
            am_pm = "PM"
            if hour > 12:
                hour -= 12
        else:
            am_pm = "AM"
            if hour == 0:
                hour = 12
        minute = int((f % 1) * 60)
        return "{0:d}:{1:02d} {2}".format(hour, minute, am_pm)

    # creates a shallow copy of a list; useful since python copies references to lists instead of copying the contents
    # O(n) = n
    def clone_list(l):
        c = []
        for e in l:
            c.append(e)
        return c
