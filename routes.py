from functools import wraps
from flask import Flask, render_template, Response,request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Subject, Chapter,Quiz, Question, QuizAttempt
import datetime
import re

from app import app

def auth_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to continue')
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    return inner

def admin_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            flash('Please login to continue')
            return redirect(url_for('login'))

        user = User.query.get(user_id)
        if not user:
            session.pop('user_id', None)  # Remove invalid session
            flash('User does not exist. Please login again.')
            return redirect(url_for('login'))

        if not user.is_admin:
            # flash('You are not authorized to access this page', 'danger')
            return redirect(url_for('index'))
        
        return func(*args, **kwargs)
    return inner

@app.route('/admin')
@admin_required
def admin():
    
    # user_id = session.get('user_id')
    # query = request.args.get('query', '').strip().lower()
    # subjects = Subject.query.all()

    # if query:
    #     subjects = [subject for subject in subjects if query in subject.name.lower()]

    user_id = session.get('user_id')
    subjects = Subject.query.all()

    query = request.args.get('query', '').strip().lower()
    if query:
        subjects = [subject for subject in subjects if
                    subject.name and query in subject.name.lower() or
                    subject.id and str(subject.id) in query 
                    ]

    if not user_id:
        flash('Please login to continue', 'warning')
        return redirect(url_for('login'))

    user = User.query.get(user_id)
    if not user:
        session.pop('user_id', None)
        flash('User does not exist. Please login again.')
        return redirect(url_for('login'))

    return render_template('admin.html', user=user, subjects=subjects)


# from flask import session, redirect, url_for

# @app.route('/profile')
# @auth_required
# def profile():
#     user = User.query.get(session['user_id'])
    
#     # Get all attempted quizzes
#     attempted_quizzes = QuizAttempt.query.filter_by(user_id=user.id).all()

#     # Initialize subject analysis dictionary
#     subject_analysis = {}

#     for attempt in attempted_quizzes:
#         if not attempt.quiz or not attempt.quiz.chapter or not attempt.quiz.chapter.subject:
#             continue  # Skip if any relation is missing (deleted)

#         quiz = attempt.quiz
#         chapter = quiz.chapter
#         subject = chapter.subject
#         subject_name = subject.name

#         if subject_name not in subject_analysis:
#             subject_analysis[subject_name] = {
#                 'total_quizzes': 0,
#                 'score': 0,
#                 'total_questions': 0
#             }

#         subject_analysis[subject_name]['total_quizzes'] += 1
#         subject_analysis[subject_name]['score'] += attempt.score
#         subject_analysis[subject_name]['total_questions'] += attempt.total_questions

#     # Compute average score safely
#     for subject in subject_analysis:
#         if subject_analysis[subject]['total_questions'] > 0:
#             subject_analysis[subject]['average_score'] = (
#                 subject_analysis[subject]['score'] / subject_analysis[subject]['total_questions'] * 100
#             )
#         else:
#             subject_analysis[subject]['average_score'] = 0  # Avoid division error

#     return render_template(
#         'profile.html', 
#         user=user, 
#         attempted_quizzes=attempted_quizzes, 
#         subject_analysis=subject_analysis
#     )



# @app.route('/profile')
# @auth_required
# def profile():
#     user_id = session.get('user_id')
#     if not user_id:
#         return redirect(url_for('login'))

#     user = User.query.get(user_id)
#     if not user:
#         return "User not found", 404

#     # Get quiz attempts for summary
#     quiz_attempts = QuizAttempt.query.filter_by(user_id=user_id).all()
    
#     subject_analysis = {}
#     for attempt in quiz_attempts:
#         quiz = Quiz.query.get(attempt.quiz_id)
#         chapter = Chapter.query.get(quiz.chapter_id) if quiz else None
#         subject = Subject.query.get(chapter.subject_id) if chapter else None

#         if subject:
#             if subject.name not in subject_analysis:
#                 subject_analysis[subject.name] = {'total_quizzes': 0, 'total_score': 0, 'total_questions': 0}
            
#             subject_analysis[subject.name]['total_quizzes'] += 1
#             subject_analysis[subject.name]['total_score'] += attempt.score
#             subject_analysis[subject.name]['total_questions'] += attempt.total_questions

#     for subject in subject_analysis:
#         if subject_analysis[subject]['total_questions'] > 0:
#             subject_analysis[subject]['average_score'] = (
#                 subject_analysis[subject]['total_score'] / subject_analysis[subject]['total_questions'] * 100
#             )
#         else:
#             subject_analysis[subject]['average_score'] = 0

    
#     return render_template(
#         'profile.html',
#         user=user,
#         attempted_quizzes=quiz_attempts,
#         subject_analysis=subject_analysis
#     )

