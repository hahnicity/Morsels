from __future__ import with_statement

from django.http import HttpResponse
from django.utils import simplejson
from django.core.urlresolvers import reverse

from django.shortcuts import get_object_or_404, redirect
from django.views.generic import TemplateView
from django.views.generic.edit import DeleteView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from morselsapp.models import MyMorsel
from morselsapp import utils

import logging

class UploadMedia(TemplateView):
    """ Handles media uploads; currently supports images and audio """
    template_name = 'upload.html'

    @method_decorator(csrf_exempt)
    def post(self, request, **kwargs):
        blob_file = request.FILES.get(u'files', None)
        blob_size = blob_file._get_size()
        blob_name = blob_file.name

        #If files are chunked, the original file metadata is stored in extra META headers and the
        #POSTed file is called 'blob'. For files that aren't chunked, use the POSTed file directly.
        expected_file_size = request.META.get('HTTP_X_FILE_SIZE', None) or blob_size
        expected_file_name = request.META.get('HTTP_X_FILE_NAME', None) or blob_name

        logging.debug("Blob got: %s (expected: %s), size got: %s (expected: %s)" % (
            blob_name, expected_file_name, blob_size, expected_file_size))

        chunked_file, blobstore_filename, file_finalized = utils.handle_blob_upload(
            blob_file,
            expected_file_name,
            expected_file_size
        )

        if not file_finalized:
            # The file isn't finalized yet so keep adding to it. Dump the uploaded bytes
            # to the client and let it handle resume / retries.
            data = {
                'size': utils._get_uploaded_bytes(expected_file_name)
            }
            return HttpResponse(simplejson.dumps(data), mimetype='application/json')

        try:
            mymorsel = MyMorsel(file_name=expected_file_name)
            mymorsel.file_object.save(expected_file_name, chunked_file)
            mymorsel.save()
            return redirect(reverse('uploaded_mymorsel', kwargs={'pk': mymorsel.id}))

        except Exception, e:
            logging.exception('UploadHandler failed: %s %s' % (Exception, str(e)))
            #Log the error then dump an error message to the client
            response = [{
                "name": expected_file_name,
                "error": "ERROR SAVING FILE"
            }]
            return HttpResponse(simplejson.dumps(response), mimetype='application/json')

    def get(self, request, **kwargs):
        file_name = self.request.GET.get('file')
        if request.is_ajax():
            #an uploadedBytes variable is required client-side for resuming uploads
            data = {
                'size': utils._get_uploaded_bytes(file_name)
            }
            return HttpResponse(simplejson.dumps(data), mimetype='application/json')
        return super(UploadMedia, self).get(request, **kwargs)

upload_media = UploadMedia.as_view()

class MyMorselDeleteView(DeleteView):
    """ Handles MyMorsel deletion for the upload widget """
    model = MyMorsel

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        self.pk = kwargs['pk']
        return super(MyMorselDeleteView, self).dispatch(request, *args, **kwargs)

    def get_object(self, *args, **kwargs):
        return get_object_or_404(MyMorsel, id=self.pk)

    def get_success_url(self):
        return reverse('mymorsel_delete_callback', kwargs={'pk': self.kwargs.get('pk')})

delete_mymorsel = MyMorselDeleteView.as_view()

class MyMorselDeleteCallback(TemplateView):
    """ Handles MyMorsel deletion callback for the bulk media upload widget"""

    def render_to_response(self, context, **response_kwargs):
        pk = self.kwargs.get('pk')
        data = simplejson.dumps({'id': pk})
        return HttpResponse(data, mimetype='application/json')

mymorsel_delete_callback = MyMorselDeleteCallback.as_view()

class UploadedMyMorselView(TemplateView):
    """ Returns uploaded MyMorsel metadata as JSON"""

    def render_to_response(self, context, **kwargs):
        id = self.kwargs.get('pk')
        mymorsel = get_object_or_404(MyMorsel, pk=id)
        mymorsel_data = {
            "name": mymorsel.file_name,
            "size": mymorsel.file_object._get_size(),
            "delete_url": reverse('delete_mymorsel', kwargs={'pk': id}),
            "delete_type": "POST",
            }

        #Only return a thumbnail_url if the mymorsel has one
        thumb = mymorsel.thumbnail(pixel_size=100)
        if thumb is not None:
            mymorsel_data.update({"thumbnail_url": thumb})

        data = simplejson.dumps([mymorsel_data])
        HttpResponse.status_code = 200
        return HttpResponse(data, mimetype='application/json')

uploaded_mymorsel = UploadedMyMorselView.as_view()




