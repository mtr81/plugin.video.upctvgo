﻿try:  # Python 3
    from http.server import BaseHTTPRequestHandler
except ImportError:  # Python 2
    from BaseHTTPServer import BaseHTTPRequestHandler

try:  # Python 3
    from socketserver import TCPServer
except ImportError:  # Python 2
    from SocketServer import TCPServer

try:  # Python 3
    from urllib.parse import parse_qs, urlparse, urlencode,quote,unquote
except ImportError:  # Python 2
    from urlparse import urlparse, parse_qs
    from urllib import urlencode,quote,unquote
import base64
import re
import socket
from contextlib import closing

import time

import xbmcaddon, xbmcgui

addon = xbmcaddon.Addon(id='plugin.video.horizongo')
import requests
import sys
PY3 = sys.version_info >= (3,0,0)

def getToken(conloc,gg=False):
    oesptoken=addon.getSetting("oespToken")
    cook=addon.getSetting("kuks")
    username = addon.getSetting("username")
    sharedProfileId =addon.getSetting('sharedProfileId')
    hostapi = addon.getSetting("hostapi")
    uid=addon.getSetting("deviceId")
    old_token=addon.getSetting("token")

    headers = {
        'Host': hostapi,
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0',
        'Accept': 'application/json',
        'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
        'Content-Type': 'application/json',
        'X-Client-Id': '4.31.13||'+'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0',
        'X-OESP-Token': oesptoken,
        'X-OESP-Username': username,
        'X-OESP-Profile-Id': sharedProfileId,
        'Origin': 'https://www.upctv.pl',
        'Referer': 'https://www.upctv.pl/',
    }
    
    data = {"contentLocator":conloc,'drmScheme':'sdash:BR-AVC-DASH'}

    response = requests.post('https://prod.oesp.upctv.pl/oesp/v4/PL/pol/web/license/token', headers=headers, json=data,verify=False)

    responsecheck=response.text
  
    response=response.json()

    a=''

    if 'code":"concurrency"' in responsecheck:

        xbmcgui.Dialog().notification('[B]Błąd[/B]', 'Maksymalna liczba odtwarzaczy.\nZamknij jeden z odtwarzaczy.',xbmcgui.NOTIFICATION_INFO, 9000,False)    
        sys.exit(0)

    try:

        if 'reason":"prohibited"' in responsecheck or 'code":"adultCredentialVerification"' in responsecheck and not 'code":"ipBlocked' in responsecheck:# and not 'type":"requestBody' in responsecheck:
            if not 'type":"requestBody' in responsecheck:
                a = xbmcgui.Dialog().numeric(heading='Podaj PIN:',type=0,defaultt='')
                if a:
                
                    data = {"value":str(a)}
                    if response[0].get('code',None)=="adultCredentialVerification":
                        response = requests.post(BASURL+'/PL/pol/web/profile/adult/verifypin', headers=headers, json=data,verify=False)
                
                    else:    
                        response = requests.post(BASURL+'/PL/pol/web/profile/parental/verifypin', headers=headers, json=data,verify=False)
                    getSession()
                
                    data = {"contentLocator":conloc}
                
                    response = requests.post(BASURL+'/PL/pol/web/license/token', headers=headers, json=data,verify=False)
                    responsecheck = response.text
                    response=response.json()

    except:
        pass
    
    dod=''
    try:
        if not a:
            dod = response['token']
            data = {"contentLocator":conloc,"token":dod}
        else:
            data = {"contentLocator":conloc}
        oesptoken=addon.getSetting("oespToken")
        cook=addon.getSetting("kuks")
        username = addon.getSetting("username")

        headers = {
            'Host': hostapi,
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0',
            'Accept': 'application/json',
            'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
            'Content-Type': 'application/json',
            'X-Client-Id': '4.31.13||'+'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0',
            'X-OESP-Token': oesptoken,
            'X-OESP-Username': username,
            'X-OESP-Profile-Id': sharedProfileId,
            'Origin': 'https://www.upctv.pl',
            'Referer': 'https://www.upctv.pl/',
        }
        
        data = {"contentLocator":conloc}#,'drmScheme':'sdash:BR-AVC-DASH'}
        
        if 'REPLAY' in conloc:
            data.update({"deviceId": uid,'drmScheme':'sdash:BR-AVC-DASH','token':unquote(old_token),'playState':'playing','offset':1})    #,'playState':'playing','token':old_token,'offset':1
        if gg:
            data.update({"deviceId": uid,'drmScheme':'sdash:BR-AVC-DASH','token':unquote(old_token),'playState':'playing','offset':1})  #,'playState':'playing','token':old_token,'offset':1

        response = requests.post('https://prod.oesp.upctv.pl/oesp/v4/PL/pol/web/license/token', headers=headers, json=data,verify=False)
        responsecheck=response.text
        response=response.json()
        if 'code":"concurrency"' in responsecheck:

            xbmcgui.Dialog().notification('[B]Błąd[/B]', 'Maksymalna liczba odtwarzaczy.\n Zamknij jeden z odtwarzaczy i spróbuj ponownie.',xbmcgui.NOTIFICATION_INFO, 9000,False)    
            sys.exit(0)

        dod = response['token']
        dod = quote(dod)
    except Exception as ecv:
        xbmcgui.Dialog().notification('[B]Błąd[/B]', 'Nie można odtworzyć poza siecią UPC',xbmcgui.NOTIFICATION_INFO, 8000,False)

    return dod
    

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        """Handle http get requests, used for manifest"""

        path = self.path  # Path with parameters received from request e.g. "/manifest?id=234324"
        manifest_data=b''

        time_now=int(time.time())
        time_tkn=int(addon.getSetting('time_token'))
        
        if addon.getSetting('source')=='vod':
        
            if 'index.mpd/Manifest' in path:
                url_stream=''
                url_stream=path.split('manifest=')[1]
                hdr =  eval(addon.getSetting('heaNHL'))
                manifest_data = requests.get(url_stream, headers=hdr).content
                self.send_response(200)
                self.send_header('Content-type', 'application/xml+dash')
                self.end_headers()
                self.wfile.write(manifest_data)
            else:
                old_token=addon.getSetting('token')
                url=''
                orgurl=addon.getSetting('orgurl')
                if time_now>=time_tkn+60 and '.mpd' in path:
                    contentlocator=addon.getSetting('conloc')
                    oesptoken=addon.getSetting("oespToken")
                    username=addon.getSetting('username')
                    uri=addon.getSetting('uri')
                    ps = True if '/sdash' in orgurl else False
                    playToken = getToken(contentlocator,ps)
                    addon.setSetting('token',playToken)
                    addon.setSetting('time_token',str(int(time.time())))
                    url_stream=path.split('manifest=')[1]
                    url=url_stream.replace(addon.getSetting('first_token'),addon.getSetting('token'))
                 
                else:
                    url_stream=path.split('manifest=')[1]
                    url=url_stream.replace(addon.getSetting('first_token'),old_token)
                       
                self.send_response(302)
                self.send_header('Location', url)
                self.end_headers()
        
        if addon.getSetting('source')=='livetv':
            if 'manifest.mpd' in path:
                url_stream=path.split('manifest=')[1].replace(addon.getSetting('first_token'),addon.getSetting('token'))
                hdr =  eval(addon.getSetting('heaNHL'))
                manifest_data = requests.get(url_stream, headers=hdr).content
                self.send_response(200)
                self.send_header('Content-type', 'application/xml+dash')
                self.end_headers()
                self.wfile.write(manifest_data)
            else:
                old_token=addon.getSetting('token')
                url=''
                orgurl=addon.getSetting('orgurl')
                if time_now>=time_tkn+60 and 'manifest.mpd' not in path:
                    contentlocator=addon.getSetting('conloc')
                    oesptoken=addon.getSetting("oespToken")
                    username=addon.getSetting('username')
                    uri=addon.getSetting('uri')
                    ps = True if '/sdash' in orgurl else False
                    playToken = getToken(contentlocator,ps)
                    addon.setSetting('token',playToken)
                    addon.setSetting('time_token',str(int(time.time())))
                    url_stream=path.split('manifest=')[1]
                    url=url_stream.replace(addon.getSetting('first_token'),addon.getSetting('token'))
                else:
                    url_stream=path.split('manifest=')[1]
                    url=url_stream.replace(addon.getSetting('first_token'),old_token)
                
                self.send_response(302)
                self.send_header('Location', url)
                self.end_headers()
      

    def do_POST(self):
        """Handle http post requests, used for license"""
        path = self.path  # Path with parameters received from request e.g. "/license?id=234324"

        if '/licensetv' not in path:
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get('content-length', 0))
        isa_data = self.rfile.read(length)

        challenge = isa_data
        path2 = path.split('censetv=')[-1]
        ab=eval(addon.getSetting('heaNHL'))

        result = requests.post(url=path2, headers=ab, data=challenge, verify=False).content
           
            
        self.send_response(200)
        self.end_headers()
        
        self.wfile.write(result)

            
            
def find_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        addon.setSetting('proxyport',str(s.getsockname()[1]))
        return s.getsockname()[1]           


address = '127.0.0.1'  # Localhost

port = find_free_port()
server_inst = TCPServer((address, port), SimpleHTTPRequestHandler)
server_inst.serve_forever()