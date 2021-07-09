# remote-client
Remote SSH/SFTP Client Python Library

Largely borrowed from: https://github.com/hackersandslackers/paramiko-tutorial

Quite a few changes have been made to faciliate internal tooling for my team. 

Due to the nature of our work, remote host keys constantly change, so there is an option for trust=True to set the connection policy to auto-add. 