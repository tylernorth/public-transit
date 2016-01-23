from transit.common import utils as common_utils
from transit.modules.nextbus import urls, utils
from transit.modules.nextbus import stop

def _route_base(route_data, encoding):
    data = common_utils.parse_page(route_data, ['tag'], encoding)
    data['route_tag'] = data.pop('tag', None)
    return data

def _route(route_data, encoding):
    data = _route_base(route_data, encoding)
    data.update(common_utils.parse_page(route_data, ['title'], encoding))
    return data

def _route_info(route_data, encoding):
    data = _route_base(route_data, encoding)
    args = ['title', 'color', 'oppositecolor', 'latmin', 'latmax', 'lonmin', 'lonmax']
    additional_data = common_utils.parse_page(route_data, args, encoding)
    data.update(additional_data)
    data['opposite_color'] = data.pop('oppositecolor', None)
    data['latitude_min'] = data.pop('latmin', None)
    data['latitude_max'] = data.pop('latmax', None)
    data['longitude_min'] = data.pop('lonmin', None)
    data['longitude_max'] = data.pop('lonmax', None)

    data['stops'] = []
    data['paths'] = []
    data['directions'] = []

    # Add all complete stop data
    # Directions will have stops with just "tags"
    # Ignore those for now
    for new_stop in route_data.find_all('stop'):
        if not new_stop.get('stopid'):
            continue
        data['stops'].append(stop._stop(new_stop, encoding))

    for direction in route_data.find_all('direction'):
        new_dir = _route_direction(direction, encoding)
        # now add all stop tags for each direction
        for i in direction.find_all('stop'):
            new_dir['stop_tags'].append(i.get('tag'))
        data['directions'].append(new_dir)

    for path in route_data.find_all('path'):
        path_points = []
        for point in path.find_all('point'):
            path_points.append(stop._point(point, encoding))
        data['paths'].append(path_points)
    return data

def _route_direction(direction_data, encoding):
    args = ['tag', 'name', 'title', 'useforui']
    data = common_utils.parse_page(direction_data, args, encoding)
    data['use_for_ui'] = data.pop('useforui', None)
    data['stop_tags'] = []
    return data

def _message(message_data, encoding):
    args = ['id', 'priority', 'startboundary', 'endboundary', 'startboundarystr',
            'endboundarystr', 'senttobuses']
    data = common_utils.parse_page(message_data, args, encoding)
    data['message_id'] = data.pop('id', None)
    data['start_boundary_epoch'] = data.pop('startboundary', None)
    data['end_boundary_epoch'] = data.pop('endboundary', None)
    data['start_boundary'] = data.pop('startboundarystr', None)
    data['end_boundary'] = data.pop('endboundarystr', None)
    data['send_to_buses'] = data.pop('senttobuses', None)
    data['text'] = []
    for text in message_data.find_all('text'):
        data['text'].append(common_utils.clean_value(text.contents[0], encoding))
    return data

def _route_message(route_data, encoding):
    data = _route_base(route_data, encoding)
    data['messages'] = [_message(mes, encoding) for mes in route_data.find_all('message')]
    return data

def route_list(agency_tag):
    '''Get list of agency routes
       agency_tag: agency tag
    '''
    assert isinstance(agency_tag, basestring), 'agency tag must be string type'
    url = urls.route_list(agency_tag)
    soup, encoding = utils.make_request(url)
    return_data = []
    for route in soup.find_all('route'):
        return_data.append(_route(route, encoding))
    return return_data

def route_get(agency_tag, route_tag):
    '''Get information about route
       agency_tag: agency tag
       route_tag : route_tag
    '''
    assert isinstance(agency_tag, basestring), 'agency tag must be string type'
    assert isinstance(route_tag, basestring), 'route tag must be string type'
    url = urls.route_show(agency_tag, route_tag)
    soup, encoding = utils.make_request(url)
    return _route_info(soup.find('route'), encoding)

def route_messages(agency_tag, route_tags):
    '''Get alert messages for routes
       agency_tag : agency tag
       route_tags : either single route tag, or list of tags
    '''
    assert isinstance(agency_tag, basestring), 'agency tag must be string type'
    assert isinstance(route_tags, basestring) or isinstance(route_tags, list),\
        'route tag must be string type or list of string types'
    url = urls.message_get(agency_tag, route_tags)
    soup, encoding = utils.make_request(url)
    return [_route_message(route, encoding) for route in soup.find_all('route')]
