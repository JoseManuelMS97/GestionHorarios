from extensions import db

class Nurse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    availabilities = db.relationship('Availability', backref='nurse', lazy=True)

class Availability(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nurse_id = db.Column(db.Integer, db.ForeignKey('nurse.id'), nullable=False)
    day = db.Column(db.String(50), nullable=False)
    start_time = db.Column(db.String(5), nullable=False)
    end_time = db.Column(db.String(5), nullable=False)
