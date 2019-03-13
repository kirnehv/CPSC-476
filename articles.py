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


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def get_name(email):
    conn = sqlite3.connect('api.db')
    cur = conn.cursor()
    username = cur.execute('SELECT name FROM users WHERE email=?', [email]).fetchone()
    conn.close()

    return username[0]


@app.route('/articles/new', methods=['POST'])
@auth.required
def post():
    day = datetime.datetime.now()
    title = request.json['title']
    content = request.json['content']
    username = get_name(request.authorization['username'])

    article_post = [day.strftime("%x %X"), day.strftime("%x %X"), content, title, username]

    conn = sqlite3.connect('api.db')
    cur = conn.cursor()
    cur.execute('''INSERT INTO articles (date_created, date_modified, content, title, author)
                    VALUES (?, ?, ?, ?, ?)''', article_post)
    conn.commit()
    conn.close()

    return Response(
        'Article posted.\n',
        201,
        mimetype='application/json',
        headers={
            'Location':'/articles/view?id=%s' % id
        }
    )


# Custom CLI
@app.cli.command()
@click.argument('title')
@click.argument('content')
def post(title, content):
    day = datetime.datetime.now()
    username = "Root"

    article_post = [day.strftime("%x %X"), day.strftime("%x %X"), content, title, username]

    conn = sqlite3.connect('api.db')
    cur = conn.cursor()
    cur.execute('''INSERT INTO articles (date_created, date_modified, content, title, author)
                    VALUES (?, ?, ?, ?, ?)''', article_post)
    conn.commit()
    conn.close()

    return 'Article posted.\n', 201


@app.route('/articles/view', methods=['GET', 'PUT', 'DELETE'])
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
    conn.close()

    if article_post:
        return jsonify(article_post), 200
    else:
        return 'The resource could not be found.\n', 404


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

        # title or content can be updated
        if title and content:
            article_update = [day.strftime("%x %X"), content, title, articleid]
            cur.execute('UPDATE articles SET date_modified=?, content=?, title=? WHERE id=?', article_update)
        elif title and not content:
            article_update = [day.strftime("%x %X"), title, articleid]
            cur.execute('UPDATE articles SET date_modified=?, title=? WHERE id=?', article_update)
        elif content and not title:
            article_update = [day.strftime("%x %X"), content, articleid]
            cur.execute('UPDATE articles SET date_modified=?, content=?, WHERE id=?', article_update)
        else:
            return 'No title or content provided.\n', 409

        conn.commit()
        conn.close()

        return 'Article updated.\n', 200
    else:
        return 'You do not have permission to edit this post.\n', 403


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
        conn.close()
        return 'Article deleted.\n', 200
    else:
        conn.close()
        return 'The resource could not be found.\n', 404


# Custom CLI
@app.cli.command()
@click.argument('id')
def delete(id):
    articleid = id
    conn = sqlite3.connect('api.db')
    cur = conn.cursor()
    author = cur.execute('SELECT author FROM articles WHERE id=?', [articleid]).fetchone()

    cur.execute('DELETE FROM articles WHERE id=?', [articleid])
    conn.commit()
    conn.close()
    return 'Article deleted.\n', 200


@app.route('/articles/view/all', methods=['GET'])
def view_all():
    conn = sqlite3.connect('api.db')
    conn.row_factory = dict_factory
    cur = conn.cursor()
    articles = cur.execute('SELECT * FROM articles').fetchall()
    conn.close()

    return jsonify(articles), 200


@app.route('/articles/view/recent', methods=['GET'])
def view_recent():
    num = request.args.get('amount')

    conn = sqlite3.connect('api.db')
    conn.row_factory = dict_factory
    cur = conn.cursor()
    articles = cur.execute('SELECT * FROM articles ORDER BY date_created DESC LIMIT ?', [num]).fetchall()
    conn.close()

    return jsonify(articles), 200


@app.route('/articles/view/recent/meta', methods=['GET'])
def view_meta():
    num = request.args.get('amount')

    conn = sqlite3.connect('api.db')
    conn.row_factory = dict_factory
    cur = conn.cursor()
    articles = cur.execute('SELECT date_created, title, author, id FROM articles ORDER BY date_created DESC LIMIT ?', [num]).fetchall()
    conn.close()

    return jsonify(articles), 200


app.run(port=5001)
