[issues]: https://github.com/kladiv/docker-nsq/issues
[NSQ]: http://nsq.io/
[Docker Hub]: https://hub.docker.com/r/claudiomastrapasqua/docker-nsq/


## docker-nsq

Custom docker image for [NSQ].

This image is on [Docker Hub].

### Getting the image

To get the image download it via:

`docker pull claudiomastrapasqua/docker-nsq`

### How to use this image

This image is provided for a Docker Swarm Mode environment. Following **nsqlookup** container is required and must be deployed together to this image:

`$ docker run --name <nsqlookupd_name> -p 4160:4160 -p 4161:4161 nsqio/nsq /nsqlookupd`

then use this image for:

1. **nsqd**: the daemon that receives, queues, and delivers messages to clients

`$ docker run --name <nsqd_name> -p 4150:4150 -p 4151:4151 claudiomastrapasqua/docker-nsq /nsqd --broadcast-address=<name> --lookupd-tcp-address=tasks.<nsqlookup_name>:4160`

2. **nsqadmin**: a Web UI to perform various administrative tasks and ***NSQ Controller***:

`$ docker run --name <name> -p 4171:4171 claudiomastrapasqua/docker-nsq /nsqadmin --lookupd-http-address=tasks.<nsqlookup_name>:4161`

### Deploy stack via docker-compose file (3-nodes example)

*Requirements: Docker Engine 17.12.0+*

```
version: "3.5"

services:
  nsqlookup:
    image: nsqio/nsq
    networks:
      - nsq
    command: /nsqlookupd
    configs:
      - source: nsqlookup-healthcheck
        target: /nsqlookup-healthcheck
        mode: 0755
    healthcheck:
        test: ["CMD", "sh", "/nsqlookup-healthcheck"]
        interval: 30s
        timeout: 10s
        retries: 3
    deploy:
      mode: global
      placement:
        constraints:
          - node.role == manager

  nsqd:
    image: claudiomastrapasqua/docker-nsq
    networks:
      - nsq
    environment:
      RESOLVE_BROADCAST_ADDR: 1
    command: /nsqd --broadcast-address=nsqd --lookupd-tcp-address=tasks.nsqlookup:4160
    deploy:
      replicas: 3
      endpoint_mode: dnsrr
      placement:
        constraints:
          - node.role == worker
    depends_on:
      - nslookup

  nsqadmin:
    image: claudiomastrapasqua/docker-nsq
    hostname: nsqadmin
    ports:
      - "4171:4171"
    networks:
      - nsq
      - proxy
    environment:
      SWARM_CONTROLLER: 1
      NSQLOOKUP_SERVICE_NAME: "${STACK_NAME:-nsqtest}_nsqlookup"
      NSQ_SERVICE_NAME: "${STACK_NAME:-nsqtest}_nsqd"
    command: /nsqadmin --lookupd-http-address=tasks.nsqlookup:4161
    deploy:
      replicas: 1
      placement:
        constraints:
          - node.role == worker
    depends_on:
      - nslookup

configs:
  nsqlookup-healthcheck:
    file: "${STACK_HOME:-.}/scripts/nsqlookup-healthcheck.sh"

networks:
  nsq:
    attachable: true
  proxy:
    external: true
```

### Monitoring

NSQ distributed cluster can be managed and monitored using **nsqadmin** container connecting to http://<docker_host>:4171 (exposed port).

### Logging

You can read container/service logs via commands:

`$ docker logs -f <container_name or container_id>`

or

`$ docker service logs -f <service_name or service_id>`

### Support

Open [issues] on GitHub
