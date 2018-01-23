# Output from MAK and GRID matching

## Method

### Matching to MAK

MAK can be queried by concatenating OR-statements together. The number of results from a MAK query can be no larger than 1000, so we nominally query with 600 sub-queries. We use the paper title from arXiv for the matching, which are prepared by the following procedure:

1. Identify any foreign characters as non-symbolic.
2. Replace all symbolic characters with spaces.
3. Ensure no more than one space separates characters.

This procedure returns a 90% match rate, which may be missing paper where the title is different from that presented on arXiv, or where the paper has not been published in a journal. It may be possible to recuperate some of these missing 10% of papers in the future, for example by matching paper credentials, although this is currently not a limiting factor in our analysis.

### Matching to GRID

The GRID dataset contains institute names, and aliases (where applicable), and a corresponding geospatial coordinate (latitude and longitude). Each institute name from MAK is matched to the comprehensive list from GRID in the following manner:

1. If there is an exact match amongst the institute names or aliases, then extract the coordinates of this match. Assign a "score" of 1 to this match (see step 3. for the definition of "score").
2. Otherwise, check whether a match has previously been found. If so, extract the coordinates and score of this match.
3. Otherwise, calculate a matching score of the MAK by convoluting the matching scores of various fuzzy-matching algorithms in the following manner:
$$ \frac{1}{\sqrt{N}} \sqrt{ \sum_{n=0}^{N} F_{n}(w_{MAK},W_{GRID})^{2} } $$

where $N$ is the number of fuzzy-matching algorithms to use, $F_{n}()$ returns a fuzzy-matching score (in the range $0 \rightarrow 1$) from the $n^{\text{th}}$ algorithm, $w_{MAK}$ is the name from MAK to be matched and $W_{GRID}$ is the comprensive list of institutes in the GRID data.

I currently use the `token_sort_ratio` and `partial_ratio` algorithms implemented in the `fuzzywuzzy` module.

## Fields

| field | source | description |
|---|---|---|
| citations | MAK | number of citations |
| date | MAK | date of publication |
| matched | joel | flag indicating a successful match between arXiv and MAK |
| pid | arXiv | arXiv publication ID, for matching back to arXiv data |
| title | joel | the normalised publication title, used for matching to MAK |
| institutes | MAK | list of institutes from successful matches between arXiv and MAK |
| lat_lon_score | GRID / joel | A list of triplets, with a one-to-one correspondence with institutes. The first two fields are, respectively, latitude and longitude. The third field is the best fuzzy-matching score between GRID and MAK institutes. |

It is generally recommended to only use institutes with scores of 1 of used, which is sufficient for 80% of individual institute-paper matches. Therefore the above method yields an approximate efficiency of 72%, although there are known issues with the GRID matching procedure which leads to a very small number of false matches.