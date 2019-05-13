import flask, hashlib, os, uuid
from flask.cli import AppGroup
from flask import request, jsonify, current_app, make_response
from db import get_db


app = flask.Flask(__name__)
app.config['DEBUG'] = True


# error handler
@app.errorhandler(404)
def not_found(error=None):
    message = {'message': 'Not Found: ' + request.url}
    return jsonify(message), 404


# post a new article
@app.route('/articles/new', methods=['POST'])
def post():
    title = request.json['title']
    content = request.json['content']
    email = request.authorization['username']
    id = uuid.uuid4()

    article_post = [content, title, email, id]

    db = get_db()
    db.execute('''INSERT INTO articles (date_created, content, title, author, id)
                    VALUES (toUnixTimestamp(now()), %s, %s, %s, %s)''', article_post)

    message = jsonify({'message': 'Article posted.'})
    message.headers['Location']: '/articles/%s' % str(id)
    return message, 201


@app.route('/articles/<uuid:articleid>', methods=['GET', 'PUT', 'DELETE'])
def options(articleid):
    if request.method == 'GET':
        return view(articleid)
    elif request.method == 'PUT':
        return edit(articleid)
    elif request.method == 'DELETE':
        return delete(articleid)

# retrieve an individual article
def view(articleid):
    db = get_db()
    article_post = db.execute('SELECT * FROM articles WHERE id=%s', [articleid])
    post = {
        "id": article_post[0].id,
        "title": article_post[0].title,
        "content": article_post[0].content,
        "author": article_post[0].author,
        "date_created": article_post[0].date_created,
        "date_modified": article_post[0].date_modified
    }

#get the value of the most recent date_modified

#if this value is none, set it to the value of date_created
    if article_post['date_modified'] == None:
        #get the value of date created and id
        timeHolder=article_post['date_created']
        idHolder=article_post ['id']
        #put these values in the article.db
        articleHolder=[timeHolder, idHolder]
        db.execute('UPDATE articles SET date_modified=? WHERE id=?',[articleHolder])
        #set the value to last_modified header
        lastMod=datetime.datetime.strptime(article_post['date_modified'], "%m/%d/%y %H:%M:%S")

        #this value hold the value of the data that will be returned
        resp=make_response(jsonify(post))
        #the header=lastMod
        resp.last_modified=lastMod

        #    check for if modifed Since
        if 'If-Modified-Since' in request.headers:
            #if the header exists check if it is older than the last_modfied header
            if request.if_modified_since < lastMod:
                #if it is then return the data
                return resp
                #if not return 304
            else:
                resp.status_code=304
                return resp
                #if there is no if since mdofied header then just return the data as usual
        else:
            return resp



    if article_post:
        return jsonify(post), 200
    else:
        return not_found()


# edit an individual article, last-modified timestamp should be updated
def edit(articleid):
    email = request.authorization['username']

    db = get_db()
    row = db.execute('SELECT author FROM articles WHERE id=%s', [articleid])

    if row == None:
        return not_found()
    elif email == row['author']:
        title = request.json.get('title')
        content = request.json.get('content')

        # title or content can be updated
        if title and content:
            article_update = [content, title, articleid]
            db.execute('UPDATE articles SET date_modified=toUnixTimestamp(now()), content=%s, title=%s WHERE id=%s', article_update)
        elif title and not content:
            article_update = [title, articleid]
            db.execute('UPDATE articles SET date_modified=toUnixTimestamp(now()), title=%s WHERE id=%s', article_update)
        elif content and not title:
            article_update = [content, articleid]
            db.execute('UPDATE articles SET date_modified=toUnixTimestamp(now()), content=%s WHERE id=%s', article_update)
        else:
            message = {'message': 'No title or content provided.'}
            return jsonify(message), 409


        message = {'message': 'Article updated.'}
        return jsonify(message), 200
    else:
        message = {'message': 'You do not have permission to edit this post.'}
        return jsonify(message), 403


# delete a specific existing article
def delete(articleid):
    email = request.authorization['username']
    db = get_db()
    row = db.execute('SELECT author FROM articles WHERE id=%s', [articleid])

    if email == row['author']:
        db.execute('DELETE FROM articles WHERE id=%s', [articleid])
        message = {'message': 'Article deleted.'}
        return jsonify(message), 200
    else:
        return not_found()


