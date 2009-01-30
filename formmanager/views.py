from django.http import HttpResponseRedirect,HttpResponse
from django.core import mail
from models import *
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404,render_to_response
from django.template import RequestContext
from django.conf import settings

def form_processor(request,slug):
    mform=get_object_or_404(ManagedForm,slug=slug)
    if not mform.is_live(): raise Http404("Form is not accepting submissions")
    if request.method == 'POST':
        form=mform.get_form(request.POST,request.FILES)
        if form.is_valid():
            mfe=ManagedFormEntry(form=mform,
                                 referer=request.META.get('HTTP_REFERER',""),
                                 submit_ip=request.META.get("REMOTE_ADDR",""))
            mfe.save()
            for k in form.cleaned_data:
                field=mform.get_field(k)
                if field:
                    mfef=ManagedFormEntryField(entry=mfe,field=field)
                    mfef.set_value(form.cleaned_data[k])
                    mfef.save()
            if mform.cc_email:
                content = "\n".join("%s: %s"%(fe[0],fe[1]) for fe in mfe.get_entry_fields().items())
                mail.send_mail("New Submission - %s"%mform.slug, content, settings.ADMIN_EMAIL, [mform.cc_email],True)
            return HttpResponseRedirect(mform.success_page)
    else:
        form=mform.get_form()
    template="formmanager/default.html"
    if mform.template: template=mform.template
    return render_to_response(template,{"form":form},context_instance=RequestContext(request))

def export(request, slug):
    mform=get_object_or_404(ManagedForm,slug=slug)
    queryset=mform.managedformentry_set.all()
    filters = dict()
    for key, value in request.GET.items():
        if key not in ('ot', 'o'):
            filters[str(key)] = str(value)
    if len(filters):
        queryset = queryset.filter(**filters)
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=%s.csv' % mform.slug
    export_template="formmanager/csv_template.csv"
    if mform.export_template: export_template=mform.export_template
    response.content = render_to_string(export_template, {'object_list':queryset})
    return response

