import eg
import httplib
import xml.etree.ElementTree as ET

eg.RegisterPlugin(
    name = "Homematic XML API",
    author = "klemensl",
    version = "0.0.1",
    kind = "other",
    description = "..."
)

class HMXMLAPI(eg.PluginBase):
    HM_XMLAPI_URL= "/config/xmlapi/"
    HM_XMLAPI_STATE = "state.cgi?datapoint_id={0}"
    HM_XMLAPI_STATECHANGE = "statechange.cgi?ise_id={0}&new_value={1}"

    def __init__(self):
        self.AddAction(sysvarlist)
        self.AddAction(statelist)
        self.AddAction(turnOnOrOff)
        self.AddAction(setValue)
        self.AddAction(setValueFromPayload)
        self.AddAction(callCGIfromPayload)
        self.AddAction(turnOnFromPayload)
        self.AddAction(turnOffFromPayload)
        
    def __start__(self, protocol, host, port):
        self.host = host
        print "Homematic XML API Plugin is started with parameter: " + self.host
        
    def Configure(self, protocol="HTTP", host="", port=80):
        panel = eg.ConfigPanel(self)
        protocolCtrl = panel.TextCtrl(protocol)
        hostCtrl = panel.TextCtrl(host)
        portCtrl = panel.SpinIntCtrl(port, min=1, max=65535)
        panel.sizer.AddMany([
            panel.StaticText("Protocol:"),
            protocolCtrl,
            panel.StaticText("Host:"),
            hostCtrl,
            panel.StaticText("Port:"),
            portCtrl,
        ])
        while panel.Affirmed():
            panel.SetResult(
                protocolCtrl.GetValue(),
                hostCtrl.GetValue(),
                portCtrl.GetValue()
            )

    def SendRequest(self, request):
        print "sending request to: " + self.host + request
        conn = httplib.HTTPConnection(self.host)
        conn.request("GET", request)
        response = conn.getresponse()
        data = response.read()
        conn.close()
        dataBody = data.partition('?>')[2]
        #print response.status, response.reason, dataBody
        eg.globals.ccu2xmlapiresponse = dataBody
        return dataBody

    def changeState(self, ise_id, new_value):
        self.SendRequest(self.HM_XMLAPI_URL + self.HM_XMLAPI_STATECHANGE.format(ise_id, new_value).lower())
        dataBody = self.SendRequest(self.HM_XMLAPI_URL + self.HM_XMLAPI_STATE.format(ise_id).lower())
        datapoint = ET.fromstring(dataBody).find('datapoint')
        if datapoint is not None:
            datapointValue = datapoint.get('value')
        else:
            datapointValue = "unknown"
        eg.globals.ccu2statechangedto = datapointValue; 
        print "ise_id {0} changed to {1}".format(ise_id, datapointValue)
            

class sysvarlist(eg.ActionBase):
    name = "CCU2 Call: sysVarList.cgi"

    def __call__(self):
        print "Action 'SysVarList'"
        data = self.plugin.SendRequest(self.plugin.HM_XMLAPI_URL + "sysvarlist.cgi")
        eg.globals.ccu2statechangedto = ""
            

class statelist(eg.ActionBase):
    name = "CCU2 Call: stateList.cgi"

    def __call__(self):
        print "Action 'StateList'"
        self.plugin.SendRequest(self.plugin.HM_XMLAPI_URL + "statelist.cgi")
        eg.globals.ccu2statechangedto = ""

            
class turnOnOrOff(eg.ActionBase):
    def __call__(self, ise_id, new_value):
        print "Action 'Statechange' - ID: {0}={1}".format(ise_id, new_value)
        self.plugin.changeState(ise_id, new_value)

    def GetLabel(self, ise_id, new_value):
        return "Change state of ise_id {0} to {1}".format(ise_id, new_value) 

    def Configure(self, ise_id="", new_value=True):
        panel = eg.ConfigPanel(self)
        ise_idCtrl = panel.TextCtrl(ise_id)
        new_valueCtrl = panel.CheckBox(new_value)
        panel.AddLine(panel.StaticText("ise_id:"), ise_idCtrl)
        panel.AddLine(panel.StaticText("ON/OFF:"), new_valueCtrl)
        while panel.Affirmed():
            panel.SetResult(
                ise_idCtrl.GetValue(),
                new_valueCtrl.GetValue()
            )

            
class setValue(eg.ActionBase):
    def __call__(self, ise_id, new_value):
        print "Action 'Statechange' - ID: {0}={1}".format(ise_id, new_value)
        self.plugin.changeState(ise_id, new_value)

    def GetLabel(self, ise_id, new_value):
        return "Set the value of ise_id {0} to {1}".format(ise_id, new_value) 

    def Configure(self, ise_id="", new_value=""):
        panel = eg.ConfigPanel(self)
        ise_idCtrl = panel.TextCtrl(ise_id)
        new_valueCtrl = panel.TextCtrl(new_value)
        panel.AddLine(panel.StaticText("ise_id:"), ise_idCtrl)
        panel.AddLine(panel.StaticText("Value:"), new_valueCtrl)
        while panel.Affirmed():
            panel.SetResult(
                ise_idCtrl.GetValue(),
                new_valueCtrl.GetValue()
            )

            
class setValueFromPayload(eg.ActionBase):
    def __call__(self, ise_id):
        if not eg.event.payload:
             print "No payload set - skipping..."
             return False
        new_value = eg.event.payload[0]
        print "Action 'Statechange' - ID: {0}={1}".format(ise_id, new_value)
        self.plugin.changeState(ise_id, new_value)

    def GetLabel(self, ise_id, new_value):
        return "Set the value of ise_id {0} to 'eg.event.payload[0]'".format(ise_id) 

    def Configure(self, ise_id=""):
        panel = eg.ConfigPanel(self)
        ise_idCtrl = panel.TextCtrl(ise_id)
        panel.AddLine(panel.StaticText("ise_id:"), ise_idCtrl)
        while panel.Affirmed():
            panel.SetResult(
                ise_idCtrl.GetValue()
            )

            
class callCGIfromPayload(eg.ActionBase):
    name = "CCU2 Call: From Event Payload"
    description = "Call the CCU2 XML API .CGI with the Payload of the current event -> http://IP/config/xmlapi/eg.event.payload[0].cgi"
    
    def __call__(self):
        if not eg.event.payload:
             print "No payload set - skipping..."
             return False
        print "Action 'From Payload' - Payload: " + eg.event.payload[0]
        self.plugin.SendRequest(self.plugin.HM_XMLAPI_URL + eg.event.payload[0] + ".cgi")

class turnOnFromPayload(eg.ActionBase):
    name = "CCU2 Call: Turn ise_id 'eg.event.payload[0]' ON"
    description = ""
    
    def __call__(self):
        if not eg.event.payload:
             print "No payload set - skipping..."
             return False
        ise_id = eg.event.payload[0]
        print "Action 'Turn ON from Payload' - Payload: " + ise_id
        self.plugin.changeState(ise_id, "true")

            
class turnOffFromPayload(eg.ActionBase):
    name = "CCU2 Call: Turn ise_id 'eg.event.payload[0]' OFF"
    description = ""
    
    def __call__(self):
        if not eg.event.payload:
             print "No payload set - skipping..."
             return False
        ise_id = eg.event.payload[0]
        print "Action 'Turn OFF from Payload' - Payload: " + ise_id
        self.plugin.changeState(ise_id, "false")