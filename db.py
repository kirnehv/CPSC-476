import click
from flask import Flask, current_app
from cassandra.cluster import Cluster


app = Flask(__name__)
cluster = Cluster(['172.17.0.2'])


def get_db():
    return cluster.connect('blog')


@app.cli.command('init-db')
def init_db():
    db = cluster.connect()
    with current_app.open_resource('cql/db.cql') as f:
        commands = f.readlines()
        for line in commands:
            db.execute(line.decode('utf-8'))
        click.echo(f'Initialized the database.')


@app.cli.command('init-data')
@click.argument('service')
def init_data(service):
    services = ['users', 'articles', 'tags', 'comments']

    if service in services:
        db = get_db()
        with current_app.open_resource(f'cql/{service}_data.cql') as f:
            commands = f.readlines()
            for line in commands:
                db.execute(line.decode('utf-8'))
            click.echo(f'Loaded dummy data for {service}')
    else:
        click.echo(f'Could not find service {service}')


@app.cli.command('drop-db')
def drop_db():
    db = cluster.connect()
    db.execute('DROP KEYSPACE blog;')
    click.echo(f'Database dropped.')
