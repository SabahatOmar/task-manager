from flask import Blueprint, render_template, redirect, request, session, url_for, flash
import requests
from datetime import datetime

frontend_bp = Blueprint('frontend', __name__, template_folder="../templates")


@frontend_bp.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('frontend.login'))

    # Ensure user_id is cast to int
    user_id = int(session.get('user_id'))
    headers = {'Authorization': f"Bearer {session.get('access_token')}"}

    try:
        # Fetch tasks using the API
        response = requests.get(f'http://127.0.0.1:5000/api/tasks/{user_id}', headers=headers)
        response.raise_for_status()  # Raise an error for bad status codes
    except requests.exceptions.RequestException as e:
        if response.status_code == 401:  # Unauthorized due to expired access token
            refresh_token = session.get('refresh_token')
            # Send the refresh token to the backend to get a new access token
            refresh_response = requests.post('http://127.0.0.1:5000/api/refresh', json={'refresh_token': refresh_token})
            if refresh_response.status_code == 200:
                new_access_token = refresh_response.json()['access_token']
                session['access_token'] = new_access_token  # Update session with the new token
                headers = {'Authorization': f"Bearer {new_access_token}"}
                # Retry the request with the new access token
                response = requests.get(f'http://127.0.0.1:5000/api/tasks/{user_id}', headers=headers)
            else:
                flash("Session expired, please log in again.", "danger")
                return redirect(url_for('frontend.login'))


    tasks = response.json() if response.status_code == 200 else []
    return render_template('home.html', tasks=tasks)


@frontend_bp.route('/login', methods=['GET', 'POST'])
def login():
    print("poop")
    if request.method == 'POST':
        print("pooop again")
        data = {'username': request.form['username'], 'password': request.form['password']}
        response = requests.post('http://127.0.0.1:5000/api/login', json=data)
        print (response)
        if response.status_code == 200:
            response_data = response.json()

            session['user_id'] = response_data['user_id']
            session['access_token'] = response_data['access_token']  # Save the token

            return redirect(url_for('frontend.home'))
        flash('Invalid username or password', 'danger')
    return render_template('login.html')


@frontend_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = {'username': request.form['username'], 'password': request.form['password']}
        try:
            response = requests.post('http://127.0.0.1:5000/api/register', json=data)
            #response.raise_for_status()  # Raise an error for bad status codes

            if response.status_code == 201:
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('frontend.login'))
            elif response.status_code == 400:  # If the username already exists
                flash('Username already exists. Please choose a different one.', 'danger')
            else:
                flash('Registration failed. Try a different username.', 'danger')
        except requests.exceptions.RequestException as e:
            flash(f"Error trying to register: {str(e)}", "danger")

    return render_template('register.html')


@frontend_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('access_token', None)  # <— also remove the JWT!

    flash('Logged out successfully', 'success')
    return redirect(url_for('frontend.login'))


@frontend_bp.route('/tasks', methods=['GET', 'POST'])
def tasks():
    if 'user_id' not in session:
        return redirect(url_for('frontend.login'))

    # Ensure user_id is cast to int
    user_id = int(session.get('user_id'))
    headers = {'Authorization': f"Bearer {session.get('access_token')}"}

    if request.method == 'POST':
        # Add a new task via API
        print("1")
        data = {
            'title': request.form['title'],
            'description': request.form['description'],
            'user_id': user_id,  # Ensure user_id is passed correctly as an integer
            'priority': request.form['priority'],  # Get priority from the form
            'deadline': request.form['deadline']  # Get deadline from the form
        }
        print("2")

        # Convert the deadline to the proper format
        if data['deadline']:
            try:
                data['deadline'] = datetime.strptime(data['deadline'], '%Y-%m-%d').strftime('%Y-%m-%d')
            except ValueError:
                flash("Invalid date format. Please use YYYY-MM-DD.", "danger")
                return redirect(url_for('frontend.tasks'))
            print("3")

        try:
            # Fetch tasks using the API
            response = requests.get(f'http://127.0.0.1:5000/api/tasks/{user_id}', headers=headers)
            response.raise_for_status()  # Raise an error for bad status codes
        except requests.exceptions.RequestException as e:
            if response.status_code == 401:  # Unauthorized due to expired access token
                refresh_token = session.get('refresh_token')
                # Send the refresh token to the backend to get a new access token
                refresh_response = requests.post('http://127.0.0.1:5000/api/refresh',
                                                 json={'refresh_token': refresh_token})
                if refresh_response.status_code == 200:
                    new_access_token = refresh_response.json()['access_token']
                    session['access_token'] = new_access_token  # Update session with the new token
                    headers = {'Authorization': f"Bearer {new_access_token}"}
                    # Retry the request with the new access token
                    response = requests.get(f'http://127.0.0.1:5000/api/tasks/{user_id}', headers=headers)
                else:
                    flash("Session expired, please log in again.", "danger")
                    return redirect(url_for('frontend.login'))
        response = requests.post('http://127.0.0.1:5000/api/tasks', json=data, headers=headers)
        if response.status_code == 201:
            flash('Task added successfully!', 'success')
        else:
            flash('Failed to add task.', 'danger')
        return redirect(url_for('frontend.tasks'))

    # Fetch tasks using the API
    response = requests.get(f'http://127.0.0.1:5000/api/tasks/{user_id}', headers=headers)
    if response.status_code == 200:
        tasks = response.json()
        return render_template('home.html', tasks=tasks)
    else:
        flash("Failed to fetch tasks.", "danger")
        return render_template('home.html', tasks=[])

@frontend_bp.route('/delete_task/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('frontend.login'))

    headers = {'Authorization': f"Bearer {session.get('access_token')}"}

    try:
        # Attempt to delete the task
        response = requests.delete(f'http://127.0.0.1:5000/api/tasks/{task_id}', headers=headers)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        # If token is expired or unauthorized, try to refresh
        if response.status_code == 401:
            refresh_token = session.get('refresh_token')
            if not refresh_token:
                flash("Session expired. Please log in again.", "danger")
                return redirect(url_for('frontend.login'))

            # Refresh the access token
            refresh_response = requests.post('http://127.0.0.1:5000/api/refresh', json={'refresh_token': refresh_token})
            if refresh_response.status_code == 200:
                new_access_token = refresh_response.json()['access_token']
                session['access_token'] = new_access_token  # Update session
                headers['Authorization'] = f"Bearer {new_access_token}"

                # Retry deleting the task
                response = requests.delete(f'http://127.0.0.1:5000/api/tasks/{task_id}', headers=headers)
                if response.status_code == 200:
                    flash('Task deleted successfully!', 'success')
                else:
                    flash('Failed to delete task after refreshing token.', 'danger')
                return redirect(url_for('frontend.tasks'))
            else:
                flash("Session expired. Please log in again.", "danger")
                return redirect(url_for('frontend.login'))
        else:
            flash("An error occurred while deleting the task.", "danger")
            return redirect(url_for('frontend.tasks'))

    # If delete succeeded without error
    flash('Task deleted successfully!', 'success')
    return redirect(url_for('frontend.tasks'))

