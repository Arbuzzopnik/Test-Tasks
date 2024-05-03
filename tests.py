from io import BytesIO

import paramiko
import pytest

from database_client import DatabaseClient
from datamodels import DbConfig


class TestValidateHostname:
    """
    Test suite for validating hostname validation method.

    This test suite contains test cases related to validating hostnames with DatabaseClient class.
    """
    @pytest.mark.parametrize("hostname", ["192.168.1.1", "8.8.8.8", "www.example.com", "google.com"])
    def test_valid_hostname_success(self, hostname):
        """
        Test case to validate successful hostname validation.

        This test checks if valid hostnames pass without raising an exception.

        Args:
            hostname (str): Hostname to be validated.

            Raises:
            AssertionError: If validation fails for valid hostnames.
        """
        assert DatabaseClient.validate_hostname(
            hostname) is None, "Valid hostname should pass without raising an exception."

    @pytest.mark.parametrize("hostname", ["invalid_ip", "256.256.256.256"])
    def test_validate_hostname_exception_handling(self, hostname):
        """
        Test case to validate exception handling in hostname validation.

        This test checks if invalid hostnames raise a ValueError exception.

        Args:
            hostname (str): Invalid hostname to be validated.

            Raises:
            AssertionError: If expected ValueError exception is not raised.
        """

        # Ожидание исключения ValueError, вызываемого в блоке except
        with pytest.raises(ValueError):
            DatabaseClient.validate_hostname(hostname)


class TestSSHConnection:

    def test_ssh_connection_success(self, mocker):
        """
        Test suite for SSH connection setup method.

        This test suite contains test cases related to establishing SSH connections with DatabaseClient class.
        """
        mock_auto_add_policy = mocker.patch('paramiko.AutoAddPolicy')
        mock_ssh_client = mocker.patch('paramiko.SSHClient')

        # Создаем объект DatabaseClient для тестирования
        db_config = DbConfig(container_name='postgres', db_name='test_db', user='admin', password='pass')
        client = DatabaseClient(hostname='192.168.1.1', username='mock_user', db_config=db_config)

        # Мокируем объект paramiko.AutoAddPolicy() для возврата в тесте
        mock_auto_add_policy_instance = mock_auto_add_policy.return_value

        # Мокируем set_missing_host_key_policy и connect
        mock_ssh_instance = mock_ssh_client.return_value
        mock_ssh_instance.connect.return_value = None

        client._ssh_connection()

        # Проверяем, что методы были вызваны с правильными параметрами
        mock_auto_add_policy.assert_called_once()
        mock_ssh_instance.set_missing_host_key_policy.assert_called_once_with(mock_auto_add_policy_instance)
        mock_ssh_instance.connect.assert_called_once_with(hostname='192.168.1.1', username='mock_user')

    def test_ssh_connection_exception_handling(self, mocker):
        """
        Test case to validate exception handling in SSH connection setup.

        This test checks if SSHException during connection is properly handled and a ValueError exception is raised.

        Args:
            mocker: pytest mocker object for mocking dependencies.

        Raises:
            AssertionError: If expected ValueError exception is not raised.

        """
        mock_ssh_client = mocker.patch('paramiko.SSHClient')
        # Создаем объект DatabaseClient для тестирования
        db_config = DbConfig(container_name='postgres', db_name='test_db', user='admin', password='pass')
        client = DatabaseClient(hostname='192.168.1.1', username='mock_user', db_config=db_config)

        # Мокируем connect, чтобы выбросить исключение
        mock_ssh_instance = mock_ssh_client.return_value
        mock_ssh_instance.connect.side_effect = paramiko.SSHException("Connection failed")

        # Проверяем, что исключение перехватывается и выводится правильное сообщение
        with pytest.raises(ValueError):
            client._ssh_connection()