# retrieve all articles and their contents
@app.route('/articles/all', methods=['GET'])
def view_all():
    db = get_db()
    articles = db.execute('SELECT * FROM articles')
    post = []
    for article in articles:
        post.append({
            "id": article.id,
            "title": article.title,
            "content": article.content,
            "author": article.author,
            "date_created": article.date_created,
            "date_modified": article.date_modified
        })



    #get the value of the most recent date_modified
    articles1 = db.execute('SELECT * FROM articles ORDER BY date_modified DESC LIMIT ?', [num]).fetchone()

    #if this value is none, set it to the value of date_created
    if articles1['date_modified'] == None:
        #get the value of date created and id
        timeHolder=articles1['date_created']
        idHolder=articles1['id']
        #put these values in the article.db
        articleHolder=[timeHolder, idHolder]
        db.execute('UPDATE articles SET date_modified=? WHERE id=?',[ articleHolder])
    #set the value to last_modified header
    lastMod=datetime.datetime.strptime(articles1['date_modified'], "%m/%d/%y %H:%M:%S")

    #this value hold the value of the data that will be returned
    resp=make_response(jsonify(post))
    #the header=lastMod
    resp.last_modified=lastMod

    #    check for if modifed Since
    if 'If-Modified-Since' in request.headers:
        #if the header exists check if it is older than the last_modfied header
        if request.if_modified_since < lastMod:
            #if it is then return the data
            return resp
            #if not return 304
        else:
            resp.status_code=304
            return resp
        #if there is no if since mdofied header then just return the data as usual
    else:
        return resp



# retrieve entire contents (including text) for the n most recent articles
@app.route('/articles/recent', methods=['GET'])
def view_recent():
    num = request.args.get('amount')
    db = get_db()
    articles = db.execute('SELECT * FROM articles LIMIT %s', [int(num)])
    post = []
    for article in articles:
        post.append({
            "id": article.id,
            "title": article.title,
            "content": article.content,
            "author": article.author,
            "date_created": article.date_created,
            "date_modified": article.date_modified
        })
    #get the value of the most recent date_modified
    articles1 = db.execute('SELECT * FROM articles ORDER BY date_modified DESC LIMIT ?', [num]).fetchone()

    #if this value is none, set it to the value of date_created
    if articles1['date_modified'] == None:
        #get the value of date created and id
        timeHolder=articles1['date_created']
        idHolder=articles1['id']
        #put these values in the article.db
        articleHolder=[timeHolder, idHolder]
        db.execute('UPDATE articles SET date_modified=? WHERE id=?',[ articleHolder])
    #set the value to last_modified header
    lastMod=datetime.datetime.strptime(articles1['date_modified'], "%m/%d/%y %H:%M:%S")

    #this value hold the value of the data that will be returned
    resp=make_response(jsonify(post))
    #the header=lastMod
    resp.last_modified=lastMod

    #    check for if modifed Since
    if 'If-Modified-Since' in request.headers:
        #if the header exists check if it is older than the last_modfied header
        if request.if_modified_since < lastMod:
            #if it is then return the data
            return resp
            #if not return 304
        else:
            resp.status_code=304
            return resp
    #if there is no if since mdofied header then just return the data as usual
    else:
        return resp




# retrieve metadata for the n most recent articles, including title, author, date, and URL
@app.route('/articles/recent/meta', methods=['GET'])
def view_meta():
    num = request.args.get('amount')
    db = get_db()
    articles = db.execute('SELECT date_created, title, author, id FROM articles LIMIT %s', [int(num)])
    post = []
    for article in articles:
        post.append({
            "id": article.id,
            "title": article.title,
            "author": article.author,
            "date_created": article.date_created,
        })

    #get the value of the most recent date_modified
    articles1 = db.execute('SELECT * FROM articles ORDER BY date_modified DESC LIMIT ?', [num]).fetchone()

    #if this value is none, set it to the value of date_created
    if articles1['date_modified'] == None:
        #get the value of date created and id
        timeHolder=articles1['date_created']
        idHolder=articles1['id']
        #put these values in the article.db
        articleHolder=[timeHolder, idHolder]
        db.execute('UPDATE articles SET date_modified=? WHERE id=?',[ articleHolder])
    #set the value to last_modified header
    lastMod=datetime.datetime.strptime(articles1['date_modified'], "%m/%d/%y %H:%M:%S")

    #this value hold the value of the data that will be returned
    resp=make_response(jsonify(post))
    #the header=lastMod
    resp.last_modified=lastMod

    #    check for if modifed Since
    if 'If-Modified-Since' in request.headers:
        #if the header exists check if it is older than the last_modfied header
        if request.if_modified_since < lastMod:
            #if it is then return the data
            return resp
            #if not return 304
        else:
            resp.status_code=304
            return resp
    #if there is no if since mdofied header then just return the data as usual
    else:
        return resp
