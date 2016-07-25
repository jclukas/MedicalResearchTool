#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from tkinter import *

import sys, re
import pycurl, io, json
from pprint import pprint

class ArticleManager(object):

	def __init__(self):
		self.indi = 0

	def enter_redcap(self,entry):
		self.entry['record_id'] = '9b7057f5f8894c9c'
		print("uploading")

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
		else:
			self.entry[redcap] = value

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