@app.route('/profile')
@auth_required
def profile():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    user = User.query.get(user_id)
    if not user:
        return "User not found", 404

    quiz_attempts = QuizAttempt.query.filter_by(user_id=user_id).all()

    subject_analysis = {}
    attempted_quizzes = []
    
    for attempt in quiz_attempts:
        quiz = Quiz.query.get(attempt.quiz_id)
        chapter = Chapter.query.get(quiz.chapter_id) if quiz else None
        subject = Subject.query.get(chapter.subject_id) if chapter else None

        attempted_quizzes.append({
            "quiz_title": quiz.title,
            "score": attempt.score,
            "total_questions": attempt.total_questions,
            "date_attempted": attempt.date_attempted.strftime('%Y-%m-%d')
        })
        if subject:
            if subject.name not in subject_analysis:
                subject_analysis[subject.name] = {'total_quizzes': 0, 'total_score': 0, 'total_questions': 0}
            
            subject_analysis[subject.name]['total_quizzes'] += 1
            subject_analysis[subject.name]['total_score'] += attempt.score
            subject_analysis[subject.name]['total_questions'] += attempt.total_questions

    for subject in subject_analysis:
        if subject_analysis[subject]['total_questions'] > 0:
            subject_analysis[subject]['average_score'] = (
                subject_analysis[subject]['total_score'] / subject_analysis[subject]['total_questions']
            )
        else:
            subject_analysis[subject]['average_score'] = 0

    # ✅ Generate Pie Chart (Quiz Attempts Distribution)
    pie_chart = None
    if subject_analysis:
        labels = list(subject_analysis.keys())
        values = [data['total_quizzes'] for data in subject_analysis.values()]
        
        plt.figure(figsize=(5, 5))
        plt.pie(values, labels=labels, autopct='%1.1f%%', 
                #colors=plt.cm.Paired.colors,
                colors=['#ff9999','#66b3ff','#99ff99','#ffcc99'])
        plt.title("Quiz Attempts per Subject")

        pie_img = io.BytesIO()
        plt.savefig(pie_img, format='png', bbox_inches="tight")
        pie_img.seek(0)
        pie_chart = base64.b64encode(pie_img.getvalue()).decode()
        plt.close()

    # ✅ Generate Bar Chart (Average Score per Subject)
    bar_chart = None
    if subject_analysis:
        labels = list(subject_analysis.keys())
        values = [data['average_score'] * 100 for data in subject_analysis.values()]
        
        plt.figure(figsize=(6, 4))
        plt.bar(labels, values, color=['#5a9', '#9c5', '#e55', '#77f'])
        plt.xlabel("Subjects")
        plt.ylabel("Average Score (%)")
        plt.title("Average Score per Subject")
        plt.xticks(rotation=45)

        bar_img = io.BytesIO()
        plt.savefig(bar_img, format='png', bbox_inches="tight")
        bar_img.seek(0)
        bar_chart = base64.b64encode(bar_img.getvalue()).decode()
        plt.close()

    return render_template(
        'profile.html',
        user=user,
        attempted_quizzes=quiz_attempts,
        subject_analysis=subject_analysis,
        pie_chart=pie_chart,
        bar_chart=bar_chart
    )





@app.route('/profile', methods=['POST'])
@auth_required
def profile_post():
    user = User.query.get(session['user_id'])
    username = request.form.get('username')
    name = request.form.get('name')
    qualification = request.form.get('qualification')
    dob = request.form.get('dob')
    password = request.form.get('password')
    cpassword = request.form.get('cpassword')
    if username == '' or password == '' or cpassword == '':
        flash('Username or password cannot be empty')
        return redirect(url_for('profile'))
    if not user.check_password(cpassword): 
        flash('Incorrect password')
        return redirect(url_for('profile'))
    if User.query.filter_by(username=username).first() and user.username != username:
        flash('User with this username already exists. Please choose some other username.')
        return redirect(url_for('profile'))
    user.username = username
    user.name = name
    user.password = password
    user.qualification = qualification
    user.dob = dob
    db.session.commit()

    flash('Profile updated successfully')
    return redirect(url_for('profile'))


@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():    
    # return "hello"
    username = request.form.get('username')
    password = request.form.get('password')
    
    if username == '' or password == '':
        flash('Username or password cannot be empty')
        return redirect(url_for('login'))
    user= User.query.filter_by(username=username).first()
    if not user:
        flash('User does not exist. Please Register yourself first.')
        return redirect(url_for('register'))
    if not user.check_password(password):
        flash('Incorrect password')
        return redirect(url_for('login'))
    # login successful
    session['user_id'] = user.id
    return redirect(url_for('profile'))
