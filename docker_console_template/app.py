import chatterbot

chatbot = chatterbot.ChatBot("Ben", storage_adapter="chatterbot.storage.SQLStorageAdapter",
                                     database_uri="sqlite:///db.sqlite3",)


while(True):
    str = input()
    print(chatbot.get_response(str))
