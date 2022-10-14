from flask import Flask, render_template, url_for, \
    redirect, request,session, flash
from flask_bootstrap import Bootstrap
from flask_mysqldb import MySQL
import yaml
import os
from werkzeug.security import generate_password_hash,check_password_hash
from flask_ckeditor import CKEditor

app = Flask(__name__)
Bootstrap(app)
CKEditor(app)

db = yaml.safe_load(open('db.yaml'))
app.config['MYSQL_HOST'] = db['mysql_host']
app.config['MYSQL_USER'] = db['mysql_user']
app.config['MYSQL_PASSWORD'] = db['mysql_password']
app.config['MYSQL_DB'] = db['mysql_db']
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config['SECRET_KEY'] = os.urandom(24)

mysql = MySQL(app)

@app.route('/')
def index():
    cursor = mysql.connection.cursor()
    result_value = cursor.execute("SELECT * FROM blog")
    if result_value > 0:
        blogs = cursor.fetchall()
        cursor.close()
        return render_template('index.html',blogs=blogs)
    return render_template('index.html', blogs=None)

@app.route('/about/')
def about():
    return render_template('about.html')

@app.route('/blogs/<int:id>')
def blogs(id):
    cursor = mysql.connection.cursor()
    result_value = cursor.execute("SELECT * FROM blog WHERE blog_id = {}".format(id))
    if result_value>0:
        blog = cursor.fetchone()
        return render_template('blogs.html',blog=blog)
    return 'Blog is not found'

@app.route('/register/',methods=['GET','POST'])
def register():
    if request.method == 'POST':
        user_details = request.form
        if user_details['password'] != user_details['confirmPassword']:
            flash('Passwords do not match! Try again','danger')
            return render_template('register.html')
        try:
            cursor = mysql.connection.cursor()
            #genpass = generate_password_hash(user_details['password'], method='pbkdf2:sha256')
            cursor.execute("INSERT INTO user(first_name, last_name, user_name, email, password) VALUES (%s, %s, %s, %s, %s)",
                           (user_details['first_name'],user_details['last_name'],
                            user_details['user_name'],user_details['email'],
                            generate_password_hash(user_details['password'])))

            mysql.connection.commit()
            cursor.close()
            flash('Registraton successful! please login','success')
            return redirect('/login')
        except:
            flash('Error!!!!')
            return render_template('register.html')
    return render_template('register.html')

@app.route('/login/',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        user_details = request.form
        user_name = user_details['user_name']
        cursor = mysql.connection.cursor()
        results_value = cursor.execute("SELECT * FROM user WHERE user_name = %s",([user_name]))
        if results_value > 0:
            user = cursor.fetchone()
            if check_password_hash(user['password'],user_details['password']):
                session['login'] = True
                session['first_name'] = user['first_name']
                session['last_name'] = user['last_name']
                flash('Weclome' + session['first_name'] + '!You have been successfully logged in','success')
            else:
                cursor.close
                flash('Password is incorrect!','danger')
                return render_template('login.html')
        else:
            cursor.close()
            flash(f"User doesn't exist", 'danger')
            return render_template('login.html')
        cursor.close()
        return redirect('/')
    return render_template('login.html')

@app.route('/write-blog/',methods=['GET','POST'])
def write_blog():
    if request.method == 'POST':
        blogpost = request.form
        title = blogpost['title']
        body = blogpost['body']
        author = session['first_name']+''+session['last_name']
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO blog (title, body, author) VALUES (%s, %s, %s)", (title,body,author))
        mysql.connection.commit()
        cursor.close()
        flash("Success", "success")
        return redirect('/')
    return render_template('write-blog.html')

@app.route('/my-blogs/')
def my_blogs():
    try:
        author = session['first_name']+''+session['last_name']
        cursor = mysql.connection.cursor()
        result_value = cursor.execute("SELECT * FROM blog WHERE author = %s", [author])
        if result_value>0:
            my_blogs = cursor.fetchall()
            return render_template("my-blogs.html", my_blogs=my_blogs)
        else:
            return render_template('my-blogs.html',my_blogs=None)
    except:
        flash('You are not logged in!!!!')
        return redirect('/login')

@app.route('/edit-blog/<int:id>',methods=['GET','POST'])
def edit_blog(id):
    if request.method == 'POST':
        cursor = mysql.connection.cursor()
        title = request.form['title']
        body = request.form['body']
        cursor.execute("UPDATE blog SET title = %s, body = %s WHERE blog_id = %s",
                       (title,body,id))
        mysql.connection.commit()
        cursor.close()
        flash('Blog is updated successfully','success')
        return redirect('/blogs/{}'.format(id))
    cursor = mysql.connection.cursor()
    result_value = cursor.execute("SELECT * FROM blog WHERE blog_id = {}".format(id))
    if result_value>0:
        blog = cursor.fetchone()
        blog_form = {}
        blog_form['title'] = blog['title']
        blog_form['body'] = blog['body']
        return render_template('edit-blog.html',blog_form = blog_form)


@app.route('/delete-blog/<int:id>')
def delete_blog(id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM blog WHERE blog_id ={}".format(id))
    mysql.connection.commit()
    flash("Your blog has been deleted","success")
    return redirect("/my-blogs")

@app.route('/logout/')
def logout():
    session.clear()
    flash('You have been logged out','info')
    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True,port=5002)

