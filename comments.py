import flask, sqlite3, datetime, hashlib, click
from flask_cli import FlaskCLI
from flask import request, jsonify, Response
from flask_basicauth import BasicAuth

app = flask.Flask(__name__)
FlaskCLI(app)
app.config['DEBUG'] = True


class Auth(BasicAuth):
    def check_credentials(self, email, password):
        conn = sqlite3.connect('users.db')
        cur = conn.cursor()
        user_password = cur.execute('SELECT password FROM user WHERE email=?', [email]).fetchone()
        conn.close()

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
        conn = sqlite3.connect('users.db')
        cur = conn.cursor()
        username = cur.execute('SELECT name FROM user WHERE email=?', [email]).fetchone()
        conn.close()
        return username[0]


@app.route('/comments/new', methods=['POST'])
def post():
    if request.authorization:
        email = request.authorization['username']
        password = request.authorization['password']
        conn = sqlite3.connect('users.db')
        cur = conn.cursor()
        db_password = cur.execute('SELECT password FROM user WHERE email=?', [email]).fetchone()

        if db_password:
            if hash_password(password) == db_password[0]:
                author = get_name(email)
            else:
                conn.close()
                return 'User not found.\n', 404
        else:
            conn.close()
            return 'User not found.\n', 404
    else:
        author = "Anonymous"

    content = request.json['content']
    date = datetime.datetime.now()
    articleid = request.args.get('id')
    add_comment = [author, content, date, articleid]

    conn = sqlite3.connect('comments.db')
    cur = conn.cursor()

    cur.execute('''INSERT INTO comment (author, content, date, articleid)
                    VALUES (?, ?, ?, ?)''', add_comment)
    location = cur.execute('''SELECT articleid, id FROM comment
                            WHERE author=? AND content=? AND date=? AND articleid=?''', add_comment)
    conn.commit()
    conn.close()

    return Response(
        'Comment added.\n',
        201,
        mimetype='application/json',
        headers={
            'Location':'/comments?id=%s&amount=?' % location
        }
    )

# Custom CLI
@app.cli.command()
@click.argument('id')
@click.argument('content')
def post(id, content):
    author = "Root"

    content_cli = content
    date = datetime.datetime.now()
    articleid = id
    add_comment = [author, content_cli, date, articleid]

    conn = sqlite3.connect('comments.db')
    cur = conn.cursor()

    cur.execute('''INSERT INTO comment (author, content, date, articleid)
                    VALUES (?, ?, ?, ?)''', add_comment)
    location = cur.execute('''SELECT articleid, id FROM comment
                            WHERE author=? AND content=? AND date=? AND articleid=?''', add_comment)
    conn.commit()
    conn.close()

    return Response(
        'Comment added.\n',
        201,
        mimetype='application/json',
        headers={
            'Location':'/comments?id=%s&amount=?' % location
        }
    )


@app.route('/comments/delete', methods=['DELETE'])
@auth.required
def delete():
    user = get_name(request.authorization['username'])
    commentid = request.args.get('id')
    conn = sqlite3.connect('comments.db')
    cur = conn.cursor()
    author = cur.execute('SELECT author FROM comment WHERE id=?', [commentid]).fetchone()

    if author is None:
        conn.close()
        return "Article does not exist.\n", 409

    if author[0] == "Anonymous":
        articleid = cur.execute('SELECT articleid FROM comment WHERE id=?', [commentid]).fetchone()
        articleOwner = cur.execute('SELECT author FROM articles WHERE id=?', [articleid[0]]).fetchone()
        if articleOwner[0] == user:
            cur.execute('DELETE FROM comment WHERE id=?', [commentid])
            conn.commit()
            conn.close()
            return 'Comment deleted.\n', 200

    if user == author[0]:
        cur.execute('DELETE FROM comment WHERE id=?', [commentid])
        conn.commit()
        conn.close()
        return 'Comment deleted.\n', 200
    else:
        conn.close()
        return 'You do not have permission to delete this comment.\n', 403


# Using Custom CLI
@app.cli.command()
@click.argument('id')
def delete(id):
    commentid = id

    conn = sqlite3.connect('comments.db')
    cur = conn.cursor()
    author = cur.execute('SELECT author FROM comment WHERE id=?', [commentid]).fetchone()
    user = author

    if author is None:
        return "Article does not exist", 409
    if author == "Anonymous":
        articleid = cur.execute('SELECT articleid FROM comment WHERE id=?', [commentid]).fetchone()[0]
        articleOwner = cur.execute('SELECT author FROM article WHERE id=?', [articleid]).fetchone()[0]
        if articleOwner == user:
            cur.execute('DELETE FROM comment WHERE id=?', [commentid])
            conn.commit()
            return 'Comment deleted.\n', 200
    if user == author:
        cur.execute('DELETE FROM comment WHERE id=?', [commentid])
        conn.commit()

        return 'Comment deleted.\n', 200
    else:
        return 'You do not have permission to delete this comment.\n', 403



@app.route('/comments/count', methods=['GET'])
def retrieve_count():
    articleid = request.args.get('id')
    conn = sqlite3.connect('comments.db')
    cur = conn.cursor()
    articles = cur.execute('SELECT COUNT(articleid) FROM comment WHERE articleid=?', [articleid]).fetchall()
    conn.close()

    if articles:
        return jsonify(articles[0]), 200
    else:
        return 'The resource could not be found.', 404


@app.route('/comments', methods=['GET'])
def retrieve_comments():
    articleid = request.args.get('id')
    num = request.json['amount']
    conn = sqlite3.connect('comments.db')
    cur = conn.cursor()
    comments = cur.execute('SELECT content FROM comment WHERE articleid=? ORDER BY date DESC LIMIT ?', [articleid, num]).fetchall()
    conn.close()
    return jsonify(comments), 200


app.run(port=5002)