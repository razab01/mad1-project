from flask import render_template, request, url_for, session, redirect,flash
from controller import app
from applications.db import database
from applications.model import *
import datetime
from sqlalchemy.sql import func


@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    
    if request.method == 'POST':
        # request.form.get('email')
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email_id = email).first()
        if not user:
            # error messages
            flash("User not registered","danger")
            return render_template('login.html')
        
        if user.password != password:
            # error messages
            flash('password is not correct','danger')
            return render_template('login.html')
        
        session['user_id'] = user.user_id
        session['email_id'] = user.email_id
        session['Name'] = user.name
        session['Is_Admin'] = user.is_admin
        if user.is_admin:
            return redirect(url_for('admin'))
        
        if user.is_blocked:
            flash('Account is Blocked')
            return redirect(url_for('login'))
        return redirect(url_for('user'))
    
        
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('email_id', None)
    #session.pop('role', None)
    return redirect(url_for('login'))


@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')
    
    if request.method == 'POST':
        Salutation=request.form.get('Salutation')
        name=request.form.get('name')
        email = request.form.get('email')
        age = request.form.get('age')
        gender=request.form.get('gender')
        mob_no = request.form.get('mob_no')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        qualification = request.form.get('qualification')
        
        #data validation
        if password != confirm_password:
            # flash error messages
            flash("Passwords do not match.", "error")
            return redirect(url_for('signup'))

        if not Salutation or not name or not email or not age or not gender or not mob_no or not password or not confirm_password or not qualification:
            # flash error messages
            flash("All fields are required", "error")
            return redirect(url_for('signup'))

        is_admin = User.query.count() == 0

        user = User.query.filter_by(email_id = email).first()
        if user:
            # flash error messages
            flash('Email is already registered','error')
            return redirect(url_for('signup'))
        
        if User.query.filter_by(mob_no=mob_no).first():
            flash('Mobile number is already registered', 'error')
            return redirect(url_for('signup'))
        
        #new_user_role = Role.query.filter_by(role_name = role).first()
        #if not new_user_role:
            # flash error messages
         #   return redirect(url_for('register'))
        
        new_user = User(
            Salutation=Salutation,
            name = name,
            email_id = email,
            age = age,
            gender=gender,
            mob_no = mob_no,
            password = password,
            qualification = qualification,
            is_admin=is_admin
        )

        database.session.add(new_user)
        database.session.commit()
        return redirect(url_for('login'))
    

    # List all available services (this can be a dropdown in your form)
    
    #subjects = Subject.query.all()
    #return render_template('become_professional.html', services=subjects)


@app.route('/user')
def user():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    if not user:
        return redirect(url_for('login'))

    # Retrieve the latest quiz attempt for the user (if any)
    attempt = QuizAttempt.query.filter_by(user_id=user.user_id)\
                               .order_by(QuizAttempt.id.desc()).first()
    quiz_score = attempt.score if attempt else None

    # Compute subject-wise average scores for the user.
    # Group the QuizAttempt records by subject_id and calculate the average score.
    subject_avgs = database.session.query(
        QuizAttempt.subject_id,
        func.avg(QuizAttempt.score).label('avg_score')
    ).filter(QuizAttempt.user_id == user.user_id)\
     .group_by(QuizAttempt.subject_id).all()

    # Create a dictionary mapping subject names to their average scores.
    subject_avg_scores = {}
    for subject_id, avg_score in subject_avgs:
        subject = Subject.query.get(subject_id)
        if subject:
            subject_avg_scores[subject.name] = round(avg_score, 2)

    return render_template('welcome.html', user=user, quiz_score=quiz_score, subject_avg_scores=subject_avg_scores)


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    user = User.query.get(session['user_id'])
    users = User.query.filter_by(is_admin=False).all()

    # Calculate user activity stats
    active_users = len([u for u in users if not u.is_blocked])
    blocked_users = len([u for u in users if u.is_blocked])

    # Prepare subject average data
    subjects = Subject.query.all()
    subject_data = []
    for subject in subjects:
        # Calculate the average score for this subject using subject_id
        avg_score = (
            database.session.query(func.avg(QuizAttempt.score))
            .filter(QuizAttempt.subject_id == subject.subject_id)
            .scalar() or 0
        )
        subject_data.append({'name': subject.name, 'avg': round(avg_score, 2)})

    if user.is_admin:
        if request.method == 'POST':
            action = request.form.get('action')
            user_id = int(request.form.get('user_id'))
            selected_user = User.query.get(user_id)

            if not selected_user:
                return redirect(url_for('admin'))

            if action == 'delete':
                database.session.delete(selected_user)
                database.session.commit()
            elif action == 'block':
                selected_user.is_blocked = True
                database.session.commit()
            elif action == 'unblock':
                selected_user.is_blocked = False
                database.session.commit()

            return redirect(url_for('admin'))

        # Pass computed stats and subject_data to the template
        return render_template(
            'admin.html',
            user=user,
            users=users,
            active_users=active_users,
            blocked_users=blocked_users,
            subject_data=subject_data
        )

    flash("You don't have permission to access this page.", "error")
    return redirect(url_for('user'))



