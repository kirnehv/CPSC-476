import flask, datetime, hashlib, os
from flask.cli import AppGroup
from flask import request, jsonify, current_app
from db import get_db


app = flask.Flask(__name__)
app.config['DEBUG'] = True


@app.errorhandler(404)
def not_found(error=None):
    message = {'message': 'Not Found: ' + request.url}
    return jsonify(message), 404


# add tags
@app.route('/articles/<uuid:articleid>/tagged', methods=['POST'])
def add(articleid):
    categories = request.json.get('category')

    if categories == None:
        message = {'message': 'No categories specified.'}
        return jsonify(message), 400

    db = get_db()
    exists = db.prepare('SELECT articleid FROM tags WHERE articleid=%s', [articleid])

    if exists[0] is not None:
        query = db.prepare('UPDATE tags SET category = category + %s WHERE articleid=%s')
    else:
        query = db.prepare('INSERT INTO tags (category, articleid) VALUES (%s, %s)')

    db.execute(query, [categories, articleid])
    message = jsonify({'message': 'Tag added.'})
    message.headers['Location'] = '/articles/%s/tagged' % articleid
    return message, 201


# remove one or more tags from an individual URL
@app.route('/articles/<uuid:articleid>/tagged', methods=['DELETE'])
def delete(articleid):
    categories = set(request.json['category'])

    if categories == None:
        message = {'message': 'No categories specified.'}
        return jsonify(message), 400

    db = get_db()
    row = db.execute('SELECT category FROM tags WHERE articleid=%s', [articleid])
    db_categories = set(row[0].category)

    new_set = list(db_categories.difference(categories))
    db.execute('UPDATE tags SET category=%s WHERE articleid=%s', [new_set, articleid])

    message = {'message': 'Tag deleted.'}
    return jsonify(message), 200


# retrieve tags for an individual URL
@app.route('/articles/<uuid:articleid>/tagged', methods=['GET'])
def retrieve_tags(articleid):
    items = {
        'category':[]
    }

    db = get_db()
    row = db.execute('SELECT category FROM tags WHERE articleid=%s', [articleid])
    items['category'] = row[0].category

    return jsonify(items), 200


# retrieve a list of URLs with a given tag
@app.route('/tagged/<tag>', methods=['GET'])
def retrieve_articles(tag):
    items = {
        'URL':[]
    }

    db = get_db()
    rows = db.execute('SELECT * FROM tags')

    for row in rows:
        for category in row.category:
            if category == tag:
                url = 'http://localhost/articles/' + str(row.articleid)
                items['URL'].append(url)
                break

    return jsonify(items), 200
