from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask import Flask, render_template, request, redirect, url_for
from extensions import db
from scheduler import NurseScheduler
from models import Nurse, Availability
from collections import defaultdict

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///nurses.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

@app.route('/')
def index():
    nurses = Nurse.query.all()
    return render_template('index.html', nurses=nurses)

@app.route('/add_nurse_form')
def add_nurse_form():
    return render_template('add_nurse_form.html')

@app.route('/add_nurse', methods=['POST'])
def add_nurse():
    name = request.form['name']
    nurse = Nurse(name=name)
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
            scheduler.add_availability(nurse.name, availability.day, availability.start_time, availability.end_time)

    schedule, unassigned_hours = scheduler.generate_schedule()

    # Preprocess schedule for Jinja2
    processed_schedule = {day: [] for day in
                          ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']}
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

                if current_nurses is None:
                    current_nurses = nurses
                    current_start = start_hour
                    current_end = end_hour
                elif current_nurses == nurses:
                    current_end = end_hour
                else:
                    processed_schedule[day].append({
                        'start': current_start,
                        'end': current_end,
                        'nurses': current_nurses
                    })
                    for nurse in current_nurses:
                        nurse_hours[nurse] += (current_end - current_start)

                    current_nurses = nurses
                    current_start = start_hour
                    current_end = end_hour

            if current_nurses is not None:
                processed_schedule[day].append({
                    'start': current_start,
                    'end': current_end,
                    'nurses': current_nurses
                })
                for nurse in current_nurses:
                    nurse_hours[nurse] += (current_end - current_start)

    # Create a detailed message for unassigned hours
    unassigned_message = None
    unassigned_details = []
    for day, periods in unassigned_hours.items():
        for period in periods:
            unassigned_details.append(f"{day}: {period[0]} - {period[1]}")

    if unassigned_details:
        unassigned_message = "Las siguientes horas no pudieron ser cubiertas:\n" + "\n".join(unassigned_details)

    return render_template('schedule.html', schedule=processed_schedule, nurse_hours=nurse_hours,
                           unassigned_message=unassigned_message)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)