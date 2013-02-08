from __future__ import with_statement

from google.appengine.api import files
from google.appengine.ext.blobstore import BlobInfo

from django.conf import settings
from django.core.cache import cache

from djangoappengine.storage import BlobstoreUploadedFile

import time

import logging

def handle_blob_upload(uploaded_file, expected_file_name, expected_file_size):
    """ Handle chunked, resumable blobstore uploads by:

        * creating a new blobstore file via _get_write_blob() or getting an existing
        blobstore_file_name out of cache.

        * Storing a cached blobstore_file_name for use in future requests.

        Returns the blob, the blobstore_file_name and a finalized boolean indicating
        whether .finalize() has been called on the blob or not. Finalize() is only called
        when all chunks have been written to the blobstore file.

        This could be adapted to use Sessions or some other temporary storage instead.
    """
    info = {
        'name': uploaded_file.name,
        'size': uploaded_file._get_size(),
        'type': uploaded_file.content_type,
        'expected_name': expected_file_name,
        'expected_size': expected_file_size
    }

    existing_blobstore_file_name = cache.get("%s::%s::blobstore_file_name" % (settings.APP_NAME,
                                                                              expected_file_name))

    blob, blobstore_file_name, blob_finalized = _get_write_blob(uploaded_file, info,
                                                                blobstore_file_name=existing_blobstore_file_name)

    if not existing_blobstore_file_name and blobstore_file_name:
        #Store the blobstore_file_name so it can be used in future requests
        cache.set("%s::%s::blobstore_file_name" % (settings.APP_NAME, expected_file_name),
                  blobstore_file_name, settings.DEFAULT_CACHE_TIMEOUT)

    logging.debug("handle_upload: blob %s, blobstore_file_name %s, finalised: %s" % (blob,
                                                                                     blobstore_file_name,
                                                                                     blob_finalized))

    if blob_finalized:
        #The blob has been finalized so these aren't needed any longer
        cache.delete("%s::%s::blobstore_file_name" % (settings.APP_NAME, expected_file_name))
        cache.delete("%s::%s::uploaded_bytes" % (settings.APP_NAME, blobstore_file_name))

    return blob, blobstore_file_name, blob_finalized


def _create_blob(info):
    """ Create a new blobstore file using app engine's file API"""
    return files.blobstore.create(mime_type=info['type'],
                                  _blobinfo_uploaded_filename=info['expected_name'])


def _get_write_blob(uploaded_file, info, blobstore_file_name=None):
    """ Write data to a blobstore file; either create a new blobstore file using
    the uploded_file or append to an existing blobstore file by passing in an
    existing blobstore_file_name. """

    #If no existing blobstore file name is provided, create a new one
    if blobstore_file_name is None:
        blobstore_file_name = _create_blob(info)

    #Append data to blobstore file
    append_string_to_blobstore_file(blobstore_file_name, uploaded_file.read())

    #Write the uploaded bytes to cache; used for resuming uploads
    uploaded_bytes = _set_and_get_uploaded_bytes(blobstore_file_name, info['expected_name'],
                                                 uploaded_file.size)
    expected_bytes = info['expected_size']

    logging.debug("_get_write_blob, uploaded_bytes: %s, expected_bytes: %s" % (uploaded_bytes,
                                                                               expected_bytes))

    finalize = False
    if (uploaded_bytes and expected_bytes) is not None:
        if int(uploaded_bytes) == int(expected_bytes):
            finalize = True

    if finalize:
        files.finalize(blobstore_file_name)
        blobstore_key = get_blobstore_key(blobstore_file_name)
        return get_blobstore_uploaded_file(blobstore_key), blobstore_file_name, True

    return None, blobstore_file_name, False


def _set_and_get_uploaded_bytes(blobstore_file_name, file_name, new_bytes):
    """Store the currently uploaded_bytes in cache and return the uploaded_bytes"""
    uploaded_bytes = _get_uploaded_bytes(file_name)
    if uploaded_bytes:
        uploaded_bytes += new_bytes
    else:
        uploaded_bytes = new_bytes
    cache.set("%s::%s::uploaded_bytes" % (settings.APP_NAME, blobstore_file_name),
              uploaded_bytes, settings.DEFAULT_CACHE_TIMEOUT)
    return uploaded_bytes


def _get_uploaded_bytes(file_name):
    """ Convenience method for fetching uploaded_bytes from cache """
    blobstore_file_name = cache.get("%s::%s::blobstore_file_name" % (settings.APP_NAME, file_name))
    uploaded_bytes = cache.get("%s::%s::uploaded_bytes" % (settings.APP_NAME, blobstore_file_name))
    return uploaded_bytes


def get_blobstore_key(blobstore_file_name):
    while True:
        # work around for bug http://code.google.com/p/googleappengine/issues/detail?id=4872
        # discussion: https://groups.google
        # .com/group/google-appengine/browse_thread/thread/4411a53814bbfd3e
        blobstore_key = files.blobstore.get_blob_key(blobstore_file_name)
        if blobstore_key:
            return blobstore_key
        time.sleep(1)


def get_blobstore_uploaded_file(blobstore_key):
    """ Convenience method for returning a BlobstoreUploadedFile object for a given blobstore_key
    """
    return BlobstoreUploadedFile(BlobInfo(blobstore_key), charset="utf-8")


def append_string_to_blobstore_file(blobstore_file_name, string):
    """ Use the AppEngine Files API to write to the blobstore
    """
    if isinstance(string, unicode):
        string = string.encode('utf8')

    with files.open(blobstore_file_name, 'a') as blobstore_file:
        blobstore_write_limit = 512 * 1024
        for i in range(0, len(string), blobstore_write_limit):
            blobstore_file.write(string[i:i + blobstore_write_limit])
            time.sleep(0.25)