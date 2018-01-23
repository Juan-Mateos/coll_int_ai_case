import feedparser
import time
import pickle
import numpy as np
import sys

class ArxivAPI():
	"""TODO:
	1. add bool
	2. add other stuff apart form 'all' in search_query
	3. prune useless dict keys 
	
	"""
	def __init__(self):
		self.homepage_url = 'http://export.arxiv.org/api/'
		
	def search_query(self, query, prune=True, start=0, max_results=1000, sorting_method='submittedDate', order='descending'):

		# Gets a list of top results, each of which is a dict
		query_terms = 'query?search_query=all:' + query
		first_result = '&start=' + str(start)
		last_result = '&max_results=' + str(max_results)
		sort_parameter = '&sortBy=' + sorting_method
		sort_order = '&sortOrder=' + order # get newest results first
		
		results = feedparser.parse(self.homepage_url + query_terms + first_result + last_result + sort_parameter + sort_order)
		
		if results['status'] != 200:
			raise Exception("HTTP Error " + str(results['status']) + " in query")
		else:
			results = results['entries']

		return results

if __name__ == '__main__':

	# Instantiate the API
	arxiv_api = ArxivAPI()

	# subjects = ['cond-mat.dis-nn', 'cond-mat.mtrl-sci', 'cond-mat.mtrl-sci', 'cond-mat.other', 'cond-mat.quant-gas', 'cond-mat.soft', 'cond-mat.stat-mech', 'cond-mat.str-el',
	# 'cond-mat.supr-con', 'physics.acc-ph', 'physics.app-ph', 'physics.ao-ph', 'physics.atom-ph', 'physics.atm-clus', 'physics.bio-ph', 'physics.chem-ph', 'physics.class-ph', 
	# 'physics.comp-ph', 'physics.data-an', 'physics.flu-dyn', 'physics.gen-ph', 'physics.geo-ph', 'physics.hist-ph', 'physics.ins-det', 'physics.med-ph', 'physics.optics',
	# 'physics.ed-ph', 'physics.soc-ph', 'physics.plasm-ph', 'physics.pop-ph', 'physics.space-ph', 'math.AG','math.AT', 'math.AP', 'math.CA', 'math.CT', 'math.CO', 'math.AC', 
	# 'math.CV', 'math.DG', 'math.DS', 'math.FA', 'math.GM', 'math.GN', 'math.GT', 'math.GR', 'math.HO', 'math.IT', 'math.KT', 'math.LO', 

	subjects= ['math.MP', 'math.MG', 'math.NT', 
	'math.NA', 'math.OA', 'math.OC', 'math.PR', 'math.QA', 'math.RT', 'math.RA', 'math.SP', 'math.ST', 'math.SG', 'quant-ph', 'nlin.AO', 'nlin.CG', 'nlin.CD', 'nlin.SI', 
	'nlin.PS', 'cs.AI', 'cs.CC', 'cs.CG', 'cs.CE', 'cs.CL', 'cs.CV', 'cs.CY', 'cs.CR', 'cs.DB', 'cs.DS', 'cs.DL', 'cs.DM', 'cs.DC', 'cs.ET', 'cs.FL', 'cs.GT', 'cs.GL', 
	'cs.GR', 'cs.AR', 'cs.HC', 'cs.IR', 'cs.IT', 'cs.LG', 'cs.LO', 'cs.MS', 'cs.MA', 'cs.MM', 'cs.NI', 'cs.NE', 'cs.NA', 'cs.OS', 'cs.OH', 'cs.PF', 'cs.PL', 'cs.RO', 
	'cs.SI', 'cs.SE', 'cs.SD', 'cs.SC', 'cs.SY', 'q-bio.BM', 'q-bio.CB', 'q-bio.GN', 'q-bio.MN', 'q-bio.NC', 'q-bio.OT', 'q-bio.PE', 'q-bio.QM', 'q-bio.SC', 'q-bio.TO', 
	'q-fin.CP', 'q-fin.EC', 'q-fin.GN', 'q-fin.MF', 'q-fin.PM', 'q-fin.PR', 'q-fin.RM', 'q-fin.ST', 'q-fin.TR', 'stat.AP', 'stat.CO', 'stat.ML', 'stat.ME', 'stat.OT', 
	'stat.TH', 'astro-ph', 'gr-qc', 'hep-ex', 'hep-lat', 'hep-ph', 'hep-th', 'math.ph', 'nucl-ex', 'nucl-th', 'physics'] 

	for subject in subjects:
		print('COLLECTING: {}'.format(subject))

		papers = []
		total_papers = 0

		for num in np.arange(0,40000, 1000):
			# print('Starting paper index: {}'.format(num))
			papers.extend(arxiv_api.search_query(query=subject, start=num))
			if len(papers) % 1000 != 0 and total_papers != len(papers):
				break
			else:
				time.sleep(2)

			# Keep track in the number of papers.
			total_papers = len(papers)
			print('Number of collected papers: {}'.format(total_papers))

		# Save all the papers of a subject to a pickle.
		with open('data/{}_papers.pickle'.format(subject.replace('.','_')), 'wb') as h:
			pickle.dump(papers, h)

		print('TOTAL {}: {} '.format(subject, len(papers)))