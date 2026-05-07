from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

app = Flask(__name__)

app.config['SECRET_KEY'] = 'secretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(100), nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class RegisterForm(FlaskForm):
    username = StringField(
        'Username',
        validators=[DataRequired(), Length(min=3, max=20)]
    )

    password = PasswordField(
        'Password',
        validators=[DataRequired(), Length(min=5)]
    )

    submit = SubmitField('Register')


class LoginForm(FlaskForm):
    username = StringField(
        'Username',
        validators=[DataRequired()]
    )

    password = PasswordField(
        'Password',
        validators=[DataRequired()]
    )

    submit = SubmitField('Login')


class PostForm(FlaskForm):
    title = StringField(
        'Title',
        validators=[DataRequired()]
    )

    content = TextAreaField(
        'Content',
        validators=[DataRequired()]
    )

    submit = SubmitField('Submit')


@app.route('/')
def index():
    posts = Post.query.all()
    return render_template('index.html', posts=posts)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():

        existing_user = User.query.filter_by(
            username=form.username.data
        ).first()

        if existing_user:
            flash('Username already exists')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(
            form.password.data
        )

        user = User(
            username=form.username.data,
            password=hashed_password
        )

        db.session.add(user)
        db.session.commit()

        flash('Registration successful!')
        return redirect(url_for('login'))

    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():

        user = User.query.filter_by(
            username=form.username.data
        ).first()

        if user and check_password_hash(
            user.password,
            form.password.data
        ):

            login_user(user)

            flash('Login successful!')
            return redirect(url_for('dashboard'))

        else:
            flash('Invalid username or password')

    return render_template('login.html', form=form)


@app.route('/dashboard')
@login_required
def dashboard():

    posts = Post.query.filter_by(
        author=current_user.username
    ).all()

    return render_template(
        'dashboard.html',
        posts=posts
    )


@app.route('/create', methods=['GET', 'POST'])
@login_required
def create_post():

    form = PostForm()

    if form.validate_on_submit():

        post = Post(
            title=form.title.data,
            content=form.content.data,
            author=current_user.username
        )

        db.session.add(post)
        db.session.commit()

        flash('Post created successfully!')

        return redirect(url_for('dashboard'))

    return render_template(
        'create_post.html',
        form=form
    )


@app.route('/post/<int:post_id>')
def view_post(post_id):

    post = Post.query.get_or_404(post_id)

    return render_template(
        'view_post.html',
        post=post
    )


@app.route('/edit/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):

    post = Post.query.get_or_404(post_id)

    if post.author != current_user.username:
        flash('Unauthorized access')
        return redirect(url_for('dashboard'))

    form = PostForm()

    if form.validate_on_submit():

        post.title = form.title.data
        post.content = form.content.data

        db.session.commit()

        flash('Post updated successfully!')

        return redirect(url_for('dashboard'))

    form.title.data = post.title
    form.content.data = post.content

    return render_template(
        'edit_post.html',
        form=form
    )


@app.route('/delete/<int:post_id>')
@login_required
def delete_post(post_id):

    post = Post.query.get_or_404(post_id)

    if post.author != current_user.username:
        flash('Unauthorized access')
        return redirect(url_for('dashboard'))

    db.session.delete(post)
    db.session.commit()

    flash('Post deleted successfully!')

    return redirect(url_for('dashboard'))


@app.route('/logout')
@login_required
def logout():

    logout_user()

    flash('Logged out successfully!')

    return redirect(url_for('index'))


@app.route('/search')
def search():

    query = request.args.get('query')

    if query:
        posts = Post.query.filter(
            Post.title.contains(query)
        ).all()
    else:
        posts = []

    return render_template(
        'search.html',
        posts=posts,
        query=query
    )



if __name__ == '__main__':

    with app.app_context():
        db.create_all()

    app.run(debug=True)