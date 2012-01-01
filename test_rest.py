from rest.client import Connection
import json

if __name__ == '__main__':
    conn = Connection('http://api.twitter.com/1/statuses/')
    response_data = conn.request_get('/public_timeline.json', {'trim_user': True})
    
    data = json.loads(response_data['body'])
    
    for el in data:
        print '-------------------------'
        for key, value in el.iteritems():
            print key, ':', value
    
