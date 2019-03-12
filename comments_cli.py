# open terminal
# python comments.py
# FLASK_APP=comments.py flask delete (comment id to be deleted)

import flask, sqlite3, datetime, hashlib, click
from flask_cli import FlaskCLI
from flask import request, jsonify
from flask_basicauth import BasicAuth

app = flask.Flask(__name__)
FlaskCLI(app)
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

def get_name(email):
    if email == "":
        return "Anonymous"
    else:
        conn = sqlite3.connect('api.db')
        cur = conn.cursor()
        username = cur.execute('SELECT name FROM users WHERE email=?', [email]).fetchone()
        return username[0]


@app.route('/comments/new', methods=['POST'])
def post():
    if request.authorization:
        email = request.authorization['username']
        password = request.authorization['password']
        conn = sqlite3.connect('api.db')
        cur = conn.cursor()
        db_password = cur.execute('SELECT password FROM users WHERE email=?', [email]).fetchone()

        if db_password:
            if hash_password(password) == db_password[0]:
                author = get_name(email)
            else:
                return 'You do not have permission to delete this comment.\n', 403
        else:
            return 'You do not have permission to delete this comment.\n', 403
    else:
        author = "Anonymous"
    content = request.json['content']
    date = datetime.datetime.now()
    articleid = request.args.get('id')
    add_comment = [author, content, date, articleid]

    conn = sqlite3.connect('api.db')
    cur = conn.cursor()

    cur.execute('''INSERT INTO comments (author, content, date, articleid)
                    VALUES (?, ?, ?, ?)''', add_comment)
    conn.commit()

    return 'Comment added.\n', 201


@app.route('/comments/delete', methods=['DELETE'])
@auth.required
@app.cli.command()
@click.argument('id')
def delete(id):
    is_cli = id is not None

    # NOT CLI
    if not is_cli:
        user = get_name(request.authorization['username'])
        commentid = request.args.get('id')

    # CLI
    else:
        commentid = id

    conn = sqlite3.connect('api.db')
    cur = conn.cursor()
    author = cur.execute('SELECT author FROM comments WHERE id=?', [commentid]).fetchone()

    # CLI
    if is_cli:
        user = author

    if author is None:
        return "Article does not exist", 409
    if author == "Anonymous":
        articleid = cur.execute('SELECT articleid FROM comments WHERE id=?', [commentid]).fetchone()[0]
        articleOwner = cur.execute('SELECT author FROM articles WHERE id=?', [articleid]).fetchone()[0]
        if articleOwner == user:
            cur.execute('DELETE FROM comments WHERE id=?', [commentid])
            conn.commit()
            return 'Comment deleted.\n', 200
    if user == author:
        cur.execute('DELETE FROM comments WHERE id=?', [commentid])
        conn.commit()

        return 'Comment deleted.\n', 200
    else:
        return 'You do not have permission to delete this comment.\n', 403


@app.route('/comments/count', methods=['GET'])
def retrieve_count():
    articleid = request.args.get('id')
    conn = sqlite3.connect('api.db')
    cur = conn.cursor()
    articles = cur.execute('SELECT COUNT(articleid) FROM comments WHERE articleid=?', [articleid]).fetchall()

    if articles:
        return jsonify(articles[0]), 200
    else:
        return 'The resource could not be found.\n', 404


@app.route('/comments', methods=['GET'])
def retrieve_comments():
    articleid = request.args.get('id')
    num = request.json['amount']
    conn = sqlite3.connect('api.db')
    cur = conn.cursor()
    comments = cur.execute('SELECT content FROM comments WHERE articleid=? LIMIT ?', [articleid, num]).fetchall()
    return jsonify(comments), 200


app.run()
