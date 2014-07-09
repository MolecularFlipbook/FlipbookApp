# Author: Sargis Dallakyan (sargis@scripps.edu)
# $Header: /opt/cvs/WebServices/listGUI.py,v 1.2 2008/03/27 22:15:42 sargis Exp $
# $Id: listGUI.py,v 1.2 2008/03/27 22:15:42 sargis Exp $
"GUI for listing available Web Service"

import sys,time
import Tkinter
import Pmw
import urllib

from mglutil.web.services.AppService_client import AppServiceLocator, launchJobRequest, \
getOutputsRequest, queryStatusRequest, getAppMetadataRequest
from mglutil.web.services.AppService_types import ns0
class ListWS:
    """
    This class tries to list the deployed Web services
    """
    def __init__(self, parent = None):
        if not parent:
            parent = Tkinter.Tk()
            Pmw.initialise(parent)
            title = 'View the list of deployed Web services'
            parent.title(title)
            exitButton = Tkinter.Button(parent, text = 'Exit', command = parent.destroy)
            exitButton.pack(side = 'bottom')
        self.parent = parent
        # Create a group widget to contain the ComboBox for the Hosts.
        Hosts_Group = Pmw.Group(parent, tag_pyclass = None)
        Hosts_Group.pack(fill='x')
        self.Hosts_ComboBox = Pmw.ComboBox(Hosts_Group.interior(),
                           label_text = 'Hosts:',
                           labelpos = 'ws',
                           entry_width = 30,
                           scrolledlist_items=('http://ws.nbcr.net:8080/opal',),
                           selectioncommand = self.update_services
                           )
        self.Hosts_ComboBox.pack(padx = 1, pady = 1)

        # ScrolledListBox for listing Services
        from mglutil.gui.BasicWidgets.Tk.TreeWidget.tree import TreeView
        frame = Tkinter.Frame(parent)
        frame.pack(side = 'left',fill='both')
        label = Tkinter.Label(frame,text = 'Services')
        label.pack()
        self.Services_Tree = TreeView(master=frame,treeWidth=230,width=230)
        self.Services_Tree.setAction(event='select', 
                                      function=self.getDescription)

        # ScrolledText for providing information about Web Services
        self.Description_Text = Pmw.ScrolledText(parent,
        labelpos='nsew',
        label_text='Description',
        text_state = 'disabled'
        )
        
        #self.Services_Box.pack(side = 'left',fill='both')
        self.Description_Text.pack(side = 'right',expand = 1,fill='both')
        self.Hosts_ComboBox.selectitem(0)
        self.Services_dict = {}
        self.update_services(None)
        parent.mainloop()
        
    def update_services(self,event):
        self.parent.config(cursor='watch')
        self.Description_Text.configure(text_state = 'normal')
        self.Description_Text.clear()
        self.URL = self.Hosts_ComboBox.get()
        opener = urllib.FancyURLopener({}) 

        for key in self.Services_dict:
            self.Services_Tree.deleteNode(key)
        self.Services_dict = {}
        try:
            servlet = opener.open(self.URL+"/servlet/AxisServlet")
        except IOError:
            errorMsg = self.URL+"/servlet/AxisServlet could not be found"
            errorMsg += "\nPlease make sure that server is up and running"
            import tkMessageBox
            tkMessageBox.showerror("Error!",errorMsg)
            self.parent.config(cursor='')
            return

        text = servlet.read()
        text = text.split('<ul>')
        if text[0].find('<h2>And now... Some Services</h2>') == -1:
            errorMsg = self.URL+"/servlet/AxisServlet could not be found"
            errorMsg += "\nPlease make sure that server is up and running"
            import tkMessageBox
            tkMessageBox.showerror("Error!",errorMsg)
            self.parent.config(cursor='')
            return
        text = text[1:]
        last_service = ""
        for line in text[:-1]:
            methods = line.split('</ul>')
            if len(methods) > 1:
                methods = methods[0]
                methods = methods.split('<li>')
                methods = methods[1:]
                for method in methods:
                    self.Services_Tree.addNode(method.strip(),parent=last_service)
            tmp_text = line.split(self.URL+"/services/")
            port = tmp_text[-1].split('wsdl')
            self.Services_Tree.addNode(port[0][:-1])
            self.Services_dict[port[0][:-1]] = self.URL+"/services/" + \
                port[0][:-1] + "?wsdl"
            last_service = port[0][:-1]
        methods = line.split('</ul>')
        if len(methods) > 1:
            methods = methods[0]
            methods = methods.split('<li>')
            methods = methods[1:]
            for method in methods:
                self.Services_Tree.addNode(method.strip(),parent=last_service)
        self.parent.config(cursor='')        
        #self.Services_Tree.deleteNode('AdminService')
        #self.Services_Tree.deleteNode('Version')
        #self.Services_Tree.deleteNode('APBSJobSubPort')

    def getDescription(self, tree_node):
        if tree_node.parent:
            service = tree_node.parent.GetFullName()
        else:
            service = tree_node.GetFullName()
        import ZSI
        self.Description_Text.configure(text_state = 'normal')
        self.Description_Text.clear()
        from ZSI.generate.wsdl2python import WriteServiceModule
        from ZSI.wstools import WSDLTools
        reader = WSDLTools.WSDLReader()
        wsdl = reader.loadFromURL(self.Services_dict[service])
        try:  
            wsdl.services['AppService']
        except:
            self.Description_Text.insert('end', 'Sorry, only Opal based web services are supported http://nbcr.net/services/opal')
            self.Description_Text.configure(text_state = 'disabled')
            return
        appLocator = AppServiceLocator()
        appServicePort = appLocator.getAppServicePort(\
                       self.URL + "/services/"+service)
        req = getAppMetadataRequest()
        resp = appServicePort.getAppMetadata(req)
        self.Description_Text.configure(text_state = 'normal')
        if resp._info:
            self.Description_Text.insert('end',resp._usage+"\n\n")
            self.Description_Text.insert('end',resp._info[0])
        else:
            self.Description_Text.insert('end',resp._usage)
        self.Description_Text.configure(text_state = 'disabled')
######################################################################               
# Create demo in root window for testing.
if __name__ == '__main__':
    ListWS()