@app.route('/admin/create_subject', methods=['GET', 'POST'])
def create_subject():
    if request.method == 'POST':
        # Retrieve form data
        subject_name = request.form['subject_name']
        subject_description = request.form['subject_description']
        time_required = request.form['time_required']
        date = request.form['date']
        date = datetime.datetime.strptime(date, "%Y-%m-%dT%H:%M")
        # Add new service to the database
        new_subject = Subject(name=subject_name, description=subject_description,time_required=int(time_required),date=date)
        database.session.add(new_subject)
        database.session.commit()
        flash('Service created successfully!', 'success')
        return redirect(url_for('create_subject'))

    # Fetch all services from the database
    subject = Subject.query.all()
    module = Module.query.all()
    return render_template('create_service.html',subject=subject,module=module)


# Route to delete a service
@app.route('/admin/delete_subject/<int:subject_id>', methods=['POST'])
def delete_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    database.session.delete(subject)
    database.session.commit()
    flash('Service deleted successfully!', 'success')
    return redirect(url_for('create_subject'))


# Route to edit a service
@app.route('/admin/edit_subject/<int:subject_id>', methods=['POST'])
def edit_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    subject.name = request.form['subject_name']
    subject.description = request.form['subject_description']
    subject.time_required = int(request.form['time_required'])
    subject.date = datetime.datetime.strptime(request.form['date'], "%Y-%m-%dT%H:%M")
    database.session.commit()
    flash('Service updated successfully!', 'success')
    return redirect(url_for('create_subject'))


def check_if_quiz_exists(subject_id, module_name):
    module = Module.query.filter_by(subject_id=subject_id, module_name=module_name).first()
    if module and QuizQuestion.query.filter_by(module_name=module_name).first():
        return True
    return False

@app.route('/admin/create_module', methods=['GET', 'POST'])
def create_module():
    if request.method == 'POST':
        # Retrieve form data
        subject_id = request.form['subject_id']
        module_name = request.form['module_name']
        module_description = request.form['module_description']
        # Add new module to the database
        new_module = Module(subject_id=subject_id, module_name=module_name,module_description=module_description)
        database.session.add(new_module)
        database.session.commit()
        flash('Service created successfully!', 'success')
        return redirect(url_for('create_module'))
    subject = Subject.query.all()
    module = Module.query.all()
    return render_template('create_service.html', subject=subject,module=module)

@app.route('/admin/delete_module/<int:subject_id>/<module_name>', methods=['POST'])
def delete_module(subject_id,module_name):
    module = Module.query.filter_by(subject_id=subject_id, module_name=module_name).first_or_404()
    database.session.delete(module)
    database.session.commit()
    flash('Service deleted successfully!', 'success')
    return redirect(url_for('create_module'))

@app.route('/admin/edit_module/<int:subject_id>/<module_name>', methods=['POST'])
def edit_module(subject_id, module_name):
    module = Module.query.filter_by(subject_id=subject_id, module_name=module_name).first_or_404()
    
    new_subject_id = request.form.get('subject_id')
    new_module_name = request.form.get('module_name')
    new_module_description = request.form.get('module_description')
    
    if not new_subject_id or not new_module_name or not new_module_description:
        flash('All fields are required!', 'error')
        return redirect(url_for('create_module'))
    
    # Update the module values (cast subject_id to int if necessary)
    module.subject_id = int(new_subject_id)
    module.module_name = new_module_name
    module.module_description = new_module_description

    database.session.commit()
    flash('Service updated successfully!', 'success')
    return redirect(url_for('create_module'))

