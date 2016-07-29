#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from tkinter import *

import sys, re, os
sys.path.append("{0}/Desktop/cbmi/reproduce/python/MedicalResearchTool/objects".format(os.environ['HOME']))
sys.path.append("{0}/Desktop/cbmi/reproduce/python/MedicalResearchTool".format(os.environ['HOME']))

import pycurl, io, json
from pprint import pprint
from bs4 import BeautifulSoup
from Query import Query

class ArticleManager(object):

	def __init__(self,metadata=Query().get_metadata()):
		self.indi = 0
		self.verify_meta(metadata)
		self.metadata = metadata

	def verify_meta(self,metadata):
		example = """[{'select_choices_or_calculations': '', 'field_type': 'text', 'field_label': 'Record ID', 'field_name': 'record_id'},
{'select_choices_or_calculations': '1, Hypothesis Driven | 2, Hypothesis Generating | 3, Unclear', 'field_type': 'radio', 'branching_logic': '', 'field_label': 'Is the research hypothesis-driven or hypothesis-generating?', 'field_name': 'hypothesis_gen_or_driv'}"""
		if (type(metadata) is not list):
			raise TypeError("metadata must be type 'list' but is type: {0} \n\nmetadata: {1} \nexample metadata: {2}".format(type(metadata),metadata,example))
		for item in metadata:
			if (type(item) is not dict):
				raise TypeError("each list-item of metadata must be a dict but item: {} is type: {}\nexample metadata: {}".format(item,type(item),example))
			try:
				item['field_name']
				item['field_type']
				item['select_choices_or_calculations']
			except KeyError as e:
				raise KeyError("""each list-item in metadata must contain at least the keys: 1) 'field_name', 2) 'field_type', 3) 'select_choices_or_calculations' 
									.\nitem: {}\nexample metadata: {}""".format(item,example))

	#could do
	#def enter_redcap(self,entry,**kwargs)
	#so can only overwrite record_id if user provides record_id
	def enter_redcap(self,entry,record_id=0):
		#entry['record_id'] = record_id			#leave out for now so I dont destroy redcap...
		entry['record_id'] = '9b7057f5f8894c9c'

		from config import config
		buf = io.BytesIO()
		data = json.dumps([entry])
		fields = {
		    'token': config['api_token'],
		    'content': 'record',
		    'format': 'json',
		    'type': 'flat',
		    'data': data,
		}

		ch = pycurl.Curl()
		ch.setopt(ch.URL, config['api_url'])
		ch.setopt(ch.HTTPPOST, list(fields.items()))
		ch.setopt(ch.WRITEFUNCTION, buf.write)
		ch.perform()
		ch.close()

		self.redcap_return = buf.getvalue()
		buf.close()
		if (re.search(b'error',self.redcap_return)):
			splitreturn = self.redcap_return.split(b'\\"')
			fail_field = splitreturn[3].decode()
			fail_reason = splitreturn[7].decode()
			print("redcap entry failed on field: '{}'' \nbecause: '{}'".format(fail_field,fail_reason))
			if (self.ask_question("Would you like to edit field: '{}'".format(fail_field))):
				entry[fail_field] = self.ask("What is the value of {}?".format(fail_field),fail_field)
				return self.enter_redcap(entry,record_id)
			else:
				print("retrying entry without that field")
				del entry[fail_field]
				return self.enter_redcap(entry,record_id)
		return self.redcap_return

	def ask(self,question,redcap):
		if (self.indi == 1):
			return 0
		choices = self.get_choices(redcap)
		if (choices == -1):
			return self.ask_without_choices(question,"Please enter the value: ",redcap)
		self.generate_chooser(question,"",choices)
		if (self.user_choice != -1):
			self.entry[redcap] = self.user_choice
			return 1
		return 0

	def ask_without_choices(self,question,entry,redcap):
		if (self.indi == 1):
			return 0
		if (self.ask_question(question)):
			value = input(entry)
			print("\n\n")
			self.assign(redcap,value)
			return 1
		return 0

	def ask_question(self,question):
		if (self.indi == 1):
			return 0
		can_answer = input(question + " (if yes, type yes and press enter; otherwise, press enter): ")
		print("\n\n")
		if re.search(r'yes',can_answer,re.I):
			return 1
		else:
			return 0

	def generate_chooser(self,variable,info,choices):
		if (self.indi == 1):
			self.user_choice = -1
			return
		root = Tk()
		v = IntVar()
		v.set(1)
		root.title("Chooser GUI")
		#scrollbar = Scrollbar(root)
		#crollbar.pack(side=RIGHT,fill=Y)

		#mylist = Listbox(root, yscrollcommand=scrollbar.set )

		#menu = Menu(root)
		#root.config(menu=menu)
		Message(root, text=variable).pack(fill=X)
		Button(root, text='OK', width=25, command=root.destroy).pack()
		for choice in choices:
			#mylist.insert(END, Radiobutton(root,text=choice,padx=30,variable=v,value=choices[choice]).pack())
			#menu.add_command(label="test**",command=)
			Radiobutton(root,text=choice,padx=30,variable=v,value=choices[choice]).pack()
		#mylist.insert(Radiobutton(root,text="None of the options",padx=30,variable=v,value=-1).pack())
		Radiobutton(root,text="None of the options",padx=30,variable=v,value=-1).pack()
		#menu.pack()

		#mylist.pack( side = LEFT, fill = BOTH )
		#scrollbar.config( command = mylist.yview )
		root.mainloop()
		self.user_choice = v.get()

	def get_choices(self,redcap):
		for item in self.metadata:
			if (item['field_name'] == redcap):
				if (item['field_type'] == "yesno"):
					return {"yes":1,"no":0}
				opt_str = item['select_choices_or_calculations']
		if (not opt_str):
			return -1
		opt_tup = opt_str.split('|')
		opt_dic = {}
		for each_tup in opt_tup:
			(val,opt) = each_tup.split(',')
			val = val.strip()
			opt = opt.strip()
			opt_dic[opt] = val
		return opt_dic


	def assign(self,redcap,value):
		if (redcap in self.entry):
			self.entry[redcap] += "," + value
			return self.entry[redcap]
		else:
			self.entry[redcap] = value
			return value

	def check(self,variable,value,display,info,redcap):
		correct = self.check_boolean(variable,value,display,info,redcap)
		if (correct == 1):
			return
		if (self.ask_question("Do you know the correct value?")):
			choices = self.get_choices(redcap)
			if (choices == -1):
				overwrite_val = input("Type the correct value for " + variable + ": ")
				overwrite_val.strip()
				self.assign(redcap,overwrite_val)
				print("\n\n")
				return
			self.generate_chooser(variable,info,choices)
			self.assign(redcap,self.user_choice)
		else:
			return

	def check_boolean(self,variable,value,display,info,redcap):
		if (self.indi):
			self.assign(redcap,value)
			return 1

		print("I think '" + variable + "' should be: '" + display + "' based on:\n" + info)
		if (self.ask_question("Is this wrong?")):
			print("\n\n")
			return 0
		else:
			print("\n\n")
			self.assign(redcap,value)
			return 1

	def read_xml(self,file,identifier,search_id):
		with open(file,'r') as x:
			bs = BeautifulSoup(x.read(),"lxml")

		#TODO, make more efficient
		for ass in bs.find_all("article"):
			#if (ass.find('article-id',{'pub-id-type':'pmc'}).text == '3592787'):
			if (ass.find('article-id',{'pub-id-type':identifier}).text == search_id):
				if (ass.find(text=re.compile("The publisher of this article does not allow downloading of the full text in XML form"))):
					#article isnt open access :(
					return -1
				#found open access article
				return str(ass)
		return -1		#article not found
				
