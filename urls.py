from django.conf.urls.defaults import *
from django.views.generic import RedirectView
from django.core.urlresolvers import reverse
from django.utils.functional import lazy
reverse_lazy = lazy(reverse, str)

handler500 = 'djangotoolbox.errorviews.server_error'

urlpatterns = patterns('',
    (r'^$', RedirectView.as_view(url=reverse_lazy('upload_media'))), #Redirect homepage to upload_media
    (r'^_ah/warmup$', 'djangoappengine.views.warmup'),
    (r'^morsels/', include('morsels.urls')),
)
