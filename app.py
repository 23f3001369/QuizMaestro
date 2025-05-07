from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
# from datetime import datetime

app = Flask(__name__)
app.secret_key = '93497481983a33913f9dbe2a8473938d615ebeec2139dcb8aaaa4253536f2e89'
import config
import models

import routes



