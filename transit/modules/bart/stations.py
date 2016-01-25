from transit.common import utils as common_utils
from transit.modules.bart import urls, utils
from transit.exceptions import TransitException

datetime_format = '%I:%M %p'

# bart doesnt have a way to call this easily that I can find
# .. the one on their official website didnt include the new(-ish) station
# .. at Oakland Airport, so I assume it isnt maintained
STATION_MAPPING = {
    "12th" : "12th St. Oakland City Center",
    "16th" : "16th St. Mission (SF)",
    "19th" : "19th St. Oakland",
    "24th" : "24th St. Mission (SF)",
    "ashb" : "Ashby (Berkeley)",
    "balb" : "Balboa Park (SF)",
    "bayf" : "Bay Fair (San Leandro)",
    "cast" : "Castro Valley",
    "civc" : "Civic Center (SF)",
    "cols" : "Coliseum/Oakland Airport",
    "colm" : "Colma",
    "conc" : "Concord",
    "daly" : "Daly City",
    "dbrk" : "Downtown Berkeley",
    "dubl" : "Dublin/Pleasanton",
    "deln" : "El Cerrito del Norte",
    "plza" : "El Cerrito Plaza",
    "embr" : "Embarcadero (SF)",
    "frmt" : "Fremont",
    "ftvl" : "Fruitvale (Oakland)",
    "glen" : "Glen Park (SF)",
    "hayw" : "Hayward",
    "lafy" : "Lafayette",
    "lake" : "Lake Merritt (Oakland)",
    "mcar" : "MacArthur (Oakland)",
    "mlbr" : "Millbrae",
    "mont" : "Montgomery St. (SF)",
    "nbrk" : "North Berkeley",
    "ncon" : "North Concord/Martinez",
    "oakl" : "Oakland Int'l Airport",
    "orin" : "Orinda",
    "pitt" : "Pittsburg/Bay Point",
    "phil" : "Pleasant Hill",
    "powl" : "Powell St. (SF)",
    "rich" : "Richmond",
    "rock" : "Rockridge (Oakland)",
    "sbrn" : "San Bruno",
    "sfia" : "San Francisco Int'l Airport",
    "sanl" : "San Leandro",
    "shay" : "South Hayward",
    "ssan" : "South San Francisco",
    "ucty" : "Union City",
    "wcrk" : "Walnut Creek",
    "wdub" : "West Dublin",
    "woak" : "West Oakland",
}

# what is in the station object will differ on the call
# this base class has the very basic stuff that should be in all

def _station_info(station_data, encoding):
    args = ['name', 'abbr', 'gtfs_latitude', 'gtfs_longitude', 'address', 'city',
            'county', 'state', 'zipcode', 'platform_info', 'intro', 'cross_street',
            'food', 'shopping', 'attraction', 'link']
    data = common_utils.parse_page(station_data, args, encoding)
    data['abbreviation'] = data.pop('abbr', None)

    data['north_routes'] = []
    north_routes = station_data.find('north_routes')
    for route in north_routes.find_all('route'):
        route_string = common_utils.clean_value(route.contents[0], encoding)
        data['north_routes'].append(int(route_string.replace('ROUTE ', '')))

    data['south_routes'] = []
    south_routes = station_data.find('south_routes')
    for route in south_routes.find_all('route'):
        route_string = common_utils.clean_value(route.contents[0], encoding)
        data['south_routes'].append(int(route_string.replace('ROUTE', '')))

    north_platforms = station_data.find('north_platforms')
    data['north_platforms'] = []
    for plat in north_platforms.find_all('platform'):
        route_string = common_utils.clean_value(plat.contents[0], encoding)
        data['north_platforms'].append(int(route_string))

    south_platforms = station_data.find('south_platforms')
    data['south_platforms'] = []
    for plat in south_platforms.find_all('platform'):
        route_string = common_utils.clean_value(plat.contents[0], encoding)
        data['south_platforms'].append(int(route_string))
    return data

def _station_access(station_data, encoding):
    args = ['name', 'abbr', 'parking_flag', 'bike_flag', 'locker_flag',
            'entering', 'exiting', 'parking', 'lockers', 'destinations', 'transit_info',
            'link']
    data = common_utils.parse_page(station_data, args, encoding)
    data['abbreviation'] = data.pop('abbr', None)
    data['parking_flag'] = data.pop('parking_flag', 0) == 1
    data['bike_flag'] = data.pop('bike_flag', 0) == 1
    data['locker_flag'] = data.pop('locker_flag', 0) == 1
    return data

def _estimate(estimate_data, encoding):
    args = ['platform', 'direction', 'length', 'color', 'bikeflag', 'minutes']
    data = common_utils.parse_page(estimate_data, args, encoding)
    data['bike_flag'] = data.pop('bikeflag', 0) == 1
    if not isinstance(data['minutes'], int) and 'leaving' in data['minutes'].lower():
        data['minutes'] = 0
    return data

def _direction_estimates(estimate_data, encoding, destinations=None):
    data = common_utils.parse_page(estimate_data, ['abbreviation'], encoding)
    # if destinations given, check here if valid
    # .. if not valid give up now to save time
    if destinations and data['abbreviation'].lower() not in destinations:
        raise TransitException("Not valid destination:%s" % data['abbreviation'])
    new_data = common_utils.parse_page(estimate_data, ['destination'], encoding)
    data['name'] = new_data.pop('destination', None)
    data['estimates'] = []
    for est in estimate_data.find_all('estimate'):
        estimate_data = _estimate(est, encoding)
        data['estimates'].append(estimate_data)
    return data

