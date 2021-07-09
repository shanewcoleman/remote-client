
import paramiko
import os
import io
import logging 

from paramiko.sftp import SFTPError
from paramiko.ssh_exception import SSHException



class RemoteClient:
    def __init__(self, **kwargs):
        self.user: str = kwargs.get('username') 
        self.host: str = kwargs.get('host')
        self.key: str = kwargs.get('key')
        self.password: str = kwargs.get('password')
        self.key_path = kwargs.get('key_path')
        self.trust = kwargs.get('trust')



    @property
    def client(self):
        try:
            client = paramiko.SSHClient()
            if self.trust is True:
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            if self.key is not None:
                client.connect(
                    self.host,
                    username=self.user,
                    password=self.password,
                    key_filename=self.key_path,
                    timeout=5000,
                    look_for_keys=False
                )
            else:
                client.connect(
                    self.host,
                    username=self.user,
                    password=self.password,
                    timeout=5000,
                    look_for_keys=False
                )
            return client
        except SSHException as e:
            logging.error(
                f"Encountered SSH error:\n {e}"
            )
            raise e
        except paramiko.AuthenticationException as e:
            logging.error(f"Encountered authentication error, check your connection settings:\n {e}")
        except Exception as e:
            logging.error(f"Unexpected error occurred:\n {e}")
            raise e
        

    @property
    def sftp(self):
        try:
            sftp = self.client.open_sftp()
            return sftp
        
        except SFTPError as e:
            logging.error(f"Unexpected SFTP error:\n {e} occurred.")
        except Exception as e:
            logging.error(f"Enountered an error: {e}")
    @property
    def _get_ssh_key(self):
        """ Fetch locally stored SSH key."""
        if self.key_path is not None:
            try:
                self.key = paramiko.RSAKey.from_private_key_file(
                    self.key_path
                )
                logging.info(
                    f"Found SSH key at self {self.key_path}"
                )
                return self.key
            except paramiko.SSHException as e:
                logging.error(e)
        else:
            logging.debug(f"Key path was not provided, skipping retrieval.")

    def list_local_files(self, dir: str) -> list:
        local_files = os.walk(dir)
        for root, dirs, files in local_files:
            return [os.path.join(root, dirs, file) for file in files]

    def list_remote_directory(self, dir: str) -> list:
        return self.sftp.listdir(dir)

    def run_cmd_list(self, command: list, environments=None):
        for c in command:
            stdin, stdout, stderr = self.client.exec_command(command, environment=environments)
            stdout.channel.recv_exit_status()
            response = stdout.readlines()
            for line in response:
                logging.debug(f"Command: {c}")
                logging.info(f"Output: {line}")

    def upload_file(self, local_file: str, remote_file: str):
        try:
            self.sftp.put(local_file, remote_file)
        except SFTPError as e:
            raise e 

    def write_to_remote_file(self, file, path: str):
        try:
            self.sftp.putfo(io.BytesIO(file, path))
        except SFTPError as e:
            logging.error(f"Encountered an issue writing to file:\n {e}")

    def open_file(self, file: str, mode: str = None, buffsize: int = None) -> object:
        if self.sftp is not None:
            try:
                with self.sftp.file(file, mode, buffsize) as f:
                    f_size = f.stat().st_size
                    f.prefetch(f_size)
                    f.set_pipelined()
                    return io.BytesIO(f.read(f_size))
            except SFTPError as e:
                logging.error(f"Encountered SFTP error: \n {e}")
            except IOError as e:
                logging.error(f"Encountered a transport error:\n {e}")
        else:
            logging.error("You need to instantiate an STFP connection first.")
    def download_file(self, file: str):
        return self.sftp.get(file)

    def disconnect(self):
        """Close SSH & SFTP connection."""
        if self.client:
            self.client.close()
        if self.sftp:
            self.sftp.close()