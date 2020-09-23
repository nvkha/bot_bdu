from csv import reader
from re import T
import pdftables_api
import csv
import pandas as pd
import os
from crawl import crawl 
import tabula 

def preprosess(name):

    df = tabula.read_pdf(f"{name}.pdf", encoding='utf-8',multiple_tables=False, pages='all')
    tabula.convert_into(f"{name}.pdf", "output.csv", output_format="csv", pages='all')
    
    l = ["STT","Thứ","Ngày","Giờ","Số tiết","Phòng","SL","CBGD","Mã MH","Tên môn","Nhóm","Lớp"]
    with open("output.csv", 'r', encoding='utf-8', errors='ignore') as data_file:
        lines = data_file.readlines()
        lines[0]= ",".join(l)+"\n" # replace first line, the "header" with list contents
        with open("output.csv", 'w', encoding='utf-8', errors='ignore') as out_data:
            for line in lines: # write updated lines
                out_data.write(line)
                

preprosess('myfile')