# redirect(url_for('index'))
    

    
@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register_post():
    username = request.form.get('username')
    password = request.form.get('password')
    name = request.form.get('name')
    qualification = request.form.get('qualification')
    dob = request.form.get('dob')
    if len(name) > 10:
        flash("Name can't be longer than 10 chars")
        return redirect(url_for('register'))
    if username == '' or password == '' or name == '':
        flash('Username or password cannot be empty')
        return redirect(url_for('register'))
    if User.query.filter_by(username=username).first():
        flash('User with this username already exists. Please choose some other username.')
        return redirect(url_for('register'))
    user = User(username=username, password=password, name=name, qualification=qualification, dob=dob)
    db.session.add(user)
    db.session.commit()
    flash('User registered successfully')
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))


@app.route('/subject/add')
@admin_required
def add_subject():
    return render_template('subject/add.html', user = User.query.get(session['user_id']))

@app.route('/subject/add', methods=['POST'])
@admin_required
def add_subject_post():
    name = request.form.get('name')
    description = request.form.get('description')
    if name == '':
        flash('Subject cannot be empty')
        return redirect(url_for('add_subject'))
    if len(name) > 80:
        flash('Subject cannot be of more than 80 characters')
        return redirect(url_for('add_subject'))
    
    subject = Subject(name=name, description=description)
    db.session.add(subject)
    db.session.commit()
    flash('Subject added successfully')
    return redirect(url_for('admin'))

@app.route('/subject/<int:subject_id>/show')
@admin_required
def show_subject(subject_id):
    
    user = User.query.get(session['user_id'])
    subject = Subject.query.get_or_404(subject_id)
    # chapters = Chapter.query.filter_by(subject_id=subject_id).all()  # Assuming chapters are a relationship
    query = request.args.get('query', '').strip().lower()
    # chapters = Chapter.query.all()
    chapters= subject.chapters

    # if query:
    #     chapters = [ch for ch in subject.chapters if query in ch.name.lower()]
    # return render_template('subject/show.html', user = user, subject = subject, chapters = chapters, query = query)

    if query:
        chapters = [chapter for chapter in chapters if 
                   (chapter.id and str(chapter.id) in query) or
                #    (chapter.subject.name and query in chapter.subject.name.lower()) or
                   (chapter.name and query in chapter.name.lower()) ]

    return render_template('subject/show.html', user = user, subject = subject, chapters = chapters, query = query)

@app.route('/chapter/add')
@admin_required
def add_chapter():
    subject_id = -1
    args = request.args
    if 'subject_id' in args:
        if Subject.query.get(int(args.get('subject_id'))):
            subject_id = int(args.get('subject_id'))
            # flash('subject does not exist')
            # return redirect(url_for('admin'))
    return render_template('chapter/add.html', 
                           user = User.query.get(session['user_id']), 
                           subject_id = subject_id,
                           subjects = Subject.query.all(),
                        #    nowstring = datetime.datetime.now().strftime("%Y-%m-%d"),
                           )

@app.route('/chapter/add', methods=['POST'])
@admin_required
def add_chapter_post():
    name = request.form.get('name')
    description = request.form.get('description')
    # subject = request.form.get('subject')
    subject_id = int(request.form.get('subject'))  
    subject = Subject.query.get_or_404(subject_id) 
   


    if not name:
        flash('Chapter name cannot be empty.')
        return redirect(url_for('add_chapter'))

    if not subject_id:
        flash('Subject ID cannot be empty.')
        return redirect(url_for('add_chapter'))

    subject = Subject.query.get_or_404(int(subject_id))  

    chapter = Chapter(name=name, subject_id=subject.id, description=description)  
    db.session.add(chapter)
    db.session.commit()

    flash('Chapter added successfully.')
    return redirect(url_for('show_subject', subject_id=subject.id))

    

    

    

@app.route('/chapter/<int:chapter_id>edit')
@admin_required
def edit_chapter(chapter_id):
    return render_template('chapter/edit.html', user = User.query.get(session['user_id']), 
                           chapter = Chapter.query.get(chapter_id),
                           subjects = Subject.query.all())
                        #    nowstring = datetime.datetime.now().strftime("%Y-%m-%d"),
                        #    quiz_date = Chapter.query.get(chapter_id).quiz_date.strftime("%Y-%m-%d"))


