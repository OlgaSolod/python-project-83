from flask import (
    Flask,
    render_template,
    url_for,
    flash,
    request,
    redirect
    )
import psycopg2
from psycopg2.extras import NamedTupleCursor
import os
from dotenv import load_dotenv
from validators import url as validate_url
from urllib.parse import urlparse


app = Flask(__name__)
load_dotenv()
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')
conn = psycopg2.connect(DATABASE_URL)


@app.route("/")
def index():
    return render_template(
        'index.html',
        title='Анализатор страниц'
    )


@app.get("/urls")
def urls_get():
    urls = get_all_from_urls()
    print(urls)
    return render_template(
        'urls.html',
        data=urls
        )


@app.post("/urls")
def urls_post():
    actual_url = request.form.get('url')
    if validate_url(actual_url):
        scheme = urlparse(actual_url).scheme
        hostname = urlparse(actual_url).hostname
        url = f"{scheme}://{hostname}"
        if check_url_in_urls(url):
            url_id = insert_url_in_urls(url)
            flash("Страница успешно добавлена", category='success')
            return redirect(url_for('url_page', id=url_id))
        else:
            flash("Страница уже существует", category='info')
            url_id = find_id_in_urls(url)
            return redirect(url_for('url_page', id=url_id))
    elif not validate_url(actual_url) or len(actual_url) > 255:
        flash("Некорректный URL", category='danger')
        return render_template('index.html'), 422


@app.get('/urls/<int:id>')
def url_page(id):
    page = get_data_from_urls(id)
    checks = find_data_from_url_checks(id)
    if page:
        id, name, created_at = page
        return render_template(
            'url_page.html',
            name=name, id=id,
            created_at=created_at,
            data=checks
            )
    else:
        return render_template('404.html')


@app.post('/urls/<int:id>/checks')
def url_check(id):
    get_url_id_from_url_checks(id)
    return redirect(url_for('url_page', id=id))


def get_url_id_from_url_checks(id):
    sql = 'insert into url_checks (url_id) values (%s);'
    with conn.cursor(cursor_factory=NamedTupleCursor) as cur:
        cur.execute(sql, (id,))
        conn.commit()


def check_url_in_urls(url):
    sql = "select * from urls where name = %s;"
    with conn.cursor() as cur:
        cur.execute(sql, (url,))
        return cur.fetchone() is None


def insert_url_in_urls(url):
    sql = '''insert into urls
            (name) values (%s)
            RETURNING id;'''
    with conn.cursor() as cur:
        cur.execute(sql, (url,))
        url_id = cur.fetchone()[0]
        conn.commit()
    return url_id


def get_data_from_urls(id):
    sql = "select id, name, created_at::date from urls where id = %s;"
    with conn.cursor(cursor_factory=NamedTupleCursor) as cur:
        cur.execute(sql, (id,))
        return cur.fetchone()


def get_all_from_urls():
    sql = '''select distinct
                urls.id,
                (urls.name),
                checks.created_at::date,
                checks.status_code
            from urls
            left join url_checks as checks on urls.id = checks.url_id
            order by checks.created_at::date desc;
            '''
    with conn.cursor(cursor_factory=NamedTupleCursor) as cur:
        cur.execute(sql)
        return cur.fetchall()


def find_id_in_urls(name):
    sql = "select id from urls where name = %s;"
    with conn.cursor() as cur:
        cur.execute(sql, (name,))
        return cur.fetchone()[0]


def find_data_from_url_checks(id):
    sql = "select id, created_at::date from url_checks where url_id = %s;"
    with conn.cursor(cursor_factory=NamedTupleCursor) as cur:
        cur.execute(sql, (id,))
        return cur.fetchall()
