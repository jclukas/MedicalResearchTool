#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys, os
sys.path.append("{0}/Desktop/cbmi/reproduce/python/tools/objects".format(os.environ['HOME']))
sys.path.append("{0}/Desktop/cbmi/reproduce/python/tools".format(os.environ['HOME']))

from getopt import getopt
from Article import PMCArticle, ClosedArticle
from Trainer import Trainer
import nltk
from Query import Query
from pprint import pprint
from ArticleExtractor import ArticleExtractor

import re, requests
import subprocess

def get_command_args(argv):
	firstarticles = ["24433938","26513432","23632207","25266841","25203000","26236002","24119466",
					"20842022","21411379","23552606","21700714","26850871","25883689","24934411",
					"24656777","25839735","25368396","26231634","23374784"]
	secondarticles = ["26775158","26815253","26825406","26824374","26803428","26795617","26784271","26783357","26783356","26781389"]
	pmcarticles = ['23632207','25266841','24119466','21700714','25883689','24934411','25368396','26775158','26803428','26784271']
	pmcs = ['PMC3852715','PMC4527599','PMC4254085','PMC3137948','PMC4384267','PMC4070347','PMC4221799','PMC4715304','PMC4747833','PMC4742403']

	articles = secondarticles
	#articles = pmcarticles
	#excluded: "26824581"

	indi = xml = pdf = redcap = down = train = 0
	opts, args = getopt(argv,"a:dixprt",["articles=","download","independent","xml","pdf","redcap","train"])
	for opt,arg in opts:
		if opt in ("-a","--articles"):
			articles = arg.split(',')
		elif opt in ("-i","--independent"):
			indi = 1
		elif opt in ("-x","--xml"):
			xml = 1
		elif opt in ("-p","--pdf"):
			pdf = 1
		elif opt in ("-r","--redcap"):
			redcap = 1
		elif opt in ("-d","--download"):
			down = 1
		elif opt in ("-t","--train"):
			train = 1
	return ({
		'indi':indi,
		'xml':xml,
		'pdf':pdf,
		'redcap':redcap,
		'down':down,
		'train':train
		}, articles)

def side_project(article):
	xml = ArticleExtractor().xml_load("http://www.ncbi.nlm.nih.gov/pubmed/{0}?report=xml&format=text".format(article))
	ids = xml['PubmedArticle']['PubmedData']['ArticleIdList']['ArticleId']
	try:
		for each_id in ids:
			if (each_id['@IdType'] == "pmc"):
				pmc = each_id['#text']
	except TypeError:
		if (ids['@IdType'] == "pmc"):
			pmc = ids['#text']
	try:
		print("{0} , {1}".format(pmc,article))
	except UnboundLocalError:
		#no pmc value
		pass



def main(argv):
	opts, articles = get_command_args(argv)
	metadata = Query().get_metadata()




	if (opts['train']):
		
		#define which to train
		#TODO, could add option to -t argument, which redcaps
		#meta_analysis = Trainer("meta_analysis",articles)
		#meta_analysis.pickle()

		#primary_research = Trainer("primary_research",articles)

		#algs.append(qu.get_mldata("reproducibilityresearch_yn"))
		searchwords = ['statistical','analysis','standard','deviation','sd','chi-squared','test','significance','t-test','regression','model','data','intercepts']
		analysis_processes_clear = Trainer("analysis_processes_clear",articles,searchwords)


	for each_article in articles:
		print(each_article)

		############side projects#################
		#xml = ArticleExtractor().xml_load("https://www.ncbi.nlm.nih.gov/pmc/oai/oai.cgi?verb=GetRecord&identifier=oai:pubmedcentral.nih.gov:{0}&metadataPrefix=pmc".format(re.sub(r'pmc','',each_article)))
		#xml = ArticleExtractor().xml_load("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id={0}".format(re.sub(r'pmc','',each_article)))
		#continue

		
		#side_project(each_article)
		#continue

		#r = requests.get("http://www.ncbi.nlm.nih.gov/pmc/articles/{0}/?report=reader".format(each_article))
		#proc = subprocess.Popen(["curl","-s","-o /dev/null",'-w "%{http_code}"',"http://www.ncbi.nlm.nih.gov/pmc/articles/{0}/?report=reader".format(each_article)],stdout=subprocess.PIPE)
		
		#proc = subprocess.Popen(["curl","-s",'-w "%{http_code}"',"http://www.ncbi.nlm.nih.gov/pmc/articles/{0}/?report=reader".format(each_article)],stdout=subprocess.PIPE)
		"""
		code = proc.communicate()[0]
		code = code.strip()
		code = code.strip(b'"')
		print(code == b"403")
		print("\n")
		continue
		"""
		###############side projects###############



		art = ClosedArticle(each_article,opts['indi'],metadata)
		#art = PMCArticle(each_article,opts['indi'],metadata)

		if (opts['xml']):
			art.xml_extract()
			art.get_institution()
			art.get_clinical_domain_from_xml()

		if (opts['down']):
			art.download_pdf()

		if (opts['pdf']):

			art.get_reviewer()
			art.get_clinical_domain_from_pdf()
			art.get_hypotheses()
			art.get_funding()
			art.get_inex_criteria()
			art.get_ontol_vocab()
			art.get_databases()
			art.get_query()		#TODO
			art.get_nlp()

			#left off for pmc here:
			art.get_analysis()
			art.get_stats()

			art.get_limitations()
		
		#TODO, user friendly version of data
		art.clean_entry()
		pprint(art.entry)
		
		if (opts['redcap']):
			art.enter_redcap(art.entry)

		print("\n\n\n\n")

if __name__ == "__main__":
	main(sys.argv[1:])
