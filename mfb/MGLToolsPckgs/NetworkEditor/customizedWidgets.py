#########################################################################
#
# Date: July 2003  Authors: Daniel Stoffler, Michel Sanner
#
#       stoffler@scripps.edu
#       sanner@scripps.edu
#
# Copyright: Daniel Stoffler, Michel Sanner, and TSRI
#
#########################################################################

"""This module subclasses widgets such as the Pmw Notebook """

import sys, os
import Pmw
import Tkinter
from mglutil.gui.BasicWidgets.Tk.customizedWidgets import KeySelectableScrolledCanvas
from mglutil.gui import widgetsOnBackWindowsCanGrabFocus

class kbScrolledCanvas(Pmw.ScrolledCanvas, KeySelectableScrolledCanvas):
    """Pmw.ScrolledCanvas with support to type the name of an item which will
scroll the canvas to the requested item.
"""
    
    def __init__(self, *args, **kw):
        if kw.has_key('itemNames'):
            itemNames = kw['itemNames']
            del kw['itemNames']
        else:
            itemNames = ['']

        # Pmw widgets are very delicate when it comes to subclassing!
        apply( Pmw.ScrolledCanvas.__init__, (self,)+args, kw)

        # now remove the initialization only keywords and configure the widget
        if kw.has_key('borderframe'):
            del kw['borderframe']
        if kw.has_key('labelpos'):
            del kw['labelpos']
        if kw.has_key('usehullsize'):
            del kw['usehullsize']
        apply( self.configure, (self,), kw)

        myWidget = self
        KeySelectableScrolledCanvas.__init__(self, myWidget, itemNames)

        if os.name == 'nt': #sys.platform == 'win32':
            self.component('canvas').bind("<MouseWheel>", self.scrollUpDown)
        else:
            self.component('canvas').bind("<Button-4>", self.scrollUp)
            self.component('canvas').bind("<Button-5>", self.scrollDown)
        self.component('canvas').bind("<Enter>", self.enter_cb)


    def scrollUp(self, event):
        self.component('canvas').yview_scroll(-1, "units")


    def scrollDown(self, event):
        self.component('canvas').yview_scroll(1, "units")


    def scrollUpDown(self, event):
        if event.delta < 0:
            self.scrollDown(event)
        else:
            self.scrollUp(event)


    def enter_cb(self, event=None):
        if widgetsOnBackWindowsCanGrabFocus is False:
            lActiveWindow = self.widget.focus_get()
            if    lActiveWindow is not None \
              and ( lActiveWindow.winfo_toplevel() != self.widget.winfo_toplevel() ):
                return
        self.component('canvas').focus_set()



