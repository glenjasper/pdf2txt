#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
import sys
import time
import argparse
# import pdftotext
import subprocess
import traceback
import xlsxwriter
import unicodedata
import numpy as np
import pandas as pd
from colorama import init
init()

def menu():
    parser = argparse.ArgumentParser(description = "This script converts .pdf files to .txt files.", epilog = "Thank you!")
    parser.add_argument("-f", "--folder_pdf", required = True, help = "Folder that contains all .pdf files")
    parser.add_argument("-o", "--output", help = "Output folder")
    parser.add_argument("--version", action = "version", version = "%s %s" % ('%(prog)s', op2t.VERSION))
    args = parser.parse_args()

    folder_pdf_name = os.path.basename(args.folder_pdf)
    folder_pdf_path = os.path.dirname(args.folder_pdf)
    if folder_pdf_path is None or folder_pdf_path == "":
        folder_pdf_path = os.getcwd().strip()

    op2t.FOLDER_PDF = os.path.join(folder_pdf_path, folder_pdf_name)
    if not op2t.check_path(op2t.FOLDER_PDF):
        op2t.show_print("%s: error: the folder '%s' doesn't exist" % (os.path.basename(__file__), op2t.FOLDER_PDF), showdate = False, font = op2t.YELLOW)
        op2t.show_print("%s: error: the following arguments are required: -f/--folder_pdf" % os.path.basename(__file__), showdate = False, font = op2t.YELLOW)
        exit()

    if args.output is not None:
        output_name = os.path.basename(args.output)
        output_path = os.path.dirname(args.output)
        if output_path is None or output_path == "":
            output_path = os.getcwd().strip()

        op2t.OUTPUT_PATH = os.path.join(output_path, output_name)
        created = op2t.create_directory(op2t.OUTPUT_PATH)
        if not created:
            op2t.show_print("%s: error: Couldn't create folder '%s'" % (os.path.basename(__file__), op2t.OUTPUT_PATH), showdate = False, font = op2t.YELLOW)
            exit()
    else:
        op2t.OUTPUT_PATH = os.getcwd().strip()
        op2t.OUTPUT_PATH = os.path.join(op2t.OUTPUT_PATH, 'output_txt')
        op2t.create_directory(op2t.OUTPUT_PATH)

