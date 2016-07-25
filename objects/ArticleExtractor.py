#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys, re
import nltk
import requests, html
import xmltodict
from pprint import pprint
from stemming.porter2 import stem
from ArticleManager import ArticleManager

import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape, unescape
from bs4 import BeautifulSoup
import time

class ArticleExtractor(ArticleManager):

	def clean_entry(self):
		for (k,v) in self.entry.items():
			copy = v
			try:
				val = copy.split(',')
				val = set(val)
				val = ', '.join(val)
				self.entry[k] = val
			except AttributeError:
				#wrong type
				pass


	def xml_load(self,site):
		"""
		xml_text = requests.get(site).text
		beaut = BeautifulSoup(xml_text,"xml")
		print("\n\n\n\n")
		print(beaut)
		print(beaut.permissions)
		conti = input()

		return beaut



		xml_text = requests.get(site).text
		root = ET.fromstring(xml_text)
		xml = xmltodict.parse(xml_text)
		return root

		"""
		xml_text = requests.get(site).text
		xml_text = re.sub(r'&lt;',"<",xml_text)
		xml_text = re.sub(r'&gt;',">",xml_text)
		#unescape(requests.get(site).text,{"&lt;":"<", "&gt;":">"})		<--- alternate to above regex

		data = xmltodict.parse(xml_text)
		return data

	def get_reviewer(self):
		username = os.getlogin() or pwd.getpwuid(os.getuid())[0]
		users = self.get_choices("reviewer")
		for user in users:
			if (re.search(username,user,re.I)):
				self.check("Whos reviewing the article?",users[user],user,"user of computer","reviewer")
				return
		self.ask("Whos reviewing the article?","reviewer")	

	def get_name_ent(self,sent):
		words = nltk.word_tokenize(sent)
		tagged = nltk.pos_tag(words)
		#tagged = nltk.pos_tag([word.rstrip(''.join([str(i) for i in range(10)])) for word in words])
		chunkGram = r"Chunk: {<NNP.?><NNP.?|NN.?|,|\(|\)|:|IN|CC|DT>*<NNP.?|\)>}"
		chunkedParser = nltk.RegexpParser(chunkGram)
		chunked = chunkedParser.parse(tagged)
		return chunked

	def get_clinical_domain(self,key_words):
		if ('clinical_domain' in self.entry):
			return
		stopwords = nltk.corpus.stopwords.words('english') + ['health','disease','medicine','medical','sciences','medicine','international']
		key_words = [stem(word.lower().strip()) for word in key_words if word.lower() not in stopwords]
		domains = self.get_choices("clinical_domain")
		for word in key_words:
			for domain in domains:
				try:
					if (re.search(word,domain,re.I)):
						return domain
				except Exception as e:
					#error in keyword
					pass
		return 0

	def _get_hypotheses(self,text):
		for each_sent in nltk.sent_tokenize(text):
			if (re.search(r'we.*?hypothes',each_sent,re.I)):
				self.check("Hypothesis Driven or Hypothesis Generating",1,"driven",each_sent,"hypothesis_gen_or_driv")
				if ("hypothesis_gen_or_driv" in self.entry):
					self.generate_chooser("Does the publication state null and alternative hypotheses?",each_sent,self.get_choices("clear_hypothesis"))
					if (self.user_choice != -1):
						self.entry['clear_hypothesis'] = self.user_choice
					return
		self.entry['hypothesis_gen_or_driv'] = 2

	#	**26784271 - weird format :(
	def _get_funding(self,text):		#nltk could improve; low priority now though
		for each_sent in nltk.sent_tokenize(text):
			if (re.search(r'funded.*?by',each_sent,re.I|re.S)): 	#TODO, or re.search(r'supported.*?by',each_sent,re.I|re.S)):
				search = re.search(r"grant.*?(\w*\d[\w\d/-]*)",each_sent,re.I)
				if (search):
					self.check("Grant ID",search.group(1).strip(),search.group(1).strip(),each_sent,"grant_ids")
				search = re.search(r'grant.*?from (.*?)[^\w\s-]',each_sent,re.I|re.S)
				if (search):
					self.check("Funders",search.group(1).strip(),search.group(1).strip(),each_sent,"funders")
				else:
					search = re.search(r'funded.*?by (.*?)[^\w\s-]',each_sent,re.I|re.S)
					self.check("Funders",search.group(1).strip(),search.group(1).strip(),each_sent,"funders")

	def _get_inex_criteria(self,text):	#TODO, expand
		for each_sent in nltk.sent_tokenize(text):
			copy = each_sent
			if(re.search(r'were\W*includ',each_sent,re.I) or re.search(r'were\W*exclud',each_sent,re.I) or
				re.search(r'inclus',each_sent,re.I) or (re.search(r'exclus',each_sent,re.I) and not re.search(r'exclusively',each_sent,re.I))):
				if ("inclusion_and_exclusion_stated" not in self.entry):
					self.check_boolean("Inclusion Exclusion Criteria Stated",1,"yes",each_sent,"inclusion_and_exclusion_stated")
				if ("inclusion_and_exclusion_stated" in self.entry):
					self.entry['inclusion_exclu_location'] = 3 #TODO, enter as list??
					self.check_ontol(each_sent)
					return

	def _get_ontol_vocab(self,text): #TODO, if ontol occurs outside of inclusion / exclusion
		ont_dict = self.get_choices("proc_vocabulary")
		ont_dict.update(self.get_choices("diag_vocabulary"))
		ont_dict.update(self.get_choices("med_vocab"))
		ont_dict.update(self.get_choices("lab_vocab"))
		ontols = list(ont_dict.keys())

	def check_ontol(self,info):
		if ("ontol_and_vocab_stated" in self.entry):
			return
		if (not self.indi):
			print("based on:")
			print(info)
		if (self.ask_question("Are any standard ontologies stated (such as CPT, ICD9, etc)?")):
			self.entry['ontol_and_vocab_stated'] = 1
			c1 = {
				"Procedure":1,
				"Diagnosis":2,
				"Medication":3,
				"Laboratory":4
				}
			c2 = {
				"Procedure":"proc_vocabulary",
				"Diagnosis":"diag_vocabulary",
				"Medication":"med_vocab",
				"Laboratory":"lab_vocab"
				}
			c3 = dict((v,k) for k,v in c1.items())
			self.generate_chooser("What categories are the ontologies a part of?",info,c1)
			if (self.user_choice != -1):
				self.ask("What ontologies are given for the category " + c3[self.user_choice] + "?",c2[c3[self.user_choice]])

	def _get_databases(self,text):

		def longest(tree):
			max_list = []
			for each_list in tree:
				if (len(each_list) > len(max_list)):
					max_list = each_list
			return max_list

		
		for each_sent in nltk.sent_tokenize(text):
			if (re.search(r'database',each_sent,re.I)):		#re.search(r'electronic.*?records',each_sent,re.I) or 
				tree = self.get_name_ent(each_sent)
				sts = []
				for st in tree.subtrees(lambda tree: tree.height() == 3):
					for st2 in st.subtrees(lambda tree: tree.height() == 2):
						sts.append([str(tup[0]) for tup in st2.leaves()])
				if (len(sts) > 0):
					self.check("Database Name",' '.join(longest(sts)),' '.join(longest(sts)),each_sent,"db_citation_1")		#TODO, it there's more than one
				if ('db_citation_1' in self.entry):
					self.entry['state_data_sources'] = 1
					self.entry['state_database_where'] = 4		#TODO, list
					self.ask("Do they cite the database?","database_cited")		#TODO, what does it mean to site a database?
					return
		self.entry['state_data_sources'] = 0

	def _get_query(self,text):
		self.entry['query_script_shared'] = 0
		for each_sent in nltk.sent_tokenize(text):		#TODO, how to tell??
			if (re.search(r'abstracted',each_sent,re.I) or 
					re.search(r'manual',each_sent,re.I) or 
					re.search(r'query',each_sent,re.I) or 
					(re.search('records',each_sent,re.I) and re.search('review',each_sent,re.I))):
				self.check_boolean("Query Method Stated",1,"yes",each_sent,"query_method_stated")
			if ('query_method_stated' in self.entry):
				self.entry['query_method_location'] = 4			#TODO
				return
		self.entry['query_method_stated'] = 0

	def _get_nlp(self,text):
		for each_sent in nltk.sent_tokenize(text):
			if (re.search(r'language\spro',each_sent,re.I) or re.search(r'\snlp\s',each_sent,re.I)):
				self.check_boolean("Research Involves Natural Language Processing",1,"yes",each_sent,"text_nlp_yn")
				if ("text_nlp_yn" in self.entry):
					if (self.ask_without_choices("Does the publication state source of the text from which data were mined? (ex: emergency department summary, operative notes, etc)\n","Enter the source of text: ","text_mine_source")):					
						if (re.search(r'appendix',each_sent,re.I)):
							if (self.check_boolean("Manuscript shares a pre-processed sample text source in",9,"appendix",each_sent,"nlp_source_shared_loc")):
								self.assign("text_mining_preprocess",1)
						elif (re.search(r'\Wgit',each_sent,re.I)):
							if (self.check_boolean("Manuscript shares a pre-processed sample text source in",5,"GitHub",each_sent,"nlp_source_shared_loc")):
								self.assign("text_mining_preprocess",1)
						if ("text_mining_preprocess" not in self.entry):
							if (self.ask_question("Do they share a pre-processed sample of the text source?")):
								self.assign("text_mining_preprocess",1)
								self.ask("Where is the sample shared?","nlp_source_shared_loc")
					#self.nlp_validation()		#TODO
						if (self.ask_without_choices("Does the publication state software used for text mining?","Enter softwares used: ","nlp_software")):
							self.ask("Is the software open or proprietary?","nlp_software_open")
						return

	def _get_analysis(self,text):
		for each_sent in nltk.sent_tokenize(text):
			if (re.search(r'statistical analys[ie]s',each_sent,re.I) or re.search(r'data analys[ie]s',each_sent,re.I)):
				if (self.check_boolean("Publications States Analysis Methodology And Process",1,"yes",each_sent,"analysis_processes_clear")):
					self.entry['data_analysis_doc_loc'] = 4
					return



	def _get_stats(self,text):
		self.check_standards(text)
		if ("analysis_sw" in self.entry):
			self.entry['software_analysis_code'] = 1
			return

		for each_sent in nltk.sent_tokenize(text):
			search = re.search(r'analys[ie]s (were)?(was)? performed\s+\w+\W+(.*?)\s',each_sent,re.I)
			if (search):
				self.check("Analyses Software",search.group(3).strip(),search.group(3).strip(),each_sent,"analysis_sw")
			#if (not search):
			#	search = re.search(r'analys',each_sent,re.I) and re.search(r'\s(.*?)\swas used',each_sent,re.I)
			#	if (search):
			#		self.check("Analyses Software",search.group(1).strip(),search.group(1).strip(),each_sent,"analysis_sw")
			else:
				search = re.search(r'analys',each_sent,re.I) and re.search(r'were\s\w*\susing\s(.*?)\s',each_sent,re.I)
				if (search):
					self.check("Analyses Software",search.group(1),search.group(1),each_sent,"analysis_sw")
			if ("analysis_sw" in self.entry):
				self.entry['software_analysis_code'] = 1

				search = re.search(self.entry['analysis_sw'] + r'.*?(\d[\d\.]*\d)',each_sent,re.I|re.S)
				if (search):
					self.check("Analysis Software Version",search.group(1),search.group(1),each_sent,"analysis_sw_version")
				self.check_operating_system(each_sent)
				return
		self.entry['software_analysis_code'] = 2	
		
	def check_standards(self,text):
		stands = ["STATA","SAS","SPSS"]
		for each_sent in nltk.sent_tokenize(text):
			for stand in stands:
				if re.search(stand,each_sent):
					self.check("Analysis Software",stand,stand,each_sent,"analysis_sw")
					if ("analysis_sw" in self.entry and stand in self.entry['analysis_sw']):
						self.entry['analysis_software_open'] = 1		#TODO, how to enter in redcap
						search = re.search(stand + r'.*?(\d[\d\.]*\d)',each_sent)
						if (search):
							self.check("Analysis Software Version",search.group(1),search.group(1),each_sent,"analysis_sw_version")
						self.check_operating_system(each_sent)
			if (re.search(r'analys',each_sent,re.I) and re.search(r'\sR\s',each_sent)):
				self.check("Analysis Software","R","R",each_sent,"analysis_sw")
				if ("analysis_sw" in self.entry and "R" in self.entry['analysis_sw']):
					search = re.search(r'\sR\s.*?(\d[\d\.]*\d)',each_sent)
					if (search):
						self.check("Analysis Software Version",search.group(1),search.group(1),each_sent,"analysis_sw_version")
					self.entry['analysis_software_open'] = 2
					search = re.search(r'\sR\s.*?(\d[\d\.]*\d)',each_sent)
					self.ask_without_choices("Does the publication list the operating system used in analyses?","Type the operating system used: ","analysis_os")

	def check_operating_system(self,text):
		if (re.search(r'windows',text,re.I)):
			self.check_boolean("Operating System Used For Analyses",'Windows','Windows',text,"analysis_os")
			if ("analysis_os" in self.entry):
				return
		if (self.ask_question("Do they cite what operating system they used?")):
			self.ask("What operating system was used for analyses?","analysis_os")

	def _get_limitations(self,text):
		for each_sent in nltk.sent_tokenize(text):
			if (re.search(r'shortcomings',each_sent,re.I) or re.search(r'limitation',each_sent,re.I) or re.search(r'(was)?(is)? limited',each_sent,re.I)):
				self.check_boolean("Publication Documents Limitations Of The Study",7,"yes",each_sent,"limitations_where")
				if ("limitations_where" in self.entry):
					return

	def _get_primary_research(self,text):
		return
		#TODO, run machine learning algorithm on text

	def _get_clear_analysis(self,text):
		return
		#TODO, run machine learning algorithm on text


	def xml_extract(self):
		
		doi = journalName = firstName = lastName = email = articleTitle = ""

		journalName = self.try_xml(self.xml,['PubmedArticle','MedlineCitation','Article','Journal','Title'])
		date = self.try_xml(self.xml,['PubmedArticle','MedlineCitation','Article','ArticleDate'])
		#print self.xml['PubmedArticle']['MedlineCitation']['Article']
		day = self.try_xml(date,['Day'])
		month = self.try_xml(date,['Month'])
		year = self.try_xml(date,['Year'])
		publisher = self.try_xml(self.xml,['PubmedArticle','MedlineCitation','Article','Abstract','CopyrightInformation'])

		EIDs = self.try_xml(self.xml,['PubmedArticle','MedlineCitation','Article','ELocationID'])
		try:
			if EIDs["@EIdType"] == "doi":
				doi = EIDs['#text']
		except TypeError:
			for EID in EIDs:
				if EID["@EIdType"] == "doi":
					doi = EID['#text']

		article = self.try_xml(self.xml,['PubmedArticle','MedlineCitation','Article'])
		articleTitle = self.try_xml(article,['ArticleTitle'])

		if (isinstance(self.try_xml(article,['AuthorList','Author']),list)):
			firstAuthor = self.try_xml(article,['AuthorList','Author'])[0]
		else:
			firstAuthor = self.try_xml(article,['AuthorList','Author'])
		lastName = self.try_xml(firstAuthor,['LastName'])
		firstName = self.try_xml(firstAuthor,['ForeName'])
		institution = self.try_xml(firstAuthor,['AffiliationInfo','Affiliation'])
		if ('@' in institution):
			search = re.search(r'\s((\w|\.)+@.+)',institution);
			email = search.group(1);
			if ('Electronic address:' in institution):
				search = re.search(r'(.*) Electronic address:',institution)
				institution = search.group(1);
			else:
				search = re.search(r'(.*)\s.+@',institution)
				institution = search.group(1);
		else:
			email = ""
		self.institution = institution

		if (month and day and year):
			self.entry = {
				'article_doi':doi,
				'journal_publication':journalName,
				'publication_date':"{0}-{1}-{2}".format(month,day,year),
				'author_fn':firstName,
				'author_ln':lastName,
				'author_email':email,
				'article_title':articleTitle,
			}
		else:
			self.entry = {
				'article_doi':doi,
				'journal_publication':journalName,
				'author_fn':firstName,
				'author_ln':lastName,
				'author_email':email,
				'article_title':articleTitle,
			}

	def try_xml(self,xml,layers):
		data = xml
		try:
			while layers and data:
				layer = layers.pop(0)
				data = data[layer]
			return data
		except KeyError as e:
			#print(e)
			return ""
		except TypeError as e:
			#print(e)
			return self.try_xml(data,[0] + [layer] + layers)

	def _get_institution(self):
		af_from_xml = self.institution.split(", ")

		for option in af_from_xml:		#could tweak slightly
			if (re.search(r'hospital',option,re.I) or re.search(r'university',option,re.I) or re.search(r'school',option,re.I) or re.search(r'college',option,re.I) or re.search(r'institute',option,re.I)):
				self.check("Institution",option,option,self.institution,"institution_corr_author")
			if ("institution_corr_author" in self.entry):
				return
		try:
			self.check("Institution",af_from_xml[1],af_from_xml[1],self.institution,"institution_corr_author")
		except IndexError:
			pass

	def get_clinical_domain_from_xml(self):
		#TODO, chooser doesnt have scrollbar
			#option is to switch check to check_boolean if run out of time

		def _clinical_asides(afs):
			department = division = ""
			for option in afs:
				search = re.search(r'departments? of(.*)',option,re.I)
				if (search):
					department = search.group(1).strip()
				search = re.search(r'division of(.*)',option,re.I)
				if (search):
					division = search.group(1).strip()
			return (department,division)

		af_from_xml = self.institution.split(", ")
		(department, division) = _clinical_asides(af_from_xml)

		cd_from_department = self.get_clinical_domain(department.split())
		if (cd_from_department):
			self.check("Clinical Domain",self.get_choices("clinical_domain")[cd_from_department],cd_from_department,"Department: {0}".format(department),"clinical_domain")

		cd_from_division = self.get_clinical_domain(division.split())
		if (cd_from_division):
			self.check("Clinical Domain",self.get_choices("clinical_domain")[cd_from_division],cd_from_division,"Division: {0}".format(division),"clinical_domain")


		cd_from_journal = self.get_clinical_domain(self.entry['journal_publication'].split())
		if (cd_from_journal):
			self.check("Clinical Domain",self.get_choices("clinical_domain")[cd_from_journal],cd_from_journal,"Journal Title: " + self.entry['journal_publication'],"clinical_domain")

		cd_from_title = self.get_clinical_domain(self.entry['article_title'].split())
		if (cd_from_title):
			self.check("Clinical Domain",self.get_choices("clinical_domain")[cd_from_title],cd_from_title,"Article Title: " + self.entry['article_title'],"clinical_domain")