class mglNoteBook(Pmw.NoteBook):
    """This notebook implements a showpage and hidepage method that allows to
show/hide notebook pages without destroying them."""


    def __init__(self, *args, **kw):
        # Pmw widgets are very delicate when it comes to subclassing!
        apply( Pmw.NoteBook.__init__, (self,)+args, kw)


    def hidepage(self, pageName):
        """New method hidepage"""
        # hide is not possible if only one page present
        if len(self._pageNames) == 1:
            return

        pageInfo = self._pageAttrs[pageName]

        # return, if already hidden
        if pageInfo['visible'] == 0:
            return

        pageInfo['visible'] = 0
        pageIndex = self.index(pageName)
        if pageIndex == 0:
            newTopIndex = 1
        else:
            newTopIndex = pageIndex - 1

        if newTopIndex >=  0:
            newTopPage = self._pageNames[newTopIndex]
            self.selectpage(newTopPage)

        if self._withTabs:
            self._pending['tabs'] = 1
            self._layout()
        

    def showpage(self, pageName):
        """new method showpage"""
        pageInfo = self._pageAttrs[pageName]

        # return, if already visible
        if pageInfo['visible'] == 1:
            return
        
        pageInfo['visible'] = 1

        if self._withTabs:
            self._pending['tabs'] = 1
            self._layout()
        self.selectpage(pageName)


    def selectpage(self, page):
        """overwrite the original method to take in account hidden pages"""
        pageName = self._pageNames[self.index(page)]
        # return if page is not visible
        if self._pageAttrs[pageName]['visible'] == 0:
            return
        oldTopPage = self.getcurselection()
        if pageName != oldTopPage:
            self._pending['topPage'] = pageName
            if oldTopPage == self._topPageName:
                self._hull.delete(self._topPageItem)
            cmd = self['lowercommand']
            if cmd is not None:
                cmd(oldTopPage)
            self._raiseNewTop(pageName)

            self._layout()

        # Set focus to the tab of new top page:
        if self._withTabs and self['arrownavigation']:

            if widgetsOnBackWindowsCanGrabFocus is False:
                lActiveWindow =self._pageAttrs[pageName]['tabbutton'].focus_get()
                if    lActiveWindow is not None \
                  and ( lActiveWindow.winfo_toplevel() != \
                        self._pageAttrs[pageName]['tabbutton'].winfo_toplevel() ):
                    return

            self._pageAttrs[pageName]['tabbutton'].focus_set()


    def previouspage(self, pageIndex = None):
        """overwrite original method"""
        if pageIndex is None:
            curpage = self.index(Pmw.SELECT)
        else:
            curpage = self.index(pageIndex)
        i = 1
        while 1:
            if curpage > 0:
                prevpage = self._pageNames[curpage-i]
                if  self._pageAttrs[prevpage]['visible'] == 0:
                    i = i + 1
                    continue
                else:
                   self.selectpage(curpage - i) 
                   break
            else:
                break


    def nextpage(self, pageIndex = None):
        """overwrite original method"""
        if pageIndex is None:
            curpage = self.index(Pmw.SELECT)
        else:
            curpage = self.index(pageIndex)

        i = 1
        while 1:
            if curpage+i < len(self._pageNames):
                nextpage = self._pageNames[curpage+i]
                if  self._pageAttrs[nextpage]['visible'] == 0:
                    i = i + 1
                    continue
                else:
                   self.selectpage(curpage + i) 
                   break
            else:
                break


    def _layout(self):
        """overwrite original method"""
        if not self.winfo_ismapped() or self._canvasSize is None:
            # Don't layout if the window is not displayed, or we
            # haven't yet received a <Configure> event.
            return

        hullWidth, hullHeight = self._canvasSize
        borderWidth = self._borderWidth
        canvasBorder = int(self._hull['borderwidth']) + \
            int(self._hull['highlightthickness'])
        if not self._withTabs:
            self.tabBottom = canvasBorder
        oldTabBottom = self.tabBottom

        if self._pending.has_key('borderColor'):
            self._lightBorderColor, self._darkBorderColor = \
                    Pmw.Color.bordercolors(self, self['hull_background'])

        # Draw all the tabs.
        if self._withTabs and (self._pending.has_key('tabs') or
                self._pending.has_key('size')):
            # Find total requested width and maximum requested height
            # of tabs.
            sumTabReqWidth = 0
            maxTabHeight = 0
            for pageInfo in self._pageAttrs.values():
                sumTabReqWidth = sumTabReqWidth + pageInfo['tabreqwidth']
                if maxTabHeight < pageInfo['tabreqheight']:
                    maxTabHeight = pageInfo['tabreqheight']
            if maxTabHeight != 0:
                # Add the top tab border plus a bit for the angled corners
                self.tabBottom = canvasBorder + maxTabHeight + borderWidth * 1.5

            # Prepare for drawing the border around each tab button.
            tabTop = canvasBorder
            tabTop2 = tabTop + borderWidth
            tabTop3 = tabTop + borderWidth * 1.5
            tabBottom2 = self.tabBottom
            tabBottom = self.tabBottom + borderWidth

            numTabs = 0
            for v in self._pageAttrs.values():
                if v['visible'] == 1:
                    numTabs = numTabs + 1
            availableWidth = hullWidth - 2 * canvasBorder - \
                numTabs * 2 * borderWidth
            x = canvasBorder
            cumTabReqWidth = 0
            cumTabWidth = 0

            # Position all the tabs.
            for pageName in self._pageNames:
                pageInfo = self._pageAttrs[pageName]
                (windowitem, lightshadow, darkshadow) = pageInfo['tabitems']
                if sumTabReqWidth <= availableWidth:
                    tabwidth = pageInfo['tabreqwidth']
                else:
                    # This ugly calculation ensures that, when the
                    # notebook is not wide enough for the requested
                    # widths of the tabs, the total width given to
                    # the tabs exactly equals the available width,
                    # without rounding errors.
                    cumTabReqWidth = cumTabReqWidth + pageInfo['tabreqwidth']
                    tmp = (2*cumTabReqWidth*availableWidth + sumTabReqWidth) \
                            / (2 * sumTabReqWidth)
                    tabwidth = tmp - cumTabWidth
                    cumTabWidth = tmp

                # Position the tab's button canvas item.
                self.coords(windowitem, x + borderWidth, tabTop3)

                # Tabs that are not shown are drawn as a single line
                if pageInfo['visible'] == 0:
                    tabwidth = 1
                    
                self.itemconfigure(windowitem,
                    width = tabwidth, height = maxTabHeight)

                # Make a beautiful border around the tab.
                left = x
                left2 = left + borderWidth
                left3 = left + borderWidth * 1.5
                right = left + tabwidth + 2 * borderWidth
                right2 = left + tabwidth + borderWidth
                right3 = left + tabwidth + borderWidth * 0.5

                self.coords(lightshadow, 
                    left, tabBottom2, left, tabTop2, left2, tabTop,
                    right2, tabTop, right3, tabTop2, left3, tabTop2,
                    left2, tabTop3, left2, tabBottom,
                    )
                self.coords(darkshadow, 
                    right2, tabTop, right, tabTop2, right, tabBottom2,
                    right2, tabBottom, right2, tabTop3, right3, tabTop2,
                    )
                pageInfo['left'] = left
                pageInfo['right'] = right

                x = x + tabwidth + 2 * borderWidth

        # Redraw shadow under tabs so that it appears that tab for old
        # top page is lowered and that tab for new top page is raised.
        if self._withTabs and (self._pending.has_key('topPage') or
                self._pending.has_key('tabs') or self._pending.has_key('size')):

            if self.getcurselection() is None:
                # No pages, so draw line across top of page area.
                self.coords(self._pageTop1Border,
                    canvasBorder, self.tabBottom,
                    hullWidth - canvasBorder, self.tabBottom,
                    hullWidth - canvasBorder - borderWidth,
                        self.tabBottom + borderWidth,
                    borderWidth + canvasBorder, self.tabBottom + borderWidth,
                    )

                # Ignore second top border.
                self.coords(self._pageTop2Border, 0, 0, 0, 0, 0, 0)
            else:
                # Draw two lines, one on each side of the tab for the
                # top page, so that the tab appears to be raised.
                pageInfo = self._pageAttrs[self.getcurselection()]
                left = pageInfo['left']
                right = pageInfo['right']
                self.coords(self._pageTop1Border,
                    canvasBorder, self.tabBottom,
                    left, self.tabBottom,
                    left + borderWidth, self.tabBottom + borderWidth,
                    canvasBorder + borderWidth, self.tabBottom + borderWidth,
                    )

                self.coords(self._pageTop2Border,
                    right, self.tabBottom,
                    hullWidth - canvasBorder, self.tabBottom,
                    hullWidth - canvasBorder - borderWidth,
                        self.tabBottom + borderWidth,
                    right - borderWidth, self.tabBottom + borderWidth,
                    )

            # Prevent bottom of dark border of tabs appearing over
            # page top border.
            self.tag_raise(self._pageTop1Border)
            self.tag_raise(self._pageTop2Border)

        # Position the page border shadows.
        if self._pending.has_key('size') or oldTabBottom != self.tabBottom:

            self.coords(self._pageLeftBorder,
                canvasBorder, self.tabBottom,
                borderWidth + canvasBorder,
                    self.tabBottom + borderWidth,
                borderWidth + canvasBorder,
                    hullHeight - canvasBorder - borderWidth,
                canvasBorder, hullHeight - canvasBorder,
                )

            self.coords(self._pageBottomRightBorder,
                hullWidth - canvasBorder, self.tabBottom,
                hullWidth - canvasBorder, hullHeight - canvasBorder,
                canvasBorder, hullHeight - canvasBorder,
                borderWidth + canvasBorder,
                    hullHeight - canvasBorder - borderWidth,
                hullWidth - canvasBorder - borderWidth,
                    hullHeight - canvasBorder - borderWidth,
                hullWidth - canvasBorder - borderWidth,
                    self.tabBottom + borderWidth,
                )

            if not self._withTabs:
                self.coords(self._pageTopBorder,
                    canvasBorder, self.tabBottom,
                    hullWidth - canvasBorder, self.tabBottom,
                    hullWidth - canvasBorder - borderWidth,
                        self.tabBottom + borderWidth,
                    borderWidth + canvasBorder, self.tabBottom + borderWidth,
                    )

        # Color borders.
        if self._pending.has_key('borderColor'):
            self.itemconfigure('lighttag', fill = self._lightBorderColor)
            self.itemconfigure('darktag', fill = self._darkBorderColor)

        newTopPage = self._pending.get('topPage')
        pageBorder = borderWidth + self._pageMargin

        # Raise new top page.
        if newTopPage is not None:
            self._topPageName = newTopPage
            self._topPageItem = self.create_window(
                pageBorder + canvasBorder, self.tabBottom + pageBorder,
                window = self._pageAttrs[newTopPage]['page'],
                anchor = 'nw',
                )

        # Change position of top page if tab height has changed.
        if self._topPageName is not None and oldTabBottom != self.tabBottom:
            self.coords(self._topPageItem,
                    pageBorder + canvasBorder, self.tabBottom + pageBorder)

        # Change size of top page if,
        #   1) there is a new top page.
        #   2) canvas size has changed, but not if there is no top
        #      page (eg:  initially or when all pages deleted).
        #   3) tab height has changed, due to difference in the height of a tab
        if (newTopPage is not None or \
                self._pending.has_key('size') and self._topPageName is not None
                or oldTabBottom != self.tabBottom):
            self.itemconfigure(self._topPageItem,
                width = hullWidth - 2 * canvasBorder - pageBorder * 2,
                height = hullHeight - 2 * canvasBorder - pageBorder * 2 -
                    (self.tabBottom - canvasBorder),
                )

        self._pending = {}


    def insert(self, pageName, before = 0, **kw):
        """overwrite original method"""
	if self._pageAttrs.has_key(pageName):
	    msg = 'Page "%s" already exists.' % pageName
	    raise ValueError, msg

        # Do this early to catch bad <before> spec before creating any items.
	beforeIndex = self.index(before, 1)

        pageOptions = {}
        if self._withTabs:
            # Default tab button options.
            tabOptions = {
                'text' : pageName,
                'borderwidth' : 0,
            }

        # Divide the keyword options into the 'page_' and 'tab_' options.
        for key in kw.keys():
            if key[:5] == 'page_':
                pageOptions[key[5:]] = kw[key]
                del kw[key]
            elif self._withTabs and key[:4] == 'tab_':
                tabOptions[key[4:]] = kw[key]
                del kw[key]
            else:
		raise KeyError, 'Unknown option "' + key + '"'

        # Create the frame to contain the page.
	page = apply(self.createcomponent, (pageName,
		(), 'Page',
		Tkinter.Frame, self._hull), pageOptions)

        attributes = {}
        attributes['page'] = page
        attributes['created'] = 0
        attributes['visible'] = 1

        if self._withTabs:
            # Create the button for the tab.
            def raiseThisPage(self = self, pageName = pageName):
                self.selectpage(pageName)
            tabOptions['command'] = raiseThisPage
            tab = apply(self.createcomponent, (pageName + '-tab',
                    (), 'Tab',
                    Tkinter.Button, self._hull), tabOptions)

            if self['arrownavigation']:
                # Allow the use of the arrow keys for Tab navigation:
                def next(event, self = self, pageName = pageName):
                    self.nextpage(pageName)
                def prev(event, self = self, pageName = pageName):
                    self.previouspage(pageName)
                tab.bind('<Left>', prev)
                tab.bind('<Right>', next)

            attributes['tabbutton'] = tab
            attributes['tabreqwidth'] = tab.winfo_reqwidth()
            attributes['tabreqheight'] = tab.winfo_reqheight()

            # Create the canvas item to manage the tab's button and the items
            # for the tab's shadow.
            windowitem = self.create_window(0, 0, window = tab, anchor = 'nw')
            lightshadow = self.create_polygon(0, 0, 0, 0, 0, 0,
                tags = 'lighttag', fill = self._lightBorderColor)
            darkshadow = self.create_polygon(0, 0, 0, 0, 0, 0,
                tags = 'darktag', fill = self._darkBorderColor)
            attributes['tabitems'] = (windowitem, lightshadow, darkshadow)
            self._pending['tabs'] = 1

        self._pageAttrs[pageName] = attributes
	self._pageNames.insert(beforeIndex, pageName)

        # If this is the first page added, make it the new top page
        # and call the create and raise callbacks.
        if self.getcurselection() is None:
            self._pending['topPage'] = pageName
            self._raiseNewTop(pageName)

        self._layout()
        return page
