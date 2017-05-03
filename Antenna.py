import paramiko
from datetime import datetime
import time
import os

class RecAntenna():
    def __init__(self, ip):
        """ Lets make a class for collecting those reception signals. First, we'll make a data member
         that will operate the ssh communication after the user passes us an IP address"""
        self.ssh = paramiko.SSHClient()
        self.ip = ip

    def connect(self):
        "Connect the device to the IP address"
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # ↑ this is required because our host name is an unknown host
        # ↑ we need to tell our ssh to automatically add unknown hosts

        self.ssh.connect(hostname = self.ip, port = 22, username = "ubnt", password = "ubnt")
        # Pretty intuitive
        # ssh.connect(hostname="192.168.1.2", port = 22, username="ubnt", password="ubnt")

    def scrape(self):
        ssh_stdin, ssh_stdout, ssh_stderr = self.ssh.exec_command('cd "bin"')
        ssh_stdin, ssh_stdout, ssh_stderr = self.ssh.exec_command('ubntbox mca-status')
        # to obtain our information, we need to move to the "bin" folder where the
        # majority of data is stored. Then execute the mca-status command to
        # obtain all of the antennas information including frequency, signal strength
        # and GPS location

        data = (ssh_stdout.read())
        list_data = (data.decode().split('\r\n'))       # split the string by the new lines
        del ssh_stdin, ssh_stdout, ssh_stderr           # attempt to clean up after ourselves here ... but this is Python so ...

        index = 0
        data = {}                                       # we want all of our data accessible via dictionary
        for each in list_data:
            if list_data[index] == '':                  # delete empty entries
                del list_data[index]
            else:
                x = list_data[index].split("=")         # our keys and values are separated by an equal sign
                data[x[0]] = x[1]                       # store them in our dictionary!
            index += 1
        del index

        return ''.join((str(datetime.now().strftime('%Y-%m-%d %H:%M:%S ')),
                        "Signal: ", data["signal"],
                        "dBm  Noise: ", data["noise"], "dBm "))

    def close(self):
        self.ssh.close()

def main():
    x = RecAntenna("192.168.11.1")
    x.connect()
    data = ""
    while 1:
        file = open('C:/Users/Dylan/Documents/UAVRT/Final Design Test/AntData_2.txt', 'a')
        file.write(''.join((x.scrape(), '\n')))
        time.sleep(0.25)
        file.close()
    x.close()
main()

# Helpful links:
#   https://community.ubnt.com/t5/NanoStation-and-Loco-Devices/Telnet-commands/td-p/156247
#   https://www.siteground.com/tutorials/ssh/ssh_searching.htm
#   http://www.inmotionhosting.com/support/website/ssh/navigate-command-line
#   http://www.webhostingtalk.com/showthread.php?t=344497