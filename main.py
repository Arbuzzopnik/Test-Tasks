import paramiko


def connect(ip_addr: str, username: str, commands: tuple):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=ip_addr, username=username)

    result = {}
    for command in commands:
        stdin, stdout, stderr = client.exec_command(command)
        output = stdout.read().decode('utf-8')
        # print(output)
        result[command] = output
        error = stderr.read().decode('utf-8')

        if error:
            print(f"Error occurred while running command '{command}': {error}")
            result[command] = error
        else:
            #print(output)
            result[command] = output

    client.close()
    return result


if __name__ == '__main__':
    commands = ("mkdir -p $HOME/docker/volumes/postgres",
                "docker pull postgres",
                "docker run -d --restart unless-stopped --name postgres_test -e POSTGRES_PASSWORD=pass -e "
                "POSTGRES_USER=admin -e POSTGRES_DB=postgres_test_db -d -p 5432:5432 -v "
                "$HOME/docker/volumes/postgres:/var/lib/postgresql/data postgres",
                "docker exec postgres_test psql -U admin -d postgres_test_db -c 'SELECT 1;'"
                )
    commands_to_dell = ('docker stop postgres_test',
                        'docker rm postgres_test',
                        'docker rmi postgres',
                        'rm - rf $HOME/docker/volumes/postgres',
                        )
    commands_2 = ("docker exec postgres_test psql -U admin -d postgres_test_db -c 'SELECT 1;'",)
    commands_3 = ("pwd", "ls",)

    result = connect(ip_addr="192.168.56.103", username="admin", commands=commands)
    for key, value in result.items():
        print(f'{key}: {value}')
    result = connect(ip_addr="192.168.56.103", username="admin", commands=commands_2)
    for key, value in result.items():
        print(f'{key}: {value}')