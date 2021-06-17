import re
from collections import Counter
from itertools import zip_longest
from typing import Tuple


def chunks_of(iterable, n, fillvalue=None):
    """Collect data into fixed-length chunks or blocks"""
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


def print_counter_aligned(to_print: Counter, indent=4) -> None:
    if len(to_print) == 0:
        print(f"{' ' * indent} Empty.")
        return
    longest = max(len(k) for k in to_print.keys())
    for name, count in to_print.most_common():
        print(f"{' ' * indent}{name}:{' ' * (longest - len(name) + 1)}{count}")

def is_good_action_reason_pair(action: str, reason: str):
    if action in ["Update", "Add"]:
        return True
    
    if action == "Skipped" and ALREADY_CONTAINS_N_CHAPTERS.match(reason):
        return True


if __name__ == '__main__':
    ALREADY_CONTAINS_N_CHAPTERS = re.compile(r"Already contains (\d+) chapters\.$")
    ERROR_492_TOO_MANY_REQ = r"HTTP Error in FFF '429 Client Error: Too Many Requests for url"
    
    error_path = r"calibre_errors.txt"
    
    KNOWN_ACTIONS = ["Skipped", "Error", "Add", "Update", "Different URL"]
    
    
    more_than_one_known_list:list[Tuple[str, str, str, str, str]] = []
    save_again:list[Tuple[str, str, str, str, str]] = []
    counts = Counter()
    
    specific_counts = {k: Counter() for k in KNOWN_ACTIONS}
    to_redownload : list[str] = []
    
    with open(error_path, "rt", encoding="utf8") as f:
        action: str; name: str; author: str; reason: str; ulr: str
        for (action, name, author, reason, url) in chunks_of(f.read().splitlines(), 5):
            counts[action] += 1
            if not is_good_action_reason_pair(action, reason):
                save_again.append((action, name, author, reason, url))
                if action == "Error" and reason.startswith(ERROR_492_TOO_MANY_REQ):
                    specific_counts[action][ERROR_492_TOO_MANY_REQ] += 1
                else:
                    specific_counts[action][reason] += 1
            else:
                specific_counts[action]["Good"] += 1
                
            if action == "Skipped":
                if ALREADY_CONTAINS_N_CHAPTERS.match(reason):
                    pass
                elif reason == r"More than one identical book by Identifier URL or title/author(s)--can't tell which book to update/overwrite.":
                    more_than_one_known_list.append((action, name, author, reason, url))
            elif action == "Error":
                if reason.startswith(ERROR_492_TOO_MANY_REQ):
                    to_redownload.append(url)    
        
    print("Action counts:")
    print_counter_aligned(counts)
    
    print("Specific bad action reasons:")
    for (name, counter) in specific_counts.items():
        print(f"{name}:")
        print_counter_aligned(counter)
    
    if to_redownload:
        print(f"Download again: ({len(to_redownload)})")
        for url in to_redownload:
            print(url)
    
    if more_than_one_known_list:
        print(f"More than one known for (author name pairs): ({len(more_than_one_known_list)})")
        # for (action, name, author, reason, url) in more_than_one_known_list:
        #     print("---")
        #     print(f"{author}")
        #     print(f"{name}")
        #     print(f"{url}")
        print("Those for easy pasting after fixing: ")
        for (action, name, author, reason, url) in more_than_one_known_list:
            print(url)


    print("Rewriting only errors...")
    
    with open(error_path, "wt", encoding="utf8") as f:
        for tuple_ in save_again:
            for elem in tuple_:
                f.write(elem)
                f.write("\n")
            