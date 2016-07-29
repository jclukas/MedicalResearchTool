#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from Article import RawArticle
from Query import Query
import json
import nltk
from pprint import pprint
import random
import re



class Trainer(object):
	def __init__(self,redcap,articles,searchwords):
		self.articles = articles
		self.allwords = searchwords
		self.train(redcap)
		

	def train(self,redcap):
		print("training")
		pubmed = json.loads(open("pubmed.json").read())
		ml_data = Query().get_ml_data(redcap)
		#pprint(ml_data)		#print records and their corresponding ml values (0 or 1)
		train = []
		featuresset = []

		for each_article in self.articles:
			art = RawArticle(each_article)
			try:
				#tup = (list(nltk.word_tokenize(art.text.lower())),ml_data[str(pubmed[each_article]['record'])]=='1')
				#train.append(tup)
				featuresset.append(({word: 1 if re.search(word,art.text.lower()) else 0 for word in self.allwords},ml_data[str(pubmed[each_article]['record'])]=='1'))
			except KeyError:
				print("couldnt find article with record_id: {0}".format(each_article))

		acc = []
		for i in range(1000):
			random.shuffle(featuresset)
			trainset = featuresset[:-7]
			testset = featuresset[-7:]
			classifier = nltk.NaiveBayesClassifier.train(trainset)
			acc.append(nltk.classify.accuracy(classifier,testset))
			#classifier.show_most_informative_features(10)

		print(sum(acc)/len(acc))


		
