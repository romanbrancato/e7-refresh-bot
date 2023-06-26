from client import Client
from bot import Bot


def main():
    client = Client("1")
    client.setup()
    bot = Bot(10761805, 6475, 0, 0, 5, 50, client)
    bot.handle_refresh()


if __name__ == '__main__':
    main()
