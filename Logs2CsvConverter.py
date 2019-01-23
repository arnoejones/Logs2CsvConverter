# -----------------------------------------------------------------------
# <copyright file = "Logs2CsvConverter.py" company = "IGT">
#     Copyright © 2018 IGT.  All rights reserved.
# </copyright>
# -----------------------------------------------------------------------

import PySimpleGUI as sg
import os
import re
import pandas as pd

# listbox_tuple = ()
# logfiles_list = []
logfile_name = ''
global myPath
myPath = ''
path_and_file_list = []

deleted_items_list = []

add_logfile_button_label = 'Add selected logfile to list'
delete_logfile_button_label = 'Whoops, delete selected logfile(s)'


class FileNotFoundException(Exception):
    def __init__(self, file):
        self.file = file

    def __str__(self):
        error_string = "File not found: {0}".format(repr(self.file))
        return error_string


# def strip_nonascii(b):
#     z = str(b.decode('ascii', errors='ignore'))
#     return z


# def list_to_tuple(listbox_contents):  # put in format the user interface can understand
#     listbox_tuple = ()
#     for item in listbox_contents:
#         listbox_tuple += (item,)
#
#     return listbox_tuple


def create_empty_folder(folder_name):
    if not os.path.exists(folder_name):
        print("creating", folder_name)
        os.makedirs(folder_name)


def verify_path(path):
    """Verify that the path specified exists."""
    if not os.path.exists(path):
        raise FileNotFoundException(path)


def empty_dir(top):
    if top == '/' or top == "\\":
        return
    else:
        for root, dirs, files in os.walk(top, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))


def convert_txt_to_csv(textfiles, output_file_name):
    pat = re.compile(
        '[_\n ]*(?P<info>\S+)\s+\|\s+(?P<dt>\S+)\s+(?P<tm>\S+)\s+\|\s+(?P<app_name>.+)\n(?P<msg>.+)')

    for logfile in textfiles:
        if os.path.getsize(logfile) > 0:
            sum = []
            with open(logfile, "rb") as log_file:  # rb = read, binary.  This is the big one.  Reading text is better
                                                    # because it reads ascii.  If you know for sure that your log
                                                    # files will not contain binary data, then the command should
                                                    # look like: with open(logfile, "r") as log_file:
                for line in log_file:
                    # look for binary (non-ascii) and ignore
                    ascii_data = line.decode("ascii", errors="ignore")
                    # take the new, decoded lines and add to the sum list. Strings are immutable.
                    sum.append(ascii_data)
                str = ''.join(sum)  # turns a list into a string that we can regex against.

                match = re.findall(pat, str)  # match is a list of tuples

                # tuples are immutable, so we have to deconstruct them, make our changes, and reconstruct them.
                # tmp_list = []
                # for item in match:  # each list
                #     for tup in item:  # each tuple
                #         tmp_list.append(tup)  # list contains just items now, not tuples
                tmp_list = [tup for item in match for tup in item]

                for idx, l in enumerate(tmp_list):  # for each item in list
                    if '\r' in l:  # remove the crlf if found
                        # now it's a modified list of changed values, but not tuples
                        tmp_list[idx] = l.replace('\r', ' ')



                counter = 0

                # now we need to reconstruct a list of tuples.  BTW, each list item contains 5 tuples. Each tuple contains
                # the category of info, such as the INFO, Date, Time, Message, etc.  This way each list item is one
                # line in the spreadsheet.  In other words, the tuples are related by being a list item.  No need to
                # comma-delimit or other shenanigans when your data already has commas or whatever.
                final_tuple_list = []
                temp_tuple_list = []
                for list_item in tmp_list:
                    # there is probably and elegant, pythonic way to do this, but I'm not experienced enough yet, so
                    # here it is in agonizing detail.
                    if counter <= 5:  # this is some hard-coding I hate.  Normally I would try to dynamically figure
                        # out how many categories there are, but you promised there are only 5, so I'm taking the path
                        # of least-resistance :-)
                        temp_tuple_list.append(list_item)
                        counter += 1
                        if counter == 5:
                            t = tuple(temp_tuple_list)
                            final_tuple_list.append(t)
                            counter = 0
                            temp_tuple_list = []

                # at this point we have a dumb array of data.  Let's smarten it up a bit anc conver the list of tuples
                # into a Pandas dataframe.  Dataframes can be sophisticated and allow all kinds of programmatic
                # customization.  For this task, the customization only consists of adding the column headers and
                # and adding the log file names.
                df = pd.DataFrame(final_tuple_list)
                df.columns = ['Log Level', 'Date', 'Time', 'App Name', 'Message']
                # let's add a new column name
                df_log_name = pd.DataFrame(columns=['Log File Data Extracted From'])
                # Fill that new column with the name of the source log file
                df_log_name.loc[0] = logfile
                # and finally, add it to the existing dataframe
                df3 = df.assign(**df_log_name.iloc[0])

                try:
                    with open(output_file_name, 'a') as f:
                        # writing a dataframe to file is different the the
                        df3.to_csv(f, mode='a', header=True)
                        # normal Python way.
                except:
                    # You should get this error message if you have the file open in Excel while you are trying to
                    # write this file.  Excel (and others) put a lock on the file.  I won't know that until I get here.
                    sg.Print("Something is wrong with opening the {} file. Is it in use?").format(
                        output_file_name)

    return True


# https://pysimplegui.readthedocs.io/#how-do-i
layout = [
    [sg.Text('Convert a Log File into a CSV File')],
    [sg.Text('Output CSV Filename'), sg.InputText('MyFileName.csv', do_not_clear=True)],
    [sg.Text('CSV results directory', size=(15, 1)), sg.InputText(
        r"D:\Log2Csv\Log2CsvResults", do_not_clear=True)],
    [sg.Text('Location of logfile(s)')],
    [sg.InputText(r'D:\Log2Csv\Log2CsvLogs', do_not_clear=True), sg.FolderBrowse()],
    [sg.Submit(button_color=('black', 'lightgreen')), sg.Exit(button_color=('black', 'Crimson'))]
]

window = sg.Window('Create a CSV File').Layout(layout)

while True:
    event, values = window.Read()
    csv_filename = values[0]
    csv_target_dir = values[1]
    raw_logs_folder = values[2]

    if event is None or event == 'Exit':
        break

    if event == 'Submit':

        print('submit events: ', event, values)
        print('button was pressed')

        destination = os.path.join(csv_target_dir, logfile_name)
        # now separate out the filename
        myfileName = os.path.basename(destination)  # which I don't care about
        # and separate out the path
        myPath = os.path.dirname(destination)
        # now join all that stuff again

        list_of_logs = os.listdir(raw_logs_folder)
        print(list_of_logs)
        for log in list_of_logs:
            path_and_file_list.append(os.path.join(raw_logs_folder, log))

        # convert_txt_to_csv
        convert_txt_to_csv(path_and_file_list, output_file_name=os.path.join(
            csv_target_dir, csv_filename))

        sg.Popup('CSV files successfully created. OK to close app.')

window.Close()
