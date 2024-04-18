import pytest
from main import ssh_connect, connect, request


# Фикстура для передачи IP-адресов
@pytest.fixture
def ip_addresses():
    ip_addr = "192.168.56.103"
    wrong_ip_addr = "192.168.100.100"
    return ip_addr, wrong_ip_addr


# Тесты для функции ssh_connect()
def test_ssh_connect_successful(ip_addresses):
    ip_addr, _ = ip_addresses
    # Проверка успешного подключения к известному хосту
    client = ssh_connect(ip_addr, "admin")
    assert client is not None


def test_ssh_connect_failed(ip_addresses):
    _, wrong_ip_addr = ip_addresses
    # Проверка обработки ошибки при подключении к недоступному хосту
    client = ssh_connect("wrong_ip_addr", "admin")
    assert client is None


# Тесты для функции connect()
def test_connect_successful(ip_addresses):
    ip_addr, _ = ip_addresses
    commands = {"Test Command": "echo 'Hello, World!'",
                "Docker Test Command": "docker ps -a"}  # Пример команд для успешного выполнения
    result = connect(ip_addr, "admin", commands)
    assert result is True


def test_connect_failed(ip_addresses):
    ip_addr, _ = ip_addresses
    commands = {"Invalid Command": "invalid_command"}  # Пример команды для неуспешного выполнения
    result = connect(ip_addr, "admin", commands)
    assert result is False


# Тесты для функции request()
def test_request_successful(ip_addresses):
    ip_addr, _ = ip_addresses
    db_config = {'container_name': 'postgres_test', 'db_name': 'postgres_test_db', 'user': 'admin', 'password': 'pass'}
    request_text = "SELECT 1;"
    result = request(ip_addr, "admin", db_config, request_text)
    assert result == " ?column? \n----------\n        1\n(1 row)\n\n"



    def test_request_failed(ip_addresses):
        ip_addr,_ = ip_addresses
    db_config = {'container_name': 'test_container', 'db_name': 'test_db', 'user': 'test_user', 'password': 'test_pass'}
    request_text = "INVALID SQL"
    request(ip_addr, "admin", db_config, request_text)
