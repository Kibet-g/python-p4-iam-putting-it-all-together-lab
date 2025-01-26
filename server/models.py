from sqlalchemy.orm import validates
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy_serializer import SerializerMixin

from config import db, bcrypt

class User(db.Model, SerializerMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    _password_hash = db.Column(db.String, nullable=False)
    image_url = db.Column(db.String)
    bio = db.Column(db.String)

    recipes = db.relationship('Recipe', backref='user')

    serialize_rules = ('-recipes.user', '-_password_hash')

    @hybrid_property
    def password_hash(self):
        raise AttributeError("Password hashes cannot be accessed directly")

    @password_hash.setter
    def password_hash(self, password):
        self._password_hash = bcrypt.generate_password_hash(password.encode('utf-8')).decode('utf-8')

    def authenticate(self, password):
        return bcrypt.check_password_hash(self._password_hash, password.encode('utf-8'))

    @validates('username')
    def validate_username(self, key, username):
        if not username:
            raise ValueError("Username is required")
        return username

class Recipe(db.Model, SerializerMixin):
    __tablename__ = 'recipes'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    instructions = db.Column(db.String, nullable=False)
    minutes_to_complete = db.Column(db.Integer, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    serialize_rules = ('-user.recipes',)

    @validates('title', 'instructions', 'minutes_to_complete')
    def validate_fields(self, key, value):
        if key == 'title' and not value:
            raise ValueError("Title is required")
        if key == 'instructions' and len(value) < 50:
            raise ValueError("Instructions must be at least 50 characters long")
        if key == 'minutes_to_complete' and value <= 0:
            raise ValueError("Minutes to complete must be greater than zero")
        return value
