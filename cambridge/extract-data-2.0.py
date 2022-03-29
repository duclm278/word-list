import os
import spacy
import re
import requests
from bs4 import BeautifulSoup
from helpers import Setup
from lemminflect import getAllInflections

max_quotes = 5
get_audios = False
get_spells = True

host = "http://englishprofile:vocabulary@vocabulary.englishprofile.org"

setup = Setup()
nlp = spacy.load("en_core_web_sm")

def main():
    setup.set_proxies()

    urls = []
    with open("mapping.txt", "r", encoding="utf-8") as file:
        for row in file:
            row = row.strip()
            parts = row.split("\t")
            urls.append(parts[1])
    
    if not urls:
        exit()

    with open("data-2.0.txt", "a", encoding="utf-8") as file:
        for i in range(0, len(urls)):
            term, data = get_data(urls[i])

            file.write(data)
            print(f"{i + 1}. {term}")

    print("=> Extract complete!")

def get_data(url):
    for attempt in range(5):
        try:
            response = requests.get(url, headers=setup.headers, proxies=setup.proxies)
            soup = BeautifulSoup(response.content, "html.parser")

            entry = soup.find("span", attrs={"class": "entry"})
            head = entry.find("div", attrs={"class": "head"})
        except:
            continue
        else:
            break
    else:
        print(f"Failed: {url}")
        exit()

    term = head.find("h1", attrs={"class": "hw"}).get_text()

    pron = ""
    pron_tag = head.find("span", attrs={"class": "pron"})
    if get_spells and pron_tag:
        pron = pron_tag.get_text()
        pron = " ".join(pron.split())

    audio = ""
    audio_tag = head.find("img")
    if get_audios and audio_tag:
        audio = get_audio(audio_tag)

    title = term

    details = []
    posblocks = entry.find_all("div", attrs={"class": "posblock"})
    for posblock in posblocks:
        details += posblock.find_all(recursive=False)

    blocks = []
    for detail in details:
        if get_audios and details.name == "img":
            audio = get_audio(detail)

        if get_spells and detail.name == "div":
            if "pron" in detail["class"]:
                pron = detail.get_text()

        if detail.name == "div" and "block" in detail["class"][0]:
            blocks.append((title, pron, audio, detail))

        if detail.name == "div" and "phrasal_verb" in detail["class"]:
            title_tag = detail.find("h3", attrs={"class": "phrase"})
            title = title_tag.get_text().strip()
            title = " ".join(title.split())
            subdetails = detail.find_all("div", attrs={"class": "gwblock"})
            for subdetail in subdetails:
                blocks.append((title, pron, audio, subdetail))

    data = get_blocks(term, blocks)
    return term, data

def get_audio(audio_tag):
    audio_fun = audio_tag["onclick"]
    audio_src = re.search(r"(\/dictionary.*mp3)", audio_fun).group(1)
    audio_url = host + audio_src
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

def get_blocks(term, blocks):
    data = ""
    for block in blocks:
        title, pron, audio, main = block

        phrase_tag = main.find("h3", attrs={"class": "phrase"})
        if phrase_tag:
            title = phrase_tag.get_text().strip()
            title = " ".join(title.split())

        guide = ""
        guide_tag = main.find("h3", attrs={"class": "gw"})
        if guide_tag:
            guide = guide_tag.string.strip()
            title = f"{title} ({guide})"

        senses = main.find_all("div", attrs={"class": "sense"})
        if not senses:
            continue

        basics = (term, title, pron, audio)
        for sense in senses:
            data += get_sense(basics, sense)

    return data

def get_sense(basics, sense):
    term, title, pron, audio = basics

    label = sense.find("span", attrs={"class": re.compile("freq.*")}).string
    definition = sense.find("span", attrs={"class": "def"}).get_text().strip()
    definition = " ".join(definition.split())

    example = sense.find("div", attrs={"class": "examp-block"})
    if example:
        example_quotes = example.find_all("blockquote", attrs={"class": "examp"})
    else:
        example_quotes = None

    learner_quotes = sense.find_all("blockquote", attrs={"class": "clc"})
    if learner_quotes:
        for i in range(len(learner_quotes)):
            learner_quotes[i].find("div", attrs={"class": "clc_before"}).decompose()
            src_tag = learner_quotes[i].find("div", attrs={"class": "src"})
            if src_tag:
                src_tag.string = f"({src_tag.string})"
    else:
        learner_quotes = None

    cloze = occlude_text(term, term, term)[1]
    form_dict = getAllInflections(term)
    forms = {y for x in form_dict.values() for y in x}
    if not forms:
        forms = {term}

    sentences = ""
    for i in range(max_quotes):
        if example_quotes:
            sentence = example_quotes.pop(0).get_text().strip()
            sentence = ' '.join(sentence.split())
            selected_text, occluded_text = occlude_text(sentence, term, forms)
            sentences += "\t" + selected_text + "\t" + occluded_text
        elif learner_quotes:
            sentence = learner_quotes.pop(0).get_text().strip()
            sentence = ' '.join(sentence.split())
            selected_text, occluded_text = occlude_text(sentence, term, forms)
            sentences += "\t" + selected_text + "\t" + occluded_text
        else:
            sentences += "\t\t"

    data = f"{term}\t{cloze}\t{title}\t{pron}\t{audio}\t{label}\t{definition}{sentences}\n"
    return data

def occlude_word(word):
    result = ""
    if len(word) <= 2:
        # processed += "[...]"
        result += " ".join(["_"] * len(word))
    elif len(word) <= 4:
        # processed += text[0] + "[...]"
        result += word[0] + " _" * (len(word) - 1)
    else:
        # processed += text[0] + "[...]" + text[-1]
        result += word[0] + " _" * (len(word) - 2) + " " + word[-1]

    return result

def occlude_text(text, term, forms):
    selected_text = ""
    occluded_text = ""

    if len(term.split()) > 1:
        selected_text, occluded_text = text, text
        for word in term.split():
            selected_word = f"<b>{word}</b>"
            selected_text = selected_text.replace(word, selected_word)
            selected_word = f"<b>{word.capitalize()}</b>"
            selected_text = selected_text.replace(word.capitalize(), selected_word)
            occluded_word = f"<b>{occlude_word(word)}</b>"
            occluded_text = occluded_text.replace(word, occluded_word)
            occluded_word = f"<b>{occlude_word(word).capitalize()}</b>"
            occluded_text = occluded_text.replace(word.capitalize(), occluded_word)

        return selected_text, occluded_text

    doc = nlp(text)
    for token in doc:
        word = token.text
        if word in forms or word.lower() in forms:
            selected_text += f"<b>{word}</b>"
            selected_text += token.whitespace_
            occluded_text += f"<b>{occlude_word(word)}</b>"
            occluded_text += token.whitespace_
        else:
            selected_text += token.text_with_ws
            occluded_text += token.text_with_ws

    return selected_text, occluded_text

if __name__ == "__main__":
    main()