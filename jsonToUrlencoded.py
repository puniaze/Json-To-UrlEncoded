from burp import IBurpExtender, IContextMenuFactory
from java.io import PrintWriter
from java.util import ArrayList
from javax.swing import JMenuItem
from javax.swing import JOptionPane
import json, re

class BurpExtender(IBurpExtender,IContextMenuFactory):
    
    def	registerExtenderCallbacks(self, callbacks):
        
        self._callbacks = callbacks
        self._helpers = callbacks.getHelpers()
        
        self.stdout = PrintWriter(callbacks.getStdout(), True)
        self.stderr = PrintWriter(callbacks.getStderr(), True)

        self._callbacks.setExtensionName("Json-to-Urlencoded")
        self.echo("[*] @author Abdulla Ismayilov - ai@underdefense.com")
        self._callbacks.registerContextMenuFactory(self)
        

    def echo(self, data):
        self.stdout.println(data)


    def createMenuItems(self, invocation):
        self.context = invocation
        menuList = ArrayList()

        menuList.add(JMenuItem("Convert json to x-www-form-urlencoded",
                actionPerformed=self.convertJsonToUrlencoded))

        return menuList


    def convertJsonToUrlencoded(self, event):
        IHttpRequestResponse = self.context.getSelectedMessages()[0]
        request_bytes = IHttpRequestResponse.getRequest()
        req_analyze = self._helpers.analyzeRequest(request_bytes)
        
        req_headers = req_analyze.getHeaders()
        req_body_offset = req_analyze.getBodyOffset()
        
        bodyBytes = request_bytes[req_body_offset:]
        body = self._helpers.bytesToString(bodyBytes)
        body = self.jsonToUrlEnc(body)
        
        fin_headers = []
        for header in req_headers:
            if('content-type:' in header.lower()):
                fin_headers.append('Content-Type: application/x-www-form-urlencoded')
            else:
                fin_headers.append(header)

        converted_request = self._helpers.buildHttpMessage(fin_headers,  self._helpers.stringToBytes(body))
        IHttpRequestResponse.setRequest(converted_request)

    def typeToStr(self, t):
        return re.findall("'(.*)'", str(type(t)))[0]

    def parser(self, parent, inner):
        res = ''
        typeOfInner = self.typeToStr(inner)
        if(typeOfInner == 'dict'):
            for key in inner.keys():
                if(self.typeToStr(inner[key]) == 'list' or self.typeToStr(inner[key]) == 'dict'):
                    res += self.parser(parent+'.'+key, inner[key])
                else:
                    res += parent+'.'+key+'='+self._helpers.urlEncode(str(inner[key]))+'&'
        elif(typeOfInner == 'list'):
            for key in inner:
                if(self.typeToStr(key) == 'list' or self.typeToStr(key) == 'dict'):
                    res += self.parser(parent+'[]', key)
                else:
                    res += parent+'[]='+self._helpers.urlEncode(str(key))+'&'
        else:
            if(self.typeToStr(inner) == 'bool'):
                res += parent + '='+self._helpers.urlEncode(str(int(inner)))+'&'
            elif(self.typeToStr(inner) == 'NoneType'):
                res += parent + '=&'
            else:
                res += parent+'='+self._helpers.urlEncode(str(inner))+'&'

        return res     
    
    def jsonToUrlEnc(self, body):
        try:
            js = json.loads(body)
        except:
            return body

        result = ''
        for key in js.keys():
            result += self.parser(key, js[key])

        
        return result[:len(result)-1]


