def RemoveDuplicatedVertices(vertices, faces, vnorms = None):
    """Remove duplicated vertices and re-index the polygonal faces such that
they share vertices
"""
    vl = {}
    vrl = {}
    nvert = 0
    vertList = []
    normList = []
    
        
    for i,v in enumerate(vertices):
        key = '%f%f%f'%tuple(v)
        if not vl.has_key(key):
            vl[key] = nvert
            vrl[i] = nvert
            nvert +=1
            vertList.append(v)
            if vnorms is not None:
                normList.append(vnorms[i])
        else:
            nind = vl[key]
            vrl[i] = nind
            if vnorms is not None:
                vn1 = normList[nind]
                vn2 = vnorms[i]
                normList[nind] = [(vn1[0] +vn2[0])/2,
                                   (vn1[1] +vn2[1])/2,
                                   (vn1[2] +vn2[2])/2 ]

    faceList = []
    for f in faces:
        faceList.append( map( lambda x, l=vrl: vrl[x],  f ) )
    if vnorms is not None:
        return vertList, faceList, normList
    return vertList, faceList

