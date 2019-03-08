 # NOT WORKING:
    # edit an individual article

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


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def get_name(email):
    conn = sqlite3.connect('api.db')
    cur = conn.cursor()
    username = cur.execute('SELECT name FROM users WHERE email=?', [email]).fetchone()
    return username[0]


@app.route('/articles/new', methods=['POST'])
@auth.required
def post():
    day = datetime.datetime.now()
    title = request.json['title']
    content = request.json['content']
    username = get_name(request.authorization['username'])
    print(request.authorization['username'])
    article_post = [day.strftime("%x %X"), day.strftime("%x %X"), content, title, username]

    conn = sqlite3.connect('api.db')
    cur = conn.cursor()
    cur.execute('''INSERT INTO articles (date_created, date_modified, content, title, author)
                    VALUES (?, ?, ?, ?, ?)''', article_post)
    conn.commit()

    return 'Article posted.\n'


@app.route('/articles', methods=['GET', 'PUT', 'DELETE'])
def options():
    if request.method == 'GET':
        return view()
    elif request.method == 'PUT':
        return edit()
    elif request.method == 'DELETE':
        return delete()


def view():
    articleid = request.args.get('id')
    conn = sqlite3.connect('api.db')
    conn.row_factory = dict_factory
    cur = conn.cursor()
    article_post = cur.execute('SELECT * FROM articles WHERE id=?', [articleid]).fetchone()

    if article_post:
        return jsonify(article_post)
    else:
        return page_not_found(404)


@auth.required
def edit():
    articleid = request.args.get('id')
    email = request.authorization['username']
    user = get_name(email)

    conn = sqlite3.connect('api.db')
    cur = conn.cursor()
    author = cur.execute('SELECT author FROM articles WHERE id=?', [articleid]).fetchone()

    if user == author[0]:
        day = datetime.datetime.now()
        title = request.json.get('title')
        content = request.json.get('content')

        query = 'UPDATE articles SET '
        update = []

        if title:
            query += 'title=? '
            update.append(title)
        if content:
            query += 'content=?, '
            update.append(content)
        if not (title or content):
            return 'No changes made\n'

        query += 'date_modified=? WHERE id=?'
        update.append(day.strftime("%x %X"))
        update.append(id)

        print(query)

        cur.execute(query, update)
        conn.commit()

        return 'Article updated.\n'
    else:
        return 'You do not have permission to edit this post.\n'


@auth.required
def delete():
    articleid = request.args.get('id')
    conn = sqlite3.connect('api.db')
    cur = conn.cursor()
    author = cur.execute('SELECT author FROM articles WHERE id=?', [articleid]).fetchone()
    user = get_name(request.authorization['username'])

    if user == author[0]:
        cur.execute('DELETE FROM articles WHERE id=?', [articleid])
        conn.commit()
        return 'Article deleted\n'
    else:
        return page_not_found(404)


@app.route('/articles/all', methods=['GET'])
def view_all():
    conn = sqlite3.connect('api.db')
    conn.row_factory = dict_factory
    cur = conn.cursor()
    articles = cur.execute('SELECT * FROM articles').fetchall()
    return jsonify(articles)


@app.route('/articles/recent', methods=['GET'])
def view_recent():
    num = request.args.get('amount')
    conn = sqlite3.connect('api.db')
    conn.row_factory = dict_factory
    cur = conn.cursor()
    articles = cur.execute('SELECT * FROM articles ORDER BY date_created DESC LIMIT ?', [num]).fetchall()
    return jsonify(articles)


@app.route('/articles/recent/meta', methods=['GET'])
def view_meta():
    num = request.args.get('amount')
    conn = sqlite3.connect('api.db')
    conn.row_factory = dict_factory
    cur = conn.cursor()
    articles = cur.execute('SELECT date_created, title, author, id FROM articles ORDER BY date_created DESC LIMIT ?', [num]).fetchall()
    return jsonify(articles)


@app.errorhandler(404)
def page_not_found(e):
    return '<h1>404<h1><p>The resource could not be found.</p>', 404


app.run()
