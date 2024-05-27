from collections import defaultdict
from datetime import datetime


class NurseScheduler:
    def __init__(self, required_hours):
        self.required_hours = required_hours
        self.availabilities = defaultdict(list)
        self.nurse_hours = defaultdict(int)

    def add_availability(self, nurse_name, day, start_time, end_time):
        self.availabilities[nurse_name].append((day, start_time, end_time))

    def generate_schedule(self):
        schedule = {day: [] for day in self.required_hours.keys()}
        unassigned_hours = {day: list(times) for day, times in self.required_hours.items()}
        total_hours = sum(self.calculate_hours(slot) for slots in self.required_hours.values() for slot in slots)

        while total_hours > 0:
            assigned_any = False
            for nurse, times in self.availabilities.items():
                for day, start_time, end_time in times:
                    if day in unassigned_hours:
                        for time_slot in list(unassigned_hours[day]):
                            if start_time <= time_slot[0] and end_time >= time_slot[1]:
                                schedule[day].append((time_slot, nurse))
                                unassigned_hours[day].remove(time_slot)
                                hours = self.calculate_hours(time_slot)
                                self.nurse_hours[nurse] += hours
                                total_hours -= hours
                                assigned_any = True
                                if not unassigned_hours[day]:
                                    break
                        if not unassigned_hours[day]:
                            break
            if not assigned_any:
                break

        return schedule, unassigned_hours

    def calculate_hours(self, time_slot):
        time_format = "%H:%M"
        start = datetime.strptime(time_slot[0], time_format)
        end = datetime.strptime(time_slot[1], time_format)
        return (end - start).seconds / 3600
