import hou
from ast import literal_eval
from collections import OrderedDict
import datetime
import re


def get_info(node):
    """ Returns notable info about the node in a dictionary.
    Args:
        node (hou.Node): Node to operate on.

    Returns:
        dict: Info
    """
    # get general info
    sop_info_tree = node.infoTree().branches()['SOP Info']
    sop_dict = dict()
    for info_type, info in sop_info_tree.rows():
        sop_dict[info_type] = info

    for tree_name, info_tree in sop_info_tree.branches().items():
        sop_dict[tree_name] = info_tree.rows()

    return sop_dict


def _eval(val):
    if val is not None:
        if isinstance(val, basestring):
            if val == 'Yes':
                return True
            elif val == 'No':
                return False
            else:
                try:
                    return literal_eval(val)
                except:
                    return val
        else:
            return eval(''.join(val))


def _hv2(val):
    if val is not None:
        return hou.Vector2(_eval(val))


def _hv3(val):
    if val is not None:
        return hou.Vector3(_eval(val))


def _seconds(val):
    val, unit = val.split()
    val = _eval(val)
    if unit == 'ms':
        val *= 0.01
    return val


def _megabytes(val):
    val, unit, instanced = val.split()
    val = _eval(val)
    if unit == 'KB':
        val *= 0.001
    return val


def _date(val):
    val = _eval(val)
    date = datetime.datetime.strptime(val, '%d %b %Y %I:%M %p')
    # TODO timezone???
    return date


def _to_dict(info_tree, branch):
    return {k: v for k, v in info_tree.branches()[branch].rows()}


def _to_attrib(info_tree, branch):
    attribs = info_tree.branches()[branch].rows()
    d = []
    for name, size, attr_type, sub_type, vector_type, n_unique, _ in attribs:
        _info = []

        # handle size
        size = int(size)
        if size > 1:
            size = str(size)
        else:
            size = ''

        # handle attr type
        attr_type = attr_type.replace('Integer', 'int')
        attr_type = attr_type.replace('Float', 'flt')
        attr_type = attr_type.replace('String', 'str')
        attr_type = attr_type.replace('Vector', 'flt')
        attr_type = attr_type.replace('Array', '[]')
        # print repr(attr_type),
        # remove precision
        attr_type = re.sub(r'\([\w-]+\)', r'', attr_type)
        attr_type = attr_type.replace(' ', '')
        # print repr(attr_type)
        attr_type = '{}{}'.format(size, attr_type.strip())
        _info.append(attr_type)

        # handle vector type
        if vector_type:
            vector_type = vector_type.replace('Vector', 'Vec')
            vector_type = vector_type.replace('Position', 'Pos')
            vector_type = vector_type.replace('Normal', 'Nml')
            vector_type = vector_type.replace('Color', 'Clr')
            vector_type = vector_type.replace('Transform Matrix', 'Matrix')
            vector_type = vector_type.replace('Texture Coord', 'Tex')
            vector_type = vector_type.replace('Non-arithmetic', '')
            if vector_type:
                vector_type = '({})'.format(vector_type.strip())
                _info.append(vector_type)

        # handle unique
        if n_unique:
            n_unique = '({} unique)'.format(n_unique.strip())
            _info.append(n_unique)

        d.append('{} {}'.format(name, ' '.join(_info)))

    return tuple(sorted(d))


def _to_vol(info_tree, branch):
    vols = info_tree.branches()[branch].rows()
    d = dict()
    print vols
    for prim_num, name, voxel_size, res, voxel_count, vol_type in vols:
        d[int(prim_num)] = (name,
                            literal_eval(res),
                            'Voxels: {}'.format(voxel_count),
                            'Voxel Size: {}'.format(voxel_size))

    return tuple([d[x] for x in sorted(d.keys())])


def _to_sparse(info_tree, branch):
    vols = info_tree.branches()[branch].rows()
    d = dict()
    print vols
    for prim_num, name, vol_type, data_type, voxel_size, res, voxel_count, banding_size, vol_hint, _, _ in vols:
        d[int(prim_num)] = (name,
                            literal_eval(res),
                            '{} Voxels: {}'.format(data_type, voxel_count),
                            'Voxel Size: {}'.format(voxel_size))

    return tuple([d[x] for x in sorted(d.keys())])


