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
        
        
#Arxiv diversity. NB this is supercrude, just using a herfindahl index.
arxiv_cat_totals = pd.pivot_table(mv_data_pre.groupby(['region','arxiv_first_cat']).size().reset_index(drop=False),
                              index='region',columns='arxiv_first_cat',values=0).fillna(0)

#We do it for all disciplines
arxiv_all_divers = arxiv_cat_totals.apply(lambda x: calculate_herfindahl(x),axis=1)
arxiv_all_divers.name = 'arxiv_all_div'

#And for CS disciplines
arxiv_cs_divers = arxiv_cat_totals[[x for x in arxiv_cat_totals.columns if x[:2]=='cs']].apply(
    lambda x: calculate_herfindahl(x),axis=1)
arxiv_cs_divers.name = 'arxiv_cs_div'

fig,ax = plt.subplots()

ax.scatter(arxiv_all_divers,arxiv_cs_divers,alpha=0.75)
ax.set_title('Diversity in CS vs Diversity in all disciplines')
ax.set_ylabel('Diversity in CS')
ax.set_xlabel('Diversity in all disciplines')

 def spec_volatility(self,ax,unit='country',high_cited=False,top_ranking=20,year_threshold=2012,
                       #[high_dl,low_dl]
                       ):
        '''
        This compares the volatility of changes in specialisation for DL, high DL sectors and low DL sectors before and after 2012.
        
        
        '''
        
        
        #Load papers
        papers = self.papers
        
        #This is a repetition of what we did before.
        #Add variable for subsetting
        papers['threshold_year'] = ['pre_'+str(year_threshold) if y<year_threshold else 'post_'+str(year_threshold) for
                                   y in papers['year']]
        
        #Locations
        locations = papers[unit].value_counts()[:top_ranking].index
        
        
        #If we are working with highly cited papers
        #Split into two years, apply the get_cited_papers and combine
        if high_cited != False:
            papers =papers.groupby('threshold_year').apply(lambda x: get_cited_papers(
                x,'citations',high_cited)).reset_index(drop=True)
        
        
        #Create the lq
        #Now we calculate the LQs for both years.
        lqs = papers.groupby(
            'threshold_year').apply(lambda x: create_lq_df(pd.crosstab(x[unit],x['is_dl']))).reset_index(drop=False)
        
        
        #This creates the table for plotting
        specs_wide = pd.pivot_table(lqs,
               index=unit,columns='threshold_year',values='dl').loc[locations]
        
        #This gives the change in specialisation for the top years.
        specs_change = specs_wide['post_'+str(year_threshold)]-specs_wide['pre_'+str(year_threshold)]
        
        #We store the country totals here
        spec_store =[]
        
        #And now to work with the arxiv categories
        for cat in self.categories:
            
            t0 = papers.loc[(papers.year<year_threshold) & ([cat in x for x in papers['arxiv_categories']])]
            t1 = papers.loc[(papers.year>year_threshold) & ([cat in x for x in papers['arxiv_categories']])]
            
            #Total number of papers by country and category
            t0_loc,t1_loc = t0[unit].value_counts(), t1[unit].value_counts()
            t0_loc.name = cat
            t1_loc.name = cat
            
            
            
            #Store the information
            spec_store.append([t0_loc,t1_loc])
            
        
        #Now we create the LQs in each category
        #out = pd.concat([pd.melt(create_lq_df(pd.concat([x[num] for x in spec_store])).fillna(0).reset_index(drop=False),
        #                 index='index') for num in [0,1]],axis=1)
        
        return(spec_store)
            
        #Concatenate
        
        

    def get_spec_volatility(df,threshold_var='threshold_year',activity_var='is_dl'):
    '''
    This returns changes in specialisation for a df
    
    '''
    
    #Create the lq
        #Now we calculate the LQs for both years.
    lqs = papers.groupby(
        'threshold_year').apply(lambda x: create_lq_df(pd.crosstab(x[unit],x['is_dl']))).reset_index(drop=False)
        
        
    #This creates a table with the LQs
    specs_wide = pd.pivot_table(lqs,
                                index=unit,columns='threshold_year',values='dl')[locations]
        
    #This gives the change of specialisation for the top years.
    specs_change = specs_wide['post_'+str(year_threshold)]-specs_wide['pre_'+str(year_threshold)]
        
    
    
    ### Crude analysis of the situation in China

country_collabs = papers_clust.groupby('arxiv_id')['country'].apply(lambda x: list(x)).reset_index(drop=False)

country_collabs['china_us'] = [('China' in x) & ('United States of America' in x) for x in country_collabs['country']]

country_collabs['is_dl'] = [x in papers_expansive for x in country_collabs['arxiv_id']]

country_collabs['year'] = [papers_meta.loc[x,'year'] for x in country_collabs['arxiv_id']]

dl_ct = pd.crosstab(country_collabs['china_us'],country_collabs['is_dl'],margins=1)

china_us_shares = dl_ct[True]/dl_ct['All']

fig,ax = plt.subplots()

(100*china_us_shares[[True,'All']]).plot.bar(color='steelblue',title='Share of DL papers is bigger among US-China collaborations \n than in the wider corpus of arXiv papers',ax=ax)
ax.set_xlabel('')
ax.set_ylabel('DL percentage in category')
ax.set_xticklabels(['Chinese-US collaborations','All arXiv CS papers'],rotation=45,ha='right')

plt.tight_layout()

plt.savefig('/Users/jmateosgarcia/Desktop/china_collabs.png')


dl_papers_recent = country_collabs.loc[(country_collabs['year']>2010) & (country_collabs['is_dl']==True),:]

fig,ax = plt.subplots()
pd.crosstab(dl_papers_recent['year'],dl_papers_recent['china_us'],normalize=0).iloc[:,[1,0]].plot.bar(
    stacked=True,ax=ax,
    colors=['orange','steelblue'],title='Chinese-USA collaborations are \n gaining importance over time')

ax.legend(bbox_to_anchor=(1,1),title='China-US collaborations')
plt.tight_layout()

plt.savefig('/Users/jmateosgarcia/Desktop/china_collabs_time.png')


len(papers_meta)