import os
import requests
from bs4 import BeautifulSoup

max_quotes = 2

def save_audio(filename, url):
    response = requests.get(url)
    if response.status_code == 200:
        if not os.path.exists("media"):
            os.makedirs("media")
        with open(f"media/{filename}", "wb") as file:
            file.write(response.content)

def save_data(data):
    with open("data.txt", "a") as file:
        file.write(data)

def search_word(n):
    url = f"https://www.englishprofile.org/american-english/words/usdetail/{n}"
    response = requests.get(url)
    doc = BeautifulSoup(response.content, "html.parser")

    details = doc.find_all("div", attrs={"class": "evp_details"})[-1]
    headword = details.find("span", attrs={"class": "headword"}).string
    entries = details.find_all(recursive=False)
    for entry in entries:
        if entry["class"] == ["pos_section"]:
            audio = ""
            audio_tag = entry.find("audio")
            if audio_tag != None:
                audio_src = audio_tag.find("source")["src"]
                audio_url = "https://www.englishprofile.org" + audio_src
                filename = os.path.basename(audio_url).lower()
                save_audio(filename, audio_url)
                audio = f"[sound:{filename}]"

            written = ""
            written_tag = entry.find("span", attrs={"class": "written"})
            if written_tag != None:
                written = written_tag.string

            subentries = entry.select("div.info.sense")
            for subentry in subentries:
                title = subentry.find("div", attrs={"class": "sense_title"}).string
                label = subentry.find("span", attrs={"class": "label"}).string
                definition = subentry.find("span", attrs={"class": "definition"}).string

                example = subentry.find("div", attrs={"class": "example"})
                if example != None:
                    example_quotes = example.find_all("p", attrs={"class": "blockquote"})
                else:
                    example_quotes = None

                learner = subentry.find("div", attrs={"class": "learner"})
                if learner != None:
                    learner_quotes = learner.find_all("p", attrs={"class": "learnerexamp"})
                else:
                    learner_quotes = None

                sentences = ""
                for i in range(max_quotes):
                    if example_quotes:
                        sentences += "\t" + example_quotes.pop(0).get_text().strip()
                    elif learner_quotes:
                        sentences += "\t" + learner_quotes.pop(0).get_text().strip()
                    else:
                        sentences += "\t"

                data = f"{title}\t{written}\t{audio}\t[{label}] {definition}{sentences}\n"
                save_data(data)
        else:
            audio = ""
            written = ""

            title = entry.find("div", attrs={"class": "sense_title"}).string
            label = entry.find("span", attrs={"class": "label"}).string
            definition = entry.find("span", attrs={"class": "definition"}).string

            example = entry.find("div", attrs={"class": "example"})
            if example != None:
                example_quotes = example.find_all("p", attrs={"class": "blockquote"})
            else:
                example_quotes = None

            learner = entry.find("div", attrs={"class": "learner"})
            if learner != None:
                learner_quotes = learner.find_all("p", attrs={"class": "learnerexamp"})
            else:
                learner_quotes = None

            sentences = ""
            for i in range(max_quotes):
                if example_quotes:
                    sentences += "\t" + example_quotes.pop(0).get_text().strip()
                elif learner_quotes:
                    sentences += "\t" + learner_quotes.pop(0).get_text().strip()
                else:
                    sentences += "\t"

            data = f"{title}\t{written}\t{audio}\t[{label}] {definition}{sentences}\n"
            save_data(data)

    return headword

for i in range(1, 6757):
    print(f"{i}. {search_word(i)}")
print("Extract complete!")
