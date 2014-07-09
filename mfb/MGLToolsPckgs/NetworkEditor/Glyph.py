#
#
#

#$Id$

from mglutil.util.callback import CallbackFunction



class Glyph:

    def __init__(self,canvas,shape,kw={}):
        self.canvas = canvas
        self.shape =shape
        #if self.shape in ['label','circle','rectangle','polygon','line','arc','image','bitmap']:
        #    if self.shape == 'label':
        #        label = kw['label']
        #        font = kw['font']
        #        fill = kw['fill']
        #        position = kw['position']
        #        anchor = kw['anchor']
        #        self.create_label(postion=postion,text=label,font=font,fill=fill,anchor=anchor)
        #    if self.shape == 'circle':
        #        bbox = kw['bbox']
        #        fill = kw['fill']
        #        outline = kw['outline']
        #        anchor = kw['anchor']
        #        
        #    if self.shape == 'rectangle':
        #        bbox = kw['bbox']
        #        fill = kw['fill']
        #        outline = kw['outline']
        #        anchor = kw['anchor']
        #        self.create_rectangle(bbox=bbox,fill=fill,outline =outline,anchor=anchor)    
        #    if self.shape == 'polygon':
        #        coords = kw['coords']
        #        fill = kw['fill']
        #        outline = kw['outline']
        #        anchor = kw['anchor']
        #        self.create_polygon(coords=coords,fill=fill,outline =outline,anchor=anchor)
        #ids = self.canvas.find_withtag("movable")
        #for id in ids:
        #    cb =  CallbackFunction(self.moveCanvasObject, id)
        #    self.canvas.tag_bind(id, '<B2-Motion>', cb)


        
    def create_label( self,label, font, fill,position,anchor):
        lab = self.canvas.create_text(position=postion,text=label,font=font,fill=fill,anchor=anchor)

    def create_circle(self,bbox,fill,outline,anchor):
        
        cir = self.canvas.create_oval(bbox[0],bbox[1],bbox[2],bbox[3],fill=fill,outline =outline)
        return cir

    def create_rectangle(self,bbox,fill,outline,anchor):
        rec = self.canvas.create_rectangle(bbox[0],bbox[1],bbox[2],bbox[3],fill=fill,outline =outline) 
        return rec

    def create_polygon(self,coords,fill,outline,anchor):
        poly = self.canvas.create_polygon(coords=coords,fill=fill,outline =outline,anchor=anchor) 

    
        
        
        
    
        