class SopInfo(object):
    """ Get sop info.
    """
    def __init__(self, node):
        """ Initialize node.
        Args:
            node: node to work on.
        """
        if not isinstance(node, hou.SopNode):
            raise TypeError('Node must be SOP type.')

        self.node = node

    @property
    def bb_center(self):
        sop_info = _to_dict(self.node.infoTree(), 'SOP Info')
        return _hv3(sop_info.get('Center'))

    @property
    def bb_minimum(self):
        sop_info = _to_dict(self.node.infoTree(), 'SOP Info')
        return _hv3(sop_info.get('Minimum'))

    @property
    def bb_maximum(self):
        sop_info = _to_dict(self.node.infoTree(), 'SOP Info')
        return _hv3(sop_info.get('Maximum'))

    @property
    def memory(self):
        sop_info = _to_dict(self.node.infoTree(), 'SOP Info')
        return _eval(sop_info.get('Memory'))

    @property
    def contained_nodes(self):
        general_info = _to_dict(self.node.infoTree(), 'General Info')
        return _eval(general_info.get('Contained Nodes'))

    @property
    def synchronized_with_definition(self):
        general_info = _to_dict(self.node.infoTree(), 'General Info')
        return _eval(general_info.get('Synchronized with Definition'))

    @property
    def last_cook_time(self):
        general_info = _to_dict(self.node.infoTree(), 'General Info')
        return _seconds(_eval(general_info.get('Last Cook Time')))

    @property
    def total_cooks(self):
        general_info = _to_dict(self.node.infoTree(), 'General Info')
        return _eval(general_info.get('Total Cooks'))

    @property
    def created_time(self):
        general_info = _to_dict(self.node.infoTree(), 'General Info')
        return _date(_eval(general_info.get('Created Time')))

    @property
    def modified_time(self):
        general_info = _to_dict(self.node.infoTree(), 'General Info')
        return _date(_eval(general_info.get('Modified Time')))

    @property
    def version(self):
        operator_info = _to_dict(self.node.infoTree().branches()['General Info'], 'Operator Info')
        return _eval(operator_info.get('Version'))

    @property
    def defined_by(self):
        script_operator_info = _to_dict(self.node.infoTree().branches()['General Info'], 'Script Operator Info')
        return _eval(script_operator_info.get('Defined By'))

    @property
    def time_dependent(self):
        dependency_info = _to_dict(self.node.infoTree(), 'Dependency')
        return _eval(dependency_info.get('Time Dependent'))

    @property
    def subnetwork_outputs(self):
        try:
            subnetwork_output_info = _to_dict(self.node.infoTree(), 'Subnetwork SOP Info')
        except KeyError:
            return ()
        raw_paths = [subnetwork_output_info[k] for k in sorted(subnetwork_output_info.keys())]
        nodes = [self.node.node(x.replace(self.node.name(), '', 1).lstrip('/')) for x in raw_paths]
        return tuple(nodes)

    @property
    def geo_counts(self):
        try:
            counts_info = _to_dict(self.node.infoTree().branches()['SOP Info'], 'Counts')
        except KeyError:
            return dict()
        vals = {k: _eval(v) for k, v in counts_info.items()}
        d = OrderedDict()
        d['Points'] = vals.get('Points')
        d['Primitives'] = vals.get('Primitives')
        d['Vertices'] = vals.get('Vertices')
        d['Volumes'] = vals.get('Volumes')
        d['VDBs'] = vals.get('VDBs')
        d['Packed Geos'] = vals.get('Packed Geometries')
        d['Packed Fragments'] = vals.get('Packed Fragments')
        return d

    @property
    def detail_attributes(self):
        try:
            detail_info = _to_attrib(self.node.infoTree().branches()['SOP Info'], 'Detail Attributes')
        except KeyError:
            return ()
        return detail_info

    @property
    def point_attributes(self):
        try:
            point_info = _to_attrib(self.node.infoTree().branches()['SOP Info'], 'Point Attributes')
        except KeyError:
            return ()
        return point_info

    @property
    def vertex_attributes(self):
        try:
            vertex_info = _to_attrib(self.node.infoTree().branches()['SOP Info'], 'Vertex Attributes')
        except KeyError:
            return ()
        return vertex_info

    @property
    def primitive_attributes(self):
        try:
            prim_info = _to_attrib(self.node.infoTree().branches()['SOP Info'], 'Primitive Attributes')
        except KeyError:
            return ()
        return prim_info

    @property
    def volumes(self):
        try:
            volume_info = _to_vol(self.node.infoTree().branches()['SOP Info'], 'Volumes')
        except KeyError:
            return ()
        return volume_info

    @property
    def sparse_volumes(self):
        try:
            volume_info = _to_sparse(self.node.infoTree().branches()['SOP Info'], 'Sparse Volumes')
        except KeyError:
            return ()
        return volume_info
