from flask import Flask, render_template
from dotenv import load_dotenv
import os


app = Flask(__name__)
load_dotenv()
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')


@app.route("/")
def main_page():
    return render_template(
        'index.html',
        title='Анализатор страниц'
    )
