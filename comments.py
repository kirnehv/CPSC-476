import flask, hashlib, os, uuid
from flask.cli import AppGroup
from flask import request, jsonify, current_app, g, make_response
from db import get_db


app = flask.Flask(__name__)
app.config['DEBUG'] = True


@app.errorhandler(404)
def not_found(error=None):
    message = {'message': 'Not Found: ' + request.url}
    return jsonify(message), 404


# post a new comment on an article
@app.route('/articles/<uuid:articleid>/comments/new', methods=['POST'])
def post(articleid):
    email = request.authorization['username']

    if email:
        author = email
    else:
        author = "Anonymous Coward"

    content = request.json['content']
    id = uuid.uuid4()
    add_comment = [author, content, articleid, id]

    db = get_db()
    db.execute('''INSERT INTO comments (author, content, date, articleid, id)
                    VALUES (%s, %s, toUnixTimestamp(now()), %s, %s)''', add_comment)

    message = jsonify({'message': 'Comment added.'})
    message.headers['Location'] = '/articles/{0}/comments/{1}'.format(str(articleid), str(id))
    return message, 201


# delete an individual comment
@app.route('/articles/<uuid:articleid>/comments/<uuid:commentid>', methods=['DELETE'])
def delete(articleid, commentid):
    email = request.authorization['username']
    db = get_db()
    row = db.execute('SELECT author FROM comments WHERE id=%s', [commentid])

    if row[0].author == None:
        return not_found()

    # Anonymous comments cannot be deleted
    # only users can delete their own comments
    if email == row[0].author:
        db.execute('DELETE FROM comments WHERE id=%s', [commentid])
        message = {'message': 'Comment deleted.'}
        return jsonify(message), 200

    else:
        message = {'message': 'You do not have permission to delete this comment'}
        return jsonify(message), 403


# retrieve the number of comments on a given article
@app.route('/articles/<uuid:articleid>/comments/count', methods=['GET'])
def retrieve_count(articleid):
    db = get_db()
    row = db.execute('SELECT COUNT(articleid) FROM comments WHERE articleid=%s', [articleid])
    count = {'count':row[0].system_count_articleid}

    #get only one value: the most recent comment's date
    oneComment=db.execute('SELECT * FROM comments WHERE articleid=? ORDER BY date DESC LIMIT ?', [articleid, num]).fetchone()

    #set the header
    #first convert the header into the datetime fomrat
    lastMod=datetime.datetime.strptime(oneComment['date'], "%m/%d/%y %H:%M:%S")
    #create the make_repsonse which will return the value jsonify(count)
    resp=make_response(jsonify(count))
    #set the resonse header for last_modifed with the date taken from the comments
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



# retrieve the n most recent comments on a URL
@app.route('/articles/<uuid:articleid>/comments', methods=['GET'])
def retrieve_comments(articleid):
    num = request.args.get('amount')
    db = get_db()
    comments = db.execute('SELECT * FROM comments WHERE articleid=%s LIMIT %s', [articleid, int(num)])
    post = []
    for comment in comments:
        post.append({
            "articleid": comment.articleid,
            "id": comment.id,
            "author": comment.author,
            "content": comment.content,
            "date": comment.date
        })

    #get only one value: the most recent comment's date
    oneComment=db.execute('SELECT * FROM comments WHERE articleid=? ORDER BY date DESC LIMIT ?', [articleid, num]).fetchone()

    #set the header
    #first convert the header into the datetime fomrat
    lastMod=datetime.datetime.strptime(oneComment['date'], "%m/%d/%y %H:%M:%S")
    #create the make_repsonse which will return the value jsonify(post)
    resp=make_response(jsonify(post))
    #set the resonse header for last_modifed with the date taken from the comments
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
