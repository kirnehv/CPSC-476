import flask, hashlib, os
from flask.cli import AppGroup
from flask import request, jsonify, current_app, g
from flask_basicauth import BasicAuth
from Crypto.Hash import SHA256
from db import get_db


app = flask.Flask(__name__)
app.config['DEBUG'] = True


# overwrite check_credentials to read from database
class Auth(BasicAuth):
    def check_credentials(self, email, password):
        db = get_db()
        row = db.execute('SELECT name, password FROM users WHERE email=%s', [email])

        if row:
            return hash_password(password) == row['password']
        else:
            return False


auth = Auth(app)


def hash_password(password):
    salt = 'cpsc476'
    db_password = password + salt
    h = SHA256.new(db_password).hexdigest()
    return h


@app.errorhandler(404)
def not_found(error=None):
    message = {'message': 'Not Found: ' + request.url}
    return jsonify(message), 404


# create user
@app.route('/registration', methods=['POST'])
def register():
    name = request.json['name']
    email = request.json['email']
    password = hash_password(request.json['password'])
    new_user = [name, email, password]

    # check if all fields are populated
    if not (name and email and password):
        message = {'message': 'Missing parameter'}
        return jsonify(message), 409

    db = get_db()
    email_exists = db.execute('SELECT email FROM users WHERE email=%s', [email])

    # check if name or email exist before creating new user
    if email_exists:
        message = {'message': 'Email is already in use.'}
        return jsonify(message), 409

    db.execute('INSERT INTO users (name, email, password) VALUES (%s,%s,%s)', new_user)

    message = jsonify({'message': 'User created.'})
    message.headers['Location'] = '/users/%s', name
    return message, 201


# change existing user's password
@app.route('/users/change-password', methods=['PUT'])
def change_password():
    new_password = hash_password(request.json['new-password'])
    email = request.authorization['username']
    db = get_db()
    db.execute('UPDATE users SET password=%s WHERE email=%s', [new_password, email])
    message = {'message': 'Password has been changed.'}
    return jsonify(message), 200


# delete existing user
@app.route('/users/delete-account', methods=['DELETE'])
def delete():
    email = request.authorization['username']
    db = get_db()
    db.execute('DELETE FROM users WHERE email=%s', [email])
    message = {'message': 'User has been deleted.'}
    return jsonify(message), 200


app.run()
