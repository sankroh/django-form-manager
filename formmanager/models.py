from django.db import models
from django import forms 
from django.core import urlresolvers
from django.contrib import admin,sites
import datetime

FORMFIELD_MAP={
    "char":("Single Line Input (max 200 characters)",forms.CharField,{}),
    "text":("Multiline Input",forms.CharField,{"widget":forms.widgets.TextInput}),
    "int":("Integer Input",forms.IntegerField,{}),
    "float":("Decimal Input",forms.DecimalField,{}),
    "file":("File Input",forms.FileField,{}),
    "choice":("Choice Field",forms.ChoiceField,{}),
    "datetime":("Date/Time",forms.DateTimeField,{}),
    "password":("Password Field",forms.CharField,{"widget":forms.widgets.PasswordInput}),
}

FORMFIELD_CHOICES=[(k,FORMFIELD_MAP[k][0]) for k in FORMFIELD_MAP]

class ManagedForm(models.Model):
    slug=models.SlugField()
    active=models.BooleanField(default=False)
    drop_date=models.DateTimeField(blank=True,null=True)
    end_date=models.DateTimeField(blank=True,null=True)
    success_page=models.CharField(max_length=200,help_text=u"URL to be redirected to on success")
    template=models.CharField(max_length=200,blank=True,help_text=u"Default: formmanager/default.html")
    export_template=models.CharField(max_length=200,blank=True,help_text=u"Default: formmanager/csv_template/csv")
    cc_email=models.EmailField(blank=True,help_text=u"Add an email address to have a copy of every submission mailed to. <b>Warning</b>, this can quickly be loaded with spam and should not be someone's primary email address")

    def is_live(self):
        if not self.active: return False
        dt=datetime.datetime.now()
        if self.drop_date and dt < self.drop_date: return False
        if self.end_date and dt > self.end_date: return False
        return True

    def get_form(self,post=None,files=None):
        f=forms.Form(post,files)
        for field in self.fields():
            fftyp=FORMFIELD_MAP[field.type]
            widgdict=field.customize_widget_dict(fftyp[2]) # allow field to add stuff to widget
            label = field.title
            if field.required: label="*%s"%field.title
            f.fields[field.key]=fftyp[1](label=label,required=field.required,**widgdict)
        f.full_clean()
        return f

    def get_field(self,key):
        fs=self.managedformfield_set.filter(key=key)
        if len(fs): return fs[0]
        return None

    def fields(self):
        return self.managedformfield_set.order_by("order")    

    def required_fields(self):
        return self.managedformfield_set.filter(required=True)

    def duration(self):
        if self.drop_date and self.end_date:
            return (self.end_date - self.drop_date).days
        if self.drop_date: return "%s and later"%self.drop_date
        return "Ongoing"

    def action(self):
        return self.get_absolute_url()

    def get_absolute_url(self):
        return urlresolvers.reverse('managed_form_action', args=[self.slug,])

    def get_admin_csv(self):
        n=datetime.datetime.now()
        return """<a href="%(url)sexport/?form__id__exact=%(id)i">today</a><br/>
                  <a href="%(url)sexport/?form__id__exact=%(id)i&submit_date__day=%(day)i&submit_date__month=%(month)i&submit_date__year=%(year)i">this week</a><br/>
                  <a href="%(url)sexport/?form__id__exact=%(id)i&submit_date__gte=%(year)i-%(month)i-%(day)i">this month</a><br/>
                  <a href="%(url)sexport/?form__id__exact=%(id)i">all</a>
                """%{"id":self.id,"year":n.year,"month":n.month,"day":n.day,"url":self.get_absolute_url()}
    get_admin_csv.allow_tags=True

    def __unicode__(self):
        return self.slug