@app.route('/quiz_dashboard', methods=['GET', 'POST'])
def quiz_dashboard():
    user = User.query.get(session.get('user_id'))
    if not user:
        flash("Please log in first.", "error")
        return redirect(url_for('login'))
    
    if user.is_admin:
        subjects = Subject.query.all()
        selected_subject_id = request.args.get('selected_subject_id')
        selected_module_name = request.args.get('module_name')
        try:
            question_count = int(request.args.get('question_count', 1))
        except ValueError:
            question_count = 1
        
        modules = []
        questions = []
        edit_question = None
        edit_options = []
        edit_question_id = request.args.get('edit_question_id')
        
        # When a subject is selected, get its modules
        if selected_subject_id:
            modules = Module.query.filter_by(subject_id=selected_subject_id).all()
            # When a module is selected, list its quiz questions
            if selected_module_name:
                questions = QuizQuestion.query.filter_by(
                    subject_id=selected_subject_id,
                    module_name=selected_module_name
                ).all()
        
        # If an edit_question_id is present, load that question and its options
        if edit_question_id:
            try:
                edit_question_id = int(edit_question_id)
                edit_question = QuizQuestion.query.get(edit_question_id)
                if edit_question:
                    edit_options = QuizOption.query.filter_by(question_id=edit_question_id)\
                                                     .order_by(QuizOption.id).all()
            except ValueError:
                pass
        
        # Process inline edit submission if a question is being edited
        if request.method == 'POST' and edit_question:
            edit_question.question_text = request.form.get('edit_question_text')
            updated_options = request.form.getlist('edit_option[]')
            correct_option = request.form.get('edit_correct_option')
            
            if len(edit_options) != len(updated_options):
                flash("Option count mismatch. Please provide all four options.", "error")
            else:
                for i, option in enumerate(edit_options):
                    option.option_text = updated_options[i]
                    option.is_correct = 1 if str(i) == correct_option else 0
                database.session.commit()
                flash("Question updated successfully", "success")
                return redirect(url_for('quiz_dashboard',
                                        selected_subject_id=selected_subject_id,
                                        module_name=selected_module_name))
        
        return render_template('quiz_dashboard.html',
                               base_template="navbar.html",
                               is_admin=True,
                               subjects=subjects,
                               selected_subject_id=selected_subject_id,
                               selected_module_name=selected_module_name,
                               modules=modules,
                               question_count=question_count,
                               questions=questions,
                               edit_question=edit_question,
                               edit_options=edit_options)
    else:
        # USER (non-admin) branch: retrieve enrolled subjects
        enrolled_subjects = (database.session.query(Subject)
                             .join(Enrollment, Subject.subject_id == Enrollment.subject_id)
                             .filter(Enrollment.user_id == user.user_id)
                             .all())
        
        for subject in enrolled_subjects:
            modules = subject.module  # Using the relationship 'module'
            for mod in modules:
                mod.quiz_exists = check_if_quiz_exists(subject.subject_id, mod.module_name)
                attempt = QuizAttempt.query.filter_by(
                    user_id=user.user_id,
                    subject_id=subject.subject_id,
                    module_name=mod.module_name
                ).first()
                if attempt:
                    mod.attempted = True
                    mod.score = attempt.score
                else:
                    mod.attempted = False

                # Fetch previous quiz attempts from the Reattempt table
                mod.old_attempts = Reattempt.query.filter_by(
                    user_id=user.user_id,
                    subject_id=subject.subject_id,
                    module_name=mod.module_name
                ).order_by(Reattempt.attempt_date.desc()).all()
            
            subject.modules = modules
        
        return render_template('quiz_dashboard.html',
                               base_template="navbar.html",
                               is_admin=False,
                               enrolled_subjects=enrolled_subjects)




@app.route('/create_quiz_question', methods=['GET','POST'])
def create_quiz_question():
    user = User.query.get(session.get('user_id'))
    if not user or not user.is_admin:
        flash("You do not have permission to access this page.", "danger")
        return redirect(url_for('quiz_dashboard'))

    # Get common subject and module info (module selection is based on module_name)
    subject_id = request.form.get('subject_id')
    module_name = request.form.get('module_name')
    
    # Retrieve lists of values for each question block
    question_texts = request.form.getlist('question_text[]')
    correct_options = request.form.getlist('correct_option[]')
    
    # For options, each is an array:
    option1_list = request.form.getlist('option1[]')
    option2_list = request.form.getlist('option2[]')
    option3_list = request.form.getlist('option3[]')
    option4_list = request.form.getlist('option4[]')
    
    # Ensure that the number of question blocks matches across all arrays.
    num_questions = len(question_texts)
    for idx in range(num_questions):
        q_text = question_texts[idx]
        correct_option_str = correct_options[idx]
        
        if not correct_option_str:
            flash("Please select the correct option for every quiz question.", "error")
            return redirect(url_for('quiz_dashboard'))
        
        correct_option_index = int(correct_option_str) - 1  # Adjust for 0-based index

        # Create the quiz question. Note: we use module_name field since our model doesn't have module_id.
        question = QuizQuestion(subject_id=subject_id, module_name=module_name, question_text=q_text)
        database.session.add(question)
        database.session.commit()  # Commit here to get the question ID

        # Prepare the list of options for this question
        options = [
            option1_list[idx],
            option2_list[idx],
            option3_list[idx],
            option4_list[idx]
        ]

        # Add each option, marking the correct one appropriately.
        for i, option_text in enumerate(options):
            quiz_option = QuizOption(
                question_id=question.id,
                option_text=option_text,
                is_correct=(i == correct_option_index)
            )
            database.session.add(quiz_option)
    
    database.session.commit()
    flash("Quiz questions added successfully!", "success")
    return redirect(url_for('quiz_dashboard'))






