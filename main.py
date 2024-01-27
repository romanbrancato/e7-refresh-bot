from ldplayer.client import Client


def main():
    client = Client("1")
    print(client.get_info())


if __name__ == '__main__':
    main()
