from django.core.urlresolvers import NoReverseMatch
from mezzanine.pages.admin import PageAdmin
from mezzanine.pages.models import RichTextPage, Page
from mezzanine.utils.urls import admin_url, clean_slashes
from django.contrib.gis import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from .models import *

# class InlineResourceFiles(GenericTabularInline):
#     model = ResourceFile
#
# class GenericResourceAdmin(PageAdmin):
#     inlines = PageAdmin.inlines + [InlineResourceFiles]
#
# admin.site.register(GenericResource, GenericResourceAdmin)


class ResourceModelAdmin(admin.ModelAdmin):
    list_filter = ('creator',)
    list_display = ('title', 'creator', 'created')
    list_max_show_all = 2
    list_per_page = 5

admin.site.register(GenericResource, ResourceModelAdmin)


class RichTextPageAdmin(admin.ModelAdmin):
    # Using this template gives the page ordering interface but lists all resource types
    # similar to the original Pages menu. If we don't use this template then we get only the list
    # of records that are of type RichTextPage (which is desired) but we don't get the interface
    # for ordering the pages
    change_list_template = "admin/pages/page/change_list.html"

    def get_queryset(self, request):
        return RichTextPage.objects.all()

class MyPageAdmin(PageAdmin):
    def in_menu(self):
        return self.model is not Page


admin.site.unregister(Page)
admin.site.unregister(RichTextPage)
admin.site.register(Page, MyPageAdmin)
admin.site.register(RichTextPage, RichTextPageAdmin)