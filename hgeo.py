import os
import sys
import json

"""
HGeo
Simple conversion of Houdini's GEO ascii file format into
an OBJ file.
I use this with Apprentice Houdini to "Save geometry..." and then
I drag'n'drop that GEO file on to this python script.
It will create an OBJ with the same base name in the same folder.
The stdout and stderr are saved on the desktop.
"""


class Polygon(object):

    def __init__(self,indices,closed=False):
        self.indicies = indices
        self.closed   = closed


class HGeo(object):

    def __init__(self,filePath=None):
        self.filePath = filePath
        self.points = list()
        self.normals = list()
        self.uvs = list()
        self.polys = list()
        if filePath is not None:
            self.read(filePath)


    @staticmethod
    def _pairListToDict(pairs):
        return dict( zip(pairs[0::2],pairs[1::2]) )


    def _faceIndex(self,i):
        v = str(self.pointrefs[i] + 1)
        vt = ""
        if self.haveUvs == "point":
            vt = str(self.pointrefs[i] + 1)
        elif self.haveUvs == "vertex":
            vt = str(i + 1)
        vn = ""
        if self.haveNormals == "point":
            vn = str(self.pointrefs[i] + 1)
        elif self.haveNormals == "vertex":
            vn = str(i + 1)
        if vn and vt:
            s = "%s/%s/%s" % (v,vt,vn)
        elif vn:
            s = "%s//%s" % (v,vn)
        elif vt:
            s = "%s/%s" % (v,vt)
        else:
            s = v
        return s


    def writeObj(self,objPath):
        assert objPath.endswith(".obj"), "must end in .obj"
        basepath = os.path.splitext(objPath)[0]
        basename = os.path.basename(basepath)
        with open(objPath,'w') as fp:
            fp.write("# %s.obj\n\n" % basename)
            #fp.write("mtllib %s.mtl\n" % basepath)
            #fp.write("usemtl %s\n" % basename)
            #fp.write("usemap %s.png\n" % basepath)
            fp.write("g %s\n" % basename)
            uvs = self.uvs.get(self.haveUvs,list())
            normals = self.normals.get(self.haveNormals,list())
            for v in self.points:
                fp.write("v %s %s %s\n" % tuple(v[:3]))
            for v in normals:
                fp.write("vn %s %s %s\n" % tuple(v[:3]))
            for v in uvs:
                fp.write("vt %s %s %s\n" % tuple(v[:3]))
            for p in self.polys:
                fp.write("f %s\n" % " ".join([self._faceIndex(i) for i in p.indicies ]))


    def read(self,filePath):
        self.filePath = filePath
        self.points = list()
        self.normals = dict(point=list(),vertex=list())
        self.uvs = dict(point=list(),vertex=list())
        self.haveNormals = ""
        self.haveUvs = ""
        self.polys = list()
        self.npts = 0
        self.nvtx = 0
        self.nplys = 0
        self.pointrefs = None

        with open(filename, 'r') as fp:
            self.rawgeo = json.load(fp)
            for name,item in zip(self.rawgeo[0::2],self.rawgeo[1::2]):
                if name == 'fileversion':
                    pass
                elif name == 'pointcount':
                    self.npts = item
                elif name == 'vertexcount':
                    self.nvtx = item
                elif name == 'primitivecount':
                    self.nplys = item
                elif name == 'info':
                    pass
                elif name == 'topology':
                    topology = HGeo._pairListToDict(item)
                    for topName, topItem in topology.items():
                        if topName == "pointref":
                            ptRef = HGeo._pairListToDict(topItem)
                            self.pointrefs = ptRef['indices']
                        else:
                            raise RuntimeError("unknon topology %s" % repr(topology))
                elif name == 'attributes':
                    for attrName,a in zip(item[0::2],item[1::2]):
                        if attrName in ( "vertexattributes", "pointattributes" ):
                            type_ = attrName.replace("attributes","")
                            pts = dict()
                            for pa in a:
                                desc, vals = pa
                                descDict = HGeo._pairListToDict(desc)
                                valDict = HGeo._pairListToDict(vals)
                                valuesDict = HGeo._pairListToDict(valDict['values'])
                                pts[ descDict['name'] ] = valuesDict['tuples']
                            for ptAttr, ptVal in pts.items():
                                if ptAttr == "P":
                                    self.points = ptVal
                                elif ptAttr == "uv":
                                    self.uvs[type_] = ptVal
                                    self.haveUvs = type_
                                elif ptAttr == "N":
                                    self.normals[type_] = ptVal
                                    self.haveNormals = type_
                                else:
                                    print "*** unknown point attribute %s" % ptAttr
                elif name == 'primitives':
                    for prim in item:
                        self._addPrim(prim)


    def _addPrim(self,prim):
        desc = HGeo._pairListToDict(prim[0])
        if desc['type'] == "Poly":
            data = HGeo._pairListToDict(prim[1])
            self.polys.append( Polygon(data['vertex'],data['closed']) )
        elif desc['type'] == "run" and desc["runtype"] == "Poly":
            if desc["varyingfields"] == ["vertex"] and desc["uniformfields"].keys() == ["closed"]:
                for vtx in prim[1]:
                    self.polys.append( Polygon(vtx[0],desc["uniformfields"]["closed"]) )
        else:
            raise RuntimeError("bad type %s" % repr(desc))



if __name__ == "__main__":
    import sys

    home    = ["HOME", "USERPROFILE"][sys.platform.startswith("win")]
    desktop = os.path.join(os.getenv(home), "Desktop")
    logfile = os.path.join(desktop, "templog.txt")
    errfile = os.path.join(desktop, "temperr.txt")

    filename = sys.argv[1]
    if len(sys.argv) > 2:
        objname = sys.argv[2]
    else:
        base, ext = os.path.splitext(filename)
        objname = "%s.obj" % base

    with open( errfile, 'a') as sys.stderr:
        with open( logfile, 'a') as sys.stdout:

            print "--- converting %s ----" % filename

            try:
                g = HGeo(filename)
                g.writeObj(objname)
            except StandardError, err:
                import traceback
                traceback.print_exc()
            else:
                print "--- done, output to %s ----" % objname

