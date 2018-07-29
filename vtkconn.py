import vtk
import os
import requests
import numpy as np
import allensdk.core.json_utilities as ju

DATA_SET_IDS = [100140756,100141219,112162251,114292355,158435116,272916915,127138787,100141454,100141563,180073473,126861679,174361040,272737914,100149969,127866392,139426984,272697944,180673746,113887868,157711748,115958825]
CENTER = [ 6600.0, 4000.0, 5700.0 ]
COLORS = { 100140756:(206,4,9),
           100141219:(0,112,192),
           112162251:(255,204,0),
           114292355:(0,204,0),
           158435116:(125,26,142),
           272916915:(68,2,166),
           127138787:(0,0,204),
           100141454:(253,119,129),
           100141563:(244,238,0),
           180073473:(0,138,135),
           126861679:(153,0,255),
           174361040:(51,51,153),
           272737914:(102,0,51),
           100149969:(187,102,17),
           127866392:(139,188,0),
           139426984:(204,51,153),
           272697944:(255,99,21),
           180673746:(165,0,33),
           113887868:(51,51,255),
           157711748:(192,0,0),
           115958825:(0,210,205)
}

def download(data_set_id):
    res = requests.post("http://datacube.brain-map.org/call",
                        json={'procedure': 'org.brain_map.locator.get_lines',
                              'kwargs': { 'id': data_set_id }})

    data = res.json()['args'][0]

    lines = [ np.array([ [v['x'], v['y'], v['z'], v['density']]
                        for v in d ])
              for d in data['lines'] ]

    ijs = np.array([ [d['x'], d['y'], d['z'] ]
                     for d in data['injection_sites'] ])

    scale = 1e-3
    
    for line in lines:
        line[:,:3] = (line[:,:3] - CENTER) * scale

    ijs = (ijs - CENTER) * scale

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

def generate_lines(lines, color):
    vtkpoints = vtk.vtkPoints()
    vtklines = vtk.vtkCellArray()

    vtkradii = vtk.vtkDoubleArray()
    vtkradii.SetNumberOfComponents(1)
    vtkradii.SetName("radius")

    colors = vtk.vtkUnsignedCharArray()
    colors.SetNumberOfComponents(3)
    colors.SetName("colors")

    for line in lines:
        line_pids = []
        for v in line:
            pid = vtkpoints.InsertNextPoint(v[0], v[1], v[2])
                
            vtkradii.InsertNextTuple1(v[3])
            colors.InsertNextTuple3(color[0], color[1], color[2])
            
            line_pids.append(pid)

        vtklines.InsertNextCell(len(line_pids))
        for pid in line_pids:
            vtklines.InsertCellPoint(pid)

    polyData = vtk.vtkPolyData()
    polyData.SetPoints(vtkpoints)
    polyData.SetLines(vtklines)
    polyData.GetPointData().AddArray(vtkradii)
    polyData.GetPointData().AddArray(colors)
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

def generate_sphere(pos, radius, color):
    s = vtk.vtkSphereSource()
    s.SetRadius(radius)
    s.SetCenter(pos[0], pos[1], pos[2])
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

def generate_mesh(lines, sphere_pos, color, line_radius=0.01, sphere_radius=0.1):
    pd = generate_lines(lines, color)
    tpd = generate_tube(pd, radius=line_radius)
    spd = generate_sphere(sphere_pos, sphere_radius, color)
    
    f = vtk.vtkAppendPolyData()
    f.AddInputData(tpd)
    f.AddInputData(spd)
    f.Update()

    return f.GetOutput()

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
    injections_file = os.path.join(base_dir, "experiments.json")

    #save_npz(DATA_SET_IDS, base_dir=base_dir)

    #r = requests.get("http://api.brain-map.org/api/v2/data/ApiConnectivity/query.json?num_rows=3000")
    #d = r.json()
    #ju.write(injections_file, d['msg'])
    
    injection_voxels = ju.read(injections_file)
    injection_voxels = { d['data_set_id']: [ (d['injection_x']-CENTER[0])*1e-3,
                                             (d['injection_y']-CENTER[1])*1e-3,
                                             (d['injection_z']-CENTER[2])*1e-3 ] for d in injection_voxels }
    
    for did, data in load_npz(DATA_SET_IDS, base_dir=base_dir):
        print(did)

        injection_voxel = data['injection_sites'].mean(axis=0)
        v = data['injection_sites'].shape[0]
        r_vox = np.power(3.0/4.0 * v / np.pi, 1.0/3.0)
        r = r_vox * 1e2 * 1e-3

        color = np.array(COLORS[did])
        
        pd = generate_mesh(data['lines'], injection_voxel,
                           color=color, line_radius=0.01, sphere_radius=r)
        write_ply(pd, os.path.join(base_dir, "%d.ply" % did))
