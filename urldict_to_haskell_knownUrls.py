from main import get_url_to_wordcount_dict

if __name__ == '__main__':
    url_to_words = get_url_to_wordcount_dict()
    text = "fromList ["
    for (url, words) in get_url_to_wordcount_dict().items():
        url: str
        words: int
        url_text = url.removeprefix("https://archiveofourown.org")
        words_text = str(words) if words is not None else 0
        text += f"(\"{url_text}\",{words_text}),"
    
    text = text[:-1]
    text += "]"

    with open("knownUrls.txt", "w+") as f:
        f.write(text)
