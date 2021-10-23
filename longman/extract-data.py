import bleach
import os
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Login info
email = ""
password = ""

# Number of items
max_meanings = 5
max_sentences = 5

def main():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.headless = True
    driver = webdriver.Chrome("chromedriver.exe", options=chrome_options)
    wait = WebDriverWait(driver, 10)
    print("=> Loading...")

    driver.get("http://global.longmandictionaries.com/auth/login")
    driver.find_element_by_id("email").send_keys(email)
    driver.find_element_by_id("password").send_keys(password)
    driver.find_element_by_id("submit").click()

    driver.get("http://global.longmandictionaries.com/ldoce6/advanced_search")
    driver.find_element_by_id("corevocab-button").click()
    driver.find_element_by_link_text("All").click()
    driver.find_element_by_id("search_submit").click()

    with open("data.txt", "a", encoding="utf-8") as file:
        i = 1
        while True:
            # Traverse the sidebar
            try:
                wait.until(EC.visibility_of_element_located((By.XPATH, f"//*[@id='word_list']/div/div[1]/ul/li[{i}]")))
            except:
                break
            item = driver.find_element_by_xpath(f"//*[@id='word_list']/div/div[1]/ul/li[{i}]")
            word = item.find_element_by_tag_name("a")
            word.location_once_scrolled_into_view
            word.click()

            # Wait for the page to load
            wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "entry")))
            entry = driver.find_element_by_class_name("entry")
            try:
                wait.until(EC.staleness_of(entry))
                wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "entry")))
            except:
                continue
            entry = driver.find_element_by_class_name("entry")
            current_id = entry.get_attribute("id")

            # Pass the page to Beautiful Soup
            html = entry.get_attribute("innerHTML")
            data = get_data(html)

            file.write(data)
            print(f"{i}. {current_id}")
            i += 1

    print("=> Extract complete!")
    print("=> Exiting...")
    driver.quit()

def get_data(html):
    soup = BeautifulSoup(html, "html.parser")
    entryhead = soup.find("span", attrs={"class": "entryhead"})
    headword = entryhead.find("span", attrs={"class": "hwd"}).string.strip()

    proncodes = ""
    proncodes_tag = entryhead.find("proncodes")
    if proncodes_tag != None:
        proncodes = proncodes_tag.get_text().strip()

    level = ""
    level_tag = entryhead.find("span", attrs={"class": "level"})
    if level_tag != None:
        level = level_tag.string.strip()

    pos = ""
    pos_tags = entryhead.find_all("span", attrs={"class": "pos"})
    for pos_tag in pos_tags:
        pos += pos_tag.get_text().strip()

    gram1 = ""
    gram1_tag = entryhead.find("span", attrs={"class": "gram"})
    if gram1_tag != None:
        gram1 = gram1_tag.get_text().strip()

    audio_uk_list = []
    audio_uk_tags = entryhead.find_all("a", attrs={"variant": "bre"})
    for audio_uk_tag in audio_uk_tags:
        audio_uk_src = audio_uk_tag.get("file")
        filename = "uk_" + os.path.basename(audio_uk_src)
        audio_uk_url = f"http://global.longmandictionaries.com/res/audio/hwd/bre/{audio_uk_src}"
        save_audio(filename, audio_uk_url)
        audio_uk_list.append(f"[sound:{filename}]")
    audio_uk = ', '.join(audio_uk_list)

    audio_us_list = []
    audio_us_tags = entryhead.find_all("a", attrs={"variant": "ame"})
    for audio_us_tag in audio_us_tags:
        audio_us_src = audio_us_tag.get("file")
        filename = "us_" + os.path.basename(audio_us_src)
        audio_us_url = f"http://global.longmandictionaries.com/res/audio/hwd/ame/{audio_us_src}"
        save_audio(filename, audio_us_url)
        audio_us_list.append(f"[sound:{filename}]")
    audio_us = ', '.join(audio_us_list)

    audio = ""
    if audio_uk != "" and audio_us != "":
        audio = f"{audio_uk}, {audio_us}"
    if audio_uk != "" and audio_us == "":
        audio = f"{audio_uk}"
    if audio_uk == "" and audio_us != "":
        audio = f"{audio_us}"

    data = ""
    head_data = {
        "headword": f"{headword}",
        "proncodes": f"{proncodes}",
        "level": f"{level}",
        "pos": f"{pos}",
        "gram1": f"{gram1}",
        "audio": f"{audio}"
    }

    sense_list = []
    phrvb_list = []
    subentries = soup.find_all(recursive=False)
    for subentry in subentries:
        if "sense" in subentry["class"]:
            sense_list.append(subentry)
        if "spokensect" in subentry["class"]:
            for sense in subentry.find_all("span", attrs={"class": "sense"}):
                sense_list.append(sense)
        if "phrvbentry" in subentry["class"]:
            phrvb_list.append(subentry)

    data += get_senses(soup, head_data, sense_list)

    for i, phrvb in enumerate(phrvb_list):
        entryhead = phrvb.find("span", attrs={"class": "entryhead"})
        phrvbhwd = entryhead.find("span", attrs={"class": "phrvbhwd"})
        headword = bleach.clean(f"{phrvbhwd}", tags=["object"], strip=True, strip_comments=True)
        headword = headword.replace("<object>", "<object style='font-weight: normal;'>")
        headword = f"<b>{headword}</b>"

        pos = ""
        pos_tags = entryhead.find_all("span", attrs={"class": "pos"})
        for pos_tag in pos_tags:
            pos += pos_tag.get_text().strip()
        
        gram1 = ""
        gram1_tag = entryhead.find("span", attrs={"class": "gram"})
        if gram1_tag != None:
            gram1 = gram1_tag.get_text().strip()
        
        # Update keys related to phrvb
        head_data["headword"] = headword
        head_data["pos"] = pos
        head_data["gram1"] = gram1
        
        sense_list = []
        subentries = phrvb.find_all(recursive=False)
        for subentry in subentries:
            if "sense" in subentry["class"]:
                sense_list.append(subentry)
            if "spokensect" in subentry["class"]:
                for sense in subentry.find_all("span", attrs={"class": "sense"}):
                    sense_list.append(sense)
        
        data += get_senses(soup, head_data, sense_list)

    return data

