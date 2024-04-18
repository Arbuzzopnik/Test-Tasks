import time

import paramiko
from tqdm import tqdm


def ssh_connect(ip_addr: str, username: str):
    """
    Устанавливает SSH-соединение с удаленным хостом.

    :param ip_addr: IP-адрес удаленного хоста, к которому требуется подключиться. (str)
    :param username: Имя пользователя для аутентификации при подключении. (str)
    :return: Клиентское соединение SSH (paramiko.SSHClient) в случае успешного подключения;
             None в случае возникновения ошибки.
    """
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(hostname=ip_addr, username=username)
    except (paramiko.SSHException, OSError) as e:
        print(f"Error connecting to {ip_addr} as {username}:\n{e}")
        return None
    return client


def connect(ip_addr: str, username: str, commands: dict) -> bool:
    """
    Устанавливает SSH-соединение с указанным IP-адресом и именем пользователя, а затем выполняет список команд на удаленном хосте.

    :param ip_addr: IP-адрес удаленного хоста, к которому требуется подключиться. (str)
    :param username: Имя пользователя для аутентификации при подключении. (str)
    :param commands: Словарь команд, которые необходимо выполнить на удаленном хосте. Ключи словаря представляют собой описания команд, а значения - сами команды. (dict)
    :return:True, если все команды были успешно выполнены без ошибок;
            False, если произошла хотя бы одна ошибка при выполнении команд. (bool)
    """

    client = ssh_connect(ip_addr, username)
    if client is None:
        print(f"Проверьте возможность соединения с {ip_addr}")
        return False

    try:
        for key, value in tqdm(commands.items(), colour=False):
            stdin, stdout, stderr = client.exec_command(value)

            tqdm.write(f"{key}", end='')

            error = stderr.read().decode('utf-8')

            if error:
                tqdm.write("\033[91m\u2717\033[0m")  # Красный крестик
                print(f"\nError occurred while running command '{value}': {error}")
                return False

            tqdm.write("\033[92m\u2713\033[0m")  # Зеленая галочка

        return True
    except Exception as e:
        print(f"An error occurred during execution: {e}")
        return False
    finally:
        client.close()


def request(ip_addr: str, username: str, db_config: dict, request_text: str) -> None:
    """
    Устанавливает SSH-соединение с удаленным хостом и выполняет запрос к базе данных.

    :param ip_addr: IP-адрес удаленного хоста, к которому требуется подключиться. (str)
    :param username: Имя пользователя для аутентификации при подключении. (str)
    :param db_config: Конфигурация базы данных, содержащая информацию о контейнере, пользователе и БД. (dict)
    :param request_text: Текст запроса к базе данных PostgreSQL. (str)

    :return: None

    """
    client = ssh_connect(ip_addr, username)
    if client is None:
        print(f"Проверьте возможность соединения с {ip_addr}")
        return None

    try:
        stdin, stdout, stderr = client.exec_command(
           f"docker exec {db_config['container_name']} psql -U {db_config['user']} -d {db_config['db_name']} -c '{request_text}'")
        error = stderr.read().decode('utf-8')
        output = stdout.read().decode('utf-8')
        if error:
            return error
        return output

    except Exception as e:
        print(f"An error occurred during execution: {e}")
        return None
    finally:
        client.close()



def main():
    """
    Главная функция, которая управляет установкой PostgreSQL и выполнением тестового запроса.

    :return: None
    """
    # Параметры для подключения к удаленному серверу
    ip_addr = "192.168.56.103"
    username = "admin"

    # Текст тестового SQL-запроса
    request_text = "SELECT 1;"

    # Конфигурация базы данных PostgreSQL
    db_config = {'container_name': 'postgres_test',
                 'db_name': 'postgres_test_db',
                 'user': 'admin',
                 'password': 'pass',
                 }

    # Команды для установки и настройки PostgreSQL
    commands = {
        'Создание директории для монтирования': 'mkdir -p $HOME/docker/volumes/postgres',
        'Загрузка образа PostgreSQL из Docker Hub': "docker pull postgres",
        'Запуск контейнера PostgreSQL': f"docker run -d --restart unless-stopped --name {db_config['container_name']} -e "
                                       f"POSTGRES_PASSWORD={db_config['password']} -e "
                                       f"POSTGRES_USER={db_config['user']} -e POSTGRES_DB={db_config['db_name']} -d -p 5432:5432 -v "
                                       "$HOME/docker/volumes/postgres:/var/lib/postgresql/data postgres",
    }

    # Команды для удаления контейнера и образа PostgreSQL
    commands_to_dell = {
        '1': f'docker stop {db_config["container_name"]}',
        '2': f'docker rm {db_config["container_name"]}',
        '3': f'docker rmi postgres',
        '4': f'rm -r $HOME/docker/volumes/postgres',
    }

    # Попытка установки PostgreSQL
    installation_status = connect(ip_addr=ip_addr, username=username, commands=commands)

    time.sleep(1)

    # Проверка успешности установки и выполнение тестового запроса
    if installation_status:
        print(f"Установка завершена, тестовый запрос {request_text}:")
        print(request(ip_addr=ip_addr, username=username, db_config=db_config, request_text=request_text))
    else:
        print("Не удалось установить PostgreSQL")


if __name__ == '__main__':
    ip_addr = "192.168.56.103"
    username = "admin"

    # Текст тестового SQL-запроса
    request_text = 'SELECT 1;'

    # Конфигурация базы данных PostgreSQL
    db_config = {'container_name': 'postgres_test',
                 'db_name': 'postgres_test_db',
                 'user': 'admin',
                 'password': 'pass',
                 }
    #request(ip_addr=ip_addr, username=username, db_config=db_config, request_text=request_text)
    main()

