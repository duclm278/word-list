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

    ipa = ""
    ipa_tag = head.find("span", attrs={"class": "pron"})
    if get_spells and ipa_tag:
        ipa = ipa_tag.get_text()
        ipa = " ".join(ipa.split())

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
                ipa = detail.get_text()

        if detail.name == "div" and "block" in detail["class"][0]:
            blocks.append((title, ipa, audio, detail))

        if detail.name == "div" and "phrasal_verb" in detail["class"]:
            title_tag = detail.find("h3", attrs={"class": "phrase"})
            title = title_tag.get_text().strip()
            title = " ".join(title.split())
            subdetails = detail.find_all("div", attrs={"class": "gwblock"})
            for subdetail in subdetails:
                blocks.append((title, ipa, audio, subdetail))

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
        title, ipa, audio, main = block

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

        basics = (term, title, ipa, audio)
        for sense in senses:
            data += get_sense(basics, sense)

    return data

def get_sense(basics, sense):
    data = ""
    term, title, ipa, audio = basics

    level = sense.find("span", attrs={"class": re.compile("freq.*")}).string
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

    form_dict = getAllInflections(term)
    forms = {y for x in form_dict.values() for y in x}
    if not forms:
        forms = {term}

    sentences = ""
    for i in range(max_quotes):
        if example_quotes:
            sentence = example_quotes.pop(0).get_text().strip()
            sentence = ' '.join(sentence.split())
            focus_text, cloze_text = occlude_text(sentence, term, forms)
            sentences += "\t" + focus_text + "\t" + cloze_text
        elif learner_quotes:
            sentence = learner_quotes.pop(0).get_text().strip()
            sentence = ' '.join(sentence.split())
            focus_text, cloze_text = occlude_text(sentence, term, forms)
            sentences += "\t" + focus_text + "\t" + cloze_text
        else:
            sentences += "\t\t"

    sentences = sentences[1:]
    cloze_term = occlude_text(term, term, term)[1]
    data += f"{term}\t{cloze_term}\t{title}\t{ipa}\t{audio}\t"
    data += f"{level}\t{definition}\t{sentences}\n"
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
    focus_text = ""
    cloze_text = ""

    if len(term.split()) > 1:
        focus_text, cloze_text = text, text
        for word in term.split():
            focus_word = f"<b>{word}</b>"
            focus_text = focus_text.replace(word, focus_word)
            focus_word = f"<b>{word.capitalize()}</b>"
            focus_text = focus_text.replace(word.capitalize(), focus_word)
            cloze_word = f"<b>{occlude_word(word)}</b>"
            cloze_text = cloze_text.replace(word, cloze_word)
            cloze_word = f"<b>{occlude_word(word).capitalize()}</b>"
            cloze_text = cloze_text.replace(word.capitalize(), cloze_word)

        return focus_text, cloze_text

    doc = nlp(text)
    for token in doc:
        word = token.text
        if word in forms or word.lower() in forms:
            focus_text += f"<b>{word}</b>"
            focus_text += token.whitespace_
            cloze_text += f"<b>{occlude_word(word)}</b>"
            cloze_text += token.whitespace_
        else:
            focus_text += token.text_with_ws
            cloze_text += token.text_with_ws

    return focus_text, cloze_text

if __name__ == "__main__":
    main()