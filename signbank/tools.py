import signbank.settings
import os
import shutil
from zipfile import ZipFile
from datetime import datetime, date
import json
import re

from django.utils.translation import override

from signbank.dictionary.models import *
from signbank.dictionary.update import gloss_from_identifier
from django.utils.dateformat import format
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse

def get_gloss_data():

    glosses = Gloss.objects.all()
    gloss_data = {}
    for gloss in glosses:
        gloss_data[gloss.pk] = gloss.get_fields_dict()

    return gloss_data

def create_zip_with_json_files(data_per_file,output_path):

    """Creates a zip file filled with the output of the functions supplied.

    Data should either be a json string or a list, which will be transformed to json."""

    INDENTATION_CHARS = 4

    zip = ZipFile(output_path,'w')

    for filename, data in data_per_file.items():

        if isinstance(data,list) or isinstance(data,dict):
            output = json.dumps(data,indent=INDENTATION_CHARS)
            zip.writestr(filename+'.json',output)
