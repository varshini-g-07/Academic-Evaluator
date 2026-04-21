from app import app, mongo, login
from app.forms import CgpaForm, TeacherRegForm, TeacherLoginForm, AddStudent, StudentLoginForm, PasswordChange
from flask import render_template, url_for, redirect, flash, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, current_user, login_user, logout_user, login_required
from bson.objectid import ObjectId
from functools import wraps

class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.email = user_data.get('email')
        self.rollno = user_data.get('rollno')
        self.userName = user_data.get('teacherName') or user_data.get('studentName')
        self.role = user_data.get('role')

@login.user_loader
def load_user(id):
    teacher_data = mongo.db['teachers'].find_one({"_id": ObjectId(id)})
    if teacher_data:
        teacher_data['role'] = 'teacher'
        return User(teacher_data)
    
    student_data = mongo.db['students'].find_one({"_id": ObjectId(id)})
    if student_data:
        student_data['role'] = 'student'
        return User(student_data)
    
    return None

def teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'teacher':
            return redirect(url_for('teacherLogin'))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/teacher-register", methods = ['GET', 'POST'])
def teacherRegister():
    if current_user.is_authenticated:
        return redirect(url_for('classroom'))

    form = TeacherRegForm()
    if form.validate_on_submit():
        email = form.email.data
        old_user = mongo.db['teachers'].find_one({"email": email})
        if old_user:
            flash("Teacher already exists!")
        else:
            password = form.password.data
            teacherName = form.teacherName.data
            hash_pass = generate_password_hash(password)
            mongo.db['teachers'].insert_one({
                "teacherName": teacherName,
                "email": email,
                "password": hash_pass,
                "role": 'teacher'
            })
            flash("Account created successfully!")
        return redirect(url_for('teacherLogin'))
    return render_template("teacher-reg.html", form = form)

@app.route("/teacher-login", methods = ['GET', 'POST'])
def teacherLogin():
    if current_user.is_authenticated:
        return redirect(url_for('classroom'))

    form = TeacherLoginForm()
    if form.validate_on_submit():
        email = form.email.data
        check_user = mongo.db['teachers'].find_one({"email": email})
        if check_user:
            password = form.password.data
            check_pass = check_password_hash(check_user['password'], password)
            if check_pass:
                teacher = User(check_user)
                login_user(teacher)
                return redirect(url_for('classroom')) # also to change
        else:
            flash("Incorrect username or password!")
    return render_template("teacher-login.html", form = form)

@app.route("/calculate-cgpa", methods=['GET', 'POST'])
@login_required
@teacher_required
def calculator():
    addStudent = AddStudent()
    form = CgpaForm()
    step = request.args.get('step', 1, type=int)

    if step == 1 and addStudent.validate_on_submit():
        studentName = addStudent.studentName.data
        rollno = addStudent.rollno.data
        check_student = mongo.db.students.find_one({"rollno": rollno})
        if check_student:
            return redirect(url_for('calculator'))
        else:
            mongo.db.students.insert_one({
                "studentName": studentName,
                "rollno": rollno,
                "password": generate_password_hash(str(rollno)),
                "teacher": current_user.id,
                "role": 'student',
            })
            return redirect(url_for('calculator', step=2, rollno=rollno))
    
    current_roll = None
    if step == 2:
        rollno = request.args.get('rollno')
        current_roll = int(rollno)

    if step == 2 and form.validate_on_submit():
        if form.add_subject.data:
            form.items.append_entry()
        
        if form.submit.data:
            marks = [(i.marks.data*0.6)+i.internal_marks.data for i in form.items]
            subjects = [i.sub.data for i in form.items]
            max_credits = [i.credits.data for i in form.items]

            grade_points = list(map(lambda x: 10 if x > 90 else 9 if x > 80 else 8 if x > 70 else 7 if x > 60 else 6 if x > 50 else 0, marks))
            total_credits = sum(a * b for a, b in zip(grade_points, max_credits))
            grades = list(map(lambda x: "O" if x == 10 else "A" if x == 9 else "B" if x == 8 else "C" if x == 7 else "D" if x == 6 else "U", grade_points))
            
            cgpa = total_credits/sum(max_credits)           
            performance = [
                {'subject': s, 'mark': m, 'grade': g}
                for s, m, g in zip(subjects, marks, grades)
            ]

            mongo.db.students.update_one(
                {'rollno': current_roll},
                {'$set': {
                    'cgpa': cgpa,
                    'performance': performance
                }}
            )

            return redirect(url_for('classroom')) #redirect to dashboard

        if form.reset.data:
            form = CgpaForm(formdata=None)

    return render_template("form.html", form = form, addStudent = addStudent, step = step)

@app.route('/student-login', methods = ['GET', 'POST'])
def studentLogin():
    if current_user.is_authenticated:
        return redirect(url_for('classroom'))
    
    form = StudentLoginForm()
    if form.validate_on_submit():
        rollno = form.rollno.data
        password = form.password.data
        check_student = mongo.db.students.find_one({'rollno': rollno})
        if check_student:
            verify_pass = check_password_hash(check_student['password'], password)
            if verify_pass:
                student = User(check_student)
                login_user(student)

                check_pass = (str(password) == str(check_student['rollno']))
                if check_pass:
                    return redirect(url_for('changePassword'))
                else:
                    return redirect(url_for('dashboard')) #eheh change to class view
        else:
            flash('incorrect username or password!')   
  
    return render_template("student-login.html", form = form)

@app.route('/change-password', methods = ['GET', 'POST'])
@login_required
def changePassword():
    form = PasswordChange()
    if form.validate_on_submit():
        old_pass = form.current_pass.data
        new_pass = form.new_pass.data
        user_role = current_user.role
        collection = mongo.db.teachers if user_role == 'teacher' else mongo.db.students
        user = collection.find_one({"_id": ObjectId(current_user.id)})

        validate = check_password_hash(user['password'], old_pass)
        if validate:
            hash_pass = generate_password_hash(new_pass)
            collection.update_one(
                {"_id": ObjectId(current_user.id)},
                {"$set": {"password": hash_pass}}
            )

            logout_user()
            if user_role == 'teacher':
                return redirect(url_for('teacherLogin'))
            else:
                return redirect(url_for('studentLogin'))
        
        else:
            flash("Enter correct details!")
    
    return render_template("change-password.html", form = form)

@app.route('/student-dashboard')
@login_required
def dashboard():
    mark_details = mongo.db.students.find_one({"_id": ObjectId(current_user.id)})
    return render_template("student-dashboard.html", marks = mark_details)

@app.route('/classroom')
@login_required
def classroom():
    if current_user.role == 'teacher':
        all_students = mongo.db.students.find({"teacher": current_user.id})
    else:
        me = mongo.db.students.find_one({"_id": ObjectId(current_user.id)})
        all_students = mongo.db.students.find({"teacher": me['teacher']})

    return render_template('classroom.html', students=all_students)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))