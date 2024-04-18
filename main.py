import paramiko
from tqdm import tqdm


def ssh_connect(ip_addr: str, username: str):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=ip_addr, username=username)
    return client


def connect(ip_addr: str, username: str, commands: dict):
    client = ssh_connect(ip_addr, username)
    for key, value in tqdm(commands.items(), colour=False):
        stdin, stdout, stderr = client.exec_command(value)

        tqdm.write(f"{key}", end='')

        error = stderr.read().decode('utf-8')

        if error:
            tqdm.write("\033[91m\u2717\033[0m")  # Красный крестик
            print(f"\nError occurred while running command '{value}': {error}")
            break
        else:
            tqdm.write("\033[92m\u2713\033[0m")  # Зеленая галочка
    client.close()


def request(ip_addr: str, username: str, db_config: dict, request_text: str):
    client = ssh_connect(ip_addr, username)
    stdin, stdout, stderr = client.exec_command(
        f"docker exec {db_config['container_name']} psql -U {db_config['user']} -d {db_config['db_name']} -c '{request_text}'")

    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')

    if error:
        print(error)
    else:
        print(output)
    client.close()


def main():
    ip_addr = "192.168.56.103"
    username = "admin"
    request_text = "SELECT 1;"
    db_config = {'container_name': 'postgres_test',
                 'db_name': 'postgres_test_db',
                 'user': 'admin',
                 'password': 'pass',
                 }

    commands = {'Создание директории для монтирования': 'mkdir -p $HOME/docker/volumes/postgres',
                'Загрузка образа PostgreSQL из Docker Hub': "docker pull postgres",
                'Запуск контейнер PostgreSQL': f"docker run -d --restart unless-stopped --name {db_config['container_name']} -e " 
                                               f"POSTGRES_PASSWORD={db_config['password']} -e "
                                               f"POSTGRES_USER={db_config['username']} -e POSTGRES_DB={db_config['db_name']} -d -p 5432:5432 -v "
                                               "$HOME/docker/volumes/postgres:/var/lib/postgresql/data postgres",
                }
    commands_to_dell = {'1': f'docker stop {db_config["container_name"]}',
                        '2': f'docker rm {db_config["container_name"]}',
                        '3': f'docker rmi postgres',
                        '4': f'rm - r $HOME/docker/volumes/postgres',
                        }

    connect(ip_addr=ip_addr, username=username, commands=commands)
    request(ip_addr=ip_addr, username=username, db_config=db_config, request_text=request_text)


if __name__ == '__main__':
    main()
