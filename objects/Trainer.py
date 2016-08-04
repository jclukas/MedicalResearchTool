#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from Article import RawArticle
from Redcap import Redcap
import json
import nltk
from pprint import pprint
import random
import re



class Trainer(object):
	def __init__(self,redcap,articles,searchwords=[]):
		self.articles = articles
		ml_data = Redcap().get_ml_data(redcap)
		if (not searchwords):
			self.allwords = self.get_allwords()
		else:
			self.allwords = searchwords
		self.train(redcap,ml_data)

	def get_allwords(self):
		allwords = []
		for each_article in self.articles:
			art = RawArticle("articles/{}".format(each_article))
			try:
				allwords.extend([word for word in nltk.word_tokenize(art.text) if word not in nltk.corpus.stopwords.words('english')])
			except TypeError as e:
				#article not found
				pass
		allwords = list(set(allwords))
		return allwords

	def train(self,redcap,ml_data):
		print("training")
		pubmed = json.loads(open("pubmed.json").read())
		train = []
		featuresset = []


		for each_article in self.articles:
			art = RawArticle("articles/{}".format(each_article))
			numwords = len(self.allwords)
			useword = sorted(self.allwords,key=self.allwords.count,reverse=True)[int(numwords/1.5)]
			try:
				featuresset.append(({word: 1 if re.search(re.escape(word),art.text) else 0 for word in self.allwords},ml_data[str(pubmed[each_article]['record'])]=='1'))
			except KeyError:
				print("couldnt find article with record_id: {0}".format(each_article))

		acc = []
		for i in range(100):
			if (i%50 == 0):
				print(i)
			random.shuffle(featuresset)
			trainset = featuresset[:-7]
			testset = featuresset[-7:]
			classifier = nltk.NaiveBayesClassifier.train(trainset)
			acc.append(nltk.classify.accuracy(classifier,testset))
			#classifier.show_most_informative_features(10)
		print(sum(acc)/len(acc))
