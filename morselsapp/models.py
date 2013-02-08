from google.appengine.ext import blobstore
from google.appengine.api import images
from google.appengine.api.images import Error as UnknownImageError, LargeImageError
from google.appengine.runtime import DeadlineExceededError
from google.appengine.runtime import apiproxy_errors
from django.db import models

import os

#See https://developers.google.com/appengine/docs/python/images/functions
APPENGINE_IMAGES_SUPPORTED_FILE_TYPES = ['.jpeg', '.jpg', '.png', '.gif', '.bmp', '.tiff', '.ico']

class MyMorsel(models.Model):
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    file_object = models.FileField(
        upload_to='mymorsels/%Y/%m/%d/',
        null=True,
        blank=True,
        verbose_name="File")
    file_name = models.CharField(max_length=200, blank=True, null=True, editable=False)

    #Store the result of get_serving_url
    blobstore_url = models.CharField(max_length=200, null=True, blank=True, editable=False)
    image_error = models.CharField(max_length=100, blank=True, null=True)

    @property
    def filename(self):
        """ Convenience method for returning the filename. """
        if self.file_object:
            return self.file_object.name.rsplit('/', 1)[-1]
        return None

    @property
    def file_extension(self):
        """ Convenience method for returning the file_extension. """
        return os.path.splitext(self.filename)[-1]

    def thumbnail(self, pixel_size=100):
        """ Convenience method for returning a resized image. Requires that we have a stored
        result of get_serving_url (see the store_serving_url method)."""
        if self.blobstore_url:
            return "%s=s%s" % (self.blobstore_url, pixel_size)
        return None

    def delete(self, *args, **kwargs):
        """ Additional delete actions:

        * Delete the associated blob when the mymorsel is deleted.

        """
        if self.file_object:
            if self.file_object.file.blobstore_info:
                blob_key = self.file_object.file.blobstore_info.key()._BlobKey__blob_key
                blobstore.delete(blob_key)
        return super(MyMorsel, self).delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        """ Additional save actions:

        * Check if the file is an image supported by the AppEngine images API and, if so,
        attempt to call and save get_serving_url via store_serving_url.

        """
        if self.file_extension.lower() in APPENGINE_IMAGES_SUPPORTED_FILE_TYPES and self.file_object:
            self.store_serving_url()
        return super(MyMorsel, self).save()

    def store_serving_url(self):
        """ Store the result of get_serving_url because it's inefficient to look it up every
        time the image is rendered on a page."""
        blobstore_info = self.file_object.file.blobstore_info
        # in principle, blobstore_info should never be none but this sometimes happens on
        # production
        if blobstore_info:
            blob_key = blobstore_info.key()._BlobKey__blob_key
            try:
                self.blobstore_url = images.get_serving_url(blob_key)
            except LargeImageError:
                # image is too large to be handled by get_serving_url. We log it here so we can
                # process these later if we want to
                self.image_error = 'LargeImageError'
            except (UnknownImageError, DeadlineExceededError,
                    apiproxy_errors.DeadlineExceededError, NotImplementedError):
                # something else went wrong
                self.image_error = 'UnknownImageError'
