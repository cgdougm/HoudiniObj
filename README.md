HoudiniObj
==========

Simple conversion of Houdini's GEO ascii file format into an OBJ file.

I use this with Apprentice Houdini to "Save geometry..." and then I drag'n'drop that GEO file on to this python script.

It will create an OBJ with the same base name in the same folder.

The stdout and stderr are saved on the desktop.

Usage:
      from HoudiniObj import HGeo
      g = HGeo(filename)
      g.writeObj(objname)

This is not intended to be the Right Way. It cannot handle many GEO files. 
But it works just fine for me when I have simple geometry I use for Octane rendering.

The geometry works best if you have UV and normals (I usually run a Facet SOP to post-compute normals.)

See http://instangram.com/raette for examples of Octane renders I've done with this tool.