@app.route('/question/delete/<int:question_id>', methods=['POST'])
def delete_question(question_id):
    # Retrieve the question or return a 404 if not found
    question = QuizQuestion.query.get_or_404(question_id)
    
    # Delete the question from the database
    database.session.delete(question)
    database.session.commit()
    
    flash('Question deleted successfully', 'success')
    return redirect(url_for('quiz_dashboard'))


@app.route('/enroll_subject', methods=['GET', 'POST'])
def enroll_subject():
    """ Student enrolls in a subject. """
    user = User.query.get(session.get('user_id'))
    if request.method == 'POST':
        subject_id = request.form.get('subject_id')
        existing_enrollment = Enrollment.query.filter_by(user_id=user.user_id, subject_id=subject_id).first()

        if existing_enrollment:
            flash("You are already enrolled in this subject.", "info")
        else:
            enrollment = Enrollment(user_id=user.user_id, subject_id=subject_id)
            database.session.add(enrollment)
            database.session.commit()
            flash("Successfully enrolled in the subject!", "success")

        return redirect(url_for('quiz_dashboard'))
    
    subject = Subject.query.all()
    module = Module.query.all()
    return render_template('enroll_subject.html', subject=subject,module=module)


@app.route('/take_quiz', methods=['GET', 'POST'])
def take_quiz():
    user = User.query.get(session.get('user_id'))
    if not user:
        flash("Please log in.", "error")
        return redirect(url_for('login'))
    
    subject_id = request.args.get('subject_id')
    module_name = request.args.get('module_name')
    if not subject_id or not module_name:
        flash("Please select both subject and module.", "error")
        return redirect(url_for('quiz_dashboard'))
    try:
        subject_id = int(subject_id)
    except ValueError:
        flash("Invalid subject ID.", "error")
        return redirect(url_for('quiz_dashboard'))
    
    enrollment = Enrollment.query.filter_by(user_id=user.user_id, subject_id=subject_id).first()
    if not enrollment:
        flash("You are not enrolled in this subject.", "danger")
        return redirect(url_for('quiz_dashboard'))
    
    questions = QuizQuestion.query.filter_by(subject_id=subject_id, module_name=module_name).all()
    
    if request.method == 'POST':
        total_questions = len(questions)
        score = 0
        for question in questions:
            submitted = request.form.get(f'question_{question.id}')
            if submitted:
                correct_option = QuizOption.query.filter_by(question_id=question.id, is_correct=True).first()
                if correct_option and int(submitted) == correct_option.id:
                    score += 1
        percentage_score = round((score / total_questions) * 100, 2) if total_questions > 0 else 0

        # Check for an existing attempt
        existing_attempt = QuizAttempt.query.filter_by(
            user_id=user.user_id,
            subject_id=subject_id,
            module_name=module_name
        ).first()
        if existing_attempt:
            # Copy the old attempt's data to a new Reattempt record
            new_reattempt = Reattempt(
                user_id=existing_attempt.user_id,
                subject_id=existing_attempt.subject_id,
                module_name=existing_attempt.module_name,
                score=existing_attempt.score,
                total_questions=existing_attempt.total_questions,
                attempt_date=existing_attempt.attempt_date
            )
            database.session.add(new_reattempt)
            # Delete the old QuizAttempt record
            database.session.delete(existing_attempt)
            # Optionally flush to force deletion before adding new attempt
            database.session.flush()

        # Now create and add the new QuizAttempt
        new_attempt = QuizAttempt(
            user_id=user.user_id,
            subject_id=subject_id,
            module_name=module_name,
            score=percentage_score,
            total_questions=total_questions
        )
        database.session.add(new_attempt)
        database.session.commit()
        flash(f'Your quiz has been submitted! Score: {score}/{total_questions} ({percentage_score}%)', 'success')
        return render_template('take_quiz.html', questions=questions, subject_id=subject_id, module_name=module_name, quiz_score=percentage_score)
    
    if 'quiz_start_time' not in session:
        session['quiz_start_time'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    return render_template('take_quiz.html', questions=questions, subject_id=subject_id, module_name=module_name)