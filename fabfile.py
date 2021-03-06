from fabric.api import *

import os
import shutil
import time
import glob
import hashlib
import yaml

env.shell = "/bin/sh -c"
env.command_prefixes = [ 'export PATH=$HOME/.virtualenvs/hyde/bin:$PATH',
                         'export VIRTUAL_ENV=$HOME/.virtualenvs/hyde' ]

def _hyde(args):
    return local('python ../hyde/h %s' % args)

def regen():
    """Regenerate dev content"""
    local('rm -rf deploy')
    gen()

def gen():
    """Generate dev content"""
    _hyde('gen')

def serve():
    """Serve dev content"""
    _hyde('serve -a 0.0.0.0')

def sprite():
    """Regenerate sprites"""
    import Image
    conf = {
        'imgdir': "content/media/images/l/sprites",
        'sprite': "content/media/images/l/sprite.png",
        'css': "content/media/css/luffy.sprite.less",
        'class': "lf-sprite",
        'spacer': 2,
        }
    images = glob.glob(os.path.join(conf['imgdir'], '*.png'))
    images.sort()

    print "[+] Generate sprites for %s" % ", ".join([os.path.basename(i) for i in images])
    css = """/* -*- css -*- */
/* Autogenerated. */

.%(class)s {
    background: url('%(sprite)s') no-repeat left top;
    display: inline-block;
}
""" % { 'class': conf['class'],
        'sprite': os.path.relpath(conf['sprite'],
                                  os.path.dirname(conf['css'])),
        }

    # Get the total height and max width
    width = 0
    height = 0
    for image in images:
        im = Image.open(image)
        height += im.size[1]
        if im.size[0] > width:
            width = im.size[0]
    height += (len(images) - 1) * conf['spacer']
    sprite = Image.new('RGBA', (width, height))
    height = 0
    for image in images:
        im = Image.open(image)
        sprite.paste(im, (0, height))
        css += """
.%(class)s-%(name)s {
    .%(class)s;
    background-position: 0px %(offset)spx;
    width: %(width)spx;
    height: %(height)spx;
}
""" % { "class": conf['class'],
        "name":   os.path.basename(image).split(".")[0],
        "offset": -height,
        "width":  im.size[0],
        "height": im.size[1] }
        height += im.size[1] + conf['spacer']
    print "[+] Write sprite to %s" % conf['sprite']
    sprite.save(conf['sprite'], "PNG", optimize=True)
    print "[+] Write CSS to %s" % conf['css']
    file(conf['css'], "w").write(css)

def build():
    """Build production content"""
    local("git checkout master")
    local("rm -rf .final/*")
    conf = "site-production.yaml"
    media = yaml.load(file(conf))['media_url']
    _hyde('gen -c %s' % conf)
    with lcd(".final"):
        for p in [ 'media/js/*.js',
                   'media/css/*.css',
                   'media/images/l/sprite.png' ]:
            files = local("echo %s" % p, capture=True).split(" ")
            for f in files:
                # Compute hash
                md5 = local("md5sum %s" % f, capture=True).split(" ")[0][:8]
                print "[+] MD5 hash for %s is %s" % (f, md5)
                # New name
                root, ext = os.path.splitext(f)
                newname = "%s.%s%s" % (root, md5, ext)
                # Symlink
                local("ln -s %s %s" % (os.path.basename(f), newname))
                # Remove deploy/media
                f = f[len('media/'):]
                newname = newname[len('media/'):]
                if ext == ".png":
                    # Fix CSS
                    local("sed -i 's+%s+%s+g' media/css/*.css" % (f, newname))
                else:
                    # Fix HTML
                    local(r"find . -name '*.html' -type f -print0 | xargs -r0 sed -i "
                          '"'
                          r"s+\([\"']\)%s%s\1+\1%s%s\1+g"
                          '"' % (media, f, media, newname))
        local("git add *")
        local("git diff --stat HEAD")
        answer = prompt("More diff?", default="yes")
        if answer.lower().startswith("y"):
            local("git diff --word-diff HEAD")
        answer = prompt("Keep?", default="yes")
        if answer.lower().startswith("y"):
            local('git commit -a -m "Autocommit"')
        else:
            local("git reset --hard")
            local("git clean -d -f")

def push():
    """Push production content to ace"""
    local("git push github")
    local("git push ace.luffy.cx")


    # media.luffy.cx
    local("rsync --exclude=.git -a .final/media/ ace.luffy.cx:/srv/www/luffy/media/")

    # HTML
    local("rsync --exclude=.git -a .final/ ace.luffy.cx:/srv/www/luffy/")
