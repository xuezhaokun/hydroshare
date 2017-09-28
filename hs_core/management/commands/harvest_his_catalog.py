# -*- coding: utf-8 -*-

"""
This harvests all of HIS into HydroShare time series reference resources. 

"""

from django.core.management.base import BaseCommand
from hs_core.models import BaseResource
from hs_core.hydroshare.utils import get_resource_by_shortkey

import logging

class Command(BaseCommand):
    help = "Harvest HIS metadata into time series reference resources."

    def add_arguments(self, parser):
        parser.add_argument(
            '--log',
            action='store_true',  # True for presence, False for absence
            dest='log',  # value is options['log']
            help='log errors to system log'
        )
        # if --soap is true, --variable and --site are necessary 
        parser.add_argument(
            '--soap',
            action='store_true',  # It is bool: True for presence, False for absence
            dest='soap',          # value is options['log']
            help='invoke soap query'
        )
        parser.add_argument(
            '--variable',
            action='store',   # This is a string
            dest='variable',  # value is options['variable']
            help='soap variable'
        ) 
        parser.add_argument(
            '--site',
            action='store',   # This is a string
            dest='site',      # value is options['site']
            help='soap site'
        ) 

    def handle(self, *args, **options):
        pass
