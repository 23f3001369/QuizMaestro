from flask_sqlalchemy import SQLAlchemy
from app import app
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(40), unique=True, nullable=False)
    passhash = db.Column(db.String(512), nullable=False)
    name = db.Column(db.String(80), nullable=True)
    qualification = db.Column(db.String(80), nullable=True)
    dob = db.Column(db.Date, nullable=True)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.passhash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.passhash, password)
class Subject(db.Model):
    # __tablename__ = 'subject'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(200), nullable=True)

    # relationships
    chapters = db.relationship('Chapter', backref='subject', lazy=True)

class Chapter(db.Model):
    __tablename__ = 'chapter'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id' , ondelete="CASCADE"), nullable=False)
    description = db.Column(db.String(200), nullable=True)
    # quiz_date = db.Column(db.Date, nullable=False)
    
    # relationships
    quizzes = db.relationship('Quiz', backref='chapter', cascade="all, delete-orphan" , lazy=True)
    
class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    quiz_date = db.Column(db.Date, nullable=False)
    duration = db.Column(db.Integer, nullable=False, default=30)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id', ondelete = 'CASCADE'), nullable=False)
    # attempts = db.relationship('QuizAttempt', backref='quiz_data', cascade="all, delete-orphan")
    # attempts = db.relationship('QuizAttempt', backref='quiz', overlaps="quiz_attempts,quiz_data")
    attempts = db.relationship('QuizAttempt', back_populates="quiz")
# relationships
    

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    question_text = db.Column(db.String(500), nullable=False)
    option1 = db.Column(db.String(200), nullable=False)
    option2 = db.Column(db.String(200), nullable=False)
    option3 = db.Column(db.String(200), nullable=False)
    option4 = db.Column(db.String(200), nullable=False)
    correct_option = db.Column(db.Integer, nullable=False)



class QuizAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id', ondelete="CASCADE"), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    total_questions = db.Column(db.Integer, nullable=False, default=0)
    date_attempted = db.Column(db.DateTime, default=datetime.utcnow())

    # Relationships
    # user = db.relationship('User', backref=db.backref('attempts', lazy=True))
    # quiz = db.relationship('Quiz', backref=db.backref('quiz_attempts', lazy=True))

    # quiz = db.relationship('Quiz', backref=db.backref('attempts', lazy=True), overlaps="attempts,quiz_data")
    # user = db.relationship('User', backref=db.backref('quiz_attempts', lazy=True))

    quiz = db.relationship('Quiz', back_populates="attempts")
    user = db.relationship('User', backref='quiz_attempts')

# Create Database if it doesn't exist
with app.app_context():
    db.create_all()

    # create admin if admin doesn't exist
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', password='admin123', name='admin', is_admin=True)
        db.session.add(admin)
        db.session.commit()