@app.route('/chapter/<int:chapter_id>edit', methods=['POST'])
@admin_required
def edit_chapter_post(chapter_id):
    name = request.form.get('name')
    description = request.form.get('description')
    subject = request.form.get('subject')
    
    if name == '':
        flash('Chapter name cannot be empty.')
        return redirect(url_for('add_chapter'))
    if len(name)>80:
        flash('Chapter name cannot be greater than 80 characters.')
        return redirect(url_for('add_chapter'))
    if subject == '':  
        flash('Subject cannot be empty.')
        return redirect(url_for('add_chapter'))
    subject = Subject.query.get(subject)
    if not subject:
        flash('Subject does not exist.')
        return redirect(url_for('add_chapter'))
    
    chapter = Chapter.query.get(chapter_id)
    chapter.name = name
    chapter.description = description
    chapter.subject = subject

    # chapter.quiz_date = quiz_date
    db.session.add(chapter)
    db.session.commit()
    flash('Chapter edited successfully')
    return redirect(url_for('show_subject', subject_id=subject.id))

@app.route('/chapter/<int:chapter_id>delete')
@admin_required 
def delete_chapter(chapter_id):
    chapter = Chapter.query.get(chapter_id)
    if chapter is None:
        flash('chapter does not exist')
        return redirect(url_for('admin'))
    return render_template('chapter/delete.html', user = User.query.get(session['user_id']), chapter = chapter) 

@app.route('/chapter/<int:chapter_id>delete', methods=['POST'])
@admin_required
def delete_chapter_post(chapter_id):
    chapter = Chapter.query.get(chapter_id)
    if not chapter:
        flash('Chapter not found!', 'danger')
        return redirect(url_for('admin'))

    # Delete quizzes related to the chapter
    quizzes = Quiz.query.filter_by(chapter_id=chapter.id).all()
    for quiz in quizzes:
        QuizAttempt.query.filter_by(quiz_id=quiz.id).delete()  # Delete quiz attempts
        db.session.delete(quiz)  # Delete the quiz

    db.session.delete(chapter)  # Finally, delete the chapter
    db.session.commit()
    flash('Chapter and related data deleted successfully!', 'success')
    return redirect(url_for('admin'))

@app.route('/chapter/<int:chapter_id>show')
@admin_required
def show_chapter(chapter_id):
    user = User.query.get(session['user_id'])
    chapter = Chapter.query.get_or_404(chapter_id)
    quizzes = Quiz.query.filter_by(chapter_id=chapter_id).all()
    query = request.args.get('query', '').strip().lower()
    
    # if query:
    #     quizzes = [quiz for quiz in quizzes if query in quiz.title.lower()]
    # return render_template('admin/users.html', users=users, query=query)
    if query:
        quizzes = [quiz for quiz in quizzes if 
                   (quiz.id and str(quiz.id) in query) or
                   (quiz.title and query in quiz.title.lower()) or
                #    (quiz.chapter.name and query in quiz.chapter.name.lower()) or
                   (quiz.quiz_date and query in quiz.quiz_date.strftime("%d/%m/%Y")) ]


    return render_template('chapter/show.html', user = user, chapter = chapter, quizzes = quizzes, query = query)
    



@app.route('/subject/<int:subject_id>edit')
@admin_required
def edit_subject(subject_id):
    return render_template('subject/edit.html', user = User.query.get(session['user_id']), subject = Subject.query.get(subject_id))   

@app.route('/subject/<int:subject_id>edit', methods=['POST'])
@admin_required
def edit_subject_post(subject_id):
    subject = Subject.query.get(subject_id)
    description = request.form.get('description')
    name = request.form.get('name') 
    if name == '':
        flash('Subject name cannot be empty')
        return redirect(url_for('edit_subject', subject_id=subject_id))
    if len(name) > 80:
        flash('Subject name cannot be more than 80 characters')
        return redirect(url_for('edit_subject', subject_id=subject_id))
    subject.name = name
    subject.description = description
    db.session.commit()
    flash('Subject updated successfully')
    return redirect(url_for('admin'))


@app.route('/subject/<int:subject_id>delete')
@admin_required
def delete_subject(subject_id):
    subject = Subject.query.get(subject_id)
    if subject is None:
        flash('Subject does not exist')
        return redirect(url_for('admin'))
    return render_template('subject/delete.html', user = User.query.get(session['user_id']), subject = subject)   

@app.route('/subject/<int:subject_id>delete', methods=['POST'])
@admin_required
def delete_subject_post(subject_id):
    subject = Subject.query.get(subject_id)
    if subject is None:
        flash('Subject does not exist')
        return redirect(url_for('admin'))
    chapters = Chapter.query.filter_by(subject_id=subject_id).all()
    for chapter in chapters:
        quizzes = Quiz.query.filter_by(chapter_id=chapter.id).all()
        for quiz in quizzes:
            QuizAttempt.query.filter_by(quiz_id=quiz.id).delete()  # Delete quiz attempts
            db.session.delete(quiz)
        db.session.delete(chapter)
    db.session.delete(subject)
    db.session.commit()
    
    flash('Subject and related chapters and quizzes deleted successfully')
    return redirect(url_for('admin'))


