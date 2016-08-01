#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys, re
sys.path.append("{0}/Desktop/cbmi/reproduce/python/MedicalResearchTool/objects".format(os.environ['HOME']))
sys.path.append("{0}/Desktop/cbmi/reproduce/python/MedicalResearchTool".format(os.environ['HOME']))

import requests, xmltodict, bs4

class XMLExtractor(object):
	"""
	Depends on imported modules:
		requests		-- http://docs.python-requests.org/en/master/
		xmltodict 		-- https://github.com/martinblech/xmltodict
	See documentation for more information
	"""

	def xml_load(self,site : 'string - url where xml data lives') -> 'collections.OrderedDict':
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
		"""
		Get xml data on an article
		Args: url address (string)
		Return: ordered dictionary of xml data
				0 to indicate an error occurred

		Example:
		>>> xe = XMLExtractor()
		>>> xe.xml_load("http://www.ncbi.nlm.nih.gov/pubmed/24433938?report=xml&format=text")
		OrderedDict([('pre',
              OrderedDict([('PubmedArticle',
                            OrderedDict([('MedlineCitation',
                                          OrderedDict([('@Owner', 'NLM'),
                                                       ('@Status', 'MEDLINE'),
                                                       ('PMID',
                                                        OrderedDict([('@Version',
                                                                      '1'),
                                                                     ('#text',
                                                                      '24433938')])),
                                                                      ...

		Requests manages error handling
		>>> xe.xml_load("this is not a valid url")
		request to site: 'this is not a valid url'
		failed. error information from requests:
			 Invalid URL 'this is not a valid url': No schema supplied. Perhaps you meant http://this is not a valid url?
		0
		"""
		try:
			xml_text = requests.get(site).text
			xml_text = re.sub(r'&lt;',"<",xml_text)
			xml_text = re.sub(r'&gt;',">",xml_text)
			#unescape(requests.get(site).text,{"&lt;":"<", "&gt;":">"})		<--- alternate to above regex
			data = self.parse_xml(xml_text)
			if (not data):
				print("xml could not be interpretted for site: {}".format(site))
				return 0
			return data
		except Exception as e:
			print("request to site: '{}'\nfailed. error information from requests:".format(site))
			print("\t",e)
			return 0

	def parse_xml(self,xml : 'string - xml formatted string') -> 'collections.OrderedDict':
		"""
		Parse an xml string
		Args: string to be parsed
		Return: ordered dictionary of xml data
				0 to indicate an error occurred

		Example:
		>>> xe = XMLExtractor()
		>>> xml = xe.parse_xml("<ImportantInformation><BestDinosaur>triceratops</BestDinosaur><BestCountry>Ireland</BestCountry></ImportantInformation>")
		>>> xml
		OrderedDict([('ImportantInformation',
		              OrderedDict([('BestDinosaur', 'triceratops'),
		                           ('BestCountry', 'Ireland')]))])
		>>> xml['ImportantInformation']
		OrderedDict([('BestDinosaur', 'triceratops'), ('BestCountry', 'Ireland')])
		>>> xml['ImportantInformation']['BestDinosaur']
		triceratops

		xmltodict manages error handling
		>>> xe.parse_xml(<tag 1>"The Soviet Onion"</tag 1>)
		xml parse failed on line:
		<tag 1>The Soviet Onion</tag 1>
		error information from requests: 
			not well-formed (invalid token): line 1, column 5
		"""
		try:
			data = xmltodict.parse(xml)
		except Exception as e:
			search = re.search(r'line (\d+), column (\d+)',e.args[0])
			print("xml parse failed on line:\n{}".format(xml.split('\n')[int(search.group(1))-1]))
			print("error information from requests: \n\t{}".format(e))
			return 0
		return data

	def xml_extract(self,xml : 'dictionary - xml data from ncbi site') -> 'dictionary':
		"""
		Extract redcap fields from the xml dictionary
		Args: xml data (dictionary)
		Return: dictionary of redcap data
				empty dictionary if errors occur
		"""
		
		if (not xml):
			#likely, xml download failed because invalid url or misformatted data (user has already been notified in xml_load or parse_xml method calls)
			#return empty dictionary so that redcap entry doesnt throw errors
			return {}
		if (type(xml) is not dict):
			#verify xml is a dictionary
			print("xml_extract called on invalid argument: '{}'\n type of arg is: {} but should be a dictionary".format(xml,type(xml)))
			#return empty dictionary so that redcap entry doesnt throw errors
			return {}

		#initialize fields to empty strings to prevent 'reference before instantiation errors'
		doi = journalName = firstName = lastName = email = articleTitle = ""

		journalName = self.try_xml(xml,['PubmedArticle','MedlineCitation','Article','Journal','Title'])
		date = self.try_xml(xml,['PubmedArticle','MedlineCitation','Article','ArticleDate'])
		day = self.try_xml(date,['Day'])
		month = self.try_xml(date,['Month'])
		year = self.try_xml(date,['Year'])
		publisher = self.try_xml(xml,['PubmedArticle','MedlineCitation','Article','Abstract','CopyrightInformation'])

		#EID may be list
		EIDs = self.try_xml(xml,['PubmedArticle','MedlineCitation','Article','ELocationID'])
		try:
			if EIDs["@EIdType"] == "doi":
				doi = EIDs['#text']
		except TypeError:
			for EID in EIDs:
				if EID["@EIdType"] == "doi":
					doi = EID['#text']

		article = self.try_xml(xml,['PubmedArticle','MedlineCitation','Article'])
		articleTitle = self.try_xml(article,['ArticleTitle'])

		if (isinstance(self.try_xml(article,['AuthorList','Author']),list)):
			firstAuthor = self.try_xml(article,['AuthorList','Author'])[0]
		else:
			firstAuthor = self.try_xml(article,['AuthorList','Author'])

		#redcap only allows alpha characters for first and last name. sub out invalid characters
		lastName = re.sub('[\W_\s]','',self.try_xml(firstAuthor,['LastName']))
		firstName = re.sub('[\W_\s]','',self.try_xml(firstAuthor,['ForeName']))

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

		#of these fields, only publication_date has formatting restrictions
		if (month and day and year):
			return ({
				'article_doi':doi,
				'journal_publication':journalName,
				'publication_date':"{0}-{1}-{2}".format(year,month,day),
				'author_fn':firstName,
				'author_ln':lastName,
				'author_email':email,
				'article_title':articleTitle,
			})
		else:
			return ({
				'article_doi':doi,
				'journal_publication':journalName,
				'author_fn':firstName,
				'author_ln':lastName,
				'author_email':email,
				'article_title':articleTitle,
			})

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