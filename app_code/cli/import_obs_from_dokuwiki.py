#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#  Copyright (c) 2016 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Phil Hopper <phillip_hopper@wycliffeassociates.org>
#

from __future__ import print_function, unicode_literals
import argparse
import json
import os
import re
import sys
from general_tools.file_utils import write_file
from app_code.obs.obs_classes import OBS, OBSManifest, OBSManifestEncoder, OBSSourceTranslation
from general_tools.print_utils import print_warning, print_error, print_ok
from general_tools.url_utils import get_languages, join_url_parts, get_url


# regular expressions for replacing Dokuwiki formatting
h1_re = re.compile(r'====== (.*?) ======', re.UNICODE)
h2_re = re.compile(r'===== (.*?) =====', re.UNICODE)
h3_re = re.compile(r'==== (.*?) ====', re.UNICODE)
h4_re = re.compile(r'=== (.*?) ===', re.UNICODE)
h5_re = re.compile(r'== (.*?) ==', re.UNICODE)
italic_re = re.compile(r'[^:]//(.*?)//', re.UNICODE)
bold_re = re.compile(r'\*\*(.*?)\*\*', re.UNICODE)
image_re = re.compile(r'\{\{(.*?)\}\}', re.UNICODE)
link_re = re.compile(r'\[\[(http[s]*:[^:]*)\|(.*?)\]\]', re.UNICODE)
li_re = re.compile(r'[ ]{1,3}(\*)', re.UNICODE)
li_space_re = re.compile(r'^(\*.*\n)\n(?=\*)', re.UNICODE + re.MULTILINE)

# regular expressions for removing text formatting
html_tag_re = re.compile(r'<.*?>', re.UNICODE)
link_tag_re = re.compile(r'\[\[.*?\]\]', re.UNICODE)
img_tag_re = re.compile(r'{{.*?}}', re.UNICODE)
img_link_re = re.compile(r'https://.*\.(jpg|jpeg|gif)', re.UNICODE)


def import_obs_from_dw(lang_data, git_repo, out_dir):
    """
    Gets OBS files from Github repository, converts them to markdown, and saves them locally
    :param dict lang_data:
    :param str git_repo:
    :param str out_dir:
    :return: None
    """
    lang_code = lang_data['lc']

    # pre-flight checklist
    if git_repo[-1:] == '/':
        git_repo = git_repo[:-1]

    # get the source files from the git repository
    base_url = git_repo.replace('github.com', 'raw.githubusercontent.com')

    # initialize
    obs_obj = OBS()
    obs_obj.direction = lang_data['ld']
    obs_obj.language = lang_code

    # download needed files from the repository
    files_to_download = []
    for i in range(1, 51):
        files_to_download.append(str(i).zfill(2) + '.txt')

    # download OBS story files
    story_dir = os.path.join(out_dir, 'content')
    for file_to_download in files_to_download:
        download_obs_file(base_url, file_to_download, story_dir)

    # download front and back matter
    download_obs_file(base_url, 'front-matter.txt', os.path.join(out_dir, 'content', '_front'))
    download_obs_file(base_url, 'back-matter.txt', os.path.join(out_dir, 'content', '_back'))

    # get the status
    uwadmin_dir = 'https://raw.githubusercontent.com/Door43/d43-en/master/uwadmin'
    status = get_json_dict(join_url_parts(uwadmin_dir, lang_code, 'obs/status.txt'))
    manifest = OBSManifest()
    manifest.status['pub_date'] = status['publish_date']
    manifest.status['contributors'] = re.split(r'\s*;\s*|\s*,\s*', status['contributors'])
    manifest.status['checking_level'] = status['checking_level']
    manifest.status['comments'] = status['comments']
    manifest.status['version'] = status['version']
    manifest.status['pub_date'] = status['publish_date']
    manifest.status['checking_entity'] = re.split(r'\s*;\s*|\s*,\s*', status['checking_entity'])

    source_translation = OBSSourceTranslation()
    source_translation.language_slug = status['source_text']
    source_translation.resource_slug = 'obs'
    source_translation.version = status['source_text_version']

    manifest.status['source_translations'].append(source_translation)

    manifest.language['slug'] = lang_code
    manifest.language['name'] = lang_data['ang']
    manifest.language['dir'] = lang_data['ld']

    manifest_str = json.dumps(manifest, sort_keys=False, indent=2, cls=OBSManifestEncoder)
    write_file(os.path.join(out_dir, 'manifest.json'), manifest_str)


