from collections import defaultdict
import datetime

class NurseScheduler:
    def __init__(self, required_hours):
        self.required_hours = required_hours
        self.availabilities = defaultdict(list)
        self.schedule = defaultdict(lambda: defaultdict(list))
        self.unassigned_hours = defaultdict(list)

    def add_availability(self, nurse_name, day, start_time, end_time):
        self.availabilities[day].append((nurse_name, start_time, end_time))

    def generate_schedule(self):
        for day, periods in self.required_hours.items():
            for start, end in periods:
                start_dt = datetime.datetime.strptime(start, '%H:%M')
                end_dt = datetime.datetime.strptime(end, '%H:%M')
                hours_needed = (end_dt - start_dt).seconds / 3600

                available_nurses = sorted(self.availabilities[day], key=lambda x: x[2])

                hours_assigned = 0
                for nurse_name, nurse_start, nurse_end in available_nurses:
                    nurse_start_dt = datetime.datetime.strptime(nurse_start, '%H:%M')
                    nurse_end_dt = datetime.datetime.strptime(nurse_end, '%H:%M')

                    if nurse_start_dt <= start_dt and nurse_end_dt >= end_dt:
                        self.schedule[day][(start, end)].append(nurse_name)
                        hours_assigned += hours_needed

                if hours_assigned < hours_needed:
                    self.unassigned_hours[day].append((start, end))

        return self.schedule, self.unassigned_hours
