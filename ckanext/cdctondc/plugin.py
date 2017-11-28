import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

# import self-defined helpers.py
from helpers import *

class CdctondcPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)

    # necessary to import self-defined functions/methods
    plugins.implements(plugins.ITemplateHelpers)

    # IConfigurer
    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'cdctondc')

    # set the corresponding function name 
    def get_helpers(self):
        # define in the helpers.py
        return { 'syncNDCState' : syncNDCState, \
                 'syncNDCInitDataset' : syncNDCInitDataset, \
                 'testNDC' : testNDC, \
                 'SYNCNDC' : SYNCNDC, \
                 'actSYNC2NDC' : actSYNC2NDC \
               }
