#!/usr/bin/python
from bs4 import BeautifulSoup
import json
import re
import tkinter as tk 
import tkinter.filedialog
import urllib.request
import os
import errno
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool

def parseScratchHTML(input_file):
    try:
        with open(input_file) as html_file:
            parse_list = list()
            soup = BeautifulSoup(html_file, 'html.parser')
            item_list = soup.find_all("dl", class_="item-list-l")
            for item in item_list:

                item_name = item.find("dt").get_text()
                ahref_concept_art_url = item.find("a", title="設定画")
                concept_art_url = ahref_concept_art_url.get('href') if ahref_concept_art_url else ""
                genreAndRate = item.find_all("td")

                box_contents = item.find("ul", class_="image")

                if box_contents is not None:
                    box_contents = box_contents.find_all("li")
                    contents = list()
                    for sub_item in box_contents:
                        sub_item_name = re.findall("「(.*?)」", sub_item.get_text())[0]
                        sub_item_genre = re.findall(r'\（(.*?)\）', sub_item.get_text())[0]

                        ahref_subitem = item.find("a", title=sub_item_name)
                        image_url = ahref_subitem.get('href') if ahref_subitem else ""
                        contents.append({
                            "name(jp)": sub_item_name,
                            "name(en)": "",
                            "image_url": image_url,
                            "genre(jp)": sub_item_genre,
                            "genre(en)": sub_item_genre
                        })

                    parse_list.append({
                        "name(jp)": item_name,
                        "name(en)": "",
                        "concept_art": concept_art_url,
                        "genre(jp)": genreAndRate[0].get_text(),
                        "genre(en)": genreAndRate[0].get_text(),
                        "rate": genreAndRate[1].get_text(),
                        "contents": contents
                    })
                else:
                    ahref_item = item.find("a", title=item_name)
                    image_url = ahref_item.get('href') if ahref_item else ""
                    parse_list.append({
                        "name(jp)": item_name,
                        "name(en)": "",
                        "image_url": image_url,
                        "concept_art": concept_art_url,
                        "genre(jp)": genreAndRate[0].get_text(),
                        "genre(en)": genreAndRate[0].get_text(),
                        "rate": genreAndRate[1].get_text()
                    })

            return parse_list
    except:
        tk.messagebox.showerror(title="Parsing Failed", message="File parsing has failed")

def button_selectAndParseHTMLFile():
    filename = tk.filedialog.askopenfilename(initialdir = "/", title = "Select a File", filetypes = (("HTML", "*.html*"),("All Files", "*.*")))

    if len(filename) == 0:
        return

    parse_list = parseScratchHTML(filename)

    output_filetypes = [("JSON", "*.json"),("All Files", "*.*")]
    output_filename = tk.filedialog.asksaveasfile(filetypes = output_filetypes, initialfile="scratch_data", defaultextension = output_filetypes)

    json.dump(parse_list, output_filename, ensure_ascii=False, indent=4)
    output_filename.close()

    label_file_explorer.configure(text="Parsed: "+filename)

def downloadImages():
    json_filename = tk.filedialog.askopenfilename(initialdir = "/", title = "Select JSON", filetypes = (("JSON", "*.json"),("All Files", "*.*")))
    save_directory = tk.filedialog.askdirectory() + '/'

    label_file_explorer.configure(text="Start downloading")

    with open(json_filename) as json_file:
        item_list = json.load(json_file)

        option = image_filename_option.get()

        urls = list()

        for item in item_list:
        
            if item.get("concept_art"):
                filename = item["concept_art"].split('/')[-1] if option == "original" else "{item}_concept.jpg".format(item=item[option])
                urls.append({
                    "url": item["concept_art"],
                    "filename": save_directory + filename.replace('/','_')
                })
            
            if item.get("image_url"):
                filename = item["image_url"].split('/')[-1] if option == "original" else "{item}.jpg".format(item=item[option])
                urls.append({
                    "url": item["image_url"],
                    "filename": save_directory + filename.replace('/','_')
                })
            
            if item.get("contents"):
                for subitem in item["contents"]:
                    filename = subitem["image_url"].split('/')[-1] if option == "original" else "{item}.jpg".format(item=subitem[option])
                    urls.append({
                    "url": subitem["image_url"],
                    "filename": save_directory + filename.replace('/','_')
                })
        
        pool = ThreadPool(16)
        pool.map(downloadImage, urls)
    
    label_file_explorer.configure(text="Finish downloading")

def downloadImage(obj):
    filename = obj.get("filename")
    url = obj.get("url")
    print("Start " + filename + " " + url)
    if len(filename) == 0:
        return
    urllib.request.urlretrieve(url, filename)
    print("End " + filename + " " + url)

m = tk.Tk()
m.title("PSO2 Scratch Parser")
topFrame = tk.Frame(m)
middleFrame = tk.Frame(m)
bottomFrame = tk.Frame(m)
topFrame.grid(row = 0)
middleFrame.grid(row = 1)
bottomFrame.grid(row = 2)

label_file_explorer = tk.Label(topFrame, text = "No file has been selected", width = 100, height = 4, fg = "blue")
label_file_explorer.grid(column = 1, row = 1)

button_select = tk.Button(topFrame, text='Select HTML File', width=25, command=button_selectAndParseHTMLFile)
button_select.grid(column = 1, row = 2)

image_filename_option = tk.StringVar(m, "original")
tk.Radiobutton(middleFrame, text = "Original", variable = image_filename_option, value = "original").pack(side = tk.LEFT)
tk.Radiobutton(middleFrame, text = "JP Item Name", variable = image_filename_option, value = "name(jp)").pack(side = tk.LEFT)
tk.Radiobutton(middleFrame, text = "EN Item Name", variable = image_filename_option, value = "name(en)").pack(side = tk.LEFT)

button_select = tk.Button(bottomFrame, text='Download Images', width=25, command=downloadImages)
button_select.pack()

m.mainloop()

