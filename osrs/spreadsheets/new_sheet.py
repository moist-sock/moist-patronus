import gspread


def main():
    """
    Instructions on how to use:
    1. Make a copy of "spindel kc" and click share with same people or after its created share with gservice account
    2. name the sheet for the new boss you're grinding
    3. On line 13 enter the name of the sheet
    4. Run this code and it will clear all the data but keep the formulas
    """

    name_of_spreadsheet = "duke kc"

    account = gspread.service_account()
    spreadsheet = account.open(name_of_spreadsheet)
    clear_sheets(spreadsheet)

    print(f'{name_of_spreadsheet} is all cleared')


def clear_sheet(name_of_sheet, list_of_cells):
    name_of_sheet.batch_clear(list_of_cells)


def clear_sheets(spreadsheet):
    name_of_sheets = [
        'kc tracker',
        'rank 1',
        'rank 100',
        'rank 500',
        'rank 1000',
    ]

    for sheet in name_of_sheets:
        cells_to_clear = ["A2:P499"]

        if sheet == 'kc tracker':
            cells_to_clear = ["A2:H499"]

        worksheet = spreadsheet.worksheet(sheet)
        clear_sheet(worksheet, cells_to_clear)


if __name__ == "__main__":
    main()
