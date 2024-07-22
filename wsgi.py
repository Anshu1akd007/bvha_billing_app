from app import app
from flask_sqlalchemy import SQLAlchemy
import flask
app = flask.Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bills.db'
db = SQLAlchemy(app)
if __name__ == '__main__':
    with app.app_context():
        # db.drop_all() # use this to drop prevous database
        db.create_all()
    app.run(debug=True)