@app.route('/quiz/add/<int:chapter_id>', methods=['GET', 'POST'])
@auth_required
def add_quiz(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)

    if request.method == 'POST':
        title = request.form['title']
        quiz_date_str = request.form['quiz_date']  
        
        quiz_date = datetime.datetime.strptime(quiz_date_str, "%Y-%m-%d").date()
        duration = request.form.get('duration')  # Get duration

        if not duration:
            flash("Duration cannot be empty!")
            return redirect(url_for('add_quiz', chapter_id=chapter_id))

        new_quiz = Quiz(title=title, quiz_date=quiz_date,duration=int(duration), chapter_id=chapter_id)
        db.session.add(new_quiz)
        db.session.commit()

        flash('Quiz added successfully!')
        return redirect(url_for('show_chapter', chapter_id=chapter_id))

    return render_template('quiz/add.html', chapter=chapter)

@app.route('/quiz/<int:quiz_id>')
@auth_required
def show_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id) 
    questions = Question.query.filter_by(quiz_id=quiz_id).all() 
    print(f"Quiz ID: {quiz.id}, Questions: {[(q.id, q.question_text) for q in questions]}")
    return render_template('quiz/show.html', quiz=quiz, questions=questions)

@app.route('/quiz/edit/<int:quiz_id>', methods=['GET','POST'])
@auth_required
def edit_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    
    if request.method == 'POST':
        title = request.form.get('title')
        quiz_date_str = request.form.get('quiz_date')
        # duration = request.form.get('duration')
        # duration = int(duration)

        if title:
            quiz.title = title

        if quiz_date_str:
            quiz.quiz_date = datetime.datetime.strptime(quiz_date_str, '%Y-%m-%d')

        # if duration:
        #     quiz.duration = duration + 20

        db.session.commit()
        flash('Quiz updated successfully!', 'success')
        return redirect(url_for('show_chapter', chapter_id=quiz.chapter_id))

    return render_template('quiz/edit.html', quiz=quiz)


# @app.route('/quiz/delete/<int:quiz_id>', methods=['POST'])
# @auth_required
# def delete_quiz(quiz_id):
#     quiz = Quiz.query.get_or_404(quiz_id)
#     if quiz is None:

#         flash('Quiz not found!', 'danger')
#         return redirect(url_for('admin'))

#     QuizAttempt.query.filter_by(quiz_id=quiz.id).delete()  # Delete quiz attempts
#     db.session.delete(quiz)  # Delete the quiz
#     db.session.commit()
#     flash('Quiz deleted successfully!', 'success')
#     return redirect(url_for('show_chapter', chapter_id=quiz.chapter_id))  


