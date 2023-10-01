import json


def store_test(thing_to_store):
    with open("storage/test.json", "w") as f:
        json.dump(thing_to_store, f, indent=2)

