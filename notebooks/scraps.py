#Tidy the variable names
papers.columns = ['category','id','categories','is_dl_cex1','is_dl_cex15','citations',
                  'cities','city','codes','countries',
                  'date','organisations','lat_lon','is_dl_lda','mak_match','abstract','year',
                  'summary','title']

#Drop a small number of duplicates (TOCHECK: Where do these come from?)
papers.drop_duplicates('id',inplace=True)

#Set the arXiv index for the paper as the index. This will help concatenate things later.
#papers.set_index('id',inplace=True)

papers.head()

#Load topic_mixes

topic_mix = pd.read_json(ext_data+'/arxiv_corex_with_weights.json')

topic_mix.shape

#The topics are in the columns. We print them
for x in [x for x in topic_mix.columns if len(x)>20]:
    print(x)
    print('\n')
    
#We clean the topics_mix to make sure we only have topics, and leave the id
#as an index we will use for concatenating later.

topics_clean = topic_mix.set_index('id')[[x for x in topic_mix.columns if len(x)>20]]

#The index had some arXiv text in it so we remove it.
topics_clean.index = [x.split(':')[-1] for x in topics_clean.index]


class dlPaperClassification():
    '''
    The class takes a paper df, a topic mix and an index for the topics which contain DL.

    It has a .label_papers method that takes the topic mix and categories papers into DL groups.
    
    It also generates a categorical variable indicating if a paper is 'specialist' (dl is top category) or 
    embedded (dl is simply present)
        
    '''
    
    def __init__(self,papers,topic_mix,dl_var):
        '''
        Initialise the class with a papers file,
        A topic mix file and a list of DL categories.
        
        '''
        
        #NB we will have 
        self.papers = papers
        self.topics = topic_mix
        
        #This can be more than one
        self.dl_var = dl_var
        
        
    def label_papers(self,thres=0.1):
        '''
        We label papers into different levels of DL activity based on the weight
        in their topic mix
        -present if it is above a certain threshold
        -top if it is the top topic (not necessarily above 0.5)
        
        '''
        
        #Load all the information we need for the analysis
        papers = self.papers
        topics = self.topics
        dl_var = self.dl_var
        
        #We use a simple strategy to label DL variables.
        #Since we are taking acce
        topics_melt = pd.melt(topics.reset_index(drop=False),
                             id_vars='arxiv_id')
        
        #Rename
        topics_melt['topic_labelled'] = [x if x not in dl_var else 'topic_ai_dl' for x in topics_melt['variable']]
        
                
        #And pivot. This will aggregate the weights of all topics in DL into a single one 
        topic_aggregated = pd.pivot_table(topics_melt,
                                          index='arxiv_id',
                                          columns='topic_labelled',values='value',aggfunc='sum')
        
        

        #Classify papers into categories
        #Is the DL topic present?
        dl_present = pd.Series(topic_aggregated['topic_ai_dl'].apply(lambda x: x>thres),
                              name='dl_present')
        
        #Is the DL topic the biggest one?
        dl_max = pd.Series(topic_aggregated.idxmax(axis=1)=='topic_ai_dl',name='dl_spec')
                
        #Concatenate all categories and index them (to concatenate with the papers in a moment)
        dl_all_class = pd.concat([dl_present,dl_max],axis=1)
        
        #We define an 'embed' category if papers have dl presence but are not specialised
        dl_all_class['dl_embed'] = (dl_all_class['dl_present']==True) & (dl_all_class['dl_spec']==False)
        
        dl_all_class.index = topics.index
        
        #Concatenate papers and our topic classification
        papers_lab = pd.concat([papers,dl_all_class],axis=1)
        
        #And give them a categorical variable depending on whether they are specialist or embedded
        papers_lab['dl_category'] = ['dl_spec' if x==True else 'dl_embed' if y==True else 'not_dl' for
                                      x,y in zip(papers_lab['dl_spec'],papers_lab['dl_embed'])]
    
        #Save outputs
        #Labels stores the labels we have created
        self.labels = dl_all_class
        
        #Papers_lab stores the paper metadata labelled
        self.papers_lab = papers_lab
        
        #topics_agg stores the aggregated topics (mostly for checking)
        self.topics_agg = topic_aggregated       