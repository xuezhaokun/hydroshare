__author__ = 'tonycastronova'

import os
from django.http import HttpResponse
from hs_model_program.models import ModelProgramResource
import json
import datetime
import urllib

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

    url = r['git_url']
    sha = r['git_sha']

    # remove the .git extension from the url
    if url[:-4] == '.git':
        url = url[:-4]

    if sha.strip() == '':
        sha = 'master'

    url_format = '{repo}/archive/{sha}.zip'


    full_url = url_format.format(repo=url, sha=sha)

    res = urllib.urlretrieve(full_url, '/tmp/'+sha+'.zip')

    print 'done'
