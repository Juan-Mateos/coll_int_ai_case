from alphabet_detector import AlphabetDetector
import requests
import json

# Inputs for the MAK POST request, including the API key
HEADERS = {
    'Ocp-Apim-Subscription-Key': 'a9a9efa851b44d5bbd6c841215a99e00',
    'Content-Type': 'application/x-www-form-urlencoded'
}

# Fields to return from MAK
FIELDS = ["Id","Ti","D","AA.AuN","AA.AuId","F.FId",
          "J.JId","AA.AfId","CC","ECC","AA.AfN","J.JN"]

#_______________________
class TitleProcessor(AlphabetDetector):
    '''Processes a pure utf-8 title into something ready for a MAK query.'''
    def process_title(self,title):
        # Get replace non-alphanums (allowing foreign characters)
        result = "".join([x
                          if len(self.detect_alphabet(x)) > 0
                          or x.isnumeric()
                          else " " for x in title.lower()])
        # Replace double-spaces with single-spaces
        while "  " in result:
            result = result.replace("  "," ")        
        return result

#_______________________
'''Find matches to titles from the MAK database.

    raw_titles: A list of titles in the form (id, title)
    call_limit: The maximum number of MAK API calls. 
                NB: Nesta's allowance is 10,000 per month.
'''
def mak_from_titles(raw_titles,call_limit):

    # Make arXiv titles match MAK title format (strip non-alphanums,
    # allowing foreign chars)
    tp = TitleProcessor()
    titles = [(pid,tp.process_title(t)) for pid,t in raw_titles]

    # Maximum of title_count titles, returning query_count results
    title_count = 600
    title_offset = 0
    query_count = 1000

    # Count the number of calls for book-keeping
    calls = 0

    # Iterate until done
    data = []
    while title_offset < len(titles):
        # A soft limit so that we don't overrun the API limit
        if calls >= call_limit:
            break
        calls += 1
        # Get the index of the final title
        last_title = title_offset+title_count
        # Python indexing [n:None] will return n --> end
        if last_title > len(titles):
            last_title = None
        # Get the title subset for this query
        titles_subset = titles[title_offset:last_title]
        title_offset += title_count        
        # Generate the MAK query (OR statement of titles (Ti))
        expr = ["Ti='"+t+"'" for _,t in titles_subset]
        print("Posting",len(expr),"queries")
        expr = ','.join(expr)
        expr = "expr=OR("+expr+")"
        # Write and launch the query
        query = expr+"&count="+str(query_count)+"&attributes="+",".join(FIELDS)
        r = requests.post('https://westus.api.cognitive.microsoft.com/academic/v1.0/evaluate', 
                          data=query.encode("utf-8"), headers=HEADERS)
        try:
            js = r.json()
        except json.decoder.JSONDecodeError as err:
            print("Error with status code ",r.status_code)
            print(r.text)
            raise err
        # Print out some stats
        print("Got",len(js["entities"]),"results")
        # Append the results to the output
        for pid,t in titles_subset:
            # Flag in case no match is found
            matched = False
            for row in js["entities"]:
                if t != row["Ti"]:
                    continue
                insts = list(set(author["AfN"] for author in row["AA"] if "AfN" in author))
                data.append(dict(pid=pid,title=t,institutes=insts,citations=row["CC"],date=row["D"],matched=True))
                matched = True
                break
            # Default in case no match is found
            if not matched:
                data.append(dict(pid=pid,title=t,matched=False))

    # Print summary statistics
    nmatch = 0 
    nboth = 0
    for row in data:
        if not row["matched"]:
            continue
        nmatch += 1
        if row["citations"] > 0 and len(row["institutes"]) > 0:
            nboth += 1
    print("Made",calls,"calls")
    print("Got",nmatch,"matches from",len(data),"queries, of which",
          nboth,"contained both institutes and citation information")
    # Done
    return data

#_______________________
if __name__ == "__main__":

    # Example input titles
    raw_titles = [(1,"Search for invisible decays of a Higgs boson using vector-boson fusion in pp collisions at s√=8 TeV with the ATLAS detector"),
                  (2,"Muon-induced background to proton decay in the p→K+ν decay channel with large underground liquid argon TPC detectors"),
                  (3,"personalizing search via automated analysis of interests and activities")]

    # Example output
    data = mak_from_titles(raw_titles,call_limit=3)
    with open('MAK-matched.json', 'w') as fp:
        json.dump(data, fp)
