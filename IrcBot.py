from ircutils import client
import os

IRC_SERVER = os.environ.get('IRC_SERVER', 'irc.freenode.net')
IRC_PORT = int(os.environ.get('IRC_PORT', '6667'))
IRC_CHANNEL = os.environ.get('IRC_CHANNEL', '#sharehood')
IRC_CHANNEL_PASSWORD = os.environ.get('IRC_CHANNEL_PASSWORD')
IRC_NAME = os.environ.get('IRC_NAME', 'SharehoodProcScalar')


def send_irc_message(message):
    def on_welcome(client, event):
        client.send_notice(IRC_CHANNEL, message)
        client.quit()

    def message_printer(client, event):
        print "<{0}/{1}> {2}".format(event.source, event.target, event.message)

    # Create a SimpleClient instance
    my_client = client.SimpleClient(nick=IRC_NAME)

    # Add the event handlers
    my_client["join"].add_handler(on_welcome)
    #my_client["channel_message"].add_handler(message_printer)

    # Finish setting up the client
    #my_client.connect(IRC_SERVER, port=IRC_PORT)
    #my_client.connect("irc.freenode.net", channel="#sharehood insecure")
    my_client.connect("irc.freenode.net", channel="#hmmsharehoodtest")
    my_client.start()
