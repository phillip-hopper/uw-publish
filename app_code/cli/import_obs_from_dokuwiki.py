#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#  Copyright (c) 2014, 2016 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@distantshores.org>
#  Phil Hopper <phillip_hopper@wycliffeassociates.org>
#
#  Requires PyGithub for unfoldingWord export.

from __future__ import print_function, unicode_literals

import codecs
import json
import re
import glob
import argparse
import datetime
from general_tools.git_wrapper import *
from general_tools.file_utils import write_file, load_json_object
from general_tools.smartquotes import smartquotes
from app_code.cli.obs_published_langs import ObsPublishedLangs
from app_code.obs.obs_classes import OBS
from app_code.util.languages import Language
import os
import sys

root = '/var/www/vhosts/door43.org/httpdocs/data/gitrepo'
pages = os.path.join(root, 'pages')
uwadmin_dir = os.path.join(pages, 'en/uwadmin')
export_dir = '/var/www/vhosts/door43.org/httpdocs/exports'
unfoldingWord_dir = '/var/www/vhosts/api.unfoldingword.org/httpdocs/obs/txt/1/'
rtl = ['he', 'ar', 'fa']
img_url = 'https://api.unfoldingword.org/obs/jpg/1/{0}/360px/obs-{0}-{1}.jpg'


status_headers = ('publish_date',
                  'version',
                  'contributors',
                  'checking_entity',
                  'checking_level',
                  'source_text',
                  'source_text_version',
                  'comments'
                  )

# regular expressions for splitting the chapter into components
title_re = re.compile(r'======.*', re.UNICODE)
ref_re = re.compile(r'//.*//', re.UNICODE)
frame_re = re.compile(r'{{[^{]*', re.DOTALL | re.UNICODE)
fr_id_re = re.compile(r'[0-5][0-9]-[0-9][0-9]', re.UNICODE)
num_re = re.compile(r'([0-5][0-9]).txt', re.UNICODE)

# regular expressions for removing text formatting
html_tag_re = re.compile(r'<.*?>', re.UNICODE)
link_tag_re = re.compile(r'\[\[.*?\]\]', re.UNICODE)
img_tag_re = re.compile(r'{{.*?}}', re.UNICODE)
img_link_re = re.compile(r'https://.*\.(jpg|jpeg|gif)', re.UNICODE)

# regular expressions for front matter
obs_name_re = re.compile(r'\| (.*)\*\*', re.UNICODE)
tag_line_re = re.compile(r'\n\*\*.*openbiblestories', re.UNICODE | re.DOTALL)
link_re = re.compile(r'\[\[.*?\]\]', re.UNICODE)


