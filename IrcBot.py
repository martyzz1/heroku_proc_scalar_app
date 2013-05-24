from ircutils import client
import os

IRC_SERVER = os.environ.get('IRC_SERVER', 'irc.freenode.net')
IRC_PORT = int(os.environ.get('IRC_PORT', '6667'))
IRC_CHANNEL = os.environ.get('IRC_CHANNEL', False)
IRC_CHANNEL_PASSWORD = os.environ.get('IRC_CHANNEL_PASSWORD', False)
IRC_NAME = os.environ.get('IRC_NAME', 'ProcScalar')

room = "%s %s" % (IRC_CHANNEL, IRC_CHANNEL_PASSWORD)
print "room = %s" % room


def send_irc_message(message):
    def on_welcome(client, event):
        client.send_notice(str(IRC_CHANNEL), str(message))
        client.quit()

    def message_printer(client, event):
        print "<{0}/{1}> {2}".format(event.source, event.target, event.message)

    # Create a SimpleClient instance
    my_client = client.SimpleClient(nick=IRC_NAME)

    # Add the event handlers
    my_client["join"].add_handler(on_welcome)

    # Finish setting up the client
    #my_client.connect("irc.freenode.net", channel=room)
    my_client.connect("irc.freenode.net", channel="#hmmsharehoodtest")
    my_client.start()
