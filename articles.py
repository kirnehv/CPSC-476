 # NOT WORKING:
    # post new article
    # retrieve an individual article
    # edit an individual article
    # delete a specific existing article

import flask, sqlite3, datetime, hashlib
from flask import request, jsonify
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


auth = Auth(app)


def hash_password(password):
    salt = "cpsc476"
    db_password = password + salt
    h = hashlib.md5(db_password.encode())
    return h.hexdigest()


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def get_username(email):
    conn = sqlite3.connect('blog.db')
    cur = conn.cursor()

    username = cur.execute('SELECT username FROM users WHERE email=?', [email]).fetchone()
    return username[0]


@app.route('/articles', methods=['POST'])
@auth.required
def post():
    day = datetime.datetime.date()
    title = request.json['title']
    content = request.json['content']
    tags = request.json['tags']
    username = get_username(request.authorization['username'])

    article_post = [day, day, content, title, tags, username]

    conn = sqlite3.connect('blog.db')
    cur = conn.cursor()

    cur.execute(''''INSERT INTO articles (creation_date, last_modified, content, title, tags, author)'
                    'VALUES (?, ?, ?, ?, ?, ?)''', article_post)

    conn.commit()


@app.route('/articles/<articleid>', methods=['GET', 'PUT', 'DELETE'])
def options(articleid):
    if request.method == 'GET':
        view(articleid)
    elif request.method == 'PUT':
        edit(articleid)
    elif request.method == 'DELETE':
        delete(articleid)


def view(articleid):
    conn = sqlite3.connect('blog.db')
    conn.row_factory = dict_factory
    cur = conn.cursor()
    article_post = cur.execute('SELECT * FROM articles WHERE id=?', [articleid]).fetchone()

    if article_post:
        return jsonify(article_post)
    else:
        return page_not_found(404)


@auth.required
def edit(articleid):
    email = request.authorization['username']
    user = get_username(email)

    conn = sqlite3.connect('blog.db')
    cur = conn.cursor()
    author = cur.execute('SELECT author FROM articles WHERE id=?', [articleid]).fetchone()

    if user == author:
        day = datetime.datetime.date()
        title = request.json['title']
        content = request.json['content']

        query = 'UPDATE articles SET last_modified=?'
        update = [day]

        if title:
            query += ' title=?'
            update.append(title)
        if content:
            query += ' content=?'
            update.append(content)
        if not (title or content):
            return 'No changes made\n'

        query += ' WHERE id=?'
        update.append(id)
        cur.execute(query, update)
        conn.commit()
    else:
        return 'You do not have permission to edit this post\n'


@auth.required
def delete(articleid):
    conn = sqlite3.connect('blog.db')
    cur = conn.cursor()
    author = cur.execute('SELECT author FROM articles WHERE id=?', [articleid]).fetchone()
    user = get_username(request.authorization['username'])

    if user == author:
        cur.execute('DELETE FROM articles WHERE id=?', [articleid])
        conn.commit()
        return 'Article deleted\n'
    else:
        return page_not_found(404)


@app.route('/articles/all', methods=['GET'])
def view_all():
    conn = sqlite3.connect('blog.db')
    conn.row_factory = dict_factory
    cur = conn.cursor()
    articles = cur.execute('SELECT * FROM articles').fetchall()
    return jsonify(articles)


@app.route('/articles/recent/<num>', methods=['GET'])
def view_recent(num):
    conn = sqlite3.connect('blog.db')
    conn.row_factory = dict_factory
    cur = conn.cursor()
    articles = cur.execute('SELECT * FROM articles ORDER BY creation_date DESC LIMIT ?', [num]).fetchall()
    return jsonify(articles)


@app.route('/articles/recent/meta/<num>', methods=['GET'])
def view_meta(num):
    conn = sqlite3.connect('blog.db')
    conn.row_factory = dict_factory
    cur = conn.cursor()
    articles = cur.execute('SELECT creation_date, title, author, id FROM articles ORDER BY creation_date DESC LIMIT ?', [num]).fetchall()
    return jsonify(articles)


@app.errorhandler(404)
def page_not_found(e):
    return '<h1>404<h1><p>The resource could not be found.</p>', 404


app.run()
