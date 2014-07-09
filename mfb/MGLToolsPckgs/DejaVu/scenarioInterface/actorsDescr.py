## Automatically adapted for numpy.oldnumeric Jul 23, 2007 by 

from DejaVu.Transformable import Transformable
from DejaVu.Displayable import Displayable
from DejaVu.Geom import Geom
from DejaVu.IndexedGeom import IndexedGeom
from DejaVu.Cylinders import Cylinders
from DejaVu.Light import Light
from DejaVu.Spheres import Spheres
from DejaVu.Clip import ClippingPlane
from DejaVu.Camera import Camera, Fog
from DejaVu.Materials import propertyNum

from opengltk.OpenGL import GL

from Scenario2.interpolators import VarVectorInterpolator, FloatVectorInterpolator,\
     IntScalarInterpolator, RotationInterpolator,\
     BooleanInterpolator, FloatVarScalarInterpolator, FloatScalarInterpolator
##     ReadDataInterpolator
from Scenario2.datatypes import FloatType, IntType, BoolType,IntVectorType,\
     FloatVectorType, IntVarType, FloatVarType, VarVectorType

from actor import DejaVuActor, DejaVuMaterialActor,  DejaVuScissorActor, \
     DejaVuClipZActor, DejaVuFogActor, DejaVuLightColorActor, \
     DejaVuSpheresRadiiActor, DejaVuRotationActor, DejaVuConcatRotationActor, \
     DejaVuGeomVisibilityActor, DejaVuTransformationActor, DejaVuGeomEnableClipPlaneActor, DejaVuCameraActor

from mglutil.gui.BasicWidgets.Tk.thumbwheel import ThumbWheel
from DejaVu.states import getRendering, setRendering, setObjectRendering
import numpy.oldnumeric as Numeric
id4x4 = Numeric.identity(4).astype('f')
from numpy import copy

