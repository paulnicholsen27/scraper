import requests
import re
import os
import urllib2
import sys
import shutil

from bs4 import BeautifulSoup

from auth import username, password

from pprint import pprint

from scraper import get_form_id, login, empty_folder

music_url = "http://gmcw.groupanizer.com/g/music"

all_music_url = """https://gmcw.groupanizer.com/g/music?
field_active_category_value=2&field_music_categories_tid=61
&field_voicing_value=&field_solo_voices_value=&field_reference_value=
&page={}
"""

def parse_page(session, ):
    sheet_music_links = []
    recording_links = []
    form_build_id, form_token = get_form_id(session, music_url)
    cookies = login(session, username, password)
    music_page = session.get(
        all_music_url.format(0),
        cookies=cookies)
    soup = BeautifulSoup(music_page.content)
    links = ['http://gmcw.groupanizer.com'+link.get('href') for link in set(soup.find_all("a", "field_music_files"))]
    import ipdb; ipdb.set_trace()
    for link in links:
        page = session.get(link, cookies=cookies)
        soup = BeautifulSoup(page.content)
        for music_link in soup.find_all('a'):
            if music_link.get('href').endswith('.pdf'):
                sheet_music_links.append(
                    (music_link.text, music_link.get('href')))
            elif music_link.get('href').endswith('.mp3'):
                recording_links.append(
                    (music_link.text, music_link.get('href')))
    return sheet_music_links, recording_links, cookies


def write_sheet_music_to_file(session, sheet_music_links, directory_str):
    '''takes as input list of music links and writes all sheet music
        to specified directory_str for that concert period'''
    for filename in sheet_music_links:
        new_filename = filename[0].replace('/', '_')
        if new_filename.find('.pdf') == -1:
            new_filename += '.pdf'
        f = open(directory_str + new_filename, 'wb')
        f.write(session.get(filename[1]).content)
        f.close()

def write_recording_to_file(session, link, file_path, cookies):
    '''downloads all recording sessions to proper directories'''
    song = session.get(link, cookies=cookies)
    with open(file_path+'.mp3', 'wb') as handle:
        for block in song.iter_content(1024):
            if not block:
                break
            handle.write(block)


def process_recording_links(session, recording_links, directory_str, cookies):
    '''sends recordings and respective directory strings to be written'''
    upper_directory = directory_str + "T1T2/"
    lower_directory = directory_str + "B1B2/"
    full_directory = directory_str + "full/"
    for directory in [upper_directory, lower_directory, full_directory]:
        if not os.path.exists(directory):
            os.makedirs(directory)
    for recording_link in recording_links:
        if recording_link[0] != "":
            title = recording_link[0]
            url = recording_link[1]
            if any(voice_part in title for voice_part in ['B1', 'B2', 'BB']):
                voiced_directory = lower_directory
            elif any(voice_part in title for voice_part in ['T1', 'T2', 'TT']):
                voiced_directory = upper_directory
            else:
                voiced_directory = full_directory
            fullpath = '{0}{1}'.format(
                voiced_directory, title.replace('/', '_'))
            if not os.path.isfile(fullpath):
                if url.lower().find('.mp3') != -1:
                    write_recording_to_file(
                        session, url, fullpath, cookies)

def main():
    session = requests.session()
    sheet_music_links, recording_links, cookies = parse_page(session)
    base_directory_str = '/Users/paulnichols/Dropbox/chorus_music/'
    if not os.path.isdir(base_directory_str):
        base_directory_str = "/Users/pnichols/Dropbox/chorus_music/"  # if on work computer or somewhere else dumb
    sheet_music_directory = base_directory_str + "sheet_music/"
    recording_directory = base_directory_str + "recordings/"
    for directory in [sheet_music_directory, recording_directory]:
        if not os.path.exists(directory):
            os.makedirs(directory)
    empty_folder(sheet_music_directory, recording_directory)
    write_sheet_music_to_file(session, sheet_music_links, sheet_music_directory)
    process_recording_links(session, recording_links, recording_directory, cookies)

if __name__ == '__main__':
    main()