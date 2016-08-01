#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from ArticleExtractor import ArticleExtractor
from XMLExtractor import XMLExtractor
from bs4 import BeautifulSoup
import re,sys
import textract, nltk

text = "filler"

class RawArticle(ArticleExtractor):
	def __init__(self,pubmed):
		self.pubmed_code = pubmed
		self.text = self.get_text()


	def get_text(self):		#TODO, clean up or remove proper nouns
		pdf_file = "articles/" + self.pubmed_code + ".pdf"
		
		text = textract.process(pdf_file)
		text = text.strip()
		text = re.sub(b'\n+',b" ",text)
		text = re.sub(b'\s+',b" ",text)
		if (re.search(b'(.*)references',text,re.I)):
			search = re.search(b'(.*?)\Wreferences',text,re.I)
			if (search):
				text = search.group(1)
			else:
				print("check reference")

			#TODO
		"""
		words = nltk.word_tokenize(text.decode('utf-8'))
		tagged = nltk.pos_tag(words)
		newwords = []
		print len(tagged)
		for word,part in tagged:
			if (re.search(r'NNP.?',part)):
				newwords.append(re.sub(r'\.','',word))
			else:
				newwords.append(word)
		text = ' '.join([word for word in newwords])
		text = re.sub(r'\s\.','.',text)
		print text
		sys.exit()
		"""

		return text.decode()
		#self.sents = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s',text)

class PMCArticle(ArticleExtractor,XMLExtractor):

	#TODO, fix here and others so that metadata has default if none provided
	def __init__(self,pubmed,run_style,metadata):
		self.pubmed_code = pubmed
		self.indi = run_style
		self.entry = {}
		#self.extra = {}
		super(PMCArticle,self).__init__(metadata)		#TODO, change elsewhere if this works

		#self.fulltext = self.load_text().text 			#for pmc using online xml
		self.fulltext = pubmed 			#change to 'text' or something similar if stick with xml format
		self.bs = BeautifulSoup(self.fulltext,"lxml")

	def load_text(self):
		ids = self.xml['PubmedArticle']['PubmedData']['ArticleIdList']['ArticleId']
		for each_id in ids:
			if (each_id['@IdType'] == "pmc"):
				pmc = each_id['#text']
		try:
			return requests.get("{0}pmc/articles/{1}/?report=reader".format(ncbi_site,pmc))
		except UnboundLocalError as e:
			print(e)
			print("not a pmc article, maybe closed source?")
			raise

	def section(self,sections,tag):
		tags = self.bs.find_all(tag)
		for tag in tags:
			for section in sections:
				if (re.search(section,tag.get_text(),re.I)):
					sect = re.sub(r'title','',tag.get('id'))
		try:
			return self.bs.div(id=sect)[0]
		except UnboundLocalError as e:
			#couldnt find sect
			return self.bs

	def search(self,regex):
		try:
			return self.bs.find(text=regex).parent.parent
		except IndexError:
			#regex search returned no results
			return self.bs
		except AttributeError:
			#match occurred at top level of tree
			return self.bs

	def xml_section(self,*titles):
		body = self.bs.body
		for title in titles:
			if (body.find("sec",{"sec-type":title})):
				return body.find("sec",{"sec-type":title}).text
			if (body.find("title",text=title)):
				return body.find("title",text=re.compile(title,re.I)).parent.text
		return body.text		#unable to find section




	
	def download_pdf(self):
		"""
		if (not os.path.isdir("articles/")):
			os.makedirs("articles/")

		ids = self.xml['PubmedArticle']['PubmedData']['ArticleIdList']['ArticleId']
		for each_id in ids:
			if (each_id['@IdType'] == "pmc"):
				pmc = each_id['#text']

		xml = self.xml_load(ncbi_site + "pmc/" + pmc_tag + pmc)
		links = xml['OA']['records']['record']['link']
		for link in links:
			print(link)
			if (link['@format'] == 'pdf'):
				href = link['@href']
		print(href)
		bashCommand = "wget " + href
		subprocess.run(bashCommand.split())

		bashCommand = "mv " + href.split('/')[-1] + " " + self.pubmed_code + ".pdf"
		subprocess.run(bashCommand.split())
		"""
		return

	def get_hypotheses(self):
		return self._get_hypotheses(self.xml_section('background','introduction'))
		return self._get_hypotheses(self.section(["background","introduction"],"h2").get_text())

	def get_funding(self):		#nltk could improve; low priority now though
		#self.bs.find_all(string=re.compile(r'fund[ie]'))
		return self._get_funding(self.search(re.compile(r'funded.*?by',re.I)).get_text())

	def get_inex_criteria(self):	#TODO, expand
		return self._get_inex_criteria(self.xml_section('methods'))
		return self._get_inex_criteria(self.section(["methods"],"h2").get_text())

	def get_ontol_vocab(self): #TODO, if ontol occurs outside of inclusion / exclusion
		return	#TODO
		return self._get_ontol_vocab(text)

	def get_databases(self):
		return self._get_databases(self.xml_section('methods'))
		return self._get_databases(self.section(["methods"],"h2").get_text())

	def get_query(self):
		return #TODO
		return self._get_query(self.fulltext)
		self.entry['query_script_shared'] = 0

	def get_nlp(self):
		return self._get_nlp(self.xml_section('methods'))
		return self._get_nlp(self.section(["methods"],"h2").get_text())

	def get_analysis(self):
		return #TODO
		return self._get_analysis(text)

	def get_stats(self):
		return #TODO
		return self._get_stats(text)

	def get_limitations(self):
		return self._get_limitations(self.xml_section('discussion','conclusion'))
		return #TODO
		return self._get_limiations(text)

	def get_primary_research(self):
		return #TODO
		return self._get_primary_research(text)
		#TODO, run machine learning algorithm on text

	def get_clear_analysis(self):
		return #TODO
		return self._get_clear_analysis(text)
		#TODO, run machine learning algorithm on text

	def get_institution(self,institution):
		return #TODO
		return self._get_institution(institution)

