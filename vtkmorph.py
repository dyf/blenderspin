import sys
import numpy as np
import vtk
import vtk.util.numpy_support


def preorder_traversal(root, compartments):
    nodestack = []
    nodelist = []

    node = root

    while True:
        nodelist.append(node)

        for childId in node['children']:
            child = compartments.get(childId, None)
            if child:
                nodestack.append(child)
            
        if len(nodestack) == 0:
            break
        else:
            node = nodestack.pop()
        
    return nodelist

def morphology_polydata(compartments, soma_compartment, color_fn, minRadius=0.0):
    points = vtk.vtkPoints()
    lines = vtk.vtkCellArray()

    radii = vtk.vtkDoubleArray()
    radii.SetNumberOfComponents(1)
    radii.SetName("radius")

    types = vtk.vtkUnsignedCharArray()
    types.SetNumberOfComponents(1)
    types.SetName("type")

    colors = vtk.vtkUnsignedCharArray()
    colors.SetNumberOfComponents(3)
    colors.SetName("colors")

    compartment_ids = vtk.vtkUnsignedIntArray()
    compartment_ids.SetNumberOfComponents(1)
    compartment_ids.SetName("compartment_id")

    pidmap = {}
    soma_pid = -1
    soma_radius = 0

    roots = [ c for c in compartments.values() if c['parent'] == -1 ]
    
    for ri, root in enumerate(roots):
        print "root", ri
        nodelist = preorder_traversal(root, compartments)

        line = []

        for node in nodelist:
            if len(line) == 0 and node['parent'] != -1:
                line.append(pidmap[node['parent']])

            pid = points.InsertNextPoint(node['x'], node['y'], node['z'])
                
            # keep track of the pid of the root node, as well as the radius of
            # one of its children.  We'll use that radius as a surrogate radius,
            # since dendrites don't actually have a cone shape
            if node == soma_compartment:
                soma_pid = pid
            if node['parent'] == soma_compartment['id']:
                soma_radius = node['radius']

            radii.InsertNextTuple1(max(node['radius'], minRadius))
            types.InsertNextTuple1(node['type'])

            color = color_fn(node)
            colors.InsertNextTuple3(color[0], color[1], color[2])
            compartment_ids.InsertNextTuple1(int(node['id']))

            pidmap[node['id']] = pid

            line.append(pid)
            if len(node['children']) == 0:
                lines.InsertNextCell(len(line))
                for i in line:
                    lines.InsertCellPoint(i)
                line = []

    for p in xrange(1,points.GetNumberOfPoints()):
        p1 = points.GetPoint(p-1)
        p2 = points.GetPoint(p)

    # assuming we found a root, update its radius
    if soma_radius > 0 and soma_pid >= 0:
        radii.SetTuple1(soma_pid, soma_radius)

    polyData = vtk.vtkPolyData()
    polyData.SetPoints(points)
    polyData.SetLines(lines)
    polyData.GetPointData().AddArray(radii)
    polyData.GetPointData().AddArray(types)
    polyData.GetPointData().AddArray(colors)
    polyData.GetPointData().AddArray(compartment_ids)
    polyData.GetPointData().SetActiveScalars("radius")

    return polyData

def generate_sphere(root, color):
    s = vtk.vtkSphereSource()
    s.SetRadius(root['radius'])
    s.SetCenter(root['x'], root['y'], root['z'])
    s.SetThetaResolution(32)
    s.SetPhiResolution(16)
    s.Update()

    pd = s.GetOutput()
    colors = vtk.vtkUnsignedCharArray()
    colors.SetNumberOfComponents(3)
    colors.SetName("colors")

    points = pd.GetPoints()
    for i in range(points.GetNumberOfPoints()):
        colors.InsertNextTuple3(color[0], color[1], color[2])

    pd.GetPointData().AddArray(colors)
    return pd

def generate_mesh(compartments, root_compartment, color_fn, sides=6, radius=None):
    tubepd = generate_tube(compartments, root_compartment, color_fn, sides=sides, radius=radius)
    spherepd = generate_sphere(root_compartment, color_fn(root_compartment))
    
    f = vtk.vtkAppendPolyData()
    f.AddInputData(tubepd)
    f.AddInputData(spherepd)
    f.Update()

    return f.GetOutput()

    
def generate_tube(compartments, root_compartment, color_fn, sides=6, radius=None):
    polyData = morphology_polydata(compartments, root_compartment, color_fn)

    cleanFilter = vtk.vtkCleanPolyData()
    cleanFilter.SetInputData(polyData)

    tubeFilter = vtk.vtkTubeFilter()
    tubeFilter.SetNumberOfSides(sides)
    tubeFilter.SidesShareVerticesOn()
    tubeFilter.SetInputConnection(cleanFilter.GetOutputPort())
    if radius is None:
        tubeFilter.SetVaryRadiusToVaryRadiusByAbsoluteScalar()
    else:
        tubeFilter.SetRadius(radius)
    tubeFilter.CappingOn()
    tubeFilter.Update()

    return tubeFilter.GetOutput()

# breaking down all of the strips in a vtk tube by type
def tube_to_numpy(pd):
    strips = vtk.util.numpy_support.vtk_to_numpy(pd.GetStrips().GetData())

    strips_by_type = {}

    types = vtk.util.numpy_support.vtk_to_numpy(pd.GetPointData().GetScalars("type"))
    points = vtk.util.numpy_support.vtk_to_numpy(pd.GetPoints().GetData())
    compartment_ids = vtk.util.numpy_support.vtk_to_numpy(pd.GetPointData().GetScalars("compartment_id"))
    normals = vtk.util.numpy_support.vtk_to_numpy(pd.GetPointData().GetNormals())

    def append_substrip(ptype, strip):
        if ptype not in strips_by_type:
           strips_by_type[ptype] = np.array(strip, dtype=np.uint32)
        else:
            type_strip = strips_by_type[ptype] 
            type_strip = np.append(type_strip, [type_strip[-1], strip[0]])
            strips_by_type[ptype] = np.append(type_strip, strip)

    # loop through each triangle strip ( n, p1, p2, p3, ..., n, p1, p2, p3, ... )
    offset = 0
    while offset < strips.size:
        npts = strips[offset]
        offset += 1
        
        strip = strips[offset:offset+npts]
        # classify each strip by the type of its last point
        strip_type = types[strip[-1]]

        append_substrip(strip_type, strip)

        offset += npts

    for k,v in strips_by_type.iteritems():
        strips_by_type[k] = v.astype(np.uint32)

    return {
        "points": points,
        "compartment_ids": compartment_ids,
        "normals": normals,
        "strips": strips_by_type,
        "types": types
    }

def write_vtk(pd, filename):
    w = vtk.vtkPolyDataWriter()
    w.SetFileName(filename)
    w.SetInputData(pd)
    w.Update()        

def write_ply(pd, filename):
    f = vtk.vtkTriangleFilter()
    f.SetInputData(pd)
    f.Update()
    
    w = vtk.vtkPLYWriter()
    w.SetFileName(filename)
    w.SetInputData(f.GetOutput())
    w.SetArrayName("colors")
    w.SetFileTypeToASCII()
    w.Update()        

    
