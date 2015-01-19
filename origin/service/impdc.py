import imp
import sys


def impdc(name):
    sys.path.append('//home//kimice//PycharmProjects//mytest//dataservice')
    fp, pathname, description = imp.find_module(name)
    try:
        return imp.load_module(name, fp, pathname, description)
    finally:
        if fp:
            fp.close()