def save_audio(filename, url):
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    if response.status_code == 200:
        if not os.path.exists("media"):
            os.makedirs("media")
        with open(f"media/{filename}", "wb") as file:
            file.write(response.content)

def get_senses(soup, head_data, sense_list):
    headword = head_data["headword"]
    proncodes = head_data["proncodes"]
    level = head_data["level"]
    pos = head_data["pos"]
    gram1 = head_data["gram1"]
    audio = head_data["audio"]

    data = ""
    for i, sense in enumerate(sense_list):
        if i + 1 > max_meanings:
            break

        lexunit1 = ""
        lexunit1_tag = sense.find("span", attrs={"class": "lexunit"}, recursive=False)
        if lexunit1_tag != None:
            lexunit1 = lexunit1_tag.string.strip()

        gram2 = ""
        gram2_tag = sense.find("span", attrs={"class": "gram"}, recursive=False)
        if gram2_tag != None:
            gram2 = gram2_tag.get_text().strip()

        subsenses = sense.find_all("span", attrs={"class": "subsense"})
        if subsenses:
            for subsense in subsenses:
                lexunit2_tag = subsense.find("span", attrs={"class": "lexunit"})
                if lexunit2_tag != None:
                    lexunit2 = lexunit2_tag.string.strip()
                else:
                    lexunit2 = lexunit1

                gram3 = ""
                gram3_tag = subsense.find("span", attrs={"class": "gram"})
                if gram3_tag != None:
                    gram3 = gram3_tag.get_text().strip()
                else:
                    gram3 = gram2

                definition = ""
                definition_tag = subsense.find("span", attrs={"class": "def"})
                if definition_tag != None:
                    definition = definition_tag.get_text().strip()

                synonym_list = []
                synonym_tags = subsense.find_all("span", attrs={"class": "syn"})
                for synonym_tag in synonym_tags:
                    synonym_list.append(synonym_tag.get_text())
                synonyms = "".join(synonym_list)
                synonyms = synonyms.replace("SYN", "")
                synonyms = synonyms.strip()

                antonym_list = []
                antonym_tags = subsense.find_all("span", attrs={"class": "opp"})
                for antonym_tag in antonym_tags:
                    antonym_list.append(antonym_tag.get_text())
                antonyms = "".join(antonym_list)
                antonyms = antonyms.replace("OPP", "")
                antonyms = antonyms.strip()

                sentences = get_sentences(soup, subsense)

                data += f"{headword}\t{proncodes}\t{level}\t{pos}\t{gram1}\t{audio}\t"
                data += f"{lexunit2}\t{gram3}\t{definition}\t{synonyms}\t{antonyms}"
                for j in range(max_sentences):
                    if sentences:
                        data += "\t" + sentences.pop(0)
                    else:
                        data += "\t"
                data += "\n"
        else:
            definition = ""
            definition_tag = sense.find("span", attrs={"class": "def"})
            if definition_tag != None:
                definition = definition_tag.get_text().strip()

            synonym_list = []
            synonym_tags = sense.find_all("span", attrs={"class": "syn"})
            for synonym_tag in synonym_tags:
                synonym_list.append(synonym_tag.get_text())
            synonyms = "".join(synonym_list)
            synonyms = synonyms.replace("SYN", "")
            synonyms = synonyms.strip()

            antonym_list = []
            antonym_tags = sense.find_all("span", attrs={"class": "opp"})
            for antonym_tag in antonym_tags:
                antonym_list.append(antonym_tag.get_text())
            antonyms = "".join(antonym_list)
            antonyms = antonyms.replace("OPP", "")
            antonyms = antonyms.strip()

            sentences = get_sentences(soup, sense)

            data += f"{headword}\t{proncodes}\t{level}\t{pos}\t{gram1}\t{audio}\t"
            data += f"{lexunit1}\t{gram2}\t{definition}\t{synonyms}\t{antonyms}"
            for j in range(max_sentences):
                if sentences:
                    data += "\t" + sentences.pop(0)
                else:
                    data += "\t"
            data += "\n"

    return data

