##Morsels
An implementation of [jQuery File Upload](https://github.com/blueimp/jQuery-File-Upload) with a Django / Google AppEngine backend.

###Demo
[Morsels demo app](http://morselsdemo.appspot.com)

### Summary
Morsels uses the [AppEngine Files API](https://developers.google.com/appengine/docs/python/blobstore/overview#Writing_Files_to_the_Blobstore) to write blobs to the blobstore in chunks, automatically resuming uploads from where they left off. Each chunk is sent in a separate POST request. The upshot is you can upload very large files without having to worry about request deadlines and without needing to use the create_upload_url() method.

Although this module uses Django models, it could quite easily be adapted to bypass Django and use the AppEngine Model class.

### Features
* Automatically resumes cancelled or aborted uploads
* Uses get_serving_url (where possible) to give you a stable, dedicated, high-performance URL for serving web-suitable image thumbnails.

###Setup instructions
Morsels is already bundled into a django non-rel demo app. Just check out the source and run `python manage.py runserver`

### Requirements
* PIL (for Images API / get_serving_url)
* Django 1.3
* Underscore.js (templating)
* Also see https://github.com/blueimp/jQuery-File-Upload/#requirements

### License
Released under the [MIT license](http://www.opensource.org/licenses/MIT)

### Credits
Steven Holmes - for the Django / AppEngine backend
Sebastian Tschan (blueimp) - for the excellent jQuery File Upload library.