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

    def __init__(self):
        self.AddAction(sysvarlist)
        self.AddAction(statelist)
        self.AddAction(turnonoroff)
        self.AddAction(frompayload)
        self.AddAction(turnOnFromPayload)
        self.AddAction(turnOffFromPayload)
        self.AddAction(setValue)
		
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
                portCtrl.GetValue(),
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
			

class sysvarlist(eg.ActionBase):
    name = "CCU2 Call: SysVarList"

    def __call__(self):
        print "Action 'SysVarList'"
        data = self.plugin.SendRequest("/config/xmlapi/sysvarlist.cgi")
        eg.globals.ccu2statechangedto = ""
			

class statelist(eg.ActionBase):
    name = "CCU2 Call: StateList"

    def __call__(self):
        print "Action 'StateList'"
        data = self.plugin.SendRequest("/config/xmlapi/statelist.cgi")
        eg.globals.ccu2statechangedto = ""
			
class turnonoroff(eg.ActionBase):
    name = "CCU2 Call: Turn Channel (ise_id) ON or OFF (new_value)"

    def __call__(self, ise_id, new_value):
        print "Action 'Statechange' - ID: {0}={1}".format(ise_id, new_value)
        dataBody = self.plugin.SendRequest("/config/xmlapi/statechange.cgi?ise_id={0}&new_value={1}".format(ise_id, new_value).lower())
        dataBody = self.plugin.SendRequest("/config/xmlapi/state.cgi?datapoint_id={0}".format(ise_id).lower())
        eg.globals.ccu2statechangedto = ET.fromstring(dataBody).find('datapoint').get('value')

    def Configure(self, ise_id="", new_value=True):
        panel = eg.ConfigPanel(self)
        ise_idCtrl = panel.TextCtrl(ise_id)
        new_valueCtrl = panel.CheckBox(new_value)
        panel.AddLine(panel.StaticText("Ise ID:"), ise_idCtrl)
        panel.AddLine(panel.StaticText("ON/OFF:"), new_valueCtrl)
        while panel.Affirmed():
            panel.SetResult(
                ise_idCtrl.GetValue(),
                new_valueCtrl.GetValue(),
            )
			
class setValue(eg.ActionBase):
    name = "CCU2 Call: Set Channel (ise_id) value (new_value)"

    def __call__(self, ise_id, new_value):
        print "Action 'Statechange' - ID: {0}={1}".format(ise_id, new_value)
        dataBody = self.plugin.SendRequest("/config/xmlapi/statechange.cgi?ise_id={0}&new_value={1}".format(ise_id, new_value).lower())
        dataBody = self.plugin.SendRequest("/config/xmlapi/state.cgi?datapoint_id={0}".format(ise_id).lower())
        eg.globals.ccu2statechangedto = ET.fromstring(dataBody).find('datapoint').get('value')

    def Configure(self, ise_id="", new_value=""):
        panel = eg.ConfigPanel(self)
        ise_idCtrl = panel.TextCtrl(ise_id)
        new_valueCtrl = panel.TextCtrl(new_value)
        panel.AddLine(panel.StaticText("Ise ID:"), ise_idCtrl)
        panel.AddLine(panel.StaticText("Value:"), new_valueCtrl)
        while panel.Affirmed():
            panel.SetResult(
                ise_idCtrl.GetValue(),
                new_valueCtrl.GetValue(),
            )
			
class frompayload(eg.ActionBase):
    name = "CCU2 Call: From Event Payload"
    description = "Call the CCU2 XML API with the Payload of the current event -> http://IP/config/xmlapi/EventPayload.cgi"
	
    def __call__(self):
        if not eg.event.payload:
             print "No payload set - skipping..."
             return False
        print "Action 'From Payload' - Payload: " + eg.event.payload[0]
        data = self.plugin.SendRequest("/config/xmlapi/" + eg.event.payload[0] + ".cgi")
			
class turnOnFromPayload(eg.ActionBase):
    name = "CCU2 Call: Turn ON from Event Payload"
    description = ""
	
    def __call__(self):
        if not eg.event.payload:
             print "No payload set - skipping..."
             return False
        ise_id = eg.event.payload[0]
        print "Action 'Turn ON from Payload' - Payload: " + ise_id
        dataBody = self.plugin.SendRequest("/config/xmlapi/statechange.cgi?ise_id={0}&new_value=true".format(ise_id).lower())
        dataBody = self.plugin.SendRequest("/config/xmlapi/state.cgi?datapoint_id={0}".format(ise_id).lower())
        eg.globals.ccu2statechangedto = ET.fromstring(dataBody).find('datapoint').get('value')

			
class turnOffFromPayload(eg.ActionBase):
    name = "CCU2 Call: Turn OFF from Event Payload"
    description = ""
	
    def __call__(self):
        if not eg.event.payload:
             print "No payload set - skipping..."
             return False
        ise_id = eg.event.payload[0]
        print "Action 'Turn OFF from Payload' - Payload: " + ise_id
        dataBody = self.plugin.SendRequest("/config/xmlapi/statechange.cgi?ise_id={0}&new_value=false".format(ise_id).lower())
        dataBody = self.plugin.SendRequest("/config/xmlapi/state.cgi?datapoint_id={0}".format(ise_id).lower())
        eg.globals.ccu2statechangedto = ET.fromstring(dataBody).find('datapoint').get('value')
