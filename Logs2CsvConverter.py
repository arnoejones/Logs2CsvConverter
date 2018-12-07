# -----------------------------------------------------------------------
# <copyright file = "Logs2CsvConverter.py" company = "IGT">
#     Copyright © 2018 IGT.  All rights reserved.
# </copyright>
# -----------------------------------------------------------------------

import PySimpleGUI as sg
import os
import re
import pandas as pd

# print = sg.Print
listbox_tuple = ()
logfiles_list = []
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


def list_to_tuple(listbox_contents):  # put in format the user interface can understand
    listbox_tuple = ()
    for item in listbox_contents:
        listbox_tuple += (item,)

    return listbox_tuple


def create_empty_folder(folder_name):
    if not os.path.exists(folder_name):
        print("creating", folder_name)
        os.makedirs(folder_name)


def verify_path(path):
    """Verify that the path specified exists."""
    if not os.path.exists(path):
        raise FileNotFoundException(path)


def empty_dir(top):
    if (top == '/' or top == "\\"):
        return
    else:
        for root, dirs, files in os.walk(top, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))


def convert_txt_to_csv(textfiles, output_file_name):

    for logfile in textfiles:
        with open(logfile) as lfile:
            if os.path.getsize(logfile) > 0:
                try:
                    text = lfile.read()
                except:
                    break  # sometimes there's a weird ascii char that won't translate.  Skip it.
                match = re.findall(
                    r"[_\n ]*(?P<info>\S+)\s+\|\s+(?P<dt>\S+)\s+(?P<tm>\S+)\s+\|\s+(?P<app_name>.+)\n(?P<msg>.+)", text)
                df = pd.DataFrame(match)
                df.columns = ['Log Level', 'Date', 'Time', 'App Name', 'Message']

                df_log_name = pd.DataFrame(columns=['Log File Data Extracted From'])
                df_log_name.loc[0] = logfile

                df3 = df.assign(**df_log_name.iloc[0])

                try:
                    with open(output_file_name, 'a') as f:
                        df3.to_csv(f, mode='a', header=False)
                except:
                    sg.Print("Something is wrong with opening the {} file. Is it in use?").format(output_file_name)

    #
    #             for tup in match:
    #                 tup_list = []
    #                 for t in tup:
    #                     tt = t.strip()
    #                     tup_list.append(tt)
    #                     tup_list.append(', ')
    #                 tup_list.append('\n')
    #                 for a in tup_list:
    #                     print(a)
    #                     csv_file.write(a)

    return True


layout = [
    [sg.Text('Convert a Log File into a CSV File')],
    [sg.Text('Output CSV Filename'), sg.InputText('MyFileName.csv', do_not_clear=True)],
    [sg.Text('CSV results directory', size=(15, 1)), sg.InputText(r"D:\Log2Csv\Log2CsvResults", do_not_clear=True)],
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
        convert_txt_to_csv(path_and_file_list, output_file_name=os.path.join(csv_target_dir, csv_filename))

        sg.Popup('CSV files successfully created. OK to close app.')

window.Close()
