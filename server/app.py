#!/usr/bin/env python3

from flask import request, session
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import app, db, api
from models import User, Recipe

class Signup(Resource):
    def post(self):
        data = request.get_json() or {}
        username = data.get("username")
        password = data.get("password")
        bio = data.get("bio")
        image_url = data.get("image_url")
        
        if not username or not password:
            return {"error": "Username and password are required."}, 422
        
        try:
            user = User(username=username, bio=bio, image_url=image_url)
            user.password_hash = password  # Setter will hash the password.
            db.session.add(user)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return {"error": "Username already taken."}, 422
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 422

        session["user_id"] = user.id
        return user.to_dict(), 201

class CheckSession(Resource):
    def get(self):
        user_id = session.get("user_id")
        if user_id:
            user = db.session.get(User, user_id)
            if user:
                return user.to_dict(), 200
        return {"error": "Unauthorized."}, 401

class Login(Resource):
    def post(self):
        data = request.get_json() or {}
        username = data.get("username")
        password = data.get("password")
        
        if not username or not password:
            return {"error": "Username and password are required."}, 422
        
        user = User.query.filter_by(username=username).first()
        if user and user.authenticate(password):
            session["user_id"] = user.id
            return user.to_dict(), 200
        else:
            return {"error": "Invalid username or password."}, 401

class Logout(Resource):
    def delete(self):
        user_id = session.get("user_id")
        if user_id:
            session.pop("user_id")
            return {}, 204
        else:
            return {"error": "Unauthorized."}, 401

class RecipeIndex(Resource):
    def get(self):
        if session.get("user_id"):
            recipes = Recipe.query.all()
            return [recipe.to_dict() for recipe in recipes], 200
        return {"error": "Unauthorized."}, 401

    def post(self):
        if not session.get("user_id"):
            return {"error": "Unauthorized."}, 401
        
        data = request.get_json() or {}
        title = data.get("title")
        instructions = data.get("instructions")
        minutes_to_complete = data.get("minutes_to_complete")
        
        if not title or not instructions:
            return {"error": "Title and instructions are required."}, 422
        
        # Validate that instructions are at least 50 characters long.
        if len(instructions) < 50:
            return {"error": "Instructions must be at least 50 characters long."}, 422
        
        recipe = Recipe(
            title=title,
            instructions=instructions,
            minutes_to_complete=minutes_to_complete,
            user_id=session["user_id"]
        )
        try:
            db.session.add(recipe)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 422
        
        return recipe.to_dict(), 201

# Add resources to the API.
api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')

if __name__ == '__main__':
    app.run(port=5555, debug=True)
