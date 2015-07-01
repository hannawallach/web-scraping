import os
from contextlib import contextmanager
from hashlib import md5
from urllib2 import URLError


def makedir(dirname):
    """
    Creates the specified directory if it doesn't exist, along with
    any intermediate directories.

    Arguments:

    dirname -- directory name (inc. path)
    """

    if not os.path.exists(dirname):
        os.makedirs(dirname)


@contextmanager
def safe_write(filename):
    """
    Yields the specified file, opened for writing. If there's a
    problem in doing this, and the specified file already exists,
    delete the file and raise an exception.

    Arguments:

    filename -- filename (inc. path)
    """

    try:
        with file(filename, 'wb') as f:
            yield f
    except:
        if os.path.exists(filename):
            os.remove(filename)
            raise


def url2filename(url):
    """
    Returns the md5 hash (as a hex string) of the specified url.

    Arguments:

    url -- url for which to create the hash
    """

    return md5(url).hexdigest()


def _download(br, url, cache, data=None):
    """
    Uses the specified Browser object to download the contents of the
    specified url to the specified cache directory. Returns the name
    of the file to which the url contents were downloaded.

    Arguments:

    br -- Browser object
    url -- url
    cache -- cache directory

    Keyword arguments:

    data -- Browser data (e.g., username/password)
    """

    makedir(cache)

    filename = os.path.join(cache, url2filename(url))

    if not os.path.exists(filename):
        with safe_write(filename) as f:
            f.write(br.open(url, data).read())

    return filename


def download(br, url, cache, data=None, tries=3):
    """
    Tries (the specified number of times) to use the specified
    Browser object to download the contents of the specified url to
    the specified cache directory. Returns the name of the file to
    which the url contents were downloaded.

    Arguments:

    br -- Browser object
    url -- url
    cache -- cache directory

    Keyword arguments:

    data -- Browser data (e.g., username/password)
    tries -- number of times to try
    """


    for i in xrange(tries):
        try:
            return _download(br, url, cache, data)
        except URLError as last_exception:
            pass

    raise last_exception


def download_url(br, url, cache, data=None, tries=3):
    """
    Tries (the specified number of times) to use the specified
    Browser object to download the contents of the specified url to
    the specified cache directory. After each try, checks that the
    file to which the url contents were downloaded can be read and
    isn't empty; if both are true, returns the name of the file;
    otherwise, deletes the file and tries again.

    Arguments:

    br -- Browser object
    url -- url
    cache -- cache directory

    Keyword arguments:

    data -- Browser data (e.g., username/password)
    tries -- number of times to try
    """

    for i in xrange(tries):

        filename = download(br, url, cache, data)

        try:
            contents = file(filename).read()
            assert contents, 'Empty file'
            return filename
        except AssertionError as last_exception:
            os.remove(filename)

    raise last_exception
