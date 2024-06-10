from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask import Flask, render_template, request, redirect, url_for
from extensions import db
from scheduler import NurseScheduler
from models import Nurse, Availability
from collections import defaultdict

from flask import send_file
from io import BytesIO
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///nurses.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

@app.route('/')
def index():
    nurses = Nurse.query.all()
    return render_template('index.html', nurses=nurses)


@app.route('/download_schedule_pdf')
def download_schedule_pdf():
    nurses = Nurse.query.all()
    required_hours = {
        'Monday': [('09:00', '14:00'), ('15:00', '20:00')],
        'Tuesday': [('09:00', '14:00'), ('15:00', '20:00')],
        'Wednesday': [('09:00', '14:00'), ('15:00', '20:00')],
        'Thursday': [('09:00', '14:00'), ('15:00', '20:00')],
        'Friday': [('09:00', '14:00'), ('15:00', '20:00')]
    }

    scheduler = NurseScheduler(required_hours)
    for nurse in nurses:
        for availability in nurse.availabilities:
            scheduler.add_availability(nurse.name, nurse.role, availability.day, availability.start_time, availability.end_time)

    schedule, unassigned_hours = scheduler.generate_schedule()

    processed_schedule = {day: [] for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']}
    medical_schedule = {day: [] for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']}
    nurse_hours = defaultdict(int)

    for day, periods in schedule.items():
        if periods:
            current_nurses = None
            current_start = None
            current_end = None

            for (start, end), nurses in sorted(periods.items()):
                start_hour = int(start[:2])
                end_hour = int(end[:2])
                duration = end_hour - start_hour

                unique_nurses = []
                seen_nurses = set()
                for nurse in sorted(nurses, key=lambda x: x[1] != 'Médico'):
                    if nurse[0] not in seen_nurses:
                        unique_nurses.append(nurse)
                        seen_nurses.add(nurse[0])

                if current_nurses is None:
                    current_nurses = unique_nurses
                    current_start = start_hour
                    current_end = end_hour
                elif current_nurses == unique_nurses:
                    current_end = end_hour
                else:
                    processed_schedule[day].append({
                        'start': current_start,
                        'end': current_end,
                        'nurses': [nurse for nurse in current_nurses if nurse[1] != 'Médico']
                    })
                    medical_schedule[day].append({
                        'start': current_start,
                        'end': current_end,
                        'nurses': [nurse for nurse in current_nurses if nurse[1] == 'Médico']
                    })
                    for nurse, role in current_nurses:
                        nurse_hours[nurse] += (current_end - current_start)

                    current_nurses = unique_nurses
                    current_start = start_hour
                    current_end = end_hour

            if current_nurses is not None:
                processed_schedule[day].append({
                    'start': current_start,
                    'end': current_end,
                    'nurses': [nurse for nurse in current_nurses if nurse[1] != 'Médico']
                })
                medical_schedule[day].append({
                    'start': current_start,
                    'end': current_end,
                    'nurses': [nurse for nurse in current_nurses if nurse[1] == 'Médico']
                })
                for nurse, role in current_nurses:
                    nurse_hours[nurse] += (current_end - current_start)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
    elements = []

    # Crear la tabla de horarios
    data = [['Hora', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']]

    for hour in range(9, 21):
        row = [f"{hour:02d}:00"]
        for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
            cell = []
            for period in processed_schedule[day]:
                if period['start'] == hour:
                    cell.append(f"{period['start']:02d}:00 - {period['end']:02d}:00")
                    cell.extend([f"{nurse[0]} ({nurse[1]})" for nurse in period['nurses']])
            row.append('\n'.join(cell))
        data.append(row)

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    elements.append(table)

    # Crear la tabla de médicos
    data_medical = [['Hora', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']]
    for hour in range(9, 21):
        row = [f"{hour:02d}:00"]
        for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
            cell = []
            for period in medical_schedule[day]:
                if period['start'] == hour:
                    cell.append(f"{period['start']:02d}:00 - {period['end']:02d}:00")
                    cell.extend([f"{nurse[0]} ({nurse[1]})" for nurse in period['nurses']])
            row.append('\n'.join(cell))
        data_medical.append(row)

    table_medical = Table(data_medical, repeatRows=1)
    table_medical.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    elements.append(table_medical)

    # Crear la tabla de horas totales por trabajador
    data_hours = [['Trabajador', 'Horas']]
    for nurse, hours in nurse_hours.items():
        data_hours.append([nurse, hours])

    table_hours = Table(data_hours)
    table_hours.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    elements.append(table_hours)

    doc.build(elements)

    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="calendario.pdf", mimetype='application/pdf')



@app.route('/add_nurse_form')
def add_nurse_form():
    return render_template('add_nurse_form.html')

@app.route('/add_nurse', methods=['POST'])
def add_nurse():
    name = request.form['name']
    role = request.form['role']  # Recibir el rol del formulario
    nurse = Nurse(name=name, role=role)
    db.session.add(nurse)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/edit_nurse_form/<int:nurse_id>')
def edit_nurse_form(nurse_id):
    nurse = Nurse.query.get(nurse_id)
    return render_template('edit_nurse_form.html', nurse=nurse)

@app.route('/edit_nurse/<int:nurse_id>', methods=['POST'])
def edit_nurse(nurse_id):
    nurse = Nurse.query.get(nurse_id)
    nurse.name = request.form['name']
    nurse.role = request.form['role']  # Actualizar el rol
    db.session.commit()

    # Remove existing availabilities
    Availability.query.filter_by(nurse_id=nurse_id).delete()

    # Add updated availabilities
    for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']:
        start_time = request.form.get(f'{day.lower()}_start')
        end_time = request.form.get(f'{day.lower()}_end')
        if start_time and end_time:
            availability = Availability(day=day, start_time=start_time, end_time=end_time, nurse_id=nurse_id)
            db.session.add(availability)

    db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete_nurse/<int:nurse_id>')
def delete_nurse(nurse_id):
    Nurse.query.filter_by(id=nurse_id).delete()
    Availability.query.filter_by(nurse_id=nurse_id).delete()
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/generate_schedule')
def generate_schedule():
    nurses = Nurse.query.all()
    required_hours = {
        'Monday': [('09:00', '14:00'), ('15:00', '20:00')],
        'Tuesday': [('09:00', '14:00'), ('15:00', '20:00')],
        'Wednesday': [('09:00', '14:00'), ('15:00', '20:00')],
        'Thursday': [('09:00', '14:00'), ('15:00', '20:00')],
        'Friday': [('09:00', '14:00'), ('15:00', '20:00')]
    }

    scheduler = NurseScheduler(required_hours)
    for nurse in nurses:
        for availability in nurse.availabilities:
            scheduler.add_availability(nurse.name, nurse.role, availability.day, availability.start_time, availability.end_time)

    schedule, unassigned_hours = scheduler.generate_schedule()

    processed_schedule = {day: [] for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']}
    medical_schedule = {day: [] for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']}
    nurse_hours = defaultdict(int)

    for day, periods in schedule.items():
        if periods:
            current_nurses = None
            current_start = None
            current_end = None

            for (start, end), nurses in sorted(periods.items()):
                start_hour = int(start[:2])
                end_hour = int(end[:2])
                duration = end_hour - start_hour

                unique_nurses = []
                seen_nurses = set()
                for nurse in sorted(nurses, key=lambda x: x[1] != 'Médico'):
                    if nurse[0] not in seen_nurses:
                        unique_nurses.append(nurse)
                        seen_nurses.add(nurse[0])

                if current_nurses is None:
                    current_nurses = unique_nurses
                    current_start = start_hour
                    current_end = end_hour
                elif current_nurses == unique_nurses:
                    current_end = end_hour
                else:
                    processed_schedule[day].append({
                        'start': current_start,
                        'end': current_end,
                        'nurses': [nurse for nurse in current_nurses if nurse[1] != 'Médico']
                    })
                    medical_schedule[day].append({
                        'start': current_start,
                        'end': current_end,
                        'nurses': [nurse for nurse in current_nurses if nurse[1] == 'Médico']
                    })
                    for nurse, role in current_nurses:
                        nurse_hours[nurse] += (current_end - current_start)

                    current_nurses = unique_nurses
                    current_start = start_hour
                    current_end = end_hour

            if current_nurses is not None:
                processed_schedule[day].append({
                    'start': current_start,
                    'end': current_end,
                    'nurses': [nurse for nurse in current_nurses if nurse[1] != 'Médico']
                })
                medical_schedule[day].append({
                    'start': current_start,
                    'end': current_end,
                    'nurses': [nurse for nurse in current_nurses if nurse[1] == 'Médico']
                })
                for nurse, role in current_nurses:
                    nurse_hours[nurse] += (current_end - current_start)

    unassigned_message = None
    unassigned_details = []
    for day, periods in unassigned_hours.items():
        for period in periods:
            unassigned_details.append(f"{day}: {period[0]} - {period[1]}")

    if unassigned_details:
        unassigned_message = "Las siguientes horas no pudieron ser cubiertas:\n" + "\n".join(unassigned_details)

    return render_template('schedule.html',
                           processed_schedule=processed_schedule,
                           medical_schedule=medical_schedule,
                           nurse_hours=dict(nurse_hours),
                           unassigned_message=unassigned_message)




if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)