def get_sentences(soup, sense):
    sentences = []
    blockquotes = sense.find_all(recursive=False)
    for blockquote in blockquotes:
        form = ""
        glossary = ""
        split = ""
        example_tags = []

        if blockquote["class"] == ["colloexa"]:
            form_tag = blockquote.find("span", attrs={"class": "collo"}, recursive=False)
            if form_tag != None:
                form = form_tag.get_text().strip()
                form = f"<b>{form}</b>"

            glossary_tag = blockquote.find("span", attrs={"class": "gloss"}, recursive=False)
            if glossary_tag != None:
                glossary = glossary_tag.get_text().strip()

            example_tags = blockquote.find_all("span", attrs={"class": "example"}, recursive=False)
            split = "<br>"

        if blockquote["class"] == ["gramexa"]:
            form_tag = blockquote.find("span", attrs={"class": "propform"}, recursive=False)
            if form_tag == None:
                form_tag = blockquote.find("span", attrs={"class": "propformprep"}, recursive=False)

            # If form_tag is found after previous attempts
            if form_tag != None:
                form = form_tag.get_text().strip()
                form = f"<b>{form}</b>"

            glossary_tag = blockquote.find("span", attrs={"class": "gloss"}, recursive=False)
            if glossary_tag != None:
                glossary = glossary_tag.get_text().strip()

            example_tags = blockquote.find_all("span", attrs={"class": "example"}, recursive=False)
            split = "<br>"

        if blockquote["class"] == ["example"]:
            example_tags.append(blockquote)

        extra = f"{form} {glossary}"
        extra = extra.strip()

        for example_tag in example_tags:
            bold_tags = example_tag.find_all("span", attrs={"class": "colloinexa"})
            for bold_tag in bold_tags:
                new_tag = soup.new_tag("b")
                new_tag.string = bold_tag.get_text()
                bold_tag.replace_with(new_tag)
            
            example = bleach.clean(f"{example_tag}", tags=["b"], strip=True, strip_comments=True)
            example = ' '.join(example.split())
            sentence = f"{extra}{split}{example}"
            sentences.append(sentence)

    return sentences

main()
