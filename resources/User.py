import uuid
from flask import request, make_response
from flask_restful import Resource
from werkzeug.security import generate_password_hash, check_password_hash

from models.User import db, User
import jwt
import datetime
from functools import wraps
from flask import current_app


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']

        if not token:
            return "Token is missing", 401

        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'])
            current_user = User.query.filter_by(public_id=data['public_id']).first()
        except:
            return "Token is invalid!", 401

        return f(current_user, *args, **kwargs)

    return decorated


class Login(Resource):
    def post(self):
        auth = request.authorization

        if not auth or not auth.username or not auth.password:
            return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login required!"'})

        user = User.query.filter_by(name=auth.username).first()

        if not user:
            return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm="No user found"'})

        if check_password_hash(user.password, auth.password):
            token = jwt.encode(
                {'public_id': user.public_id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)},
                current_app.config['SECRET_KEY'])

            return {"access-token": token.decode("UTF-8"), "name": user.name, "isAdmin": user.admin, "email": user.email}

        return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm="The password is wrong"'})


class CreateUser(Resource):
    def post(self):
        data = request.get_json()

        hashed_password = generate_password_hash(data['password'], method='sha256')
        new_user = User(public_id=str(uuid.uuid4()), name=data['name'], email=data['email'],
                        password=hashed_password, admin=False)

        try:
            db.session.add(new_user)
            db.session.commit()
        except:
            db.session.rollback()
            raise
        finally:
            db.session.close()  # optional, depends on use case

        return {'message': 'New user ' + data['name'] + ' created'}


class GetAllUsers(Resource):
    @token_required
    def get(current_user, public_id):
        if not current_user.admin:
            return "Can not perform that function!", 403

        users = User.query.all()
        output = []

        for user in users:
            user_data = {'public_id': user.public_id, 'name': user.name, 'email': user.email, 'admin': user.admin}
            output.append(user_data)

        return output


class GetUser(Resource):
    @token_required
    def get(current_user, self, public_id):

        # if not current_user.admin:
        # return "Can not perform that function!", 403

        if current_user.public_id == public_id:
            user = User.query.filter_by(public_id=public_id).first()
            return {'public_id': user.public_id, 'name': user.name, 'email': user.email, 'admin': user.admin}, 201
        else:
            return "Can not perform that function!", 403

        # user = User.query.filter_by(public_id=public_id).first()

        # if not user:
        #   return {'Message': 'No user found with the public id: ' + str(public_id)}

        # user_data = {'public_id': user.public_id, 'name': user.name, 'email': user.email, 'admin': user.admin}

    # return user_data


class UpdateUser(Resource):
    @token_required
    def put(self, current_user, public_id):
        if not current_user.admin:
            return "Can not perform that function!", 403

        return 1 + public_id


class DeleteUser(Resource):
    @token_required
    def delete(self, current_user, public_id):

        if not current_user.admin:
            return "Can not perform that function!", 403

        user = User.query.filter_by(public_id=public_id).first()

        if not user:
            return {'Message': 'No user found with the public id: ' + str(public_id)}

        try:
            db.session.delete(user)
            db.session.commit()
        except:
            db.session.rollback()
            raise
        finally:
            db.session.close()

        return {'Message': 'The user with public id: ' + str(public_id) + ' has been deleted'}


class PromoteUser(Resource):
    @token_required
    def put(self, current_user, public_id):

        if not current_user.admin:
            return "Can not perform that function!", 403

        user = User.query.filter_by(public_id=public_id).first()

        if not user:
            return {'Message': 'No user found with the public id: ' + str(public_id)}

        try:
            user.admin = True
            db.session.commit()
        except:
            db.session.rollback()
            raise
        finally:
            db.session.close()

        return {'message': 'The user has been promoted'}
