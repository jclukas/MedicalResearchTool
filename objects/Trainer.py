#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from Article import RawArticle,XMLArticle
from DatabaseManager import DatabaseManager
from ArticleManager import ArticleManager
import json
import nltk
from pprint import pprint
import random
import re
import sys

from bs4 import BeautifulSoup



class Trainer(object):
	#cant do redcap as *redcap because text to be searched could be from methods, discussion, etc
	def __init__(self,redcap,articles,searchwords=[]):
		self.articles = articles
		#ml_data = DatabaseManager().get_ml_data(redcap)
		ml_data = "filler"
		if (not searchwords):
			self.allwords = self.get_allwords()
		else:
			self.allwords = searchwords
		self.train(redcap,ml_data)

	def get_allwords(self):
		allwords = []

		"""
		for each_article in self.articles:
			#art = RawArticle("articles/{}".format(each_article))
			xmlfile = "/Users/christian/Desktop/cbmi/reproduce/python/articles/sub_pmc_result.xml"
			try:
				art = XMLArticle(ArticleManager().read_xml(xmlfile,'doi',each_article),1,each_article,'doi')
			except TypeError as e:
				#article not found or not open access
				continue
			try:
				#allwords.extend([word for word in nltk.word_tokenize(art.text) if word not in nltk.corpus.stopwords.words('english')])
				allwords.extend([word for word in nltk.word_tokenize(art.bs.text) if word not in nltk.corpus.stopwords.words('english')])
			except TypeError as e:
				#article not found
				pass

			#xmltext = ArticleManager().read_xml(file,identifier,each_article)
			#allwords.extend([word for word in nltk.word_tokenize(xmltext.text) if word not in nltk.corpus.stopwords.words('english')])
			#example of how Trainer could be used on xml articles
		"""
		with open("/Users/christian/Desktop/cbmi/reproduce/python/articles/sub_pmc_result.xml",'r') as x:
			bs = BeautifulSoup(x.read(),'lxml')

		closed = 0
		doi = 0
		for ass in bs.find_all('article'):
			if (ass.find(text=re.compile("The publisher of this article does not allow downloading of the full text in XML form"))):
				#article isnt open access :(
				closed += 1
				continue
			try:
				art = XMLArticle(str(ass),1,ass.find('article-id',{'pub-id-type':'doi'}).text,'doi')
				allwords.extend([word for word in nltk.word_tokenize(art.bs.body.text) if word not in nltk.corpus.stopwords.words('english')])
			except AttributeError as e:
				#no doi
				doi += 1
				continue

		print(closed, doi)

		allwords = list(set(allwords))
		return allwords

	def get_features(self,text):
		return {word: 1 if re.search(re.escape(word),text,re.I) else 0 for word in self.allwords}


	def train(self,redcap,ml_data):
		print("training")
		print(len(self.allwords))
		pubmed = json.loads(open("pubmed.json").read())
		train = []
		featuresset = []

		numwords = len(self.allwords)
		usewords = sorted(list(set(self.allwords)),key=self.allwords.count,reverse=True)[:int(numwords/1.5)]

		arts = []
		with open("/Users/christian/Desktop/cbmi/reproduce/python/articles/xmlarticlefile.txt",'r') as x:
			arts = x.read().split()


		#for each_article in self.articles:
		with open("/Users/christian/Desktop/cbmi/reproduce/python/articles/sub_pmc_result.xml",'r') as x:
			bs = BeautifulSoup(x.read(),'lxml')

		all_arts = 0
		for ass in bs.find_all('article'):
			if (ass.find(text=re.compile("The publisher of this article does not allow downloading of the full text in XML form"))):
				#article isnt open access :(
				continue
			try:
				doi = ass.find('article-id',{'pub-id-type':'doi'}).text.strip()
			except AttributeError as e:
				#no doi
				print('no doi')
				continue
			#art = RawArticle("articles/{}".format(each_article))
			art = 0
			try:
				art = XMLArticle(str(ass),1,doi,'doi')
			except TypeError as e:
				#article not found or not open access
				print('couldnt find article with doi: '.format(doi))
				continue



			#art = XMLArticle(ArticleManager().read_xml(file,identifier,each_article),1,each_article,identifier,metadata=metadata)
			#ex: art = XMLArticle(ArticleManager().read_xml('articles/sub_pmc_resul.xml','pmid',26781389),1,26781389,'pmid')
			#example of how Trainer could be applied to xml articles



			try:
				#featuresset.append(({word: 1 if re.search(re.escape(word),art.text,re.I) else 0 for word in usewords},ml_data[str(pubmed[each_article]['record'])]=='1'))
				#featuresset.append(({word: 1 if re.search(re.escape(word),art.bs.text,re.I) else 0 for word in self.allwords},ml_data[str(pubmed[each_article]['record'])]=='1'))
				featuresset.append(({word: 1 if re.search(re.escape(word),art.bs.body.text,re.I) else 0 for word in self.allwords},1 if doi in arts else 0))
				#example of how Trainer could be applied to xml articles
			except KeyError:
				print("couldnt find article with record_id: {0}".format(doi))
				continue
			all_arts += 1
			print(all_arts)

		#print(featuresset[:int(len(featuresset)/10)])
		#print(featuresset)
		print(len(featuresset))

		acc = []
		for i in range(200):
			if (i%25 == 0):
				print(i)
			random.shuffle(featuresset)
			trainset = featuresset[:-1]
			testset = featuresset[-1:]
			#classifier = nltk.NaiveBayesClassifier.train(trainset)
			classifier = nltk.NaiveBayesClassifier.train(featuresset)
			break

			accuracy = nltk.classify.accuracy(classifier,testset)
			acc.append(accuracy)
		#print(sum(acc)/len(acc))

		with open("/Users/christian/Desktop/cbmi/reproduce/python/articles/pmc_result.xml",'r') as x:
			bs = BeautifulSoup(x.read(),'lxml')
		for ass in bs.find_all('article'):
			if (ass.find(text=re.compile("The publisher of this article does not allow downloading of the full text in XML form"))):
				#article isnt open access :(
				continue
			try:
				doi = ass.find('article-id',{'pub-id-type':'doi'}).text.strip()
			except AttributeError as e:
				#no doi
				continue
			try:
				art = XMLArticle(str(ass),1,doi,'doi')
			except TypeError as e:
				#article not found or not open access
				print('couldnt find article with doi: '.format(doi))
				continue
			if (classifier.classify(self.get_features(art.bs.body.text))):
				print(doi)
