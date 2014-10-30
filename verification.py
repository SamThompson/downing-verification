from concurrent import futures
import datetime 
from email.mime.text import MIMEText
import csv
import smtplib
from optparse import OptionParser
import os
from Queue import Queue
from threading import Thread


def eliminate_duplicates(csv_file, eid_index, time_index):
    student_dict = {}
    for csv_line in csv:
        eid = csv_line[eid_index]
        dt = csv_line[time_index]
        date, time = dt.split()
        mon, day, year = [int(i) for i in date.split('/')]
        hour, minute, second = [int(i) for i in time.split(':')]
        sub_time = datetime.datetime(year, mon, day, hour, minute, second)

        if eid not in student_dict:
            student_dict[eid] = {}
            student_dict[eid]['csv_line'] = csv_line
            student_dict[eid]['datetime'] = sub_time
        else:
            if student_dict[eid]['datetime'] < sub_time:
                student_dict[eid]['csv_line'] = csv_line
                student_dict[eid]['datetime'] = sub_time

    student_csvs = []
    for eid in student_dict:
        student_csvs.append(student_dict[eid]['csv_line'])

    return student_csvs


def pull(csvLine, uteid_index, url_index, sha_index):
    os.system('mkdir ' + csvLine[uteid_index] + ';' +
            'cd ' + csvLine[uteid_index] + ';' + 
            'git init;' +
            'git remote add origin ' + csvLine[url_index] + ';' +
            'git pull;' +
            'git checkout ' + csvLine[sha_index] + ';')
    return csvLine


def check(files, direct):
    res = []
    for f in files:
        if not os.path.exists(direct + '/' + f):
            res.append(f + ' does not exist')
    return res


def email(email, password, smtpServer, to, cc, subject, eid, msg):
    message = "From: " + email + "\nTo: " + to + "\nCC: "
    for i in range(len(cc)-1):
        message += cc[i] + ','
    message += cc[len(cc)-1] + \
        '\nSubject:' + '[CS371p] ' + subject + '\n\n'
    message += 'This is an automated message, please contact the graders if you have questions.\n\n'
    message += 'EID: ' + eid + '\n'
    for m in msg:
        message += m + '\n'
    message += '\nPlease push these files to your repo and notify the graders ASAP.\n\nCS371p Graders'

    smtp = smtplib.SMTP(smtpServer)
    smtp.starttls()
    smtp.login(email, password)
    smtp.sendmail(email, [to] + [cc], message)
    smtp.quit()


class SenderThread(Thread):

    END = '___________END WORK EVENT'

    def __init__(self, source, outq, func):
        super(SenderThread, self).__init__()
        self.source = source
        self.outq = outq
        self.func = func

    def run(self):
        for s in source:
            out_val =  self.func(s)
            self.outq.put(out_val)
        self.outq.put(SenderThread.END)

class SenderReceiverThread(Thread):

    def __init__(self, inq, outq, func):
        super(SenderReceiverThread, self).__init__()
        self.inq = inq
        self.outq = outq
        self.func = func

    def run(self):
        run = True
        while run:
            in_val = self.inq.get()
            if in_val == SenderThread.END:
                run = False
                self.outq.put(in_val)
            else:
                out_val = self.func(in_val)
                self.outq.put(out_val)
            in_val.task_done()

if __name__=='__main__':

    csvq = Queue()
    dirq = Queue()
    probq = Queue()
    outputq = Queue()

    parser = OptionParser()
    parser.add_option('-f', dest='csv_file', help='csv file to be read')
    parser.add_option('-u', dest='user', help='email address')
    parser.add_option('-p', dest='passw', help='email password')
    parser.add_option('--smtp', dest='smtp', help='smtp server')
    parser.add_option('--cc', dest='cc', help='email cc\'s')
    parser.add_option('--files', dest='files', help='required files')
    parser.add_option('--csv_time', dest='csv_time', help='csv time column index')
    parser.add_option('--csv_eid', dest='csv_eid', help='csv eid column index')
    parser.add_option('--csv_email', dest='csv_email', help='csv email column index')
    parser.add_option('--csv_url', dest='csv_url', help='csv url column index')
    parser.add_option('--csv_sha', dest='csv_sha', help='csv sha column index')
    (option, args) = parser.parse_args()

    csv_file_name = option.csv_file
    email_addr = option.user
    password = option.passw
    smtp = option.smtp
    subject = 'Missing files'
    cc = option.cc.split(',')
    files = option.files.split(',')
    csv_time = int(option.csv_time)
    csv_eid = int(option.csv_eid)
    csv_email = int(option.csv_email)
    csv_url = int(option.csv_url)
    csv_sha = int(option.csv_sha)

    print 'option list:', parser.option_list

    print 'Csv file:', csv_file_name
    print 'Email sending:', email_addr
    print 'CC\'d:', cc
    print 'Smtp server:', smtp
    print 'Required files:', files
    print 'Index of time:', csv_time
    print 'Index of eid:', csv_eid
    print 'Index of email:', csv_email
    print 'Index of project url:', csv_url
    print 'Index of sha:', csv_sha


    # read in all of the lines of the csv
    clean_csv = []
    with open(csv_file_name, "rb") as csv_file:
        csv = csv.reader(csv_file, delimiter=",")
        clean_csv = eliminate_duplicates(csv, csv_eid, csv_time)

    # put all of the clean lines into the first queue
    END = '______________NO_MORE_LINES'
    for line in clean_csv:
        csvq.put(line)
    csvq.put(END)

    # wrapper for pulling the projects
    def pull_projects():
        run = True
        while run:
            csv_line = csvq.get()
            if csv_line != END:
                out_val = pull(csv_line, csv_eid, csv_url, csv_sha)
                dirq.put(out_val)
            else:
                dirq.put(END)
                run = False
            csvq.task_done()


    # wrapper for checking the projects
    def check_files():
        run = True
        while run:
            csv_line = dirq.get()
            if csv_line != END:
                direct = csv_line[csv_eid]
                message = check(files, direct)
                if len(message) > 0:
                    probq.put((csv_line, message))
                    outputq.put((csv_line, message))
                else:
                    outputq.put((csv_line, ['OK to grade']))
            else:
                run = False
                probq.put(END)
                outputq.put(END)
            dirq.task_done()

    # wrapper for emailing the projects
    def email_missing():
        run = True
        while run:
            in_val = probq.get()
            if in_val != END:
                csv_line, message = in_val 
                email(email_addr, password, smtp, csv_line[csv_email], cc, subject, csv_line[csv_eid], message)
            else:
                run = False
            probq.task_done()

    f = open('validation_results.csv', 'wb')
    def write():
        run = True
        while run:
            in_val = outputq.get()
            if in_val != END:
                csv_line, message = in_val 
                output_string = csv_line[csv_time] + ',' + csv_line[csv_eid] + ','
                for m in message:
                    output_string += m + ';'
                output_string += ', ' + csv_line[csv_url] + ',' + csv_line[csv_sha] + '\n'
                f.write(output_string)
                print output_string
            else:
                run = False
            outputq.task_done()


    pulling_thread1 = Thread(target = pull_projects)
    checking_thread = Thread(target = check_files)
    emailing_thread = Thread(target = email_missing)
    output_thread = Thread(target = write)

    pulling_thread1.start()
    checking_thread.start()
    emailing_thread.start()
    output_thread.start()

    pulling_thread1.join()
    checking_thread.join()
    emailing_thread.join()
    output_thread.join()

    f.close()

    print "done"
