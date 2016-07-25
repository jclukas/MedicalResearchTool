#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from getopt import getopt
import csv, os, sys, re
sys.path.append("{0}/Desktop/cbmi/reproduce/python".format(os.environ['HOME']))
import pycurl, json, io
from pprint import pprint
from config import config


class Query(object):
	def __init__(self):
		self.matches = []
		self.mldata = {}
	
	def get_data(self,field):

		buf = io.BytesIO()
		data = {
		    'token': 'D9FFA77DB83AE7D9E3E92BB0B0CBBFDB',
		    'content': 'record',
		    'format': 'json',
		    'type': 'flat',
		    'fields[0]': 'article_doi',
		    'fields[1]': 'record_id',
		    'fields[2]': field,
		    'rawOrLabel': 'raw',
		    'rawOrLabelHeaders': 'raw',
		    'exportCheckboxLabel': 'false',
		    'exportSurveyFields': 'false',
		    'exportDataAccessGroups': 'false',
		    'returnFormat': 'json'
		}
		ch = pycurl.Curl()
		ch.setopt(ch.URL, 'https://redcap.wustl.edu/redcap/srvrs/prod_v3_1_0_001/redcap/api/')
		ch.setopt(ch.HTTPPOST, list(data.items()))
		ch.setopt(ch.WRITEFUNCTION, buf.write)
		ch.perform()
		ch.close()
		records = json.loads(buf.getvalue().decode())
		buf.close()
		return records

	def get_matches(self,redcap,boolean,val):
		for eachdict in self.get_data(redcap):
			if (boolean):
				if (eachdict[redcap].strip() == str(val)):
					self.matches.append((eachdict['article_doi'],eachdict['record_id']))
			else:
				if (eachdict[redcap].strip() != str(val)):
					self.matches.append((eachdict['article_doi'],eachdict['record_id']))
		return self.matches
	
	def get_searches(self,redcap,boolean,val):
		for eachdict in self.get_data(redcap):
			if (boolean):
				if (re.search(str(val),eachdict[redcap].strip(),re.I)):
					self.matches.append((eachdict['article_doi'],eachdict['record_id']))
			else:
				if not (re.search(str(val),eachdict[redcap].strip(),re.I)):
					self.matches.append((eachdict['article_doi'],eachdict['record_id']))
		return self.matches

	def get_metadata(self):
		
		buf = io.BytesIO()

		fields = {
		    'token': config['api_token'],
		    'content': 'metadata',
		    'format': 'json'
		}

		ch = pycurl.Curl()
		ch.setopt(ch.URL, config['api_url'])
		ch.setopt(ch.HTTPPOST, list(fields.items()))
		ch.setopt(ch.WRITEFUNCTION, buf.write)
		ch.perform()
		ch.close()

		metadata = json.loads(buf.getvalue().decode())
		buf.close()
		return metadata

	def get_ml_data(self,redcap):
		#TODO, if item['field_name'] never matches self.redcap
			#or just remove?
		for item in self.get_metadata():
			if (item['field_name'] == redcap):
				if (item['field_type'] != "yesno"):
					print("get_data called on invalid redcap field: {0}".format(redcap))
					return
		for eachdict in self.get_data(redcap):
			self.mldata[eachdict['record_id'].strip()] = eachdict[redcap].strip()
		return self.mldata
