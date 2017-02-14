from mezzanine.pages.admin import PageAdmin
from django.contrib.gis import admin
from .models import RasterResource
from hs_core.admin import ResourceModelAdmin

# admin.site.register(MyResource, PageAdmin)


admin.site.register(RasterResource, ResourceModelAdmin)
