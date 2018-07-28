import vtk
import os
import requests
import numpy as np

DATA_SET_IDS = [100140756,100141219,112162251,114292355,158435116,272916915,127138787,100141454,100141563,180073473,126861679,174361040,272737914,100149969,127866392,139426984,272697944,180673746,113887868,157711748,115958825]

def download(data_set_id):
    res = requests.post("http://datacube.brain-map.org/call",
                        json={'procedure': 'org.brain_map.locator.get_lines',
                              'kwargs': { 'id': did }})

    data = res.json()['args'][0]

    lines = [ np.array([ [v['x'], v['y'], v['z'], v['density']]
                        for v in d ])
              for d in data['lines'] ]

    ijs = np.array([ [d['x'], d['y'], d['z']]
                     for d in data['injection_sites'] ])

    return { 'lines': lines,
             'injection_sites': ijs }


def save_npz(data_set_ids, base_dir='.'):
    for did in data_set_ids:
        data = download(did)

        print(did)
        np.savez(os.path.join(base_dir, "%d_conn.npz" % did), **data)

def load_npz(data_set_ids, base_dir='.'):
    for did in data_set_ids:
        yield did, np.load(os.path.join(base_dir, "%d_conn.npz" % did) )

def build_vtk(lines):
    vtkpoints = vtk.vtkPoints()
    vtklines = vtk.vtkCellArray()

    vtkradii = vtk.vtkDoubleArray()
    vtkradii.SetNumberOfComponents(1)
    vtkradii.SetName("radius")

    for line in lines:
        line_pids = []
        for v in line:
            pid = vtkpoints.InsertNextPoint(v[0], v[1], v[2])
                
            vtkradii.InsertNextTuple1(v[3])

            line_pids.append(pid)

        vtklines.InsertNextCell(len(line_pids))
        for pid in line_pids:
            vtklines.InsertCellPoint(pid)

    polyData = vtk.vtkPolyData()
    polyData.SetPoints(vtkpoints)
    polyData.SetLines(vtklines)
    polyData.GetPointData().AddArray(vtkradii)
    polyData.GetPointData().SetActiveScalars("radius")

    return polyData

def generate_tube(polyData, sides=6, radius=None):
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

if __name__ == "__main__":
    base_dir = 'conn'
    for did, data in load_npz(DATA_SET_IDS, base_dir=base_dir):
        print(did)
        pd = build_vtk(data['lines'])
        tpd = generate_tube(pd)
        write_ply(tpd, os.path.join(base_dir, "%d.ply" % did))
