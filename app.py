from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from datetime import date
from flask_cors import CORS, cross_origin
from json import dumps, loads
from passlib.hash import pbkdf2_sha256 as sha256
from flask_jwt_extended import (JWTManager, jwt_required, create_access_token,
                                jwt_refresh_token_required, create_refresh_token,
                                get_jwt_identity, set_access_cookies,
                                set_refresh_cookies, unset_jwt_cookies, get_csrf_token)
from os import path, makedirs, remove
from copy import copy
from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer, ListTrainer
import docker
import subprocess
import csv
import sqlite3

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres+psycopg2://postgres:ad@localhost:5432/chatbot-generator'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'a7cbba9d9acf4ec1d4c8cc4307c0c599'
app.config['JWT_SECRET_KEY'] = 'dbdf36be0fb6bba6dcbc6de18c243195'

app.config['JWT_BLACKLIST_ENABLED'] = False

app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access', 'refresh']

app.config['JWT_ACCESS_COOKIE_PATH'] = '/'
app.config['JWT_TOKEN_LOCATION'] = ['cookies']
app.config['JWT_COOKIE_SECURE'] = False
app.config['JWT_COOKIE_CSRF_PROTECT'] = True

app.config['UPLOAD_FOLDER'] = 'tmps'
# app.config['CSRF_COOKIE_NAME '] = "XSRF-TOKEN";

cors = CORS(app)

db = SQLAlchemy(app)

jwt = JWTManager(app)

migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)

active_bots = {}


class Users(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.VARCHAR(250), unique=True, nullable=False)
    firstname = db.Column(db.VARCHAR(250))
    lastname = db.Column(db.VARCHAR(250))
    password = db.Column(db.VARCHAR(250))
    email = db.Column(db.VARCHAR(250))
    company = db.Column(db.VARCHAR(250))

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def to_json(self):
        return {
            'id': self.id,
            'username': self.username,
            'firstname': self.firstname,
            'lastname': self.lastname,
            'email': self.email,
            'company': self.company
        }

    @staticmethod
    def get_all_users():
        return Users.query.all()

    @staticmethod
    def get_one_user(id):
        return Users.query.get(id)

    @staticmethod
    def get_user_by_name(user_name):
        return Users.query.filter_by(username=user_name).first()

    @staticmethod
    def generate_hash(password):
        return sha256.hash(password)

    @staticmethod
    def verify_hash(password, hash):
        return sha256.verify(password, hash)


class Bots(db.Model):
    __tablename__ = "bots"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.VARCHAR(250))
    user_id = db.Column(db.Integer)

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    @staticmethod
    def get_all_bots():
        return Bots.query.all()

    @staticmethod
    def get_user_bots(user_id):
        return Bots.query.filter_by(user_id=user_id)

    @staticmethod
    def get_bot_by_id(bot_id):
        return Bots.query.filter_by(id=bot_id).first()

    @staticmethod
    def get_one_bot(id):
        return Bots.query.get(id)

    def to_json(self):
        return {
            'id': self.id,
            'name': self.name
        }


class Tags(db.Model):
    __tablename__ = "tags"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.VARCHAR())
    bot_id = db.Column(db.Integer)

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    @staticmethod
    def get_all_tags():
        return Tags.query.all()

    @staticmethod
    def get_bot_tags(bot_id):
        return Tags.query.filter_by(bot_id=bot_id)

    @staticmethod
    def get_one_tag(id):
        return Tags.query.get(id)

    @staticmethod
    def insert_tags(tags_list):
        return db.engine.execute(Tags.__table__.insert(), tags_list)


