import os
from django.http import HttpResponseRedirect

from django_irods.icommands import SessionException
from django_irods.storage import IrodsStorage

from django.conf import settings
from django.core.files.uploadedfile import UploadedFile

from hs_core.hydroshare.utils import get_resource_by_shortkey, add_file_to_resource

def execute_wso(request, shortkey, *args, **kwargs):
    port = int(settings.IRODS_DFC_WORKFLOW_PORT)
    user = str(settings.IRODS_DFC_WORKFLOW_USERNAME)
    password = str(settings.IRODS_DFC_WORKFLOW_AUTH)
    zone = str(settings.IRODS_DFC_WORKFLOW_ZONE)
    host = str(settings.IRODS_DFC_WORKFLOW_HOST)
    def_res = str(settings.IRODS_DFC_WORKFLOW_DEFAULT_RESOURCE)
    homedir = "/"+zone+"/home/"+user

    res = get_resource_by_shortkey(shortkey)
    cm = res.get_content_model()
    mss_file_name = None
    mpf_file_names = []
    # retrieve mss workflow file and mpf parameter file from this resource
    for f in cm.files.all():
        ext = os.path.splitext(f.resource_file.name)[1].strip().lower()
        if ext == '.mss' and not mss_file_name: # workflow file
            mss_file_name = f.resource_file.name
        elif ext == '.mpf':
            mpf_file_names.append(f.resource_file.name)

    if not mss_file_name or not mpf_file_names:
        request.session['validation_error'] = "Workflow mss file and/or parameter mpf files don't exist in the resource"
        return HttpResponseRedirect(request.META['HTTP_REFERER'])

    try:
        irods_storage = IrodsStorage()
        # download resource mss file and mpf files to prepare for subsequent ingesting
        mss_tmp_file = irods_storage.download(mss_file_name)
        mpf_tmp_files = []
        for fname in mpf_file_names:
            mpf_tmp_files.append(irods_storage.download(fname))

        # ingest files into workflow iRODS server to trigger workflow execution
        irods_storage.set_user_session(username=user, password=password, host=host, port=port, def_res=def_res, zone=zone)
        to_file_name = os.path.basename(mss_file_name).strip()
        to_coll_name = os.path.splitext(to_file_name)[0]
        to_file_path = '{cwd}/{path}/{fname}'.format(cwd=homedir, path=to_coll_name, fname=to_file_name)
        irods_storage.saveFile(mss_tmp_file.name, to_file_path, True, 'msso file')

        # create a wso sub-collection that will be used to execute the WSO
        wso_coll_name = "{cwd}/{coll_name}/wso".format(cwd=homedir, coll_name=to_coll_name)
        irods_storage.session.run("imkdir", None, '-p', wso_coll_name)
        irods_storage.session.run("imcoll", None, '-m', 'msso', to_file_path, wso_coll_name)
        for f in mpf_tmp_files:
            wso_mpf_path = "{coll_name}/{mpf_name}".format(coll_name=wso_coll_name, mpf_name=f.name)
            irods_storage.saveFile(f.name, wso_mpf_path, False)
            # trigger WSO execution via a iget of the generated run file
            run_file_name = "{coll_name}/{base_name}.run".format(coll_name=wso_coll_name,
                                                                 base_name=os.path.splitext(f.name)[0])
            tmpFile = irods_storage.download(run_file_name)
            fname = os.path.basename(run_file_name.rstrip(os.sep))
            add_file_to_resource(res, UploadedFile(file=tmpFile, name=fname))
    except SessionException as ex:
        request.session['validation_error'] = ex.stderr
        return HttpResponseRedirect(request.META['HTTP_REFERER'])

    return HttpResponseRedirect(request.META['HTTP_REFERER'])