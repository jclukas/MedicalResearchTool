#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys, re
sys.path.append("{0}/Desktop/cbmi/reproduce/python/MedicalResearchTool/objects".format(os.environ['HOME']))
sys.path.append("{0}/Desktop/cbmi/reproduce/python/MedicalResearchTool".format(os.environ['HOME']))

import requests, xmltodict

class XMLExtractor(object):

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


	def xml_extract(self,xml):
		
		doi = journalName = firstName = lastName = email = articleTitle = ""

		journalName = self.try_xml(xml,['PubmedArticle','MedlineCitation','Article','Journal','Title'])
		date = self.try_xml(xml,['PubmedArticle','MedlineCitation','Article','ArticleDate'])
		#print xml['PubmedArticle']['MedlineCitation']['Article']
		day = self.try_xml(date,['Day'])
		month = self.try_xml(date,['Month'])
		year = self.try_xml(date,['Year'])
		publisher = self.try_xml(xml,['PubmedArticle','MedlineCitation','Article','Abstract','CopyrightInformation'])

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