class RevokedTokenModel(db.Model):
    __tablename__ = 'revoked_tokens'
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(120))

    def add(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def is_jti_blacklisted(cls, jti):
        query = cls.query.filter_by(jti=jti).first()
        return bool(query)


@app.route("/user", methods=['GET'])
def get_user():
    try:
        db_user = Users.get_user_by_name(request.values['username'])

        return jsonify(db_user.to_json())
    except Exception as ex:
        return str(ex)


@app.after_request
def after_request(response):
    response.headers.add("Access-Control-Allow-Credentials", "true")
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response


@app.route("/register", methods=['POST'])
def register_user():
    try:
        new_user = Users(
            username=request.values['username'],
            firstname=request.values['first_name'],
            lastname=request.values['last_name'],
            company=request.values['company'],
            email=request.values['email'],
            password=Users.generate_hash(request.values['password'])
        )

        new_user.save()

        access_token = create_access_token(identity=request.values['username'])
        refresh_token = create_refresh_token(identity=request.values['username'])

        response = jsonify({
            'message': 'User {} was created'.format(request.values['username']),
            'user_id': new_user.id
        })

        set_access_cookies(response, access_token)
        set_refresh_cookies(response, refresh_token)

        return response, 200
    except Exception as ex:
        return str(ex)


@app.route("/login", methods=['POST'])
# @cross_origin()
def login_user():
    try:
        current_user = Users.get_user_by_name(request.values['username'])

        if not current_user:
            return jsonify({'message': 'User {} doesn\'t exist'.format(request.values['username'])})

        if Users.verify_hash(request.values['password'], current_user.password):
            access_token = create_access_token(identity=request.values['username'])
            refresh_token = create_refresh_token(identity=request.values['username'])

            response = jsonify({
                'message': 'Logged in as {}'.format(current_user.username),
                'user_id': current_user.id,
                'csrf_token': get_csrf_token(access_token)
            })

            set_access_cookies(response, access_token)
            set_refresh_cookies(response, refresh_token)

            # response.headers.add("Access-Control-Allow-Credentials", "true")

            return response, 200
        else:
            return jsonify({'message': 'Wrong credentials'})
    except Exception as ex:
        return str(ex)


@app.route('/refresh', methods=['POST'])
@jwt_refresh_token_required
def refresh():
    # Create the new access token
    current_user = get_jwt_identity()
    access_token = create_access_token(identity=current_user)

    # Set the access JWT and CSRF double submit protection cookies
    # in this response
    resp = jsonify({'refresh': True})
    set_access_cookies(resp, access_token)
    return resp, 200


@app.route('/logout', methods=['POST'])
def logout():
    resp = jsonify({'logout': True})
    unset_jwt_cookies(resp)
    return resp, 200


@jwt.token_in_blacklist_loader
def check_if_token_in_blacklist(decrypted_token):
    jti = decrypted_token['jti']
    return RevokedTokenModel.is_jti_blacklisted(jti)


# @jwt_required
# def logout_user_access():
#     jti = get_raw_jwt()['jti']
#     try:
#         revoked_token = RevokedTokenModel(jti=jti)
#         revoked_token.add()
#         return {'message': 'Access token has been revoked'}
#     except:
#         return {'message': 'Something went wrong'}, 500
#
#
# @jwt_refresh_token_required
# def logout_user_refresh():
#     jti = get_raw_jwt()['jti']
#     try:
#         revoked_token = RevokedTokenModel(jti=jti)
#         revoked_token.add()
#         return {'message': 'Refresh token has been revoked'}
#     except:
#         return {'message': 'Something went wrong'}, 500


# @jwt.unauthorized_loader
# def unauthorized_loader(msg):
#     return render_template('register/register.html')
#
#
# @jwt.expired_token_loader
# def expired_token(msg):
#     return render_template('register/register.html')


@app.route('/addedit_bot', methods=['GET'])
@jwt_required
def addedit_bot():
    return render_template('editbot/bot.html')


def generate_tag(tag_name, bot_id):
    return {
        "name": tag_name,
        "bot_id": bot_id
    }


@app.route('/create_bot', methods=['POST'])
@jwt_required
def create_bot():
    try:
        name = request.values['name']
        # knowledge = loads(request.values['knowledge'])
        knowledge = request.values['knowledge'].split(",") if request.values['knowledge'] != '' else []
        db_user = Users.get_user_by_name(get_jwt_identity())

        new_bot = Bots(
            name=name,
            user_id=db_user.id
        )

        new_bot.save()

        tags_list = [generate_tag(tag, new_bot.id) for tag in knowledge] if knowledge else []
        corpus_list = ['chatterbot.corpus.english.{}'.format(tag) for tag in knowledge] if knowledge else []
        Tags.insert_tags(tags_list)

        if not path.exists('bots_db/{0}'.format(db_user.id)):
            makedirs('bots_db/{0}'.format(db_user.id))

        new_chatterbot = ChatBot(name, storage_adapter="chatterbot.storage.SQLStorageAdapter",
                                 database_uri="sqlite:///bots_db/{0}/{1}.sqlite3".format(db_user.id, name))
        trainer = ChatterBotCorpusTrainer(new_chatterbot)

        if corpus_list:
            trainer.train(
                *corpus_list
            )

        active_bots.update({
            '{0}.{1}'.format(db_user.id, name): copy(new_chatterbot)
        })

        yml_files = request.files.getlist("yml_files")
        csv_files = request.files.getlist("csv_files")

        if not path.exists('tmps/{0}'.format(db_user.id)):
            makedirs('tmps/{0}'.format(db_user.id))

        if yml_files:
            for file in yml_files:
                filepath = path.join(app.config['UPLOAD_FOLDER'] + '\{0}'.format(db_user.id), file.filename)
                file.save(filepath)
                trainer.train(filepath)
                remove(filepath)

        if csv_files:
            list_trainer = ListTrainer(new_chatterbot)
            for file in csv_files:
                filepath = path.join(app.config['UPLOAD_FOLDER'] + '\{0}'.format(db_user.id), file.filename)
                file.save(filepath)
                conversation = []
                with open(filepath) as csv_file:
                    delimiter = csv_file.__next__().strip()[-1:]
                    csv_file.seek(0)
                    csv_reader = csv.reader(csv_file, delimiter=delimiter)
                    for row in csv_reader:
                        conversation.extend([row[0], row[1]])

                    list_trainer.train(conversation)
                    # update last inserted tag with filename
                remove(filepath)

        response = jsonify({'message': '{} was created!'.format(name)})
        return response, 200
    except Exception as ex:
        print(ex)
        response = jsonify({'message': 'Error!'})
        return response, 200


@app.route('/get_response', methods=['GET'])
@jwt_required
def get_response():
    if 'bot_id' in request.args and 'user_id' in request.args:
        print(active_bots)
        try:
            bot_name = Bots.get_bot_by_id(request.values['bot_id']).name

            if not '{0}.{1}'.format(request.values['user_id'], bot_name) in active_bots:
                chatterbot = ChatBot(bot_name, storage_adapter="chatterbot.storage.SQLStorageAdapter",
                                     database_uri="sqlite:///bots_db/{0}/{1}.sqlite3".format(request.values['user_id'],
                                                                                             bot_name))
                active_bots.update({
                    '{0}.{1}'.format(request.values['user_id'], bot_name): copy(chatterbot)
                })

                response = chatterbot.get_response(request.values['question'])
            else:
                response = active_bots[
                    '{0}.{1}'.format(request.values['user_id'], bot_name)].get_response(
                    request.values['question'])

            response = jsonify({'answer': '{}'.format(response)})
            # response.headers.add("Access-Control-Allow-Credentials", "true")
            return response, 200
        except Exception as ex:
            print(ex)
            return "Error geting the response!"


@app.route('/bot', methods=['DELETE'])
@jwt_required
def delete_bot():
    if 'bot_id' in request.args and 'user_id' in request.args:
        try:
            bot = Bots.get_bot_by_id(request.args['bot_id'])
            response = jsonify({'Deleted bot': '{}'.format(bot.name)})
            bot.delete()

            return response, 200
        except Exception as ex:
            print(ex)
            return "Error deleting the bot!"


@app.route('/')
def index():
    return render_template('register/register.html')


@app.route('/get_user_bots', methods=['GET'])
@jwt_required
def get_user_bots():
    if 'user_id' in request.args:
        userBots = Bots.get_user_bots(request.values['user_id'])

        response = jsonify(bots=[bot.to_json() for bot in userBots])
        return response, 200
    else:
        return jsonify({'message': 'No user id provided'}), 200


@app.route('/most_asked_questions', methods=['GET'])
@jwt_required
def get_most_asked_questions():
    if 'bot_id' in request.args and 'user_id' in request.args:
        userBot = Bots.get_bot_by_id(request.args['bot_id'])

        server_db_path = path.join("bots_db/{0}/{1}.sqlite3".format(request.values['user_id'], userBot.name))

        conn = sqlite3.connect(server_db_path)
        cur = conn.cursor()
        cur.execute("SELECT text, COUNT(*) as number_asked FROM statement GROUP BY text ORDER BY Count(*) DESC LIMIT 0,9")
        # cur.execute(
        #     "SELECT s.text, COUNT(*) as number_asked, t.name FROM statement s INNER JOIN tag_association ta ON ta.statement_id = s.id INNER JOIN tag t on t.id = ta.tag_id GROUP BY text ORDER BY Count(*) DESC LIMIT 0,9")
        rows = cur.fetchall()

        questions = []
        for row in rows:
            questions.append(row)

        response = jsonify(questions)
        return response, 200
    else:
        return jsonify({'message': 'No user id provided'}), 200


@app.route('/most_asked_topics_bot', methods=['GET'])
@jwt_required
def get_most_asked_topics_bot():
    if 'bot_id' in request.args and 'user_id' in request.args:
        userBot = Bots.get_bot_by_id(request.args['bot_id'])

        server_db_path = path.join("bots_db/{0}/{1}.sqlite3".format(request.values['user_id'], userBot.name))

        conn = sqlite3.connect(server_db_path)
        cur = conn.cursor()
        cur.execute("SELECT t.name, COUNT(*) as number_asked FROM statement s INNER JOIN tag_association ta ON ta.statement_id = s.id INNER JOIN tag t on t.id = ta.tag_id GROUP BY t.name ORDER BY Count(*) DESC LIMIT 0,5")
        rows = cur.fetchall()

        questions = []
        for row in rows:
            questions.append(row)

        response = jsonify(questions)
        return response, 200
    else:
        return jsonify({'message': 'No user id provided'}), 200


@app.route('/bot_usage', methods=['GET'])
@jwt_required
def get_bot_usage():
    if 'bot_id' in request.args and 'user_id' in request.args:
        userBot = Bots.get_bot_by_id(request.args['bot_id'])

        server_db_path = path.join("bots_db/{0}/{1}.sqlite3".format(request.values['user_id'], userBot.name))

        conn = sqlite3.connect(server_db_path)
        cur = conn.cursor()
        cur.execute("SELECT strftime('%m',created_at) AS month_name, COUNT(*) AS usage_stats FROM statement GROUP BY strftime('%m',created_at)")
        rows = cur.fetchall()

        questions = []
        for row in rows:
            questions.append(row)

        response = jsonify(questions)
        return response, 200
    else:
        return jsonify({'message': 'No user id provided'}), 200


@app.route('/user_safe', methods=['GET'])
@jwt_required
def protected():
    username = "admin sure"
    return jsonify({'hello': 'from {}'.format(username)}), 200


@app.route('/build_docker_img', methods=['GET'])
@jwt_required
def build_docker_image():
    client = docker.from_env()
    new_image = client.images.build(path="./docker_template", tag='chatbot')

    ret = subprocess.run(['docker', 'save', '-o', './chatbot2.tar', 'chatbot'])
    print(ret)
    username = "admin sure"
    return jsonify({'hello': 'from {}'.format(username)}), 200


@app.route('/user_unsafe', methods=['GET'])
def protected_1():
    username = "probably admin"
    return jsonify({'hello': 'from {}'.format(username)}), 200


@app.route('/home')
@jwt_required
def home():
    return render_template('home/home.html')


if __name__ == '__main__':
    # app.run()
    manager.run()
