# not executable so that you can pick correct Python to run
# ziplib.py
# Lloyd Kvam's tool for creating a module from a bunch of .py files
# 4Oct2012

import zipfile, os

def main(zipname, pyfiles):
    '''Given a zipfile name and a list of files python files
    Build an importable zip file
    '''
    assert zipname.endswith('.zip')
    ziplib = zipfile.PyZipFile(zipname, mode='w',compression=zipfile.ZIP_DEFLATED)
    for pyfile in pyfiles:
        try:
            os.remove( pyfile+'c')
        except OSError, exc:
            if exc.errno == 2:
                pass
        ziplib.writepy(pyfile)
    ziplib.close()

if __name__ == '__main__':
    import sys

    try:
        main(sys.argv[1], sys.argv[2:])
    except:
        sys.exit(2)
    else:
        sys.exit(0)
