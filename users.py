import flask, sqlite3, hashlib
from flask import request
from flask_basicauth import BasicAuth

app = flask.Flask(__name__)
app.config['DEBUG'] = True


class Auth(BasicAuth):
    def check_credentials(self, email, password):
        conn = sqlite3.connect('api.db')
        cur = conn.cursor()
        user_password = cur.execute('SELECT password FROM users WHERE email=?', [email]).fetchone()

        if user_password:
            return hash_password(password) == user_password[0]
        else:
            return False


def hash_password(password):
    salt = "cpsc476"
    db_password = password + salt
    h = hashlib.md5(db_password.encode())
    return h.hexdigest()


auth = Auth(app)


@app.route('/registration', methods=['POST'])
def register():
    email = request.json['email']
    username = request.json['username']
    password = request.json['password']
    new_user = [username, email, hash_password(password)]

    conn = sqlite3.connect('api.db')
    cur = conn.cursor()
    exists = cur.execute('SELECT * FROM users WHERE email=?', [email]).fetchone()

    if exists:
        return 'Email is already in use\n'
    else:
        cur.execute('INSERT INTO users (name, email, password) VALUES (?,?,?)', new_user)
        conn.commit()
        return 'Successfully registered!\n'
    # curl -X POST -H 'Content-Type: application/json' - d '{"email":"ari@test.com", "password":"password", "username":"ari"}' http://127.0.0.1:5000/registration


@app.route('/users/settings', methods=['PUT', 'DELETE'])
def options():
    if request.method == 'PUT':
        return change_password()
    elif request.method == 'DELETE':
        return delete()


@auth.required
def change_password():
    new_password = request.json['new-password']
    email = request.authorization['username']
    # print(email, new_password)

    conn = sqlite3.connect('api.db')
    cur = conn.cursor()
    cur.execute('UPDATE users SET password=? WHERE email=?', [new_password, email])
    conn.commit()

    return 'Password successfully updated!\n'
    # curl -X PUT --user ari@test.com:password -H 'Content-Type: application.json' -d '{"new-password":"12345"}'  http://127.0.0.1:5000/users/settings


@auth.required
def delete():
    email = request.authorization['username']
    conn = sqlite3.connect('api.db')
    cur = conn.cursor()
    cur.execute('DELETE FROM users WHERE email=?', [email])
    conn.commit()
    return 'User has been deleted.\n'
    # curl -X DELETE --user ari@test.com:password  http://127.0.0.1:5000/users/settings


app.run()