class ClosedArticle(ArticleExtractor,XMLExtractor):

	def __init__(self,pubmed,run_style,metadata):
		self.pubmed_code = pubmed
		self.indi = run_style
		self.metadata = metadata
		self.entry = {}
		self.extra = {}
		self.text = RawArticle(pubmed).get_text()
	
	def get_clinical_domain_from_pdf(self):
		for each_sent in nltk.sent_tokenize(self.text):
			search = re.search(r'key.*?words(.*)',each_sent,re.I)
			if (search):
				key_words = re.sub(r'[()]',"",search.group(1))
				key_words = key_words.split()
				self.get_clinical_domain(key_words)

	def get_hypotheses(self):
		return self._get_hypotheses(self.text)

	def get_funding(self):		#nltk could improve; low priority now though
		#self.bs.find_all(string=re.compile(r'fund[ie]'))
		return self._get_funding(self.text)

	def get_inex_criteria(self):	#TODO, expand
		return self._get_inex_criteria(self.text)

	def get_ontol_vocab(self): #TODO, if ontol occurs outside of inclusion / exclusion
		return #TODO
		return self._get_ontol_vocab(self.text)

	def get_databases(self):
		return self._get_databases(self.text)

	def get_query(self):
		return self._get_query(self.text)
		self.entry['query_script_shared'] = 0

	def get_nlp(self):
		return self._get_nlp(self.text)

	def get_stats(self):
		return self._get_stats(self.text)

	def get_limitations(self):
		return self._get_limitations(self.text)

	def get_primary_research(self):
		return self._get_primary_research(self.text)
		#TODO, run machine learning algorithm on text


	def get_analysis(self):
		return
		return self._get_analysis(self.text)
	# ^ same 	
	def get_clear_analysis(self):
		return
		return self._get_clear_analysis(self.text)
		#TODO, run machine learning algorithm on text

	def get_institution(self,institution):
		return self._get_institution(institution)

	
	
"""
	def get_databases():

		def get_new_text(text):
			search = re.search(r'Conclusion(.*)',text)
			if (search):
				return search.group(1)
			else:
				return text

		new_text = get_new_text(self.text)

		new_sents = nltk.tokenize.sent_tokenize(new_text)
		found_methods = 0
		for each_sent in new_sents:
			if (re.search(r'Methods',each_sent) or re.search(r'METHODS',each_sent)):
				found_methods = 1
			if (found_methods == 1):
				return
"""
