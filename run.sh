#!/bin/sh

TREC_EVAL=../../../trec_eval.9.0/trec_eval
[ ! -f $TREC_EVAL ] && TREC_EVAL=../../trec_eval.9.0/trec_eval
OPTS="-q -c -l3"
REL_INFO_FILE=result_judge/NTCIR11_Math-qrels.dat
SRC_DIR=result_submit/
DST_DIR=result_trec_eval_R/

for f in `cd $SRC_DIR; ls *.dat`
do
  name=`echo $f | sed s/\.dat//`
  echo $name
  $TREC_EVAL $OPTS -m qrels_jg -R qrels_jg $REL_INFO_FILE $SRC_DIR$name.dat > $DST_DIR$name.dat
done

OPTS="-q -c -l1"
REL_INFO_FILE=result_judge/NTCIR11_Math-qrels.dat
SRC_DIR=result_submit/
DST_DIR=result_trec_eval_PR/

for f in `cd $SRC_DIR; ls *.dat`
do
  name=`echo $f | sed s/\.dat//`
  echo $name
  $TREC_EVAL $OPTS -m qrels_jg -R qrels_jg $REL_INFO_FILE $SRC_DIR$name.dat > $DST_DIR$name.dat
done
