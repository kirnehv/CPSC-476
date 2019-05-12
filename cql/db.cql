CREATE KEYSPACE IF NOT EXISTS blog WITH REPLICATION = {'class': 'SimpleStrategy', 'replication_factor': 3};
USE blog;
CREATE TABLE IF NOT EXISTS articles (id uuid, title text, content text, author text, date_created timestamp, date_modified timestamp, PRIMARY KEY(id, date_created));
CREATE TABLE IF NOT EXISTS users (email text, username text, password text, PRIMARY KEY(email));
CREATE TABLE IF NOT EXISTS tags (articleid uuid, category list<text>, PRIMARY KEY(articleid));
CREATE TABLE IF NOT EXISTS comments (articleid uuid, id uuid, author text, content text, date timestamp, PRIMARY KEY(articleid, id));