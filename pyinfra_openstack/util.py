from os import path


def get_package_path(*paths):
    return path.join(path.dirname(__file__), *paths)


def get_template_path(filename):
    return get_package_path('templates', filename)
