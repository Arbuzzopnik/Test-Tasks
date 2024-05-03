import sys
from ipaddress import IPv4Address
from socket import gethostbyname
from time import sleep

import paramiko
from colorama import Fore, init
from tqdm import tqdm

from datamodels import DbConfig


class DatabaseClient:
    """
    The DatabaseClient class is designed to automate the process of setting up and configuring a PostgreSQL
    database within a Docker container on a remote host. It provides functionalities to validate hostnames,
    establish SSH connections, install and configure PostgreSQL, and execute queries against the database.
    """

    @staticmethod
    def validate_hostname(hostname: str):
        """
        This method is сhecks the validity of the IP address or DNS name

        :param hostname:IP address of the remote host.
        :type hostname: str

        :return: None
        """
        try:
            IPv4Address(hostname)
        except Exception:
            try:
                IPv4Address(gethostbyname(hostname))
            except Exception as e:
                print(f"Error: {e}. Invalid IP address or host.")
                raise ValueError("Invalid hostname") from None

    def __init__(self, hostname: str, username: str, db_config: DbConfig):
        """
        This method is initializes an instance of the DatabaseClient class.

        :param hostname: IP address or domain name of the remote host .
        :type hostname: str
        :param username: Username to connect to the remote host.
        :type username: str
        :param db_config: Database configuration including container name, database name, username and password.
        :type db_config: DbConfig
        """
        self.validate_hostname(hostname)
        self.hostname = hostname
        self.username = username
        self.db_config = db_config
        self.client = paramiko.SSHClient()

    def _ssh_connection(self) -> None:
        """
        This method is establishes an SSH connection with a remote host.

        :return: None.
        """

        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.client.connect(hostname=self.hostname, username=self.username)
        except (paramiko.SSHException, OSError) as e:
            raise ValueError("Error connecting to {self.hostname} as {self.username}:\n{e}")

    def install_postgres(self) -> None:
        """
        This method is designed to automate the process of setting up and configuring a PostgreSQL database within a
        Docker container. It initializes the necessary directories, pulls the PostgreSQL image from Docker Hub,
        runs the container with specified configurations, and sets up the database to accept connections from any IP
        address.


        :return:None.
        """

        # Initializing the colorama
        init(autoreset=True)

        # Commands for installing and configuring PostgreSQL
        cmds = {
            'Creating a mount directory': 'docker volume create pg_data_volume',
            'Downloading a PostgreSQL image from Docker Hub': "docker pull postgres",
            'Running a PostgreSQL container': f"docker run -d --name {self.db_config.container_name} -e POSTGRES_PASSWORD={self.db_config.password} -e POSTGRES_USER={self.db_config.user} -e POSTGRES_DB={self.db_config.db_name} -d -p 5432:5432 -v pg_data_volume:/var/lib/postgresql/data postgres",
            'Allowing incoming connections to the database': f"docker exec  {self.db_config.container_name} bash -c 'echo \"host all "
                                                             f"all 0.0.0.0/0 "
                                                             "md5\" >> /var/lib/postgresql/data/pg_hba.conf'",

        }

        self._ssh_connection()
        try:
            for key, value in tqdm(cmds.items(), colour=False):
                stdin, stdout, stderr = self.client.exec_command(value)
                print(value)
                tqdm.write(f"{key}... ", end='')

                error = stderr.read().decode('utf-8')

                if error:
                    tqdm.write(Fore.RED + 'Error')
                    raise ValueError(f"Error occurred while running command '{value}': {error}")
                else:
                    tqdm.write(Fore.GREEN + 'Done')
                sleep(1)
            print('Installation completed')
        except Exception as e:
            raise ValueError(f"An error occurred during execution: {e}")
        finally:
            self.client.close()

    def request_to_db(self, query_text: str) -> None:
        """
        This method is establishes an SSH connection to a remote host, queries the database, print results and close connection.

        :param query_text: PostgreSQL database query text.
        :type query_text: str

        :return: Database query result

        """
        self._ssh_connection()
        try:
            stdin, stdout, stderr = self.client.exec_command(
                f"docker exec {self.db_config.container_name} psql -U {self.db_config.user} -d {self.db_config.db_name} -c '{query_text}'")
            error = stderr.read().decode('utf-8')
            output = stdout.read().decode('utf-8')
            print(error or output)
        except Exception as e:
            raise ValueError(f"An error occurred during execution: {e}")
        finally:
            self.client.close()


if __name__ == '__main__':
    # Parameters for connecting to a remote host
    hostname = sys.argv[1]
    username = "arbuzzopnik"

    # PostgreSQL database configuration
    db_config = DbConfig(container_name='postgres',
                         db_name='some_db',
                         user='postgres',
                         password='pass')

    # Attempt to install PostgreSQL
    client = DatabaseClient(hostname=hostname, username=username, db_config=db_config)
    client.install_postgres()

    # Running a test request
    query_text = "SELECT 1;"
    client.request_to_db(query_text=query_text)
