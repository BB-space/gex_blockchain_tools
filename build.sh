#!/bin/bash

rm -rf build/contracts/*
truffle compile
truffle deploy --reset