import csv


def download_csv(termoline, filename: str, dialect):
    with open(f'{filename}.csv', 'w', newline='') as f:
        writer = csv.writer(f, dialect)
        for row in range(termoline.tableWidget.rowCount()):
            row_data = [''] if row < 5 else [row - 4]
            for col in range(termoline.tableWidget.columnCount()):
                item = termoline.tableWidget.item(row, col)
                if item is not None:
                    row_data.append(item.text().replace('.', ','))
            if termoline.line_edit_temp_ref.text():
                if row <= 4 and row != 2:
                    row_data.append('-')
                elif row > 4:
                    t_ref = termoline.line_edit_temp_ref.text()
                    t_ref = t_ref.replace('.', ',')
                    if len(t_ref) <= 7:
                        add_diff = 0
                        if ',' not in t_ref:
                            t_ref += ','
                        if len(t_ref.split(',')[0]) == 1 or (len(t_ref.split(',')[0]) == 2 and '-' in t_ref):
                            add_diff += 1
                        if '-' in t_ref:
                            add_diff -= 1
                        t_ref += (6 - len(t_ref) - add_diff) * '0'
                    row_data.append(t_ref)
                else:
                    row_data.append('tref')
            writer.writerow(row_data)


def download_txt(termoline, filename: str):
    with open(f'{filename}.txt', 'w', newline='') as f:
        for row in range(termoline.tableWidget.rowCount()):
            row_data = 9 * ' ' + 'N' if row < 5 else (10 - len(str(row-4))) * ' ' + f'{row-4}'
            for col in range(termoline.tableWidget.columnCount()):
                item = termoline.tableWidget.item(row, col)
                if item is not None:
                    item_text = (10-len(item.text())) * ' ' + item.text()
                    row_data += item_text.replace(',', '.')
            if termoline.line_edit_temp_ref.text():
                if row <= 4 and row != 2:
                    row_data += 9 * ' ' + '-'
                elif row > 4:
                    t_ref = termoline.line_edit_temp_ref.text()
                    t_ref = t_ref.replace(',', '.')
                    if len(t_ref) <= 7:
                        add_diff = 0
                        if '.' not in t_ref:
                            t_ref += '.'
                        if len(t_ref.split('.')[0]) == 1 or (len(t_ref.split('.')[0]) == 2 and '-' in t_ref):
                            add_diff += 1
                        if '-' in t_ref:
                            add_diff -= 1
                        t_ref += (6 - len(t_ref) - add_diff) * '0'
                        t_ref = (10 - len(t_ref)) * ' ' + t_ref
                    row_data += (max_row_length - len(row_data) - 10) * ' ' + t_ref
                else:
                    row_data += 6 * ' ' + 'tref'
            if row == 0:
                max_row_length = len(row_data)
            f.write(row_data + '\n')



