import click
import pandas as pd
import re
import time
import phonenumbers
from os import path

title = "Luck's Telefoonboek".upper()
frontpage_header = 'MOBIELE NUMMERS'
cellular_txt = 'Mobiel:'

@click.command()
@click.option('--csv-file', help="Path to phone numbers in CSV format")
def new_phonebook(csv_file):
    savedir = path.dirname(csv_file)

    numbers = pd.read_csv(csv_file, dtype={'name': str, 'phone': str, 'cellular': str, 'sort': str, 'frontpage': str})
    numbers = numbers.fillna('')

    frontpage, rest = process_numbers(numbers)

    latex_source = r'''
        \documentclass[a5paper]{article}
        \usepackage[a5paper]{geometry}
        \usepackage{ltablex}

        \usepackage[table]{xcolor}
        \definecolor{lightgray}{gray}{0.9}
        \let\oldtabularx\tabularx
        \let\endoldtabularx\endtabularx
        \renewenvironment{tabularx}{\rowcolors{2}{white}{lightgray}\oldtabularx}{\endoldtabularx}

        \title{%s}
        \date{%s}
        \author{}

        \begin{document}
        \begin{titlepage}
        \maketitle
        \thispagestyle{empty}
        \end{titlepage}
        \shipout\null
    ''' % (title, time.strftime("%d-%m-%Y"))

    # Front page
    latex_source = append_line(latex_source, r'\section*{'+frontpage_header+'}')

    latex_source = append_line(latex_source, r'\keepXColumns\begin{tabularx}{\textwidth}{X r}')
    for i, row in frontpage.iterrows():
        name = format_name(row['name'])
        phone = format_phone(row['cellular'])
        latex_source = append_line(latex_source, r'%s & %s \\ ' % (name, phone))
    latex_source = append_line(latex_source, r'\end{tabularx}')
    latex_source = append_line(latex_source, r'\clearpage')

    # Rest
    for letter, group in rest:
        latex_source = append_line(latex_source, r'\section*{'+letter+'}')

        latex_source = append_line(latex_source, r'\keepXColumns\begin{tabularx}{\textwidth}{X r}')
        for i, row in group.iterrows():
            name = format_name(row['name'])
            if row['phone']:
                phone = format_phone(row['phone'])
                latex_source = append_line(latex_source, r'%s & %s \\ ' % (name, phone))
                if row['cellular']:
                    cell = format_phone(row['cellular'])
                    latex_source = append_line(latex_source, r'\hspace{1em}%s & %s \\ ' % (cellular_txt, cell))
            elif row['cellular']:
                cell = format_phone(row['cellular'])
                latex_source = append_line(latex_source, r'%s & %s \\ ' % (name, cell))
        latex_source = append_line(latex_source, r'\end{tabularx}')
        latex_source = append_line(latex_source, r'\clearpage')

    latex_source = append_line(latex_source, r'\end{document}')

    with open(path.join(savedir, 'generated_phone_book.tex'), "w") as text_file:
        text_file.write(latex_source)

def append_line(latex_source, line):
    latex_source += line
    latex_source += '\n'
    return latex_source

def format_phone(phone):
    if phone == '':
        return phone

    try:
        phone_obj = phonenumbers.parse(phone, 'NL')
        if phone_obj.country_code != 31:
            return phonenumbers.format_number(phone_obj, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        else:
            return phonenumbers.format_number(phone_obj, phonenumbers.PhoneNumberFormat.NATIONAL)
    except phonenumbers.phonenumberutil.NumberParseException:
        print('Error: ' + phone)
        return phone

def format_name(name):
    return tex_escape(name)

def process_numbers(numbers):
    # update missing sort keys
    numbers.loc[numbers['sort'] == '', 'sort'] = numbers['name']

    numbers.sort_values('sort', inplace=True)

    # group into front page and rest
    frontpage = numbers[numbers['frontpage'] != '']
    rest = numbers

    # group rest on first letter of sort
    rest.loc[:, 'first_letter'] = rest['sort'].astype(str).str[0].str.upper()
    rest_grouped = rest.groupby('first_letter')

    return frontpage, rest_grouped

def tex_escape(text):
    """
        :param text: a plain text message
        :return: the message escaped to appear correctly in LaTeX
    """
    conv = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\^{}',
        '\\': r'\textbackslash{}',
        '<': r'\textless{}',
        '>': r'\textgreater{}',
    }
    regex = re.compile('|'.join(re.escape(str(key)) for key in sorted(conv.keys(), key = lambda item: - len(item))))
    return regex.sub(lambda match: conv[match.group()], text)

if __name__ == '__main__':
    new_phonebook()
