""" 
    Form Manager - a form builder for Django

    author: Nikolaj Baer (nikolajbaer.us)
    sponsor: Cuker Design (cukerdesign.com)
    
    fork author: Rohit Sankaran

"""
VERSION = (0, 1, 1)

# Dynamically calculate the version based on VERSION tuple
if len(VERSION)>2 and VERSION[2] is not None:
    str_version = "%d.%d_%s" % VERSION[:3]
else:
    str_version = "%d.%d" % VERSION[:2]

__version__ = str_version