actorsDescr = {

    Transformable: {
        'rotation': {
            'actor': (DejaVuRotationActor, (), {})
             } ,

        'concatRotation': {
            'actor': (DejaVuConcatRotationActor, (), {})
             } ,

    
        'translation': {
            'actor': (DejaVuActor, (), {'interp':FloatVectorInterpolator,
                                        #'setMethod': '_setTranslation',
                                        'datatype': FloatVectorType} )
            },
        'scale': {
            'actor': (DejaVuActor, (), {'interp':FloatVectorInterpolator,
                                        #'setMethod': '_setScale',
                                        'datatype': FloatVectorType} )
            },
        'pivot': {
            'actor': (DejaVuActor, (), {'interp': FloatVectorInterpolator,
                                        #'setMethod': '_setPivot',
                                        'datatype': FloatVectorType} )
            },
        'transformation':{
            'actor': (DejaVuTransformationActor, (), {})
             } ,
        },
    

   Displayable: {
        'colors':{
            'actor': (DejaVuActor, (),
              {
                'setFunction':\
                #lambda actor, value: actor.object.Set(materials=value, inheritMaterial=0),
                lambda actor, value: actor.object.Set(materials=value, redo=1, tagModified=False,
                                                      transparent='implicit', inheritMaterial=0),
                'getFunction':(lambda x,y: copy(x.materials[y].prop[1][:, :3]), (GL.GL_FRONT,), {}),
                'interp': VarVectorInterpolator,
                'datatype':VarVectorType
               },
                      ),
                 },
        'colorsB':{
            'actor': (DejaVuActor, (),
              {
                'setFunction':\
                #lambda actor, value: actor.object.Set(materials=value, inheritMaterial=0),
                lambda actor, value: actor.object.Set(materials=value, redo=1,
                                                      tagModified=False, polyFace = GL.GL_BACK,
                                                      transparent='implicit', inheritMaterial=0),
                'getFunction':(lambda x,y: copy(x.materials[y].prop[1][:, :3]), (GL.GL_BACK,), {}),
                'interp': VarVectorInterpolator,
                'datatype':VarVectorType
               },
                      ),
                 },
        'lineWidth': {
        'actor': (DejaVuActor, (),
                  {'setFunction': \
               lambda actor, value: actor.object.Set(lineWidth=value, inheritLineWidth=0),
                   'interp': IntScalarInterpolator, 'datatype':IntType})
                     },
        
        'pointWidth': {
              'actor': (DejaVuActor, (),
                        {'setFunction': \
               lambda actor, value: actor.object.Set(pointWidth=value, inheritPointWidth=0),
                         'interp': IntScalarInterpolator, 'datatype':IntType})
              },
        
        'rendering': {
              'actor': (DejaVuActor, (),
                        {'getFunction': lambda object: getRendering(object.viewer,checkAnimatable=True).get(object.fullName, None),
                         'setFunction': lambda actor, value: setObjectRendering(actor.object.viewer, actor.object, value)})
              },
    
        },
    
    Geom:  {
       'material': {
            'actor': (DejaVuMaterialActor, (), {} ),

            },
        'opacity': {
            'actor': (DejaVuActor, (),
              {'setFunction': \
               lambda actor, value: actor.object.Set(opacity=value, transparent='implicit', polyFace=GL.GL_FRONT_AND_BACK,
                                                     inheritMaterial=0),
               'getFunction':(
                   lambda x,y: x.materials[y].prop[propertyNum['opacity']], (GL.GL_FRONT,), {}
                             ),
               'interp': FloatVarScalarInterpolator,
               'datatype': FloatVarType
               }
                      ),
                  },
       'opacityF': {
            'actor': (DejaVuActor, (),
              {'setFunction': \
               lambda actor, value: actor.object.Set(opacity=value, transparent='implicit',
                                                     polyFace=GL.GL_FRONT,
                                                     inheritMaterial=0),
               'getFunction':(
                   lambda x,y: x.materials[y].prop[propertyNum['opacity']], (GL.GL_FRONT,), {}
                             ),
               'interp': FloatVarScalarInterpolator,
               'datatype': FloatVarType
               }
                      ),
                  },
        'opacityB': {
            'actor': (DejaVuActor, (),
              {'setFunction': \
               lambda actor, value: actor.object.Set(opacity=value, transparent='implicit',
                                                     polyFace=GL.GL_BACK,
                                                     inheritMaterial=0),
               'getFunction':(
                   lambda x,y: x.materials[y].prop[propertyNum['opacity']], (GL.GL_BACK,), {}
                             ),
               'interp': FloatVarScalarInterpolator,
               'datatype': FloatVarType
               }
                      ),
                  },
       
        'visible': {
            'actor': (DejaVuGeomVisibilityActor, (),
                      {'interp': BooleanInterpolator, 'datatype': BoolType})
            },
        
        'depthMask': {
            'actor': (DejaVuActor, (),
                      {'interp': BooleanInterpolator, 'datatype': BoolType})
            },
        
        'scissor': {
              'actor': (DejaVuActor, (), {'interp': BooleanInterpolator, 'datatype': BoolType})
                     }, # turns the scissor on/off.
        
        'scissorResize': {
              'actor': ( DejaVuScissorActor, (), {}),             
              },
       
        'xyz':{
            'actor': (DejaVuActor, (),
              {
                'setFunction': lambda actor, value: actor.object.Set(vertices=value),
                'getFunction':(lambda obj: obj.vertexSet.vertices.array, (), {}),
                'interp': VarVectorInterpolator,
                'datatype':VarVectorType
               },
                      ),
           },

        'clipEnable': {
              'actor': (DejaVuGeomEnableClipPlaneActor, (), {}),
              },

##        'function':{
##     'actor':(DejaVuActor, (), {'setFunction': None, 'getFunction': None,
##                                'interp':ReadDataInterpolator, 'datatype': None})  
##                   }

        },

    IndexedGeom:  {
     'faces':{
            'actor': (DejaVuActor, (),
              {
                'setFunction': lambda actor, value: actor.object.Set(faces=value),
                'getFunction':(lambda obj: obj.faceSet.faces.array, (), {}),
                'interp': VarVectorInterpolator,
                'datatype':VarVectorType
               },),
           },

     'vertface':{
            'actor': (DejaVuActor, (),
              {
                'setFunction': lambda actor, value: actor.object.Set(vertices=value[0], faces=value[1]),
                'getFunction':(lambda obj: [obj.vertexSet.vertices.array, obj.faceSet.faces.array], (), {}),
               },),
           },
     
        },


        Spheres: {
        'radii':   {
             'actor': (DejaVuSpheresRadiiActor, (), {}),
                    },
        'quality':   {
             'actor': (DejaVuActor, (),
                       {
                        'setFunction': lambda actor, value: actor.object.Set(quality=value),
                        'interp': IntScalarInterpolator, 'datatype':IntType
                       }),
                    },
        'vertices':{
                     'actor': (DejaVuActor, (), 
                {'setFunction': lambda actor, value: actor.object.Set(vertices=value),
                 'getFunction':(lambda obj: obj.vertexSet.vertices.array, (), {}) } ),
                    }
         },

        Cylinders: {
         'radii':   {
             'actor': (DejaVuActor, (),
                       {'setFunction': lambda actor, value: actor.object.Set(radii=list(value)),
                        'getFunction':(lambda obj: obj.vertexSet.radii.array, (), {}),
                        'interp': FloatVectorInterpolator,
                        'datatype': FloatVectorType} 
                       ),
                    },
         'quality':   {
             'actor': (DejaVuActor, (),
                       {
                        'setFunction': lambda actor, value: actor.object.Set(quality=value),
                        'interp': IntScalarInterpolator, 'datatype':IntType
                       }),
                    },
        'vertices':{
                     'actor': (DejaVuActor, (), 
                {'setFunction': lambda actor, value: actor.object.Set(vertices=value),
                 'getFunction':(lambda obj: obj.vertexSet.vertices.array, (), {}) } ),
                    }         
          },

        Fog:{
##           'start': {
##             'actor': (DejaVuActor, (),
##                       {
##                           'getFunction':(getattr, ('start',), {}),
##                           'interp': FloatScalarInterpolator,
##                           'datatype': FloatType
##                           },
##                       ),
##             },
##           'end': {
##             'actor': (DejaVuActor, (),
##                       {
##                           'getFunction':(getattr, ('end',), {}),
##                           'interp': FloatScalarInterpolator,
##                           'datatype': FloatType
##                           },
##                       ),
##             },
             'start': {'actor': (DejaVuFogActor, (), {'attr':'start'},)},
             'end': {'actor': (DejaVuFogActor, (), {'attr':'end'},) },
    
        },
    
        Camera:{
         'clipZ':{
             'actor': (DejaVuClipZActor, (), {} ),
                       },
         
         'backgroundColor': {
              'actor': (DejaVuCameraActor, (),
                         #(lambda c, value: c.Set(color=value),  ),
               {'setFunction': lambda actor, value: (actor.object.Set(color=value), actor.object.fog.Set(color=value)),  #,actor.object.Redraw()),
                        
                'getFunction':(getattr, ('backgroundColor',), {}),
                'interp': FloatVectorInterpolator,
                'datatype': FloatVectorType
                },
                        ),
              
              },

         'fieldOfView': {
              'actor': (DejaVuCameraActor, (),
                        {'setMethod': '_setFov',
                        'getFunction':(getattr, ('fovy',), {}),
                        'interp': FloatScalarInterpolator,
                        'datatype': FloatType
                         },
                        ),
              
              },
          'near': {
              'actor': (DejaVuCameraActor, (),
                        {
                        'getFunction':(getattr, ('near',), {}),
                        'interp': FloatScalarInterpolator,
                        'datatype': FloatType
                         },
                        ),
              
              },
         'far': {
              'actor': (DejaVuCameraActor, (),
                        {
                        'getFunction':(getattr, ('far',), {}),
                        'interp': FloatScalarInterpolator,
                        'datatype': FloatType
                         },
                        ),
              
              },
          'width': {
              'actor': (DejaVuCameraActor, (),
                        {
                        'getFunction':(getattr, ('width',), {}),
                        'interp': IntScalarInterpolator,
                        'datatype': IntType
                         },
                        ),
              
              },
         'heigt': {
              'actor': (DejaVuCameraActor, (),
                        {
                        'getFunction':(getattr, ('heigt',), {}),
                        'interp': IntScalarInterpolator,
                        'datatype': IntType
                         },
                        ),
              
              },
         'antialiased': {
              'actor': (DejaVuCameraActor, (),
                        {
                        'getFunction':(getattr, ('antiAliased',), {}),
                        'interp': IntScalarInterpolator,
                        'datatype': IntType
                         },
                        ),
              
              },
         'boundingbox':   {
             'actor': (DejaVuCameraActor, (),
                       {
                        'interp': IntScalarInterpolator,
                        'getFunction':(getattr, ('drawBB',), {}),
                        'datatype':IntType
                       }),
                    },
         'projectionType': {
            'actor': (DejaVuCameraActor, (),
                      {'interp': BooleanInterpolator, 'datatype': BoolType})
            },
         'drawThumbnail': {
            'actor': (DejaVuCameraActor, (),
                      {'interp': BooleanInterpolator, 'datatype': BoolType})
            },
         'contours': {
            'actor': (DejaVuCameraActor, (),
                      {'interp': BooleanInterpolator,
                       'getFunction':(getattr, ('drawThumbnailFlag',), {}),
                       'datatype': BoolType})
            },
         
         'lookFrom': {
              'actor': (DejaVuCameraActor, (),
                        {'setMethod': '_setLookFrom',
                         'getFunction':(getattr, ('lookFrom',), {}),
                         'interp':FloatVectorInterpolator,
                         'datatype': FloatVectorType} )
              },
         'lookAt': {
              'actor': (DejaVuCameraActor, (),
                        {'getFunction':(getattr, ('lookAt',), {}),
                         'interp':FloatVectorInterpolator,
                         'datatype': FloatVectorType} )
              },
         
         }, 
    
        ClippingPlane: {
            'visible': {
              'actor': (DejaVuActor, (), {'interp': BooleanInterpolator, 'datatype': BoolType
                                          })
                     },
            'color': {
              'actor': (DejaVuActor, (), {'interp': FloatVectorInterpolator,
                                          'datatype': FloatVectorType 
                                          })
    
                            },
            },

    Light: {
        'visible': {
              'actor': (DejaVuActor, (), {'interp': BooleanInterpolator, 'datatype': BoolType
                                          })
                     },

        'color': {
               'actor':(DejaVuLightColorActor, (), {}),
               },
          
    'direction': { 'actor': (DejaVuActor, (), {'interp': FloatVectorInterpolator,
                                               'datatype': FloatVectorType} )
                   }
        }
    }

