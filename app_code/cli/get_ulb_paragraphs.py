#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#    This file gets chunk information from the api.
#
#    Copyright (c) 2016 unfoldingWord
#    http://creativecommons.org/licenses/MIT/
#    See LICENSE file for details.
#
#    Contributors:
#    Phil Hopper <phillip_hopper@wycliffeassociates.org>

from __future__ import print_function, unicode_literals

import codecs
import glob
import re
from collections import OrderedDict

from general_tools.file_utils import write_file, make_dir, unzip
import json
import os
from general_tools.url_utils import download_file

paragraph_re = re.compile(r'\\p\s\\v\s(\d{1,3}[-,d]*)')

if __name__ == '__main__':
    ulb_repo = 'https://github.com/Door43/ulb-en/archive/master.zip'

    download_dir = '/tmp/ulb'
    make_dir(download_dir)
    downloaded_file = '{0}/ulb-en.zip'.format(download_dir)
    file_to_download = ulb_repo

    # download the repository
    try:
        print('Downloading {0}...'.format(file_to_download), end=' ')
        if not os.path.isfile(downloaded_file):
            download_file(file_to_download, downloaded_file)
    finally:
        print('finished.')

    try:
        print('Unzipping...'.format(downloaded_file), end=' ')
        unzip(downloaded_file, download_dir)
    finally:
        print('finished.')

    # get the book directories
    repo_dir = os.path.join(download_dir, 'ulb-en-master')
    dirs = os.walk(repo_dir).next()[1]

    # remove the .github directory
    dirs = [d for d in dirs if d[0] != '.']
    dirs.sort()

    # loop through the books
    bible_data = []
    for d in dirs:
        book_info = d.split('-')
        book_data = OrderedDict([('usfm_num', book_info[0]), ('usfm_id', book_info[1]), ('chapters', [])])

        files = glob.glob('{0}/{1}/*.usfm'.format(repo_dir, d))
        files.sort()
        for f in files:

            # skip the 00 files
            file_name = f.rpartition('/')[2]
            if file_name == '00.usfm' or file_name == '000.usfm':
                continue

            file_info = file_name.split('.')
            with codecs.open(f, 'r', encoding='utf-8-sig') as in_file:
                content = in_file.read()

            content = content.replace('\r', '')

            chapter_data = OrderedDict([('number', file_info[0]), ('paragraph_before', [])])

            for verse_num in paragraph_re.findall(content):
                split_num = re.split(',-', verse_num)
                chapter_data['paragraph_before'].append(split_num[0])

            book_data['chapters'].append(chapter_data)

        bible_data.append(book_data)

    #     print(d)
    #     old_chunks = json.loads(get_url(api_url.format(d)))
    #     chunks = []
    #
    #     for old_chunk in old_chunks:
    #         chap_num = int(old_chunk['chp'])
    #         found = [x for x in chunks if x['chapter'] == chap_num]
    #         if found:
    #             chunk = found[0]
    #         else:
    #             chunk = {'chapter': chap_num, 'first_verses': []}
    #             chunks.append(chunk)
    #
    #         chunk['first_verses'].append(int(old_chunk['firstvs']))
    #

    s = json.dumps(bible_data, indent=2, separators=(',', ': '))
    s = re.sub(r'(",)\s+("\d)', r'\1 \2', s)
    s = re.sub(r'(\[)\s+("\d)', r'\1\2', s)
    s = re.sub(r'(\d")\s+(\])', r'\1\2', s)
 
    file_name = '/home/team43/paragraphs.json'
    write_file(file_name, s)

    print('Finished')