obs_frame_set = set([
    "01-01", "01-02", "01-03", "01-04", "01-05", "01-06", "01-07", "01-08", "01-09", "01-10", "01-11", "01-12", "01-13", "01-14", "01-15", "01-16",
    "02-01", "02-02", "02-03", "02-04", "02-05", "02-06", "02-07", "02-08", "02-09", "02-10", "02-11", "02-12",
    "03-01", "03-02", "03-03", "03-04", "03-05", "03-06", "03-07", "03-08", "03-09", "03-10", "03-11", "03-12", "03-13", "03-14", "03-15", "03-16",
    "04-01", "04-02", "04-03", "04-04", "04-05", "04-06", "04-07", "04-08", "04-09",
    "05-01", "05-02", "05-03", "05-04", "05-05", "05-06", "05-07", "05-08", "05-09", "05-10",
    "06-01", "06-02", "06-03", "06-04", "06-05", "06-06", "06-07",
    "07-01", "07-02", "07-03", "07-04", "07-05", "07-06", "07-07", "07-08", "07-09", "07-10",
    "08-01", "08-02", "08-03", "08-04", "08-05", "08-06", "08-07", "08-08", "08-09", "08-10", "08-11", "08-12", "08-13", "08-14", "08-15",
    "09-01", "09-02", "09-03", "09-04", "09-05", "09-06", "09-07", "09-08", "09-09", "09-10", "09-11", "09-12", "09-13", "09-14", "09-15",
    "10-01", "10-02", "10-03", "10-04", "10-05", "10-06", "10-07", "10-08", "10-09", "10-10", "10-11", "10-12",
    "11-01", "11-02", "11-03", "11-04", "11-05", "11-06", "11-07", "11-08",
    "12-01", "12-02", "12-03", "12-04", "12-05", "12-06", "12-07", "12-08", "12-09", "12-10", "12-11", "12-12", "12-13", "12-14",
    "13-01", "13-02", "13-03", "13-04", "13-05", "13-06", "13-07", "13-08", "13-09", "13-10", "13-11", "13-12", "13-13", "13-14", "13-15",
    "14-01", "14-02", "14-03", "14-04", "14-05", "14-06", "14-07", "14-08", "14-09", "14-10", "14-11", "14-12", "14-13", "14-14", "14-15",
    "15-01", "15-02", "15-03", "15-04", "15-05", "15-06", "15-07", "15-08", "15-09", "15-10", "15-11", "15-12", "15-13",
    "16-01", "16-02", "16-03", "16-04", "16-05", "16-06", "16-07", "16-08", "16-09", "16-10", "16-11", "16-12", "16-13", "16-14", "16-15", "16-16", "16-17", "16-18",
    "17-01", "17-02", "17-03", "17-04", "17-05", "17-06", "17-07", "17-08", "17-09", "17-10", "17-11", "17-12", "17-13", "17-14",
    "18-01", "18-02", "18-03", "18-04", "18-05", "18-06", "18-07", "18-08", "18-09", "18-10", "18-11", "18-12", "18-13",
    "19-01", "19-02", "19-03", "19-04", "19-05", "19-06", "19-07", "19-08", "19-09", "19-10", "19-11", "19-12", "19-13", "19-14", "19-15", "19-16", "19-17", "19-18",
    "20-01", "20-02", "20-03", "20-04", "20-05", "20-06", "20-07", "20-08", "20-09", "20-10", "20-11", "20-12", "20-13",
    "21-01", "21-02", "21-03", "21-04", "21-05", "21-06", "21-07", "21-08", "21-09", "21-10", "21-11", "21-12", "21-13", "21-14", "21-15",
    "22-01", "22-02", "22-03", "22-04", "22-05", "22-06", "22-07",
    "23-01", "23-02", "23-03", "23-04", "23-05", "23-06", "23-07", "23-08", "23-09", "23-10",
    "24-01", "24-02", "24-03", "24-04", "24-05", "24-06", "24-07", "24-08", "24-09",
    "25-01", "25-02", "25-03", "25-04", "25-05", "25-06", "25-07", "25-08",
    "26-01", "26-02", "26-03", "26-04", "26-05", "26-06", "26-07", "26-08", "26-09", "26-10",
    "27-01", "27-02", "27-03", "27-04", "27-05", "27-06", "27-07", "27-08", "27-09", "27-10", "27-11",
    "28-01", "28-02", "28-03", "28-04", "28-05", "28-06", "28-07", "28-08", "28-09", "28-10",
    "29-01", "29-02", "29-03", "29-04", "29-05", "29-06", "29-07", "29-08", "29-09",
    "30-01", "30-02", "30-03", "30-04", "30-05", "30-06", "30-07", "30-08", "30-09",
    "31-01", "31-02", "31-03", "31-04", "31-05", "31-06", "31-07", "31-08",
    "32-01", "32-02", "32-03", "32-04", "32-05", "32-06", "32-07", "32-08", "32-09", "32-10", "32-11", "32-12", "32-13", "32-14", "32-15", "32-16",
    "33-01", "33-02", "33-03", "33-04", "33-05", "33-06", "33-07", "33-08", "33-09",
    "34-01", "34-02", "34-03", "34-04", "34-05", "34-06", "34-07", "34-08", "34-09", "34-10",
    "35-01", "35-02", "35-03", "35-04", "35-05", "35-06", "35-07", "35-08", "35-09", "35-10", "35-11", "35-12", "35-13",
    "36-01", "36-02", "36-03", "36-04", "36-05", "36-06", "36-07",
    "37-01", "37-02", "37-03", "37-04", "37-05", "37-06", "37-07", "37-08", "37-09", "37-10", "37-11",
    "38-01", "38-02", "38-03", "38-04", "38-05", "38-06", "38-07", "38-08", "38-09", "38-10", "38-11", "38-12", "38-13", "38-14", "38-15",
    "39-01", "39-02", "39-03", "39-04", "39-05", "39-06", "39-07", "39-08", "39-09", "39-10", "39-11", "39-12",
    "40-01", "40-02", "40-03", "40-04", "40-05", "40-06", "40-07", "40-08", "40-09",
    "41-01", "41-02", "41-03", "41-04", "41-05", "41-06", "41-07", "41-08",
    "42-01", "42-02", "42-03", "42-04", "42-05", "42-06", "42-07", "42-08", "42-09", "42-10", "42-11",
    "43-01", "43-02", "43-03", "43-04", "43-05", "43-06", "43-07", "43-08", "43-09", "43-10", "43-11", "43-12", "43-13",
    "44-01", "44-02", "44-03", "44-04", "44-05", "44-06", "44-07", "44-08", "44-09",
    "45-01", "45-02", "45-03", "45-04", "45-05", "45-06", "45-07", "45-08", "45-09", "45-10", "45-11", "45-12", "45-13",
    "46-01", "46-02", "46-03", "46-04", "46-05", "46-06", "46-07", "46-08", "46-09", "46-10",
    "47-01", "47-02", "47-03", "47-04", "47-05", "47-06", "47-07", "47-08", "47-09", "47-10", "47-11", "47-12", "47-13", "47-14",
    "48-01", "48-02", "48-03", "48-04", "48-05", "48-06", "48-07", "48-08", "48-09", "48-10", "48-11", "48-12", "48-13", "48-14",
    "49-01", "49-02", "49-03", "49-04", "49-05", "49-06", "49-07", "49-08", "49-09", "49-10", "49-11", "49-12", "49-13", "49-14", "49-15", "49-16", "49-17", "49-18",
    "50-01", "50-02", "50-03", "50-04", "50-05", "50-06", "50-07", "50-08", "50-09", "50-10", "50-11", "50-12", "50-13", "50-14", "50-15", "50-16", "50-17"
])


