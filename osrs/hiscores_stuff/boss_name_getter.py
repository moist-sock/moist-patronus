from util.async_request import request
import re
import json


async def main():
    """
    This code will update json files for whenever the osrs boss hiscores experiences a shift when a new boss comes out
    This code should work until a boss comes out that comes after Zulrah alphabetically if that happens just change
    the final_boss variable to that new bosses name
    Also this code takes forever to run dont be alarmed at how long it takes (45 seconds)
    """

    final_boss = "Zulrah"

    name_of_bosses = []
    page_number = 1

    while True:
        status, text = await get_page(page_number)
        boss_name = name_of_boss(text)
        name_of_bosses.append(boss_name)
        page_number += 1
        if boss_name == final_boss:
            break

    print(name_of_bosses)

    with open(r"osrs/hiscores_stuff/osrs_bosses_list.json", "w") as f:
        print(f"saving boss list")
        json.dump(name_of_bosses, f, indent=2)

    dictoio = {}

    for count, bossy in enumerate(name_of_bosses, 1):
        dictoio[bossy] = {}
        dictoio[bossy]["ID"] = count

    with open(r"osrs/hiscores_stuff/osrs_bosses.json", "r") as f:
        old_boss_dict = json.load(f)

        for boss in old_boss_dict:

            dictoio[boss]["PNG"] = old_boss_dict[boss].get("PNG", None)
            dictoio[boss]["ALIAS"] = old_boss_dict[boss].get("ALIAS", [])
            dictoio[boss]["COLOR"] = old_boss_dict[boss].get("COLOR", None)

    with open(r"osrs/hiscores_stuff/osrs_bosses.json", "w") as f:

        print(f"saving boss json")
        json.dump(dictoio, f, indent=2)


async def get_page(number):
    url = f"https://secure.runescape.com/m=hiscore_oldschool/overall?category_type=1&table={number}#headerHiscores"
    status, html = await request(url)
    return status, html


def name_of_boss(text):
    pattern = r'<title>Old School (.*) Hiscores</title>'
    result = re.search(pattern, text)

    if result:
        return result.group(1)


if __name__ == '__main__':
    main()
