import requests, flask, datetime
from rfeed import *
from flask import jsonify


app = flask.Flask(__name__)
app.config['DEBUG'] = True


# summary feed listing the title, author, date, and link for the 10 most recent articles
@app.route('/rss/recent', methods=['GET'])
def summary_feed():
    r = requests.get('http://localhost:5000/articles/recent', params={'amount': '10'})
    
    if r.status_code == requests.codes.ok:
        articles = r.json()
        rss_articles = []

        for article in articles:
            rss_articles.append (
                Item (
                    title = article['title'],
                    author = article['author'],
                    pubDate = datetime.datetime.strptime(article['date_created'], "%Y-%m-%d %H:%M"),
                    link = 'http:://localhost/articles/' + str(article['id'])
                )
            )
        
        feed = Feed (
            title = 'RSS Recent Feed',
            link = 'http://localhost/rss/recent',
            description = 'Recent article feed',
            language = 'en-US',
            items = rss_articles
        )
        
        return feed.rss()
    
    else:
        message = {'message':'Request error'}
        return jsonify(message), 404


# full feed containing the full text for each article, its tags as RSS categories, and a comment count
@app.route('/rss/articles/<articleid>', methods=['GET'])
def full_feed(articleid):
    r = requests.get('http://localhost:5000/articles/' + articleid)
    r2 = requests.get('http://localhost:5300/articles/' + articleid + '/comments/count')
    r3 = requests.get('http://localhost:5100/articles/' + articleid + '/tagged')
    
    if r.status_code == requests.codes.ok and r2.status_code == requests.codes.ok and r3.status_code == requests.codes.ok:
        article = r.json()
        comment_count = r2.json()
        tags = r3.json()

        rss_article = Item (
            title = article['title'],
            author = article['author'],
            pubDate = datetime.datetime.strptime(article['date_created'], "%a, %d %b %Y %H:%M:%S %Z"),
            link = 'http:://localhost/articles/' + articleid,
            description = article['content'],
            categories = tags['category'],
            comments = comment_count['count']
        )
    
        feed = Feed (
            title = 'RSS Article Feed',
            link = 'https://localhost/rss/articles/' + articleid,
            description = 'Full article feed',
            language = 'en-US',
            items = [rss_article]
        )

        return feed.rss()
    
    else:
        message = {'message':'Request error'}
        return jsonify(message), 404
            

# comment feed for each article
@app.route('/rss/articles/<articleid>/comments', methods=['GET'])
def comment_feed(articleid):
    r = requests.get('http://localhost:5000/articles/' + articleid)
    r2 = requests.get('http://localhost:5300/articles/' + articleid + '/comments/count')

    if r.status_code == requests.codes.ok and r2.status_code == requests.codes.ok:
        article = r.json()
        num_of_comments = r2.json()['count']
        rss_comments = []

        r3 = requests.get('http://localhost:5300/articles/' + articleid + '/comments', params={'amount':str(num_of_comments)})

        if r3.status_code == requests.codes.ok:
            comments = r3.json()

            for comment in comments:
                rss_comments.append (
                    Item (
                        title = 'RE: ' + article['title'],
                        author = comment['author'],
                        description = comment['content'],
                        pubDate = datetime.datetime.strptime(comment['date'], "%a, %d %b %Y %H:%M:%S %Z"),
                    )
                )
    
        feed = Feed (
            title = 'RSS Comment Feed',
            link = 'http://localhost/rss/articles/' + articleid + '/comments',
            description = 'Article comment feed',
            language = 'en-US',
            items = rss_comments
        )

        return feed.rss()
    
    else:
        message = {'message':'Request error.'}
        return jsonify(message), 404


app.run()