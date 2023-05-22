from django import forms
from django.contrib import admin

from django.db.models import ForeignKey, OneToOneField, CharField, TextField

from countless_admin import CountlessAdminMixin

# Register your models here.
from .models import __all__ as all_models
from .models import *


# check
#@admin.register()

temp = []

#class SiteAdmin(admin.ModelAdmin):
#    list_select_related = ()

#temp = ['SiteAdmin', ]

#@admin.register(globals()['Message'])

class AdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['discuss_message'].disabled = True
        #self.fields['discuss_message'].widget.can_change_related = False

    class Meta:
        model = globals()['Message']
        fields = '__all__'

class MyModelAdmin(CountlessAdminMixin, admin.ModelAdmin):
    #list_display = [ 'get_id', ]
    #list_select_related = ['id', ]
    #readonly_fields = ['discuss_message']a
    #list_editable = ['id', ]
    raw_id_fields = ['discuss_message', ]

    #@admin.display(description='id')
    #def get_id(self, object):
    #    return 1
    #    return object.id

    #def get_queryset(self, request):
    #    qs = super(MyModelAdmin, self).get_queryset(request)
    #    return qs.prefetch_related('discuss_message')
    #form = AdminForm

    raw_id_fields = ()
    search_fields = ()

    def __init__(self, model, admin_site, *args, **kwargs):
        self.raw_id_fields = self.setup_raw_id_fields(model)
        self.search_fields = self.setup_search_fields(model)
        super().__init__(model, admin_site, *args, **kwargs)

    def setup_raw_id_fields(self, model):
        return tuple(
            f.name
            for f in model._meta.get_fields()
            if isinstance(f, ForeignKey) or isinstance(f, OneToOneField)
        )

    def setup_search_fields(self, model):
        return tuple(
            f.name
            for f in model._meta.get_fields()
            if isinstance(f, CharField) or isinstance(f, TextField)
        )


for model in [*all_models, *temp]:
    #print(model)
    #print(globals()[model])
    admin.site.register(globals()[model], MyModelAdmin)