@app.route('/quiz/<int:quiz_id>delete')
@admin_required 
def delete_quiz(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    if quiz is None:
        flash('Quiz does not exist')
        return redirect(url_for('admin'))
    return render_template('quiz/delete.html', user = User.query.get(session['user_id']), quiz = quiz)

@app.route('/quiz/<int:quiz_id>delete', methods=['POST'])
@admin_required
def delete_quiz_post(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    if quiz is None:
        flash('Quiz does not exist')
        return redirect(url_for('admin'))
    

    QuizAttempt.query.filter_by(quiz_id=quiz.id).delete()  # Delete quiz attempts
    db.session.delete(quiz)  # Delete the quiz
    db.session.commit()

    flash('Quiz deleted successfully!')
    return redirect(url_for('admin'))


# Add Question

@app.route('/question/add/<int:quiz_id>', methods=['GET', 'POST'])
@auth_required
def add_question(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)

    if request.method == 'POST':
        question_text = request.form['question_text']
        options = [request.form[f'option{i}'] for i in range(1, 5)]
        correct_option = int(request.form['correct_option'])

        new_question = Question(
            quiz_id=quiz_id,
            question_text=question_text,
            option1=options[0],
            option2=options[1],
            option3=options[2],
            option4=options[3],
            correct_option=correct_option
        )

        db.session.add(new_question)
        db.session.commit()
        flash('Question added successfully!')
        return redirect(url_for('show_quiz', quiz_id=quiz_id))

    return render_template('question/add.html', quiz=quiz)


@app.route('/question/edit/<int:question_id>/edit', methods=['GET', 'POST'])
@auth_required
def edit_question(question_id):
    question = Question.query.get_or_404(question_id)

    if request.method == 'POST':
        question.question_text = request.form['question_text']
        question.option1 = request.form['option1']
        question.option2 = request.form['option2']
        question.option3 = request.form['option3']
        question.option4 = request.form['option4']
        question.correct_option = int(request.form['correct_option'])

        db.session.commit()
        flash('Question updated successfully!')
        return redirect(url_for('show_quiz', quiz_id=question.quiz_id))

    return render_template('question/edit.html', question=question)

@app.route('/question/delete/<int:question_id>', methods=['POST'])
@auth_required
def delete_question(question_id):
    question = Question.query.get_or_404(question_id)

    db.session.delete(question)
    db.session.commit()
    
    flash('Question deleted successfully!')
    return redirect(url_for('show_quiz', quiz_id=question.quiz_id))  


@app.route('/')
@auth_required
def index():
    user = User.query.get(session['user_id'])
    if user.is_admin:
        return redirect(url_for('admin'))
    
    parameter = request.args.get('parameter')
    query = request.args.get('query')
    
    parameters = {
        'subject': 'Subject Name',
        'chapter': 'Chapter Name',
        'quiz': 'Quiz Title'
    }

    if not parameter or not query:
        return render_template('index.html', user=user, subjects=Subject.query.all(), parameters=parameters)

    if parameter == 'subject':
        subjects = Subject.query.filter(Subject.name.ilike(f"%{query}%")).all()
        return render_template('index.html', user=user, subjects=subjects, query=query, parameter=parameter, parameters=parameters)

    if parameter == 'chapter':
        subjects = Subject.query.join(Chapter).filter(Chapter.name.ilike(f"%{query}%")).all()
        return render_template('index.html', user=user, subjects=subjects, query=query, parameter=parameter, parameters=parameters)

    if parameter == 'quiz':
        subjects = Subject.query.join(Chapter).join(Quiz).filter(Quiz.title.ilike(f"%{query}%")).all()
        return render_template('index.html', user=user, subjects=subjects, query=query, parameter=parameter, parameters=parameters)

    return render_template('index.html', user=user, subjects=Subject.query.all(), parameters=parameters)

@app.route('/profile/edit', methods=['GET', 'POST'])
@auth_required
def edit_profile():
    """Edit user profile"""
    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        new_name = request.form.get('name')
        new_email = request.form.get('email')
        new_password = request.form.get('password')

        if new_name:
            user.name = new_name
        if new_email:
            user.email = new_email
        if new_password:
            user.password = generate_password_hash(new_password)  

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))

    return render_template('profile/edit.html', user=user)

# @app.route('/user_dashboard')
# def user_dashboard():
#     return render_template('user_dashboard.html')

# start and submit quiz

@app.route('/quiz/start/<int:quiz_id>')
@auth_required
def start_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz_id).all()

    return render_template('quiz/start.html', quiz=quiz, questions=questions)

@app.route('/quiz/view/<int:quiz_id>')
@auth_required
def view_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    num_questions = Question.query.filter_by(quiz_id=quiz.id).count()

    quiz_data = {
        "id": quiz.id,
        "title": quiz.title,
        "quiz_date": quiz.quiz_date.strftime('%d/%m/%Y'),
        "num_questions": num_questions
    }

    return render_template('quiz/quiz_details.html', quiz=quiz_data)


@app.route('/quiz/submit/<int:quiz_id>', methods=['POST'])
@auth_required
def submit_quiz(quiz_id):
    user_id = session.get('user_id')  
    if not user_id:
        flash('Please login to submit a quiz.', 'danger')
        return redirect(url_for('login'))

    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    
    total_questions = len(questions)  
    score = 0

    for question in questions:
        user_answer = request.form.get(f'question_{question.id}')
        if user_answer and int(user_answer) == question.correct_option:
            score += 1

    existing_attempt = QuizAttempt.query.filter_by(user_id=user_id, quiz_id=quiz_id).first()
    if existing_attempt:
        existing_attempt.score = score
        existing_attempt.total_questions = total_questions  
        existing_attempt.date_attempted = db.func.current_timestamp()
    else:
        new_attempt = QuizAttempt(user_id=user_id, quiz_id=quiz_id, score=score, total_questions=total_questions)
        db.session.add(new_attempt)

    db.session.commit()
    
    flash(f'Quiz submitted successfully! You scored {score} out of {total_questions}.', 'success')
    return redirect(url_for('profile'))


from sqlalchemy.sql import func

# @app.route('/quiz/<int:quiz_id>/summary')
# @auth_required
# def quiz_summary(quiz_id):
#     user_id = session.get('user_id')
    
#     quiz = Quiz.query.get_or_404(quiz_id)

#     chapter = Chapter.query.get(quiz.chapter_id)
#     subject = Subject.query.get(chapter.subject_id) if chapter else None

