from chatterbot import ChatBot

chatbot = ChatBot('Chatbot', storage_adapter="chatterbot.storage.SQLStorageAdapter", database="db.sqlite3",
                  database_uri="sqlite:///db.sqlite3")

while (True):
    user_input = input()
    print(chatbot.get_response(user_input))