def get_chapter(chapter_path, chapter_dict):

    with codecs.open(chapter_path, 'r', encoding='utf-8') as in_file:
        chapter = in_file.read()

    # Get title for chapter
    title = title_re.search(chapter)
    if title:
        chapter_dict['title'] = title.group(0).replace('=', '').strip()
    else:
        chapter_dict['title'] = u'NOT FOUND'
        print('NOT FOUND: title in {0}'.format(chapter_path))
    # Get reference for chapter
    ref = ref_re.search(chapter)
    if ref:
        chapter_dict['ref'] = ref.group(0).replace('/', '').strip()
    else:
        chapter_dict['ref'] = u'NOT FOUND'
        print('NOT FOUND: reference in {0}'.format(chapter_path))
    # Get the frames
    for fr in frame_re.findall(chapter):
        fr_lines = fr.split('\n')
        fr_se = fr_id_re.search(fr)
        if fr_se:
            fr_id = fr_se.group(0)
        else:
            fr_id = u'NOT FOUND'
            print('NOT FOUND: frame id in {0}'.format(chapter_path))
        frame = { 'id': fr_id,
                  'img': get_img(fr_lines[0].strip(), fr_id),
                  'text': get_text(fr_lines[1:])
                }
        chapter_dict['frames'].append(frame)
    # Sort frames
    chapter_dict['frames'].sort(key=lambda f: f['id'])
    return chapter_dict


def get_img(link, frame_id):
    link_se = img_link_re.search(link)
    if link_se:
        link = link_se.group(0)
        return link
    return img_url.format('en', frame_id)


def get_text(lines):
    """
    Groups lines into a string and runs through cleanText and smartquotes.
    """
    text = u''.join([x for x in lines[1:] if u'//' not in x]).strip()
    text = text.replace(u'\\\\', u'').replace(u'**', u'').replace(u'__', u'')
    text = clean_text(text)
    text = smartquotes(text)
    return text


def clean_text(text):
    """
    Cleans up text from possible DokuWiki and HTML tag pollution.
    """
    if html_tag_re.search(text):
        text = html_tag_re.sub(u'', text)
    if link_tag_re.search(text):
        text = link_tag_re.sub(u'', text)
    if img_tag_re.search(text):
        text = img_tag_re.sub(u'', text)
    return text


def write_page(outfile, p):
    write_file(outfile.replace('.txt', '.json'), p)


def get_dump(j):
    return json.dumps(j, sort_keys=True)


def load_lang_strings():
    langs = Language.load_languages()
    lang_dict = {}
    if not langs:
        return lang_dict

    for lang_obj in langs:  # :type Language
        lang_dict[lang_obj.lc] = lang_obj.ln

    return lang_dict