class TestInstallPostgres:
    """
    Test suite for PostgreSQL installation method.

    This test suite contains test cases related to installing PostgreSQL with the DatabaseClient class.
    """
    def test_install_postgres_success(self, mocker):

        """
        Test case to validate successful PostgreSQL installation.

        This test checks if the PostgreSQL installation completes successfully without errors.

        Args:
            mocker: pytest mocker object for mocking dependencies.

        Raises:
            AssertionError: If the completion message is not printed as expected.
        """
        mock_auto_add_policy = mocker.patch('paramiko.AutoAddPolicy')
        mock_ssh_client = mocker.patch('paramiko.SSHClient')

        db_config = DbConfig(container_name='postgres', db_name='test_db', user='admin', password='pass')
        client = DatabaseClient(hostname='192.168.1.1', username='mock_user', db_config=db_config)

        mock_print = mocker.patch('builtins.print')

        mock_auto_add_policy_instance = mock_auto_add_policy.return_value
        mock_ssh_instance = mock_ssh_client.return_value

        # Мокируем exec_command чтобы успешно выполнить команды
        mock_ssh_instance.exec_command.side_effect = [
            (BytesIO(), BytesIO(b'something output'), BytesIO()),
            (BytesIO(), BytesIO(b'something output'), BytesIO()),
            (BytesIO(), BytesIO(b'something output'), BytesIO()),
            (BytesIO(), BytesIO(b'something output'), BytesIO()),
        ]

        client.install_postgres()

        # Проверяем, что выводится правильное сообщение об успешном завершении
        mock_print.assert_called_with('Installation completed')

    def test_install_postgres_with_exception(self, mocker):
        """
        Test case to validate exception handling in PostgreSQL installation.

        This test checks if the installation method handles errors properly and raises a ValueError exception.

        Args:
            mocker: pytest mocker object for mocking dependencies.

        Raises:
            AssertionError: If expected ValueError exception is not raised.
        """
        mock_auto_add_policy = mocker.patch('paramiko.AutoAddPolicy')
        mock_ssh_client = mocker.patch('paramiko.SSHClient')

        db_config = DbConfig(container_name='postgres', db_name='test_db', user='admin', password='pass')
        client = DatabaseClient(hostname='192.168.1.1', username='mock_user', db_config=db_config)

        mock_auto_add_policy_instance = mock_auto_add_policy.return_value
        mock_ssh_instance = mock_ssh_client.return_value

        # Мокируем exec_command чтобы успешно выполнить команды
        mock_ssh_instance.exec_command.side_effect = (BytesIO(), BytesIO(), BytesIO(b'error'))

        with pytest.raises(ValueError):
            client.install_postgres()


class TestRequestToDB:
    """
    Test suite for the request_to_db method in DatabaseClient class.

    This test suite contains test cases related to querying the database using the request_to_db method.

    """

    def test_request_to_db_success(self, mocker):
        """
        Test case to validate successful database query execution.

        This test checks if the database query is executed successfully and the result is returned without any errors.

        Args:
            mocker: pytest mocker object for mocking dependencies.

        Raises:
            AssertionError: If the database query result is not returned as expected.

        """

        # Mocking necessary dependencies
        mock_ssh_client = mocker.patch('paramiko.SSHClient')
        client = DatabaseClient(hostname='192.168.1.1', username='mock_user',
                                db_config=DbConfig(container_name='postgres', db_name='test_db', user='admin',
                                                   password='pass'))

        mock_ssh_instance = mock_ssh_client.return_value

        # Mocking exec_command to simulate successful query execution
        mock_ssh_instance.exec_command.return_value = (BytesIO(), BytesIO(b'query_output'), BytesIO())

        client.request_to_db("SELECT * FROM table")

        # Check if exec_command was called with the correct command
        mock_ssh_instance.exec_command.assert_called_once_with("docker exec postgres psql -U admin -d test_db -c 'SELECT * FROM table'")

    def test_request_to_db_exception_handling(self, mocker):
        """
        Test case to validate exception handling in database query execution.

        This test checks if exceptions during database query execution are properly handled and a ValueError is raised.

        Args:
            mocker: pytest mocker object for mocking dependencies.

        Raises:
            AssertionError: If expected ValueError exception is not raised.

        """

        # Mocking necessary dependencies
        mock_ssh_client = mocker.patch('paramiko.SSHClient')
        client = DatabaseClient(hostname='192.168.1.1', username='mock_user',
                                db_config=DbConfig(container_name='postgres', db_name='test_db', user='admin',
                                                   password='pass'))

        mock_ssh_instance = mock_ssh_client.return_value

        # Mocking exec_command to raise an exception
        mock_ssh_instance.exec_command.side_effect = OSError("Connection error")

        with pytest.raises(ValueError):
            client.request_to_db("SELECT * FROM table")
