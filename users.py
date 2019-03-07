# NOT WORKING:
    # change password
    # delete

import flask, sqlite3, hashlib
from flask import request
from flask_basicauth import BasicAuth

app = flask.Flask(__name__)
app.config['DEBUG'] = True


class Auth(BasicAuth):
    def check_credentials(self, email, password):
        conn = sqlite3.connect('blog.db')
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

    new_user = [email, username, hash_password(password)]

    conn = sqlite3.connect('blog.db')
    cur = conn.cursor()
    exists = cur.execute('SELECT * FROM users WHERE email=?', [email]).fetchone()

    if exists:
        return 'Email is already in use\n'
    else:
        cur.execute('INSERT INTO users VALUES (?,?,?)', new_user)
        conn.commit()
        return 'Successfully registered!\n'


@app.route('/users', methods=['PUT', 'DELETE'])
@auth.required
def options():
    if request.method == 'PUT':
        new_password = request.json['new-password']
        email = request.autjorization['username']
        change_password(email, new_password)
    elif request.method == 'DELETE':
        delete()


def change_password(email, new_password):
    # new_password = request.json['new-password']
    # email = request.authorization['username']

    print(new_password, email)

    conn = sqlite3.connect('blog.db')
    cur = conn.cursor()
    cur.execute('UPDATE users SET password=? WHERE email=?', [new_password, email])
    conn.commit()

    return 'Password successfully updated!\n'


def delete():
    email = request.authorization['username']
    conn = sqlite3.connect('blog.db')
    cur = conn.cursor()
    cur.execute('DELETE FROM users WHERE email=?' [email])
    return 'User has been deleted.\n'


app.run()