#     summary = db.session.query(
#         func.count(QuizAttempt.id).label("total_attempts"),
#         func.sum(QuizAttempt.score).label("total_score"),
#         func.sum(QuizAttempt.total_questions).label("total_questions"),
#     ).filter(QuizAttempt.quiz_id == quiz_id).first()

#     average_score = (summary.total_score / summary.total_questions * 100) if summary.total_questions else 0

#     return render_template(
#         'quiz/summary.html',
#         quiz=quiz,
#         chapter=chapter,
#         subject=subject,
#         total_attempts=summary.total_attempts,
#         average_score=average_score,
#     )


@app.route('/', methods=['GET'])
@auth_required
def home():
    """Handles user search functionality and dashboard"""
    
    user_id = session.get('user_id')

    if not user_id:
        flash('Please login to continue')
        return redirect(url_for('login'))

    user = User.query.get(user_id)
    if not user:
        session.pop('user_id', None)
        flash('User does not exist. Please login again.')
        return redirect(url_for('login'))

    if user.is_admin:
        return redirect(url_for('admin'))

    parameter = request.args.get('parameter')
    query = request.args.get('query')

    if parameter and query:
        results = []
        if parameter == 'subject':
            results = Subject.query.filter(Subject.name.ilike(f"%{query}%")).all()
        elif parameter == 'chapter':
            results = Chapter.query.filter(Chapter.name.ilike(f"%{query}%")).all()
        elif parameter == 'quiz':
            results = Quiz.query.filter(Quiz.title.ilike(f"%{query}%")).all()
        return render_template('index.html', user=user, results=results, query=query, parameter=parameter)

    
    subjects = Subject.query.all()
    return render_template('index.html', user=user, subjects=subjects)



# @app.route('/admin/user/<int:user_id>/summary', methods=['GET'])
# @admin_required
# def user_summary(user_id):
#     user = User.query.get_or_404(user_id)

    
#     quiz_attempts = QuizAttempt.query.filter_by(user_id=user_id).all()


#     subject_analysis = {}
#     attempted_quizzes = []

#     for attempt in quiz_attempts:
#         quiz = Quiz.query.get(attempt.quiz_id)
#         chapter = Chapter.query.get(quiz.chapter_id)  # Fetch chapter
#         subject = Subject.query.get(chapter.subject_id)  # Fetch subject
#         # if not quiz:
#         #     continue
        
#         # subject_name = quiz.chapter.subject.name

#         attempted_quizzes.append({
#             "quiz_title": quiz.title,
#             "score": attempt.score,
#             "total_questions": attempt.total_questions,
#             "date_attempted": attempt.date_attempted.strftime('%Y-%m-%d')
#         })

#         if subject.name not in subject_analysis:
#             subject_analysis[subject.name] = {'total_quizzes': 0, 'total_score': 0, 'total_questions': 0}

#         subject_analysis[subject.name]['total_quizzes'] += 1
#         subject_analysis[subject.name]['total_score'] += attempt.score
#         subject_analysis[subject.name]['total_questions'] += attempt.total_questions
        
#     for subject in subject_analysis:
        
#         if subject_analysis[subject]['total_questions'] > 0:
#             subject_analysis[subject]['average_score'] = (
#                 subject_analysis[subject]['total_score'] / subject_analysis[subject]['total_questions']
#             )
#         else:
#             subject_analysis[subject]['average_score'] = 0


#     return render_template('admin/user_summary.html', user=user, attempted_quizzes=attempted_quizzes, subject_analysis=subject_analysis)

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
from flask import Flask, render_template
from models import db, Quiz, QuizAttempt, Chapter, Subject
from sqlalchemy.sql import func


from io import BytesIO
import base64

def plot():
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.plot([1, 2, 3], [4, 5, 6])  # Example plot

    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plt.close(fig)  # Close figure to free memory

    return Response(buffer.getvalue(), mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True)


@app.route('/quiz/<int:quiz_id>/summary')
@auth_required
def quiz_summary(quiz_id):
    user_id = session.get('user_id')

    quiz = Quiz.query.get_or_404(quiz_id)
    chapter = Chapter.query.get(quiz.chapter_id)
    subject = Subject.query.get(chapter.subject_id) if chapter else None

    summary = db.session.query(
        func.count(QuizAttempt.id).label("total_attempts"),
        func.sum(QuizAttempt.score).label("total_score"),
        func.sum(QuizAttempt.total_questions).label("total_questions"),
    ).filter(QuizAttempt.quiz_id == quiz_id).first()

    average_score = (summary.total_score / summary.total_questions * 100) if summary.total_questions else 0

    # Generate Charts
    pie_chart = generate_pie_chart(summary.total_score, summary.total_questions)
    bar_chart = generate_bar_chart(quiz_id)

    return render_template(
        'quiz/summary.html',
        quiz=quiz,
        chapter=chapter,
        subject=subject,
        total_attempts=summary.total_attempts,
        average_score=average_score,
        pie_chart=pie_chart,
        bar_chart=bar_chart
    )

