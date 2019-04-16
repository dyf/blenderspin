import pandas as pd
import vtk

file_name = "ephys_cells.csv"

df = pd.read_csv(file_name)

append = vtk.vtkAppendPolyData()
writer = vtk.vtkPLYWriter()

for i,row in df.iterrows():
    print(i)
    s = vtk.vtkSphereSource()
    s.SetRadius(0.1)
    s.SetCenter(row['y'], row['x'], row['z'])
    s.SetThetaResolution(16)
    s.SetPhiResolution(8)
    s.Update()

    pd = s.GetOutput()
    colors = vtk.vtkUnsignedCharArray()
    colors.SetNumberOfComponents(3)
    colors.SetName("colors")

    points = pd.GetPoints()
    for i in range(points.GetNumberOfPoints()):
        colors.InsertNextTuple3(row['r']*255, row['g']*255, row['b']*255)

    pd.GetPointData().AddArray(colors)
    
    append.AddInputData(pd)

append.Update()

writer.SetFileName("geo.ply")
writer.SetArrayName("colors")
writer.SetFileTypeToASCII()

writer.SetInputConnection(append.GetOutputPort())
writer.Write()

