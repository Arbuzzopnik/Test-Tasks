from time import sleep

import socket
import ipaddress

import paramiko
from tqdm import tqdm

from datamodels import DbConfig


def validate_ip(ip_addr: str) -> str:
    """
    Checks the validity of the IP address or DNS name

    :param ip_addr:IP address of the remote host. (str)
    :return: IP address of the remote host . (str)
    """
    try:
        ip = ipaddress.IPv4Address(ip_addr)
        return str(ip)
    except ValueError:
        try:
            ip = ipaddress.IPv4Address(socket.gethostbyname(ip_addr))
        except Exception as e:
            print(f"Error: {e}. Invalid IP address or host.")
        return str(ip)


class Client():
    def __init__(self, ip_addr: str, username: str):
        """
        :param ip_addr: Remote host IP address
        :param username: Remote host username
        """
        self.ip_addr = ip_addr
        self.username = username
        self.client = paramiko.SSHClient()

    def get_ssh_connection(self) -> None:
        """
        Establishes an SSH connection with a remote host.

        :return: None.
        """

        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.client.connect(hostname=self.ip_addr, username=self.username)
        except (paramiko.SSHException, OSError) as e:
            print(f"Error connecting to {self.ip_addr} as {self.username}:\n{e}")

    def send_commands(self, cmds: dict) -> None:
        """
        Establishes an SSH connection to the specified IP address and username, and then executes a list of commands
        on the remote host and close connection.

        :param cmds: A dictionary of commands that need to be executed on the remote host. The dictionary keys are
        descriptions of the commands, and the values are the commands themselves. (dict)

        :return:None.
        """
        self.get_ssh_connection()
        try:
            for key, value in tqdm(cmds.items(), colour=False):
                stdin, stdout, stderr = self.client.exec_command(value)

                tqdm.write(f"{key}", end='')

                error = stderr.read().decode('utf-8')

                if error:
                    tqdm.write("\033[91m\u2717\033[0m")  # Красный крестик
                    print(f"\nError occurred while running command '{value}': {error}")

                tqdm.write("\033[92m\u2713\033[0m")  # Зеленая галочка
        except Exception as e:
            print(f"An error occurred during execution: {e}")
        finally:
            self.client.close()

    def request_to_db(self, db_config: DbConfig, query_text: str) -> None:
        """
        Establishes an SSH connection to a remote host, queries the database, print results and close connection.

        :param db_config: Database configuration containing information about the container, user and database. (dict)
        :param query_text: PostgreSQL database query text. (str)

        :return: None

        """
        self.get_ssh_connection()
        try:
            stdin, stdout, stderr = self.client.exec_command(
                f"docker exec {db_config.container_name} psql -U {db_config.user} -d {db_config.db_name} -c '{query_text}'")
            error = stderr.read().decode('utf-8')
            output = stdout.read().decode('utf-8')
            print(error or output)
        except Exception as e:
            print(f"An error occurred during execution: {e}")
        finally:
            self.client.close()


if __name__ == '__main__':
    # Parameters for connecting to a remote host
    ip_addr = "192.168.56.103"
    ip_addr = validate_ip(ip_addr)
    username = "admin"

    # Test SQL query text
    query_text = "SELECT 1;"

    # PostgreSQL database configuration

    db_config = DbConfig(container_name='postgres_test',
                         db_name='postgres_test_db',
                         user='admin',
                         password='pass')

    # Commands for installing and configuring PostgreSQL
    cmds = {
        'Создание директории для монтирования': 'mkdir -p $HOME/docker/volumes/postgres',
        'Загрузка образа PostgreSQL из Docker Hub': "docker pull postgres",
        'Запуск контейнера PostgreSQL': f"docker run -d --restart unless-stopped --name {db_config.container_name} -e "
                                        f"POSTGRES_PASSWORD={db_config.password} -e "
                                        f"POSTGRES_USER={db_config.user} -e POSTGRES_DB={db_config.db_name} -d -p 5432:5432 -v "
                                        "$HOME/docker/volumes/postgres:/var/lib/postgresql/data postgres",
    }

    # Commands for deleting a PostgreSQL container and image
    commands_to_dell = {
        '1': f'docker stop {db_config.container_name}',
        '2': f'docker rm {db_config.container_name}',
        '3': f'docker rmi postgres',
        '4': f'rm -r $HOME/docker/volumes/postgres',
    }

    # Attempt to install PostgreSQL
    client = Client(ip_addr=ip_addr, username=username)
    client.send_commands(cmds=cmds)

    sleep(1)

    # Running a test request
    client.request_to_db(db_config=db_config, query_text=query_text)
