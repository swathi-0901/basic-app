from flask import render_template
from app import app

@app.route('/')
@app.route('/index')
def index():
    user = {'username': 'Swathi'}
    posts = [
        {
            'author': {'username': 'user1'},
            'body': 'Beautiful day!'
        },
        {
            'author': {'username': 'user2'},
            'body': 'The Avengers movie was so cool!'
        }
    ]
    return render_template('index.html', title='Home', user=user, posts=posts)