# Function to generate a Pie Chart
def generate_pie_chart(score, total_questions):
    labels = ['Correct', 'Incorrect']
    values = [score, total_questions - score]

    plt.figure(figsize=(5, 5))
    plt.pie(values, labels=labels, autopct='%1.1f%%', colors=['#4CAF50', '#FF5252'], startangle=90)
    plt.title("Quiz Performance Breakdown")

    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    return base64.b64encode(img.getvalue()).decode()

# Function to generate a Column Chart
def generate_bar_chart(quiz_id):
    attempts = QuizAttempt.query.filter_by(quiz_id=quiz_id).all()
    users = [f"User {attempt.user_id}" for attempt in attempts]
    scores = [attempt.score for attempt in attempts]

    plt.figure(figsize=(8, 5))
    plt.bar(users, scores, color='skyblue')
    plt.xlabel("Users")
    plt.ylabel("Scores")
    plt.title("User Scores for Quiz")
    plt.xticks(rotation=45)

    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    return base64.b64encode(img.getvalue()).decode()


@app.route('/admin/user/<int:user_id>/summary', methods=['GET'])
@admin_required
def user_summary(user_id):
    user = User.query.get_or_404(user_id)
    quiz_attempts = QuizAttempt.query.filter_by(user_id=user_id).all()

    subject_analysis = {}
    attempted_quizzes = []

    for attempt in quiz_attempts:
        quiz = Quiz.query.get(attempt.quiz_id)
        chapter = Chapter.query.get(quiz.chapter_id) 
        subject = Subject.query.get(chapter.subject_id) 
        
        attempted_quizzes.append({
            "quiz_title": quiz.title,
            "score": attempt.score,
            "total_questions": attempt.total_questions,
            "date_attempted": attempt.date_attempted.strftime('%Y-%m-%d')
        })

        if subject.name not in subject_analysis:
            subject_analysis[subject.name] = {'total_quizzes': 0, 'total_score': 0, 'total_questions': 0}

        subject_analysis[subject.name]['total_quizzes'] += 1
        subject_analysis[subject.name]['total_score'] += attempt.score
        subject_analysis[subject.name]['total_questions'] += attempt.total_questions

    for subject in subject_analysis:
        if subject_analysis[subject]['total_questions'] > 0:
            subject_analysis[subject]['average_score'] = (
                subject_analysis[subject]['total_score'] / subject_analysis[subject]['total_questions']
            )
        else:
            subject_analysis[subject]['average_score'] = 0

    # 🎯 Generate Pie Chart for Subject Distribution  
    subjects = list(subject_analysis.keys())
    quiz_counts = [subject_analysis[sub]['total_quizzes'] for sub in subjects]

    plt.figure(figsize=(6, 6))
    plt.pie(quiz_counts, labels=subjects, autopct='%1.1f%%', colors=['#ff9999','#66b3ff','#99ff99','#ffcc99'])
    plt.title("Quiz Attempts per Subject")

    pie_img = io.BytesIO()
    plt.savefig(pie_img, format='png')
    pie_img.seek(0)
    pie_data = base64.b64encode(pie_img.getvalue()).decode()

    # 🎯 Generate Column Chart for Average Scores  
    avg_scores = [(subject_analysis[sub]['average_score'] * 100) for sub in subjects]

    plt.figure(figsize=(8, 5))
    plt.bar(subjects, avg_scores, color=['#5a9', '#9c5', '#e55', '#77f'])
    plt.xlabel("Subjects")
    plt.ylabel("Average Score (%)")
    plt.title("Average Score per Subject")
    plt.ylim(0, 100)

    bar_img = io.BytesIO()
    plt.savefig(bar_img, format='png')
    bar_img.seek(0)
    bar_data = base64.b64encode(bar_img.getvalue()).decode()

    return render_template(
        'admin/user_summary.html',
        user=user,
        attempted_quizzes=attempted_quizzes,
        subject_analysis=subject_analysis,
        pie_chart=pie_data,
        bar_chart=bar_data
    )



@app.route('/admin/users')
@admin_required
def admin_users():
    query = request.args.get('query', '').strip().lower()
    users = User.query.all()
    
    if query:
        users = [user for user in users if 
                 (user.id and str(user.id) in query) or
                 (user.name and query in user.name.lower()) or
                 (user.username and query in user.username.lower()) or 
                 (user.qualification and query in user.qualification.lower())]   # Filter based on search query
    return render_template('admin/users.html', users=users, query=query)



