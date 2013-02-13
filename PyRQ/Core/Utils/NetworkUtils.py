'''
Created on 10 Oct 2012

@author: francis
'''

import subprocess, re

def get_ipv4_address():
    """
    @see: http://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib
    Returns IP address(es) of current machine.
    :return:
    """
    p = subprocess.Popen(["ifconfig"], stdout=subprocess.PIPE)
    ifc_resp = p.communicate()
    patt = re.compile(r'inet\s*\w*\S*:\s*(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})')
    resp = patt.findall(ifc_resp[0])
    return resp
