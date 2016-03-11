import os
from django.http import HttpResponse, HttpResponseRedirect

from django_irods.icommands import SessionException
from django_irods.storage import IrodsStorage

from django.conf import settings

from hs_core.hydroshare.utils import get_resource_by_shortkey

def execute_wso(request, shortkey, *args, **kwargs):
    port = int(settings.IRODS_DFC_WORKFLOW_PORT)
    user = str(settings.IRODS_DFC_WORKFLOW_USERNAME)
    password = str(settings.IRODS_DFC_WORKFLOW_AUTH)
    zone = str(settings.IRODS_DFC_WORKFLOW_ZONE)
    host = str(settings.IRODS_DFC_WORKFLOW_HOST)

    res = get_resource_by_shortkey(shortkey)
    cm = res.get_content_model()
    mss_file = None
    mpf_files = []
    # retrieve mss workflow file and mpf parameter file from this resource
    for f in cm.files.all():
        ext = os.path.splitext(f.resource_file.name)[1].strip().lower()
        if ext == '.mss' and not mss_file: # workflow file
            mss_file = f.resource_file
        elif ext == '.mpf':
            mpf_files.append(f.resource_file)

    if not mss_file or not mpf_files:
        request.session['validation_error'] = "Workflow mss file and/or parameter mpf files don't exist in the resource"
        return HttpResponseRedirect(request.META['HTTP_REFERER'])

    try:
        irods_storage = IrodsStorage()
        irods_storage.set_user_session(username=user, password=password, host=host, port=port, zone=zone)
        to_file_name = os.path.basename(mss_file.name).strip()
        to_file_path = '{path}/{fname}'.format(path=os.path.splitext(to_file_name)[0], fname=to_file_name)
        irods_storage.saveFile(mss_file, to_file_name, True) # need to set parameters

    #except SessionException as ex:
    #    request.session['validation_error'] = ex.stderr
    #    return HttpResponseRedirect(request.META['HTTP_REFERER'])

    return HttpResponseRedirect(request.META['HTTP_REFERER'])