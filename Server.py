import socket
import os
from datetime import datetime
import _thread

PORT = 3777
FORMAT = 'utf-8'
SIZE = 1024

INFO_FILE = 'Server/info.txt'

def send_data_to_receiver(data,s):
    s.send(data.encode(FORMAT))

def get_path(email_addr):
    try:
        name = email_addr.split('@')[0]
        server = email_addr.split('@')[1]
        path = os.getcwd() + '/' + 'Server' + '/' + name
    except:
        return ''
    return path

def check_for_email(email_addr):
    return os.path.isdir(get_path(email_addr))

def generate_text(command):
    text = '<subject> ' + command[1] + '</subject>\n' +\
        '<email_from> ' + command[2] + ' </email_from>\n' +\
        '<email_to> ' + command[3] + ' </email_to>\n' +\
        '<email_data>\n' + command[4] + '\n</email_data>'
    return text

def write_to_file(data,path):
    f = open(path, "w+")
    f.write(data)
    f.close()

def check_credentials(username,password):
    try:
        f = open(INFO_FILE,'r')
        lines = f.read().splitlines()
        for line in lines:
            if line.split('|')[0] == username and line.split('|')[1] == password:
                return True
        f.close()
    except:
        return False

def get_username_from_email(email_addr):
    return email_addr.split('@')[0]

def extract_data_from_email(data):
    return data.split('<email_data>')[1].split('</email_data>')[0][1:-1]

def extract_header_from_email(data):
    return data.split('<email_data>')[0][:-1]

def get_data_from_subject(username, subject, partial = 'False'):
    data = ''
    for dirpath, dirnames, filenames in os.walk("Server/" + username):
        for filename in filenames:
            if filename.startswith(subject):
                path = os.path.join(dirpath, filename)
                f = open(path,'r')
                lines = f.read()
                f.close()
                if partial == 'True':
                    data = extract_header_from_email(lines)
                    return data
                else:
                    return lines
    return ''

def get_all_mail_for_user(username):
    data = []
    try:
        for dirpath, dirnames, filenames in os.walk("Server/" + username):
            for filename in filenames:
                if filename.endswith('.txt'):
                    path = os.path.join(dirpath, filename)
                    f = open(path,'r')
                    lines = f.read()
                    f.close()
                    data.append(lines)
        data = '|'.join(data)
        return data
    except:
        return ''

def delete_email_by_subject(username, subject):
    try:
        for dirpath, dirnames, filenames in os.walk("Server/" + username):
            for filename in filenames:
                if filename.startswith(subject):
                    path = os.path.join(dirpath, filename)
                    os.remove(path)
                    return True
    except:
        return False

def search_mail(username,word):
    try:
        for dirpath, dirnames, filenames in os.walk("Server/" + username):
            for filename in filenames:
                if filename.endswith('.txt'):
                    path = os.path.join(dirpath, filename)
                    f = open(path,'r')
                    lines = f.read()
                    if word in lines:
                        f.close()
                        return lines
                    f.close()
        return ''
    except:
        return ''

def new_client(csocket,address):
    command = csocket.recv(SIZE).decode(FORMAT).split('|')
    
    try:
        if command[0] == 'handshake':
            send_data_to_receiver("Please enter credentials to continue ( Username | Password )", csocket)
        elif command[0] == 'auth':
            try:
                if check_credentials(command[1].strip(),command[2].strip()):
                    send_data_to_receiver("True|Authentication successful, welcome " + command[1].strip(), csocket)
                else:
                    send_data_to_receiver("False|User not found", csocket)
            except :
                send_data_to_receiver("False|Error, incorrect format", csocket)
        elif command[0] == 'read':
            data = get_data_from_subject(command[1],command[2],command[3])
            if data != '':
                send_data_to_receiver("True|" + data,csocket)
            else:
                send_data_to_receiver("False|Error, Mail not found", csocket)
        elif command[0] == 'get_all':
            send_data_to_receiver(get_all_mail_for_user(command[1]),csocket)
        elif command[0] == 'delete':
            if delete_email_by_subject(command[1],command[2]):
                send_data_to_receiver("True|Email deleted successful",csocket)
            else:
                send_data_to_receiver("False|Error, mail not found or could not be deleted", csocket)
        elif command[0] == 'forward':
            data = get_data_from_subject(get_username_from_email(command[2]),command[1])
            new_data = extract_data_from_email(data)
            dest_path = get_path(command[3]) + '/inbox/' +\
                command[1] + '.txt'
            command.append(new_data)
            write_to_file(generate_text(command), dest_path)
            send_data_to_receiver('Email forwarded.',csocket)
        elif command[0] == 'check':
            if check_for_email(command[1]):
                send_data_to_receiver("True|Receiver address valid",csocket)
            else:
                send_data_to_receiver("False|Error, receiver not found",csocket)
        elif command[0] == 'compose':
            dest_path = get_path(command[3]) + '/inbox/' +\
                command[1] + '.txt'
            write_to_file(generate_text(command), dest_path)
            send_data_to_receiver('Email sent.',csocket)
        elif command[0] == 'search':
            data = search_mail(command[1],command[2])
            if data != '':
                send_data_to_receiver("True|" + data,csocket)
            else:
                send_data_to_receiver("False|Error, no mail found containing the word", csocket) 
        elif command[0] == 'logout':
            send_data_to_receiver("You have logged out of the IMAP system", csocket)
    except:
        send_data_to_receiver("False|Something went wrong", csocket)
    csocket.close()

if __name__ == '__main__':
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversocket.bind(("127.0.0.1", PORT))
    serversocket.listen(5)
    print("server running")
    while True:
        csocket, address = serversocket.accept()
        _thread.start_new_thread(new_client,(csocket,address))

    serversocket.close()