def get_json_dict(stat_file):
    return_val = {}
    if os.path.isfile(stat_file):
        for line in codecs.open(stat_file, 'r', encoding='utf-8'):

            if line.startswith(u'#') or line.startswith(u'\n') or line.startswith(u'{{') or u':' not in line:
                continue

            newline = clean_text(line)
            k, v = newline.split(u':', 1)
            return_val[k.strip().lower().replace(u' ', u'_')] = v.strip()
    return return_val


def clean_status(status_dict):
    for key in [k for k in status_dict.keys()]:
        if key not in status_headers:
            del status[key]
    return status


def export_unfolding_word(status_dict, git_dir, json_data, lang_code, github_org, front_matter, back_matter):
    """
    Exports JSON data for each language into its own Github repo.
    """
    write_page(os.path.join(git_dir, 'obs-{0}.json'.format(lang_code)), json_data)
    write_page(os.path.join(git_dir, 'obs-{0}-front-matter.json'.format(lang_code)), front_matter)
    write_page(os.path.join(git_dir, 'obs-{0}-back-matter.json'.format(lang_code)), back_matter)

    write_page(os.path.join(git_dir, 'status-{0}.json'.format(lang_code)), clean_status(status_dict))
    write_page(os.path.join(git_dir, 'README.md'), OBS.get_readme_text())

    gitCreate(git_dir)
    name = 'obs-{0}'.format(lang_code)
    desc = 'Open Bible Stories for {0}'.format(lang_code)
    url = 'http://unfoldingword.org/{0}/'.format(lang_code)
    githubCreate(git_dir, name, desc, url, github_org)
    commit_msg = str(status_dict)
    gitCommit(git_dir, commit_msg)
    gitPush(git_dir)


def uw_qa(jsd, lang_code, status_dict):
    """
    Implements basic quality control to verify correct number of frames,
    correct JSON formatting, and correct status headers.
    """
    flag = True
    for header in status_headers:
        if header not in status_dict:
            print('==> !! Cannot export {0}, status page missing header {1}'.format(lang_code, header))
            flag = False
    if 'NOT FOUND.' in str(jsd):
        print('==> !! Cannot export {0}, invalid JSON format'.format(lang_code))
        flag = False
    frame_list = []
    for c in json_lang['chapters']:
        for f in c['frames']:
            if len(f['text']) > 10:
                frame_list.append(f['id'])
    frameset = set(frame_list)
    obs_lang_diff = obs_frame_set.difference(frameset)
    if obs_lang_diff:
        print('==> !! Cannot export {0}, missing frames:'.format(lang_code))
        for x in obs_lang_diff:
            print(x)
        flag = False
    lang_obs_diff = frameset.difference(obs_frame_set)
    if lang_obs_diff:
        print('==> !! Cannot export {0}, extra frames:'.format(lang_code))
        for x in lang_obs_diff:
            print(x)
        flag = False
    return flag


def update_uw_admin_status_page():
    ObsPublishedLangs.update_page(ObsPublishedLangs.cat_url, ObsPublishedLangs.uw_stat_page)


def get_front_matter(lang_code, today_str):
    return_val = OBS.get_front_matter()
    return_val['language'] = lang_code
    return_val['date_modified'] = today_str

    front_path = os.path.join(pages, lang_code, 'obs', 'front-matter.txt')
    if os.path.exists(front_path):

        with codecs.open(front_path, 'r', encoding='utf-8') as in_file:
            front = in_file.read()

        for l in link_re.findall(front):
            if '|' in l:
                clean_url = l.split(u'|')[1].replace(u']', u'')
            else:
                clean_url = l.replace(u']', u'').replace(u'[', u'')
            front = front.replace(l, clean_url)

        return_val['front-matter'] = front

        obs_name_se = obs_name_re.search(front)
        if obs_name_se:
            return_val['name'] = obs_name_se.group(1)

        tag_line_se = tag_line_re.search(front)
        if tag_line_se:
            return_val['tagline'] = tag_line_se.group(0).split('**')[1].strip()

    return return_val


def get_back_matter(lang_code, today_str):
    return_val = OBS.get_front_matter()
    return_val['language'] = lang_code
    return_val['date_modified'] = today_str

    back_path = os.path.join(pages, lang_code, 'obs', 'back-matter.txt')
    if os.path.exists(back_path):
        with codecs.open(back_path, 'r', encoding='utf-8') as in_file:
            back = in_file.read()

        return_val['back-matter'] = clean_text(back)

    return return_val


