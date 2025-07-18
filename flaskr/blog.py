from flask import(
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort
from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('blog', __name__)

@bp.route('/')
def index():
    db = get_db()
    posts = db.execute(
        'SELECT p.id, title, body, created, author_id, username,'
        ' (SELECT COUNT(*) FROM like WHERE post_id = p.id AND action_ = 1) AS like_count,'
        ' (SELECT COUNT(*) FROM like WHERE post_id = p.id AND action_ = -1) AS dislike_count,'
        ' (SELECT action_ FROM like WHERE user_id = ? AND post_id = p.id) AS user_action'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' ORDER BY created DESC',
        (g.user['id'] if g.user else 0,)
    ).fetchall()
    return render_template('blog/index.html', posts=posts)

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = "Title is required."
        
        if error is not None:
            flash(error)
        
        else:
            db = get_db()
            db.execute(
                'INSERT INTO post (title, body, author_id)'
                ' VALUES (?, ?, ?)',
                (title, body, g.user['id'])
            )
            db.commit()
            return redirect(url_for('blog.index'))
    
    return render_template('blog/create.html')

def get_post(id, check_author=True):
    post = get_db().execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")
    
    if check_author and post['author_id'] != g.user['id']:
        abort(403)
    
    return post

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'
        
        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE post SET title = ?, body = ?'
                ' WHERE id = ?',
                (title, body, id)
            )
            db.commit()
            return redirect(url_for('blog.index'))
    
    return render_template('blog/update.html', post = post)

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.index'))

@bp.route('/<int:id>/like', methods=('POST',))
@login_required
def like(id):
    db = get_db()
    #if post exists
    post = get_post(id, check_author=False)
    if post is None:
        abort(404, f"Post id {id} does not exist.")
    
    #current user action check
    current_action = db.execute(
        'SELECT action_ FROM like WHERE user_id = ? AND post_id = ?',
        (g.user['id'], id)
    ).fetchone()

    #If no action exists, insert a new record with action = 1 (like)
    if current_action is None:
        db.execute(
            'INSERT INTO like (user_id, post_id, action_) VALUES (?,?,?)',
            (g.user['id'], id, 1)
        )
    elif current_action['action_'] == 1: #if already liked then toggle back
        db.execute(
            'DELETE FROM like WHERE user_id =? AND post_id =?',
            (g.user['id'], id)
        )
    elif current_action['action_'] == -1: #if disliked already then change intolike
        db.execute(
            'UPDATE like SET action_ =? WHERE user_id =? AND post_id=?',
            (1, g.user['id'], id)
        )
    
    db.commit()
    return redirect(url_for('blog.index'))

@bp.route('/<int:id>/dislike', methods=('POST',))
@login_required
def dislike(id):
    db = get_db()
    post = get_post(id, check_author=False)
    if post is None:
        abort(404, f"Post id {id} does not exist.")
    
    current_action = db.execute(
        'SELECT action_ FROM like WHERE user_id = ? AND post_id = ?',
        (g.user['id'], id)
    ).fetchone()

    if current_action is None:
        db.execute(
            'INSERT INTO like (user_id, post_id, action_) VALUES (?,?,?)',
            (g.user['id'], id, -1)
        )
    elif current_action['action_'] == -1: #if already disliked then toggle back
        db.execute(
            'DELETE FROM like WHERE user_id =? AND post_id =?',
            (g.user['id'], id)
        )
    elif current_action['action_'] == 1: #if liked already then change into dislike
        db.execute(
            'UPDATE like SET action_ =? WHERE user_id =? AND post_id=?',
            (-1, g.user['id'], id)
        )
    
    db.commit()
    return redirect(url_for('blog.index'))