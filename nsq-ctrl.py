#!/usr/bin/env python3
import os, logging, traceback, json, requests, dns.resolver
from time import sleep

def update_nsq_config(lookup_addrs, type, addr, port):
    # Run a PUT request. If there are any exceptions, print the exception and return an empty list.
    logger = logging.getLogger(__name__)
    config_uri = 'nsqlookupd_tcp_addresses' if type == 'nsqd' else 'nsqlookupd_http_addresses'
    try:
      r = requests.put('http://{}:{}/config/{}'.format(addr, port, config_uri), data=json.dumps(lookup_addrs), timeout=30)
      if r.ok:
        logger.info('{} {} has been updated'.format(type, addr))

    except Exception as e:
      logging.error(traceback.format_exc())
      pass

def get_configured_nsqlookups(type, addr, port):
    # Run a GET request and return a list of IP. If there are any exceptions, print the exception and return an empty list.
    logger = logging.getLogger(__name__)
    ips = []
    config_uri = 'nsqlookupd_tcp_addresses' if type == 'nsqd' else 'nsqlookupd_http_addresses'
    try:
      r = requests.get('http://{}:{}/config/{}'.format(addr, port, config_uri), timeout=30)
      ips = r.json()
      logger.debug('{} {} configured nsqlookup addresses: {}'.format(type, addr, ', '.join(ips)))

    except Exception as e:
      logging.error(traceback.format_exc())
      pass

    return ips

def check_and_update(nsqlookup_addrs, nsq_type, nsq_addr, nsq_port):
    if set(get_configured_nsqlookups(nsq_type, nsq_addr, nsq_port)).symmetric_difference(set(nsqlookup_addrs)):
      logger.warning('nsqlookup addresses of {} {} must be updated'.format(nsq_type, nsq_addr))
      update_nsq_config(nsqlookup_addrs, nsq_type, nsq_addr, nsq_port)
      return True
    else:
      logger.info('nsqlookup addresses of {} {} are up-to-date'.format(nsq_type, nsq_addr))
      return False
def resolve(fqdn, rtype='A'):
    # Query the DNS server for a record of type rtype. The default is A records.
    # Resolve DNS query and return a list of answers. If there are any exceptions, print the exception and return an empty list.
    logger = logging.getLogger(__name__)
    ips = []
    try:
      ans = dns.resolver.query(fqdn, rtype)
      ips = [a.to_text() for a in ans]

    except Exception as e:
      logging.error(traceback.format_exc())
      pass

    return ips

if __name__ == '__main__':

  # logging
  logging.basicConfig(level=logging.DEBUG) if os.getenv('DEBUG') == 'true' else logging.basicConfig(level=logging.INFO)
  logger = logging.getLogger(__name__)

  # environment variables
  nsqlookup_service = os.getenv('NSQLOOKUP_SERVICE_NAME')
  nsq_service = os.getenv('NSQ_SERVICE_NAME')
  if nsqlookup_service is None:
    logger.error('NSQLOOKUP_SERVICE_NAME environment is required')
    exit(1)
  if nsq_service is None:
    logger.error('NSQ_SERVICE_NAME environment is required')
    exit(1)

  # startup sleep time
  logger.info('Waiting startup time...')
  sleep(int(os.getenv('STARTUP_WAIT') or '1'))

  # set service DNS name and service port
  nsqlookupd_dns, _, nsqlooupd_port = nsqlookup_service.partition(':')
  nsqd_dns, _, nsqd_port = nsq_service.partition(':')

  while True:
    sleep(10)
    # resolve DNS and set ip addresses and ports
    nsqd_ips = resolve('tasks.' + nsqd_dns)
    nsqd_port = nsqd_port or '4151'
    nsqlookupd_ips = resolve('tasks.' + nsqlookupd_dns)
    nsqlookupd_tcp_port = nsqlooupd_port or '4160'
    nsqlookupd_http_port = str(int(nsqlookupd_tcp_port) + 1)
    nsqlookupd_tcp_addrs = [ip + ':{}'.format(nsqlookupd_tcp_port) for ip in nsqlookupd_ips]
    nsqlookupd_http_addrs = [ip + ':{}'.format(nsqlookupd_http_port) for ip in nsqlookupd_ips]

    logger.info('nsqlookupd IPs: {}'.format(', '.join(nsqlookupd_ips)))
    logger.info('nsqd IPs: {}'.format(', '.join(nsqd_ips)))

    # nsqd
    for nsqd_ip in nsqd_ips:
      check_and_update(nsqlookupd_tcp_addrs, 'nsqd', nsqd_ip, nsqd_port)
    # nsqadmin
    check_and_update(nsqlookupd_http_addrs, 'nsqadmin', '127.0.0.1', '4171')
