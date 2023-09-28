from util.async_request import request
import re
import json


async def get_kc_for_rank(rank, boss_name):
    """
    returns killcount for rank, name of person at that rank for boss provided
    ---------------------
    If a new boss is added run the python file boss_name_getter.py and copy the dictionary that is printed under the
    dashed lines and replace the dictionary under the name boss_to_number on line 22 of this file and things should work
    """
    status, html = await get_hiscores_source_page(rank, boss_name)
    if status != 200:
        return status, None, None

    text_after = remove_text_before_desired_rank(html)
    text_list = text_after.splitlines()
    kc = text_list[8]
    name = name_of_player_with_desired_rank(text_after)

    return status, kc, name


async def get_hiscores_source_page(desired_rank, boss_name):
    with open(r"osrs/hiscores_stuff/osrs_bosses.json", "r") as f:
        boss_to_number = json.load(f)

    desired_rank = str(desired_rank)
    osrs_hiscores_url = f"https://secure.runescape.com/m=hiscore_oldschool/a=97/c=ATksZos0eXY/overall?category_type=1" \
                        f"&rank={desired_rank}&table={boss_to_number[boss_name]}&submit=Search "
    status, body = await request(osrs_hiscores_url)
    if status != 200:
        return status, None

    return status, body


def remove_text_before_desired_rank(text):
    split_text = text.split(r'<tr class="personal-hiscores__row personal-hiscores__row--type-highlight">')
    return split_text[1]


def name_of_player_with_desired_rank(text):
    pattern = r'hiscorepersonal\?user1=(.*?)\"'
    result = re.search(pattern, text)

    if result:
        return result.group(1)
