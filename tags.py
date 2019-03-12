import flask, sqlite3, datetime, hashlib
from flask import request, jsonify, Response
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
    conn = sqlite3.connect('api.db')
    cur = conn.cursor()
    username = cur.execute('SELECT name FROM users WHERE email=?', [email]).fetchone()
    conn.close()
    return username[0]

@app.route('/tags/new', methods=['POST'])
@auth.required
def add_new():
    category = request.json['category']
    articleid = request.args.get('id')
    add_tag = [category, articleid]
    user = get_name(request.authorization['username'])

    conn = sqlite3.connect('api.db')
    cur = conn.cursor()
    author = cur.execute('SELECT author FROM articles WHERE id=?', [articleid]).fetchone()

    # check if articleid exists
    if author is None:
        cur.execute('''INSERT INTO tags (category, articleid)
                        VALUES (?, ?)''', add_tag)
        conn.commit()
        conn.close()
        return Response(
            'Tag added.\n',
            201,
            mimetype='application/json',
            headers={
                'Location':'/tags?id=%s' % articleid
            }
        )
    if user == author[0]:
        conn.close()
        return 'Article exists.\n', 409
    else:
        conn.close()
        return 'Article exists. You do not have permission to add a tag to this article.\n', 403


@app.route('/tags/exists', methods=['POST'])
@auth.required
def add_existing():
    category = request.json['category']
    articleid = request.args.get('id')
    add_tag = [category, articleid]
    user = get_name(request.authorization['username'])

    conn = sqlite3.connect('api.db')
    cur = conn.cursor()
    author = cur.execute('SELECT author FROM articles WHERE id=?', [articleid]).fetchone()

    # check if articleid exists
    if author is None:
        conn.close()
        return 'Article does not exist.\n', 404

    if user == author[0]:
        cur.execute('''INSERT INTO tags (category, articleid)
                        VALUES (?, ?)''', add_tag)
        conn.commit()
        conn.close()

        return Response(
            'Tag added.\n',
            201,
            mimetype='application/json',
            headers={
                'Location':'/tags?id=%s' % articleid
            }
        )
    else:
        conn.close()
        return 'You do not have permission to add a tag to this article.\n', 403


@app.route('/tags/delete', methods=['DELETE'])
@auth.required
def delete():
    user = get_name(request.authorization['username'])
    category = request.json['category']
    articleid = request.args.get('id')
    delete_tag = [category, articleid]

    conn = sqlite3.connect('api.db')
    cur = conn.cursor()
    author = cur.execute('SELECT author FROM articles WHERE id=?', [articleid]).fetchone()

    if user == author[0]:
        cur.execute('''DELETE FROM tags WHERE category=? AND articleid=?''', delete_tag)
        conn.commit()
        conn.close()

        return 'Tag deleted.\n', 200
    else:
        conn.close()
        return 'You do not have permission to delete a tag from this article.\n', 403


@app.route('/tags', methods=['GET'])
def retrieve_tags():
    articleid = request.args.get('id')
    conn = sqlite3.connect('api.db')
    cur = conn.cursor()
    tags = cur.execute('SELECT category FROM tags WHERE articleid=?', [articleid]).fetchall()
    conn.close()

    if tags:
        return jsonify(tags), 200
    else:
        return 'The resource could not be found.\n', 404


@app.route('/tags/articles', methods=['GET'])
def retrieve_articles():
    category = request.json['category']
    conn = sqlite3.connect('api.db')
    cur = conn.cursor()
    articles = cur.execute('SELECT articleid FROM tags WHERE category=?', [category]).fetchall()
    conn.close()

    if articles:
        return jsonify(articles), 200
    else:
        return 'The resource could not be found.\n', 404


app.run()
