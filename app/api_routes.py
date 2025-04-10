from datetime import datetime, timedelta
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, create_refresh_token

from flask import Blueprint, jsonify, request, session
from .models import User, Task, db
from . import bcrypt
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity

api_bp = Blueprint('api', __name__)

# 🔹 User Registration
@api_bp.route('/register', methods=['POST'])
def register_user():
    data = request.json
    if not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Username and password required'}), 409

    existing_user = User.query.filter_by(username=data['username']).first()
    if existing_user:
        return jsonify({'message': 'Username already exists'}), 400

    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    new_user = User(username=data['username'], password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User registered successfully'}), 201

# 🔹 User Login
@api_bp.route('/login', methods=['POST'])
def login_user():
    print("different poop")
    data = request.json
    user = User.query.filter_by(username=data['username']).first()

    if user and bcrypt.check_password_hash(user.password, data['password']):
        # Create JWT token
        access_token = create_access_token(identity=user.id, expires_delta=timedelta(minutes=1))  # Identity can be anything (e.g., user id)
        refresh_token = create_refresh_token(identity=user.id)

        return jsonify({
            'message': 'Login successful',
            'user_id': user.id,
            'access_token': access_token , # Send the token back to the client
            'refresh_token': refresh_token  # Send the refresh token

        })

    return jsonify({'message': 'Invalid credentials'}), 401




# 🔹 Refresh Token
@api_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)  # This ensures that the request is made with a refresh token
def refresh_token():
    current_user = get_jwt_identity()  # Get the user id from the refresh token

    # Create a new access token with the same identity
    new_access_token = create_access_token(identity=current_user)

    return jsonify({
        'access_token': new_access_token  # Send the new access token
    }), 200


# 🔹 Get Tasks for User
@api_bp.route('/tasks/<int:user_id>', methods=['GET'])
@jwt_required()  # This decorator ensures that the user is authenticated

def get_tasks(user_id):
    print("in get tasks")
    current_user = get_jwt_identity()
    if current_user!= user_id:
        return jsonify({'message': 'Unauthorized'}), 401
    tasks = Task.query.filter_by(user_id=user_id).order_by(Task.deadline.asc()).all()
    tasks_list = [
        {
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'deadline': task.deadline.strftime('%Y-%m-%d') if task.deadline else None,
            #'deadline': task.deadline,

            'priority': task.priority
        }
        for task in tasks
    ]
    return jsonify(tasks_list), 200

# 🔹 Create Task
@api_bp.route('/tasks', methods=['POST'])
@jwt_required()  # Protect the route

def create_task():
    print ("ENtered create task")
    current_user = get_jwt_identity()  # Retrieve the user identity from the JWT
    data = request.json
    #if data['user_id'] != current_user:
        #return jsonify({'message': 'Unauthorized'}), 401

    required_fields = ['title', 'description', 'user_id']

    if not all(field in data for field in required_fields):
        return jsonify({'message': 'Missing required task fields'}), 400
    priority = data.get('priority', 'Low')  # Default to 'Low' if not provided
    deadline = data.get('deadline')  # This will be a string like 'YYYY-MM-DD'

    if deadline:
        deadline = datetime.strptime(deadline, '%Y-%m-%d').date()
    print (data)
    print ("wegot data")
    new_task = Task(
        title=data['title'],
        description=data['description'],
        user_id=data['user_id'],
        deadline=deadline,  # Optional for now
        priority=priority   # Optional for now
    )
    db.session.add(new_task)
    db.session.commit()
    return jsonify({'message': 'Task created successfully'}), 201

# 🔹 Delete Task
@api_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
@jwt_required()

def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    current_user = get_jwt_identity()
    if task.user_id != current_user:
        return jsonify({'message': 'Unauthorized'}), 401

    # Optional: Check if user owns this task
    #if session.get('user_id') != task.user_id:
       # return jsonify({'message': 'Unauthorized'}), 403

    db.session.delete(task)
    db.session.commit()
    print("task deleted")
    return jsonify({'message': 'Task deleted successfully'}), 200
