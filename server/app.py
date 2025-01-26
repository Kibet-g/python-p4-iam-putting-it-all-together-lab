from flask import Flask, jsonify, request, session, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_restful import Api, Resource
from sqlalchemy.orm import validates

# Initialize app and extensions
app = Flask(__name__)
app.secret_key = 'secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)
api = Api(app)

# Models
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    _password_hash = db.Column(db.String(128), nullable=False)
    bio = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String, nullable=True)

    recipes = db.relationship('Recipe', backref='user', lazy=True)

    @property
    def password_hash(self):
        raise AttributeError("Password hash is not readable.")

    @password_hash.setter
    def password_hash(self, password):
        self._password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def authenticate(self, password):
        return bcrypt.check_password_hash(self._password_hash, password)

    @validates('username')
    def validate_username(self, key, username):
        if not username or len(username) < 3:
            raise ValueError("Username must be at least 3 characters long.")
        return username

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'bio': self.bio,
            'image_url': self.image_url,
            'recipes': [recipe.id for recipe in self.recipes],
        }

class Recipe(db.Model):
    __tablename__ = 'recipes'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    instructions = db.Column(db.Text, nullable=False)
    minutes_to_complete = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    @validates('instructions')
    def validate_instructions(self, key, instructions):
        if len(instructions) < 50:
            raise ValueError("Instructions must be at least 50 characters long.")
        return instructions

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'instructions': self.instructions,
            'minutes_to_complete': self.minutes_to_complete,
            'user_id': self.user_id,
        }

# Resources
class Signup(Resource):
    def post(self):
        data = request.get_json()
        try:
            username = data.get('username')
            password = data.get('password')
            bio = data.get('bio', None)
            image_url = data.get('image_url', None)

            if User.query.filter_by(username=username).first():
                return make_response({'error': 'Username already exists'}, 422)

            user = User(username=username, bio=bio, image_url=image_url)
            user.password_hash = password
            db.session.add(user)
            db.session.commit()

            session['user_id'] = user.id
            return make_response(user.to_dict(), 201)
        except Exception as e:
            db.session.rollback()
            return make_response({'error': str(e)}, 422)

class Login(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        user = User.query.filter_by(username=username).first()
        if user and user.authenticate(password):
            session['user_id'] = user.id
            return make_response(user.to_dict(), 200)
        return make_response({'error': 'Invalid username or password'}, 401)

class Logout(Resource):
    def delete(self):
        if 'user_id' in session:
            session.pop('user_id', None)
            return make_response({}, 204)
        return make_response({'error': 'Unauthorized'}, 401)

class CheckSession(Resource):
    def get(self):
        user_id = session.get('user_id')
        if user_id:
            user = User.query.get(user_id)
            return make_response(user.to_dict(), 200)
        return make_response({'error': 'Unauthorized'}, 401)

class RecipeIndex(Resource):
    def get(self):
        user_id = session.get('user_id')
        if not user_id:
            return make_response({'error': 'Unauthorized'}, 401)

        recipes = Recipe.query.filter_by(user_id=user_id).all()
        return make_response([recipe.to_dict() for recipe in recipes], 200)

    def post(self):
        user_id = session.get('user_id')
        if not user_id:
            return make_response({'error': 'Unauthorized'}, 401)

        data = request.get_json()
        try:
            title = data.get('title')
            instructions = data.get('instructions')
            minutes_to_complete = data.get('minutes_to_complete')

            recipe = Recipe(
                title=title,
                instructions=instructions,
                minutes_to_complete=minutes_to_complete,
                user_id=user_id,
            )
            db.session.add(recipe)
            db.session.commit()
            return make_response(recipe.to_dict(), 201)
        except Exception as e:
            db.session.rollback()
            return make_response({'error': str(e)}, 422)

# Add resources to API
api.add_resource(Signup, '/signup')
api.add_resource(Login, '/login')
api.add_resource(Logout, '/logout')
api.add_resource(CheckSession, '/check_session')
api.add_resource(RecipeIndex, '/recipes')

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
