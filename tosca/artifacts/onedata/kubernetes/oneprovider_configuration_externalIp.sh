#!/usr/bin/env bash

mkdir -p $1/etc
mkdir -p $1/etc/op_worker
echo "Directory $1/etc/op_worker created"

cp $2 $1/etc/op_worker
echo "File $2 copied to $1/etc/op_worker"