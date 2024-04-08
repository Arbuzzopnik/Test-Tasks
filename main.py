import socket
import time

import paramiko


def main():
    pass


def connect(ip_addr: str, username: str, commands: tuple):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname=ip_addr,
        username=username,
    )
    with client.invoke_shell() as ssh:
        result = {}
        for command in commands:
            ssh.send(f"{command}\n")
            ssh.settimeout(5)
            output = ""
            while True:
                try:
                    part = ssh.recv(60000).decode("utf-8")
                    output += part
                    time.sleep(0.5)
                except socket.timeout:
                    break
                result[command] = output
        return result



if __name__ == '__main__':
    commands = ("pwd", "ls")
    result = connect(ip_addr="192.168.56.102", username="arbuzzopnik", password="A052000", commands=commands)
    print(result["pwd"])
