import os
import pathlib
import re
import html
from shutil import copyfile
import json

import click
import mistune
import frontmatter
from jinja2 import Environment, FileSystemLoader
from slugify import slugify
from PIL import Image


@click.group()
def main():
    """click"""


def load_mds(path):
    glob = pathlib.Path(path).glob("*.md")
    results = []
    md = mistune.Markdown()
    for item in sorted(glob, reverse=True):
        matter = frontmatter.load(item)
        data = dict(matter)
        data['body'] = md(matter.content)
        data['filename'] = pathlib.Path(item).stem
        results.append(data)

    return results


def create_thumbnail(notebook):
    # check whether thumbnail exists
    filename = notebook['slug']
    thumb_file = f'work/thumb/{filename}.png'
    if not os.path.isfile(thumb_file):
        image_file = notebook['ogimg']

        if os.path.isfile(image_file):
            ogimg = Image.open(image_file)
            ogimg.thumbnail((200, 100))
            ogimg.save(thumb_file)


def load_notebooks(path):
    glob = pathlib.Path(path).glob("*.html")
    results = []
    for item in sorted(glob, reverse=True):
        data = {}
        with open(item, encoding='utf-8') as f:
            body = f.read()
            data['body'] = body
            # this is a bit too fragile ...
            title_match = re.search('<h1 id=\".+\">(?P<title>.+)<a class=\"anchor', body)
            data['title'] = title_match.groupdict().get('title')
            # slugify was confused from html entities
            data['slug'] = slugify(html.unescape(data['title']))
        data['filename'] = pathlib.Path(item).stem
        # TODO once the folders are back to normal name clean this up
        ogimg_file = f'notebooks/{data["filename"]}/ogimg.png'
        if os.path.isfile(ogimg_file):
            data['ogimg'] = ogimg_file
        ogimg_file = f'notebooks/m_{data["filename"]}/ogimg.png'
        if os.path.isfile(ogimg_file):
            data['ogimg'] = ogimg_file
        create_thumbnail(data)
        results.append(data)

    return results


@click.command()
def pub():
    # ntbs = load_mds('notebooks')
    ntbs = load_notebooks('work')
    env = Environment(
        loader=FileSystemLoader('templates'),
    )
    for notebook in ntbs:
        with open(f'public/{notebook["slug"]}.html', 'w', encoding='utf-8') as cp:
            cp.write(env.get_template('ntb.html.j2').render(piece=notebook))
        copyfile(f'work/thumb/{notebook["slug"]}.png', f'public/img/thumb/{notebook["slug"]}.png')

    with open(f'public/index.html', 'w', encoding='utf-8') as index:
        index.write(env.get_template('index.html.j2').render(notebooks=ntbs))

    # todo copy sources/static to public


main.add_command(pub)

if __name__ == "__main__":
    main()
