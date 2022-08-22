import os
import spacy
import requests
from bs4 import BeautifulSoup
from helpers import Setup
from lemminflect import getAllInflections

max_quotes = 5
get_spells = False
get_audios = False

setup = Setup()
nlp = spacy.load("en_core_web_sm")

def main():
    setup.set_proxies()

    try:
        answer = input("First: ")
        if not answer:
            answer = "1"
        first = int(answer)

        answer = input("Final: ")
        if not answer:
            answer = "6756"
        final = int(answer)
    except:
        exit()

    with open("data.txt", "a", encoding="utf-8") as file:
        for i in range(first, final + 1):
            url = f"https://www.englishprofile.org/american-english/words/usdetail/{i}"
            headword, data = get_data(url)

            file.write(data)
            print(f"{i}. {headword}")

    print("=> Extract complete!")

def get_data(url):
    for attempt in range(5):
        try:
            response = requests.get(url, headers=setup.headers, proxies=setup.proxies)
            soup = BeautifulSoup(response.content, "html.parser")

            details = soup.find_all("div", attrs={"class": "evp_details"})[-1]
        except:
            continue
        else:
            break
    else:
        print(f"Failed: {url}")
        exit()

    headword = details.find("span", attrs={"class": "headword"}).string

    data = ""
    blocks = []
    entries = details.find_all(recursive=False)
    for entry in entries:
        if "sense" in entry["class"]:
            blocks.append({
                "header": None,
                "sense": entry
            })
        if "pos_section" in entry["class"]:
            header = entry.find("div", attrs={"class": "pos_header"})
            for sense in entry.find_all("div", attrs={"class": "sense"}):
                blocks.append({
                    "header": header,
                    "sense": sense
                })
    
    data += get_senses(headword, blocks)
    return headword, data

def get_senses(headword, blocks):
    data = ""
    for block in blocks:
        audio = ""
        written = ""

        header = block["header"]
        if header:
            audio_tag = header.find("audio")
            if get_audios and audio_tag:
                audio = get_audio(audio_tag)

            written_tag = header.find("span", attrs={"class": "written"})
            if get_spells and written_tag:
                written = written_tag.string

        sense = block["sense"]
        title = sense.find("div", attrs={"class": "sense_title"}).string
        label = sense.find("span", attrs={"class": "label"}).string
        definition = sense.find("span", attrs={"class": "definition"}).string

        example = sense.find("div", attrs={"class": "example"})
        if example:
            example_quotes = example.find_all("p", attrs={"class": "blockquote"})
        else:
            example_quotes = None

        learner = sense.find("div", attrs={"class": "learner"})
        if learner:
            learner_quotes = learner.find_all("p", attrs={"class": "learnerexamp"})
        else:
            learner_quotes = None

        form_dict = getAllInflections(headword)
        forms = {y for x in form_dict.values() for y in x}
        if not forms:
            forms = {headword}

        sentences = ""
        for i in range(max_quotes):
            if example_quotes:
                sentence = example_quotes.pop(0).get_text().strip()
                sentences += "\t" + sentence + "\t" + cloze_sentence(sentence, forms)
            elif learner_quotes:
                sentence = learner_quotes.pop(0).get_text().strip()
                sentences += "\t" + sentence + "\t" + cloze_sentence(sentence, forms)
            else:
                sentences += "\t\t"

        cloze = cloze_word(headword)
        data += f"{headword}\t{cloze}\t{title}\t{written}\t{audio}\t{label}\t{definition}{sentences}\n"

    return data

def cloze_sentence(sentence, forms):
    doc = nlp(sentence)

    processed = ""
    for token in doc:
        text = token.text
        if text.lower() in forms:
            processed += "<b>" + cloze_word(text) + "</b>"
            processed += token.whitespace_
        else:
            processed += token.text_with_ws

    return processed

def cloze_word(text):
    processed = ""
    if len(text) <= 2:
        # processed += "[...]"
        processed += " ".join(["_"] * len(text))
    elif len(text) <= 4:
        # processed += text[0] + "[...]"
        processed += text[0] + " _" * (len(text) - 1)
    else:
        # processed += text[0] + "[...]" + text[-1]
        processed += text[0] + " _" * (len(text) - 2) + " " + text[-1]
    
    return processed

def get_audio(audio_tag):
    audio_src = audio_tag.find("source")["src"]
    audio_url = "https://www.englishprofile.org" + audio_src
    filename = os.path.basename(audio_url).lower()
    save_audio(filename, audio_url)
    return f"[sound:{filename}]"

def save_audio(filename, url):
    for attempt in range(5):
        try:
            response = requests.get(url, headers=setup.headers, proxies=setup.proxies)
        except:
            continue
        else:
            break
    else:
        print(f"Failed: {url}")
        exit()

    if response.status_code == 200:
        if not os.path.exists("media"):
            os.makedirs("media")
        with open(f"media/{filename}", "wb") as file:
            file.write(response.content)

if __name__ == "__main__":
    main()
