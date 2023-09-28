import gspread
from datetime import date
from osrs.hiscores_stuff.hiscores import get_boss_kc
from osrs.hiscores_stuff.hiscore_scalper import get_kc_for_rank


def main():
    """
    Whenever a new boss comes out this code will break!! Here are the steps to fixing it
    1. I think i wrote instructions in the file hiscore_scalper.py
    2. Good luck
    """

    boss = "Spindel"
    name_of_sheet = "spindel kc"
    ranks_to_get = [1, 100, 500, 1000]
    sheet = get_sheet(name_of_sheet)
    if have_we_done_today_already(sheet):
        print(f"Spindel data for {todays_date()} has already been collected")
        return

    next_row = next_row_to_use(sheet)
    input_data(sheet, next_row, boss)
    for rank in ranks_to_get:
        input_data_for_rank(sheet, next_row, rank, boss)

    print(f"All done with no problems on {todays_date()}")


def get_sheet(name_of_sheet):
    account = gspread.service_account(r"C:\Users\moist\Downloads\osrs-toa-expert-kc-tracker-c68cfa94b163.json")

    sheet = account.open(name_of_sheet)

    return sheet


def todays_date():
    return str(date.today().strftime("%m/%d/%y"))


def have_we_done_today_already(sheet):
    worksheet = sheet.worksheet("kc tracker")
    return worksheet.col_values(2)[-1] == todays_date()


def next_row_to_use(sheet):
    worksheet = sheet.worksheet("kc tracker")
    values = worksheet.col_values(2)
    next_row = 'B' + str(len(values) + 1)
    return next_row


def input_data(sheet, row, boss):
    worksheet = sheet.worksheet("kc tracker")
    rank = 1000
    kc, name = get_kc_for_rank(rank, boss)
    moisty_stats = get_boss_kc("moisty s0ck")[boss]
    worksheet.update(row, [[todays_date(), rank, name, kc, None,
                            moisty_stats["kc"], moisty_stats["rank"]]])


def input_data_for_rank(sheet, row, rank, boss):
    worksheet = sheet.worksheet(f'rank {str(rank)}')
    kc, name = get_kc_for_rank(rank, boss)
    worksheet.update(row, [[todays_date(), rank, name, kc]])

    worksheet.update(row, [[todays_date(), rank, name, kc]])


if __name__ == '__main__':
    main()
