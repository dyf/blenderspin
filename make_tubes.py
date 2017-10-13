import sys, os, csv
import numpy as np
import allensdk.core.swc as swc
import vtkmorph
import xform
import math
import argparse

def read_csv(file_name):
    rows = []
    with open(file_name, 'rb') as f:
        r = csv.reader(f)
        rows = list(r)

    return { 
        int(r[1]): {
            'swc_file_name': r[0],
            'specimen_name': r[2],
            'transform': np.array([ [ float(r[4]),  float(r[5]),  float(r[6]),  float(r[13]) ],
                                    [ float(r[7]),  float(r[8]),  float(r[9]),  float(r[14]) ],
                                    [ float(r[10]), float(r[11]), float(r[12]), float(r[15]) ] ]),
            'up_down_ratio': float(r[40]),
            'cre_line': r[41]
            }
        for r in rows }

def make_transformed_morphology(morphology, transform, radius_scale=1.0):
    #morphology.sparsify(3)

    for comp in morphology.compartment_list:
        pos = np.array([comp['x'], comp['y'], comp['z'], 1.0])
        tpos = np.dot(transform, pos)

        #if tpos[2] > (11390.0 * 0.5):
        #    tpos[2] = 11390 - tpos[2]
            
        comp['x'] = tpos[0] / 1000.0
        comp['y'] = tpos[1] / 1000.0
        comp['z'] = tpos[2] / 1000.0
        comp['radius'] = comp['radius'] / 1000.0 * radius_scale

    return morphology


def color_by_category(specimens, key):
    colors = [ 
        [31, 119, 180],
        [255, 157, 14],
        [44, 160, 44],
        [214, 39, 40],
        [148, 103, 189],
        [140, 86, 75],
        [227, 119, 194],
        [127, 127, 127],
        [188, 189, 34],
        [23, 190, 207]
        ]
               
    categories = set( [ sp[key] for spid, sp in specimens.iteritems()] )

    return { cre_line: colors[i] for i, cre_line in enumerate(categories) }

def color_by_value(specimens, key):
    values = np.array([ sp[key] for spid, sp in specimens.iteritems() ])

    vmean = np.mean(values)
    vstd = np.std(values)

    vmin = max(vmean - 2 * vstd, np.min(values))
    vmax = min(vmean + 2 * vstd, np.max(values))

    #colors = [ [0, 64, 64, 128 ],
    #           [.3, 255, 0, 0],
    #           [.6, 255, 255, 0],
    #           [1.0, 255, 255, 255] ]

    colors = [ [ 0.0, 255, 0, 0 ],
               [ 0.66, 255, 255, 0 ],
               [ 1.0, 255, 255, 255 ] ]

    #colors = [ [0,0,0,255],
    #           [1.0, 255, 255, 255] ]

    #colors = [ [0.0, 255, 0, 255 ],
    #[0.5, 255, 255, 0],
    #[1.0, 0, 255, 255] ]
    
    def hotmap(v):
        t = (v - vmin) / (vmax - vmin)
        t = min(max(t, 0), 1)
        for i in xrange(3):
            if t >= colors[i][0] and t <= colors[i+1][0]:
                tt = (t - colors[i][0]) / (colors[i+1][0] - colors[i][0])
                
                return [ 
                    int(math.floor((1.0 - tt) * colors[i][1] + tt * colors[i+1][1])),
                    int(math.floor((1.0 - tt) * colors[i][2] + tt * colors[i+1][2])),
                    int(math.floor((1.0 - tt) * colors[i][3] + tt * colors[i+1][3]))
                    ]

        return None
    
    
    return hotmap

COLORS = {
    1: (160,160,160),
    2: (70, 130, 180), 
    3: (178, 34, 34),
    4: (255, 127, 80)
    }

def color_by_type(node):
    return COLORS[node['type']]


