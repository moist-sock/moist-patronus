from util.async_request import request
import re
import json
from bs4 import BeautifulSoup


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
        if status != 200:
            print(f"error {status}: in getting boss names updated - page number {page_number}")
            return
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

    with open(r"storage/osrs_bosses.json", "r") as f:
        old_boss_dict = json.load(f)

    for count, bossy in enumerate(name_of_bosses, 1):
        dictoio[bossy] = {}
        dictoio[bossy]["ID"] = count
        dictoio[bossy]["PNG"] = old_boss_dict.get(bossy, {}).get("PNG", await get_image(bossy))
        dictoio[bossy]["ALIAS"] = old_boss_dict.get(bossy, {}).get("ALIAS", [])
        dictoio[bossy]["COLOR"] = old_boss_dict.get(bossy, {}).get("COLOR", None)

    with open(r"storage/osrs_bosses.json", "w") as f:

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


async def get_image(boss):
    url = f"https://oldschool.runescape.wiki/w/{boss.replace(' ', '_')}"
    status, html_content = await request(url)
    if status != 200:
        if status == 404:
            return None
        else:
            print(f"------------\nError in get image while building new osrs boss dict bc of the url\n{url}\n------------")
            return None

    soup = BeautifulSoup(html_content, 'html.parser')

    og_image_meta_tag = soup.find('meta', {'property': 'og:image'})

    # Extract the content attribute value
    if og_image_meta_tag:
        og_image_url = og_image_meta_tag.get('content')
        image_link = og_image_url
    else:
        image_link = None

    return image_link

if __name__ == '__main__':
    main()
