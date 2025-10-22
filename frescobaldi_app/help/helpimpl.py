# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2012 by Wilbert Berendsen
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# See http://www.gnu.org/licenses/ for more information.

"""
The help implementation.

A help page (or 'page') is a class, not an instance. Help pages
are never instantiated.

You should define the title() and body() methods and may define children()
and seealso().

"""

from __future__ import unicode_literals

import re

from PyQt4.QtGui import QAction, QShortcut, QKeySequence


all_pages = {}


class helpmeta(type):
    """Metaclass for the page base class.
    
    Does the following things to the page class:
    - automatically add the page to the all_pages dictionary
    - adds the 'name' attribute and set it to the class name
    - makes the four methods 'title', 'body', 'children' and 'seealso'
      a classmethod if they require one or more arguments, and a staticmethod
      if they require no argument.
    
    """
    def __new__(cls, name, bases, d):
        for n in ('title', 'body', 'children', 'seealso'):
            if n in d:
                if d[n].func_code.co_argcount > 0:
                    d[n] = classmethod(d[n])
                else:
                    d[n] = staticmethod(d[n])
        d['name'] = name
        page = type.__new__(cls, name, bases, d)
        all_pages[name] = page
        return page


class page(object):
    """Base class for help items.
    
    classes based on help are never instantiated; the class is simply used as a
    data container. Some methods should be defined, which are used as classmethod
    if they have an argument, or as staticmethod when they accept no arguments.
    
    The methods may return translated text, when the application changes
    language, the methods are called again.
    
    Set the popup class attribute to True to make the help topic a popup.
    """
    popup = False
    
    @classmethod
    def link(cls, title=None):
        return '<a href="help:{0}">{1}</a>'.format(cls.name, title or cls.title())
    
    def title():
        return ""
    
    def body():
        return ""
    
    def children():
        return ()
    
    def seealso():
        return ()


# This syntax to make 'page' use the metaclass works in both Python2 and 3
page = helpmeta(page.__name__, page.__bases__, dict(page.__dict__))


_template = '''\
{qt_detail}<html>
<head>
<style type="text/css">
body {{
  margin: 10px;
}}
</style>
<title>{title}</title>
</head>
<body>
{nav_up}
<h2>{title}</h2>
{body}
{nav_children}
{nav_next}
{nav_seealso}
<br/><hr width=80%/>
<address><center>{appname} {version}</center></address>
</body>
</html>
'''


def html(name):
    """Returns the HTML for the named help item."""
    from . import contents
    from info import appname, version
    page = all_pages.get(name, contents.nohelp)
    parents = [p for p in all_pages.values() if page in p.children()]
    
    qt_detail = '<qt type=detail>' if page.popup else ''
    title = striptags(page.title())
    nav_up = ''
    if parents and not page.popup:
        nav_up = '<p>{0} {1}</p>'.format(
            _("Up:"),
            ' '.join(p.link() for p in parents))
    body = markexternal(page.body())
    nav_children, nav_next, nav_seealso = '', '', ''
    if page.children():
        nav_children = '\n'.join('<div>{0}</div>'.format(p.link()) for p in page.children())
    else:
        html = []
        for p in parents:
            i = p.children().index(page)
            if i < len(p.children()) - 1:
                html.append('<div>{0} {1}</div>'.format(
                    _("Next:"), p.children()[i+1].link()))
        nav_next = '\n'.join(html)
    if page.seealso():
        html = []
        html.append("<p>{0}</p>".format(_("See also:")))
        html.extend('<div>{0}</div>'.format(p.link()) for p in page.seealso())
        nav_seealso = '\n'.join(html)
    return _template.format(**locals())


def markexternal(text):
    """Marks http(s)/ftp(s) links as external with an arrow."""
    pat = re.compile(r'''<a\s+.*?href\s*=\s*(['"])(ht|f)tps?.*?\1[^>]*>''', re.I)
    return pat.sub(r'\g<0>&#11008;', text)


def action(collection_name, action_name):
    """Returns a QAction from the application.
    
    May return None, if the named collection or action does not exist.
    
    """
    import actioncollectionmanager
    mgr = actioncollectionmanager.ActionCollectionManager.instances()[0]
    return mgr.action(collection_name, action_name)


def shortcut(item):
    """Returns a suitable text for the keyboard shortcut of the given item.
    
    Item may be a QAction, a QShortcut, a QKeySequence or a
    QKeySequence.StandardKey.
    
    The text is meant to be used in the help docs.
    
    """
    if isinstance(item, QAction):
        seq = item.shortcut()
    elif isinstance(item, QShortcut):
        seq = item.key()
    elif isinstance(item, QKeySequence.StandardKey):
        seq = QKeySequence(item)
    else:
        seq = item
    return seq.toString(QKeySequence.NativeText) or _("(no key defined)")



def menu(*titles):
    """Returns a nicely formatted list describing a menu option.
    
    e.g.
    
    menu('Edit', 'Preferences')
    
    yields something like:
    
    '<em>Edit-&gt;Preferences</em>'
    
    Single ampersands are removed and double ampersands are replaced with one.
    
    """
    rx = re.compile(r'(?<!&)&(?=[&\w])(?!\w+;)')
    return '<em>{0}</em>'.format('&#8594;'.join(rx.sub('', t) for t in titles))


def link(helppage, title=None):
    """Returns a HTML link to the given help page.
    
    The help page maybe a string name, or the class.
    If no title is given, the page's title is used.
    
    """
    if not isinstance(helppage, type):
        helppage = all_pages[helppage]
    return helppage.link(title)


def striptags(text):
    """Strips HTML tags from text."""
    return re.sub(r'<[^<>]+>', '', text)