def fetch_cell(specimen_id):
    import allensdk.internal.core.lims_utilities as lu
    query = """
    select a3d.* from specimens sp
    join alignment3ds a3d on sp.alignment3d_id = a3d.id
    where sp.id = %d
    """

    a3d = lu.query(query % specimen_id)[0]
    m = np.array([ [ a3d['tvr_00'], a3d['tvr_01'], a3d['tvr_02'], a3d['tvr_09'] ],
                   [ a3d['tvr_03'], a3d['tvr_04'], a3d['tvr_05'], a3d['tvr_10'] ],
                   [ a3d['tvr_06'], a3d['tvr_07'], a3d['tvr_08'], a3d['tvr_11'] ],
                   [ 0, 0, 0, 1 ] ])

    query = """
    select wkf.storage_directory||wkf.filename as swc_file from well_known_files wkf
    join neuron_reconstructions nr on wkf.attachable_id = nr.id
    where nr.specimen_id = %d
    and nr.superseded = false
    and nr.manual = true
    and wkf.well_known_file_type_id = 303941301
"""
    swc_file = lu.query(query % specimen_id)[0]['swc_file']
    
    return swc_file, m
    

def main_human_pr():
    parser = argparse.ArgumentParser()
    parser.add_argument('--swc_file', default=None)
    parser.add_argument('--specimen_id', default=None, type=int)
    parser.add_argument('--output_dir', default='.')
    args = parser.parse_args()

    if args.specimen_id:
        swc_file, m0 = fetch_cell(args.specimen_id)
        morphology = swc.read_swc(swc_file)
        
        t0 = np.eye(4)
        t0[:,3] = -np.dot(m0, [ morphology.root['x'],
                                morphology.root['y'],
                                morphology.root['z'],
                                1 ])
        r = xform.rotate3x(math.radians(-90))
    else:
        swc_file = args.input_file
        morphology = swc.read_swc(swc_file)
        m0 = np.eye(4)
        t0 = xform.translate3(-morphology.root['x'], 
                              -morphology.root['y'], 
                              -morphology.root['z'])

        r = xform.rotate3x(math.radians(90))

    s = xform.scale3(1,1,3)
    
    m = np.dot(np.dot(r, np.dot(s, t0)), m0)
    
    morphology = make_transformed_morphology(morphology, m, 2)

    base,ext = os.path.splitext(os.path.basename(swc_file))
    print base
    
    tube_pd = vtkmorph.generate_mesh(morphology.compartment_index, morphology.root, color_by_type, 6, radius=None)
    vtkmorph.write_ply(tube_pd, os.path.join(args.output_dir, base + ".ply"))
    vtkmorph.write_vtk(tube_pd, os.path.join(args.output_dir, base + ".vtk"))

def main_specimen():
    from allensdk.core.cell_types_cache import CellTypesCache
    specimen_id = 485880739
    
    ctc = CellTypesCache()
    morphology = ctc.get_reconstruction(specimen_id)

    for c in morphology.compartment_list:
        c['z'] *= 3

    tube_pd = vtkmorph.generate_tube(morphology.compartment_index, morphology.root, color_by_type, 6, radius=1.5)
    vtkmorph.write_ply(tube_pd, '%d.ply' % specimen_id)
    vtkmorph.write_vtk(tube_pd, '%d.vtk' % specimen_id)
    
def main():    
    #ccf_file_name = 'ccf_alignments.csv'
    #upright_file_name = 'upright_alignments.csv'
    csv_file_name = sys.argv[1]
    output_dir = sys.argv[2]

    print "reading"
    specimens = read_csv(csv_file_name)
    
    cre_colors = color_by_category(specimens, 'cre_line')

    updown_colors = color_by_value(specimens, 'up_down_ratio')

    print "making morphologies"
    for specimen_id, specimen in specimens.iteritems():
        print specimen_id
        specimen['morphology'] = make_transformed_morphology(specimen['swc_file_name'], specimen['transform'])

    try:
        os.makedirs(output_dir)
    except Exception, e:
        print e
        pass

    print "making tubes"
    for specimen_id, specimen in specimens.iteritems():
        print specimen_id
        morphology = specimen['morphology']

        color = cre_colors[specimen['cre_line']]
        color = updown_colors(specimen['up_down_ratio'])
        if color is None:
            raise Exception("Uh oh!")

        tube_pd = vtkmorph.generate_tube(morphology.compartment_index, morphology.root, color, 6)
        vtkmorph.write_ply(tube_pd, os.path.join(output_dir,'%d.ply' % specimen_id))
        vtkmorph.write_vtk(tube_pd, os.path.join(output_dir,'%d.vtk' % specimen_id))


if __name__ == "__main__": main_human_pr()

    
