from typing import Optional

import json5

def get_url_to_wordcount_dict() -> dict[str, Optional[int]]:
    try:
        with open("urldict.json", "r") as f:
            return json5.load(f)
    except ValueError as e:
        print("Failed to read url dict from file! (Re-raising to prevent removing urls_to_wordcount.)")
        raise e

if __name__ == '__main__':
    url_to_count = get_url_to_wordcount_dict()
    print(f"Total urls: {len(url_to_count)}")
    for (i, (url, count)) in enumerate(sorted(url_to_count.items(), key=lambda x: 0 if x[1] is None else x[1], reverse=True)):
        if i % 10 == 0:
            print(f"Index: {i}")
        print(url)
        # print((url,count))