def download_obs_file(base_url, file_to_download, out_dir):

    download_url = join_url_parts(base_url, 'master/obs', file_to_download)

    try:
        print('Downloading {0}...'.format(download_url), end=' ')
        dw_text = get_url(download_url).decode('utf-8')

    finally:
        print('finished.')

    print('Converting {0} to markdown...'.format(file_to_download), end=' ')
    md_text = replace_dokuwiki_text(dw_text)
    print('finished.')

    save_as = os.path.join(out_dir, file_to_download.replace('.txt', '.md'))

    print('Saving {0}...'.format(save_as), end=' ')
    write_file(save_as, md_text)
    print('finished.')


def replace_dokuwiki_text(text):
    """
    Cleans up text from possible DokuWiki and HTML tag pollution.
    :param str text:
    :return: str
    """
    global h1_re, h2_re, h3_re, h4_re, h5_re, italic_re, bold_re, image_re, link_re, li_re, li_space_re

    text = text.replace('\r', '')
    text = text.replace('\n\n\n\n\n', '\n\n')
    text = text.replace('\n\n\n\n', '\n\n')
    text = text.replace('\n\n\n', '\n\n')
    text = h1_re.sub(r'# \1', text)
    text = h2_re.sub(r'## \1', text)
    text = h3_re.sub(r'### \1', text)
    text = h4_re.sub(r'#### \1', text)
    text = h5_re.sub(r'##### \1', text)
    text = italic_re.sub(r'_\1_', text)
    text = bold_re.sub(r'__\1__', text)
    text = image_re.sub(r'![OBS Image](\1)', text)
    text = link_re.sub(r'[\2](\1)', text)
    text = li_re.sub(r'\1', text)
    text = li_space_re.sub(r'\1', text)

    old_url = 'https://api.unfoldingword.org/obs/jpg/1/en/'
    cdn_url = 'https://cdn.door43.org/obs/jpg/'
    text = text.replace(old_url, cdn_url)

    return text


def clean_text(text):
    """
    Cleans up text from possible DokuWiki and HTML tag pollution.
    """
    global html_tag_re, link_tag_re, img_tag_re
    if html_tag_re.search(text):
        text = html_tag_re.sub('', text)
    if link_tag_re.search(text):
        text = link_tag_re.sub('', text)
    if img_tag_re.search(text):
        text = img_tag_re.sub('', text)
    return text


def get_json_dict(download_url):
    return_val = {}
    status_text = get_url(download_url).decode('utf-8')
    status_text = status_text.replace('\r', '')
    lines = filter(bool, status_text.split('\n'))

    for line in lines:

        if line.startswith('#') or line.startswith('\n') or line.startswith('{{') or ':' not in line:
            continue

        newline = clean_text(line)
        k, v = newline.split(':', 1)
        return_val[k.strip().lower().replace(' ', '_')] = v.strip()

    return return_val


if __name__ == '__main__':
    print()
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-l', '--lang', dest='lang', default=False,
                        required=True, help='Language code of resource.')
    parser.add_argument('-r', '--gitrepo', dest='gitrepo', default=False,
                        required=True, help='Git repository where the source can be found.')
    parser.add_argument('-o', '--outdir', dest='outdir', default=False,
                        required=True, help='The output directory for markdown files.')

    args = parser.parse_args(sys.argv[1:])

    # get the language data
    try:
        print('Downloading language data...', end=' ')
        langs = get_languages()
    finally:
        print('finished.')

    this_lang = next(l for l in langs if l['lc'] == args.lang)

    if not this_lang:
        print_error('Information for language "{0}" was not found.'.format(args.lang))
        sys.exit(1)

    if 'github' not in args.gitrepo:
        print_warning('Currently only github repositories are supported.')
        sys.exit(0)

    # do the import
    import_obs_from_dw(this_lang, args.gitrepo, args.outdir)

    print_ok('ALL FINISHED: ', 'Please check the output directory.')
