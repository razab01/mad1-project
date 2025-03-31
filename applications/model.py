from applications.db import database
import datetime


class User(database.Model):
    __tablename__ = 'user'  # Explicitly define table name
    user_id = database.Column(database.Integer, primary_key=True)
    Salutation = database.Column(database.String(), nullable=False)
    name = database.Column(database.String(), nullable=False)
    email_id = database.Column(database.String(100), unique=True, nullable=False)
    age = database.Column(database.Integer, nullable=False)
    gender = database.Column(database.String(), nullable=False)
    mob_no = database.Column(database.String(10), unique=True, nullable=False)
    password = database.Column(database.String(100), nullable=False)
    qualification = database.Column(database.String(100), nullable=False)
    is_admin = database.Column(database.Boolean, default=False)
    is_blocked = database.Column(database.Boolean, default=False)

    
    def __repr__(self):
        return f"<User {self.name}>"


class Subject(database.Model):
    __tablename__ = 'subject'  # Explicitly define table name
    subject_id = database.Column(database.Integer, primary_key=True)
    name = database.Column(database.String(100), nullable=False)
    description = database.Column(database.Text, nullable=False)
    time_required = database.Column(database.Integer, nullable=False)
    date = database.Column(database.DateTime, nullable=True) 

    module = database.relationship('Module', back_populates='subject', uselist=True,cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Subject {self.name}>"

class Module(database.Model):
    __tablename__= 'module'
    subject_id = database.Column(database.Integer,database.ForeignKey('subject.subject_id'), nullable=False,primary_key=True)
    module_name = database.Column(database.String(150), nullable=False,primary_key=True)
    module_description = database.Column(database.Text)

    subject = database.relationship('Subject', back_populates='module',cascade="all, delete-orphan",single_parent=True)  # Define back reference
    
    def __repr__(self):
        return f"<Module {self.module_name}>"
    

class Enrollment(database.Model):
    __tablename__ = 'enrollment'
    enrollment_id = database.Column(database.Integer, primary_key=True)
    user_id = database.Column(database.Integer, database.ForeignKey('user.user_id'), nullable=False)
    subject_id = database.Column(database.Integer, database.ForeignKey('subject.subject_id'), nullable=False)

    def __repr__(self):
        return f"<Enrollment User:{self.user_id} Subject:{self.subject_id}>"


class QuizQuestion(database.Model):
    __tablename__ = 'quiz_question'
    id = database.Column(database.Integer, primary_key=True)
    subject_id = database.Column(database.Integer, database.ForeignKey('subject.subject_id'), nullable=False)
    # Since Module has a composite key, we'll store the module name as text here.
    module_name = database.Column(database.String(150), nullable=False)
    question_text = database.Column(database.Text, nullable=False)

    options = database.relationship('QuizOption', backref='question', cascade="all, delete-orphan", lazy=True)

    def __repr__(self):
        return f"<QuizQuestion {self.id}>"


class QuizOption(database.Model):
    __tablename__ = 'quiz_option'
    id = database.Column(database.Integer, primary_key=True)
    question_id = database.Column(database.Integer, database.ForeignKey('quiz_question.id'), nullable=False)
    option_text = database.Column(database.String(200), nullable=False)
    is_correct = database.Column(database.Integer, nullable=False)

    def __repr__(self):
        return f"<QuizOption {self.option_text} Correct:{self.is_correct}>"
    

class QuizAttempt(database.Model):
    __tablename__ = 'quiz_attempt'
    id = database.Column(database.Integer, primary_key=True)
    user_id = database.Column(database.Integer, database.ForeignKey('user.user_id'), nullable=False)
    subject_id = database.Column(database.Integer, database.ForeignKey('subject.subject_id'), nullable=False)
    module_name = database.Column(database.String(150), nullable=False)
    score = database.Column(database.Float, nullable=False)
    total_questions = database.Column(database.Integer, nullable=False)
    attempt_date = database.Column(database.DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return f"<QuizAttempt user_id={self.user_id} subject_id={self.subject_id} module_name={self.module_name} score={self.score}>"

class Reattempt(database.Model):
    __tablename__ = 'reattempt'
    id = database.Column(database.Integer, primary_key=True)
    user_id = database.Column(database.Integer, database.ForeignKey('user.user_id'), nullable=False)
    subject_id = database.Column(database.Integer, database.ForeignKey('subject.subject_id'), nullable=False)
    module_name = database.Column(database.String(150), nullable=False)
    score = database.Column(database.Float, nullable=False)
    total_questions = database.Column(database.Integer, nullable=False)
    attempt_date = database.Column(database.DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return f"<Reattempt user_id={self.user_id} subject_id={self.subject_id} module_name={self.module_name} score={self.score}>"