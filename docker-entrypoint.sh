#!/bin/sh

wait_for() {
  for i in `seq ${STARTUP_TIMEOUT:=5}` ; do
    nc -z "`dig $1 A +short |head -1`" "$2" > /dev/null 2>&1
    [ $? -eq 0 ] && { sleep 5; echo "`dig $1 A +short`"; return 0; }
  done
  echo "Operation timed out" >&2
  exit 1
}

for ARG in "$@"
do
  case "$ARG" in
  *lookupd-tcp-address=tasks.*|*lookupd-http-address=tasks.*|*nsqd-http-address=tasks.*)
    PARAM="`echo ${ARG} | cut -f1 -d=`"
    TASKS="`echo ${ARG} | cut -f2 -d= | cut -f1 -d:`"
    PORT="`echo ${ARG} | cut -f2 -d:`"
    ARG=`printf "${PARAM}=%s:${PORT} " $(wait_for ${TASKS} ${PORT})`
  ;;
  *broadcast-address=*)
    if [ ${RESOLVE_BROADCAST_ADDR:='0'} = "1" ]; then
      PARAM="`echo ${ARG} | cut -f1 -d=`"
      TASKS="`echo ${ARG} | cut -f2 -d=`"
      ARG="${PARAM}=`grep -w $(hostname) /etc/hosts | cut -f1`"
    fi
  ;;
  esac
  COMMAND="${COMMAND} ${ARG}"
done

if [ ${SWARM_CONTROLLER:='0'} = "1" ];
then
  /usr/local/bin/nsq-ctrl.py &
else
  rm -f /usr/local/bin/nsq-ctrl.py
fi

exec $COMMAND
