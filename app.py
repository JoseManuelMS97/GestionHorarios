from flask import Flask, render_template, request, redirect, url_for
from extensions import db
from scheduler import NurseScheduler
from models import Nurse, Availability

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///nurses.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db.init_app(app)

@app.route('/')
def index():
    nurses = Nurse.query.all()
    return render_template('index.html', nurses=nurses)

@app.route('/add_nurse', methods=['POST'])
def add_nurse():
    name = request.form['name']
    nurse = Nurse(name=name)
    db.session.add(nurse)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/add_availability/<int:nurse_id>', methods=['POST'])
def add_availability(nurse_id):
    day = request.form['day']
    start_time = request.form['start_time']
    end_time = request.form['end_time']
    availability = Availability(nurse_id=nurse_id, day=day, start_time=start_time, end_time=end_time)
    db.session.add(availability)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/generate_schedule')
def generate_schedule():
    nurses = Nurse.query.all()
    required_hours = {
        'Lunes': [('09:00', '14:00'), ('15:00', '20:00')],
        'Martes': [('09:00', '14:00'), ('15:00', '20:00')],
        'Miercoles': [('09:00', '14:00'), ('15:00', '20:00')],
        'Jueves': [('09:00', '14:00'), ('15:00', '20:00')],
        'Viernes': [('09:00', '14:00'), ('15:00', '20:00')]
    }

    scheduler = NurseScheduler(required_hours)
    for nurse in nurses:
        for availability in nurse.availabilities:
            scheduler.add_availability(nurse.name, availability.day, availability.start_time, availability.end_time)

    schedule, unassigned_hours = scheduler.generate_schedule()
    return render_template('schedule.html', schedule=schedule, unassigned_hours=unassigned_hours)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

"""scheduler.add_availability('Arya', 'Lunes', '09:00', '17:00')
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
    scheduler.add_availability('Coffee', 'Martes', '15:00', '20:00')"""