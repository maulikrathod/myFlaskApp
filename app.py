from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
# from data import articles

app = Flask(__name__)

# Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Drc@1234'
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# init MYSQL
mysql = MySQL(app)


# Articles = articles()

#    HOME PAGE
@app.route('/')
def index():
    return render_template('home.html')

#   ABOUT
@app.route('/about')
def about():
    return render_template('about.html')

#   ARTICLES
@app.route('/articles')
def articles():
        #   CREATE CURSOR
        cur = mysql.connection.cursor()

        #   GET ARTICLES FROM DB
        results = cur.execute("SELECT * FROM articles")
        articles = cur.fetchall()

        if results > 0:
            return render_template('articles.html', articles = articles)
        else:
            msg = "NO Articles Found"
            return render_template('articles.html', msg = msg)

        #   CLOSE CONNECTION
        cur.close()


#   PERTICULER ARTICLES
@app.route('/article/<string:id>/')
def article(id):
    #   CREATE CURSOR
    cur = mysql.connection.cursor()

    #   GET ARTICLES FROM DB
    results = cur.execute("SELECT * FROM articles WHERE id = %s", [id])
    article = cur.fetchone()

    return render_template('article.html', article = article)

#   Register Form Class
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')

#   REGISTER
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute query
        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)",
                    (name, email, username, password))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('You are now registered and can log in', 'success')

        return redirect(url_for('index'))
    return render_template('register.html', form=form)


#   LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # get form fields
        username = request.form['username']
        password_candidate = request.form['password']

        # create cursor
        cur = mysql.connection.cursor()

        # get user by username
        result = cur.execute(
            "SELECT * FROM users WHERE username = %s", [username])
        if result > 0:
            # get the stored hash
            data = cur.fetchone()
            password = data['password']
            print(password)
            # compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # app.logger.info("PASSWORD MATCHED")
                session['logged_in'] = True
                session['username'] = username
                flash("You are now Logged in", "success")
                return redirect(url_for("dashboard"))
            else:
                error = "Invalid Login"
                return render_template('login.html', error=error)
            cur.close()
        else:
            error = "Username Not Found"
            return render_template('login.html', error=error)
    return render_template('login.html')


#   CHECK IF LOGGED_IN
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Unauthorized, Please Login", "danger")
            return redirect(url_for("login"))
    return wrap

#   LOGOUT
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash("You are now Loged Out", "success")
    return redirect(url_for("login"))

#   DASHBOARD
@app.route('/dashboard')
@is_logged_in
def dashboard():
    #   CREATE CURSOR
    cur = mysql.connection.cursor()

    #   GET ARTICLES FROM DB
    results = cur.execute("SELECT * FROM articles")
    articles = cur.fetchall()

    if results > 0:
        return render_template('dashboard.html', articles = articles)
    else:
        msg = "NO Articles Found"
        return render_template('dashboard.html', msg = msg)

    #   CLOSE CONNECTION
    cur.close()

#   ARTICLES Form Class
class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200)])
    body = TextAreaField('Body', [validators.Length(min=30)])


#   ADD ARTICLE
@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        #   CREATE CURSOR
        cur = mysql.connection.cursor()

        #   EXECUTE
        cur.execute("INSERT INTO articles(title, body, author) VALUES(%s, %s, %s)",(title, body, session['username']))

        #   COMMIT TO DB
        mysql.connection.commit()

        #   CLOSE CONNECTION
        cur.close()

        flash("Articles Created", "success")
        return redirect(url_for('dashboard'))

    return render_template('add_article.html', form=form)


#   EDIT ARTICLE
@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):
    #   CREATE CURSOR
    cur = mysql.connection.cursor()

    #   GET THE USER BY ID
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = cur.fetchone()

    # GET FORM
    form = ArticleForm(request.form)

    # POPULATE ARTICLE FORMS
    form.title.data = article['title']
    form.body.data = article['body']

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        #   CREATE CURSOR
        cur = mysql.connection.cursor()
        #   EXECUTE
        cur.execute("UPDATE articles SET title = %s, body = %s WHERE id = %s", (title, body, id))
        #   COMMIT TO DB
        mysql.connection.commit()
        #   CLOSE CONNECTION
        cur.close()

        flash("Articles Updated", "success")
        return redirect(url_for('dashboard'))

    return render_template('edit_article.html', form=form)


#    DELETE ARTICLE
@app.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):
    #   CREATE CURSOR
    cur = mysql.connection.cursor()
    #   EXECUTE
    cur.execute("DELETE FROM articles WHERE id = %s", [id])
    #   COMMIT TO DB
    mysql.connection.commit()
    #   CLOSE CONNECTION
    cur.close()

    flash("Articles Deleted", "success")
    return redirect(url_for('dashboard'))


if __name__ == "__main__":
    app.secret_key = 'secret123'
    app.run(debug=True)
