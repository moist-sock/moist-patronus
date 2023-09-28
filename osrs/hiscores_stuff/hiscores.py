from util.async_request import request
import json


async def get_stats(user):
    status, raw_stats = await hiscores(user)
    if status != 200:
        return status, None

    return status, levels_wrapper(raw_stats)


async def get_boss_kc(user):
    status, raw_stats = await hiscores(user)

    if status != 200:
        return status, None

    return status, kc_wrapper(raw_stats)


async def hiscores(user):
    status, hiscores_info = await request(
        f"https://secure.runescape.com/m=hiscore_oldschool/index_lite.ws?player={user}")
    if status != 200:
        return status, None

    return status, hiscores_info.splitlines()


def levels_wrapper(stats):
    skills = ['Overall',
              'Attack',
              'Defence',
              'Strength',
              'Hitpoints',
              'Ranged',
              'Prayer',
              'Magic',
              'Cooking',
              'Woodcutting',
              'Fletching',
              'Fishing',
              'Firemaking',
              'Crafting',
              'Smithing',
              'Mining',
              'Herblore',
              'Agility',
              'Thieving',
              'Slayer',
              'Farming',
              'Runecraft',
              'Hunter',
              'Construction']
    skills_dict = {}

    stats = stats[:24]

    for skill, stat in zip(skills, stats):
        stat = stat.split(",")
        if stat[0] == "-1":
            continue

        skills_dict[skill] = {"rank": int(stat[0]),
                              "level": int(stat[1]),
                              "xp": int(stat[2])}

    return skills_dict


def kc_wrapper(stats):
    """
    returns a nested dictionary with the boss in osrs as the key
    the two sub keys being 'rank' and 'kc'
    """
    file_path = r"C:\Users\moist\PycharmProjects\testorsomething\osrs\hiscores_stuff\osrs_bosses_list.json"
    with open(file_path, "r") as f:
        bosses = json.load(f)

    boss_dict = {}
    stats = stats[25:]

    for boss, stat in zip(bosses, stats):
        stat = stat.split(",")
        if stat[1] == "-1":
            continue

        boss_dict[boss] = {"rank": int(stat[0]),
                           "kc": int(stat[1])}

    return boss_dict
