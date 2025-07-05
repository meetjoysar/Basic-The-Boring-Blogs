import os
from flask import Flask

def create_app(test_config=None):
    # creating and configuring app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY = 'dev',
        DATABASE = os.path.join(app.instance_path, 'flaskr.sqlite')
    )

    if test_config is None:
        #basically load the instance config, when test-config is not provided
        app.config.from_pyfile('config.py', silent=True) 
    else:
        #loading test config
        app.config.from_mapping(test_config)

    #ensuring the existance of instance folder
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    #simple hello page
    @app.route("/hello")
    def hello():
        return "Hello World"
    
    from . import db
    db.init_app(app)

    from . import auth
    app.register_blueprint(auth.bp)

    from . import blog
    app.register_blueprint(blog.bp)
    app.add_url_rule('/', endpoint='index')

    return app