from flask import Flask, render_template, jsonify, request, redirect, url_for
import chatterbot

app = Flask(__name__)


@app.route("/")
def index():
    return """
  <h1>Python Flask in Docker!</h1>
  <p>A sample web-app for running Flask inside Docker.</p>
  """


@app.route('/bot', methods=['PUT'])
def update_bot():
    try:
        if 'questions_list' in request.values or request.files.getlist("yml_files") or request.files.getlist("csv_files"):
            chatterbot = chatterbot.ChatBot("Ben", storage_adapter="chatterbot.storage.SQLStorageAdapter",
                                     database_uri="sqlite:///db.sqlite3", )

            if 'questions_list' in request.values:
                try:
                    questions = request.values['questions_list'].split(";")
                    if questions:
                        list_trainer = ListTrainer(chatterbot)
                        list_trainer.train(questions)
                except Exception as ex:
                    response_message = ex
                    print(ex)
            yml_files = request.files.getlist("yml_files")
            csv_files = request.files.getlist("csv_files")

            if not path.exists('tmps/{0}'.format(request.values['user_id'])):
                makedirs('tmps/{0}'.format(request.values['user_id']))

            if yml_files:
                trainer = ChatterBotCorpusTrainer(chatterbot)
                for file in yml_files:
                    filepath = './tmps/{}/{}'.format(request.values['user_id'], file.filename)
                    file.save(filepath)
                    trainer.train(filepath)
                    remove(filepath)

            if csv_files:
                if not list_trainer:
                    list_trainer = ListTrainer(chatterbot)

                for file in csv_files:
                    filepath = './tmps/{}/{}'.format(request.values['user_id'], file.filename)
                    file.save(filepath)

                    with open(filepath) as csv_file:
                        delimiter = csv_file.__next__().strip()[-1:]
                        csv_file.seek(0)
                        csv_reader = csv.reader(csv_file, delimiter=delimiter)
                        for row in csv_reader:
                            conversation = []
                            conversation.extend([row[0], row[1]])
                            list_trainer.train(conversation)

                        # update last inserted tag with filename
                    remove(filepath)
            response = jsonify({'message': '{} was updated!'})
            return response, 200
        else:
            response = jsonify({'message': 'Bot or user not found!'})
            return response, 200
    except Exception as ex:
        print(ex)
        response = jsonify({'message': str(ex)})
        return response, 200


@app.route('/get_response', methods=['GET'])
def get_response():
    try:
        chatterbot1 = chatterbot.ChatBot("Ben", storage_adapter="chatterbot.storage.SQLStorageAdapter",
                                            database_uri="sqlite:///db.sqlite3", )

        response = chatterbot1.get_response(request.values['question'])

        response = jsonify({'answer': '{}'.format(response)})
            # response.headers.add("Access-Control-Allow-Credentials", "true")
        return response, 200
    except Exception as ex:
        print(ex)
        return "Error geting the response!"


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
