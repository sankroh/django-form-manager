from setuptools import setup, find_packages

version = __import__('formmanager').__version__

setup(
    name = 'django-form-manager',
    version = version,
    description = "A form builder for Django",
    long_description = """Django form manager provides an interface for the user to build and export forms and form data via the admin.""",
    author = 'Nikolaj Baer',
    author_email = 'nikolaj@cukerdesign.com',
    url = 'http://django-form-manager.googlecode.com/',
    license = 'New BSD License',
    platforms = ['any'],
    classifiers = ['Development Status :: 4 - Beta',
                   'Environment :: Web Environment',
                   'Framework :: Django',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: BSD License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Topic :: Blog'],
    packages = find_packages(),
    include_package_data = True,
)
