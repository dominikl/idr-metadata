# Delete all map annotations and re-apply
export PATH=$PATH:/home/omero/workspace/OMERO-server/OMERO.server/bin
export IDR=../..

set -e
set -u

omero -q login root@localhost -w omero
ARGS=$(sed "$1"'q;d' input)
YML=$IDR/$(echo $ARGS | cut -f1 -d" ")
CSV=${YML/bulkmap-config.yml/annotation.csv}
OBJID=$(echo $ARGS | cut -f2 -d" ")


omero metadata populate --context deletemap --batch 100 --wait 120 $OBJID
omero metadata populate --context deletemap --batch 100 --wait 120 --cfg $YML $OBJID

omero metadata populate --batch 1000 --file $CSV $OBJID
omero metadata populate --batch 100 --context bulkmap --cfg $YML $OBJID