def _station_departures(station_data, encoding, station_output=None):
    args = ['name', 'abbr']
    data = common_utils.parse_page(station_data, args, encoding)
    data['abbreviation'] = data.pop('abbr', None)
    destinations = None
    if station_output:
        try:
            destinations = station_output[data['abbreviation'].lower()]
        except KeyError:
            raise TransitException("%s not in accepted stations" % data['abbreviation'].lower())

    data['directions'] = []
    # if exception was raised then direction not in destinations given
    # .. so skip and dont put it in list
    for etd in station_data.find_all('etd'):
        try:
            direction_data = _direction_estimates(etd, encoding, destinations=destinations)
            data['directions'].append(direction_data)
        except TransitException:
            continue
    return data

def _schedule_time(schedule_data, encoding):
    args = ['line', 'trainheadstation', 'origtime', 'desttime', 'trainidx',
            'bikeflag']
    data = common_utils.parse_page(schedule_data, args, encoding,
                                   datetime_format=datetime_format)
    data['line'] = int(data.pop('line', '0').replace('ROUTE ', ''))
    data['head_station'] = data.pop('trainheadstation', None)
    data['origin_time'] = data.pop('origtime', None)
    data['destination_time'] = data.pop('desttime', None)
    data['train_index'] = int(data.pop('trainidx', None))
    bike_flag = int(data.pop('bikeflag', 0))
    data['bike_flag'] = bike_flag == 1
    return data

def _station_schedule(station_data, encoding):
    args = ['name', 'abbr']
    data = common_utils.parse_page(station_data, args, encoding)
    data['abbreviation'] = data.pop('abbr', None)
    data['schedule_times'] = []
    for item in station_data.find_all('item'):
        data['schedule_times'].append(_schedule_time(item, encoding))
    return data

def station_list():
    '''List all bart stations'''
    return STATION_MAPPING

def station_info(station):
    '''Station information
        station: station abbreviation
    '''
    assert isinstance(station, basestring), 'station must be string type'
    url = urls.station_info(station)
    soup, encoding = utils.make_request(url)
    return _station_info(soup.find('station'), encoding)

def station_access(station):
    '''Station Access information
        station: station abbreviation
    '''
    assert isinstance(station, basestring), 'station must be string type'
    url = urls.station_access(station)
    soup, encoding = utils.make_request(url)
    return _station_access(soup.find('station'), encoding)

def station_multiple_departures(station_output):
    '''
    Get estimated departures for mutliple stations
    station_output:
        {
            'station_abbrevation' : [destination1, destination2],
            'station_abbreviation2' : [],
            # empty for all possible destinations
        }
    '''
    assert isinstance(station_output, dict), 'station output must be dict type'
    for key in station_output.keys():
        assert isinstance(key, basestring), 'station output keys must be stringtype'
        lowered = key.lower()
        if lowered != key:
            station_output[lowered] = station_output.pop(key)
        assert isinstance(station_output[lowered], list),\
            'station output values must be list type'
        for item in station_output[lowered]:
            assert isinstance(item, basestring),\
                'destination list item must be basestring type'

    # call a list of all departures here, then strip data for only stations requested
    url = urls.estimated_departures('all')
    soup, encoding = utils.make_request(url)

    full_data = []
    for station in soup.find_all('station'):
        try:
            full_data.append(_station_departures(station, encoding,
                                                 station_output=station_output))
        except TransitException:
            continue
    return full_data

def station_departures(station, platform=None, direction=None,
                       destinations=None):
    '''Get estimated station departures
        station: station abbreviation
        plaform: platfrom number
        direction: (n)orth or (s)outh
        destinatons: List of abbreviated destinations, exclude all others
    '''
    assert isinstance(station, basestring), 'station must be string type'
    assert platform is None or isinstance(platform, int),\
        'platform must be int or null type'
    assert direction is None or isinstance(direction, basestring),\
        'direction must be string or null type'
    assert destinations is None or isinstance(destinations, list), \
        'destinations must be list or null type'
    url = urls.estimated_departures(station, platform=platform,
                                    direction=direction)
    soup, encoding = utils.make_request(url)

    station = station.lower()
    if station.lower() == 'all':
        station_output = None
    elif destinations is not None:
        station_output = {station : [dest.lower() for dest in destinations]}
    else:
        station_output = {station : []}
    departs = []
    for station_data in soup.find_all('station'):
        departs.append(_station_departures(station_data, encoding,
                                           station_output=station_output))
    return departs

def station_schedule(station, date=None):
    '''Get a stations schedule
        station: station abbreviation
        date: mm/dd/yyyy format
    '''
    assert isinstance(station, basestring), 'station must be string type'
    if date and not utils.DATE_MATCH.match(date):
        raise TransitException('date must match pattern:%s' % utils.DATE_MATCH_REGEX)
    url = urls.station_schedule(station, date=date)
    soup, encoding = utils.make_request(url)
    return _station_schedule(soup.find('station'), encoding)
