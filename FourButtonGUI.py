import kivy
kivy.require('1.5.2')
from kivy.support import install_twisted_reactor
install_twisted_reactor()
import twisted
from twisted.internet import reactor
from twisted.internet import protocol
import socket
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import StringProperty
from kivy.properties import ListProperty


#########################################################
#SERVER
#########################################################
class TCPServerProtocol(protocol.Protocol):


    def dataReceived(self, data):
        self.factory.app.display_received_data(data, self.transport.getPeer().host)

    def connectionMade(self):
        client = self.transport.getPeer()
        self.factory.app.server_print_message(("Client connection from " + str(client.host)))
        self.factory.client_list.append(self)
        self.factory.client_ip_list.append(client.host)

    def connectionLost(self, reason):
        client = self.transport.getPeer()
        self.factory.app.server_print_message(("Lost client connection from " + str(client.host)))
        self.factory.client_list.remove(self)
        self.factory.client_ip_list.remove(client.host)


class TCPServerFactory(protocol.Factory):
    protocol = TCPServerProtocol
    client_list = []
    client_ip_list = []

    def __init__(self, app):
        self.app = app


#########################################################
#CLIENT
#########################################################
class TCP_ClientProtocol(protocol.Protocol):
    def connectionMade(self):
        self.factory.app.client_on_connection(self.transport)

    def connectionLost(self, reason):
        self.factory.app.client_off_connection(self.transport)

    def dataReceived(self, data):
        pass


class TCP_ClientFactory(protocol.ClientFactory):
    protocol = TCP_ClientProtocol
    def __init__(self, app):
        self.app = app

    def clientConnectionFailed(self, conn, reason):
        self.app.client_print_message("connection failed")

#########################################################
#MAIN WINDOW
#########################################################
class Controller(FloatLayout):
    connection = None
    listen_state = StringProperty("LISTEN")
    client_connect_state = StringProperty("CONNECT")
    listening_port = twisted.internet.interfaces.IListeningPort
    client_connector = twisted.internet.interfaces.IConnector
    local_ip = StringProperty()
    server_text_color = ListProperty()
    client_text_color = ListProperty()


    #Constructor
    def __init__(self, **kwargs):
        super(Controller, self).__init__(**kwargs)
        self.local_ip = socket.gethostbyname(socket.gethostname())
        self.server_print_message("My ip address is " + self.local_ip)


    #SERVER SIDE
    #Listen
    def tcp_server_listen(self, button_id):
        if self.listen_state == "LISTEN":
            self.listen_state = "DISCONNECT"
            port = int(self.ids.tcp_server_port_text.text)
            self.listening_port = reactor.listenTCP(port, TCPServerFactory(self))
        else:
            self.listen_state = "LISTEN"
            self.listening_port.loseConnection()
            for index in range(0, len(TCPServerFactory.client_list)):
                TCPServerFactory.client_list[index].transport.loseConnection()



    #Server Data Received
    def display_received_data(self, msg, address):
        self.ids.tcp_server_listening_text.text += ("Data Received from %s:\n%s " %(address, msg)) + "\n"

    #Server Get Connection
    def server_get_connection(self):
        self.server_print_message("new client connected")

    #Server Print Message
    def server_print_message(self, msg):
        self.ids.tcp_server_listening_text.text += "Debug Message: " + "\n" + msg + "\n"

    #Server Get Client List
    def server_get_client_list(self):
        self.server_print_message(str(TCPServerFactory.client_ip_list))

    #CLIENT SIDE
    #Client Data Send
    def tcp_client_send(self, button_id):
        msg = self.ids.tcp_client_send_text.text
        if msg and self.connection:
            self.connection.write(msg)

    #Client Connect
    def tcp_client_connect(self, button_id):
        if self.client_connect_state == "CONNECT":
            ip_address = self.ids.tcp_client_ip_text.text
            port = int(self.ids.tcp_client_port_text.text)
            self.client_connector = reactor.connectTCP(ip_address, port, TCP_ClientFactory(self))
        elif self.client_connect_state == "DISCONNECT":
            self.client_connector.disconnect()


    #Client On Connection
    def client_on_connection(self, connection):
        self.client_connect_state = "DISCONNECT"
        self.client_print_message("connected successfully")
        self.connection = connection


    #Client Off Connection
    def client_off_connection(self, connection):
        self.client_connect_state = "CONNECT"
        self.client_print_message("client disconnected")
        self.connection = connection

    #Client Print Message
    def client_print_message(self, msg):
        self.ids.tcp_client_send_text.text += "Debug Message:\n" + msg + "\n"


#########################################################
#APP START
#########################################################
#App
class ControllerApp(App):

    def build(self):
        return Controller()


#Run App
if __name__ == '__main__':
    ControllerApp().run()