if __name__ == '__main__':
    exit()
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-l', '--lang', dest="lang", default=False,
                        required=True, help="Language code of resource.")
    parser.add_argument('-e', '--export', dest="uwexport", default=False,
                        action='store_true', help="Export to unfoldingWord.")
    parser.add_argument('-t', '--testexport', dest="testexport", default=False,
                        action='store_true', help="Test export to unfoldingWord.")

    args = parser.parse_args(sys.argv[1:])
    lang = args.lang
    uw_export = args.uwexport
    test_export = args.testexport

    today = ''.join(str(datetime.date.today()).rsplit('-')[0:3])
    lang_dict = load_lang_strings()
    uw_cat_path = os.path.join(unfoldingWord_dir, 'obs-catalog.json')
    uw_catalog = load_json_object(uw_cat_path, [])
    uw_cat_langs = [x['language'] for x in uw_catalog]
    cat_path = os.path.join(export_dir, 'obs-catalog.json')
    catalog = load_json_object(cat_path, [])

    if 'obs' not in os.listdir(os.path.join(pages, lang)):
        print('OBS not configured in Door43 for {0}'.format(lang))
        sys.exit(1)
    app_words = get_json_dict(os.path.join(pages, lang, 'obs/app_words.txt'))
    lang_direction = 'ltr'
    if lang in rtl:
        lang_direction = 'rtl'
    json_lang = {'language': lang,
                 'direction': lang_direction,
                 'chapters': [],
                 'app_words': app_words,
                 'date_modified': today,
                 }
    page_list = glob.glob('{0}/{1}/obs/[0-5][0-9].txt'.format(pages, lang))
    page_list.sort()
    for page in page_list:
        json_chapter = {'number': num_re.search(page).group(1),
                        'frames': [],
                        }
        json_lang['chapters'].append(get_chapter(page, json_chapter))
    json_lang['chapters'].sort(key=lambda frame: frame['number'])
    json_lang_file_path = os.path.join(export_dir, lang, 'obs', 'obs-{0}.json'.format(lang))
    prev_json_lang = load_json_object(json_lang_file_path, {})
    cur_json = get_dump(json_lang)
    prev_json = get_dump(prev_json_lang)
    try:
        langstr = lang_dict[lang]
    except KeyError:
        print("Configuration for language {0} missing.".format(lang))
        sys.exit(1)
    status = get_json_dict(os.path.join(uwadmin_dir, lang, 'obs/status.txt'))
    lang_cat = {'language': lang,
                'string': langstr,
                'direction': lang_direction,
                'date_modified': today,
                'status': status,
                }
    if lang not in [x['language'] for x in catalog]:
        catalog.append(lang_cat)

    if str(cur_json) != str(prev_json):
        ([x for x in catalog if x['language'] == lang][0]['date_modified']) = today
        write_page(json_lang_file_path, cur_json)

    if test_export:
        print('Testing {0} export...'.format(lang))
        front_json = get_front_matter(lang, today)
        back_json = get_back_matter(lang, today)
        if not uw_qa(json_lang, lang, status):
            print('---> QA Failed.')
            sys.exit(1)
        print('---> QA Passed.')
        sys.exit()
    if uw_export:
        try:
            pw = open('/root/.github_pass', 'r').read().strip()
            g_user = githubLogin('dsm-git', pw)
            github_org = getGithubOrg('unfoldingword', g_user)
        except GithubException as e:
            print('Problem logging into Github: {0}'.format(e))
            sys.exit(1)

        unfolding_word_lang_dir = os.path.join(unfoldingWord_dir, lang)
        if 'checking_level' in status and 'publish_date' in status:
            if status['checking_level'] in ['1', '2', '3'] and status['publish_date'] == str(datetime.date.today()):
                print("==========")
                front_json = get_front_matter(lang, today)
                back_json = get_back_matter(lang, today)
                if not uw_qa(json_lang, lang, status):
                    print("==========")
                    sys.exit(1)
                print("---> Exporting to unfoldingWord: {0}".format(lang))
                export_unfolding_word(status, unfolding_word_lang_dir, cur_json,
                                      lang, github_org, front_json, back_json)
                if lang in uw_cat_langs:
                    uw_catalog.pop(uw_cat_langs.index(lang))
                    uw_cat_langs.pop(uw_cat_langs.index(lang))
                uw_catalog.append(lang_cat)
                print("==========")

    cat_json = get_dump(catalog)
    write_page(cat_path, cat_json)
    if uw_export:
        uw_cat_json = get_dump(uw_catalog)
        write_page(uw_cat_path, uw_cat_json)
        update_uw_admin_status_page()
