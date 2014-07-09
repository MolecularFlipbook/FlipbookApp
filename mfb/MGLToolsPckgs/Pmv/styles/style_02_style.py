numberOfMolecules = 2

__doc__ = """Style_02: Applies to a pair of molecules. It displays a green translucent
molecular surface and a yellow ribbon diagram for AminoAcids and Nucleotides
in the first molecule.
Ligands and ions from the second molecule are displayed ar sticks and balls
colored by atom type.
"""

def applyStyle(mv, molName1, molName2, quality='preview'):
    mode='both'
    if mv.getMolFromName(molName1).geomContainer.geoms.has_key('MSMS-MOL'):
        mv.displayMSMS("%s::AminoAcids,Nucleotides"%molName1, log=0, setupUndo=0)
    else:
        mv.computeMSMS("%s::AminoAcids,Nucleotides"%molName1, perMol=False, log=0, setupUndo=0)
    mv.displayLines("%s,%s"%(molName1, molName2), negate=True, log=0, setupUndo=0)
    mv.displaySticksAndBalls("%s::ligand, ions"%molName2, log=0, cquality=0, sticksBallsLicorice='Sticks and Balls', bquality=0, cradius=0.15, bRad=0.4, bScale=0.0, setupUndo=0)
    mv.colorByAtomType("%s::ligand, ions"%molName2, ['sticks', 'balls'], log=0, setupUndo=0)
    mv.setbackgroundcolor((1, 1, 1,), log=0, setupUndo=0)
    mv.displayExtrudedSS("%s"%molName1, log=0, setupUndo=0)

    if mode=='viewer' or mode=='both':
        ## Cameras
        ## Camera Number 0
        state = {'color': [1, 1, 1, 1.0], 'd2off': 1, 'sideBySideTranslation': 0.0, 'stereoMode': 'MONO', 'sideBySideRotAngle': 3.0, 'boundingbox': 0, 'projectionType': 0, 'contours': False, 'd2cutL': 150, 'd2cutH': 255, 'd1off': 4, 'd1cutH': 60, 'antialiased': 4, 'd1cutL': 0, 'd2scale': 0.0, 'drawThumbnail': False, 'd1scale': 0.012999999999999999}
        apply(mv.GUI.VIEWER.cameras[0].Set, (), state)
    
        state = {'end': 233.50498132315809, 'density': 0.10000000000000001, 'color': [1, 1, 1, 1.0], 'enabled': 1, 'start': 135.17698030081922, 'mode': 'GL_LINEAR'}
        apply(mv.GUI.VIEWER.cameras[0].fog.Set, (), state)
    
        ## End Cameras
    
        ## Clipping planes
        ## End Clipping planes
    
        ## Root object
        state = {'scissorAspectRatio': 1.0, 'inheritStippleLines': 0, 'stippleLines': False, 'disableStencil': False, 'replace': True, 'visible': True, 'immediateRendering': False, 'inheritLighting': False, 'invertNormals': False, 'pivot': [1.349, -19.484000000000002, 16.475999999999999], 'rotation': [0.049411494, 0.99872935, 0.0099097034, 0.0, -0.89681298, 0.048732266, -0.4397178, 0.0, -0.43964198, 0.012839964, 0.89808136, 0.0, 0.0, 0.0, 0.0, 1.0], 'instanceMatricesFromFortran': [[1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0]], 'scissorH': 200, 'frontPolyMode': 'fill', 'blendFunctions': ('GL_SRC_ALPHA', 'GL_ONE_MINUS_SRC_ALPHA'), 'outline': (False, False), 'vertexArrayFlag': False, 'scissorX': 0, 'scissorY': 0, 'listed': True, 'inheritPointWidth': 0, 'pickable': True, 'pointWidth': 2, 'scissorW': 200, 'needsRedoDpyListOnResize': False, 'stipplePolygons': False, 'pickableVertices': False, 'inheritMaterial': False, 'depthMask': 1, 'inheritSharpColorBoundaries': False, 'scale': [1.0, 1.0, 1.0], 'lighting': True, 'inheritCulling': False, 'inheritShading': False, 'shading': 'smooth', 'translation': [-0.5086943876553458, 0.87168954700743928, 28.378548532961346], 'transparent': False, 'sharpColorBoundaries': True, 'culling': 'back', 'name': 'root', 'backPolyMode': 'fill', 'inheritFrontPolyMode': False, 'inheritStipplePolygons': 0, 'inheritBackPolyMode': False, 'scissor': 0, 'inheritLineWidth': 0, 'lineWidth': 2, 'inheritXform': 0}
        #apply(mv.GUI.VIEWER.rootObject.Set, (), state)
    
        ## End Root Object
    
        ## Clipping Planes for root
        if mv.GUI.VIEWER.rootObject:
            mv.GUI.VIEWER.rootObject.clipP = []
            mv.GUI.VIEWER.rootObject.clipPI = []
            pass  ## needed in case there no modif
        ## End Clipping Planes for root
    
    if mode=='objects' or mode=='both':
        pass #needed in case there no modif
        ##
        ## Saving State for objects in Viewer
        ##
    
        ## Object root|1jff|sticks
        state = {'scissorAspectRatio': 1.0, 'inheritStippleLines': True, 'stippleLines': False, 'disableStencil': False, 'replace': True, 'visible': 1, 'immediateRendering': False, 'inheritLighting': True, 'invertNormals': False, 'pivot': [0.0, 0.0, 0.0], 'quality': 5, 'rotation': [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0], 'instanceMatricesFromFortran': [[1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0]], 'scissorH': 200, 'frontPolyMode': 'fill', 'blendFunctions': ('GL_SRC_ALPHA', 'GL_ONE_MINUS_SRC_ALPHA'), 'outline': (False, False), 'vertexArrayFlag': False, 'scissorX': 0, 'scissorY': 0, 'listed': True, 'inheritPointWidth': True, 'pickable': True, 'pointWidth': 2, 'scissorW': 200, 'needsRedoDpyListOnResize': False, 'stipplePolygons': False, 'pickableVertices': False, 'inheritMaterial': 0, 'depthMask': 1, 'inheritSharpColorBoundaries': True, 'scale': [1.0, 1.0, 1.0], 'lighting': True, 'inheritCulling': True, 'inheritShading': True, 'shading': 'smooth', 'translation': [0.0, 0.0, 0.0], 'transparent': 0, 'sharpColorBoundaries': True, 'culling': 'back', 'name': 'sticks', 'backPolyMode': 'fill', 'inheritFrontPolyMode': True, 'inheritStipplePolygons': True, 'inheritBackPolyMode': True, 'scissor': 0, 'protected': True, 'inheritLineWidth': True, 'lineWidth': 2, 'inheritXform': 1}
        obj = mv.GUI.VIEWER.FindObjectByName('root|'+molName2+'|sticks')
        if obj:
            apply(obj.Set, (), state)
    
        ## Material for sticks
        if obj:
            from opengltk.OpenGL import GL
            state = {'opacity': [1.0], 'binding': [10, 10, 10, 10, 10, 10], 'shininess': [13.0], 'emission': [[0.0, 0.0, 0.0, 1.0]], 'specular': [[0.89999997615814209, 0.89999997615814209, 0.89999997615814209, 1.0]], 'ambient': [[0.0, 0.0, 0.0, 1.0]], 'diffuse': [[0.0555555559694767, 0.0555555559694767, 0.0555555559694767, 1.0]]}
            apply(obj.materials[GL.GL_FRONT].Set, (), state)
    
        ## End Materials for sticks
    
        ## Clipping Planes for sticks
        if obj:
            obj.clipP = []
            obj.clipPI = []
            pass  ## needed in case there no modif
        ## End Clipping Planes for sticks
    
        ## Object root|1jff|balls
        state = {'scissorAspectRatio': 1.0, 'inheritStippleLines': True, 'stippleLines': False, 'disableStencil': False, 'replace': True, 'immediateRendering': False, 'inheritLighting': True, 'invertNormals': False, 'pivot': [0.0, 0.0, 0.0], 'quality': 4, 'rotation': [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0], 'instanceMatricesFromFortran': [[1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0]], 'scissorH': 200, 'frontPolyMode': 'fill', 'blendFunctions': ('GL_SRC_ALPHA', 'GL_ONE_MINUS_SRC_ALPHA'), 'outline': (False, False), 'vertexArrayFlag': False, 'scissorX': 0, 'scissorY': 0, 'listed': True, 'inheritPointWidth': True, 'pickable': True, 'pointWidth': 2, 'scissorW': 200, 'needsRedoDpyListOnResize': False, 'stipplePolygons': False, 'pickableVertices': False, 'inheritMaterial': 0, 'depthMask': 1, 'inheritSharpColorBoundaries': True, 'scale': [1.0, 1.0, 1.0], 'lighting': True, 'inheritCulling': False, 'inheritShading': True, 'shading': 'smooth', 'translation': [0.0, 0.0, 0.0], 'transparent': False, 'sharpColorBoundaries': True, 'culling': 'none', 'name': 'balls', 'backPolyMode': 'line', 'inheritFrontPolyMode': True, 'inheritStipplePolygons': True, 'inheritBackPolyMode': False, 'scissor': 0, 'protected': True, 'inheritLineWidth': True, 'lineWidth': 2, 'inheritXform': 1}
        obj = mv.GUI.VIEWER.FindObjectByName('root|'+molName2+'|balls')
        if obj:
            apply(obj.Set, (), state)
    
        ## Material for balls
        if obj:
            from opengltk.OpenGL import GL
            state = {'opacity': [1.0], 'binding': [10, 10, 10, 10, 10, 10], 'shininess': [13.0], 'emission': [[0.0, 0.0, 0.0, 1.0]], 'specular': [[0.0, 0.0, 0.0, 1.0]], 'ambient': [[0.0, 0.0, 0.0, 1.0]], 'diffuse': [[0.0, 0.0, 0.0, 1.0]]}
            apply(obj.materials[GL.GL_BACK].Set, (), state)
    
            pass  ## needed in case there no modif
        ## End Materials for balls
    
        ## Clipping Planes for balls
        if obj:
            obj.clipP = []
            obj.clipPI = []
            pass  ## needed in case there no modif
        ## End Clipping Planes for balls
    
        ## Object root|1jff|MSMS-MOL
        state = {'scissorAspectRatio': 1.0, 'inheritStippleLines': True, 'stippleLines': False, 'disableStencil': False, 'replace': True, 'visible': 1, 'immediateRendering': False, 'inheritLighting': True, 'invertNormals': False, 'pivot': [0.0, 0.0, 0.0], 'rotation': [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0], 'instanceMatricesFromFortran': [[1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0]], 'scissorH': 200, 'frontPolyMode': 'fill', 'blendFunctions': ('GL_SRC_ALPHA', 'GL_ONE_MINUS_SRC_ALPHA'), 'outline': (False, False), 'vertexArrayFlag': False, 'scissorX': 0, 'scissorY': 0, 'listed': True, 'inheritPointWidth': True, 'pickable': True, 'pointWidth': 2, 'scissorW': 200, 'needsRedoDpyListOnResize': False, 'stipplePolygons': False, 'pickableVertices': True, 'inheritMaterial': 0, 'depthMask': 1, 'inheritSharpColorBoundaries': False, 'scale': [1.0, 1.0, 1.0], 'lighting': True, 'inheritCulling': False, 'inheritShading': True, 'shading': 'smooth', 'translation': [0.0, 0.0, 0.0], 'transparent': True, 'sharpColorBoundaries': False, 'culling': 'none', 'name': 'MSMS-MOL', 'backPolyMode': 'line', 'inheritFrontPolyMode': True, 'inheritStipplePolygons': True, 'inheritBackPolyMode': False, 'scissor': 0, 'protected': True, 'inheritLineWidth': True, 'lineWidth': 2, 'inheritXform': 1}
        obj = mv.GUI.VIEWER.FindObjectByName('root|'+molName1+'|MSMS-MOL')
        if obj:
            apply(obj.Set, (), state)
    
        ## Material for MSMS-MOL
        if obj:
            from opengltk.OpenGL import GL
            state = {'opacity': [0.78461539745330811], 'binding': [10, 10, 10, 10, 10, 10], 'shininess': [11.815384864807129], 'emission': [[0.0, 0.56111109256744385, 0.18885530531406403, 1.0]], 'specular': [[0.0, 0.66666668653488159, 0.22438254952430725, 1.0]], 'ambient': [[0.10000000149011612, 0.10000000149011612, 0.10000000149011612, 1.0]], 'diffuse': [[0.0, 0.60555553436279297, 0.20381413400173187, 0.78461539745330811]]}
            obj.materials[GL.GL_FRONT].Set(**state)
            obj._setTransparent('implicit')
            
            from opengltk.OpenGL import GL
            state = {'opacity': [1.0], 'binding': [10, 10, 10, 10, 10, 10], 'shininess': [13.0], 'emission': [[0.0, 0.18888889253139496, 0.037533920258283615, 1.0]], 'specular': [[0.0, 0.0, 0.0, 1.0]], 'ambient': [[0.0, 0.0, 0.0, 1.0]], 'diffuse': [[0.0, 0.21111111342906952, 0.041949696838855743, 1.0]]}
            apply(obj.materials[GL.GL_BACK].Set, (), state)
    
        ## End Materials for MSMS-MOL
    
        ## Clipping Planes for MSMS-MOL
        if obj:
            obj.clipP = []
            obj.clipPI = []
            pass  ## needed in case there no modif
        ## End Clipping Planes for MSMS-MOL
    
        ## Object root|1jff|secondarystructure
        state = {'scissorAspectRatio': 1.0, 'inheritStippleLines': True, 'stippleLines': False, 'disableStencil': False, 'replace': True, 'visible': True, 'immediateRendering': False, 'inheritLighting': True, 'invertNormals': False, 'pivot': [0.0, 0.0, 0.0], 'rotation': [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0], 'instanceMatricesFromFortran': [[1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0]], 'scissorH': 200, 'frontPolyMode': 'fill', 'blendFunctions': ('GL_SRC_ALPHA', 'GL_ONE_MINUS_SRC_ALPHA'), 'outline': (False, False), 'vertexArrayFlag': False, 'scissorX': 0, 'scissorY': 0, 'listed': True, 'inheritPointWidth': True, 'pickable': True, 'pointWidth': 2, 'scissorW': 200, 'needsRedoDpyListOnResize': False, 'stipplePolygons': False, 'pickableVertices': False, 'inheritMaterial': 0, 'depthMask': 1, 'inheritSharpColorBoundaries': True, 'scale': [1.0, 1.0, 1.0], 'lighting': True, 'inheritCulling': False, 'inheritShading': True, 'shading': 'smooth', 'translation': [0.0, 0.0, 0.0], 'transparent': False, 'sharpColorBoundaries': True, 'culling': 'none', 'name': 'secondarystructure', 'backPolyMode': 'line', 'inheritFrontPolyMode': True, 'inheritStipplePolygons': True, 'inheritBackPolyMode': False, 'scissor': 0, 'protected': True, 'inheritLineWidth': True, 'lineWidth': 2, 'inheritXform': 1}
        obj = mv.GUI.VIEWER.FindObjectByName('root|'+molName1+'|secondarystructure')
        if obj:
            apply(obj.Set, (), state)
    
        ## Material for secondarystructure
        if obj:
            from opengltk.OpenGL import GL
            state = {'opacity': [1.0], 'binding': [10, 10, 10, 10, 10, 10], 'shininess': [13.0], 'emission': [[0.0, 0.0, 0.0, 1.0]], 'specular': [[0.0, 0.0, 0.0, 1.0]], 'ambient': [[0.10000000149011612, 0.10000000149011612, 0.10000000149011612, 1.0]], 'diffuse': [[0.65363794565200806, 0.83888888359069824, 0.0, 1.0]]}
            apply(obj.materials[GL.GL_FRONT].Set, (), state)
    
            from opengltk.OpenGL import GL
            state = {'opacity': [1.0], 'binding': [10, 10, 10, 10, 10, 10], 'shininess': [13.0], 'emission': [[0.0, 0.0, 0.0, 1.0]], 'specular': [[0.0, 0.0, 0.0, 1.0]], 'ambient': [[0.0, 0.0, 0.0, 1.0]], 'diffuse': [[0.0, 0.0, 0.0, 1.0]]}
            apply(obj.materials[GL.GL_BACK].Set, (), state)
    
            pass  ## needed in case there no modif
        ## End Materials for secondarystructure
    
        ## Clipping Planes for secondarystructure
        if obj:
            obj.clipP = []
            obj.clipPI = []
            pass  ## needed in case there no modif
        ## End Clipping Planes for secondarystructure

    mv.getMolFromName(molName1).geomContainer.geoms['MSMS-MOL'].sortPoly()
