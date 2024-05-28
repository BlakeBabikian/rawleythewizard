from flask import Flask
import os

app = Flask(__name__)
app.secret_key = "RawleyTheWizard"
port = int(os.environ.get('PORT', 5000))