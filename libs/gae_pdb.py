""" A fix to make pdb work in Google App Engine """

# To use it, just add this into your code where you want to debug:
# import gae_pdb; gae_pdb.set_trace();

import sys
import pdb
def set_trace():
    pdb.Pdb(stdin=sys.__stdin__, stdout=sys.__stdout__).set_trace(sys._getframe(1))