class Pdf2Txt:

    def __init__(self):
        self.VERSION = 1.0

        self.FOLDER_PDF = None
        self.OUTPUT_PATH = None

        self.ROOT_DIR = os.path.dirname(os.path.realpath(__file__))
        self.LOG_NAME = "run_%s_%s.log" % (os.path.splitext(os.path.basename(__file__))[0], time.strftime('%Y%m%d'))
        self.LOG_FILE = None
        self.DAMAGED_FILES = 'damaged_files.log'

        # Xls Summary
        self.XLS_FILE = 'summary_download.xlsx'
        self.XLS_FILE_CONVERTED = 'summary_converted.xlsx'
        self.XLS_SHEET_UNIQUE = 'Unique'

        # Xls Columns
        self.xls_col_item = 'Item'
        self.xls_col_title = 'Title'
        self.xls_col_year = 'Year'
        self.xls_col_doi = 'DOI'
        self.xls_col_document_type = 'Document Type'
        self.xls_col_languaje = 'Language'
        self.xls_col_cited_by = 'Cited By'
        self.xls_col_download = 'Download'
        self.xls_col_repository = 'Repository'
        self.xls_col_pdf_name = 'PDF Name'
        self.xls_col_txt_name = 'TXT Name'
        self.xls_col_converted = 'Status'

        self.xls_columns_csv = [self.xls_col_item,
                                self.xls_col_title,
                                self.xls_col_year,
                                self.xls_col_doi,
                                self.xls_col_document_type,
                                self.xls_col_languaje,
                                self.xls_col_cited_by,
                                self.xls_col_repository,
                                self.xls_col_converted,
                                self.xls_col_txt_name]

        self.STATUS_OK = 'Ok'
        self.STATUS_DAMAGED = 'Damaged file'

        # Fonts
        self.RED = '\033[31m'
        self.GREEN = '\033[32m'
        self.YELLOW = '\033[33m'
        self.BIRED = '\033[1;91m'
        self.BIGREEN = '\033[1;92m'
        self.END = '\033[0m'

    def show_print(self, message, logs = None, showdate = True, font = None, end = None):
        msg_print = message
        msg_write = message

        if font is not None:
            msg_print = "%s%s%s" % (font, msg_print, self.END)

        if showdate is True:
            _time = time.strftime('%Y-%m-%d %H:%M:%S')
            msg_print = "%s %s" % (_time, msg_print)
            msg_write = "%s %s" % (_time, message)

        print(msg_print, end = end)
        if logs is not None:
            for log in logs:
                if log is not None:
                    with open(log, 'a', encoding = 'utf-8') as f:
                        f.write("%s\n" % msg_write)
                        f.close()

    def start_time(self):
        return time.time()

    def finish_time(self, start, message = None):
        finish = time.time()
        runtime = time.strftime("%H:%M:%S", time.gmtime(finish - start))
        if message is None:
            return runtime
        else:
            return "%s: %s" % (message, runtime)

    def create_directory(self, path):
        output = True
        try:
            if len(path) > 0 and not os.path.exists(path):
                os.makedirs(path)
        except Exception as e:
            output = False
        return output

    def check_path(self, path):
        _check = False
        if path is not None:
            if len(path) > 0 and os.path.exists(path):
                _check = True
        return _check

    def check_empty(self, file):
        _check = False
        if os.stat(file).st_size == 0:
            _check = True
        return _check

    # https://stackoverflow.com/questions/229186/os-walk-without-digging-into-directories-below
    def walklevel(self, some_dir, level = 1):
        some_dir = some_dir.rstrip(os.path.sep)
        assert os.path.isdir(some_dir)
        num_sep = some_dir.count(os.path.sep)
        for root, dirs, files in os.walk(some_dir):
            yield root, dirs, files
            num_sep_this = root.count(os.path.sep)
            if num_sep + level <= num_sep_this:
                del dirs[:]

    def count_files(self, directory, extension = 'pdf'):
        count = 0
        for root, dirnames, filenames in self.walklevel(directory):
            for filename in filenames:
                if re.search('\.(%s)$' % extension, filename):
                    count += 1
        return count

    def get_listdir(self, path_docs, extension = 'txt'):
        _listdir = []
        for file in os.listdir(path_docs):
            if file.endswith('.%s' % extension):
                _listdir.append(os.path.join(path_docs, file))
        return _listdir

    def get_num_lines(self, input_file):
        num_lines = sum(1 for line in open(input_file))
        return num_lines

    def search_word_array(self, words = [[]], string = None):
        for idx, item in enumerate(words):
            reviewed = False
            for word in item:
                if word not in string:
                    reviewed = True
                    if idx == 0:
                        break
                    else:
                        return False
            if idx == 0 and not reviewed:
                return True
        return True

    def run_program(self, cmd, words = [[]]):
        _cmd = " ".join(cmd)
        try:
            p = subprocess.Popen(_cmd, shell = True, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
        except Exception as e:
            self.show_print("Error %s while executing command %s" % (e, _cmd), [self.LOG_FILE])

        error = False
        for line in iter(p.stdout.readline, b''):
            _line = line.decode('utf-8').rstrip()
            if error is False and self.search_word_array(words, _line):
                error = True
            if 'Syntax Warning:' not in _line \
               and 'Internal Error' not in _line \
               and 'Failed to parse XRef entry' not in _line \
               and 'Illegal character' not in _line \
               and 'Dictionary key must be a name object' not in _line \
               and 'End of file inside dictionary' not in _line \
               and 'name token is longer than what the specification' not in _line \
               and 'Invalid XRef entry' not in _line \
               and 'Mismatched EMC operator' not in _line \
               and 'Unknown operator' not in _line \
               and 'Couldn\'t find trailer dictionary' not in _line \
               and 'Expected the default config' not in _line \
               and 'Expected the optional content group list' not in _line \
               and 'Unterminated string' not in _line:

                self.show_print(_line, [self.LOG_FILE])
        if not error:
            return True
        else:
            return False

    def read_xls(self):
        dict_pdf = {}
        if self.check_path(self.XLS_FILE):
            df = pd.read_excel(io = self.XLS_FILE, sheet_name = self.XLS_SHEET_UNIQUE)
            # df = df.where(pd.notnull(df), None)
            df = df.replace({np.nan: None})

            for idx, row in df.iterrows():
                if row[self.xls_col_download] == self.STATUS_OK:
                    collect = {}
                    collect[self.xls_col_title] = row[self.xls_col_title]
                    collect[self.xls_col_year] = row[self.xls_col_year]
                    collect[self.xls_col_doi] = row[self.xls_col_doi]
                    collect[self.xls_col_document_type] = row[self.xls_col_document_type]
                    collect[self.xls_col_languaje] = row[self.xls_col_languaje]
                    collect[self.xls_col_cited_by] = row[self.xls_col_cited_by]
                    collect[self.xls_col_repository] = row[self.xls_col_repository]
                    collect[self.xls_col_pdf_name] = row[self.xls_col_pdf_name]
                    index = '%s/%s' % (row[self.xls_col_document_type], row[self.xls_col_pdf_name])
                    dict_pdf.update({index: collect})

        return dict_pdf

    def get_txtname(self, pdffile):
        txtname = os.path.basename(pdffile)
        txtname, _ = os.path.splitext(txtname)
        txtfile = '%s.txt' % txtname

        return txtfile

    def format_txt(self, txtfile):
        txtfile_tmp = '%s.tmp' % txtfile

        with open(txtfile, 'r') as fr, open(txtfile_tmp, 'w') as fw:
            for line in fr:
                line = ''.join(ch for ch in line if unicodedata.category(ch)[0] != 'C')
                line = line.replace(' ', ' ')
                line = line.strip()
                fw.write('%s\n' % line)
        fr.close()
        fw.close()

        os.remove(txtfile)
        os.rename(txtfile_tmp, txtfile)

    def pdf2txt_cpp(self, pdffile, txtfile):
        try:
            filetype = 'text'

            cmd = ["pdftotext",
                   "'%s'" % pdffile,
                   "'%s'" % txtfile]

            words = [["Syntax", "Error", "Couldn", "read", "xref", "table"],
                     ["Command", "Line", "Error", "Wrong", "page", "range", "given", "first", "page", "after", "last", "page"]]

            # Command Line Error: Wrong page range given: the first page (1) can not be after the last page (0).

            _result = self.run_program(cmd, words)

            return _result
        except Exception as e:
            return False

    def pdf2txt_miner(self, pdffile, txtfile):
        try:
            filetype = 'text'

            cmd = ["pdf2txt.py",
                   "-t %s" % filetype,
                   "-A",
                   "-o '%s'" % txtfile,
                   "'%s'" % pdffile]

            words = ["Unexpected", "EOF"]

            _result = self.run_program(cmd, words)

            return _result
        except Exception as e:
            return False

    def pdf2txt_python(self, pdffile, txtfile):
        try:
            with open(txtfile, 'w') as fw:
                with open(pdffile, 'rb') as fr:
                    pdf = pdftotext.PDF(fr)
                fr.close()

                for page in pdf:
                    fw.write('%s\n' % page)
            fw.close()

            return True
        except Exception as e:
            return False

    def pdf2txt_multiple(self, pdf_info):
        total = self.count_files(self.FOLDER_PDF)
        self.show_print("Found .pdf files: %s" % total, [self.LOG_FILE], font = self.GREEN)
        self.show_print("", [self.LOG_FILE], end = '\r')

        if total > 0:
            handle_damaged = open(self.DAMAGED_FILES, 'w')
            count = 0
            for root, dirnames, filenames in self.walklevel(self.FOLDER_PDF):
                for filename in filenames:
                    if re.search('\.(pdf)$', filename):
                        count += 1
                        pdffile = os.path.join(root, filename)
                        txtfile = self.get_txtname(pdffile)

                        folder_type = os.path.basename(root)
                        index_pdf = os.path.join(folder_type, filename)

                        folder_out = None
                        if index_pdf in pdf_info.keys():
                            folder_out = pdf_info[index_pdf][self.xls_col_document_type]
                            folder_out = os.path.join(self.OUTPUT_PATH, folder_out)
                            self.create_directory(folder_out)

                            pdf_info[index_pdf].update({self.xls_col_converted: self.STATUS_OK})
                            pdf_info[index_pdf].update({self.xls_col_txt_name: txtfile})

                        if folder_out is None:
                            folder_out = self.OUTPUT_PATH

                        txtfile = os.path.join(folder_out, txtfile)

                        convert = True
                        if self.check_path(txtfile):
                            convert = self.check_empty(txtfile)

                        if convert:
                            self.show_print("[%s/%s] Converting the file: %s..." % (count, total, filename[:50]), [self.LOG_FILE], end = '\r')
                            ist_ok = self.pdf2txt_cpp(pdffile, txtfile)
                            # ist_ok = self.pdf2txt_python(pdffile, txtfile)
                            # ist_ok = self.pdf2txt_miner(pdffile, txtfile)

                            if ist_ok:
                                self.format_txt(txtfile)
                            else:
                                handle_damaged.write('%s\n' % filename)
                                if len(pdf_info) > 0:
                                    pdf_info[index_pdf].update({self.xls_col_converted: self.STATUS_DAMAGED})
                                    pdf_info[index_pdf].update({self.xls_col_txt_name: None})

            handle_damaged.close()

            self.show_print("")
            self.show_print("", [self.LOG_FILE])
            self.show_print("Output path: %s" % self.OUTPUT_PATH, [self.LOG_FILE], font = self.GREEN)

            if len(pdf_info) > 0:
                self.save_summary_xls(pdf_info)
                self.show_print("  Details file: %s" % os.path.basename(self.XLS_FILE_CONVERTED), [self.LOG_FILE], font = self.GREEN)

            damageds = self.get_num_lines(self.DAMAGED_FILES)
            if damageds > 0:
                self.show_print("  Corrupted files found: %s" % damageds, [self.LOG_FILE], font = self.GREEN)
                self.show_print("    See the file: %s" % os.path.basename(self.DAMAGED_FILES), [self.LOG_FILE], font = self.GREEN)
            else:
                os.remove(self.DAMAGED_FILES)
        else:
            self.show_print("'%s' folder doesn't contain pdf files." % self.FOLDER_PDF, [self.LOG_FILE])

    def save_summary_xls(self, data_txt):
        _last_col = len(self.xls_columns_csv) - 1

        workbook = xlsxwriter.Workbook(self.XLS_FILE_CONVERTED)
        worksheet = workbook.add_worksheet(self.XLS_SHEET_UNIQUE)
        worksheet.freeze_panes(row = 1, col = 0) # Freeze the first row.
        worksheet.autofilter(first_row = 0, first_col = 0, last_row = 0, last_col = _last_col) # 'A1:H1'
        worksheet.set_default_row(height = 14.5)

        # Add columns
        cell_format_title = workbook.add_format({'bold': True,
                                                 'font_color': 'white',
                                                 'bg_color': 'black',
                                                 'align': 'center',
                                                 'valign': 'vcenter'})
        for icol, column in enumerate(self.xls_columns_csv):
            worksheet.write(0, icol, column, cell_format_title)

        # Add rows
        worksheet.set_column(first_col = 0, last_col = 0, width = 7)  # Column A:A
        worksheet.set_column(first_col = 1, last_col = 1, width = 40) # Column B:B
        worksheet.set_column(first_col = 2, last_col = 2, width = 8)  # Column C:C
        worksheet.set_column(first_col = 3, last_col = 3, width = 33) # Column D:D
        worksheet.set_column(first_col = 4, last_col = 4, width = 18) # Column E:E
        worksheet.set_column(first_col = 5, last_col = 5, width = 12) # Column F:F
        worksheet.set_column(first_col = 6, last_col = 6, width = 11) # Column G:G
        worksheet.set_column(first_col = 7, last_col = 7, width = 13) # Column H:H
        worksheet.set_column(first_col = 8, last_col = 8, width = 13) # Column I:I
        worksheet.set_column(first_col = 9, last_col = 9, width = 30) # Column J:J

        cell_format_row = workbook.add_format({'text_wrap': True, 'valign': 'top'})
        icol = 0
        for irow, (_, item) in enumerate(data_txt.items(), start = 1):
            col_title = item[self.xls_col_title]
            col_year = item[self.xls_col_year]
            col_doi = item[self.xls_col_doi]
            col_document_type = item[self.xls_col_document_type]
            col_languaje = item[self.xls_col_languaje]
            col_cited_by = item[self.xls_col_cited_by]
            col_repository = item[self.xls_col_repository]
            col_converted = item[self.xls_col_converted]
            col_txt_name = item[self.xls_col_txt_name]

            worksheet.write(irow, icol + 0, irow, cell_format_row)
            worksheet.write(irow, icol + 1, col_title, cell_format_row)
            worksheet.write(irow, icol + 2, col_year, cell_format_row)
            worksheet.write(irow, icol + 3, col_doi, cell_format_row)
            worksheet.write(irow, icol + 4, col_document_type, cell_format_row)
            worksheet.write(irow, icol + 5, col_languaje, cell_format_row)
            worksheet.write(irow, icol + 6, col_cited_by, cell_format_row)
            worksheet.write(irow, icol + 7, col_repository, cell_format_row)
            worksheet.write(irow, icol + 8, col_converted, cell_format_row)
            worksheet.write(irow, icol + 9, col_txt_name, cell_format_row)
        workbook.close()

def main():
    try:
        start = op2t.start_time()
        menu()

        op2t.LOG_FILE = os.path.join(op2t.OUTPUT_PATH, op2t.LOG_NAME)
        op2t.DAMAGED_FILES = os.path.join(op2t.OUTPUT_PATH, op2t.DAMAGED_FILES)
        op2t.XLS_FILE_CONVERTED = os.path.join(op2t.OUTPUT_PATH, op2t.XLS_FILE_CONVERTED)
        op2t.XLS_FILE = os.path.join(op2t.FOLDER_PDF, op2t.XLS_FILE)
        op2t.show_print("############################################################################", [op2t.LOG_FILE], font = op2t.BIGREEN)
        op2t.show_print("################################ PDF to TXT ################################", [op2t.LOG_FILE], font = op2t.BIGREEN)
        op2t.show_print("############################################################################", [op2t.LOG_FILE], font = op2t.BIGREEN)

        pdfs_info = op2t.read_xls()
        op2t.pdf2txt_multiple(pdfs_info)

        op2t.show_print("", [op2t.LOG_FILE])
        op2t.show_print(op2t.finish_time(start, "Elapsed time"), [op2t.LOG_FILE])
        op2t.show_print("Done!", [op2t.LOG_FILE])
    except Exception as e:
        op2t.show_print("\n%s" % traceback.format_exc(), [op2t.LOG_FILE], font = op2t.RED)
        op2t.show_print(op2t.finish_time(start, "Elapsed time"), [op2t.LOG_FILE])
        op2t.show_print("Done!", [op2t.LOG_FILE])

if __name__ == '__main__':
    op2t = Pdf2Txt()
    main()
