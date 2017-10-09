# coding: utf-8

"""
	Copyright 2017 OSIsoft, LLC
	Licensed under the Apache License, Version 2.0 (the "License");
	you may not use this file except in compliance with the License.
	You may obtain a copy of the License at
	
	  <http://www.apache.org/licenses/LICENSE-2.0>
	
	Unless required by applicable law or agreed to in writing, software
	distributed under the License is distributed on an "AS IS" BASIS,
	WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
	See the License for the specific language governing permissions and
	limitations under the License.
"""
from __future__ import absolute_import
import sys
import os
import re
import pandas as pd
import numpy as np
from six import iteritems

class DataApi(object):
	def __init__(self, streamApi, streamSetApi, attributeApi, pointApi):
		self.streamApi = streamApi
		self.streamSetApi = streamSetApi
		self.attributeApi = attributeApi
		self.pointApi = pointApi

	def convert_path_to_web_id(self, fullPath):
		system = fullPath[0:3]
		path = fullPath[3:None]
		if (system == "af:"):
			res = self.attributeApi.get_by_path(path, None)
			return (res.web_id)
		elif (system == "pi:"):
			res = self.pointApi.get_by_path(path, None)
			return (res.web_id)
		else:
			print("Error: invalid path. It needs to start with \"pi\" or \"af\"")
			return

	def convert_paths_to_web_ids(self, paths):
		lengthPaths = len(paths)
		webIds = []
		for path in paths:
			webIds.append(self.convert_path_to_web_id(path))
		return webIds

	def rename_df(self, df, i):
		df.rename(columns={'Value': 'Value' + str(i + 1)}, inplace=True)
		df.rename(columns={'Timestamp': 'Timestamp' + str(i + 1)}, inplace=True)
		df.rename(columns={'UnitsAbbreviation': 'UnitsAbbreviation' + str(i + 1)}, inplace=True)
		df.rename(columns={'Good': 'Good' + str(i + 1)}, inplace=True)
		df.rename(columns={'Questionable': 'Questionable' + str(i + 1)}, inplace=True)
		df.rename(columns={'Substituted': 'Substituted' + str(i + 1)}, inplace=True)
		return  df

	def calculateItemsIndex(self, web_id, items):
		for i in range(0, len(items)):
			if (items[i].web_id == web_id):
				return i
		return  -1


	def convert_multiple_streams_to_df(self, items, gatherInOneDataFrame, web_ids, paths):
		streamsLength = len(items)
		if (gatherInOneDataFrame == True):
			main_df = df_ = pd.DataFrame()
			for i in range(0, streamsLength):
				j = self.calculateItemsIndex(web_ids[i], items);
				df = self.convert_to_df(items[j].items)
				df = self.rename_df(df, i)
				main_df = pd.concat([main_df , df], axis = 1)
			return main_df
		else:
			dfs = {}
			for i in range(0, streamsLength):
				key = paths[i]
				j = self.calculateItemsIndex(web_ids[i], items)
				df = self.convert_to_df(items[j].items)
				dfs[key] = df
			return dfs



	def convert_to_df(self, items):
		columns = ['Value', 'Timestamp', 'UnitsAbbreviation', 'Good', 'Questionable', 'Substituted']
		value = []
		timestamp = []
		unitsAbbreviation = []
		good = []
		questionable = []
		substituted = []
		for	item in items:
			value.append(item.value)
			timestamp.append(item.timestamp)
			unitsAbbreviation.append(item.units_abbreviation)
			good.append(item.good)
			questionable.append(item.questionable)
			substituted.append(item.substituted)



		data = {
			'Value': value,
			'Timestamp': timestamp,
			'UnitsAbbreviation': unitsAbbreviation,
			'Good': good,
			'Questionable': questionable,
			'Substituted': substituted
		}
		df = pd.DataFrame(data)
		return  df

	def get_recorded_values(self, path, boundary_type, desired_units, end_time, filter_expression, include_filtered_values, max_count, selected_fields, start_time, time_zone):
		if (path is None):
			print("The variable path cannot be null.")
			return

		web_id = self.convert_path_to_web_id(path)
		res = self.streamApi.get_recorded(web_id, boundary_type, desired_units, end_time, filter_expression, include_filtered_values, max_count, selected_fields, start_time, time_zone)
		df = self.convert_to_df(res.items)
		return df



	def get_interpolated_values(self, path, desired_units, end_time, filter_expression, include_filtered_values, interval, selected_fields, start_time, time_zone):
		if (path is None):
			print("The variable path cannot be null.")
			return

		web_id = self.convert_path_to_web_id(path)
		res = self.streamApi.get_interpolated(web_id, desired_units, end_time, filter_expression, include_filtered_values, interval, selected_fields, start_time, time_zone)
		df = self.convert_to_df(res.items)
		return df


	def get_plot_values(self, path, desired_units, end_time, intervals, selected_fields, start_time, time_zone, **kwargs):
		if (path is None):
			print("The variable path cannot be null.")
			return

		web_id = self.convert_path_to_web_id(path)
		res = self.streamApi.get_plot(web_id, desired_units, end_time, intervals, selected_fields, start_time, time_zone)
		df = self.convert_to_df(res.items)
		return df

	def get_multiple_interpolated_values(self, paths, end_time, filter_expression, include_filtered_values, interval, selected_fields, start_time, time_zone):
		if (paths is None):
			print("The variable paths cannot be null.")
			return

		web_ids = self.convert_paths_to_web_ids(paths)
		res = self.streamSetApi.get_interpolated_ad_hoc(web_ids,  end_time, filter_expression, include_filtered_values, interval, selected_fields, start_time, time_zone)
		df = self.convert_multiple_streams_to_df(res.items, True, web_ids, None)
		return df

	def get_multiple_plot_values(self, paths, end_time, intervals, selected_fields, start_time, time_zone):
		if (paths is None):
			print("The variable paths cannot be null.")
			return

		web_ids = self.convert_paths_to_web_ids(paths)
		res = self.streamSetApi.get_plot_ad_hoc(web_ids, end_time, intervals, selected_fields, start_time, time_zone)
		df = self.convert_multiple_streams_to_df(res.items, True, web_ids, None)
		return df

	def get_multiple_recorded_values(self, paths,  boundary_type, end_time, filter_expression, include_filtered_values, max_count, selected_fields, start_time, time_zone):
		if (paths is None):
			print("The variable paths cannot be null.")
			return

		web_ids = self.convert_paths_to_web_ids(paths)
		res = self.streamSetApi.get_recorded_ad_hoc(web_ids, boundary_type, end_time, filter_expression, include_filtered_values, max_count, selected_fields, start_time, time_zone)
		df = self.convert_multiple_streams_to_df(res.items, False, web_ids, paths)
		return df





