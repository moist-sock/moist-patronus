import gspread
import json
from datetime import date
from osrs.hiscores_stuff.hiscores import get_boss_kc
from osrs.hiscores_stuff.hiscore_scalper import get_kc_for_rank
from osrs.hiscores_stuff.boss_name_getter import get_page, name_of_boss
from osrs.hiscores_stuff.boss_name_getter import main as update_bosses


class SecondFailure(Exception):
    pass


async def inputter(boss_name, name_of_sheet, extra=None, compare_rank=1000, main="moisty s0ck"):
    """
    Whenever a new boss comes out this code will break!! Here are the steps to fixing it
    1. I think i wrote instructions in the file hiscore_scalper.py
    2. Good luck
    """

    if not await correct_boss(boss_name):
        print(f"{boss_name} spreadsheet was not able to be completed because the hiscores boss list needs to be update"
              f"\n\nAttempting to update...\n")

        await update_bosses()
        print(f"Update complete! Will now attempt to update {boss_name} spreadsheet again")

        if not await correct_boss(boss_name):
            raise SecondFailure(f"SECOND FAILURE IN {boss_name} I WILL GIVE UP NOW PLEASE FIX ME :(")

        print(f"Boss list update successful!! Will now proceed as normal\n")

    ranks_to_get = [1, 100, 500, 1000]
    sheet = get_sheet(name_of_sheet)
    if have_we_done_today_already(sheet):
        print(f"{boss_name} data for {todays_date()} has already been collected")
        return

    next_row = next_row_to_use(sheet)

    if extra:
        await input_data_extra(sheet, next_row, boss_name, extra, compare_rank, main)

    else:
        await input_data(sheet, next_row, boss_name, compare_rank, main)

    for rank in ranks_to_get:
        await input_data_for_rank(sheet, next_row, rank, boss_name)

    print(f"{name_of_sheet} all done with no problems on {todays_date()}")


async def correct_boss(boss_name):
    file_name = r"osrs\hiscores_stuff\osrs_bosses.json"
    with open(file_name, "r") as f:
        boss_name_to_number = json.load(f)

    boss_number = boss_name_to_number[boss_name]
    status, page = await get_page(boss_number)
    osrs_boss_name = name_of_boss(page)

    return boss_name == osrs_boss_name


def get_sheet(name_of_sheet):
    account = gspread.service_account(r"config/gspread_token.json")

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


async def input_data(sheet, row, boss_name, rank, main):
    worksheet = sheet.worksheet("kc tracker")

    status, kc, name = await get_kc_for_rank(rank, boss_name)

    status, main_stats = await get_boss_kc(main)
    main_stats = main_stats[boss_name]

    input_data_list = [[todays_date(), rank, name, kc, None, main_stats["kc"], main_stats["rank"]]]
    # true_row = get_true_row(row, input_data_list)
    worksheet.update(row, input_data_list)


async def input_data_extra(sheet, row, boss, extra, rank, main):
    worksheet = sheet.worksheet("kc tracker")

    status, kc, name = await get_kc_for_rank(rank, boss)

    status, main_stats = await get_boss_kc(main)
    main_stats = main_stats[boss]

    status, extra_stats = await get_boss_kc(extra)
    extra_stats = extra_stats[boss]

    worksheet.update(row, [[todays_date(), rank, name, kc, None,
                            main_stats["kc"], main_stats["rank"],
                            None, None, None,
                            extra_stats["kc"], extra_stats["rank"]]])


async def input_data_for_rank(sheet, row, rank, boss):
    worksheet = sheet.worksheet(f'rank {str(rank)}')

    status, kc, name = await get_kc_for_rank(rank, boss)

    worksheet.update(row, [[todays_date(), rank, name, kc]])
    worksheet.update(row, [[todays_date(), rank, name, kc]])


def get_true_row(row, update_list):
    row_number = row[1:]
    number = len(update_list) + 2
    next_letter = number_to_letters(number)
    next_letter += row_number
    return row + ":" + next_letter


def number_to_letters(n):
    result = ""
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        result = chr(65 + remainder) + result
    return result


def letter_to_number(s):
    s = s.upper()
    result = 0
    for char in s:
        result = result * 26 + (ord(char) - ord('A')) + 1
    return result

