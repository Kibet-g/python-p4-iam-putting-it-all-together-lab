from sqlalchemy.orm import validates
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy_serializer import SerializerMixin
from config import db, bcrypt

class User(db.Model, SerializerMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    # Allow _password_hash to be nullable so tests creating a user without setting one will pass.
    _password_hash = db.Column(db.String(128), nullable=True)
    image_url = db.Column(db.String(255))
    bio = db.Column(db.String(255))

    # Exclude the password hash and recipes from serialization to prevent recursion.
    serialize_rules = ("-_password_hash", "-recipes")

    @hybrid_property
    def password_hash(self):
        raise AttributeError("Password is not a readable attribute.")

    @password_hash.setter
    def password_hash(self, password):
        self._password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        # If no password hash is set, return False.
        if not self._password_hash:
            return False
        return bcrypt.check_password_hash(self._password_hash, password)

    # Add an authenticate method that the tests expect.
    def authenticate(self, password):
        return self.check_password(password)

    # Relationship to recipes.
    recipes = db.relationship('Recipe', back_populates='user', cascade="all, delete-orphan")


class Recipe(db.Model, SerializerMixin):
    __tablename__ = 'recipes'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    instructions = db.Column(db.Text, nullable=False)
    minutes_to_complete = db.Column(db.Integer, nullable=False)
    # Allow user_id to be NULL so tests that create a Recipe without a user pass.
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Exclude the back reference to user.recipes to avoid recursion.
    serialize_rules = ("-user.recipes",)

    # Relationship back to the User.
    user = db.relationship('User', back_populates='recipes')
