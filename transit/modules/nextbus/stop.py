from transit.urls import nextbus
from transit.common import utils

class Stop(object):
    def __init__(self, data, encoding):
        self.tag = data.get('tag').encode(encoding)
        self.title = data.get('title').encode(encoding)
        self.latitude = float(data.get('lat').encode(encoding))
        self.longitude = float(data.get('lon').encode(encoding))
        self.stop_id = int(data.get('stopid').encode(encoding))
        try:
            self.short_title = data.get('shorttitle').encode(encoding)
        except AttributeError:
            self.short_title = None

    def __repr__(self):
        return '%s - %s' % (self.tag, self.title)


class Point(object):
    def __init__(self, point_data, encoding):
        self.latitude = float(point_data.get('lat').encode(encoding))
        self.longitude = float(point_data.get('lon').encode(encoding))

    def __repr__(self):
        return '%s lat- %s lon' % (self.latitude, self.longitude)

class RoutePrediction(object):
    def __init__(self, route_data, encoding):
        self.route_tag = route_data.get('routetag').encode(encoding)
        self.agency_title = route_data.get('agencytitle').encode(encoding)
        self.route_title = route_data.get('routetitle').encode(encoding)
        self.stop_title = route_data.get('stoptitle').encode(encoding)
        self.directions = []
        self.messages = []

        #route_pred = RoutePrediction(new_route, encoding)
        # All directions in route
        self.directions = [RouteDirectionPrediction(i, encoding) \
            for i in route_data.find_all('direction')]
        for message in route_data.find_all('message'):
            self.messages.append(message.get('text').encode('utf-8'))

    def __repr__(self):
        return '%s - %s - %s' % \
            (self.agency_title, self.stop_title, self.route_tag)

class RouteDirectionPrediction(object):
    def __init__(self, direction_data, encoding):
        self.title = direction_data.get('title').encode(encoding)
        self.predictions = []
        # Find all predictions in direction
        for pred in direction_data.find_all('prediction'):
            self.predictions.append(RouteStopPrediction(pred, encoding))

    def __repr__(self):
        return '%s' % self.title

class RouteStopPrediction(object): #pylint: disable=too-many-instance-attributes
    def __init__(self, data, encoding):
        self.seconds = int(data.get('seconds').encode(encoding))
        self.minutes = int(data.get('minutes').encode(encoding))
        self.epochtime = int(data.get('epochtime').encode(encoding))
        self.trip_tag = data.get('triptag').encode(encoding)
        self.vehicle = data.get('vehicle').encode(encoding)
        self.block = data.get('block').encode(encoding)
        self.dir_tag = data.get('dirtag').encode(encoding)
        self.is_departure = False
        if data.get('isdeparture').encode(encoding) == 'true':
            self.is_departure = True
        self.affected_by_layover = False
        try:
            if data.get('affectedbylayover').encode(encoding) == 'true':
                self.affected_by_layover = True
        except AttributeError:
            # data not present
            pass

    def __repr__(self):
        time = utils.pretty_time(self.minutes, self.seconds)
        return '%s - %s' % (time, self.vehicle)

def stop_prediction(agency_tag, stop_id, route_tags=None):
    # Different url depending on route_tag
    url = nextbus.stop_prediction(agency_tag, stop_id, route_tags=route_tags)
    soup, encoding = utils.make_request(url)
    # Add all stop predictions for routes
    routes = [RoutePrediction(i, encoding) \
        for i in soup.find_all('predictions')]
    # if no route tag list specified return
    # .. a single route tag will already be taken care of
    if not isinstance(route_tags, list):
        return routes
    # only return routes with tags in list
    tags = [i.lower() for i in route_tags]
    return [route for route in routes if route.route_tag.lower() in tags]

def multiple_stop_prediction(agency_tag, data):
    url = nextbus.multiple_stop_prediction(agency_tag, data)
    soup, encoding = utils.make_request(url)
    return [RoutePrediction(i, encoding) \
                            for i in soup.find_all('predictions')]
