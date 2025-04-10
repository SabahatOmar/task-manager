from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///task_manager.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['TEMPLATES_AUTO_RELOAD'] = True


db = SQLAlchemy(app)
bcrypt = Bcrypt(app)




@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        if User.query.filter_by(username=username).first():
            flash("Username already exists!", "danger")
            return redirect(url_for('register'))

        user = User(username=username, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash("Registered successfully!", "success")
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    print("Accessing /login route")  # Debug statement

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash("kinnda sucseful", "success")
            return redirect(url_for('home'))
        else:
            flash("Invalid credentials!", "danger")

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("the system automaticaly deleted your account", "success")
    return redirect(url_for('login'))


@app.route('/')
def home():
    print("Home route accessed")

    if 'user_id' not in session:
        return redirect(url_for('login'))

    tasks = Task.query.filter_by(user_id=session['user_id']).all()
    return render_template('home.html', tasks=tasks)


@app.route('/add_task', methods=['GET', 'POST'])
def add_task():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']

        task = Task(title=title, description=description, user_id=session['user_id'])
        db.session.add(task)
        db.session.commit()
        flash("Task added successfully!", "success")
        return redirect(url_for('home'))

    return render_template('tasks.html')


@app.route('/delete_task/<int:id>')
def delete_task(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    task = Task.query.get_or_404(id)
    if task.user_id == session['user_id']:
        db.session.delete(task)
        db.session.commit()
        flash("Task deleted successfully!", "success")
    else:
        flash("Unauthorized action!", "danger")

    return redirect(url_for('home'))

# REST API Routes
@app.route('/api/tasks', methods=['GET', 'POST'])
def api_tasks():
    if request.method == 'GET':
        tasks = Task.query.all()
        return jsonify([{'id': task.id, 'title': task.title, 'description': task.description} for task in tasks])

    if request.method == 'POST':
        data = request.get_json()
        title = data.get('title')
        description = data.get('description')
        if not title:
            return jsonify({'message': 'Title is required'}), 400
        task = Task(title=title, description=description, user_id=1)  # Default user ID for testing
        db.session.add(task)
        db.session.commit()
        return jsonify({'message': 'Task created', 'id': task.id}), 201

@app.route('/api/tasks/<int:id>', methods=['GET', 'DELETE'])
def api_task_detail(id):
    task = Task.query.get_or_404(id)
    if request.method == 'GET':
        return jsonify({'id': task.id, 'title': task.title, 'description': task.description})
    if request.method == 'DELETE':
        db.session.delete(task)
        db.session.commit()
        return jsonify({'message': 'Task deleted'})

if __name__ == '__main__':
    with app.app_context():
    #print(app.url_map)  # This will print all registered routes

        app.run(debug=True)
