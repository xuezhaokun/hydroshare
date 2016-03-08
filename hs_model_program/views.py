__author__ = 'tonycastronova'

import os
from django.http import HttpResponse
from hs_model_program.models import ModelProgramResource
import json
import datetime
import urllib
from hs_core.views import add_file_to_resource
import requests
import tempfile
from django.core.files.uploadedfile import UploadedFile

class TemporaryUploadedFile(UploadedFile):
    def __init__(self, file=None, name=None, content_type=None, size=None, charset=None, content_type_extra=None):
        super(UploadedFile, self).__init__(file, name)
        self.orig_name = name
        self.size = size
        self.content_type = content_type
        self.charset = charset
        self.content_type_extra = content_type_extra

    def temporary_file_path(self):
        return self.orig_name

def get_model_program_object(resourceid, host, secure_request=False):

    obj = ModelProgramResource.objects.filter(short_id=resourceid).first()
    metadata = {}
    mpmeta = obj.metadata.program

    # get the http protocol
    protocol = 'https' if secure_request else 'http'

    if mpmeta.modelReleaseDate:
        dt = datetime.datetime.strftime(mpmeta.modelReleaseDate,'%m/%d/%Y')
    else:
        dt = ''

    # build an output dictionary which will be returned as JSON
    if obj is not None:
        metadata = dict(
            description=obj.description,
            program_website=mpmeta.modelWebsite,
            date_released=dt,
            software_version=mpmeta.modelVersion,
            software_language=mpmeta.modelProgramLanguage,
            operating_sys=mpmeta.modelOperatingSystem,
            url = protocol+"://"+host+"/resource/"+resourceid+"/",
            modelEngine = mpmeta.modelEngine.split(';'),
            modelSoftware=mpmeta.modelSoftware.split(';'),
            modelDocumentation=mpmeta.modelDocumentation.split(';'),
            modelReleaseNotes=mpmeta.modelReleaseNotes.split(';'),
        )

    return metadata

def get_model_metadata(request):

    # get the request data
    r = request.GET

    # get the resource id for looking up the resource object
    resource_id = r['resource_id']

    # get the model program resource
    obj = ModelProgramResource.objects.filter(short_id=resource_id).first()
    metadata = {}

    if obj is not None:
        mpmeta = obj.metadata.program

        # get the http protocol
        protocol = 'https' if request.is_secure() else 'http'

        if mpmeta.modelReleaseDate:
            dt = datetime.datetime.strftime(mpmeta.modelReleaseDate,'%m/%d/%Y')
        else:
            dt = ''

        # build an output dictionary which will be returned as JSON
        if obj is not None:
            metadata = dict(
                description=obj.description,
                program_website=mpmeta.modelWebsite,
                date_released=dt,
                software_version=mpmeta.modelVersion,
                software_language=mpmeta.modelProgramLanguage,
                operating_sys=mpmeta.modelOperatingSystem,
                url = protocol+"://"+request.get_host()+"/resource/"+resource_id+"/",
                modelEngine = mpmeta.modelEngine.split(';'),
                modelSoftware=mpmeta.modelSoftware.split(';'),
                modelDocumentation=mpmeta.modelDocumentation.split(';'),
                modelReleaseNotes=mpmeta.modelReleaseNotes.split(';'),
            )

    json_data = json.dumps(metadata)
    return HttpResponse(json_data, content_type="application/json")

def import_from_git(request):

    # get the request data
    r = request.GET

    # get the resource id for looking up the resource object
    resource_id = r['resource_id']

    # get the model program resource
    obj = ModelProgramResource.objects.filter(short_id=resource_id).first()
    if obj is None:
        return False
    mpmeta = obj.metadata.program

    # extract the git url and sha from the form fields
    url = r['git_url']
    sha = r['git_sha']

    # remove the .git extension from the url
    if url[-4:] == '.git':
        url = url[:-4]

    if sha.strip() == '':
        sha = 'master'

    url_format = '{repo}/archive/{sha}.zip'

    full_url = url_format.format(repo=url, sha=sha)
    save_location =  '/tmp/'+sha+'.zip'
    f = requests.get(full_url, stream=True)

    # Create a temporary file
    lf = tempfile.NamedTemporaryFile()
    local_filename = '.'.join(full_url.split('/')[4:])

    # Read the streamed image in sections
    for block in f.iter_content(1024 * 8):
        # If no more file then stop
        if not block:
            break
        lf.write(block)

    # creat a temporary file
    tfile = TemporaryUploadedFile(lf.file, name=local_filename,
                                    content_type='application/zip',
                                    size=os.stat(lf.name).st_size)

    # add file to resource
    try:
        request._files['files'] = tfile
        add_file_to_resource(request=request, shortkey=resource_id)
    except Exception, e:
        print e

    # # set the model engine and model software values
    # m = mpmeta.modelEngine
    # mpmeta.modelEngine = local_filename
    # mpmeta.modelSoftware = local_filename

    # get the model program attributes
    mp_dict = get_model_program_object(resource_id, request.get_host(), request.is_secure())

    # return the model program object values as a dictionary
    json_data = json.dumps(mp_dict)
    return HttpResponse(json_data, content_type="application/json")
