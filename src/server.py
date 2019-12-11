#  Created by Artem Manchenkov
#  artyom@manchenkoff.me
#
#  Copyright © 2019
#
#  Сервер для обработки сообщений от клиентов
#
#  Ctrl + Alt + L - форматирование кода
#
from twisted.internet import reactor
from twisted.internet.protocol import ServerFactory, connectionDone
from twisted.protocols.basic import LineOnlyReceiver


class ServerProtocol(LineOnlyReceiver):
    factory: 'Server'
    invalid_login_count:int=0
    login: str = None

    def connectionLost(self, reason=connectionDone):
        if self.login is not None:
            self.factory.clients.remove(self)

    def lineReceived(self, line: bytes):
        content = line.decode()

        if self.login is not None:
            # Команда для выхода из чата
            if content.startswith("exit:"):
                self.transport.loseConnection()
            else:
                content = f"Message from {self.login}: {content}"
                # Обновляем историю
                self.factory.history.append(content);
                self.factory.history = self.factory.history[max(0, len(self.factory.history)-10):]

                for user in self.factory.clients:
                    if user is not self:
                        user.sendMessage(content)
        else:
            # login:admin -> admin
            if content.startswith("login:"):
                login = content.replace("login:", "")
                if login is not "":
                    if self.checkLogin(login) is True:
                        self.login = login
                        self.factory.clients.append(self)
                        self.sendMessage("Welcome!")
                        self.sendHistory()
                    else:
                        self.invalidLogin("Login is already taken")
                else:
                    self.invalidLogin()
            else:
                self.invalidLogin('Please type the "login:youLogin"')

    def sendMessage(self, message: str):
        # Метод кодирующий любую строку в набор байтов и отправляющий сообщение клиенту
        if message is not "":
            self.sendLine(message.encode())

    def sendHistory(self):
        # Метод, отправляющий историю сообщений новому пользователю
        for message in self.factory.history:
            self.sendMessage(message)

    def invalidLogin(self, message:str="Invalid login"):
        # Метод, вызываемый при неудачном вводе логина
        # Отправляет уведомление пользователю, в случае 3х неудачных попыток рвет соединение
        self.invalid_login_count = self.invalid_login_count + 1;
        if (self.invalid_login_count >= 3):
            self.transport.loseConnection()
        else:
           self.sendMessage(message) 

    def checkLogin(self, login:str):
        # Метод, проверяющий уникальность логина
        for user in self.factory.clients:
            if (user.login == login):
                return False
        return True
        


class Server(ServerFactory):
    protocol = ServerProtocol
    clients: list
    history: list

    def startFactory(self):
        self.clients = []
        self.history = []
        print("Server started")

    def stopFactory(self):
        print("Server closed")


reactor.listenTCP(1234, Server())
reactor.run()
