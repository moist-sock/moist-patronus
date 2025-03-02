import asyncio
import json

import discord
import textdistance
import random
import pathlib

from datetime import datetime, timedelta
from math import log, ceil
from discord import Embed, app_commands
from discord.ext import commands
from osrs.hiscores_stuff.hiscores import get_boss_kc, get_stats, levels_wrapper
from osrs.spreadsheets.google_sheet_inputter import inputter
from osrs.xp import xp_dict
from osrs.hiscores_stuff.boss_name_getter import main as boss_name
from util.attachment_reader import ctx_attachment_reader as reader
from util.time_functions import run_daily_task
from util.async_request import request
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from math import floor
from pprint import pprint
from util.store_test_json import store_test


def formatted_yesterday_today():
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    today -= timedelta(days=0)
    return yesterday.strftime('%d%b%Y').upper(), today.strftime('%d%b%Y').upper()


class NoName(Exception):
    async def message(self, ctx, sep):
        await ctx.send(
            f"Either add your account to the bot with /osrs or add '{sep} (account name)' after the first input")


class Runescape(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.spreadsheet = asyncio.create_task(self.spreadsheet_loop())
        self.news_loop_check = asyncio.create_task(self.news_loop())
        self.account_data = asyncio.create_task(self.account_data_loop())
        self.seperator = "/"

        self.fake_bosses = [
            "Deadman Points",
            "Bounty Hunter - Hunter",
            "Bounty Hunter - Rogue",
            "Bounty Hunter (Legacy) - Hunter",
            "Bounty Hunter (Legacy) - Rogue",
            "Clue Scrolls (all)",
            "Clue Scrolls (beginner)",
            "Clue Scrolls (easy)",
            "Clue Scrolls (medium)",
            "Clue Scrolls (hard)",
            "Clue Scrolls (elite)",
            "Clue Scrolls (master)",
            "LMS - Rank",
            "PvP Arena - Rank",
            "Soul Wars Zeal",
            "Rifts closed",
            "Tempoross",
            "Wintertodt",
            "Zalcano",
            "The Gauntlet",
            "The Corrupted Gauntlet"
        ]
        self.slayer_bosses = [
            "Abyssal Sire",
            "Alchemical Hydra",
            "Bryophyta",
            "Cerberus",
            "Grotesque Guardians",
            "Kraken",
            "Mimic",
            "Obor",
            "Skotizo",
            "Thermonuclear Smoke Devil"
        ]
        self.skills = ['Overall',
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

        with open("storage/osrs_bosses.json", "r") as f:
            self.boss_dict = json.load(f)

        with open('storage/league.json', 'r') as f:
            self.gamer_dict = json.load(f)

        try:
            with open("storage/osrs_news.json", "r") as f:
                self.news = json.load(f)

        except FileNotFoundError:
            with open("storage/osrs_news.json", "w") as f:
                json.dump([], f, indent=1)
                self.news = []

        self.items = [
            "10th birthday balloons",
            "10th birthday cape",
            "10th squad sigil",
            "20th anniversary boots",
            "20th anniversary bottom",
            "20th anniversary cape",
            "20th anniversary gloves",
            "20th anniversary hat",
            "20th anniversary necklace",
            "20th anniversary top",
            "3rd age amulet",
            "3rd age axe",
            "3rd age bow",
            "3rd age cloak",
            "3rd age druidic cloak",
            "3rd age druidic robe bottoms",
            "3rd age druidic robe top",
            "3rd age druidic staff",
            "3rd age felling axe",
            "3rd age full helmet",
            "3rd age kiteshield",
            "3rd age longsword",
            "3rd age mage hat",
            "3rd age pickaxe",
            "3rd age platebody",
            "3rd age platelegs",
            "3rd age plateskirt",
            "3rd age range coif",
            "3rd age range legs",
            "3rd age range top",
            "3rd age robe",
            "3rd age robe top",
            "3rd age vambraces",
            "3rd age wand",
            "4th birthday hat",
            "5-gallon jug",
            "8-gallon jug",
            "A big present",
            "A chair",
            "A container",
            "A dark disposition",
            "A jester stick",
            "A magic scroll",
            "A pattern",
            "A powdered wig",
            "A special tiara",
            "Abyssal ashes",
            "Abyssal bludgeon",
            "Abyssal dagger",
            "Abyssal dagger (bh)",
            "Abyssal head",
            "Abyssal lantern",
            "Abyssal needle",
            "Abyssal observations",
            "Abyssal orphan",
            "Abyssal protector",
            "Abyssal tentacle",
            "Abyssal tentacle (or)",
            "Abyssal whip (or)",
            "Abyssal-tainted essence",
            "Achey tree logs",
            "Address form",
            "Address label",
            "Adventurer's cape",
            "Adventurer's hood (t1)",
            "Adventurer's top (t1)",
            "Adventurer's top (t2)",
            "Adventurer's top (t3)",
            "Adventurer's trousers (t1)",
            "Adventurer's trousers (t2)",
            "Adventurer's trousers (t3)",
            "Afro",
            "Air nerve",
            "Aivas bust",
            "Al kharid flyer",
            "Alchemical hydra heads",
            "Ale of the gods",
            "Aluft aloft box",
            "Amethyst",
            "Ammo mould",
            "Amulet of avarice",
            "Amulet of blood fury",
            "Amulet of defence (t)",
            "Amulet of duplication",
            "Amulet of fury (or)",
            "Amulet of glory (t)",
            "Amulet of magic (t)",
            "Amulet of power (t)",
            "Amulet of the damned",
            "Amulet of torture",
            "Amy's saw",
            "Amylase crystal",
            "Ana in a barrel",
            "Ancestral key",
            "Anchovy oil",
            "Anchovy paste",
            "Ancient astroscope",
            "Ancient blood ornament kit",
            "Ancient carcanet",
            "Ancient ceremonial boots",
            "Ancient ceremonial gloves",
            "Ancient ceremonial legs",
            "Ancient ceremonial mask",
            "Ancient ceremonial top",
            "Ancient coin",
            "Ancient crozier",
            "Ancient crystal",
            "Ancient d'hide shield",
            "Ancient diary",
            "Ancient effigy",
            "Ancient emblem",
            "Ancient globe",
            "Ancient godsword",
            "Ancient halo",
            "Ancient hilt",
            "Ancient icon",
            "Ancient jewel",
            "Ancient key (Dragon Slayer II)",
            "Ancient key (Tombs of Amascut)",
            "Ancient ledger",
            "Ancient map",
            "Ancient medallion",
            "Ancient mjolnir",
            "Ancient relic",
            "Ancient remnant",
            "Ancient robe legs",
            "Ancient robe top",
            "Ancient sceptre",
            "Ancient shard",
            "Ancient signet",
            "Ancient staff",
            "Ancient statuette",
            "Ancient symbol",
            "Ancient talisman",
            "Ancient totem",
            "Ancient treatise",
            "Ancient wyvern shield",
            "Anger battleaxe",
            "Anger mace",
            "Anger spear",
            "Anger sword",
            "Angler boots",
            "Angler hat",
            "Angler top",
            "Angler waders",
            "Anguish ornament kit",
            "Anima portal",
            "Anima-infused bark",
            "Animal skull",
            "Ankou mask",
            "Ankou socks",
            "Ankou top",
            "Ankou's leggings",
            "Anti-panties",
            "Antisanta boots",
            "Antisanta gloves",
            "Antisanta jacket",
            "Antisanta mask",
            "Antisanta pantaloons",
            "Antisanta's coal box",
            "Apple barrel",
            "Apple tree seed",
            "Apprentice wand",
            "Apricot cream pie",
            "Arachnids of vampyrium",
            "Arcane sigil",
            "Arcane spirit shield",
            "Arcenia root",
            "Arceuus banner",
            "Arceuus icon",
            "Arceuus scarf",
            "Arceuus signet",
            "Archer helm",
            "Archer icon",
            "Arclight",
            "Arder mushroom",
            "Arder powder",
            "Ardougne cloak 1",
            "Ardougne cloak 2",
            "Ardougne cloak 3",
            "Ardougne cloak 4",
            "Ardougne knight platebody",
            "Ardougne knight tabard",
            "Arena book",
            "Armadyl armour ornament kit",
            "Armadyl chainskirt",
            "Armadyl chainskirt (or)",
            "Armadyl chestplate",
            "Armadyl chestplate (or)",
            "Armadyl crozier",
            "Armadyl d'hide shield",
            "Armadyl halo",
            "Armadyl helmet",
            "Armadyl helmet (or)",
            "Armadyl hilt",
            "Armadylean plate",
            "Armour shard",
            "Arms",
            "Asgoldian ale",
            "Ash sanctifier",
            "Asleif's necklace",
            "Astral nerve",
            "Attacker horn",
            "Attacker icon",
            "Attas seed",
            "Ava's assembler",
            "Avernic defender",
            "Avernic defender (beta)",
            "Avernic defender hilt",
            "Awakener's orb",
            "Axe head",
            "Baby mole",
            "Bag of salt",
            "Baguette",
            "Ball",
            "Ball of wool",
            "Ballista limbs",
            "Ballista spring",
            "Balloon structure",
            "Balloon toad",
            "Banana cape",
            "Banana hat",
            "Banana tree seed",
            "Bandos armour ornament kit",
            "Bandos boots",
            "Bandos boots (or)",
            "Bandos chestplate",
            "Bandos chestplate (or)",
            "Bandos cloak",
            "Bandos crozier",
            "Bandos d'hide shield",
            "Bandos halo",
            "Bandos hilt",
            "Bandos stole",
            "Bandos tassets (or)",
            "Bandosian components",
            "Bank filler",
            "Bank note",
            "Banner (Arrav)",
            "Banner (Asgarnia)",
            "Banner (Dorgeshuun)",
            "Banner (Dragon)",
            "Banner (Fairy)",
            "Banner (Guthix)",
            "Banner (HAM)",
            "Banner (Horse)",
            "Banner (Jogre)",
            "Banner (Kandarin)",
            "Banner (Misthalin)",
            "Banner (Money)",
            "Banner (Saradomin)",
            "Banner (Skull)",
            "Banner (Varrock)",
            "Banner (Zamorak)",
            "Banshee mask",
            "Banshee robe",
            "Banshee top",
            "Bar magnet",
            "Barb bolttips",
            "Barb-tail harpoon",
            "Barbarian rod",
            "Barbed arrow",
            "Barbed bolts",
            "Bark",
            "Baron",
            "Barrel (The Tourist Trap)",
            "Barrel of coal tar",
            "Barrelchest anchor",
            "Barrelchest anchor (bh)",
            "Barricade",
            "Barricade (Desert Treasure II)",
            "Barronite deposit",
            "Barronite guard",
            "Barronite handle",
            "Barronite head",
            "Barronite mace",
            "Basalt",
            "Basic shadow torch",
            "Basilisk head",
            "Basilisk jaw",
            "Basket",
            "Bat shish",
            "Battered book",
            "Battlestaff",
            "Bauble box",
            "Beacon ring",
            "Beads of the dead",
            "Beam",
            "Beanie",
            "Bear feet",
            "Bearhead",
            "Beaten book",
            "Beautiful yellow pansy seed",
            "Beaver",
            "Bee on a stick",
            "Beef fillet",
            "Beekeeper's hat",
            "Beekeeper's legs",
            "Beekeeper's top",
            "Beer glass (Forgettable Tale...)",
            "Beer glass of water",
            "Beer tankard",
            "Beginner wand",
            "Bell jar",
            "Belladonna seed",
            "Bellator icon",
            "Bellator ring",
            "Bellator ring (beta)",
            "Bellator vestige",
            "Belt buckle",
            "Beret mask",
            "Berserker helm",
            "Berserker icon",
            "Berserker necklace",
            "Berserker necklace (or)",
            "Berserker necklace ornament kit",
            "Big banana",
            "Big bass",
            "Big bucket",
            "Big frog leg",
            "Big harpoonfish",
            "Big pirate hat",
            "Big shark",
            "Big snowball",
            "Big swordfish",
            "Binding book",
            "Binding fluid",
            "Binding necklace",
            "Bird book",
            "Bird nest (empty)",
            "Bird nest (ring)",
            "Bird nest (Wyson, 2006-2016)",
            "Bird snare",
            "Birthday balloons",
            "Birthday cake",
            "Birthday cake (Mobile Anniversary)",
            "Bitter chocolate mix",
            "Bitternut",
            "Black demon mask",
            "Black mushroom",
            "Black prism",
            "Black tourmaline core",
            "Blacksmith's helm",
            "Blackstone fragment",
            "Blessed axe",
            "Blighted ancient ice sack",
            "Blighted bind sack",
            "Blighted entangle sack",
            "Blighted snare sack",
            "Blighted teleport spell sack",
            "Blighted vengeance sack",
            "Blindweed",
            "Blisterwood flail",
            "Blisterwood sickle",
            "Blood essence",
            "Blood nerve",
            "Blood shard",
            "Blood tithe pouch",
            "Bloodbark boots",
            "Bloodbark legs",
            "Bloodhound",
            "Bloody head",
            "Bloody mourner top",
            "Bludgeon axon",
            "Bludgeon claw",
            "Bludgeon spine",
            "Blue dragon scale",
            "Bluegill",
            "Blunt arrow",
            "Blunt scimitars",
            "Blurite sword",
            "Bob (unobtainable item)",
            "Bob the cat slippers",
            "Bobble hat",
            "Bobble scarf",
            "Body core",
            "Bologa's blessing",
            "Bolt mould",
            "Bolt of cloth",
            "Bolt pouch",
            "Bolt rack",
            "Bomber cap",
            "Bomber jacket",
            "Bone beads",
            "Bone bolts",
            "Bone club",
            "Bone dagger",
            "Bone fragments",
            "Bone in vinegar",
            "Bone shard",
            "Bone spear",
            "Bonecrusher",
            "Bonecrusher necklace",
            "Bonesack",
            "Book (Shield of Arrav)",
            "Book o' piracy",
            "Boots of brimstone",
            "Boots of darkness",
            "Boots of stone",
            "Boots of the eye",
            "Bottle of 'tonic'",
            "Bottom of sceptre",
            "Bounty hunter hat (tier 1)",
            "Bounty hunter hat (tier 2)",
            "Bounty hunter hat (tier 3)",
            "Bounty hunter hat (tier 4)",
            "Bounty hunter hat (tier 5)",
            "Bounty hunter hat (tier 6)",
            "Bounty hunter ornament kit",
            "Bow and arrow",
            "Bow-sword",
            "Bowl of fish",
            "Bowl of food (RuneScape 2 Beta)",
            "Bowl of hot water",
            "Bowl wig",
            "Box of chocolate strawberries",
            "Box trap",
            "Bracelet mould",
            "Brain tongs",
            "Branch",
            "Branch (Temple Trekking)",
            "Brandy",
            "Brassica halo",
            "Breadcrumbs",
            "Brewer's folly",
            "Bridge section",
            "Briefcase",
            "Brimstone key",
            "Brimstone ring",
            "Brine sabre",
            "Broad arrowheads",
            "Broad arrows",
            "Broken armour",
            "Broken arrow",
            "Broken axe (dragon)",
            "Broken cannon",
            "Broken cauldron",
            "Broken coffin",
            "Broken crab claw",
            "Broken crab shell",
            "Broken device",
            "Broken dragon hasta",
            "Broken egg",
            "Broken fishing rod",
            "Broken gingerbread",
            "Broken glass",
            "Broken pickaxe (dragon)",
            "Broken plate",
            "Broken pole",
            "Broken redirector",
            "Broken staff",
            "Broken tiara",
            "Bronze fire arrow",
            "Bronze speedrun trophy",
            "Brooch",
            "Bruised banana",
            "Bruma kindling",
            "Bruma torch",
            "Bryophyta's essence",
            "Bryophyta's staff",
            "Bucket (animation item)",
            "Bucket of wester sand",
            "Builder's shirt",
            "Builder's trousers",
            "Bulging taxbag",
            "Bullet arrow",
            "Bullroarer",
            "Bullseye lantern (unf)",
            "Bunny ears",
            "Bunny feet",
            "Bunny legs",
            "Bunny paws",
            "Bunny top",
            "Bunnyman mask",
            "Burnt crab meat",
            "Burnt potato",
            "Butch",
            "Butterfly jar",
            "Butterfly net",
            "Buttons",
            "Cabbage cape",
            "Cabbage round shield",
            "Cabbage seed",
            "Cactus seed",
            "Cactus spine",
            "Cake hat",
            "Cake of guidance",
            "Calamity breeches",
            "Calamity chest",
            "Calcite",
            "Callisto cub",
            "Calquat fruit",
            "Camel mask",
            "Camel mould (p)",
            "Camorra bust",
            "Camulet",
            "Candy cane",
            "Cannon ball (Between a Rock...)",
            "Cannon ball (Cabin Fever)",
            "Cannon balls (unobtainable item)",
            "Cannon barrel (Cabin Fever)",
            "Cannon barrels",
            "Cannon barrels (or)",
            "Cannon base",
            "Cannon base (or)",
            "Cannon furnace",
            "Cannon furnace (or)",
            "Cannon stand",
            "Cannon stand (or)",
            "Cap and goggles",
            "Capacitor",
            "Cape of legends",
            "Cape of skulls",
            "Carpenter's boots",
            "Carpenter's helmet",
            "Carpenter's shirt",
            "Carpenter's trousers",
            "Casket",
            "Casket piece",
            "Castle sketch 1",
            "Castle sketch 2",
            "Castle sketch 3",
            "Cat mask",
            "Cat training medal",
            "Catalytic guardian stone",
            "Catalytic talisman",
            "Catfish",
            "Cattleprod",
            "Cavalier mask",
            "Cave goblin wire",
            "Cave nightshade",
            "Cave worms",
            "Cavefish",
            "Cavern grubs",
            "Celastrus bark",
            "Celastrus seed",
            "Celestial ring",
            "Celestial signet",
            "Centurion cuirass",
            "Ceramic remains",
            "Certificate (Shield of Arrav)",
            "Chain",
            "Chair",
            "Champion's cape",
            "Champion's lamp",
            "Chaos core",
            "Chaos elemental (unobtainable item)",
            "Chaos talisman",
            "Charcoal",
            "Charge dragonstone jewellery scroll",
            "Charged cell",
            "Charged ice",
            "Charged onyx",
            "Cheese+tom batta",
            "Chicken (Recruitment Drive)",
            "Chicken cage",
            "Chilli potato",
            "Chisel (animation item)",
            "Chisel (Desert Treasure II)",
            "Choc-ice",
            "Chocolate chunks",
            "Chocolate chunks (2013 Easter event)",
            "Chocolate egg",
            "Chocolate kebbit",
            "Chompy chick",
            "Chopped garlic",
            "Christmas cracker",
            "Christmas jumper",
            "Chromium ingot",
            "Chronicle",
            "Chunk of crystal",
            "Church decoration",
            "Church lectern",
            "Cinnamon",
            "Circlet of water",
            "Circular hide",
            "Citizen shoes",
            "Citizen top",
            "Citizen trousers",
            "Claws of callisto",
            "Clay head",
            "Cleaver",
            "Climbing boots (g)",
            "Cloak of ruin",
            "Clockwork",
            "Clockwork book",
            "Clockwork suit",
            "Clothes pouch blueprint",
            "Clover insignia",
            "Clown bow tie",
            "Clown gown",
            "Clown mask",
            "Clown shoes",
            "Clown trousers",
            "Clue box",
            "Clue hunter boots",
            "Clue hunter cloak",
            "Clue hunter garb",
            "Clue hunter trousers",
            "Clue scroll (easy)",
            "Clue scroll (elite)",
            "Clue scroll (hard)",
            "Clue scroll (special)",
            "Clueless scroll",
            "Coal bag",
            "Coated frogs' legs",
            "Cobweb cape",
            "Cockatrice head",
            "Coconut",
            "Coffin",
            "Coffin nails",
            "Cog",
            "Coins",
            "Coins (My Arm's Big Adventure)",
            "Coins (Shilo Village)",
            "Collector icon",
            "Colossal blade",
            "Colour wheel",
            "Coloured ball",
            "Comfy mattress",
            "Common tench",
            "Comp ogre bow",
            "Compass (The Garden of Death)",
            "Compost bin (unobtainable item)",
            "Conch shell",
            "Condensed gold",
            "Conductor",
            "Conductor mould",
            "Cook's letter",
            "Cook's shopping list",
            "Cooked crab meat",
            "Cooking pot",
            "Cormorant's glove",
            "Corpse of woman",
            "Corrupted armadyl godsword",
            "Corrupted dragon claws",
            "Corrupted morrigan's leather body (bh)",
            "Corrupted morrigan's leather chaps (bh)",
            "Corrupted scythe of vitur",
            "Corrupted statius's platebody (bh)",
            "Corrupted statius's platelegs (bh)",
            "Corrupted tumeken's shadow",
            "Corrupted twisted bow",
            "Corrupted vesta's chainbody (bh)",
            "Corrupted vesta's plateskirt (bh)",
            "Corrupted voidwaker",
            "Corrupted zuriel's robe bottom (bh)",
            "Corrupted zuriel's robe top (bh)",
            "Cow blood",
            "Cow gloves",
            "Cow mask",
            "Cow shoes",
            "Cow tail",
            "Cow top",
            "Cow trousers",
            "Cowbells",
            "Crab claw",
            "Crab helmet",
            "Crabclaw hook",
            "Cracked cake tin",
            "Cracked sample",
            "Crackers",
            "Crandor map",
            "Crane claw",
            "Cranial clamp",
            "Crate of baskets",
            "Crate part",
            "Crate ring",
            "Crate with zanik",
            "Craw's bow",
            "Crawling hand (item)",
            "Creature keeper's journal",
            "Crier bell",
            "Crier coat",
            "Crier hat",
            "Crimson fibre",
            "Crone-made amulet",
            "Crossbow",
            "Crossbow string",
            "Crude carving",
            "Cruder carving",
            "Crunchy chocolate mix",
            "Crunchy easter egg",
            "Crunchy tray",
            "Crushed gem",
            "Crushed nest",
            "Crypt key (2018 Halloween event)",
            "Crystal (Song of the Elves)",
            "Crystal armour seed",
            "Crystal bow",
            "Crystal charm",
            "Crystal chime",
            "Crystal chime seed",
            "Crystal felling axe",
            "Crystal grail",
            "Crystal of memories",
            "Crystal pendant",
            "Crystal saw",
            "Crystal shield",
            "Crystal tool seed",
            "Crystal trinket",
            "Crystal weapon seed",
            "Cube",
            "Curator's medallion",
            "Cured yak-hide",
            "Curry leaf",
            "Curry tree seed",
            "Cursed banana",
            "Cursed goblin hammer",
            "Cursed phalanx",
            "Curved bone",
            "Cutthroat flag",
            "Cyan crystal (Tale of the Righteous, interface item)",
            "Cyclops head",
            "Cylinder",
            "Cyrisus's chest",
            "Daconia rock",
            "Daeyalt essence",
            "Daeyalt shard",
            "Dagannoth hide",
            "Dagon'hai history",
            "Dagon'hai robe bottom",
            "Dagon'hai robe bottom (or)",
            "Dagon'hai robes set",
            "Damaged armour",
            "Damaged monkey tail",
            "Damp coal dust",
            "Damp planks",
            "Dark acorn",
            "Dark altar (unobtainable item)",
            "Dark bow (bh)",
            "Dark claw",
            "Dark dagger",
            "Dark flippers",
            "Dark infinity colour kit",
            "Dark journal",
            "Dark manuscript",
            "Dark totem",
            "Dark totem base",
            "Dark totem middle",
            "Dark totem top",
            "Dark tuxedo cuffs",
            "Dark tuxedo jacket",
            "Dark tuxedo shoes",
            "Dart (unobtainable item)",
            "Dawn scarab egg",
            "Dawnbringer",
            "Dead person",
            "Dead sea slug",
            "Deadwood log",
            "Deadwood plank",
            "Death's coffer (unobtainable item)",
            "Death's fabric",
            "Decapitated head",
            "Decapitated head (The Fremennik Isles)",
            "Deconstructed onyx",
            "Decorative armour (magic hat)",
            "Decorative armour (magic legs)",
            "Decorative armour (magic top)",
            "Decorative armour (quiver)",
            "Decorative armour (ranged legs)",
            "Decorative armour (ranged top)",
            "Decorative emblem",
            "Deerstalker",
            "Defender icon",
            "Defensive shield",
            "Demon feet",
            "Demon's heart",
            "Demonic sigil",
            "Demonic sigil mould",
            "Demonic tome",
            "Desert disguise",
            "Desert legs",
            "Desert robes",
            "Desert top (overcoat)",
            "Detonator",
            "Devout boots",
            "Dinh's bulwark",
            "Dinh's hammer",
            "Directionals",
            "Disk of returning",
            "Distillator",
            "Divine rune pouch",
            "Doctor's hat",
            "Doll of iban",
            "Dorgeshuun crossbow",
            "Double ammo mould",
            "Double eye patch",
            "Dr banikan (item)",
            "Draconic visage",
            "Dragon 2h sword",
            "Dragon 2h sword (cr)",
            "Dragon arrowtips",
            "Dragon axe",
            "Dragon axe head",
            "Dragon battleaxe",
            "Dragon battleaxe (cr)",
            "Dragon boots (cr)",
            "Dragon boots ornament kit",
            "Dragon candle dagger",
            "Dragon cane",
            "Dragon chainbody (cr)",
            "Dragon chainbody (g)",
            "Dragon chainbody ornament kit",
            "Dragon claws (cr)",
            "Dragon claws (or)",
            "Dragon claws ornament kit",
            "Dragon crossbow",
            "Dragon crossbow (cr)",
            "Dragon crossbow (u)",
            "Dragon dagger (cr)",
            "Dragon dart",
            "Dragon dart tip",
            "Dragon defender (t)",
            "Dragon defender ornament kit",
            "Dragon felling axe",
            "Dragon fire arrow",
            "Dragon full helm ornament kit",
            "Dragon halberd",
            "Dragon halberd (cr)",
            "Dragon harpoon",
            "Dragon hunter lance",
            "Dragon inn tankard",
            "Dragon knife",
            "Dragon limbs",
            "Dragon longsword",
            "Dragon longsword (bh)",
            "Dragon longsword (cr)",
            "Dragon mace",
            "Dragon mace (bh)",
            "Dragon mace (cr)",
            "Dragon med helm (cr)",
            "Dragon metal lump",
            "Dragon metal shard",
            "Dragon metal slice",
            "Dragon pickaxe",
            "Dragon pickaxe (broken)",
            "Dragon pickaxe (or)",
            "Dragon pickaxe (upgraded)",
            "Dragon platelegs (cr)",
            "Dragon plateskirt (cr)",
            "Dragon scimitar (cr)",
            "Dragon scimitar (or)",
            "Dragon scimitar ornament kit",
            "Dragon spear (cr)",
            "Dragon sq shield (cr)",
            "Dragon sq shield ornament kit",
            "Dragon sword",
            "Dragon sword (cr)",
            "Dragon thrownaxe",
            "Dragon token",
            "Dragon warhammer",
            "Dragon warhammer (cr)",
            "Dragon warhammer (or)",
            "Dragon warhammer ornament kit",
            "Dragonbone necklace",
            "Dragonfire shield",
            "Dragonfire ward",
            "Dragonfruit",
            "Dragonfruit tree seed",
            "Dragonstone boots",
            "Dragonstone full helm",
            "Dragonstone gauntlets",
            "Dragonstone platebody",
            "Dragonstone platelegs",
            "Drakan's medallion",
            "Drake's claw",
            "Dream log",
            "Dried cocoa",
            "Druidic wreath",
            "Drunk parrot",
            "Dual sai",
            "Dummy portal",
            "Dusty scroll (Secrets of the North)",
            "Dwarf (The Giant Dwarf)",
            "Dwarf cake",
            "Dynamite pot",
            "Eagle cape",
            "Eagle feather",
            "Earmuffs",
            "Earthy chocolate mix",
            "Earthy easter egg",
            "Easter basket",
            "Easter chocolate dust",
            "Easter egg",
            "Easter egg half",
            "Easter egg helm",
            "Easter hat",
            "Easter ring",
            "Eastfloor spade",
            "Ecto-token",
            "Ectophial",
            "Ectoplasmator",
            "Ecumenical key",
            "Eek",
            "Eel sushi",
            "Efh salt",
            "Egg cushion",
            "Egg mould (2018 Easter event)",
            "Egg potato",
            "Egg whisk",
            "Eggshell platebody",
            "Eggshell platelegs",
            "Ekeleshuun key",
            "Elaborate lockbox",
            "Elder chaos robe",
            "Elder chaos robe (or)",
            "Elder chaos top",
            "Elder chaos top (or)",
            "Elder maul (beta)",
            "Elder maul (or)",
            "Elder maul ornament kit",
            "Elder wand",
            "Eldritch ashes",
            "Elem longsword (RuneScape 2 Beta)",
            "Elemental rune pack",
            "Elemental talisman",
            "Elidinis' ward",
            "Elite calamity breeches",
            "Elite calamity chest",
            "Elite void top",
            "Elite void top (or)",
            "Elvarg's head",
            "Elven legwear",
            "Elven signet",
            "Elysian sigil",
            "Elysian spirit shield",
            "Embalming manual",
            "Empty bucket pack",
            "Empty candle lantern",
            "Empty gourd vial",
            "Empty oil lamp",
            "Empty oil lantern",
            "Empty spice shaker",
            "Empty tax bag",
            "Enchanted curtains",
            "Enchanted hat",
            "Enchanted key (item)",
            "Enchanted robe",
            "Enchanted snowy curtains",
            "Enchanted symbol",
            "Enchanted top",
            "Engine",
            "Enhanced crystal key",
            "Enhanced crystal teleport seed",
            "Enhanced crystal weapon seed",
            "Ensouled abyssal head",
            "Ensouled aviansie head",
            "Ensouled bear head",
            "Ensouled bloodveld head",
            "Ensouled chaos druid head",
            "Ensouled dagannoth head",
            "Ensouled demon head",
            "Ensouled dog head",
            "Ensouled dragon head",
            "Ensouled elf head",
            "Ensouled giant head",
            "Ensouled goblin head",
            "Ensouled hellhound head",
            "Ensouled horror head",
            "Ensouled imp head",
            "Ensouled kalphite head",
            "Ensouled minotaur head",
            "Ensouled monkey head",
            "Ensouled ogre head",
            "Ensouled scorpion head",
            "Ensouled troll head",
            "Ensouled tzhaar head",
            "Ensouled unicorn head",
            "Ent's roots",
            "Equa leaves",
            "Escape crystal",
            "Eternal gem",
            "Eternal teleport crystal",
            "Evil chicken's egg",
            "Evil root",
            "Excalibur",
            "Executioner's axe head",
            "Explorer backpack",
            "Exquisite boots",
            "Exquisite clothes",
            "Extended brush",
            "Extradimensional bag",
            "Eye of the duke",
            "Facemask",
            "Fairy enchantment",
            "Fairy mushroom",
            "Fake beak",
            "Fake beard",
            "Fake man",
            "Falador shield 1",
            "Falador shield 2",
            "Falador shield 3",
            "Falador shield 4",
            "Falador teleport (tablet)",
            "Falconer's glove",
            "Family crest (item)",
            "Fancier boots",
            "Fancy boots",
            "Fancy tiara",
            "Fang (The Fremennik Exiles)",
            "Fang (Tombs of Amascut)",
            "Fangs of venenatis",
            "Farmer's boots",
            "Farmer's boro trousers",
            "Farmer's fork",
            "Farmer's jacket",
            "Farmer's shirt",
            "Farmer's strawhat",
            "Farming manual",
            "Farseer helm",
            "Feathered journal",
            "Fedora",
            "Felling axe handle",
            "Ferocious gloves",
            "Ferret",
            "Festive cinnamon",
            "Festive elf slippers",
            "Festive games crown",
            "Festive gingerbread gnomes",
            "Festive holly",
            "Festive tree branch",
            "Fever spider body",
            "Fez",
            "Fibula piece",
            "Field arrow",
            "Field ration",
            "Fiendish ashes",
            "Fighter hat",
            "Fighter torso",
            "Fighter torso (or)",
            "Fighting boots",
            "Fillets",
            "Fine cloth",
            "Fine mesh net",
            "Fingernails",
            "Fingers",
            "Fire (unobtainable item)",
            "Fire cape",
            "Fish barrel",
            "Fish chunks",
            "Fish offcuts",
            "Fish sack",
            "Fish sack barrel",
            "Fishbowl and net",
            "Fishing pass",
            "Fishing trophy",
            "Fishy chocolate mix",
            "Fishy easter egg",
            "Five barrels",
            "Fixed device",
            "Flamtaer bag",
            "Flamtaer hammer",
            "Flared trousers",
            "Flash powder",
            "Flattened hide",
            "Flax",
            "Flippers",
            "Fluffs' kitten",
            "Fluffy chocolate mix",
            "Fluffy easter egg",
            "Fluffy feathers",
            "Fly fishing rod",
            "Footprint (unobtainable item)",
            "Forester's ration",
            "Forestry basket",
            "Forestry boots",
            "Forestry hat",
            "Forestry kit",
            "Forestry legs",
            "Forestry top",
            "Forinthry sigil",
            "Forlorn boot",
            "Fossilised branch",
            "Fossilised leaf",
            "Fossilised mushroom",
            "Fossilised roots",
            "Fossilised stump",
            "Four barrels",
            "Fox (pet)",
            "Fox (Recruitment Drive)",
            "Fox whistle",
            "Fractured crystal (Song of the Elves)",
            "Fragment 1",
            "Fragment 2",
            "Fragment 3",
            "Fremennik blade",
            "Fremennik helm",
            "Fremennik kilt",
            "Fremennik sea boots 1",
            "Fremennik sea boots 2",
            "Fremennik sea boots 3",
            "Fremennik sea boots 4",
            "Fremennik shield",
            "Fresh chocolate mix",
            "Fresh crab claw",
            "Fresh crab shell",
            "Fresh fish",
            "Fresh start helper",
            "Frog mask",
            "Frog slippers",
            "Frog spawn",
            "Frog token",
            "Frog-leather body",
            "Frog-leather boots",
            "Frog-leather chaps",
            "Frogburger",
            "Frogspawn gumbo",
            "Frozen bucket",
            "Frozen key (The Fremennik Trials)",
            "Frozen key (The Frozen Door)",
            "Frozen key piece (armadyl)",
            "Frozen key piece (bandos)",
            "Frozen key piece (saradomin)",
            "Frozen key piece (zamorak)",
            "Frozen tablet",
            "Fruity chocolate mix",
            "Fruity easter egg",
            "Frying pan",
            "Full folder",
            "Full kettle",
            "Fungicide",
            "Fungicide spray",
            "Funky shaped log",
            "Fur head",
            "Fury ornament kit",
            "Fuse",
            "Gadderhammer",
            "Gang meeting info",
            "Garden brush",
            "Gardening boots",
            "Gardening trowel",
            "Gas mask",
            "Gauntlet cape",
            "Gem bag",
            "Ghommal's avernic defender 5",
            "Ghommal's avernic defender 6",
            "Ghommal's hilt 1",
            "Ghommal's hilt 2",
            "Ghommal's hilt 3",
            "Ghommal's hilt 4",
            "Ghommal's hilt 5",
            "Ghommal's hilt 6",
            "Ghommal's lucky penny",
            "Ghost buster 500",
            "Ghostly cloak",
            "Ghostly hood",
            "Ghostly robe (top)",
            "Ghostspeak amulet",
            "Ghrazi rapier (beta)",
            "Giant boot",
            "Giant boulder",
            "Giant bronze dagger",
            "Giant easter egg",
            "Giant egg sac",
            "Giant frog legs",
            "Giant key",
            "Giant nib",
            "Giant pen",
            "Giant pouch",
            "Giant present",
            "Giant rat bone",
            "Giant seaweed",
            "Giant squirrel",
            "Giant stopwatch",
            "Gilded cross",
            "Gilded d'hide body",
            "Gilded d'hide chaps",
            "Gilded dragonhide set",
            "Gingerbread gnome",
            "Glarial's pebble",
            "Glassblowing pipe",
            "Glistening tear",
            "Gloves of darkness",
            "Gloves of ruin",
            "Glowing dagger",
            "Glowing fungus",
            "Gnome cake",
            "Gnome child (item)",
            "Gnome child backpack",
            "Gnome child hat",
            "Gnome child icon",
            "Gnome child mask",
            "Gnome child plush",
            "Gnome goggles",
            "Gnome scarf",
            "Gnomish firelighter",
            "Goat horn dust",
            "Goblin book",
            "Goblin decorations",
            "Goblin mask",
            "Goblin paint cannon",
            "Godsword blade",
            "Godsword shard 1",
            "Godsword shard 2",
            "Godsword shard 3",
            "Godsword shards 1 & 2",
            "Godsword shards 1 & 3",
            "Godsword shards 2 & 3",
            "Gold fragment",
            "Gold helmet",
            "Gold leaf",
            "Gold paint",
            "Gold speedrun trophy",
            "Golden goblin",
            "Golden pheasant egg",
            "Golden prospector boots",
            "Golden rings",
            "Golden tench",
            "Golden wool",
            "Golovanova fruit top",
            "Gorak claw powder",
            "Gorak claws",
            "Gorgeous orange lily seed",
            "Gout tuber",
            "Goutweedy lump",
            "Graahk fur",
            "Graahk headdress",
            "Graahk legs",
            "Graahk top",
            "Graceful boots (Adventurer)",
            "Graceful boots (Trailblazer)",
            "Graceful cape (Adventurer)",
            "Graceful gloves (Adventurer)",
            "Graceful hood (Adventurer)",
            "Graceful legs (Adventurer)",
            "Graceful top (Adventurer)",
            "Grain",
            "Grain (Recruitment Drive)",
            "Grain (Tombs of Amascut)",
            "Granite body",
            "Granite boots",
            "Granite clamp",
            "Granite hammer",
            "Granite helm",
            "Granite legs",
            "Granite longsword",
            "Granite maul (or)",
            "Granite shield",
            "Grape seed",
            "Grapple (animation item)",
            "Grass seed",
            "Gravedigger boots",
            "Gravedigger gloves",
            "Gravedigger leggings",
            "Gravedigger mask",
            "Gravedigger top",
            "Greater demon mask",
            "Greater siren",
            "Green banner",
            "Green egg",
            "Green gloop soup",
            "Gregg's eastdoor",
            "Grey wolf fur",
            "Grim reaper hood",
            "Grim reaper's diary",
            "Grimy snake weed",
            "Grinder (animation item)",
            "Ground mud runes",
            "Guardian boots",
            "Guardian essence",
            "Guardian fragments",
            "Guardian statue",
            "Gublinch shards",
            "Gunpowder (Desert Treasure II)",
            "Guppy",
            "Guthan's chainskirt",
            "Guthan's platebody",
            "Guthan's warspear",
            "Guthix crozier",
            "Guthix d'hide body",
            "Guthix d'hide shield",
            "Guthix halo",
            "Guthix mjolnir",
            "Guthix platebody",
            "Guthix staff",
            "Guthixian icon",
            "Haemalchemy volume 1",
            "Haemalchemy volume 2",
            "Hair",
            "Halberd (unobtainable item)",
            "Half a rock",
            "Half moon spectacles",
            "Hallowed bricks",
            "Hallowed focus",
            "Hallowed grapple",
            "Hallowed hammer",
            "Hallowed mark",
            "Hallowed ring",
            "Hallowed symbol",
            "Hallowed token",
            "Ham joint",
            "Ham logo",
            "Hand fan",
            "Hand mirror",
            "Hard hat",
            "Hardcore group iron helm",
            "Hardcore group iron platelegs",
            "Hardcore ironman helm",
            "Hardcore ironman platebody",
            "Hardcore ironman platelegs",
            "Hardleather body",
            "Hardy gout tuber",
            "Hardy gout tubers",
            "Harpoon",
            "Harry's cutlass",
            "Hat eyepatch",
            "Hat of the eye",
            "Haunted wine bottle",
            "Hay sack",
            "Hazeel's mark",
            "Headless head",
            "Healer hat",
            "Healer icon",
            "Healing vial",
            "Heart crystal",
            "Heavy ballista (or)",
            "Heavy ballista ornament kit",
            "Heavy frame",
            "Hefty tax bag",
            "Helix fossil",
            "Hellpuppy",
            "Helm of neitiznot (or)",
            "Helm of raedwald",
            "Helmet fragment",
            "Helpful device (RuneScape 2 Beta)",
            "Herb sack",
            "Herbal tincture",
            "Herbi",
            "Heron",
            "Hespori bark",
            "Hespori seed",
            "Highwayman mask",
            "Hill giant club",
            "Histories of the hallowland",
            "History and hearsay",
            "Holos mushroom",
            "Holos powder",
            "Holy elixir",
            "Holy force",
            "Holy mould",
            "Holy ornament kit",
            "Holy sandals",
            "Holy sanguinesti staff",
            "Holy scythe of vitur",
            "Holy wraps",
            "Holy wrench",
            "Honey locust",
            "Hood of darkness",
            "Hood of ruin",
            "Hoop",
            "Hoop snake (item)",
            "Hornwood helm",
            "Horogothgar key",
            "Hosidius banner",
            "Hosidius scarf",
            "Hot kettle",
            "Hourglass (2014 Halloween event)",
            "Hourglass (Recruitment Drive)",
            "Huge snowball",
            "Human eye",
            "Humongous snowball",
            "Hunk of crystal",
            "Hunter kit",
            "Hunter's honour",
            "Hunters' crossbow",
            "Hunters' talisman",
            "Huzamogaarb key",
            "Hydra tail",
            "Hydra's claw",
            "Hydra's eye",
            "Hydra's fang",
            "Hydra's heart",
            "Ians helper (RuneScape 2 Beta)",
            "Iasor seed",
            "Iban's dove",
            "Iban's shadow",
            "Iban's staff",
            "Iban's staff (u)",
            "Ice arrows",
            "Icosahedron",
            "Icthlarin's hood (tier 5)",
            "Icthlarin's shroud (tier 1)",
            "Icthlarin's shroud (tier 2)",
            "Icthlarin's shroud (tier 3)",
            "Icthlarin's shroud (tier 4)",
            "Icthlarin's shroud (tier 5)",
            "Idol of balance",
            "Idol of chaos",
            "Idol of light",
            "Illuminating lure",
            "Imcando hammer",
            "Imp mask",
            "Imp repellent",
            "Impling jar",
            "Incantation (2020 Halloween event)",
            "Incomplete heavy ballista",
            "Incomplete light ballista",
            "Infernal ashes",
            "Infernal axe",
            "Infernal cape",
            "Infernal eel",
            "Infernal harpoon",
            "Infernal max cape",
            "Infernal pickaxe",
            "Infinite money bag",
            "Infinity boots",
            "Infinity gloves",
            "Infused wand",
            "Inquisitor's great helm",
            "Inquisitor's great helm (beta)",
            "Inquisitor's hauberk",
            "Inquisitor's hauberk (beta)",
            "Inquisitor's mace",
            "Inquisitor's mace (beta)",
            "Inquisitor's plateskirt",
            "Inquisitor's plateskirt (beta)",
            "Insect repellent",
            "Insulated boots",
            "Intelligence",
            "Intricate pouch",
            "Iron sheet",
            "Iron spit",
            "Ironman helm",
            "Ironman platebody",
            "Ironman platelegs",
            "Ivandis flail",
            "Jack lantern mask",
            "Jad plush",
            "Jad slippers",
            "Jal-nib-rek",
            "Jar generator",
            "Jar of eyes",
            "Javelin shaft",
            "Jester cape",
            "Jewellery (item)",
            "Jewellery of jubilation",
            "Jewels",
            "Jonas mask",
            "Journal page",
            "Jungle demon mask",
            "Juniper charcoal",
            "Juniper logs",
            "Junk",
            "Justiciar chestguard",
            "Justiciar chestguard (beta)",
            "Justiciar faceguard",
            "Justiciar faceguard (beta)",
            "Justiciar leg guards (beta)",
            "Justiciar legguards",
            "Justiciar's hand",
            "Jute fibre",
            "Jute seed",
            "K sigil",
            "Kalphite princess",
            "Kandarin headgear 1",
            "Kandarin headgear 2",
            "Kandarin headgear 3",
            "Kandarin headgear 4",
            "Karambwan vessel",
            "Karamjan monkey (item)",
            "Karamjan rum (banana)",
            "Karamthulhu",
            "Karamthulhu (unobtainable item)",
            "Karidian disguise",
            "Karil's coif",
            "Karil's crossbow",
            "Karil's leatherskirt",
            "Kasonde's journal",
            "Katana",
            "Kbd heads",
            "Kebbit claws",
            "Kebbit spike",
            "Kebbit teeth",
            "Kebbit teeth dust",
            "Kelp",
            "Keris",
            "Kettle",
            "Key (Treasure Trails)",
            "Key master teleport",
            "Key master's key",
            "Key print",
            "Keystone crystal",
            "Kgp id card",
            "Kharidian headpiece",
            "Khazard cell keys",
            "Kindling (2018 Easter event)",
            "Kindling (Chambers of Xeric)",
            "Kitchen knife",
            "Knife (Desert Treasure II)",
            "Knight summoner",
            "Kodai insignia",
            "Korbal herb",
            "Koriff's coif",
            "Koriff's cowl",
            "Koriff's headband",
            "Kovac's grog",
            "Kq head",
            "Kq head (tattered)",
            "Kraken tentacle",
            "Kree'arra (unobtainable item)",
            "Kronos seed",
            "Kruk jr",
            "Kruk's paw",
            "Kurask head",
            "Kyatt fur",
            "Kyatt hat",
            "Kyatt legs",
            "Kyatt top",
            "Ladder top",
            "Large cog",
            "Large fossilised limbs",
            "Large fossilised pelvis",
            "Large fossilised ribs",
            "Large fossilised spine",
            "Large ornate key",
            "Large rock",
            "Large snowball",
            "Large zombie monkey bones",
            "Larran's key",
            "Larupia fur",
            "Larupia hat",
            "Larupia legs",
            "Larupia top",
            "Lava dragon bones",
            "Lava dragon mask",
            "Lava scale",
            "Lava scale shard",
            "Leaf-bladed battleaxe",
            "Leaf-bladed sword",
            "Leaping salmon",
            "Leaping sturgeon",
            "Leaping trout",
            "Leather body",
            "Leather body (g)",
            "Leather chaps",
            "Leather chaps (g)",
            "Lederhosen hat",
            "Lederhosen shorts",
            "Lederhosen top",
            "Left boot",
            "Left eye patch",
            "Left skull half",
            "Legendary cocktail",
            "Legendary red rose seed",
            "Legs",
            "Lemon",
            "Lens mould",
            "Leprechaun charm",
            "Lesser demon mask",
            "Lever (Dorgesh-Kaan Agility Course)",
            "Lever handle",
            "Leviathan's lure",
            "Light box",
            "Light frame",
            "Light infinity colour kit",
            "Light tax bag",
            "Light tuxedo cuffs",
            "Light tuxedo jacket",
            "Light tuxedo shoes",
            "Lil' creator",
            "Lil' zik",
            "Lil'viathan",
            "Lily of the elid",
            "Lime",
            "Limestone brick",
            "Limpwurt root",
            "Limpwurt seed",
            "Linen",
            "Linum tirinum",
            "Lit candle (unobtainable item)",
            "Little nightmare",
            "Little snowball",
            "Lizardman fang",
            "Loach",
            "Lobster pot",
            "Lockpick",
            "Lockpick (Desert Treasure II)",
            "Locust meat",
            "Log basket",
            "Log brace",
            "Long bone",
            "Long kebbit spike",
            "Long pulley beam",
            "Long vine",
            "Longer pulley beam",
            "Loop half of key",
            "Loose cat hair",
            "Lost bag",
            "Lovakengj banner",
            "Lovakengj scarf",
            "Love crossbow",
            "Lucky cutlass",
            "Lumber patch",
            "Lumberjack hat",
            "Lumberjack legs",
            "Lumberjack top",
            "Lumbridge task list",
            "Lump of crystal",
            "Lunar amulet",
            "Lunar boots",
            "Lunar cape",
            "Lunar gloves",
            "Lunar helm",
            "Lunar legs",
            "Lunar ring",
            "Lunar signet",
            "Lunar staff",
            "Lunar torso",
            "Lunch by the lancalliums",
            "M sigil",
            "M'speak amulet",
            "M'speak amulet (unstrung)",
            "Magic beans",
            "Magic butterfly net",
            "Magic carpet (animation item)",
            "Magic egg",
            "Magic fang",
            "Magic lantern",
            "Magic leaves",
            "Magic shortbow (i)",
            "Magic shortbow scroll",
            "Magic whistle",
            "Magical pumpkin",
            "Magma helm",
            "Magnet (Recruitment Drive)",
            "Magus icon",
            "Magus ring",
            "Magus ring (beta)",
            "Magus vestige",
            "Mahogany seed",
            "Malediction ward (or)",
            "Malicious ashes",
            "Man speak amulet",
            "Mangled extract",
            "Maniacal monkey (item)",
            "Maoma's full helm",
            "Maoma's great helm",
            "Maoma's med helm",
            "Map part (Lozar)",
            "Map part (Melzar)",
            "Map part (Thalzar)",
            "Map scrap",
            "Maple leaves",
            "Maple seed",
            "Marble amulet",
            "Marble block",
            "Marigold seed",
            "Marigolds",
            "Marionette handle",
            "Mark of grace",
            "Marlo's crate",
            "Mask of balance",
            "Mask of ranul",
            "Mask of rebirth",
            "Masori armour set (f)",
            "Masori assembler",
            "Masori assembler max hood",
            "Masori body",
            "Masori body (f)",
            "Masori chaps",
            "Masori chaps (f)",
            "Masori crafting kit",
            "Masori mask",
            "Masori mask (f)",
            "Master scroll book",
            "Master wand",
            "Meat tenderiser",
            "Meaty chocolate mix",
            "Meaty easter egg",
            "Medical gown",
            "Medium cog",
            "Medium fossilised pelvis",
            "Medium fossilised ribs",
            "Medium fossilised skull",
            "Medium fossilised spine",
            "Medium pouch",
            "Medivaemia blossom",
            "Menaphite ornament kit",
            "Menaphite purple hat",
            "Menaphite red hat",
            "Merfolk trident",
            "Mermaid's tear",
            "Message (fireplace)",
            "Message (Romeo & Juliet)",
            "Message (Theatre of Blood)",
            "Metal bar",
            "Metal feather",
            "Metal sheet",
            "Metal spade",
            "Meter",
            "Miazrqa's pendant",
            "Mime legs",
            "Mime mask",
            "Mime top",
            "Mind core",
            "Minecart control scroll",
            "Mining helmet",
            "Mining prop",
            "Minnow",
            "Mint cake",
            "Mirror",
            "Mirror (Tombs of Amascut)",
            "Mirror shield",
            "Mist battlestaff",
            "Mith grapple",
            "Mith grapple (unf)",
            "Mith grapple tip",
            "Model ship",
            "Mole claw",
            "Mole skin",
            "Mole slippers",
            "Monkey (Monkey Madness I)",
            "Monkey (Monkey Madness II)",
            "Monkey corpse",
            "Monkey dentures",
            "Monkey paw",
            "Monkey skin",
            "Monkey skull",
            "Monkey tail",
            "Monocle",
            "Moonclan armour",
            "Moonclan boots",
            "Moonclan cape",
            "Moonclan gloves",
            "Moonclan hat",
            "Moonclan helm",
            "Moonclan skirt",
            "Mop",
            "Morrigan's javelin (bh)",
            "Morrigan's javelin (Last Man Standing)",
            "Morrigan's leather body (bh)",
            "Morrigan's leather body (c)",
            "Morrigan's leather chaps (bh)",
            "Morrigan's leather chaps (c)",
            "Morrigan's throwing axe (bh)",
            "Mort myre fungus",
            "Mort myre pear",
            "Mort myre stem",
            "Morytania legs 1",
            "Morytania legs 2",
            "Morytania legs 3",
            "Morytania legs 4",
            "Mosschin's bone",
            "Mossy key",
            "Mottled eel",
            "Mourner top",
            "Mourner trousers",
            "Mouse toy",
            "Mud",
            "Mudskipper hat",
            "Mudskipper hide",
            "Mulch",
            "Mulled pine",
            "Mummy's body",
            "Mummy's feet",
            "Mummy's hands",
            "Mummy's head",
            "Mummy's legs",
            "Musca mushroom",
            "Musca powder",
            "Museum map",
            "Mushroom",
            "Mushroom potato",
            "Mushroom spore",
            "Mushrooms",
            "Music cape",
            "Music sheet",
            "Musketeer hat",
            "Musketeer pants",
            "Musketeer tabard",
            "Mysterious orb (X Marks the Spot)",
            "Mystic cards",
            "Mystic hat (or)",
            "Mystic mist staff",
            "Mystic robe bottom (or)",
            "Mystic robe top (or)",
            "Mystic set (dusk)",
            "Mythical cape",
            "Nail beast nails",
            "Narogoshuun key",
            "Nasturtium seed",
            "Nasturtiums",
            "Nature nerve",
            "Nature offerings",
            "Necklace mould",
            "Necklace of anguish",
            "Necklace of anguish (or)",
            "Necromancy book",
            "Neitiznot faceguard",
            "Neitiznot shield",
            "Nettles",
            "Neutralising potion",
            "Nexling",
            "Nieve (item)",
            "Nightmare staff",
            "Nightmare staff (beta)",
            "Nihil horn",
            "Nihil shard",
            "Nistirio's manifesto",
            "No eggs",
            "Noon",
            "Noose wand",
            "Normal snowball",
            "Normal tax bag",
            "Nose peg",
            "Nuff's certificate",
            "Nuggets",
            "Nuggets (2018 Easter event)",
            "Numulite",
            "Nunchaku",
            "Nurse hat",
            "Oak bird house",
            "Oak leaves",
            "Oak roots",
            "Obsidian amulet",
            "Obsidian armour set",
            "Obsidian helmet",
            "Obsidian platebody",
            "Obsidian platelegs",
            "Occult necklace (or)",
            "Occult ornament kit",
            "Odd bird seed",
            "Odd key",
            "Odd spectacles",
            "Odd stuffed snake",
            "Oddskull",
            "Odium ward (or)",
            "Ogre artefact",
            "Ogre artefact (The Corsair Curse)",
            "Ogre bow",
            "Ogre relic",
            "Ohn's diary",
            "Oil can",
            "Oil lamp",
            "Oil lantern",
            "Oil lantern frame",
            "Old boot",
            "Old chipped vase",
            "Old coin",
            "Old demon mask",
            "Old man's coffin",
            "Old school bond",
            "Old symbol",
            "Old tablet",
            "Old wool",
            "Oldschool jumper",
            "Olmlet",
            "Omega egg",
            "One barrel",
            "Onion seed",
            "Onyx amulet",
            "Onyx amulet (u)",
            "Onyx necklace",
            "Orange",
            "Orange tree seed",
            "Orb",
            "Orb of light (Song of the Elves)",
            "Orb of protection",
            "Orbs of protection",
            "Ore pack (Giants' Foundry)",
            "Ore pack (Volcanic Mine)",
            "Origami balloon",
            "Ornament",
            "Ornate boots",
            "Ornate cape",
            "Ornate gloves",
            "Ornate helm",
            "Ornate legs",
            "Ornate lockbox",
            "Ornate maul handle",
            "Ornate top",
            "Osmumten's coin",
            "Osmumten's fang",
            "Osmumten's fang (or)",
            "Overseer's book",
            "Oyster",
            "Oyster pearls",
            "Padded spoon",
            "Paddle",
            "Page 1",
            "Page 2",
            "Page 3",
            "Pages (unobtainable item)",
            "Paintbrush",
            "Panning tray",
            "Pantaloons",
            "Papaya fruit",
            "Papaya tree seed",
            "Parasitic egg",
            "Parchment (Contact!)",
            "Parchment (Olaf's Quest)",
            "Part garden pie (onion)",
            "Part garden pie (tomato)",
            "Part wild pie (raw chompy)",
            "Partyhat & specs",
            "Pay-dirt",
            "Peach",
            "Pear tree sapling",
            "Pearl barbarian rod",
            "Pearl fly fishing rod",
            "Penance skirt",
            "Penguin bongos",
            "Penguin mask",
            "Pentamid",
            "Perfect gingerbread",
            "'perfect' ring",
            "Perfected shadow torch",
            "Pet chaos elemental",
            "Pet dark core",
            "Pet general graardor",
            "Pet k'ril tsutsaroth",
            "Pet kraken",
            "Pet kree'arra",
            "Pet penance queen",
            "Pet smoke devil",
            "Pet snakeling",
            "Pet zilyana",
            "Pete's candlestick",
            "Pharaoh's sceptre",
            "Pheasant (pet)",
            "Pheasant boots",
            "Pheasant cape",
            "Pheasant egg",
            "Pheasant hat",
            "Pheasant legs",
            "Pheasant tail feathers",
            "Phoenix",
            "Phoenix crossbow",
            "Pickaxe handle",
            "Pickled brain",
            "Picture",
            "Piece of railing",
            "Pieces of eight",
            "Pigeon cage",
            "Pine tree seed",
            "Pineapple ring",
            "Pipe (Elemental Workshop II)",
            "Pipe (Tower of Life)",
            "Pipe ring",
            "Pipe section",
            "Pirate boots",
            "Pirate hat & patch",
            "Pirate's hook",
            "Piscarilius banner",
            "Piscarilius scarf",
            "Pith helmet",
            "Plague jacket",
            "Plague sample",
            "Plague trousers",
            "Plank",
            "Plank sack",
            "Plaster fragment",
            "Poet's jacket",
            "Poison (item)",
            "Poison chalice",
            "Poisoned dart(p)",
            "Poisoned egg",
            "Poisoned meat",
            "Polished blue gem",
            "Polished buttons",
            "Polishing rock",
            "Portable waystone",
            "Portal talisman (death)",
            "Portal talisman (law)",
            "Portal talisman (nature)",
            "Portrait",
            "Pot of quicklime",
            "Potato cactus",
            "Potato cactus seed",
            "Potato seed",
            "Potato with butter",
            "Potato with cheese",
            "Potion note",
            "Pottery",
            "Powerbox",
            "Prayer book",
            "Prayer book (animation item)",
            "Prayer cape",
            "Preform",
            "Premade veg ball",
            "Premium banana",
            "Pressure gauge",
            "Prifddinas teleport",
            "Prince black dragon",
            "Prince leggings",
            "Prince tunic",
            "Princely monkey",
            "Princess blouse",
            "Princess skirt",
            "Prison key (Troll Stronghold)",
            "Prisoner's letter",
            "Prized cake tin",
            "Proboscis",
            "Progress hat",
            "Promissory note (2023 Birthday event)",
            "Prop sword",
            "Prop sword (incomplete)",
            "Propeller hat",
            "Prospector boots",
            "Protest banner",
            "Puddle of slime",
            "Pufferfish",
            "Pugel",
            "Pulley beam",
            "Puppet box",
            "Purple sweets",
            "Pyramid top",
            "Pyromancer boots",
            "Pyromancer garb",
            "Pyromancer hood",
            "Pyromancer robe",
            "Pyromancer set",
            "Quality violet tulip seed",
            "Queen help book",
            "Queen's secateurs",
            "R sigil",
            "Rabbit foot",
            "Rabbit mould",
            "Rabbit snare",
            "Radiant fibre",
            "Railing",
            "Rain bow",
            "Rainbow jumper",
            "Rainbow scarf",
            "Rake",
            "Rake handle",
            "Rake head",
            "Ram skull",
            "Ram skull helm",
            "Ramrod",
            "Ranger boots",
            "Ranger gloves",
            "Ranger hat",
            "Rangers' tights",
            "Rangers' tunic",
            "Ranis' head",
            "Rapier",
            "Rare fossilised limbs",
            "Rare fossilised ribs",
            "Rare fossilised skull",
            "Rare fossilised spine",
            "Rare fossilised tusk",
            "Rat poison",
            "Rat pole",
            "Rat's paper",
            "Rat's tail",
            "Rations (Desert Treasure II)",
            "Raw catfish",
            "Raw cavefish",
            "Raw guppy",
            "Raw rabbit",
            "Raw tetra",
            "Red vine worm",
            "Redeyes' bone",
            "Redwood tree seed",
            "Reindeer hat",
            "Reinforced goggles",
            "Relic (Devious Minds)",
            "Relic part 1",
            "Relic part 2",
            "Relic part 3",
            "Remnant of akkha",
            "Remnant of ba-ba",
            "Remnant of zebak",
            "Requisition note",
            "Research notes (Animal Magnetism)",
            "Resper mushroom",
            "Resper powder",
            "Restored shield (unobtainable item)",
            "Revenant ether",
            "Revitalising idol",
            "Reward token (Gnome Restaurant)",
            "Ribcage piece",
            "Rich chocolate mix",
            "Rich easter egg",
            "Right boot",
            "Right skull half",
            "Ring mould",
            "Ring of 3rd age",
            "Ring of charos",
            "Ring of coins",
            "Ring of endurance",
            "Ring of nature",
            "Ring of shadows",
            "Ring of the elements",
            "Ring of the gods",
            "Ring of the gods (i)",
            "Ring of wealth (i)",
            "Ring of wealth scroll",
            "Ripped mourner trousers",
            "Ritual mulch",
            "Rivets",
            "Roast frog",
            "Robe bottom of darkness",
            "Robe bottom of ruin",
            "Robe bottoms of the eye",
            "Robe of elidinis (bottom)",
            "Robe top of darkness",
            "Robe top of ruin",
            "Robe top of the eye",
            "Robert bust",
            "Robin hood hat",
            "Rock (Castle Wars)",
            "Rock (The Tourist Trap)",
            "Rock (unobtainable item)",
            "Rock cake",
            "Rock golem",
            "Rock hammer",
            "Rock thrownhammer",
            "Rock-shell chunk",
            "Rock-shell helm",
            "Rock-shell legs",
            "Rock-shell plate",
            "Rock-shell shard",
            "Rock-shell splinter",
            "Rocky",
            "Rod mould",
            "Rod with net",
            "Rogue boots",
            "Rogue gloves",
            "Rogue kit",
            "Rogue mask",
            "Rogue top",
            "Rogue trousers",
            "Rogue's revenge",
            "Roll",
            "Rolling pin",
            "Rose (A Kingdom Divided)",
            "Rose tinted lens",
            "Rose's diary",
            "Rosemary",
            "Rosemary seed",
            "Rotten apples",
            "Rotten food",
            "Rotten potato",
            "Royal crown",
            "Royal decree",
            "Royal gown bottom",
            "Royal gown top",
            "Royal sceptre",
            "Rubber tube",
            "Ruined backpack",
            "Ruined catfish",
            "Ruined cavefish",
            "Ruined guppy",
            "Ruined tetra",
            "Rune crossbow (or)",
            "Rune defender ornament kit",
            "Rune scimitar (guthix)",
            "Rune scimitar (saradomin)",
            "Rune scimitar (zamorak)",
            "Rune scimitar ornament kit (guthix)",
            "Rune scimitar ornament kit (saradomin)",
            "Rune scimitar ornament kit (zamorak)",
            "Runed sceptre",
            "Runefest shield",
            "Runner hat",
            "Rusty casket",
            "Rusty scimitar",
            "Sack of coal",
            "Sack pack",
            "Sacred eel",
            "Safety guarantee",
            "Sagacious spectacles",
            "Saika's hood",
            "Saika's shroud",
            "Saika's veil",
            "Sailing book",
            "Salax salt",
            "Salted chocolate mix",
            "Salted easter egg",
            "Salve shard",
            "Samurai boots",
            "Samurai gloves",
            "Samurai greaves",
            "Samurai kasa",
            "Samurai shirt",
            "Sandbag",
            "Sandstone (20kg)",
            "Sandstone (32kg)",
            "Sandstone base",
            "Sandstone body",
            "Sandwich lady hat",
            "Sandwich lady top",
            "Sandworms",
            "Sanguine ornament kit",
            "Sanguine scythe of vitur",
            "Sanguine torva full helm",
            "Sanguine torva platebody",
            "Sanguine torva platelegs",
            "Sanguinesti staff",
            "Santa boots",
            "Santa gloves",
            "Santa jacket",
            "Santa mask",
            "Santa pantaloons",
            "Santa suit",
            "Santa suit (dry)",
            "Santa suit (wet)",
            "Santa's list",
            "Sarachnis chitin",
            "Sarachnis cudgel",
            "Saradomin banner",
            "Saradomin crozier",
            "Saradomin d'hide shield",
            "Saradomin halo",
            "Saradomin hilt",
            "Saradomin mjolnir",
            "Saradomin staff",
            "Saradomin's light",
            "Saradomin's tear",
            "Saragorgak key",
            "Satchel (Desert Treasure II)",
            "Saturated heart",
            "Saucepan",
            "Saw",
            "Sawmill agreement",
            "Sawmill voucher",
            "Scaly blue dragonhide",
            "Scarab mould",
            "Scarecrow",
            "Scarred extract",
            "Scarred scraps",
            "Scarred tablet",
            "Schematic (complete)",
            "Schematic (Dondakan)",
            "Schematics (Dwarf Engineer)",
            "Schematics (Khorvak)",
            "Scorpia's offspring",
            "Scrap paper",
            "Scrapey tree logs",
            "Scroll box (beginner)",
            "Scroll box (easy)",
            "Scroll box (medium)",
            "Scroll of imbuing",
            "Scroll of imbuing (beta)",
            "Scroll of redirection",
            "Scroll sack",
            "Scrumpled paper",
            "Scythe",
            "Scythe of vitur (beta)",
            "Scythe sharpener",
            "Sea slug (item)",
            "Sea slug glue",
            "Sealed letter",
            "Sealed vase",
            "Seaweed sandwich",
            "Seaweed spore",
            "Secateurs attachment",
            "Secateurs blade",
            "Secret page",
            "Secret way map (RuneScape 2 Beta)",
            "Security book",
            "Seed box",
            "Seed dibber",
            "Seed pack",
            "Seercull",
            "Seers icon",
            "Selected iron",
            "Semi-precious blue gem",
            "Seren halo",
            "Serpentine helm",
            "Serpentine visage",
            "Severed leg",
            "Severed leg (The General's Shadow)",
            "Sextant",
            "Shadow blocker",
            "Shadow sword",
            "Shaman mask",
            "Shaman robe",
            "Shantay disclaimer",
            "Shantay pass (item)",
            "Shattered banner",
            "Shattered boots (t1)",
            "Shattered boots (t2)",
            "Shattered boots (t3)",
            "Shattered cane",
            "Shattered gingerbread",
            "Shattered hood (t1)",
            "Shattered hood (t2)",
            "Shattered hood (t3)",
            "Shattered relics dragon trophy",
            "Shattered top (t1)",
            "Shattered top (t2)",
            "Shattered top (t3)",
            "Shattered trousers (t1)",
            "Shayzien banner",
            "Shayzien medpack",
            "Shayzien scarf",
            "Shayzien supply crate",
            "Shed key",
            "Sheep feed",
            "Shield fragment",
            "Shield left half",
            "Shield right half",
            "Shielding potion",
            "Shipping order",
            "Shoes",
            "Short vine",
            "Shortcut key",
            "Shoulder parrot",
            "Shrinking recipe",
            "Shrunk ogleroot",
            "Sickle mould",
            "Sieve",
            "Signed oak bow",
            "Signed portrait",
            "Silly jester boots",
            "Silly jester hat",
            "Silly jester tights",
            "Silly jester top",
            "Silver bottle",
            "Silver paint",
            "Silver partyhat",
            "Silver speedrun trophy",
            "Silverlight key (Captain Rovin)",
            "Silverlight key (Sir Prysin)",
            "Silverlight key (Wizard Traiborn)",
            "Silverware",
            "Simple lockbox",
            "Sin'keth's diary",
            "Sinew",
            "Sinhaza shroud tier 1",
            "Sinhaza shroud tier 2",
            "Sinhaza shroud tier 3",
            "Sinhaza shroud tier 4",
            "Sinhaza shroud tier 5",
            "Siren's staff",
            "Siren's tome",
            "Sirenic tablet",
            "Sithik portrait",
            "Skavid map",
            "Skeletal bottoms",
            "Skeletal helm",
            "Skeletal top",
            "Skeletal visage",
            "Skeleton boots",
            "Skeleton gloves",
            "Skeleton leggings",
            "Skeleton mask",
            "Skeleton monkey (item)",
            "Skeleton shirt",
            "Skewer",
            "Skewer stick",
            "Skewered beast",
            "Skewered bird meat",
            "Skewered chompy",
            "Skewered rabbit",
            "Skis",
            "Skotos",
            "Skull of vet'ion",
            "Skull piece",
            "Skull staple",
            "Slashed book",
            "Slave robe",
            "Slave shirt",
            "Slayer bell",
            "Slayer gloves",
            "Slayer helmet",
            "Slayer helmet (i)",
            "Slayer's enchantment",
            "Slayer's staff",
            "Slayer's staff (e)",
            "Sleeping bag (RuneScape 2 Beta)",
            "Sleeping cap",
            "Slender blade",
            "Slimy key",
            "Slop of compromise",
            "Sluglings",
            "Small chocolate egg",
            "Small cog",
            "Small fossilised limbs",
            "Small fossilised pelvis",
            "Small fossilised ribs",
            "Small fossilised skull",
            "Small pouch",
            "Small snowball",
            "Smelly sock",
            "Smithing catalyst",
            "Smiths boots",
            "Smiths gloves",
            "Smiths gloves (i)",
            "Smiths trousers",
            "Smiths tunic",
            "Smoke battlestaff",
            "Smoke nerve",
            "Smoked chocolate mix",
            "Smoked easter egg",
            "Smoker canister",
            "Smoker fuel",
            "Smolcano",
            "Smouldering pot",
            "Smouldering stone",
            "Snailfeet's bone",
            "Snake basket",
            "Snake basket full",
            "Snake charm",
            "Snake corpse",
            "Snake spine",
            "Snakeskin bandana",
            "Snakeskin body",
            "Snakeskin boots",
            "Snakeskin chaps",
            "Snakeskin vambraces",
            "Snape grass seed",
            "Snothead's bone",
            "Snow (2021 Christmas event)",
            "Snow globe",
            "Snow goggles & hat",
            "Snow imp costume body",
            "Snow imp costume feet",
            "Snow imp costume gloves",
            "Snow imp costume head",
            "Snow imp costume legs",
            "Snow imp costume tail",
            "Snow sprite (item)",
            "Snowball",
            "Snowball (animation item)",
            "Snowman ring",
            "Socks of ruin",
            "Soft clay",
            "Sole",
            "Solus's hat",
            "Soul journey",
            "Soul wars guide",
            "Soulreaper axe",
            "Soulreaper axe (beta)",
            "Sourhog foot",
            "Spade",
            "Spade (RuneScape 2 Beta)",
            "Spade handle",
            "Spade head",
            "Spadeful of coke",
            "Spanner",
            "Spare controls",
            "Spatula",
            "Spear (Last Man Standing)",
            "Special cup",
            "Special spices",
            "Specimen jar",
            "Spectral sigil",
            "Spectral spirit shield",
            "Sphinx's token",
            "Spicy chocolate mix",
            "Spicy easter egg",
            "Spider carcass",
            "Spider hat",
            "Spider snack",
            "Spiked boots",
            "Spiked manacles",
            "Spikes (Barbarian Assault)",
            "Spinach roll",
            "Spined body",
            "Spined chaps",
            "Spined helm",
            "Spinning plate",
            "Spiny helmet",
            "Spirit angler boots",
            "Spirit angler headband",
            "Spirit angler top",
            "Spirit angler waders",
            "Spirit flakes",
            "Split log",
            "Splitbark body",
            "Splitbark boots",
            "Splitbark gauntlets",
            "Splitbark helm",
            "Splitbark legs",
            "Spooky egg",
            "Spork",
            "Sraracha",
            "Staff of balance",
            "Staff of bob the cat",
            "Staff of light",
            "Stake",
            "Stale baguette",
            "Star amulet",
            "Star fragment",
            "Star shard",
            "Star-face",
            "Starter bow",
            "Starter staff",
            "Starter sword",
            "Statius's platebody (bh)",
            "Statius's platebody (c)",
            "Statius's platelegs (bh)",
            "Statius's platelegs (c)",
            "Statius's warhammer (bh)",
            "Statius's warhammer (Last Man Standing)",
            "Statuette (Spirits of the Elid)",
            "Statuette (The Golem)",
            "Steel key ring",
            "Steel studs",
            "Stick (animation item)",
            "Stick (item)",
            "Sticky red goop",
            "Stink bomb",
            "Stinkhorn mushroom",
            "Stodgy mattress",
            "Stolen pendant",
            "Stone bowl",
            "Stone head (Cavity)",
            "Stone left arm",
            "Stone left leg",
            "Stone right arm",
            "Stone right leg",
            "Stone-plaque",
            "Stool",
            "Stool (Games)",
            "Strange box",
            "Strange cipher",
            "Strange fruit",
            "Strange hallowed tome",
            "Strange icon",
            "Strange icon (Desert Treasure II)",
            "Strange implement",
            "Strange old lockpick",
            "Strange potion",
            "Strange skull",
            "Strange slider",
            "Strangled tablet",
            "Strangler serum",
            "Stray dog plush",
            "Strength amulet (t)",
            "Stretched hide",
            "Stripy feather",
            "Strongbones' bone",
            "Stronghold notes",
            "Strung rabbit foot",
            "Studded chaps",
            "Stuffed abyssal head",
            "Stuffed basilisk head",
            "Stuffed big bass",
            "Stuffed big harpoonfish",
            "Stuffed big shark",
            "Stuffed big swordfish",
            "Stuffed cockatrice head",
            "Stuffed crawling hand",
            "Stuffed hydra heads",
            "Stuffed kbd heads",
            "Stuffed kq head",
            "Stuffed kq head (tattered)",
            "Stuffed kurask head",
            "Stuffed monkey",
            "Sturdy beehive parts",
            "Sturdy harness",
            "Sulliuscep cap",
            "Sulphur",
            "Superior calamity breeches",
            "Superior calamity chest",
            "Superior dragon bones",
            "Superior shadow torch",
            "Supplies (Tombs of Amascut)",
            "Supply crate (Mahogany Homes)",
            "Sven's last map",
            "Swamp toad (item)",
            "Swamp weed",
            "Swampbark boots",
            "Swampbark legs",
            "Sweetcorn",
            "Sweetcorn seed",
            "Swift blade",
            "Sword fragment",
            "Sword pommel",
            "Tackle box",
            "Tacks",
            "Tainted essence chunk",
            "Tangleroot",
            "Tankard",
            "Tanning wheel",
            "Tanzanite fang",
            "Tanzanite helm",
            "Target teleport scroll",
            "Tarn's diary",
            "Tattered moon page",
            "Tattered temple page",
            "Tatty graahk fur",
            "Tatty kyatt fur",
            "Tatty larupia fur",
            "Te salt",
            "Tea flask",
            "Tea flask (animation item)",
            "Tea leaves",
            "Teacher wand",
            "Teak seed",
            "Team cape i",
            "Team cape x",
            "Team cape zero",
            "Teasing stick",
            "Technical plans",
            "Tegid's soap",
            "Teleport card",
            "Temple coin",
            "Temple key",
            "Temple key (Desert Treasure II)",
            "Tenacious indigo iris seed",
            "Tenti pineapple",
            "Tephra",
            "Terrifying charm",
            "Tetra",
            "Thammaron's sceptre (a)",
            "Thanksgiving dinner",
            "The fisher's flute",
            "The sleeping seven",
            "The stuff",
            "Thieves' armband",
            "Thieving bag",
            "Thread",
            "Thread of elidinis",
            "Three barrels",
            "Throwing rope",
            "Tiara mould",
            "Tile",
            "Timber beam",
            "Tiny fish",
            "Tiny net",
            "Tiny tempor",
            "To-do list",
            "Toad batta",
            "Toad crunchies",
            "Tokkul",
            "Toktz-mej-tal",
            "Toktz-xil-ak",
            "Toktz-xil-ek",
            "Toktz-xil-ul",
            "Tomato seed",
            "Toolkit",
            "Toolkit (Castle Wars)",
            "Tooth half of key",
            "Top hat",
            "Top hat & monocle",
            "Top of sceptre",
            "Torag's hammers",
            "Torag's platebody",
            "Torch (animation item, Sea Slug)",
            "Torch (animation item, Trouble Brewing)",
            "Torch (unobtainable item)",
            "Tormented bracelet",
            "Tormented bracelet (or)",
            "Tormented ornament kit",
            "Torn prayer scroll",
            "Torn robe (bottom)",
            "Torso",
            "Torture ornament kit",
            "Torva full helm",
            "Torva platebody",
            "Torva platelegs",
            "Totem",
            "Touch paper",
            "Toxic blowpipe",
            "Toxic staff of the dead",
            "Toy cat",
            "Toy doll",
            "Toy mouse",
            "Toy ship",
            "Toy soldier",
            "Trading sticks",
            "Trailblazer axe",
            "Trailblazer banner",
            "Trailblazer boots (t1)",
            "Trailblazer cane",
            "Trailblazer globe",
            "Trailblazer graceful ornament kit",
            "Trailblazer harpoon",
            "Trailblazer pickaxe",
            "Trailblazer rug",
            "Trailblazer tool ornament kit",
            "Trailblazer top (t1)",
            "Trailblazer top (t2)",
            "Trailblazer top (t3)",
            "Trailblazer trousers (t1)",
            "Trailblazer trousers (t2)",
            "Trailblazer trousers (t3)",
            "Transdimensional notes",
            "Translated note",
            "Translated notes",
            "Trap disarmer",
            "Trap disarmer blueprint",
            "Treasure map",
            "Treasure scroll",
            "Treasure stone",
            "Tree skirt",
            "Tree top",
            "Tri-jester hat",
            "Triangle sandwich",
            "Trinket of advanced weaponry",
            "Tristan bust",
            "Trolley",
            "Trouver parchment",
            "Trowel",
            "Tullia's letter",
            "Tumeken's guardian",
            "Tumeken's shadow",
            "Tuna potato",
            "Twisted ancestral colour kit",
            "Twisted ancestral robe bottom",
            "Twisted ancestral robe top",
            "Twisted banner",
            "Twisted bow",
            "Twisted buckler",
            "Twisted cane",
            "Twisted coat (t1)",
            "Twisted coat (t2)",
            "Twisted coat (t3)",
            "Twisted dragon trophy",
            "Twisted extract",
            "Twisted horns",
            "Twisted trousers (t3)",
            "Twitcher's gloves",
            "Two barrels",
            "Tyras helm",
            "Tzhaar-ket-em",
            "Tzhaar-ket-om",
            "Tzhaar-ket-om (t)",
            "Tzhaar-ket-om ornament kit",
            "Tzrek-jad",
            "Ultimate ironman helm",
            "Ultimate ironman platebody",
            "Ultimate ironman platelegs",
            "Ultor icon",
            "Ultor ring",
            "Ultor ring (beta)",
            "Ultor vestige",
            "Uncharged cell",
            "Uncharged cell (Desert Treasure II)",
            "Uncleaned find",
            "Undead chicken (item)",
            "Undead twigs",
            "Unfinished broad bolts",
            "Unfinished crunchy (chocchip)",
            "Unfired cup",
            "Unholy mould",
            "Unholy symbol (Icthlarin's Little Helper)",
            "Unidentified fragment (harvesting)",
            "Unidentified fragment (production)",
            "Unidentified fragment (skilling)",
            "Unidentified large fossil",
            "Unidentified medium fossil",
            "Unidentified rare fossil",
            "Unidentified small fossil",
            "Unsealed letter",
            "Unsired",
            "Unstamped letter",
            "Unstrung comp bow",
            "Unstrung emblem",
            "Unstrung heavy ballista",
            "Unstrung light ballista",
            "Unstrung symbol",
            "Unusual armour",
            "Uri's hat",
            "Ursine chainmace",
            "Ursine chainmace (beta)",
            "Urt salt",
            "V's shield",
            "Valve wheel",
            "Vampyric essence",
            "Vampyrium vambraces",
            "Vanilla pod",
            "Varrock armour 1",
            "Varrock armour 2",
            "Varrock armour 3",
            "Varrock armour 4",
            "Vase lid",
            "Veg ball",
            "Venator bow",
            "Venator icon",
            "Venator ring",
            "Venator shard",
            "Venator vestige",
            "Venenatis spiderling",
            "Venom gland",
            "Ventor ring (beta)",
            "Verac's brassard",
            "Verac's brassard (Last Man Standing)",
            "Verac's flail",
            "Verac's flail (Last Man Standing)",
            "Very broken gingerbread",
            "Very long rope",
            "Vesta's chainbody (bh)",
            "Vesta's chainbody (c)",
            "Vesta's longsword (bh)",
            "Vesta's plateskirt (bh)",
            "Vesta's plateskirt (c)",
            "Vesta's spear (bh)",
            "Vet'ion jr.",
            "Victor's cape (1)",
            "Viggora's chainmace",
            "Vile ashes",
            "Virtus mask",
            "Virtus robe bottom",
            "Virtus robe top",
            "Vodka",
            "Void knight mace",
            "Void knight robe (or)",
            "Void knight top (or)",
            "Void mage helm (or)",
            "Void melee helm (or)",
            "Void ranger helm (or)",
            "Voidwaker blade",
            "Voidwaker gem",
            "Voidwaker hilt",
            "Volatile mineral",
            "Volcanic mine teleport",
            "Volcanic sulphur",
            "Vorkath's stuffed head",
            "Vorki",
            "Vyrewatch legs",
            "Vyrewatch top",
            "Vyvin's wine",
            "Wampum belt",
            "Wand (What Lies Below)",
            "War ship",
            "Warning letter",
            "Warped extract",
            "Warped sceptre",
            "Warrior guild token",
            "Warrior helm",
            "Warrior icon",
            "Washing line",
            "Waste gems",
            "Watch",
            "Water container (Tombs of Amascut)",
            "Water-filled gourd vial",
            "Watermelon",
            "Watermelon slice",
            "Waterskin",
            "Wax",
            "Waxwood log",
            "Waxwood plank",
            "Weathervane pillar",
            "Web cloak",
            "Webweaver bow",
            "Webweaver bow (beta)",
            "Weeds",
            "Weiss fire notes",
            "Wester banana",
            "Wester chocolate",
            "Wester fish",
            "Wester lemon",
            "Wester papaya",
            "Wester spices",
            "Western banner 1",
            "Western banner 2",
            "Western banner 3",
            "Western banner 4",
            "White bed sheets",
            "White lily",
            "White lily seed",
            "White pearl",
            "White pearl seed",
            "White tree fruit",
            "White tree sapling",
            "White tree shoot",
            "Whitefish",
            "Wig",
            "Wilderness crabs teleport",
            "Wilderness sword 1",
            "Wilderness sword 2",
            "Wilderness sword 3",
            "Wilderness sword 4",
            "Willow bird house",
            "Willow seed",
            "Windswept logs",
            "Wintumber tree",
            "Wise old man's santa hat",
            "Wisp",
            "Witch boots",
            "Witch cape",
            "Witch hat",
            "Witch robes",
            "Witch top",
            "Witchwood icon",
            "Withered note",
            "Woad leaf",
            "Woad seed",
            "Wolf cloak",
            "Wolf mask",
            "Wolf whistle",
            "Wolfbane",
            "Wooden cat",
            "Wooden pole",
            "Wooden shield (Weapons rack)",
            "Wooden spoon",
            "Woolly hat",
            "Word translations",
            "Worm",
            "Worm batta",
            "Worm crunchies",
            "Wrath nerve",
            "Wrench",
            "Wyvern bones",
            "Wyvern visage",
            "Xeric's talisman",
            "Xerician fabric",
            "Xerician hat",
            "Xerician robe",
            "Xerician top",
            "Yak-hide",
            "Yak-hide armour (legs)",
            "Yak-hide armour (top)",
            "Yellow egg",
            "Yew leaves",
            "Yew seed",
            "Yewnock's notes",
            "Yin yang amulet",
            "Yo-yo",
            "Youngllef",
            "Yurkolgokh key",
            "Z sigil",
            "Zaff's instructions",
            "Zalcano shard",
            "Zamorak banner",
            "Zamorak crozier",
            "Zamorak d'hide body",
            "Zamorak d'hide shield",
            "Zamorak halo",
            "Zamorak hilt",
            "Zamorak mjolnir",
            "Zamorak platebody",
            "Zamorak staff",
            "Zamorak stole",
            "Zamorakian hasta",
            "Zamorakian spear",
            "Zarosian emblem",
            "Zaryte crossbow",
            "Zaryte vambraces",
            "Zealot's boots",
            "Zealot's helm",
            "Zealot's robe bottom",
            "Zealot's robe top",
            "Zenyte amulet",
            "Zenyte amulet (u)",
            "Zenyte bracelet",
            "Zenyte necklace",
            "Zenyte ring",
            "Zenyte shard",
            "Zogre bones",
            "Zombie boots",
            "Zombie gloves",
            "Zombie head",
            "Zombie head (Treasure Trails)",
            "Zombie mask",
            "Zombie monkey (item)",
            "Zombie shirt",
            "Zombie trousers",
            "Zul-andra teleport",
            "Zulrah's scales",
            "Zuriel's robe bottom (bh)",
            "Zuriel's robe bottom (c)",
            "Zuriel's robe top (bh)",
            "Zuriel's robe top (c)",
            "Zuriel's staff (bh)"
        ]

    @commands.Cog.listener()
    async def on_ready(self):
        await self.tree_sync()

    async def tree_sync(self):
        try:
            synced = await self.bot.tree.sync()
            print(f"Synced {len(synced)} commands")

        except Exception as e:
            print(e)

    @commands.command()
    async def tree(self, ctx):
        if ctx.author.id != self.bot.settings.moist_id:
            return await ctx.send("no tree")

        await self.tree_sync()
        return await ctx.send("tree sync")

    @commands.command()
    async def funbox(self, ctx):
        return await ctx.send(
            '[{"regionId":15184,"regionX":26,"regionY":42,"z":1,"color":"#FFFFFF00"},{"regionId":15184,"regionX":24,"regionY":40,"z":1,"color":"#FFFFFF00"},{"regionId":15184,"regionX":23,"regionY":39,"z":1,"color":"#FF3AFF20"},{"regionId":15184,"regionX":26,"regionY":39,"z":1,"color":"#FF3AFF20"},{"regionId":15184,"regionX":29,"regionY":39,"z":1,"color":"#FF3AFF20"},{"regionId":15184,"regionX":29,"regionY":42,"z":1,"color":"#FF3AFF20"},{"regionId":15184,"regionX":29,"regionY":45,"z":1,"color":"#FF3AFF20"},{"regionId":15184,"regionX":26,"regionY":45,"z":1,"color":"#FF3AFF20"},{"regionId":15184,"regionX":23,"regionY":45,"z":1,"color":"#FF3AFF20"},{"regionId":15184,"regionX":23,"regionY":42,"z":1,"color":"#FF3AFF20"},{"regionId":15696,"regionX":32,"regionY":42,"z":1,"color":"#FFFFFF00"},{"regionId":15696,"regionX":37,"regionY":45,"z":1,"color":"#FFFF0000"},{"regionId":15696,"regionX":37,"regionY":44,"z":1,"color":"#FFFF0000"},{"regionId":15696,"regionX":37,"regionY":43,"z":1,"color":"#FFFF0000"},{"regionId":15696,"regionX":37,"regionY":42,"z":1,"color":"#FFFF0000"},{"regionId":15696,"regionX":37,"regionY":41,"z":1,"color":"#FFFF0000"},{"regionId":15696,"regionX":27,"regionY":45,"z":1,"color":"#FFFF0000"},{"regionId":15696,"regionX":27,"regionY":44,"z":1,"color":"#FFFF0000"},{"regionId":15696,"regionX":27,"regionY":43,"z":1,"color":"#FFFF0000"},{"regionId":15696,"regionX":27,"regionY":42,"z":1,"color":"#FFFF0000"},{"regionId":15696,"regionX":27,"regionY":41,"z":1,"color":"#FFFF0000"}]')

    @commands.command(aliases=["next"], hidden=True)
    async def next_level(self, ctx, *args):
        try:
            gamer, info = self.parse_input(ctx, args)

        except NoName:
            return await NoName.message(NoName(), ctx, self.seperator)

        print(type(info))

    @commands.command(aliases=["when"])
    async def when_calculator(self, ctx,
                              percent: str = commands.parameter(description="Percent as a whole number"),
                              rate: str = commands.parameter(description="Drop rate as a fraction")):
        """
        Sends the kc needed to reach the inputted percent chance for the inputted drop rate
        """
        try:
            if len(percent) <= 2:
                divide_by = 100

            else:
                divide_by = 10 ** (len(percent))

            probability = float(percent) / divide_by

        except (ValueError, IndexError):
            return await ctx.send("Error! example usage would be...\n"
                                  "!when percent rate\n"
                                  "!when 50 1/300")

        try:
            decimal_rate = eval(rate)  # Evaluate the rate string (e.g., "1/10" becomes 0.1)

        except ZeroDivisionError:
            return await ctx.send("Why divide by zero")

        kc_needed = log(1 - probability) / log(1 - decimal_rate)

        msg = f"{ceil(kc_needed)} kc for {probability * 100}% chance"

        return await ctx.send(msg)

    @commands.command(aliases=["drycalc", "dry"])
    async def dry_calculator(self, ctx, *args):

        try:
            current_kc = int(args[0])
            rate = args[1]

        except (ValueError, IndexError):
            return await ctx.send("Error! example usage would be...\n"
                                  "!dry kc rate\n"
                                  "!dry 10 1/100")

        try:
            decimal_rate = eval(rate)  # Evaluate the rate string (e.g., "1/10" becomes 0.1)

        except ZeroDivisionError:
            return await ctx.send("Why divide by zero")

        # Calculate the probability
        probability = 1 - (1 - decimal_rate) ** current_kc

        return await ctx.send(probability)

    @commands.command()
    async def max(self, ctx, *date):
        """Returns xp needed a day to max on certain date"""
        # jan 1 2024
        try:
            gamers, date = self.parse_input(ctx, date)

        except NoName:
            return await NoName.message(NoName(), ctx, self.seperator)

        try:
            date_object = datetime.strptime(date, "%b %d %Y")

        except ValueError:
            return await ctx.send("Bad date format - example format 'jan 1 2024'")

        days_til = date_object - datetime.utcnow()
        days_til = int(str(days_til.days))
        days_til += 1
        for gamer in gamers:
            status, stats_dict = await get_stats(gamer)

            if status != 200:
                print(f"Error in command !max: {status}\n"
                      f"account - {gamer} -")
                return

            xp_a_day = {}
            total_xp = 0
            for stat in stats_dict:
                if stats_dict[stat]["level"] >= 99:
                    continue
                try:
                    stat_xp = int((xp_dict["99"] - stats_dict[stat]["xp"]) / days_til) + 1

                except ZeroDivisionError:
                    return await ctx.send("pick a date in the future")

                if stat_xp < 0:
                    return await ctx.send("pick a date in the future")

                total_xp += stat_xp
                xp_a_day[stat] = stat_xp

            xp_a_day["Total xp a day"] = total_xp

            embed_msg = Embed(title=f"{gamer} - max on {date}")

            for skill in xp_a_day:
                embed_msg.add_field(name=skill, value=f"{xp_a_day[skill]:,}", inline=True)

            await ctx.send(embed=embed_msg)

    # noinspection PyUnresolvedReferences
    @app_commands.command(name="osrs", description="manage osrs accounts")
    @app_commands.describe(options='Options to choose from')
    @app_commands.choices(options=[
        discord.app_commands.Choice(name='View', value=1),
        discord.app_commands.Choice(name='Add', value=2),
        discord.app_commands.Choice(name='Remove', value=3)
    ])
    @app_commands.guild_only()
    async def osrs_slash(self, interaction: discord.Interaction, options: discord.app_commands.Choice[int],
                         account: str = None):
        user_id = str(interaction.user.id)
        if account:
            account = account.strip()

        user_dict = self.gamer_dict['users'].get(user_id, {})
        list_of_accounts = self.gamer_dict['users'].get(user_id, {}).get("osrs", [])

        match options.value:
            case 1:
                if not list_of_accounts:
                    return await interaction.response.send_message("you don't have any osrs accounts set up with me :(")

                output_msg = "Here are the accounts I am keeping track of\n"
                output_msg += "\n".join(list_of_accounts)
                return await interaction.response.send_message(output_msg)

            case 2:
                if account is None:
                    return await interaction.response.send_message("Type an account to add")

                elif account in list_of_accounts:
                    return await interaction.response.send_message("No! That task is already in there")

                list_of_accounts.append(account)
                user_dict['osrs'] = list_of_accounts
                self.gamer_dict['users'][user_id] = user_dict

                with open('storage/league.json', 'w') as f:
                    json.dump(self.gamer_dict, f, indent=1)
                return await interaction.response.send_message(
                    f"Account has successfully been added\n" + "\n".join(list_of_accounts))

            case 3:
                if account is None:
                    return await interaction.response.send_message("Type an account to remove")
                account = self.spell_check(account, list_of_accounts)
                list_of_accounts.remove(account)
                user_dict['osrs'] = list_of_accounts
                self.gamer_dict['users'][user_id] = user_dict

                with open('storage/league.json', 'w') as f:
                    json.dump(self.gamer_dict, f, indent=1)
                return await interaction.response.send_message(f"{account}\n has successfully been removed")

    @commands.group()
    async def osrs(self, ctx, *args):
        """Set osrs account"""
        gamers = " ".join(args).split(",")
        gamers_id = str(ctx.author.id)
        user_dict = self.gamer_dict['users'].get(gamers_id, {})

        clean_gamers = []
        for gamer in gamers:
            if not gamer:
                continue
            clean_gamers.append(gamer.strip())

        user_dict['osrs'] = clean_gamers

        self.gamer_dict['users'][gamers_id] = user_dict

        with open('storage/league.json', 'w') as f:
            json.dump(self.gamer_dict, f, indent=1)
        acc = ['account', 'accounts'][len(clean_gamers) > 1]
        return await ctx.send(f"Osrs {acc} `{'`, `'.join(clean_gamers)}` successfully set as your {acc}")

    @commands.command(aliases=['bj'], hidden=True)
    async def boss_json(self, ctx):
        boss_json = await reader(ctx)
        with open("storage/osrs_bosses.json", "w") as f:
            json.dump(boss_json, f, indent=2)

        return await ctx.send("All done!")

    @commands.command(aliases=['kc'])
    async def boss_kc(self, ctx, *args):
        with open("storage/osrs_bosses.json", "r") as f:
            self.boss_dict = json.load(f)

        try:
            gamers, raw_boss = self.parse_input(ctx, args)

        except NoName:
            return await NoName.message(NoName(), ctx, self.seperator)

        boss = await self.boss_spell_check(raw_boss)

        if ctx.message.author.nick is not None:
            title_name = ctx.message.author.nick

        else:
            title_name = ctx.message.author.name

        embed_msg = Embed(
            title=f'{title_name} - {boss}',
            type='rich',
            description="",
            colour=self.boss_dict[boss]["COLOR"]
        )

        embed_msg.set_thumbnail(url=self.boss_dict[boss]["PNG"])
        gamer_ranks = []
        for gamer in gamers:
            status, stats = await get_boss_kc(gamer)

            if status != 200:
                await ctx.send(f"User `{gamer}` does not exist")
                continue

            try:
                kc = int(stats[boss]['kc'])
                rank = stats[boss]['rank']

            except KeyError:
                kc = 0
                rank = "Unranked"
            gamer_ranks.append([gamer, kc, rank])
        gamer_ranks.sort(key=lambda x: x[1], reverse=True)
        for gamer in gamer_ranks:
            rank = gamer[2]
            try:
                rank = f"{rank:,}"
            except ValueError:
                pass

            embed_msg.add_field(name=gamer[0], value=f"Kill count: {gamer[1]:,}, Rank: {rank}", inline=False)

        await ctx.send(embed=embed_msg)

    @commands.command(aliases=["boss"], hidden=True)
    async def manually_update_boss_name(self, ctx):
        await boss_name()
        return await ctx.send("All done!")

    @commands.command(aliases=["spread"], hidden=True)
    async def manually_update_spreadsheet(self, ctx):
        await self.run_spreadsheets()
        return await ctx.send("All done!")

    @commands.command(hidden=True)
    async def check(self, ctx):
        spread_loop = "on"
        news_loop = "on"
        items_loop = "on"
        account_loop = "on"

        if self.bot.get_cog('Getracker').item_loop.done():
            items_loop = "off"
        if self.spreadsheet.done():
            spread_loop = "off"
        if self.news_loop_check.done():
            news_loop = "off"
        if self.account_data.done():
            account_loop = "off"

        await ctx.send(f"spreadsheet loop is {spread_loop}\n"
                       f"news post loop is {news_loop}\n"
                       f"item loop is {items_loop}\n"
                       f"account data loop is {account_loop}")

    @commands.command()
    async def ranboss(self, ctx):
        bosses = list(self.boss_dict.keys())

        for boss in self.fake_bosses:
            bosses.remove(boss)

        for boss in self.slayer_bosses:
            bosses.remove(boss)

        while bosses:
            budget_boss = random.choice(bosses)

            await ctx.send(f"Do a budget run for {budget_boss}")

            try:
                answer = await self.bot.wait_for('message',
                                                 check=lambda message: message.author == ctx.author and
                                                                       message.channel.id == ctx.channel.id,
                                                 timeout=10)

            except asyncio.exceptions.TimeoutError:
                return await ctx.send("ok enjoy :)")

            if answer.content == "no":
                bosses.remove(budget_boss)

            else:
                return await ctx.send("ok enjoy :)")

        return await ctx.send("okay you're being annoying goodbye")

    @commands.command()
    async def xp(self, ctx, *args):
        try:
            gamers, raw_skill = self.parse_input(ctx, args)

        except NoName:
            return await NoName.message(NoName(), ctx, self.seperator)

        skill = await self.spell_check(raw_skill, self.skills)

        embed_msg = Embed(
            title=f'{skill}',
            type='rich',
            description=""
        )
        gamer_list = []
        for gamer in gamers:
            status, stats_dict = await get_stats(gamer)

            if status != 200:
                await ctx.send(f"couldnt get stats for `{gamer}`")
                continue

            try:
                gamer_lvl = stats_dict[skill]['level']
                gamer_xp = stats_dict[skill]['xp']

            except KeyError:
                gamer_lvl = 1
                gamer_xp = 0

            gamer_list.append([gamer, gamer_lvl, gamer_xp])

        gamer_list.sort(key=lambda x: x[2], reverse=True)

        total_xp = 0
        for gamer in gamer_list:
            total_xp += int(gamer[2])
            embed_msg.add_field(name=gamer[0], value=f"Level: {gamer[1]}, Xp: {gamer[2]:,}", inline=False)

        embed_msg.add_field(name="Total xp", value=f"{total_xp:,}", inline=False)
        return await ctx.send(embed=embed_msg)

    @commands.command()
    async def lookup(self, ctx, *args):
        gamer = " ".join(args)

        status, osrs_hiscores = await get_stats(gamer)
        if status != 200:
            if status == 404:
                return await ctx.send(f"could not find data for user `{gamer}`")
            else:
                return await ctx.send(f"error in !lookup\n"
                                      f"status code {status}")
        url = f"https://sync.runescape.wiki/runelite/player/{gamer}/STANDARD"
        status, gamer_info = await request(url,
                                           headers={"User-Agent": "Message me on discord if you got beef - moists0ck"})
        if status == 200:
            wiki_sync_skills = gamer_info["levels"]
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
            total_level = 0
            for skill in skills:
                if skill == "Overall":
                    continue
                try:
                    if osrs_hiscores[skill]["level"] < wiki_sync_skills[skill]:
                        osrs_hiscores[skill]["level"] = wiki_sync_skills[skill]

                    total_level += osrs_hiscores[skill]["level"]

                except KeyError:
                    osrs_hiscores[skill] = {"level": wiki_sync_skills[skill],
                                            "color": (255, 0, 0)}
                    total_level += osrs_hiscores[skill]["level"]

            osrs_hiscores["Overall"] = {"level": total_level}

        await self.make_skills_page(osrs_hiscores, ctx)

    @commands.command()
    @commands.cooldown(1, 60, commands.BucketType.default)
    async def minlevel(self, ctx):
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
        for table_number in range(0, 24):
            url = f"https://secure.runescape.com/m=hiscore_oldschool/a=12/overall?table={table_number}&rank=2000000#headerHiscores"

            status, html = await request(url)
            if status != 200:
                print(f"kaboom in minlevel - {status}")
                return

            soup = BeautifulSoup(html, 'html.parser')

            # Find all <td> elements with class "right"
            td_elements = soup.find_all('td', class_='right')

            # Iterate through each <td> element
            for td in td_elements:
                # Check if the text of the element is "2,000,000"
                if td.get_text(strip=True) == '2,000,000':
                    # Get the username associated with this <td> element
                    username = td.find_next('td', class_='left').find('a').get_text(strip=True)
                    # Get the next <td> element which contains the level
                    level_td = td.find_next('td', class_='left').find_next_sibling('td')
                    # Get the level associated with this <td> element
                    level = level_td.get_text(strip=True)
                    skills_dict[skills[table_number]] = {'level': int(level.replace(",", ""))}
                    break

        await self.make_skills_page(skills_dict, ctx)

    async def make_skills_page(self, skills_dict, ctx):
        skills = ['Attack',
                  'Hitpoints',
                  'Mining',
                  'Strength',
                  'Agility',
                  'Smithing',
                  'Defence',
                  'Herblore',
                  'Fishing',
                  'Ranged',
                  'Thieving',
                  'Cooking',
                  'Prayer',
                  'Crafting',
                  'Firemaking',
                  'Magic',
                  'Fletching',
                  'Woodcutting',
                  'Runecraft',
                  'Slayer',
                  'Farming',
                  'Construction',
                  'Hunter']

        image_url = "https://imgur.com/DRcMNA3.png"
        status, image_data = await request(image_url, headers={"User-Agent": "Discord bot- moists0ck"})

        try:
            image = Image.open(image_data)

        except AttributeError:
            return await ctx.send(f"{status} picture broken")

        draw = ImageDraw.Draw(image)

        x_pos = 41
        y_pos = 10
        font_size = 20
        font_level = ImageFont.load_default(font_size)
        font_total_level = ImageFont.load_default(10)
        total_level_color = (225, 232, 155)

        count = 0
        overall_number = 0
        for next_row in range(8):
            next_row *= 32
            for next_column in range(3):
                next_column *= 63
                if next_row == 224 and next_column == 126:
                    continue

                try:
                    number = str(skills_dict[skills[count]]['level'])

                except KeyError:
                    number = '1'

                    if skills[count] == "Hitpoints":
                        number = '10'

                try:
                    text_color = skills_dict[skills[count]]["color"]

                except KeyError:
                    text_color = (255, 255, 255)

                if len(number) == 1:
                    next_column += 7

                draw.text((x_pos + next_column, y_pos + next_row), number, fill=text_color, font=font_level)
                count += 1
                overall_number += int(number)

        try:
            overall_number = str(skills_dict['Overall']['level'])

        except KeyError:
            overall_number = ">" + str(overall_number)

        draw.text((153, 248), overall_number, fill=total_level_color, font=font_total_level)

        with BytesIO() as image_binary:
            image.save(image_binary, 'PNG')
            image_binary.seek(0)
            file = discord.File(image_binary, filename="image.png")

        await ctx.send(file=file)

    @commands.command()
    async def who(self, ctx):
        sleep_seconds = 10
        while True:
            item_name = random.choice(self.items)
            url = f"https://oldschool.runescape.wiki/images/{item_name.replace(' ', '_')}_detail.png"

            status, image_data = await request(url)

            if status != 200:
                if status == 404:
                    continue

                else:
                    print(f"error in !who with item {item_name}\n"
                          f"error code {status}")
                    continue

            else:
                break

        color_path = "storage/temp_file_name_color.png"
        pathlib.Path(color_path).write_bytes(image_data.getbuffer().tobytes())
        image = Image.open(image_data).convert("RGBA")

        # Extract the alpha channel and threshold it at 200
        alphaThresh = image.getchannel('A').point(lambda p: 255 if p > 127 else 0)

        # Make a new completely black image same size as original
        res = Image.new('RGB', image.size)

        # Copy across the alpha channel from original
        res.putalpha(alphaThresh)

        with BytesIO() as image_binary:
            res.save(image_binary, 'PNG')

            black_path = "storage/temp_file_name.png"
            pathlib.Path(black_path).write_bytes(image_binary.getbuffer().tobytes())

        embed = Embed(title="What am I?",
                      description=f"You have {sleep_seconds} seconds")
        file = discord.File(black_path, filename="image.png")
        embed.set_image(url=f"attachment://image.png")
        msg = await ctx.send(embed=embed, file=file)

        await asyncio.sleep(sleep_seconds)

        item_url = f"[My wiki page :D](https://oldschool.runescape.wiki/w/{item_name.replace(' ', '_')})"
        new_embed = Embed(title=item_name,
                          description=item_url)
        new_file = discord.File(color_path, filename="image.png")
        new_embed.set_image(url="attachment://image.png")

        await msg.edit(embed=new_embed, attachments=[new_file])

    async def news_post(self):
        current_date = datetime.now()
        year = current_date.year
        month = current_date.month
        url = f"https://secure.runescape.com/m=news/archive?oldschool=1&year={year}&month={month}"
        status, html = await request(url)

        if status != 200:
            print("error in news_post", status)
            return

        soup = BeautifulSoup(html, "html.parser")
        for link in soup.find_all('a'):
            link = link.get('href')
            if not self.this_is_a_news_link(link) or link in self.news:
                continue

            self.news.append(link)
            with open("storage/osrs_news.json", "w") as f:
                json.dump(self.news, f, indent=1)

            real_id = 1164047806806360114
            test_id = 965680218826227812

            status, embed = await self.news_post_embed(link)

            if status != 200:
                print("problem making news post embed", status)

            await self.bot.get_channel(real_id).send(embed=embed)
            await self.bot.get_user(self.bot.settings.moist_id).send(embed=embed)
            await self.bot.get_user(426983855656796162).send(embed=embed)  # clark id

    def this_is_a_news_link(self, url):
        is_link = True
        if "https://secure.runescape.com/m=news/" not in url:
            is_link = False

        elif "1&year" in url:
            is_link = False

        elif "latest_news.rss?oldschool=true" in url:
            is_link = False

        elif "cat=" in url:
            is_link = False

        return is_link

    def parse_input(self, ctx, args):
        raw_info = " ".join(args)
        gamer = None

        try:
            dash_index = raw_info.index(self.seperator)
            data2 = raw_info[:dash_index].strip()
            gamer = [raw_info[dash_index + 2:].strip()]

        except ValueError:
            data2 = raw_info

        if gamer is None:

            try:
                gamer = self.gamer_dict['users'][str(ctx.author.id)]['osrs']

            except KeyError:
                raise NoName

        return gamer, data2

    async def news_post_embed(self, url):
        status, html = await request(url)

        if status != 200:
            return status, None

        soup = BeautifulSoup(html, "html.parser")

        descprtion = soup.find('meta')['content']

        title = soup.title.string
        image_url = soup.find('img', {'alt': title, 'title': title})['src']

        embed = Embed(title=title,
                      url=url,
                      description=descprtion)

        embed.set_thumbnail(url="https://www.runescape.com/img/rsp777/social-share.jpg?1")
        embed.set_image(url=image_url)

        return status, embed

    async def spreadsheet_loop(self):
        await self.bot.wait_until_ready()
        while self is self.bot.get_cog('Runescape'):
            await run_daily_task('08:00:00')
            await self.run_spreadsheets()

    async def account_data_loop(self):
        await self.bot.wait_until_ready()
        while self is self.bot.get_cog('Runescape'):
            await run_daily_task('04:00:45', timezone='UTC')
            await self.collection()

    async def news_loop(self):
        await self.bot.wait_until_ready()
        while self is self.bot.get_cog('Runescape'):
            await self.news_post()
            await asyncio.sleep(600)

    async def run_spreadsheets(self):

        await self.bot.get_user(self.bot.settings.moist_id).send(
            "Good morning!!\nI am gonna update the spreadsheets now :D")
        await self.bot.get_user(self.bot.settings.sarah_id).send(
            "Good morning!!\nI am gonna update the spreadsheets now :D")

        await inputter("The Whisperer", "whisperer kc", compare_rank=1)
        await inputter("The Leviathan", "leviathan kc", compare_rank=1, main="hemeonc")
        await inputter("Duke Sucellus", "duke kc", extra="hemeonc", compare_rank=1000)
        await inputter("Tombs of Amascut: Expert Mode", "toa expert kc", extra="HemeOnc")

    async def boss_spell_check(self, boss):
        distances = []

        for real_boss in self.boss_dict:

            if 'ALIAS' in self.boss_dict[real_boss]:
                boss_alias = self.boss_dict[real_boss]['ALIAS']

                for alias in boss_alias:
                    if alias in boss:
                        return real_boss

            distances.append([real_boss, textdistance.Levenshtein()(real_boss.lower(), boss)])

        return sorted(distances, key=lambda x: x[1])[0][0]

    def spell_check(self, thing_that_need_spellcheck, list_to_use):
        distances = []

        for real_thing_in_list in list_to_use:
            distances.append([real_thing_in_list,
                              textdistance.Levenshtein()(real_thing_in_list.lower(), thing_that_need_spellcheck)])

        return sorted(distances, key=lambda x: x[1])[0][0]

    async def collection(self):
        await self.bot.get_user(self.bot.settings.moist_id).send(
            "Good night!!\nI am gonna collect account data now :D")
        with open("storage/osrs_account_data.json", "r") as f:
            osrs_account_data = json.load(f)

        all_accounts = []
        for gamer in self.gamer_dict['users']:
            try:
                osrs_accounts = self.gamer_dict['users'][gamer]['osrs']
                all_accounts.extend(osrs_accounts)
            except KeyError:
                continue
        _, today = formatted_yesterday_today()
        all_accounts = list(set(all_accounts))
        for account in all_accounts:
            status, info = await request(
                f"https://secure.runescape.com/m=hiscore_oldschool/index_lite.ws?player={account}")

            if status != 200:
                info = "-1,0,0 -1,1,-1 -1,1,-1 -1,1,-1 -1,1,-1 -1,1,-1 -1,1,-1 -1,1,-1 -1,1,-1 -1,1,-1 -1,1,-1 -1,1,-1 -1,1,-1 -1,1,-1 -1,1,-1 -1,1,-1 -1,1,-1 -1,1,-1 -1,1,-1 -1,1,-1 -1,1,-1 -1,1,-1 -1,1,-1 -1,1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1"
                if status == 404:
                    print(f"status 404 in collection, skipping account {account} for data collection")
                else:
                    print(f"error{status} in collection for {account}")

            data = info.splitlines()
            joined_data = ' '.join(data)
            account_dict = osrs_account_data.get(account, {})
            account_dict[today] = joined_data
            osrs_account_data[account] = account_dict

        with open("storage/osrs_account_data.json", 'w') as f:
            json.dump(osrs_account_data, f, indent=2)

    @commands.command(aliases=["collect"], hidden=True)
    async def man_collect(self, ctx):
        if ctx.author.id != self.bot.settings.moist_id:
            return await ctx.send("Shut the fuck up")

        with open("storage/osrs_account_data.json", "r") as f:
            osrs_account_data = json.load(f)

        all_accounts = []
        for gamer in self.gamer_dict['users']:
            try:
                osrs_accounts = self.gamer_dict['users'][gamer]['osrs']
                all_accounts.extend(osrs_accounts)

            except KeyError:
                continue

        _, today = formatted_yesterday_today()

        for account in all_accounts:
            account_dict = osrs_account_data.get(account, {})

            try:
                poopie_pants = account_dict[today]
                continue

            except KeyError:
                status, info = await request(
                    f"https://secure.runescape.com/m=hiscore_oldschool/index_lite.ws?player={account}")

                if status != 200:
                    info = "-1,0,0 -1,1,-1 -1,1,-1 -1,1,-1 -1,1,-1 -1,1,-1 -1,1,-1 -1,1,-1 -1,1,-1 -1,1,-1 -1,1,-1 -1,1,-1 -1,1,-1 -1,1,-1 -1,1,-1 -1,1,-1 -1,1,-1 -1,1,-1 -1,1,-1 -1,1,-1 -1,1,-1 -1,1,-1 -1,1,-1 -1,1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1 -1,-1"
                    if status == 404:
                        print(f"status 404 in collection, skipping account {account} for data collection")
                    else:
                        print(f"error{status} in collection for {account}")

                data = info.splitlines()
                joined_data = ' '.join(data)
                account_dict = osrs_account_data.get(account, {})
                account_dict[today] = joined_data
                osrs_account_data[account] = account_dict

        with open("storage/osrs_account_data.json", 'w') as f:
            json.dump(osrs_account_data, f, indent=2)

        await ctx.send("All done :D")

    @commands.command()
    async def yest(self, ctx, *args):
        try:
            gamers, _ = self.parse_input(ctx, args)

        except NoName:
            return await NoName.message(NoName(), ctx, self.seperator)

        with open("storage/osrs_account_data.json", 'r') as f:
            data = json.load(f)

        formatted_yesterday, formatted_today = formatted_yesterday_today()

        for gamer in gamers:
            gamer_lower = gamer.lower()

            matched_key = next((key for key in data if key.lower() == gamer_lower), None)

            if matched_key:
                try:
                    yesterday_stats = levels_wrapper(data[matched_key][formatted_yesterday].split(" "))
                    today_stats = levels_wrapper(data[matched_key][formatted_today].split(" "))
                    gamer = matched_key

                except KeyError as e:
                    await ctx.send(f"Information for `{e.args[0]}` is not available")
                    continue
            else:
                await ctx.send(f"No data found for `{gamer}`")
                continue

            difference = []

            for stat in yesterday_stats.keys():

                dif_xp = int(today_stats[stat]['xp']) - int(yesterday_stats[stat]['xp'])

                if dif_xp:
                    difference.append([stat, dif_xp])

            if not difference:
                await ctx.send(f"{gamer} gained NO xp on {formatted_yesterday}\n")
                continue

            msg = f"{gamer} xp gained on {formatted_yesterday}\n"
            for dif in difference:
                msg += f"{dif[0]}: {dif[1]:,}\n"

            await ctx.send(msg)

    # noinspection PyUnresolvedReferences
    @app_commands.command(name="quest", description="look up if an osrs account has done a certain quest")
    async def slash_quest(self, interaction: discord.Interaction, quest_name: str, username: str = None):
        if username:
            gamers = [username]
        else:
            gamers = None

        if gamers is None:

            try:
                gamers = self.gamer_dict['users'][str(interaction.user.id)]['osrs']

            except KeyError:
                return await interaction.response.send_message(
                    f"Either add your account to the bot with !osrs or add a name")

        output_msg = ''
        for gamer in gamers:

            url = f"https://sync.runescape.wiki/runelite/player/{gamer}/STANDARD"

            status, gamer_info = await request(url, headers={
                "User-Agent": "Message me on discord if you got beef - moists0ck"})

            if status != 200:
                if status == 400:
                    return await interaction.response.send_message(f"No information was found for the user: `{gamer}`")
                return await interaction.response.send_message(f"something went horribly wrong - error {status}")

            quests = gamer_info["quests"]

            list_of_quests = quests.keys()
            real_quest_name = self.spell_check(quest_name, list_of_quests)

            match int(quests[real_quest_name]):

                case 0:
                    output_msg += f"{gamer} has not started {real_quest_name} :(\n\n"
                    output_msg += await self.quest_reqs(real_quest_name, gamer_info)

                case 1:
                    output_msg += f"{gamer} has started {real_quest_name} but has not finished :/\n"
                    output_msg += await self.quest_reqs(real_quest_name, gamer_info)

                case 2:
                    output_msg += f"{gamer} has finished {real_quest_name} :D\n"

                case _:
                    output_msg += "0_0\n"

        await interaction.response.send_message(output_msg)

    # noinspection PyUnresolvedReferences
    @app_commands.command(name="slayer", description="slayer monsters u can get")
    async def slayer_poop(self, interaction: discord.Interaction, gamer: str):
        url = f"https://sync.runescape.wiki/runelite/player/{gamer}/STANDARD"

        status, gamer_info = await request(url,
                                           headers={"User-Agent": "Message me on discord if you got beef - moists0ck"})
        if status != 200:
            if status == 400:
                return await interaction.response.send_message(f"No information was found for the user: `{gamer}`")
            return await interaction.response.send_message(f"something went horribly wrong - error {status}")

    # noinspection PyUnresolvedReferences
    @app_commands.command(name="maxquest", description="show quests you can do with current level")
    async def max_quest(self, interaction: discord.Interaction, gamer: str):
        url = f"https://sync.runescape.wiki/runelite/player/{gamer}/STANDARD"

        status, gamer_info = await request(url,
                                           headers={"User-Agent": "Message me on discord if you got beef - moists0ck"})
        completed_quests = gamer_info["quests"]
        if status != 200:
            if status == 400:
                return await interaction.response.send_message(f"No information was found for the user: `{gamer}`")
            return await interaction.response.send_message(f"something went horribly wrong - error {status}")

        with open("storage/quest_req.json", "r") as f:
            quest_reqs_dict = json.load(f)

        greenlight_quests = []
        for quest in quest_reqs_dict.keys():
            if await self.can_do_quest_without_training(quest, gamer_info) and completed_quests[quest] in [0, 1]:
                greenlight_quests.append(quest)

        msg = "\n".join(sorted(greenlight_quests))
        msg += f"\nQuests to do: {len(greenlight_quests)}"
        return await interaction.response.send_message(msg)

    async def quest_reqs(self, main_quest, gamer_info):
        with open("storage/quest_req.json", "r") as f:
            quest_reqs_dict = json.load(f)

        quest_reqs_for_the_quest_in_question = quest_reqs_dict[main_quest]

        levels = gamer_info["levels"]
        gamers_quest_status = gamer_info["quests"]

        missing_reqs = ""

        missing_quests = []
        for quest in quest_reqs_for_the_quest_in_question["quests"]:
            if gamers_quest_status[quest] in [0, 1]:
                missing_quests.append(quest)

        for side_quest in missing_quests:
            for quest_needed_for_side_quest in quest_reqs_dict[side_quest]["quests"]:
                if gamers_quest_status[quest_needed_for_side_quest] in [0, 1]:
                    missing_quests.append(quest_needed_for_side_quest)

        missing_quests = list(set(missing_quests))
        missing_quests.append(main_quest)

        missing_levels = {}
        for quest in missing_quests:
            quest_reqs = quest_reqs_dict[quest]
            for skill in quest_reqs["skills"].keys():
                elder_req = missing_levels.get(skill, 1)
                level_needed = quest_reqs["skills"][skill]
                if level_needed > elder_req and level_needed > levels[skill]:
                    missing_levels[skill] = level_needed

        missing_quests.remove(main_quest)

        if missing_levels:
            missing_reqs += f"Levels needed:\n"
            for skill, level in missing_levels.items():
                missing_reqs += f"{level} {skill}\n"

        if missing_quests:
            missing_reqs += "\nQuests needed:\n"
            missing_reqs += "\n".join(missing_quests) + "\n"

        if not missing_reqs:
            missing_reqs = "You have all the requirements needed!\n"

        return missing_reqs

    # If bored rewrite this function to be cleaner
    async def check_reqs(self, quest_reqs_for_the_quest_in_question, gamer_info, lumby_elite=False):
        with open("storage/quest_req.json", "r") as f:
            quest_reqs_dict = json.load(f)

        levels = gamer_info["levels"]
        gamers_quest_status = gamer_info["quests"]

        missing_reqs = ""

        missing_quests = []
        for quest in quest_reqs_for_the_quest_in_question["quests"]:
            if gamers_quest_status[quest] in [0, 1]:
                missing_quests.append(quest)

        for side_quest in missing_quests:
            for quest_needed_for_side_quest in quest_reqs_dict[side_quest]["quests"]:
                if gamers_quest_status[quest_needed_for_side_quest] in [0, 1]:
                    missing_quests.append(quest_needed_for_side_quest)

        missing_quests = list(set(missing_quests))

        if lumby_elite:
            all_quests = [
                "Cook's Assistant", "Demon Slayer", "The Restless Ghost", "Romeo & Juliet", "Sheep Shearer",
                "Shield of Arrav", "Ernest the Chicken", "Vampyre Slayer", "Imp Catcher", "Prince Ali Rescue",
                "Doric's Quest", "Black Knights' Fortress", "Witch's Potion", "The Knight's Sword", "Goblin Diplomacy",
                "Pirate's Treasure", "Dragon Slayer I", "Rune Mysteries", "Misthalin Mystery", "The Corsair Curse",
                "X Marks the Spot", "Below Ice Mountain", "Druidic Ritual", "Lost City", "Witch's House",
                "Merlin's Crystal", "Heroes' Quest", "Scorpion Catcher", "Family Crest", "Tribal Totem",
                "Fishing Contest",
                "Monk's Friend", "Temple of Ikov", "Clock Tower", "Holy Grail", "Tree Gnome Village", "Fight Arena",
                "Hazeel Cult", "Sheep Herder", "Plague City", "Sea Slug", "Waterfall Quest", "Biohazard",
                "Jungle Potion",
                "The Grand Tree", "Shilo Village", "Underground Pass", "Observatory Quest", "The Tourist Trap",
                "Watchtower",
                "Dwarf Cannon", "Murder Mystery", "The Dig Site", "Gertrude's Cat", "Legends' Quest",
                "Big Chompy Bird Hunting",
                "Elemental Workshop I", "Priest in Peril", "Nature Spirit", "Death Plateau", "Troll Stronghold",
                "Tai Bwo Wannai Trio", "Regicide", "Eadgar's Ruse", "Shades of Mort'ton", "The Fremennik Trials",
                "Horror from the Deep", "Throne of Miscellania", "Monkey Madness I", "Haunted Mine", "Troll Romance",
                "In Search of the Myreque", "Creature of Fenkenstrain", "Roving Elves", "Ghosts Ahoy",
                "One Small Favour",
                "Mountain Daughter", "Between a Rock...", "The Feud", "The Golem", "Desert Treasure I",
                "Icthlarin's Little Helper",
                "Tears of Guthix", "Zogre Flesh Eaters", "The Lost Tribe", "The Giant Dwarf", "Recruitment Drive",
                "Mourning's End Part I", "Forgettable Tale...", "Garden of Tranquillity", "A Tail of Two Cats",
                "Wanted!",
                "Mourning's End Part II", "Rum Deal", "Shadow of the Storm", "Making History", "Ratcatchers",
                "Spirits of the Elid",
                "Devious Minds", "The Hand in the Sand", "Enakhra's Lament", "Cabin Fever",
                "Fairytale I - Growing Pains",
                "Recipe for Disaster", "In Aid of the Myreque", "A Soul's Bane", "Rag and Bone Man I", "Swan Song",
                "Royal Trouble",
                "Death to the Dorgeshuun", "Fairytale II - Cure a Queen", "Lunar Diplomacy", "The Eyes of Glouphrie",
                "Darkness of Hallowvale", "The Slug Menace", "Elemental Workshop II", "My Arm's Big Adventure",
                "Enlightened Journey",
                "Eagles' Peak", "Animal Magnetism", "Contact!", "Cold War", "The Fremennik Isles", "Tower of Life",
                "The Great Brain Robbery", "What Lies Below", "Olaf's Quest", "Another Slice of H.A.M.", "Dream Mentor",
                "Grim Tales", "King's Ransom", "Monkey Madness II", "Client of Kourend", "Rag and Bone Man II",
                "Bone Voyage",
                "The Queen of Thieves", "The Depths of Despair", "Dragon Slayer II", "Tale of the Righteous",
                "A Taste of Hope",
                "Making Friends with My Arm", "The Forsaken Tower", "The Ascent of Arceuus", "Song of the Elves",
                "The Fremennik Exiles", "Sins of the Father", "A Porcine of Interest", "Getting Ahead",
                "A Night at the Theatre",
                "A Kingdom Divided", "Land of the Goblins", "Temple of the Eye", "Beneath Cursed Sands",
                "Sleeping Giants",
                "The Garden of Death", "Secrets of the North", "Desert Treasure II - The Fallen Empire",
                "The Path of Glouphrie",
                "Children of the Sun", "Defender of Varrock", "Twilight's Promise", "At First Light", "Perilous Moons",
                "The Ribbiting Tale of a Lily Pad Labour Dispute"
            ]
            missing_quests = []
            quest_count = 0
            for quest in gamers_quest_status:
                if gamers_quest_status[quest] != 2 and quest in all_quests:
                    missing_quests.append(quest)
                    quest_count += 1

        missing_levels = {}
        for quest in missing_quests:
            try:
                quest_reqs = quest_reqs_dict[quest]

            except KeyError:
                continue

            for skill in quest_reqs["skills"].keys():
                elder_req = missing_levels.get(skill, 1)
                level_needed = quest_reqs["skills"][skill]
                if level_needed > elder_req and level_needed > levels[skill]:
                    missing_levels[skill] = level_needed

        # I AM SO SORRY THIS IS SUCH DUMB CODE
        # I just dont know how to format this at the current moment in time - 5/3/2024 11pm
        for skill in quest_reqs_for_the_quest_in_question["skills"].keys():
            elder_req = missing_levels.get(skill, 1)
            level_needed = quest_reqs_for_the_quest_in_question["skills"][skill]
            if level_needed > elder_req and level_needed > levels[skill]:
                missing_levels[skill] = level_needed

        if missing_levels:
            missing_reqs += f"Levels needed:\n"
            for skill, level in missing_levels.items():
                missing_reqs += f"{level} {skill}\n"

        if missing_quests:
            missing_reqs += "\nQuests needed:\n"

            if lumby_elite:
                if quest_count > 1:
                    missing_reqs += f"{quest_count} quests left >:)"

                elif quest_count == 1:
                    missing_reqs += f"{quest_count} quest left :o"

                else:
                    missing_reqs += f"{quest_count} quests left :D"

            else:
                missing_reqs += "\n".join(missing_quests) + "\n"

        if not missing_reqs:
            missing_reqs = "You have all the requirements needed!\n"

        return missing_reqs

    async def combine_reqs(self, list_of_reqs):

        levels_needed = {}
        quests = []

        for req_list in list_of_reqs:
            for skill in req_list["skills"].keys():
                elder_req = levels_needed.get(skill, 1)

                if req_list["skills"][skill] > elder_req:
                    levels_needed[skill] = req_list["skills"][skill]

            quests.extend(req_list["quests"])

        quests = list(set(quests))

        return {"skills": levels_needed,
                "quests": quests}

    async def can_do_quest_without_training(self, quest, gamer_info, inner=False):
        with open("storage/quest_req.json", "r") as f:
            quest_reqs_dict = json.load(f)
        everything_is_okay = True
        quest_reqs_for_the_quest_in_question = quest_reqs_dict[quest]
        levels = gamer_info["levels"]
        quest_statuses = gamer_info["quests"]

        for skill in quest_reqs_for_the_quest_in_question["skills"].keys():
            level_needed = quest_reqs_for_the_quest_in_question["skills"][skill]
            if level_needed > levels[skill]:
                everything_is_okay = False

        if inner:
            return everything_is_okay

        for quest in quest_reqs_for_the_quest_in_question["quests"]:
            if quest_statuses[quest] in [0, 1]:
                if not await self.can_do_quest_without_training(quest, gamer_info, inner=True):
                    everything_is_okay = False

        return everything_is_okay

    @commands.command(aliases=["q"])
    async def quest(self, ctx, *args):
        try:
            gamers, quest_name = self.parse_input(ctx, args)

        except NoName:
            return await NoName.message(NoName(), ctx, self.seperator)

        for gamer in gamers:

            url = f"https://sync.runescape.wiki/runelite/player/{gamer}/STANDARD"

            status, gamer_info = await request(url, headers={
                "User-Agent": "Message me on discord if you got beef - moists0ck"})

            if status != 200:
                return await ctx.send(f"something went horribly wrong - error {status}")

            quests = gamer_info["quests"]

            list_of_quests = quests.keys()

            real_quest_name = self.spell_check(quest_name, list_of_quests)

            match int(quests[real_quest_name]):

                case 0:
                    output_msg = f"{gamer} has not started {real_quest_name} :("

                case 1:
                    output_msg = f"{gamer} has started {real_quest_name} but has not finished :/"

                case 2:
                    output_msg = f"{gamer} has finished {real_quest_name} :D"

                case _:
                    output_msg = "0_0"

            await ctx.send(output_msg)

    @commands.command()
    async def vyre(self, ctx, *args):
        today = False
        if " ".join(args) == "t":
            today = True

        vyre_accounts = ["moisty s0ck",
                         "silly gamer",
                         "purple mouse",
                         "chris4a4a4"]

        with open("storage/osrs_account_data.json", 'r') as f:
            data = json.load(f)

        formatted_yesterday, formatted_today = formatted_yesterday_today()

        total_kills = 0
        if today:
            msg = f"Vyrewatch kills for {formatted_today}\n"
        else:
            msg = f"Vyrewatch kills for {formatted_yesterday}\n"
        for gamer in vyre_accounts:
            try:
                yesterday_stats = levels_wrapper(data[gamer][formatted_yesterday].split(" "))
                today_stats = levels_wrapper(data[gamer][formatted_today].split(" "))

            except KeyError as e:
                await ctx.send(f"Information for `{e.args[0]}` is not available")
                continue

            if today:

                status, stats_dict = await get_stats(gamer)

                if status != 200:
                    print(f"Error in command !max: {status}\n"
                          f"account - {gamer} -")
                    return
                yesterday_stats = today_stats
                today_stats = stats_dict
                formatted_yesterday = formatted_today

            difference = []

            for stat in yesterday_stats.keys():

                dif_xp = int(today_stats[stat]['xp']) - int(yesterday_stats[stat]['xp'])

                if dif_xp:
                    difference.append([stat, dif_xp])

            if not difference:
                await ctx.send(f"{gamer} gained NO xp on {formatted_yesterday}\n")
                continue

            xp_gained = 0
            for dif in difference:
                skill = dif[0]
                xp = dif[1]
                if skill != "Strength" and skill != "Attack" and skill != "Defence":
                    continue

                xp_gained += xp

            vyre_kills = floor(xp_gained / 600)
            msg += f"{gamer}: {vyre_kills:,}\n"
            total_kills += vyre_kills

        msg += f"Total kills: {total_kills:,}"

        await ctx.send(msg)

    @app_commands.command(name="diary", description="check requirements")
    @app_commands.choices(area=[
        discord.app_commands.Choice(name='Ardougne', value=1),
        discord.app_commands.Choice(name='Desert', value=2),
        discord.app_commands.Choice(name='Falador', value=3),
        discord.app_commands.Choice(name='Fremennik', value=4),
        discord.app_commands.Choice(name='Kandarin', value=5),
        discord.app_commands.Choice(name='Karamja', value=6),
        discord.app_commands.Choice(name='Kourend & Kebos', value=7),
        discord.app_commands.Choice(name='Lumbridge & Draynor', value=8),
        discord.app_commands.Choice(name='Morytania', value=9),
        discord.app_commands.Choice(name='Varrock', value=10),
        discord.app_commands.Choice(name='Western Provinces', value=11),
        discord.app_commands.Choice(name='Wilderness', value=12)
    ]
    )
    @app_commands.choices(tier=[
        discord.app_commands.Choice(name='Easy', value=1),
        discord.app_commands.Choice(name='Medium', value=2),
        discord.app_commands.Choice(name='Hard', value=3),
        discord.app_commands.Choice(name='Elite', value=4)
    ]
    )
    @app_commands.guild_only()
    async def diaries(self, interaction: discord.Interaction, area: discord.app_commands.Choice[int],
                      tier: discord.app_commands.Choice[int],
                      gamer: str):
        url = f"https://sync.runescape.wiki/runelite/player/{gamer}/STANDARD"

        status, gamer_info = await request(url,
                                           headers={"User-Agent": "Message me on discord if you got beef - moists0ck"})
        if status != 200:
            if status == 400:
                return await interaction.response.send_message(f"No information was found for the user: `{gamer}`")
            return await interaction.response.send_message(f"something went horribly wrong - error {status}")

        if gamer_info['achievement_diaries'][area.name][tier.name]['complete'] and False not in \
                gamer_info['achievement_diaries'][area.name][tier.name]["tasks"]:
            msg = f"{gamer} has completed the {area.name} {tier.name} :)"
            return await interaction.response.send_message(msg)

        msg = f"{gamer} has not completed the {area.name} {tier.name} :(\n\n"

        with open("storage/diary_reqs.json", "r") as f:
            diary_reqs_dict = json.load(f)

        match tier.value:

            case 1:
                msg += await self.check_reqs(diary_reqs_dict[area.name]["Easy"], gamer_info)

            case 2:
                reqs_needed = await self.combine_reqs([diary_reqs_dict[area.name]["Easy"],
                                                       diary_reqs_dict[area.name]["Medium"]])
                msg += await self.check_reqs(reqs_needed, gamer_info)

            case 3:
                reqs_needed = await self.combine_reqs([diary_reqs_dict[area.name]["Easy"],
                                                       diary_reqs_dict[area.name]["Medium"],
                                                       diary_reqs_dict[area.name]["Hard"]])
                msg += await self.check_reqs(reqs_needed, gamer_info)

            case 4:
                reqs_needed = await self.combine_reqs([diary_reqs_dict[area.name]["Easy"],
                                                       diary_reqs_dict[area.name]["Medium"],
                                                       diary_reqs_dict[area.name]["Hard"],
                                                       diary_reqs_dict[area.name]["Elite"]])
                if area.name == "Lumbridge & Draynor":
                    lumby = True

                else:
                    lumby = False

                msg += await self.check_reqs(reqs_needed, gamer_info, lumby)

            case _:
                return await interaction.response.send_message("FUCK")

        return await interaction.response.send_message(msg)


async def setup(bot):
    await bot.add_cog(Runescape(bot))
