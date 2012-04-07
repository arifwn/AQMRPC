'''
AQM RPC Server

foreground: twistd -n aqmrpc
background (demonized): twistd aqmrpc

Created on Jan 22, 2012

@author: arif
'''
import servicemaker

serviceMaker = servicemaker.AQMServiceMaker()
