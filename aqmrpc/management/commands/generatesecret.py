
import random
from cStringIO import StringIO

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

import twisted.web
import twisted.internet

from aqmrpc import interface


def get_random_string(length=50):
    s_buffer = StringIO()
    char_list = 'abcdefghijklmnopqrstuvwxyz1234567890!@#$%^&*()'
    s_min = 0
    s_max = len(char_list) - 1
    
    for i in xrange(length):
        n = random.randint(s_min, s_max)
        s_buffer.write(char_list[n])
    
    return s_buffer.getvalue()

class Command(BaseCommand):
    help = "Generate a random secret key."

    def handle(self, *args, **options):
        print 'Random Secret Key'
        print get_random_string()
        