class ManagedFormField(models.Model):
    form=models.ForeignKey(ManagedForm)
    title=models.CharField(max_length=100)
    key=models.SlugField()
    type=models.CharField(max_length=16,choices=FORMFIELD_CHOICES)
    required=models.BooleanField(default=True)
    order=models.FloatField(default=1.0,help_text=u"Order form fields, lowest first.") 
    extra=models.TextField(help_text=u"Extra Information. For Choice field, this is one choice per line",blank=True)

    def customize_widget_dict(self,d):
        if self.type=="choice":
            import re
            d["choices"]=[(s.strip(),s.strip()) for s in self.extra.split("\n") if len(s.strip())]
        return d

    class Meta:
        ordering=("required",)

class ManagedFormEntry(models.Model):
    form=models.ForeignKey(ManagedForm)
    submit_date=models.DateTimeField(auto_now=True)
    submit_ip=models.CharField(max_length=64)  
    referer=models.CharField(max_length=200,blank=True)

    def get_entry_fields(self):
        fields={}
        for f in self.managedformentryfield_set.select_related().order_by("field__order","field__key"):
            fields[f.field.key]=f.value()
        return fields

    def get_escaped_entry_values(self):
        vals=[]
        for f in self.managedformentryfield_set.select_related().order_by("field__order","field__key"):
            val = f.value()
            if not val: val=""  
            vals.append(val.replace("\n",' ').replace('"','\"'))
        return vals

    def required_fields(self):
        fields=self.get_entry_fields()
        required_fields={}
        for f in self.form.required_fields():
            if not fields.has_key(f.key):
                required_fields[f.key] = None 
            else:
                required_fields[f.key]=fields[f.key]
        return required_fields 

    def required_fields_text(self):
        return "<br/>".join(["%s: %s"%(k[0],k[1]) for k in self.required_fields().items()])
    required_fields_text.allow_tags=True
 
class ManagedFormEntryField(models.Model):
    """ Should I do this with multiple fields or just one? i don't know, depends on sorting i think"""
    entry=models.ForeignKey(ManagedFormEntry)
    field=models.ForeignKey(ManagedFormField)
    char_value=models.CharField(null=True,max_length=255,blank=True)
    int_value=models.IntegerField(null=True,blank=True)
    float_value=models.FloatField(null=True,blank=True)
    big_value=models.TextField(null=True,blank=True)
    date_value=models.DateTimeField(null=True,blank=True)
    file=models.FileField(null=True,upload_to="uploaded_form_data/%Y/%m/%d/",blank=True)

    def value(self):
        if self.field.type=="char": return self.char_value
        if self.field.type=="text": return self.big_value
        if self.field.type=="int": return self.int_value
        if self.field.type=="float": return self.float_value
        if self.field.type=="file": return "http://%s%s"%(sites.Site.objects.get_current().domain,self.file.url)
        if self.field.type=="choice": return self.char_value
        if self.field.type=="datetime": return self.date_value
        else: return self.char_value

    def set_value(self,v):
        if self.field.type=="char": self.char_value=v
        if self.field.type=="text": self.big_value=v
        if self.field.type=="int": self.int_value=v
        if self.field.type=="float": self.float_value=v
        if self.field.type=="file": self.file=v
        if self.field.type=="choice": self.char_value=v
        if self.field.type=="datetime": self.date_value=v
        else: self.char_value=v

class ManagedFormFieldInline(admin.StackedInline):
    model=ManagedFormField

class ManagedFormAdmin(admin.ModelAdmin):
    list_display = ('slug','action','active','duration','get_admin_csv')
    list_filter = ('active',)
    inlines=[ManagedFormFieldInline,]
admin.site.register(ManagedForm,ManagedFormAdmin)

class ManagedFormFieldAdmin(admin.ModelAdmin):
    list_display = ('key','type','form')
    list_filter = ('form',)
    inlines=[ManagedFormFieldInline,]
admin.site.register(ManagedFormField,ManagedFormFieldAdmin)

class ManagedFormEntryAdmin(admin.ModelAdmin):
    list_display = ('submit_date','submit_ip','referer','required_fields_text')
    list_filter = ('form','submit_date')
    csv_template = "formmanager/csv_template.html" 
admin.site.register(ManagedFormEntry,ManagedFormEntryAdmin)

