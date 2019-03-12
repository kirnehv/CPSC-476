import flask, sqlite3, datetime, hashlib
from flask import request, jsonify
from flask_basicauth import BasicAuth

app = flask.Flask(__name__)
app.config['DEBUG'] = True


class Auth(BasicAuth):
    def check_credentials(self, email, password):
        conn = sqlite3.connect('api.db')
        cur = conn.cursor()
        user_password = cur.execute('SELECT password FROM users WHERE email=?', [email]).fetchone()
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
        conn = sqlite3.connect('api.db')
        cur = conn.cursor()
        username = cur.execute('SELECT name FROM users WHERE email=?', [email]).fetchone()
        conn.close()
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
                conn.close()
                return 'You do not have permission to delete this comment.\n', 403
        else:
            conn.close()
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
    conn.close()

    return 'Comment added.\n', 201


@app.route('/comments/delete', methods=['DELETE'])
@auth.required
def delete():
    user = get_name(request.authorization['username'])
    commentid = request.args.get('id')
    conn = sqlite3.connect('api.db')
    cur = conn.cursor()
    author = cur.execute('SELECT author FROM comments WHERE id=?', [commentid]).fetchone()
    
    if author is None:
        conn.close()
        return "Article does not exist.\n", 409
    
    if author[0] == "Anonymous":
        articleid = cur.execute('SELECT articleid FROM comments WHERE id=?', [commentid]).fetchone()
        articleOwner = cur.execute('SELECT author FROM articles WHERE id=?', [articleid[0]]).fetchone()
        if articleOwner[0] == user:
            cur.execute('DELETE FROM comments WHERE id=?', [commentid])
            conn.commit()
            conn.close()
            return 'Comment deleted.\n', 200

    if user == author[0]:
        cur.execute('DELETE FROM comments WHERE id=?', [commentid])
        conn.commit()
        conn.close()
        return 'Comment deleted.\n', 200
    else:
        conn.close()
        return 'You do not have permission to delete this comment.\n', 403


@app.route('/comments/count', methods=['GET'])
def retrieve_count():
    articleid = request.args.get('id')
    conn = sqlite3.connect('api.db')
    cur = conn.cursor()
    articles = cur.execute('SELECT COUNT(articleid) FROM comments WHERE articleid=?', [articleid]).fetchall()
    conn.close()

    if articles:
        return jsonify(articles[0]), 200
    else:
        return 'The resource could not be found.', 404


@app.route('/comments', methods=['GET'])
def retrieve_comments():
    articleid = request.args.get('id')
    num = request.json['amount']
    conn = sqlite3.connect('api.db')
    cur = conn.cursor()
    comments = cur.execute('SELECT content FROM comments WHERE articleid=? LIMIT ?', [articleid, num]).fetchall()
    conn.close()
    return jsonify(comments), 200


app.run()
