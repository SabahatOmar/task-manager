from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager


#app = Flask(__name__, template_folder='app/templates')

db = SQLAlchemy()
bcrypt = Bcrypt()

def create_app():
    app = Flask(__name__)

    # Configuration
    app.config['SECRET_KEY'] = 'your_secret_key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///task_manager.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key'  # Secret key for JWT encoding and decoding

    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    migrate = Migrate(app, db)
    jwt = JWTManager(app)  # Initialize JWT manager


    # Register Blueprints
    from .api_routes import api_bp
    # from .routes import frontend_bp

    app.register_blueprint(api_bp, url_prefix='/api')
    #app.register_blueprint(frontend_bp, url_prefix='/')

    return app
def create_frontend():
    app1 = Flask(__name__)

    # Configuration

    # Initialize extensions
    bcrypt.init_app(app1)

    # Register Blueprints
    from .routes import frontend_bp

    app1.register_blueprint(frontend_bp, url_prefix='/')

    return app1
