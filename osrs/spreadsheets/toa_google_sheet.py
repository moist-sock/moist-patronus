import gspread
import osrs.toa.toa_hiscore_scalper as toa
from datetime import date
from osrs.hiscores_stuff.hiscores import get_boss_kc, get_stats


def main():
    """
    Whenever a new boss comes out this code will break!! Here are the steps to fixing it
    1. Open the file "boss_name_getter.py"
    2. Follow the instructions in that file then run the code
    3. copy the output and paste it in "hiscores.py" for the variable 'bosses'
    4. go into the file "toa_hiscore_scalper.py" and update line 31 with the proper url for toa expert
    """

    ranks_to_get = [1, 100, 500, 1000]
    gamers_to_get = ['moisty s0ck, hemeonc']
    sheet = get_sheet()
    if have_we_done_today_already(sheet):
        print(f"TOA data for {todays_date()} has already been collected")
        return

    next_row = next_row_to_use(sheet)
    input_data(sheet, next_row)
    for rank in ranks_to_get:
        input_data_for_rank(sheet, next_row, rank)


def get_sheet():
    sa = gspread.service_account(r"C:\Users\moist\Downloads\osrs-toa-expert-kc-tracker-c68cfa94b163.json")

    sheet = sa.open("toa expert kc")

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


def input_data(sheet, row):
    worksheet = sheet.worksheet("kc tracker")
    boss = "Tombs of Amascut: Expert Mode"
    name, rank, kc = toa.main()
    moisty_stats = get_boss_kc("moisty s0ck")[boss]
    heme_stats = get_boss_kc("HemeOnc")[boss]
    worksheet.update(row, [[todays_date(), rank, name, kc, None,
                            moisty_stats["kc"], moisty_stats["rank"], None, None, None,
                            heme_stats["kc"], heme_stats["rank"]]])


def input_data_for_rank(sheet, row, rank):
    worksheet = sheet.worksheet(f'rank {str(rank)}')
    kc, name = toa.get_kc_for_rank(rank)
    if rank == 1:
        total_xp = get_stats(name)["Overall"]["xp"]
        total_xp = "{:,}".format(total_xp)
        worksheet.update(row, [[todays_date(), rank, name, kc, None, total_xp]])

    worksheet.update(row, [[todays_date(), rank, name, kc]])


if __name__ == '__main__':
    main()
