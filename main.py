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

    def display_schedule(self, schedule, unassigned_hours):
        for day, assignments in schedule.items():
            print(f"{day}:")
            for time_slot, nurse in assignments:
                print(f"  {time_slot[0]} - {time_slot[1]}: {nurse}")
            print()

        print("\nTotal de horas trabajadas por cada enfermera:")
        for nurse, hours in self.nurse_hours.items():
            print(f"{nurse}: {hours} horas")

        if any(unassigned_hours.values()):
            print("\nHoras sin cubrir:")
            for day, times in unassigned_hours.items():
                if times:
                    print(f"{day}:")
                    for time_slot in times:
                        print(f"  {time_slot[0]} - {time_slot[1]}")
        else:
            print("\nTodas las horas están cubiertas.")


# Ejemplo de uso
required_hours = {
    'Lunes': [('09:00', '14:00'), ('15:00', '20:00')],
    'Martes': [('09:00', '14:00'), ('15:00', '20:00')],
    'Miercoles': [('09:00', '14:00'), ('15:00', '20:00')],
    'Jueves': [('09:00', '14:00'), ('15:00', '20:00')],
    'Viernes': [('09:00', '14:00'), ('15:00', '20:00')]
}

scheduler = NurseScheduler(required_hours)

# Agregar disponibilidades de las enfermeras
scheduler.add_availability('Arya', 'Lunes', '09:00', '17:00')
scheduler.add_availability('Arya', 'Martes', '09:00', '17:00')
scheduler.add_availability('Arya', 'Miercoles', '09:00', '17:00')

scheduler.add_availability('Laura', 'Martes', '09:00', '17:00')
scheduler.add_availability('Laura', 'Miercoles', '09:00', '17:00')

scheduler.add_availability('Josema', 'Miercoles', '09:00', '17:00')
scheduler.add_availability('Josema', 'Viernes', '15:00', '20:00')
scheduler.add_availability('Josema', 'Lunes', '09:00', '17:00')

scheduler.add_availability('Cora', 'Viernes', '10:00', '20:00')
scheduler.add_availability('Cora', 'Jueves', '10:00', '20:00')
scheduler.add_availability('Cora', 'Martes', '10:00', '20:00')

scheduler.add_availability('Maya', 'Viernes', '10:00', '20:00')
scheduler.add_availability('Maya', 'Martes', '10:00', '20:00')

scheduler.add_availability('Coffee', 'Jueves', '10:00', '20:00')
scheduler.add_availability('Coffee', 'Miercoles', '10:00', '20:00')
scheduler.add_availability('Coffee', 'Martes', '15:00', '20:00')

# Generar y mostrar el horario
schedule, unassigned_hours = scheduler.generate_schedule()
scheduler.display_schedule(schedule, unassigned_hours)