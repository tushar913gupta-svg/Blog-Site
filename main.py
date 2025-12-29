from datetime import date
from flask import Flask, abort, render_template, redirect, url_for, flash
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text, Boolean
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from forms import CreatePostForm, RegisterForm, LoginForm, AdminForm, CommentForm
from hashlib import md5

def avatar(email):
    digest = md5(email.lower().encode('utf-8')).hexdigest()
    return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={100}'

def main_admin_only(f):
    @wraps(f)
    def decorate(*args, **kwargs):
        if current_user.id != 1:
            return abort(403)
        return f(*args, **kwargs)
    return decorate

def admin_only(f):
    @wraps(f)
    def decorate(*args, **kwargs):
        if not current_user.admin:
            return abort(403)
        return f(*args, **kwargs)
    return decorate

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
ckeditor = CKEditor(app)
Bootstrap5(app)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)

class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    admin: Mapped[bool] = mapped_column(Boolean)

    posts = relationship("BlogPost", back_populates="author")

    comments = relationship("Comment", back_populates="author")

class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))

    author = relationship("User", back_populates="posts")

    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)

    comments = relationship("Comment", back_populates="post")

class Comment(db.Model):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)

    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    author = relationship("User", back_populates="comments")

    post_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("blog_posts.id"))
    post = relationship("BlogPost", back_populates="comments")

with app.app_context():
    db.create_all()

@app.route('/register', methods=["GET","POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        result = db.session.execute(db.select(User).where(User.email==form.email.data))
        registered_user = result.scalar()

        if registered_user:
            flash("Account already exists. Please login instead.")
            return redirect(url_for("login"))

        admin = False
        if form.email.data == "tushar913gupta@gmail.com":
            admin = True

        password = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )

        user = User(
            email=form.email.data,
            password=password,
            name=form.name.data,
            admin = admin
        )
        db.session.add(user)
        db.session.commit()

        login_user(user)

        return redirect(url_for('get_all_posts'))
    return render_template("register.html", form=form)

@app.route('/login',methods=["GET","POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        password = form.password.data
        result = db.session.execute(db.select(User).where(User.email==form.email.data))
        user = result.scalar()

        if not user:
            flash("Account doesn't exist. Please try again.")
            return redirect(url_for("login"))

        elif not check_password_hash(user.password, password):
            flash("Password is incorrect. Please try again.")
            return redirect(url_for("login"))

        else:
            login_user(user)
            return redirect(url_for("get_all_posts"))

    return render_template("login.html", form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))

@app.route('/make-admin', methods=["GET","POST"])
@main_admin_only
def make_admin():
    form = AdminForm()
    if form.validate_on_submit():
        result = db.session.execute(db.select(User).where(User.email == form.email.data))
        user = result.scalar()

        if not user:
            flash("Account doesn't exist. Please try again.")
            return redirect(url_for("make_admin"))

        else:
            if user.admin:
                flash("Account is already an admin.")
                return redirect(url_for("make_admin"))
            else:
                user1 = db.get_or_404(User, user.id)
                user1.admin = True
                db.session.commit()
                return redirect(url_for("admin_list"))

    return render_template("login.html", form=form, admin=True)

@app.route('/admin-list')
@admin_only
def admin_list():
    result = db.session.execute(db.select(User).where(User.admin == True))
    users = result.scalars().all()
    return render_template("admin-list.html", users=users, administer=True)

@app.route('/remove-admin/<int:id>')
@main_admin_only
def remove_admin(id):
    user = db.get_or_404(User,id)
    user.admin = False
    db.session.commit()
    return redirect(url_for('admin_list'))

@app.route('/user-list')
@admin_only
def user_list():
    result = db.session.execute(db.select(User))
    users = result.scalars().all()
    return render_template("admin-list.html", users=users)

@app.route('/remove-user/<int:id>')
@admin_only
def remove_user(id):
    user = db.get_or_404(User,id)
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('user_list'))

@app.route('/')
def get_all_posts():
    result = db.session.execute(db.select(BlogPost).order_by(BlogPost.id)).scalars()
    posts = result.all()
    return render_template("index.html", posts=posts)

@app.route("/post/<int:id>", methods=["GET","POST"])
def show_post(id):
    form = CommentForm()
    post = db.get_or_404(BlogPost, id)

    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("Login/Register before entering a comment.")
            return redirect(url_for('login'))

        comment = Comment(
            text=form.comment.data,
            author=current_user,
            post=post
        )
        db.session.add(comment)
        db.session.commit()

    return render_template("post.html", post=post, form=form, avatar=avatar)

@app.route("/new-post", methods=["GET", "POST"])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            date=date.today().strftime("%B %d, %Y"),
            body=form.body.data,
            author=current_user,
            img_url=form.img_url.data
        )
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('get_all_posts'))
    return render_template("make-post.html", form=form)

@app.route("/edit-post/<int:id>", methods=["GET", "POST"])
@admin_only
def edit_post(id):
    post = db.get_or_404(BlogPost, id)
    form = CreatePostForm(
        title=post.title,
        author=post.author,
        img_url=post.img_url,
        subtitle=post.subtitle,
        body=post.body
    )
    if form.validate_on_submit():
        post.title = form.title.data
        post.author = current_user
        post.img_url = form.img_url.data
        post.subtitle = form.subtitle.data
        post.body = form.body.data
        db.session.commit()
        return redirect(url_for('show_post', id=id))
    return render_template("make-post.html", form=form, edit=True)

@app.route("/delete/<int:id>")
@admin_only
def delete_post(id):
    post = db.get_or_404(BlogPost, id)
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('get_all_posts'))

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

if __name__ == "__main__":
    app.run(debug=True, port=5002)
